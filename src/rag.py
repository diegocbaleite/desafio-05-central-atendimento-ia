"""RAG fundamentado (RF19): pergunta -> guardrail -> recuperação -> geração -> verificação.

O status final é decidido por CÓDIGO, não pelo gerador:
- conflito_de_fontes        : divergência entre documentos sem prioridade/substituição explícita;
- sem_evidencia_suficiente  : nenhuma afirmação sustentada pelos trechos;
- fundamentada              : ao menos uma afirmação sustentada e nenhuma divergência aberta.
Afirmações não sustentadas são removidas e a consulta é encaminhada à revisão.
"""

from __future__ import annotations

import hashlib
import math
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone

from . import guardrails
from .geracao import cobertura
from .ingestao import descrever_local
from .orcamento import Orcamento
from .texto import frases, numeros, quantidades, termos

STATUS = ("fundamentada", "sem_evidencia_suficiente", "conflito_de_fontes")
MENSAGEM_ABSTENCAO = (
    "Não há evidência suficiente no acervo para responder com segurança. "
    "A consulta foi encaminhada ao operador; nenhuma orientação institucional foi inventada."
)
_CACHE_IDF: dict = {}


def idf_do_indice(indice) -> dict:
    colecao = indice._colecao()
    chave = (str(indice.diretorio), indice.nome_colecao, colecao.count())
    if chave not in _CACHE_IDF:
        docs = colecao.get(include=["documents"])["documents"] or []
        n = len(docs)
        df = Counter(t for d in docs for t in set(termos(d)))
        idf = {t: math.log((n + 1) / (c + 1)) + 1 for t, c in df.items()}
        idf["__ausente__"] = math.log(n + 1) + 1  # termo que não existe no acervo pesa o máximo
        _CACHE_IDF.clear()
        _CACHE_IDF[chave] = idf
    return _CACHE_IDF[chave]


def recuperar(indice, pergunta: str, top_k: int, limiar: float) -> dict:
    todos = indice.buscar(pergunta, top_k)
    validos, quarentena, abaixo = [], [], []
    for t in todos:
        if t["metadados"].get("suspeito_injecao"):
            quarentena.append(t)  # nunca entra no contexto de geração
        elif t["similaridade"] < limiar:
            abaixo.append(t)
        else:
            validos.append(t)
    return {"todos": todos, "validos": validos, "quarentena": quarentena, "abaixo_limiar": abaixo}


def verificar_afirmacoes(afirmacoes: list[dict], trechos: list[dict]) -> list[dict]:
    """Aceita frases completas contíguas copiadas de um mesmo trecho citado.

    Sobreposição de termos não prova sentido: remover uma negação pode inverter uma
    orientação. A comparação conserva palavras, acentos e pontuação; apenas normaliza
    Unicode e espaços de extração do PDF. Paráfrases seguem para revisão.
    """
    literal = lambda s: " ".join(unicodedata.normalize("NFC", s).split())  # noqa: E731
    por_id = {t["chunk_id"]: t for t in trechos}
    verificadas = []
    for a in afirmacoes:
        motivos = []
        citados = [por_id[c] for c in a.get("chunk_ids", []) if c in por_id]
        if not a.get("chunk_ids"):
            motivos.append("sem_citacao")
        elif len(citados) != len(a["chunk_ids"]):
            motivos.append("cita_trecho_fora_do_contexto")
        texto_fonte = " ".join(t["texto"] for t in citados)
        citacao = literal(a.get("citacao_literal", ""))
        if citados and (not citacao or not any(citacao in literal(t["texto"]) for t in citados)):
            motivos.append("citacao_literal_nao_encontrada")
        if citados:
            inventados = numeros(a["texto"]) - numeros(texto_fonte)
            if inventados:
                motivos.append("numero_sem_suporte: " + ", ".join(sorted(inventados)))
            suportam = []
            for t in citados:
                unidades = [literal(f) for f in frases(t["texto"])]
                completas = {
                    " ".join(unidades[inicio:fim])
                    for inicio in range(len(unidades))
                    for fim in range(inicio + 1, len(unidades) + 1)
                }
                if literal(a["texto"]) and literal(a["texto"]) in completas:
                    suportam.append(t)
            if not suportam:
                motivos.append("afirmacao_nao_literal_completa")
            elif not any(citacao in literal(t["texto"]) for t in suportam):
                motivos.append("citacao_literal_fora_do_trecho_da_afirmacao")
        verificada = {**a, "sustentada": not motivos, "motivos": motivos}
        if not motivos:
            # O primeiro ID é usado na citação exibida. Não atribuir a afirmação
            # a outro trecho apenas porque ele também foi indicado pelo modelo.
            verificada["chunk_ids"] = list(dict.fromkeys(t["chunk_id"] for t in suportam))
        verificadas.append(verificada)
    return verificadas


def detectar_conflito(pergunta: str, trechos: list[dict], idf: dict, cobertura_minima: float) -> dict:
    """Mesma unidade (ex.: 'dias uteis') com valores diferentes em documentos distintos."""
    por_unidade: dict = defaultdict(list)
    for t in trechos:
        for frase in frases(t["texto"]):
            if cobertura(pergunta, frase, idf) < cobertura_minima:
                continue
            for valor, unidade in quantidades(frase):
                por_unidade[unidade].append({"valor": valor, "frase": frase, "trecho": t})
    divergencias = []
    for unidade, itens in por_unidade.items():
        valores_por_doc = defaultdict(set)
        for i in itens:
            valores_por_doc[i["trecho"]["metadados"]["doc_id"]].add(i["valor"])
        if len(valores_por_doc) > 1 and len({v for vs in valores_por_doc.values() for v in vs}) > 1:
            divergencias.append({"unidade": unidade, "itens": itens})
    if not divergencias:
        return {"conflito": False, "resolvido": False, "regra": None, "divergencias": []}
    # Cada divergência precisa ser resolvida. Uma substituição parcial ou um empate
    # entre as maiores prioridades não autoriza escolher arbitrariamente uma fonte.
    for d in divergencias:
        metas = {i["trecho"]["metadados"]["doc_id"]: i["trecho"]["metadados"] for i in d["itens"]}
        regras, revogados = [], set()
        for doc_id, meta in metas.items():
            alvos = {x.strip() for x in meta.get("substitui", "").split(",")} & (set(metas) - {doc_id})
            if alvos:
                revogados.update(alvos)
                regras.append(f"{doc_id} declara substituir {', '.join(sorted(alvos))}")
        vigentes = set(metas) - revogados
        maior = max((metas[c].get("prioridade", 1) for c in vigentes), default=None)
        prevalecem = {c for c in vigentes if metas[c].get("prioridade", 1) == maior}
        valores = {i["valor"] for i in d["itens"] if i["trecho"]["metadados"]["doc_id"] in prevalecem}
        d["resolvido"] = len(valores) == 1
        if d["resolvido"] and vigentes - prevalecem:
            regras.append(f"prioridade explícita: {', '.join(sorted(prevalecem))} (prioridade {maior})")
        d["regra"] = "; ".join(regras) if d["resolvido"] else None
        d["docs_descartados"] = sorted(set(metas) - prevalecem) if d["resolvido"] else []
    resolvido = all(d["resolvido"] for d in divergencias)
    return {
        "conflito": True,
        "resolvido": resolvido,
        "regra": "; ".join(dict.fromkeys(d["regra"] for d in divergencias)) if resolvido else None,
        # Defesa conservadora: nenhuma afirmação desses documentos será exibida.
        "docs_descartados": sorted({c for d in divergencias for c in d["docs_descartados"]}) if resolvido else [],
        "divergencias": [
            {
                "unidade": d["unidade"],
                "resolvido": d["resolvido"],
                "regra": d["regra"],
                "valores": [
                    {
                        "valor": i["valor"],
                        "doc_id": i["trecho"]["metadados"]["doc_id"],
                        "local": descrever_local(i["trecho"]["metadados"]),
                        "chunk_id": i["trecho"]["chunk_id"],
                        "frase": i["frase"],
                    }
                    for i in d["itens"]
                ],
            }
            for d in divergencias
        ],
    }


def _fonte(t: dict) -> dict:
    m = t["metadados"]
    return {
        "chunk_id": t["chunk_id"],
        "doc_id": m["doc_id"],
        "titulo": m["titulo"],
        "versao": m["versao"],
        "secao": m["secao"],
        "pagina": m["pagina"] if m["pagina"] > 0 else None,
        "local": descrever_local(m),
        "trecho": t["texto"],
        "similaridade": t["similaridade"],
    }


def responder(
    pergunta: str,
    *,
    indice,
    gerador,
    cfg: dict,
    top_k: int | None = None,
    fatos_solicitante: str | None = None,
    orcamento=None,
    conversar_fn=None,
    auditar: bool = True,
    arquivo_auditoria=None,
    id_execucao: str | None = None,
) -> dict:
    # Consultas independentes também têm orçamento. O fluxo integrado fornece o
    # mesmo objeto para compartilhar o teto entre todas as suas subconsultas.
    if orcamento is None:
        orcamento = Orcamento.de_config(cfg)
    r = cfg["recuperacao"]
    top_k = int(top_k or r.get("top_k", 4))
    limiar = float(r.get("limiar_similaridade", 0.35))
    cob_min = float(r.get("cobertura_minima", 0.5))
    inicio = datetime.now(timezone.utc)
    t0 = time.monotonic()
    saida = {
        "pergunta_sha256": hashlib.sha256(pergunta.encode("utf-8")).hexdigest(),
        "status": "sem_evidencia_suficiente",
        "resposta": MENSAGEM_ABSTENCAO,
        "afirmacoes": [],
        "afirmacoes_removidas": [],
        "fontes": [],
        "trechos_recuperados": [],
        "quarentena": [],
        "conflito": None,
        "encaminhar_revisao": True,
        "motivos_revisao": [],
        "gerador": {"perfil": getattr(gerador, "nome", None), "e_llm": getattr(gerador, "e_llm", None)},
        "guardrail_entrada": None,
        "guardrail_saida": None,
        "erros": [],
        "top_k": top_k,
        "limiar_similaridade": limiar,
        "cobertura_minima": cob_min,
        "indice": {"colecao": indice.nome_colecao, "versao": indice.versao_indice, "embedding": indice.embedder.nome},
    }
    try:
        # Camada 1: bloqueios que dispensam busca (segredo, tamanho, vazio).
        previa = guardrails.avaliar_entrada(pergunta, cfg, similaridade_acervo=1.0)
        if previa["decisao"] == "bloquear":
            saida.update(guardrail_entrada=previa, status="bloqueada", resposta="Consulta bloqueada pelo guardrail de entrada.")
            saida["motivos_revisao"].append("entrada bloqueada: " + ", ".join(m["codigo"] for m in previa["motivos"]))
            return saida
        rec = recuperar(indice, pergunta, top_k, limiar)
        maior = max((t["similaridade"] for t in rec["todos"]), default=None)
        guarda = guardrails.avaliar_entrada(pergunta, cfg, similaridade_acervo=maior)
        saida["guardrail_entrada"] = guarda
        saida["trechos_recuperados"] = [
            {**_fonte(t), "posicao": t["posicao"], "distancia_cosseno": t["distancia_cosseno"],
             "em_quarentena": bool(t["metadados"].get("suspeito_injecao")), "abaixo_limiar": t in rec["abaixo_limiar"]}
            for t in rec["todos"]
        ]
        saida["quarentena"] = [
            {"chunk_id": t["chunk_id"], "motivos": t["metadados"].get("motivos_suspeita")} for t in rec["quarentena"]
        ]
        if rec["quarentena"]:
            saida["motivos_revisao"].append("trecho suspeito de instrução maliciosa em quarentena (não usado)")
        if guarda["decisao"] == "bloquear":
            saida.update(status="bloqueada", resposta="Consulta bloqueada: fora do escopo do atendimento.")
            saida["motivos_revisao"].append("entrada bloqueada: " + ", ".join(m["codigo"] for m in guarda["motivos"]))
            return saida
        if guarda["decisao"] == "revisar":
            saida["motivos_revisao"].append("guardrail de entrada pediu revisão")
        idf = idf_do_indice(indice)
        gerado = gerador.gerar(
            pergunta,
            rec["validos"],
            fatos_solicitante=fatos_solicitante,
            idf=idf,
            cobertura_minima=cob_min,
            orcamento=orcamento,
            conversar_fn=conversar_fn,
        )
        saida["gerador"].update(gerado["metadados"])
        if gerado.get("erro_validacao"):
            saida["erros"].append("saída do gerador inválida após 1 correção")
        verificadas = verificar_afirmacoes(gerado["afirmacoes"], rec["validos"])
        sustentadas = [a for a in verificadas if a["sustentada"]]
        limpo = lambda s: guardrails.filtrar_saida(s or "", cfg)["texto"]  # noqa: E731
        saida["afirmacoes_removidas"] = [
            {**a, "texto": limpo(a.get("texto")), "citacao_literal": limpo(a.get("citacao_literal"))}
            for a in verificadas
            if not a["sustentada"]
        ]
        if saida["afirmacoes_removidas"]:
            saida["motivos_revisao"].append("afirmação sem suporte removida")
        conflito = detectar_conflito(pergunta, rec["validos"], idf, cob_min)
        saida["conflito"] = conflito
        descartados = set(conflito.get("docs_descartados", []))
        if descartados:
            por_id = {t["chunk_id"]: t["metadados"]["doc_id"] for t in rec["validos"]}
            mantidas = []
            for a in sustentadas:
                if any(por_id[c] in descartados for c in a["chunk_ids"]):
                    saida["afirmacoes_removidas"].append({
                        **a, "texto": limpo(a["texto"]), "citacao_literal": limpo(a["citacao_literal"]),
                        "sustentada": False, "motivos": ["fonte_nao_prevalece_no_conflito"],
                    })
                else:
                    mantidas.append(a)
            sustentadas = mantidas
        if conflito["conflito"] and not conflito["resolvido"]:
            saida["status"] = "conflito_de_fontes"
            partes = [
                f"{v['local']}: \"{v['frase']}\"" for d in conflito["divergencias"] for v in d["valores"]
            ]
            saida["resposta"] = (
                "As fontes do acervo divergem e nenhuma regra de prioridade ou substituição resolve a divergência: "
                + " | ".join(partes)
                + ". Encaminhado para revisão humana; nenhum prazo foi escolhido pelo sistema."
            )
            saida["motivos_revisao"].append("conflito de fontes não resolvido")
            usados = {v["chunk_id"] for d in conflito["divergencias"] for v in d["valores"]}
            saida["fontes"] = [_fonte(t) for t in rec["validos"] if t["chunk_id"] in usados]
        elif sustentadas:
            saida["status"] = "fundamentada"
            saida["afirmacoes"] = sustentadas
            # A resposta exibida é SEMPRE montada das afirmações verificadas; o texto livre
            # do gerador fica só na auditoria, pois pode conter conteúdo não verificado.
            saida["resposta_livre_do_gerador_nao_exibida"] = limpo(gerado.get("resposta"))[:500]
            por_id = {t["chunk_id"]: t for t in rec["validos"]}
            saida["resposta"] = " ".join(
                f"{a['texto']} [{descrever_local(por_id[a['chunk_ids'][0]]['metadados'])}]" for a in sustentadas
            )
            if conflito["conflito"]:
                saida["motivos_revisao"].append("divergência resolvida por regra documentada: " + conflito["regra"])
            usados = {c for a in sustentadas for c in a["chunk_ids"]}
            saida["fontes"] = [_fonte(t) for t in rec["validos"] if t["chunk_id"] in usados]
        else:
            saida["motivos_revisao"].append("sem evidência suficiente: abstenção")
        citados = {f["chunk_id"] for f in saida["fontes"]}
        suspeitos = sorted(
            {t["metadados"]["doc_id"] for t in rec["validos"] if t["chunk_id"] in citados and t["metadados"].get("documento_suspeito")}
        )
        if suspeitos:
            saida["motivos_revisao"].append("fonte citada pertence a documento com instrução suspeita: " + ", ".join(suspeitos))
        filtro = guardrails.filtrar_saida(saida["resposta"], cfg)
        saida["guardrail_saida"] = {"bloqueado": filtro["bloqueado"], "motivos": filtro["motivos"]}
        saida["resposta"] = filtro["texto"]
        if filtro["bloqueado"]:
            saida.update(status="bloqueada", afirmacoes=[], fontes=[])
            saida["motivos_revisao"].append("saída bloqueada: " + ", ".join(filtro["motivos"]))
        saida["encaminhar_revisao"] = saida["status"] != "fundamentada" or bool(saida["motivos_revisao"])
    except Exception as exc:  # falha tratada e auditada (RF21/T12)
        saida["status"] = "falha"
        saida["resposta"] = "Falha no processamento da consulta; nenhuma resposta foi gerada."
        saida["erros"].append(f"{type(exc).__name__}: {str(exc)[:200]}")
        saida["encaminhar_revisao"] = True
    finally:
        saida["latencia_ms"] = round((time.monotonic() - t0) * 1000, 1)
        if auditar:
            from .auditoria import registrar_d6
            from .seguranca import minimizar

            registrar_d6(
                "consulta_rag",
                arquivo=arquivo_auditoria,
                segredos=guardrails.segredos_conhecidos(cfg),
                id_execucao=id_execucao,
                inicio=inicio.isoformat(),
                fim=datetime.now(timezone.utc).isoformat(),
                latencia_ms=saida["latencia_ms"],
                consulta_minimizada=minimizar(pergunta)[:200],
                consulta_sha256=saida["pergunta_sha256"],
                versao_indice=saida["indice"],
                prompt=saida["gerador"].get("prompt", "não se aplica (gerador local)"),
                gerador=saida["gerador"].get("perfil"),
                gerador_e_llm=saida["gerador"].get("e_llm"),
                chunk_ids_recuperados=[t["chunk_id"] for t in saida["trechos_recuperados"]],
                chunk_ids_citados=[f["chunk_id"] for f in saida["fontes"]],
                quarentena=[q["chunk_id"] for q in saida["quarentena"]],
                status=saida["status"],
                encaminhar_revisao=saida["encaminhar_revisao"],
                erros=saida["erros"],
                tokens_entrada=saida["gerador"].get("tokens_entrada", "indisponível"),
                tokens_saida=saida["gerador"].get("tokens_saida", "indisponível"),
                custo_usd=saida["gerador"].get("custo_usd", "indisponível"),
                orcamento=orcamento.resumo() if orcamento else None,
                decisao_humana="não se aplica (consulta)",
            )
    return saida
