"""Normalização de texto compartilhada por NLP, RAG, guardrails e sentimentos."""

from __future__ import annotations

import re
import unicodedata

# Palavras sem conteúdo informativo para a busca (inclui verbos de pedido e de pergunta).
STOPWORDS = set(
    """
    a o as os um uma uns umas de da do das dos em na no nas nos por para pra pelo pela
    pelos pelas com sem sob sobre entre ate e ou mas que se ao aos a as la lo isso isto
    esse essa este esta aquele aquela aquilo eu tu ele ela nos vos eles elas me te lhe
    meu minha meus minhas seu sua seus suas nosso nossa voce voces qual quais quanto
    quanta quantos quantas quando onde como porque qual e sao ser foi era tem ter ha
    devo deve posso pode podem preciso precisa gostaria quero queria solicito peco
    favor informar informem informe saber ainda ja mais muito muita bem tambem so
    apenas outro outra algum alguma cada todo toda todos todas nao sim vou vai
    obrigado obrigada oi ola bom boa dia tarde noite prezados atenciosamente
    """.split()
)


def sem_acento(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalizar(texto: str) -> str:
    """Minúsculas, sem acento e com espaços simples (para comparar trechos literais)."""
    return re.sub(r"\s+", " ", sem_acento(texto).lower()).strip()


def contem(texto: str, trecho: str) -> bool:
    return normalizar(trecho) in normalizar(texto)


def raiz(palavra: str) -> str:
    """Radical simplificado (5 primeiros caracteres) para casar flexões em português."""
    p = sem_acento(palavra.lower())
    if len(p) > 4 and p.endswith("s"):
        p = p[:-1]
    return p[:5]


def termos(texto: str) -> list[str]:
    """Radicais das palavras de conteúdo (>= 3 letras ou números)."""
    saida = []
    for token in re.findall(r"[A-Za-zÀ-ÿ0-9]+", texto):
        base = sem_acento(token.lower())
        if base.isdigit():
            saida.append(base)
        elif len(base) >= 3 and base not in STOPWORDS:
            saida.append(raiz(base))
    return saida


def frases(texto: str) -> list[str]:
    """Divide em frases sem quebrar números decimais nem listas separadas por ';'."""
    texto = re.sub(r"\s+", " ", texto).strip()
    partes = re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9])", texto)
    return [p.strip() for p in partes if p.strip()]


def contar_palavras(texto: str) -> int:
    return len(re.findall(r"\S+", texto or ""))


# Quantidades com unidade (prazos, horas, valores): base para detectar conflito e invenção.
_QUANTIDADE = re.compile(
    r"(?P<num>\d+(?:[.,]\d+)?)\s*(?:\([^)]*\)\s*)?"
    r"(?P<unidade>dias? [uú]teis|dias? corridos|dias?|horas?|h\b|meses|m[eê]s|anos?|semestres?|%|reais)"
    r"|R\$\s*(?P<valor>\d+(?:[.,]\d+)?)",
    re.IGNORECASE,
)
_NUM_EXTENSO = {
    "um": "1", "uma": "1", "dois": "2", "duas": "2", "tres": "3", "quatro": "4",
    "cinco": "5", "seis": "6", "sete": "7", "oito": "8", "nove": "9", "dez": "10",
}


def quantidades(texto: str) -> set[tuple[str, str]]:
    """Pares (número, unidade normalizada), ex.: {("15", "dias uteis")}."""
    achados = set()
    base = sem_acento(texto.lower())
    for m in _QUANTIDADE.finditer(base):
        if m.group("valor"):
            achados.add((m.group("valor").replace(",", "."), "reais"))
            continue
        unidade = m.group("unidade")
        unidade = re.sub(r"^dia ", "dias ", unidade)
        unidade = {"dia": "dias", "hora": "horas", "h": "horas", "mes": "meses",
                   "ano": "anos", "semestre": "semestres"}.get(unidade, unidade)
        achados.add((m.group("num").replace(",", "."), unidade))
    for m in re.finditer(r"\b(" + "|".join(_NUM_EXTENSO) + r")\s+(dias? uteis|dias?|horas?)\b", base):
        unidade = m.group(2)
        unidade = {"dia": "dias", "hora": "horas"}.get(unidade, re.sub(r"^dia ", "dias ", unidade))
        achados.add((_NUM_EXTENSO[m.group(1)], unidade))
    return achados


def numeros(texto: str) -> set[str]:
    return set(re.findall(r"\d+(?:[.,]\d+)?", texto))
