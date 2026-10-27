"""Fluxo integrado do Desafio 6 para UMA solicitação (texto, transcrição STT ou OCR).

entrada -> guardrail -> ficha (contrato v2) -> validação -> compreensão (RF15)
        -> RAG por sub-pedido (RF19) -> minuta montada -> filtro de saída -> PENDENTE.
Ficha inválida ou entrada bloqueada => nenhuma minuta (RF14/RF16). Nada é enviado.
"""

from __future__ import annotations

import hashlib
import re
import time
from datetime import datetime, timezone

from . import contrato, guardrails, nlp, rag
from .estruturacao import estruturar
from .seguranca import minimizar

DECISOES = ("permitir", "revisar", "bloquear")


def _subconsultas(pedido: str | None) -> list[str]:
    """Pedidos múltiplos ('solicito X; peço Y') viram consultas independentes."""
    if not pedido:
        return []
    partes = [p.strip(" .") for p in re.split(r";|\.\s+", pedido) if len(p.split()) >= 3]
    return partes[:3]


def _combinar(respostas: list[dict]) -> dict:
    if not respostas:
        return {"status": "sem_evidencia_suficiente", "afirmacoes": [], "fontes": [], "conflitos": [],
                "motivos_revisao": ["pedido não identificado: consulta ao acervo não realizada"], "consultas": []}
    status = [r["status"] for r in respostas]
    if "bloqueada" in status:
        final = "bloqueada"
    elif "conflito_de_fontes" in status:
        final = "conflito_de_fontes"
    elif "fundamentada" in status:
        final = "fundamentada"
    else:
        final = "sem_evidencia_suficiente"
    fontes, vistos = [], set()
    for r in respostas:
        for f in r["fontes"]:
            if f["chunk_id"] not in vistos:
                vistos.add(f["chunk_id"])
                fontes.append(f)
    return {
        "status": final,
        "afirmacoes": [a for r in respostas for a in r["afirmacoes"]],
        "fontes": fontes,
        "conflitos": [r["conflito"] for r in respostas if r.get("conflito") and r["conflito"]["conflito"]],
        "motivos_revisao": [
            f"consulta {i}/{len(respostas)}: {m}" for i, r in enumerate(respostas, 1) for m in r["motivos_revisao"]
        ],
        "consultas": [
            {"status": r["status"], "chunk_ids": [t["chunk_id"] for t in r["trechos_recuperados"]],
             "quarentena": [q["chunk_id"] for q in r["quarentena"]], "erros": r["erros"]}
            for r in respostas
        ],
    }


def montar_minuta(ficha: dict, compreensao: dict, rag_combinado: dict, gerador, motivos: list[str]) -> str:
    e = contrato.exibir
    linhas = [
        "# MINUTA — NÃO ENVIADA (pendente de revisão humana)",
        "",
        "**Órgão:** Secretaria Fictícia de Serviços ao Cidadão",
        f"**Protocolo:** {e(ficha['protocolo'])}  ",
        f"**Data da solicitação:** {e(ficha['data'])}  ",
        f"**Solicitante:** {e(ficha['solicitante'])}  ",
        f"**Assunto:** {e(ficha['assunto'])}  ",
        f"**Categoria (inferida):** {ficha['categoria']}",
        "",
        "## Fatos informados pelo solicitante (não verificados pela instituição)",
        f"- Pedido: {e(ficha['pedido'])}",
        f"- Campos não localizados: {', '.join(ficha['campos_ausentes']) or 'nenhum'}",
        f"- Resumo ({compreensao['palavras']} palavras): {compreensao['resumo']}",
        "",
        "## Orientações institucionais (acervo fictício)",
    ]
    status = rag_combinado["status"]
    if status == "fundamentada":
        por_id = {f["chunk_id"]: f for f in rag_combinado["fontes"]}
        for a in rag_combinado["afirmacoes"]:
            fonte = por_id.get(a["chunk_ids"][0])
            local = fonte["local"] if fonte else a["chunk_ids"][0]
            linhas.append(f"- {a['texto']} — *Fonte: {local}; trecho `{a['chunk_ids'][0]}`*")
    elif status == "conflito_de_fontes":
        linhas.append("- **Conflito de fontes não resolvido.** Nenhum prazo deve ser informado ao cidadão até decisão do servidor:")
        for c in rag_combinado["conflitos"]:
            for d in c["divergencias"]:
                for v in d["valores"]:
                    linhas.append(f"  - {v['local']}: \"{v['frase']}\" (trecho `{v['chunk_id']}`)")
    else:
        linhas.append(
            "- Não foi localizada orientação suficiente no acervo para este pedido. "
            "O servidor responsável deve complementar a resposta ou solicitar esclarecimento ao cidadão."
        )
    linhas += ["", "## Pendências para o servidor"]
    linhas += [f"- {m}" for m in motivos] or ["- nenhuma pendência específica além da revisão obrigatória"]
    linhas += [
        "",
        f"> Conteúdo preparado com apoio automatizado (gerador: {gerador.nome}; LLM: "
        f"{'sim' if gerador.e_llm else 'não'}), sujeito à revisão humana. Nenhuma resposta é enviada automaticamente.",
    ]
    return "\n".join(linhas) + "\n"


def processar_solicitacao(
    texto: str,
    *,
    caso_id: str,
    modalidade: str,
    cfg: dict,
    indice,
    gerador,
    repositorio=None,
    orcamento=None,
    modo_estruturacao: str | None = None,
    conversar_fn=None,
    hoje=None,
    arquivo_auditoria=None,
    id_execucao: str | None = None,
) -> dict:
    from .auditoria import registrar_d6

    t0 = time.monotonic()
    inicio = datetime.now(timezone.utc).isoformat()
    sha_entrada = hashlib.sha256(texto.encode("utf-8")).hexdigest()
    resultado = {
        "caso_id": caso_id,
        "modalidade": modalidade,
        "sha256_entrada": sha_entrada,
        "decisao": None,
        "motivos": [],
        "guardrail": None,
        "estruturacao": None,
        "compreensao": None,
        "rag": None,
        "minuta": None,
        "minuta_id": None,
        "status_minuta": None,
    }
    try:
        previa = guardrails.avaliar_entrada(texto, cfg, similaridade_acervo=1.0)
        similaridade = None
        if previa["decisao"] != "bloquear":
            achados = indice.buscar(texto[:1000], 1)
            similaridade = achados[0]["similaridade"] if achados else None
        guarda = guardrails.avaliar_entrada(texto, cfg, similaridade_acervo=similaridade)
        resultado["guardrail"] = guarda
        if guarda["decisao"] == "bloquear":
            resultado["decisao"] = "bloquear"
            resultado["motivos"] = [f"guardrail: {m['codigo']}" for m in guarda["motivos"]]
            return resultado
        perfil_llm = cfg["geracao"]["perfis"].get(cfg.get("estruturacao", {}).get("perfil_llm", "principal"), {})
        est = estruturar(
            texto,
            modo=modo_estruturacao or cfg.get("estruturacao", {}).get("modo", "regras"),
            modalidade=modalidade,
            perfil=perfil_llm,
            orcamento=orcamento,
            conversar_fn=conversar_fn,
            hoje=hoje,
        )
        resultado["estruturacao"] = {
            "modo": est["modo"],
            "valido": est["validacao"]["valido"],
            "erros": contrato.resumo_erros(est["validacao"]),
            "tentativas": len(est["tentativas"]),
            "ficha": est["ficha"] if est["validacao"]["valido"] else est["validacao"]["objeto"],
        }
        if not est["validacao"]["valido"]:
            resultado["decisao"] = "bloquear"
            resultado["motivos"] = ["estrutura ou dados inválidos: minuta bloqueada"] + resultado["estruturacao"]["erros"]
            return resultado
        ficha = est["ficha"]
        compreensao = nlp.compreender(texto, ficha)
        resultado["compreensao"] = compreensao
        fatos = minimizar(f"Pedido: {ficha['pedido']}") if ficha["pedido"] else None
        respostas = [
            rag.responder(
                sub, indice=indice, gerador=gerador, cfg=cfg, fatos_solicitante=fatos,
                orcamento=orcamento, conversar_fn=conversar_fn, arquivo_auditoria=arquivo_auditoria,
                id_execucao=id_execucao,
            )
            for sub in _subconsultas(ficha["pedido"])
        ]
        combinado = _combinar(respostas)
        resultado["rag"] = combinado
        motivos = list(ficha["motivos_revisao"])
        motivos += [f"guardrail: {m['codigo']}" for m in guarda["motivos"]]
        motivos += combinado["motivos_revisao"]
        resultado["motivos"] = motivos
        if combinado["status"] == "bloqueada":
            resultado["decisao"] = "bloquear"
            return resultado
        # A decisão de entrada depende de guardrail e ficha; o status do RAG vai para a minuta.
        resultado["decisao"] = "revisar" if (guarda["decisao"] == "revisar" or ficha["requer_revisao"]) else "permitir"
        minuta = montar_minuta(ficha, compreensao, combinado, gerador, motivos)
        filtro = guardrails.filtrar_saida(minuta, cfg)
        if filtro["bloqueado"]:
            resultado["decisao"] = "bloquear"
            resultado["motivos"].append("minuta bloqueada pelo filtro de saída")
            return resultado
        resultado["minuta"] = filtro["texto"]
        resultado["status_minuta"] = "pendente"
        if repositorio is not None:
            resultado["minuta_id"] = repositorio.criar_minuta(
                caso_id,
                filtro["texto"],
                gerador=gerador.nome,
                ia_participou=True,
                modalidade=modalidade,
                metadados={
                    "decisao_entrada": resultado["decisao"],
                    "status_rag": combinado["status"],
                    "chunk_ids": [f["chunk_id"] for f in combinado["fontes"]],
                    "versao_schema": contrato.VERSAO_SCHEMA,
                    "sha256_entrada": sha_entrada,
                    "gerador_e_llm": gerador.e_llm,
                },
            )
        return resultado
    finally:
        registrar_d6(
            "solicitacao_processada",
            arquivo=arquivo_auditoria,
            segredos=guardrails.segredos_conhecidos(cfg),
            id_execucao=id_execucao,
            caso_id=caso_id,
            modalidade=modalidade,
            inicio=inicio,
            fim=datetime.now(timezone.utc).isoformat(),
            latencia_ms=round((time.monotonic() - t0) * 1000, 1),
            sha256_entrada=sha_entrada,
            versao_schema=contrato.VERSAO_SCHEMA,
            estruturacao_modo=(resultado["estruturacao"] or {}).get("modo"),
            estruturacao_valida=(resultado["estruturacao"] or {}).get("valido"),
            decisao_entrada=resultado["decisao"],
            motivos=resultado["motivos"],
            categoria=((resultado["estruturacao"] or {}).get("ficha") or {}).get("categoria"),
            status_rag=(resultado["rag"] or {}).get("status"),
            chunk_ids=[f["chunk_id"] for f in (resultado["rag"] or {}).get("fontes", [])],
            gerador=getattr(gerador, "nome", None),
            minuta_id=resultado["minuta_id"],
            status_minuta=resultado["status_minuta"],
            orcamento=orcamento.resumo() if orcamento else None,
            decisao_humana="pendente",
        )
