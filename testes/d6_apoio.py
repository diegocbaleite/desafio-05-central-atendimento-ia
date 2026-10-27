"""Apoio aos testes do Desafio 6: índice temporário com embedding determinístico de teste."""

import copy
import tempfile
from pathlib import Path

from src.config import carregar
from src.embeddings import EmbedderHash
from src.indice import IndiceVetorial
from src.ingestao import carregar_catalogo


def cfg_teste():
    cfg = copy.deepcopy(carregar())
    # O embedding de teste não é semântico: o limiar de similaridade fica em 0 e a
    # abstenção depende só da cobertura de termos.
    cfg["recuperacao"]["limiar_similaridade"] = 0.0
    return cfg


class IndiceTemporario:
    def __init__(self, rotulo="A", catalogo=None, embedder=None):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.pasta = Path(self._tmp.name)
        self.cfg = cfg_teste()
        self.catalogo = catalogo if catalogo is not None else carregar_catalogo(self.cfg, incluir_enviados=False)
        self.embedder = embedder or EmbedderHash()
        self.indice = IndiceVetorial.de_config(self.cfg, self.embedder, rotulo, diretorio=self.pasta / "indice")

    def reabrir(self, embedder=None, rotulo="A"):
        return IndiceVetorial.de_config(self.cfg, embedder or self.embedder, rotulo, diretorio=self.pasta / "indice")

    def fechar(self):
        self._tmp.cleanup()
