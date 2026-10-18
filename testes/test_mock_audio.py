"""Testes das referências fictícias do modo offline; não simulam STT/OCR real."""

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


class TestModoMockImagem(unittest.TestCase):
    def test_imagem_usa_referencia_rotulada_sem_executar_ocr(self):
        with tempfile.TemporaryDirectory() as d:
            pasta = Path(d)
            original = pasta / "I02.png"
            original.write_bytes(b"imagem ficticia")
            referencia = pasta / "I02_ocr_referencia.txt"
            referencia.write_text(
                "CÓDIGO: 2026-000142", encoding="utf-8"
            )
            self.assertEqual(
                preparar_entrada(
                    original, "imagem", mock=True, referencia=referencia
                ),
                "CÓDIGO: 2026-000142",
            )

    def test_referencia_ocr_ausente_falha_explicitamente(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "Referência fictícia de OCR"):
                preparar_entrada(Path(d) / "I02.png", "imagem", mock=True)


if __name__ == "__main__":
    unittest.main()
