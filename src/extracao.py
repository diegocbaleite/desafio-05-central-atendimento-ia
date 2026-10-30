"""Extração conservadora com proveniência por campo."""

import re
from datetime import datetime

from .seguranca import AUSENTE, detectar

_NOME = r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÀ-ÿ]*"
_DATA = r"\b(\d{2}/\d{2}/20\d{2})\b"
_DATA_EXTENSO = re.compile(
    r"\b(\d{1,2})\s+de\s+"
    r"(janeiro|fevereiro|março|marco|abril|maio|junho|julho|agosto|"
    r"setembro|outubro|novembro|dezembro)\s+de\s+(20\d{2})\b",
    re.IGNORECASE,
)
_MESES = {
    "janeiro": 1,
    "fevereiro": 2,
    "março": 3,
    "marco": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}
CAMPOS = {
    "protocolo": (
        r"(?:(?:protocolo|processo)\s*(?:n[ºo.]*)?\s*(?:é|[:#-])?"
        r"|c[oó]digo\s*[:#-]?)\s*"
        r"(20\d{2}\s*[.-]\s*\d{3}[-.\s]?\s*\d{3})"
    ),
    # (?-i:...) mantém o nome case-sensitive; [ \t] evita atravessar linhas.
    "solicitante": (
        r"(?:^[ \t]*nome[ \t]*:[ \t]*|meu nome é[ \t]*"
        r"|nome[ \t]*:[ \t]*)((?-i:"
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
PEDIDO_LIVRE = (
    r"\b(?:(?:não|nao|nunca|jamais|somente|apenas)\s+)*"
    r"(?:solicito|solicitamos|peço|gostaria de|quero pedir|quero solicitar)"
    r"\b(?:(?![!?;\n]|\.(?!\d)).)+"
)


def _grupo(m):
    return next((g for g in m.groups() if g), None) if m else None


def _normalizar_data(match, por_extenso=False):
    if por_extenso:
        dia, mes, ano = match.groups()
        numero_mes = _MESES[mes.lower()]
        texto = f"{int(dia):02d}/{numero_mes:02d}/{ano}"
    else:
        texto = match.group(1)
    try:
        return datetime.strptime(texto, "%d/%m/%Y").strftime("%d/%m/%Y")
    except ValueError:
        return None


def _datas(texto):
    datas = []
    for m in re.finditer(_DATA, texto):
        valor = _normalizar_data(m)
        if valor:
            datas.append((m.start(), m.end(), valor, m.group(0)))
    for m in _DATA_EXTENSO.finditer(texto):
        valor = _normalizar_data(m, por_extenso=True)
        if valor:
            datas.append((m.start(), m.end(), valor, m.group(0)))
    return sorted(datas)


def _data_solicitacao(texto):
    """Prefere data rotulada; no fallback ignora datas de nascimento."""
    rotulo = re.search(
        r"\bdata(?:\s+da\s+solicita[çc][ãa]o|"
        r"\s+(?:de\s+)?matr[ií]cula)?[ \t]*:[ \t]*",
        texto,
        re.IGNORECASE | re.MULTILINE,
    )
    datas = _datas(texto)
    if rotulo:
        for inicio, fim, valor, _ in datas:
            if inicio >= rotulo.end() and not texto[rotulo.end() : inicio].strip():
                return valor, texto[rotulo.start() : fim], "alta"
    for inicio, _, valor, evidencia in datas:
        if "nasc" not in texto[max(0, inicio - 40) : inicio].lower():
            return valor, evidencia, "media"
    return None, None, "baixa"


def _assunto_pelo_pedido(pedidos):
    for pedido in pedidos:
        sem_abertura = re.sub(
            r"^\s*(?:solicito|solicitamos|peço|gostaria de|quero pedir|quero solicitar)\b\s*",
            "",
            pedido.group(0),
            count=1,
            flags=re.IGNORECASE,
        )
        candidato = sem_abertura.split(",", 1)[0].strip()
        if any(
            termo in candidato.lower()
            for termos in CATEGORIAS.values()
            for termo in termos
        ):
            return re.sub(
                r"^(?:a|o|as|os|um|uma)\s+",
                "",
                candidato,
                flags=re.IGNORECASE,
            )
    return None


def extrair(texto, caso_id, origem, sha256, modalidade):
    pedidos = list(re.finditer(PEDIDO_LIVRE, texto, re.IGNORECASE))
    campos = {}
    for nome, padrao in CAMPOS.items():
        m = re.search(
            padrao,
            texto,
            re.IGNORECASE | (re.MULTILINE if nome == "solicitante" else 0),
        )
        valor = _grupo(m)
        if nome == "protocolo" and valor:
            partes = re.fullmatch(
                r"(20\d{2})\s*([.-])\s*(\d{3})[-.\s]?\s*(\d{3})",
                valor,
                re.IGNORECASE,
            )
            if partes:
                valor = (
                    f"{partes.group(1)}{partes.group(2)}"
                    f"{partes.group(3)}{partes.group(4)}"
                )
        campos[nome] = {
            "valor": valor.strip() if valor else AUSENTE,
            "evidencia": m.group(0) if m and valor else None,
            "confianca": "alta" if valor else "baixa",
        }
    valor, evidencia, confianca = _data_solicitacao(texto)
    campos["data_solicitacao"] = {
        "valor": valor if valor else AUSENTE,
        "evidencia": evidencia if valor else None,
        "confianca": confianca,
    }
    for nome in ("assunto", "pedido"):
        m = re.search(r"(?im)^\s*" + nome + r"\s*:\s*(.+)$", texto)
        confianca = "alta"
        valor_livre = None
        evidencia_livre = None
        if not m and nome == "assunto":
            valor_livre = _assunto_pelo_pedido(pedidos)
            confianca = "media"
        elif not m and nome == "pedido" and pedidos:
            valor_livre = "; ".join(p.group(0).strip() for p in pedidos)
            evidencia_livre = "\n".join(p.group(0).strip() for p in pedidos)
            confianca = "media"
        if m:
            valor = m.group(1).strip()
            evidencia = m.group(0).strip()
        elif valor_livre:
            valor = valor_livre
            evidencia = evidencia_livre or valor_livre
        else:
            valor = AUSENTE
            evidencia = None
        campos[nome] = {
            "valor": valor,
            "evidencia": evidencia,
            "confianca": confianca if m or valor_livre else "baixa",
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
