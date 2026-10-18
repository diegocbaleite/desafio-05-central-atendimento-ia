"""Extração conservadora com proveniência por campo."""

import re

from .seguranca import AUSENTE, detectar

_NOME = r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÀ-ÿ]*"
_DATA = r"\b(\d{2}/\d{2}/20\d{2})\b"
CAMPOS = {
    "protocolo": r"(?:protocolo|processo)\s*(?:n[ºo.]*)?\s*(?:é|[:#-])?\s*(20\d{2}[.-]\d{6})",
    # (?-i:...) mantém o nome case-sensitive; [ \t] evita atravessar linhas.
    "solicitante": (
        r"(?:nome|meu nome é)[ \t]*:?[ \t]*((?-i:"
        + _NOME
        + r"(?:[ \t]+(?:(?:de|da|do|dos|das|e)[ \t]+)?"
        + _NOME
        + r"){1,5}))"
    ),
}
# Categorias documentadas; a ordem define a precedência na classificação.
CATEGORIAS = {
    "segunda_via_documento": ("segunda via", "certidão"),
    "andamento_processo": ("andamento", "acompanhar"),
    "atualizacao_cadastral": ("atualização cadastral", "atualizar cadastro"),
    "agendamento": ("agendar", "remarcar", "agendamento"),
    "reclamacao": ("reclamação", "reclamar"),
    "efetivacao_matricula": ("matrícula", "matricula"),
}
# Fallback conservador quando não há rótulo "Pedido:" na solicitação.
PEDIDO_LIVRE = r"\b((?:solicito|solicitamos|peço|gostaria de)\b[^.\n]{5,200})"


def _grupo(m):
    return next((g for g in m.groups() if g), None) if m else None


def _data_solicitacao(texto):
    """Prefere data rotulada; no fallback ignora datas de nascimento. Devolve (match, confiança)."""
    rotulada = re.search(
        r"\bdata(?:\s+da\s+solicita[çc][ãa]o|\s+matr[ií]cula)?\s*:\s*" + _DATA,
        texto,
        re.IGNORECASE,
    )
    if rotulada:
        return rotulada, "alta"
    for m in re.finditer(_DATA, texto):
        if "nasc" not in texto[max(0, m.start() - 40) : m.start()].lower():
            return m, "media"
    return None, "baixa"


def extrair(texto, caso_id, origem, sha256, modalidade):
    campos = {}
    for nome, padrao in CAMPOS.items():
        m = re.search(padrao, texto, re.IGNORECASE)
        valor = _grupo(m)
        campos[nome] = {
            "valor": valor.strip() if valor else AUSENTE,
            "evidencia": m.group(0) if valor else None,
            "confianca": "alta" if valor else "baixa",
        }
    m, confianca = _data_solicitacao(texto)
    valor = _grupo(m)
    campos["data_solicitacao"] = {
        "valor": valor if valor else AUSENTE,
        "evidencia": m.group(0) if valor else None,
        "confianca": confianca,
    }
    for nome in ("assunto", "pedido"):
        m = re.search(r"(?im)^\s*" + nome + r"\s*:\s*(.+)$", texto)
        confianca = "alta"
        if not m and nome == "pedido":
            m = re.search(PEDIDO_LIVRE, texto, re.IGNORECASE)
            confianca = "media"
        campos[nome] = {
            "valor": m.group(1).strip() if m else AUSENTE,
            "evidencia": m.group(0).strip() if m else None,
            "confianca": confianca if m else "baixa",
        }
    baixo = texto.lower()
    categoria = "outros"
    # O pedido explícito tem precedência sobre o objeto mencionado.
    base = (
        campos["pedido"]["valor"] if campos["pedido"]["valor"] != AUSENTE else baixo
    ).lower()
    for nome, termos in CATEGORIAS.items():
        if any(t in base for t in termos):
            categoria = nome
            break
    if categoria == "outros":
        for nome, termos in CATEGORIAS.items():
            if any(t in baixo for t in termos):
                categoria = nome
                break
    ausentes = [k for k, v in campos.items() if v["valor"] == AUSENTE]
    achados = detectar(texto)
    return {
        "versao_schema": "1.0",
        "caso_id": caso_id,
        "fonte": {
            "arquivo": origem,
            "sha256": sha256,
            "modalidade": modalidade,
            "texto_fonte": origem,
        },
        "campos": campos,
        "categoria": {
            "codigo": categoria,
            "justificativa": "Palavras-chave da solicitação",
        },
        "campos_ausentes": ausentes,
        "alerta_injecao": bool(achados),
        "achados_injecao": achados,
        "requer_revisao": True,
        "motivos_revisao": ["Conferir campos críticos"]
        + (["Suspeita de instrução maliciosa"] if achados else []),
        "confianca_geral": "baixa" if ausentes else "alta",
    }
