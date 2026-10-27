"""RF20: a interface Streamlit carrega, indexa e registra decisão humana (teste headless)."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from streamlit.testing.v1 import AppTest
except ImportError:  # streamlit é dependência do Desafio 6
    AppTest = None

from src.config import ROOT


@unittest.skipIf(AppTest is None, "streamlit não instalado")
class TestApp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        base = Path(self.tmp.name)
        self.env = patch.dict(os.environ, {
            "D6_EMBEDDING_PROVIDER": "hash_teste",
            "D6_DIR_INDICE": str(base / "indice"),
            "D6_BANCO_REVISAO": str(base / "rev.sqlite3"),
            "D6_ARQUIVO_AUDITORIA": str(base / "aud.jsonl"),
        })
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_fluxo_minimo_na_interface(self):
        at = AppTest.from_file(str(ROOT / "src" / "app.py"), default_timeout=120)
        at.run()
        self.assertFalse(at.exception, at.exception)
        self.assertIn("Índice vazio", " ".join(w.value for w in at.warning))
        at.button[0].click().run()  # Indexar acervo
        self.assertFalse(at.exception, at.exception)
        # Processa uma solicitação digitada e verifica a minuta pendente.
        at.text_area[0].set_value(
            "Nome: Maria Fictícia Albuquerque\nProtocolo: 2026.000123\nData: 02/10/2026\n"
            "Assunto: segunda via de certidão\nPedido: Solicito segunda via da certidão."
        ).run()
        processar = next(b for b in at.button if b.label == "Processar solicitação")
        processar.click().run()
        self.assertFalse(at.exception, at.exception)
        self.assertTrue(any("PENDENTE" in m.value for m in at.markdown))
        # Decisão humana pela aba Revisão (operador + justificativa obrigatórios).
        at.sidebar.text_input[0].set_value("Operadora de Teste").run()
        justificativa = next(t for t in at.text_area if t.label.startswith("Justificativa"))
        justificativa.set_value("Conferido com o original no teste da interface").run()
        next(b for b in at.button if b.label == "Registrar decisão humana").click().run()
        self.assertFalse(at.exception, at.exception)
        self.assertTrue(any("Nada foi enviado" in s.value for s in at.success))
        from src.revisao import RepositorioRevisao

        repo = RepositorioRevisao(os.environ["D6_BANCO_REVISAO"])
        decisoes = repo.contagem()["decisoes_por_origem"]
        self.assertEqual(decisoes, {"humana_interface": 1})


if __name__ == "__main__":
    unittest.main()
