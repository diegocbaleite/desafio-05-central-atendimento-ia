"""RAG conservador: toda afirmação institucional exibida é um trecho literal.

O modelo seleciona as passagens; o código confere origem, texto, relevância
lexical mínima e conflitos antes de formar a minuta pendente de revisão.
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import date, datetime
from pathlib import Path

import jsonschema

from ..seguranca import delimitar, minimizar
from .indice import IndiceDesatualizado
from .contratos import CAMPOS, ErroContrato, esquema_analise, validar_analise

VERSAO_PROMPT = "rag-extrativo-1.0"
STATUS = ("fundamentada", "sem evidência suficiente", "conflito de fontes")
ESQUEMA_RAG = {
    "type": "object", "additionalProperties": False,
    "required": ["status", "afirmacoes"],
    "properties": {
        "status": {"type": "string", "enum": list(STATUS)},
        "afirmacoes": {"type": "array", "maxItems": 5, "items": {
            "type": "object", "additionalProperties": False,
            "required": ["chunk_id", "trecho"],
            "properties": {"chunk_id": {"type": "string"}, "trecho": {"type": "string", "minLength": 1}},
        }},
    },
}

_VAZIAS = {
    "a", "o", "as", "os", "um", "uma", "de", "da", "do", "das", "dos", "e", "em", "no", "na", "nos", "nas",
    "que", "qual", "quais", "como", "para", "por", "com", "se", "ao", "aos", "eu", "meu", "minha", "preciso",
    "onde", "ser", "pode", "posso", "sao", "saber", "sobre", "deve", "fazer", "solicito", "gostaria",
    "documento", "documentos", "ficticio", "ficticios", "exercicio", "institucional", "versao",
    "solicitar", "solicitacao", "solicitado",
}


def _termos(texto):
    sem_acentos = "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if not unicodedata.combining(c))
    # Stemming deliberadamente simples; não é evidência semântica nem score calibrado.
    return {("agend" if p.startswith("agend") else p[:7]) for p in re.findall(r"[a-z0-9]+", sem_acentos) if len(p) > 2 and p not in _VAZIAS}


def _fonte(item, trecho=None):
    return {"documento_id": item["documento_id"], "titulo": item["titulo"], "versao": item["versao"],
            "arquivo": item["metadata"].get("arquivo"),
            "chunk_id": item["chunk_id"], "pagina": item["pagina"], "secao": item["secao"],
            "sha256": item["sha256"], "trecho": trecho or item["texto"],
            "similaridade": item.get("similaridade")}


def _conflitos(trechos):
    grupos = {}
    for t in trechos:
        meta = t["metadata"]
        if not meta.get("conflito"):
            continue
        grupo = meta.get("grupo_politica", meta.get("conflito_grupo"))
        if grupo:
            grupos.setdefault(grupo, {})[t["documento_id"]] = t
    conflitos, preferidos = [], {}
    for grupo, docs in grupos.items():
        if len(docs) < 2:
            continue
        # Uma prioridade só resolve o conflito se documentada em todos os membros,
        # inequívoca e acompanhada de vigência expressa. Nenhuma data é presumida.
        candidatos = list(docs.values())
        prioridades = [t["metadata"].get("prioridade") for t in candidatos]
        if all(isinstance(p, (int, float)) and not isinstance(p, bool) for p in prioridades) and all(_vigencia_ativa(t["metadata"].get("vigencia")) for t in candidatos):
            maior = max(prioridades)
            vencedores = [t for t in candidatos if t["metadata"]["prioridade"] == maior]
            if len(vencedores) == 1:
                preferidos[grupo] = vencedores[0]["documento_id"]
                continue
        conflitos.extend(candidatos)
    return conflitos, preferidos


def _vigencia_ativa(valor):
    """Strings vagas não demonstram vigência; intervalo explícito é obrigatório."""
    if not isinstance(valor, dict) or set(valor) != {"inicio", "fim"}:
        return False
    try:
        inicio = date.fromisoformat(valor["inicio"])
        fim = date.fromisoformat(valor["fim"]) if valor["fim"] is not None else date.max
    except (TypeError, ValueError):
        return False
    return inicio <= date.today() <= fim


def _satisfaz_pedido_especifico(pergunta, trecho):
    """Barreira conservadora de completude para prazo ou valor quantitativos.

    Uma frase sobre o tema pode ser verdadeira sem conter a informação pedida.
    A ausência do dado solicitado obriga abstenção, mesmo havendo citação literal.
    """
    q = "".join(c for c in unicodedata.normalize("NFD", pergunta.casefold()) if not unicodedata.combining(c))
    t = "".join(c for c in unicodedata.normalize("NFD", trecho.casefold()) if not unicodedata.combining(c))
    pede_prazo = bool(re.search(r"(?:qual|quant[oa]s?).{0,25}(?:prazo|dias|meses|horas)|ate quando", q))
    pede_valor = bool(re.search(r"quanto custa|qual.{0,20}(?:valor|taxa|preco)|valor da taxa", q))
    numero = r"(?:\d+(?:[.,]\d+)?|um|uma|dois|duas|tres|quatro|cinco|seis|sete|oito|nove|dez|quinze|trinta)"
    if pede_prazo and not re.search(rf"\b{numero}\s+(?:dia|dias|mes|meses|hora|horas|semana|semanas)\b|\b\d{{1,2}}/\d{{1,2}}/\d{{4}}\b", t):
        return False
    if pede_valor and not re.search(rf"r\$\s*\d|\b{numero}\s+(?:real|reais)\b", t):
        return False
    return True


def _passagem_completa(literal, original):
    """Recortes de uma oração podem inverter negações ou remover condições."""
    if literal == original.strip():
        return True
    def sem_cabecalhos(texto):
        linhas = [l.strip() for l in texto.splitlines() if l.strip() and not
                  re.match(r"^\s*(?:#|Se[cç][aã]o\s*:)", l, re.IGNORECASE)]
        return " ".join(" ".join(linhas).split())
    fonte, citado = sem_cabecalhos(original), sem_cabecalhos(literal)
    frases = re.split(r"(?<=[.!?])\s+", fonte)
    citadas = re.split(r"(?<=[.!?])\s+", citado)
    return bool(citado) and any(frases[inicio:inicio + len(citadas)] == citadas
                               for inicio in range(len(frases)))


def _validar_solicitacao(solicitacao, original=None):
    """Flags recebidas não substituem esquema nem validação das regras locais."""
    esquema = esquema_analise()
    esquema["properties"].update({
        "modalidade": {"type": "string", "enum": ["texto", "audio", "imagem", "ocr"]},
        "conferencia_humana": {"type": "boolean"},
        "apta_para_minuta": {"type": "boolean"},
        "tentativas_validacao": {"type": "integer", "minimum": 1, "maximum": 2},
    })
    esquema["required"] += ["modalidade", "conferencia_humana", "apta_para_minuta", "tentativas_validacao"]
    try:
        jsonschema.Draft202012Validator(esquema).validate(solicitacao)
    except jsonschema.ValidationError as exc:
        raise ErroContrato("Ficha recebida pelo RAG incompatível com esquema: " + str(exc.validator)) from exc
    if solicitacao["modalidade"] != "texto" and solicitacao["conferencia_humana"] is not True:
        raise PermissionError("Dados críticos STT/OCR exigem conferência humana antes da minuta")
    if solicitacao["apta_para_minuta"] is not True:
        raise ErroContrato("Ficha recebida não está apta para minuta")
    ficha = solicitacao["ficha"]
    ausentes = [campo for campo in CAMPOS if ficha[campo] is None]
    if set(ausentes) != set(ficha["campos_ausentes"]):
        raise ErroContrato("Campos ausentes incoerentes na ficha recebida pelo RAG")
    if (ausentes or ficha["categoria"] in {"outros", "revisao"}) and not ficha["necessita_revisao"]:
        raise ErroContrato("Lacunas ou categoria incerta exigem revisão")
    if ficha["data"] is not None:
        try:
            datetime.strptime(ficha["data"], "%d/%m/%Y")
        except ValueError as exc:
            raise ErroContrato("Data impossível na ficha recebida pelo RAG") from exc
    if len(solicitacao["resumo"].split()) > 100:
        raise ErroContrato("Resumo excede 100 palavras")
    if original is not None:
        if not isinstance(original, str) or not original.strip():
            raise ErroContrato("Original da solicitação ausente ou inválido")
        validar_analise({k: solicitacao[k] for k in ("ficha", "resumo", "inferencias")}, original)


def responder(pergunta, indice, cliente, solicitacao=None, *, original=None):
    """Não lê gabaritos; nunca aprova nem envia respostas automaticamente."""
    from .guardrails import avaliar_entrada, validar_saida

    if solicitacao is not None:
        _validar_solicitacao(solicitacao, original)
    estado = indice.estado()
    resultado = {
        "status": "sem evidência suficiente", "resposta": "Não foi localizada evidência suficiente no acervo. Encaminhar para revisão humana.",
        "fontes": [], "trechos_recuperados": [], "afirmacoes": [],
        "requer_revisao_humana": True, "estado_revisao": "pendente",
        "versao_prompt": VERSAO_PROMPT, "versao_indice": estado["versao_indice"],
        "participacao_ia": True, "envio_automatico": False,
        "simulado": bool(getattr(cliente, "simulado", False)),
        "consulta_minimizada": minimizar(pergunta) if isinstance(pergunta, str) else "",
    }
    protecao = avaliar_entrada(pergunta)
    if protecao["decisao"] != "permitir":
        resultado.update({"bloqueado": True, "motivos": protecao["motivos"]})
        return resultado
    if estado["desatualizado"]:
        raise IndiceDesatualizado("Índice desatualizado; reindexe antes de gerar a minuta")
    trechos = indice.buscar(pergunta)
    termos = _termos(pergunta)
    # A barreira lexical evita que a mera existência de um vizinho vetorial seja
    # tratada como evidência. A avaliação por gabarito mede as limitações restantes.
    relevantes = [t for t in trechos if termos & _termos(t["texto"])]
    # Metadados de conflito se aplicam a uma política, não a toda pergunta que
    # compartilhe vocabulário administrativo genérico com seus documentos.
    relevantes = [t for t in relevantes if not t["metadata"].get("conflito") or
                  termos & _termos(str(t["metadata"].get("grupo_politica", t["metadata"].get("conflito_grupo", ""))).replace("_", " "))]
    resultado["trechos_recuperados"] = [_fonte(t) for t in trechos]
    if not relevantes:
        return resultado
    relevantes = indice.completar_conflitos(relevantes)
    for trecho in relevantes:
        protecao = avaliar_entrada(trecho["texto"], contexto=True)
        if protecao["decisao"] != "permitir":
            resultado.update({"bloqueado": True, "motivos": ["Conteúdo recuperado exige revisão; geração interrompida."]})
            return resultado
    conflitos, preferidos = _conflitos(relevantes)
    if conflitos:
        resultado.update({"status": "conflito de fontes", "resposta": "Foram localizadas orientações conflitantes sem precedência suficiente. Encaminhar para revisão humana.",
                          "fontes": [_fonte(t) for t in conflitos]})
        return resultado
    if preferidos:
        relevantes = [t for t in relevantes if not t["metadata"].get("conflito") or t["documento_id"] == preferidos.get(t["metadata"].get("grupo_politica", t["metadata"].get("conflito_grupo")))]
    prompt = (Path(__file__).resolve().parents[2] / "prompts/desafio6/rag.md").read_text(encoding="utf-8")
    contexto = [{"chunk_id": t["chunk_id"], "documento_id": t["documento_id"], "versao": t["versao"],
                 "pagina": t["pagina"], "secao": t["secao"], "texto": t["texto"]} for t in relevantes]
    conteudo = json.dumps({"pergunta": minimizar(pergunta), "fatos_solicitacao": solicitacao,
                           "contexto_documental": contexto}, ensure_ascii=False)
    bruto = cliente.gerar_json(prompt, delimitar(conteudo), ESQUEMA_RAG, nome="resposta_rag")
    jsonschema.validate(bruto, ESQUEMA_RAG)
    if bruto["status"] != "fundamentada":
        # O modelo não declara sozinho um conflito novo nem confirma uma fonte.
        return resultado
    por_id = {t["chunk_id"]: t for t in relevantes}
    fontes, afirmacoes = [], []
    for afirmacao in bruto["afirmacoes"]:
        origem = por_id.get(afirmacao["chunk_id"])
        literal = afirmacao["trecho"].strip()
        if not origem or not literal or literal not in origem["texto"]:
            resultado.update({"bloqueado": True, "motivos": ["Afirmação sem passagem literal correspondente; saída bloqueada."]})
            return resultado
        if not _passagem_completa(literal, indice.texto_original(origem["chunk_id"])):
            resultado.update({"bloqueado": True, "motivos": ["Citação recorta uma frase e pode omitir negação ou condição; saída bloqueada."]})
            return resultado
        if not termos & _termos(literal):
            resultado.update({"bloqueado": True, "motivos": ["Passagem sem correspondência lexical com a pergunta; revisão necessária."]})
            return resultado
        if not _satisfaz_pedido_especifico(pergunta, literal):
            resultado.update({"motivos": ["A passagem não contém o prazo/valor quantitativo solicitado; evidência insuficiente."]})
            return resultado
        protecao = validar_saida(literal)
        if protecao["decisao"] != "permitir":
            resultado.update({"bloqueado": True, "motivos": ["Saída institucional reprovada pelos guardrails."]})
            return resultado
        fonte = _fonte(origem, literal)
        fontes.append(fonte)
        afirmacoes.append({"texto": literal, "chunk_id": origem["chunk_id"], "sustentada": True,
                           "metodo_verificacao": "passagem literal idêntica à fonte; seleção temática sujeita à revisão humana"})
    if not afirmacoes:
        return resultado
    resposta = "MINUTA — NÃO ENVIADA\n\n" + "\n\n".join(a["texto"] for a in afirmacoes)
    resposta += "\n\nConteúdo preparado com auxílio de IA. Revisão humana pendente."
    resultado.update({"status": "fundamentada", "resposta": resposta, "fontes": fontes, "afirmacoes": afirmacoes,
                      "limite_verificacao": "A correspondência literal sustenta a citação, mas relevância/completude da resposta exigem conferência humana."})
    return resultado
