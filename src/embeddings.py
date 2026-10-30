"""Embeddings da recuperação (RF17), separados da geração (RF21).

- `fastembed`: modelo aberto local em ONNX; o acervo não é enviado a terceiros.
- `hash_teste`: saco-de-palavras com hashing, determinístico e SOMENTE para testes
  automatizados (não é modelo semântico e não deve ser usado em avaliação).
"""

from __future__ import annotations

import hashlib
import math

from .texto import termos


class EmbedderFastEmbed:
    tipo = "fastembed"

    def __init__(self, modelo: str):
        self.nome = modelo
        self._modelo = None
        self.dimensao = None

    def _carregar(self):
        if self._modelo is None:
            from fastembed import TextEmbedding

            self._modelo = TextEmbedding(self.nome)
        return self._modelo

    def embed(self, textos: list[str]) -> list[list[float]]:
        vetores = []
        for v in self._carregar().embed(list(textos)):
            norma = math.sqrt(float((v * v).sum())) or 1.0
            vetores.append([float(x) / norma for x in v])
        if vetores:
            self.dimensao = len(vetores[0])
        return vetores


class EmbedderHash:
    """Determinístico, sem download; usado apenas pelos testes unitários."""

    tipo = "hash_teste"

    def __init__(self, nome: str = "hash-bow-teste-v1", dimensao: int = 256):
        self.nome = nome
        self.dimensao = dimensao

    def embed(self, textos: list[str]) -> list[list[float]]:
        saida = []
        for texto in textos:
            v = [0.0] * self.dimensao
            for t in termos(texto):
                v[int(hashlib.md5(t.encode()).hexdigest(), 16) % self.dimensao] += 1.0
            norma = math.sqrt(sum(x * x for x in v)) or 1.0
            saida.append([x / norma for x in v])
        return saida


def criar_embedder(cfg: dict):
    r = cfg.get("recuperacao", {})
    provider = r.get("embedding_provider", "fastembed")
    if provider == "fastembed":
        return EmbedderFastEmbed(r["embedding_modelo"])
    if provider == "hash_teste":
        return EmbedderHash(r.get("embedding_modelo", "hash-bow-teste-v1"))
    raise ValueError("Provedor de embedding desconhecido: " + provider)
