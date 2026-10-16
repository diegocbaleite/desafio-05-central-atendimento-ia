"""Testes do mapeamento de transcrição fictícia do modo offline."""

import tempfile
import unittest
from pathlib import Path

from src.main import preparar_entrada


class TestModoMockAudio(unittest.TestCase):
    def test_audio_usa_referencia_rotulada(self):
        with tempfile.TemporaryDirectory() as d:
            pasta = Path(d)
            (pasta / "C02_audio.wav").write_bytes(
                b"audio ficticio apenas para teste de caminho"
            )
            (pasta / "C02_transcricao_ficticia.txt").write_text(
                "Transcrição fictícia", encoding="utf-8"
            )
            self.assertEqual(
                preparar_entrada(pasta / "C02_audio.wav", "audio", mock=True),
                "Transcrição fictícia",
            )

    def test_referencia_ausente_falha_explicitamente(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "Transcrição fictícia"):
                preparar_entrada(Path(d) / "C02_audio.wav", "audio", mock=True)


if __name__ == "__main__":
    unittest.main()
