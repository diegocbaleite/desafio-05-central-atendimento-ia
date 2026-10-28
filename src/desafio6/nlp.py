"""RF14/RF15: análise estruturada via adaptador e uma correção no máximo."""

from __future__ import annotations

from pathlib import Path
import re

from ..extracao import extrair
from ..seguranca import delimitar, minimizar
from .contratos import ErroContrato, esquema_analise, unidades_extrativas, validar_analise


def analisar_solicitacao(texto, cliente, *, modalidade="texto", conferencia=False):
    if not isinstance(texto, str) or not texto.strip():
        raise ErroContrato("Solicitação vazia")
    if modalidade not in {"texto", "audio", "imagem", "ocr"}:
        raise ErroContrato("Modalidade inválida")
    if type(conferencia) is not bool:
        raise ErroContrato("Conferência humana deve ser confirmação booleana explícita")
    sistema = (Path(__file__).parents[2] / "prompts/desafio6/nlp.md").read_text(encoding="utf-8")
    conteudo = delimitar(minimizar(texto))
    erro_anterior = None
    for tentativa in range(2):
        instrucao = sistema
        if tentativa:
            instrucao += "\nCorrija somente a regra rejeitada: " + str(erro_anterior)
        try:
            analise = cliente.gerar_json(instrucao, conteudo, esquema_analise(), nome="solicitacao")
            validar_analise(analise, texto)
        except ErroContrato as exc:
            erro_anterior = exc
            continue
        analise = dict(analise)
        analise["modalidade"] = modalidade
        analise["conferencia_humana"] = bool(conferencia)
        analise["apta_para_minuta"] = modalidade == "texto" or bool(conferencia)
        analise["tentativas_validacao"] = tentativa + 1
        return analise
    raise ErroContrato("Saída bloqueada após uma correção: " + str(erro_anterior))


def ficha_local_simulada(texto: str) -> dict:
    """Fixture dinâmica por regras; nunca consulta os gabaritos nem representa IA."""
    texto = texto.removeprefix("<conteudo_externo>\n").removesuffix("\n</conteudo_externo>")
    legado = extrair(texto, "simulacao", "memoria", "nao_aplicado", "texto")
    campos = legado["campos"]
    ficha = {"versao_schema": "2.0"}
    for novo, antigo in (("protocolo", "protocolo"), ("data", "data_solicitacao"),
                          ("solicitante", "solicitante"), ("assunto", "assunto"), ("pedido", "pedido")):
        valor = campos[antigo]["valor"]
        ficha[novo] = None if valor == "não localizado" else valor
    categoria = legado["categoria"]["codigo"]
    if "não sei" in texto.casefold() and " ou " in texto.casefold():
        categoria = "revisao"
    ficha["categoria"] = categoria
    orgaos = re.findall(r"(?im)^\s*[ÓO]rg[aã]o\s*:\s*(.+)$", texto)
    locais = re.findall(r"(?im)^\s*Local\s*:\s*(.+)$", texto)
    datas = re.findall(r"\b\d{1,2}/\d{1,2}/\d{4}\b|\b\d{1,2} de \w+ de \d{4}\b", texto, re.IGNORECASE)
    protocolos = re.findall(r"\b20\d{2}\s*[.-]\s*\d{3}(?:\s*[.-]?\s*)\d{3}\b", texto)
    ficha["entidades"] = {
        "pessoas": [ficha["solicitante"]] if ficha["solicitante"] else [],
        "orgaos": orgaos, "locais": locais, "datas": list(dict.fromkeys(datas)),
        "protocolos": list(dict.fromkeys(protocolos)),
    }
    ficha["campos_ausentes"] = [k for k in ("protocolo", "data", "solicitante", "assunto", "pedido") if ficha[k] is None]
    ficha["necessita_revisao"] = True
    selecionadas, palavras = [], 0
    for unidade in unidades_extrativas(texto):
        total = len(unidade.split())
        if palavras + total <= 100:
            selecionadas.append(unidade)
            palavras += total
    if not selecionadas:
        raise ErroContrato("Nenhuma frase completa cabe no resumo simulado de 100 palavras")
    return {"ficha": ficha, "resumo": " ".join(selecionadas), "inferencias": []}


def avaliar_solicitacoes(resultados, gabaritos):
    """Comparação determinística; não equivale à conferência humana do resumo."""
    esperados = {item["id"]: item for item in gabaritos}
    casos, categorias_corretas = [], 0
    for item in resultados:
        caso_id = item["id"]
        esperado = esperados[caso_id]
        analise = item.get("analise", item)
        ficha = analise["ficha"]
        correta = ficha["categoria"] == esperado["ficha"]["categoria"]
        categorias_corretas += correta
        campos = [k for k, valor in esperado["ficha"].items() if k not in {"entidades", "necessita_revisao"} and ficha.get(k) != valor]
        entidades_fonte = ficha["entidades"]
        omissoes, incorretas = [], []
        for tipo, valores in esperado["ficha"]["entidades"].items():
            omissoes.extend({"tipo": tipo, "valor": valor} for valor in valores if valor not in entidades_fonte[tipo])
            incorretas.extend({"tipo": tipo, "valor": valor} for valor in entidades_fonte[tipo] if valor not in valores)
        resumo = analise["resumo"].casefold()
        fatos_omitidos = [fato for fato in esperado["fatos_essenciais"] if fato.casefold() not in resumo]
        casos.append({"id": caso_id, "categoria_correta": correta, "campos_divergentes": campos,
                      "entidades_omitidas": omissoes, "entidades_incorretas": incorretas,
                      "fatos_essenciais_omitidos": fatos_omitidos,
                      "fatos_sem_suporte": [], "revisao_humana": "pendente"})
    total = len(casos)
    return {"categorias_corretas": categorias_corretas, "total": total,
            "acuracia_categoria": categorias_corretas / total if total else None, "casos": casos}
