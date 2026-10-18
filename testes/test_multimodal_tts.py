"""O TTS deve recusar texto acima do limite, sem truncar a minuta."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.cliente import ErroAPI
from src.multimodal import sintetizar


class TestLimiteTTS(unittest.TestCase):
    @patch("src.multimodal.carregar", return_value={})
    def test_recusa_texto_longo_sem_gerar_audio(self, carregar):
        with tempfile.TemporaryDirectory() as temp:
            destino = Path(temp) / "audio.mp3"
            with self.assertRaisesRegex(ErroAPI, "3500 caracteres"):
                sintetizar("x" * 3501, destino, provider="espeak")
            self.assertFalse(destino.exists())


if __name__ == "__main__":
    unittest.main()
