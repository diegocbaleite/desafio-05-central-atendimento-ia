"""Extração conservadora com proveniência por campo."""

import re

from .seguranca import AUSENTE, detectar

CAMPOS = {
    "protocolo": r"(?:protocolo|processo)\s*(?:n[ºo.]*)?\s*[:#-]?\s*(20\d{2}\.\d{6})",
    "data_solicitacao": r"\b(\d{2}/\d{2}/20\d{2})\b",
    "solicitante": r"(?:nome|meu nome é)\s*:?\s*([A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÀ-ÿ]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÀ-ÿ]+){1,4})",
}
CATEGORIAS = {
    "segunda_via_documento": ("segunda via", "certidão"),
    "andamento_processo": ("andamento", "acompanhar"),
    "atualizacao_cadastral": ("atualização cadastral", "atualizar cadastro"),
    "agendamento": ("agendar", "remarcar", "agendamento"),
    "reclamacao": ("reclamação", "reclamar"),
}


def extrair(texto, caso_id, origem, sha256, modalidade):
    campos = {}
    for nome, padrao in CAMPOS.items():
        m = re.search(padrao, texto, re.IGNORECASE)
        campos[nome] = {
            "valor": m.group(1).strip() if m else AUSENTE,
            "evidencia": m.group(0) if m else None,
            "confianca": "alta" if m else "baixa",
        }
    for nome in ("assunto", "pedido"):
        m = re.search(r"(?im)^\s*" + nome + r"\s*:\s*(.+)$", texto)
        campos[nome] = {
            "valor": m.group(1).strip() if m else AUSENTE,
            "evidencia": m.group(0) if m else None,
            "confianca": "alta" if m else "baixa",
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
