"""Prompts versionados do Desafio 6: arquivo + SHA-256 entram na auditoria (RF21)."""

from __future__ import annotations

import hashlib

from .config import ROOT

PASTA = "prompts/d6"


def carregar_prompt(nome: str) -> dict:
    caminho = ROOT / PASTA / f"{nome}.md"
    texto = caminho.read_text(encoding="utf-8")
    return {
        "nome": nome,
        "arquivo": f"{PASTA}/{nome}.md",
        "texto": texto,
        "sha256": hashlib.sha256(texto.encode("utf-8")).hexdigest(),
    }
