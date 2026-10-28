"""Distribuição determinística e exclusão explícita de segredos/arquivos locais."""

import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from src.desafio6 import pacote


class TestPacoteDesafio6(unittest.TestCase):
    def test_pacote_reproduzivel_sem_env_e_inclui_documento_fornecido(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            (raiz / "README.md").write_text("Dados fictícios", encoding="utf-8")
            (raiz / ".env").write_text("OPENAI_API_KEY=credencial-local-ficticia", encoding="utf-8")
            (raiz / ".env.example").write_text("OPENAI_API_KEY=", encoding="utf-8")
            (raiz / "dados/originais").mkdir(parents=True)
            (raiz / "dados/originais/edital_real.pdf").write_bytes(b"nao incluir")
            with patch.object(pacote, "ROOT", raiz):
                a = pacote.empacotar(raiz / "a.zip")
                b = pacote.empacotar(raiz / "b.zip")
            self.assertEqual(hashlib.sha256(a.read_bytes()).digest(), hashlib.sha256(b.read_bytes()).digest())
            with zipfile.ZipFile(a) as arquivo:
                self.assertNotIn(".env", arquivo.namelist())
                self.assertIn(".env.example", arquivo.namelist())
                self.assertIn("dados/originais/edital_real.pdf", arquivo.namelist())
