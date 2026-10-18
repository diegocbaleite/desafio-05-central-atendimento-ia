"""Testes locais sem chamadas pagas, aprovação simulada não gera áudio real."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from src import guilherme_multimodal as g


class TestMetricas(unittest.TestCase):
    def test_wer_cer_perfeitas(self):
        resultado = g.metricas("Protocolo 2026-000142", "Protocolo 2026-000142")
        self.assertEqual(resultado["wer"], 0)
        self.assertEqual(resultado["cer"], 0)

    def test_metricas_denunciam_troca_de_protocolo(self):
        resultado = g.metricas("Protocolo 2026-000142", "Protocolo 2026-000143")
        self.assertGreater(resultado["wer"], 0)
        self.assertGreater(resultado["cer"], 0)

    def test_wer_sem_referencia_nao_e_inventada(self):
        self.assertIsNone(g.metricas("", "algo")["wer"])
        self.assertIsNone(g.metricas("", "algo")["cer"])


class TestEntradas(unittest.TestCase):
    def test_pdf_falso_rejeitado(self):
        with tempfile.TemporaryDirectory() as d:
            arq = Path(d) / "formulario.pdf"
            arq.write_bytes(b"nao e pdf")
            with self.assertRaisesRegex(ValueError, "assinatura PDF"):
                g._validar(arq, g.IMAGENS)

    def test_extensao_invalida_rejeitada(self):
        with tempfile.TemporaryDirectory() as d:
            arq = Path(d) / "segredo.env"
            arq.write_text("fake", encoding="utf-8")
            with self.assertRaises(ValueError):
                g._validar(arq, g.AUDIO)

    def test_sem_envio_remoto_por_padrao(self):
        with tempfile.TemporaryDirectory() as d:
            audio = Path(d) / "fala.mp3"
            audio.write_bytes(b"ID3fake")
            with self.assertRaises(PermissionError):
                g.avaliar_audio(audio, provider="groq")


class TestAvaliacoes(unittest.TestCase):
    def test_audio_mock_e_separacao_bruto_revisado(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            arq = raiz / "fala.mp3"
            arq.write_bytes(b"ID3fake")
            ref = raiz / "gabarito.txt"
            ref.write_text("Meu protocolo 2026-000142", encoding="utf-8")
            revisado = raiz / "revisado.txt"
            revisado.write_text("Meu protocolo 2026-000142", encoding="utf-8")
            pasta = g.avaliar_audio(arq, provider="local", saida=raiz / "saida",
                                    gabarito=ref, revisado=revisado,
                                    transcritor_teste=lambda p: "Meu protocolo 2026-000143")
            meta = json.loads((pasta / "resultado.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["execucao"], "simulação de teste")
            self.assertGreater(meta["metricas"]["bruta"]["wer"], 0)
            self.assertEqual(meta["metricas"]["revisada"]["wer"], 0)
            self.assertEqual((pasta / "transcricao_bruta.txt").read_text(encoding="utf-8"),
                             "Meu protocolo 2026-000143")

    def test_ocr_mock_exige_revisao(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            arq = raiz / "ficha.png"
            Image.new("RGB", (40, 40), "white").save(arq)
            pasta = g.avaliar_ocr(arq, saida=raiz / "saida",
                                  motor_teste=lambda *args: ("Protocolo 2026-000142", [
                                      {"fragmento": "2026-000142", "confianca_ocr": 20.0}]))
            meta = json.loads((pasta / "resultado.json").read_text(encoding="utf-8"))
            self.assertTrue(meta["requer_revisao_humana"])
            self.assertEqual(meta["motor"], "mock")
            self.assertTrue(meta["paginas"][0]["trechos_incertos"])
            self.assertTrue((pasta / "PENDENTE_REVISAO.md").exists())

    def test_nenhuma_correção_automatica(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            arq = raiz / "teste.mp3"
            arq.write_bytes(b"ID3fake")
            pasta = g.avaliar_audio(arq, saida=raiz / "saida",
                                   transcritor_teste=lambda _: "Protoclo invaldo")
            self.assertFalse((pasta / "texto_revisado_humano.txt").exists())
            self.assertTrue((pasta / "PENDENTE_REVISAO.md").exists())


class TestControleHumano(unittest.TestCase):
    def test_tts_nega_decisao_mock(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            minuta = raiz / "minuta.md"
            minuta.write_text("# MINUTA — NÃO ENVIADA", encoding="utf-8")
            parecer = raiz / "revisao.json"
            parecer.write_text(json.dumps({"decisao": "aprovar", "simulada": True,
                                            "origem": "arquivo_yaml"}), encoding="utf-8")
            with self.assertRaises(PermissionError):
                g.gerar_voz(minuta, parecer, saida=raiz / "saida")
            self.assertFalse((raiz / "saida").exists())

    def test_tts_verifica_hash(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            minuta = raiz / "minuta.md"
            minuta.write_text("Conteúdo revisado", encoding="utf-8")
            parecer = raiz / "revisao.json"
            parecer.write_text(json.dumps({"decisao": "aprovar", "simulada": False,
                                            "origem": "revisao_humana", "revisor": "Teste",
                                            "data_revisao": "2026-10-17",
                                            "sha256_minuta": "sha incorreto"}), encoding="utf-8")
            with self.assertRaises(PermissionError):
                g.gerar_voz(minuta, parecer, saida=raiz / "saida")

    def test_avisar_ausencia_no_audio(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            minuta = raiz / "minuta.md"
            minuta.write_text("Informação não localizado", encoding="utf-8")
            parecer = raiz / "revisao.json"
            parecer.write_text(json.dumps({"decisao": "aprovar", "simulada": False,
                                            "origem": "revisao_humana", "revisor": "Servidor teste",
                                            "data_revisao": "2026-10-17",
                                            "sha256_minuta": hashlib.sha256(minuta.read_bytes()).hexdigest()}),
                                 encoding="utf-8")
            def fake_audio(roteiro, destino):
                destino.write_bytes(b"RIFFmock_audio")
                return str(destino)
            pasta = g.gerar_voz(minuta, parecer, saida=raiz / "saida",
                                sintetizador_teste=fake_audio)
            roteiro = (pasta / "roteiro_falado.txt").read_text(encoding="utf-8")
            self.assertIn("Atenção:", roteiro)
            meta = json.loads((pasta / "resultado.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["execucao"], "mock")

    def test_arte_programatica_nao_e_chamada_ia(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            def mock_gerador(destino):
                Image.new("RGB", (12, 12), "white").save(destino)
                destino.with_name("orientacao.proveniencia.json").write_text(
                    json.dumps({"por_ia": False, "metodo": "composicao_programatica"}),
                    encoding="utf-8")
                return destino
            pasta = g.gerar_visual(saida=raiz / "saida", gerador_teste=mock_gerador)
            info = json.loads((pasta / "revisao_visual.json").read_text(encoding="utf-8"))
            self.assertFalse(info["por_ia"])
            self.assertTrue(info["revisao_humana"] == "pendente")


if __name__ == "__main__":
    unittest.main()
