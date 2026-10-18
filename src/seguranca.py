"""Conteúdo externo é dado não confiável, jamais instrução."""

import re

AUSENTE = "não localizado"
PADROES = [
    r"ignore.{0,80}(instruções|instrucoes|regras|instructions|rules|previous|prior)",
    r"disregard.{0,80}(instructions|rules|previous|prior)",
    r"(^|\n)\s*(sistema|system)\s*:",
    r"revele.{0,50}(prompt|segredo|chave)",
    r"reveal.{0,60}(prompt|system|secret|key)",
    r"(?i)deferido.{0,35}(prazo|dias)",
    r"desconsidere.{0,60}(instruções|instrucoes|regras)",
]


def detectar(texto):
    return [p for p in PADROES if re.search(p, texto, re.IGNORECASE)]


def delimitar(texto):
    texto = re.sub(
        r"</?conteudo_externo[^>]*>",
        "[tag externa neutralizada]",
        texto,
        flags=re.IGNORECASE,
    )
    return "<conteudo_externo>\n" + texto + "\n</conteudo_externo>"


def minimizar(texto):
    texto = re.sub(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b", "[CPF]", texto)
    texto = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[EMAIL]", texto)
    texto = re.sub(r"\(?\d{2}\)?\s?9\d{4}-?\d{4}", "[TELEFONE]", texto)
    return texto
