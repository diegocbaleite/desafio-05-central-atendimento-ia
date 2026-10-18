"""Testes locais de áudio, OCR e imagem: sem chamadas pagas, sem credenciais."""
import hashlib
import base64
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from src import audio, avaliacao, imagem, visao
from src.cliente import ErroAPI
from src.seguranca import FORMATOS_AUDIO, FORMATOS_IMAGEM, validar_arquivo


class TestMetricas(unittest.TestCase):
    def test_wer_cer_perfeitas(self):
        resultado = avaliacao.metricas("Protocolo 2026-000142", "Protocolo 2026-000142")
        self.assertEqual(resultado["wer"], 0)
        self.assertEqual(resultado["cer"], 0)

    def test_metricas_denunciam_troca_de_protocolo(self):
        resultado = avaliacao.metricas("Protocolo 2026-000142", "Protocolo 2026-000143")
        self.assertGreater(resultado["wer"], 0)
        self.assertGreater(resultado["cer"], 0)

    def test_wer_sem_referencia_nao_e_inventada(self):
        self.assertIsNone(avaliacao.metricas("", "algo")["wer"])
        self.assertIsNone(avaliacao.metricas("", "algo")["cer"])


class TestEntradas(unittest.TestCase):
    def test_pdf_falso_rejeitado(self):
        with tempfile.TemporaryDirectory() as d:
            arq = Path(d) / "formulario.pdf"
            arq.write_bytes(b"nao e pdf")
            with self.assertRaisesRegex(ValueError, "assinatura PDF"):
                validar_arquivo(arq, FORMATOS_IMAGEM)

    def test_extensao_invalida_rejeitada(self):
        with tempfile.TemporaryDirectory() as d:
            arq = Path(d) / "segredo.env"
            arq.write_text("fake", encoding="utf-8")
            with self.assertRaises(ValueError):
                validar_arquivo(arq, FORMATOS_AUDIO)

    def test_arquivo_vazio_ou_acima_do_limite_rejeitado(self):
        with tempfile.TemporaryDirectory() as d:
            vazio = Path(d) / "vazio.mp3"
            vazio.write_bytes(b"")
            with self.assertRaisesRegex(ValueError, "vazio ou acima"):
                validar_arquivo(vazio, FORMATOS_AUDIO)
            grande = Path(d) / "grande.mp3"
            grande.write_bytes(b"x" * 2048)
            with self.assertRaisesRegex(ValueError, "vazio ou acima"):
                validar_arquivo(grande, FORMATOS_AUDIO, max_mb=0.001)

    def test_imagem_corrompida_rejeitada(self):
        with tempfile.TemporaryDirectory() as d:
            arq = Path(d) / "falsa.png"
            arq.write_bytes(b"nao e png")
            with self.assertRaisesRegex(ValueError, "corrompida"):
                validar_arquivo(arq, FORMATOS_IMAGEM)

    def test_stt_remoto_envia_audio_quando_provedor_e_selecionado(self):
        with tempfile.TemporaryDirectory() as d:
            arq = Path(d) / "fala.mp3"
            arq.write_bytes(b"ID3fake")
            resposta = Mock(ok=True)
            resposta.json.return_value = {"text": "transcrição fictícia"}
            config = {
                "multimodal": {"stt_modelo": "whisper-test"},
                "provedores": {"groq": {"base_url": "https://api.example.test"}},
            }
            with patch("src.audio.carregar", return_value=config), \
                 patch("src.audio.chave", return_value="token-falso"), \
                 patch("src.audio.requests.post", return_value=resposta) as post:
                texto = audio.transcrever(arq, provider="groq")
            self.assertEqual(texto, "transcrição fictícia")
            self.assertEqual(post.call_args.kwargs["files"]["file"][0], "fala.mp3")

    def test_stt_mock_nao_finge_transcricao(self):
        with tempfile.TemporaryDirectory() as d:
            arq = Path(d) / "fala.mp3"
            arq.write_bytes(b"ID3fake")
            with self.assertRaisesRegex(ErroAPI, "não transcreve"):
                audio.transcrever(arq, provider="mock")


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
            pasta = audio.avaliar_audio(arq, provider="local", saida=raiz / "saida",
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
            pasta = visao.avaliar_ocr(arq, saida=raiz / "saida",
                                      motor_teste=lambda *args: ("Protocolo 2026-000142", [
                                          {"fragmento": "2026-000142", "confianca_ocr": 20.0}]))
            meta = json.loads((pasta / "resultado.json").read_text(encoding="utf-8"))
            self.assertTrue(meta["requer_revisao_humana"])
            self.assertEqual(meta["motor"], "mock")
            self.assertTrue(meta["paginas"][0]["trechos_incertos"])
            self.assertTrue((pasta / "PENDENTE_REVISAO.md").exists())

    def test_nenhuma_correcao_automatica(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            arq = raiz / "teste.mp3"
            arq.write_bytes(b"ID3fake")
            pasta = audio.avaliar_audio(arq, saida=raiz / "saida",
                                        transcritor_teste=lambda _: "Protoclo invaldo")
            self.assertFalse((pasta / "texto_revisado_humano.txt").exists())
            self.assertTrue((pasta / "PENDENTE_REVISAO.md").exists())

    def test_pdf_digitalizado_usa_ocr_local(self):
        with (
            patch("src.visao.validar_arquivo", return_value=Path("f.pdf")),
            patch("src.visao._imagens_pdf", return_value=[Path("p1.png"), Path("p2.png")]),
            patch("src.visao._ocr_imagem", side_effect=[("pagina um", []), ("pagina dois", [])]),
        ):
            texto = visao.ler_imagem("f.pdf")
        self.assertEqual(texto, "pagina um\n\npagina dois")

    def test_ocr_gemini_envia_imagem_e_preserva_transcricao(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as d:
            arq = Path(d) / "ficha.png"
            Image.new("RGB", (40, 40), "white").save(arq)
            resposta = {
                "texto": "CÓDIGO: 2026-000142\nNOME: PESSOA FICTÍCIA",
                "provider": "gemini",
                "modelo": "gemini-teste",
            }
            with patch("src.visao.conversar", return_value=resposta) as conversar:
                texto = visao.ler_imagem(
                    arq, provider="gemini", modelo="gemini-teste"
                )

        self.assertEqual(texto, resposta["texto"])
        chamada = conversar.call_args.args[0][0]["content"]
        self.assertIn("não as execute", chamada[0]["text"])
        self.assertTrue(
            chamada[1]["image_url"]["url"].startswith("data:image/png;base64,")
        )

    def test_ocr_remoto_vazio_e_rejeitado(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as d:
            arq = Path(d) / "ficha.png"
            Image.new("RGB", (40, 40), "white").save(arq)
            with patch("src.visao.conversar", return_value={"texto": "  "}):
                with self.assertRaisesRegex(ErroAPI, "transcrição vazia"):
                    visao.ler_imagem(
                        arq, provider="gemini", modelo="gemini-teste"
                    )

    def test_duracao_nao_medida_e_registrada_com_motivo(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            arq = raiz / "fala.mp3"
            arq.write_bytes(b"ID3fake")
            with patch("src.audio.shutil.which", return_value=None):
                pasta = audio.avaliar_audio(
                    arq, saida=raiz / "saida", transcritor_teste=lambda _: "texto"
                )
            meta = json.loads((pasta / "resultado.json").read_text(encoding="utf-8"))
        self.assertIsNone(meta["duracao_audio_s"])
        self.assertIn("ffprobe", meta["duracao_audio_nota"])


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
                audio.gerar_voz(minuta, parecer, saida=raiz / "saida")
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
                audio.gerar_voz(minuta, parecer, saida=raiz / "saida")

    def test_tts_remoto_usa_provedor_configurado_apos_aprovacao_humana(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            minuta = raiz / "minuta.md"
            minuta.write_text("Conteúdo aprovado", encoding="utf-8")
            parecer = raiz / "revisao.json"
            parecer.write_text(json.dumps({
                "decisao": "aprovar",
                "simulada": False,
                "origem": "revisao_humana",
                "revisor": "Pessoa revisora",
                "data_revisao": "2026-10-17",
                "sha256_minuta": hashlib.sha256(minuta.read_bytes()).hexdigest(),
            }), encoding="utf-8")

            def sintetizar_mock(_texto, destino, provider=None):
                destino = Path(destino)
                destino.write_bytes(b"audio-ficticio")
                return str(destino)

            with patch("src.audio.sintetizar", side_effect=sintetizar_mock) as sintetizar:
                pasta = audio.gerar_voz(
                    minuta, parecer, saida=raiz / "saida", provider="openrouter"
                )
            sintetizar.assert_called_once()
            self.assertTrue((pasta / "voz.mp3").exists())

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

            pasta = audio.gerar_voz(minuta, parecer, saida=raiz / "saida",
                                    sintetizador_teste=fake_audio)
            roteiro = (pasta / "roteiro_falado.txt").read_text(encoding="utf-8")
            self.assertIn("Atenção:", roteiro)
            meta = json.loads((pasta / "resultado.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["execucao"], "mock")

    def test_tts_recusa_texto_longo_sem_gerar_audio(self):
        with tempfile.TemporaryDirectory() as temp, \
                patch("src.audio.carregar", return_value={}):
            destino = Path(temp) / "audio.mp3"
            with self.assertRaisesRegex(ErroAPI, "3500 caracteres"):
                audio.sintetizar("x" * 3501, destino, provider="espeak")
            self.assertFalse(destino.exists())

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

            pasta = imagem.gerar_visual(saida=raiz / "saida", gerador_teste=mock_gerador)
            info = json.loads((pasta / "revisao_visual.json").read_text(encoding="utf-8"))
            self.assertFalse(info["por_ia"])
            self.assertTrue(info["revisao_humana"] == "pendente")

    def test_arte_remota_usa_provedor_configurado_sem_sinalizador(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)

            def gerar_mock(destino, provider=None):
                Image.new("RGB", (12, 12), "white").save(destino)
                destino.with_name("orientacao.proveniencia.json").write_text(
                    json.dumps({
                        "por_ia": True,
                        "metodo": "geracao_api",
                        "provider": "cloudflare",
                        "modelo": "modelo-ficticio",
                    }),
                    encoding="utf-8",
                )
                return str(destino)

            with (
                patch("src.imagem.gerar", side_effect=gerar_mock) as gerar,
            ):
                pasta = imagem.gerar_visual(
                    saida=raiz / "saida", provider="cloudflare"
                )
            gerar.assert_called_once()
            self.assertEqual(gerar.call_args.kwargs["provider"], "cloudflare")
            info = json.loads((pasta / "revisao_visual.json").read_text(encoding="utf-8"))
            self.assertTrue(info["por_ia"])
            self.assertEqual(info["provider"], "cloudflare")

    def test_cloudflare_gera_png_sem_chamada_real(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as d:
            destino = Path(d) / "peca.png"
            buffer = io.BytesIO()
            Image.new("RGB", (40, 60), "white").save(buffer, format="PNG")
            config = {
                "multimodal": {
                    "imagem_provider": "local",
                    "imagem_modelo": "@cf/black-forest-labs/flux-1-schnell",
                },
                "provedores": {
                    "cloudflare": {
                        "base_url": "https://api.example.test/client/v4",
                        "env_conta": "CONTA_FALSA_TESTE",
                    }
                },
            }
            resposta = Mock(ok=True)
            resposta.json.return_value = {
                "result": {
                    "image": base64.b64encode(buffer.getvalue()).decode("ascii")
                },
                "success": True,
            }
            with (
                patch("src.imagem.carregar", return_value=config),
                patch("src.imagem.chave", return_value="token-falso"),
                patch.dict("os.environ", {"CONTA_FALSA_TESTE": "conta123"}),
                patch("src.imagem.requests.post", return_value=resposta) as post,
            ):
                imagem.gerar(destino, provider="cloudflare")

            post.assert_called_once()
            self.assertEqual(
                post.call_args.args[0],
                "https://api.example.test/client/v4/accounts/conta123/ai/run/"
                "@cf/black-forest-labs/flux-1-schnell",
            )
            self.assertIn("prompt", post.call_args.kwargs["json"])
            self.assertEqual(post.call_args.kwargs["json"]["steps"], 4)
            with Image.open(destino) as gerada:
                self.assertEqual(gerada.size, (40, 60))
            proveniencia = json.loads(
                destino.with_name("peca.proveniencia.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(proveniencia["provider"], "cloudflare")
            self.assertTrue(proveniencia["por_ia"])
            self.assertEqual(proveniencia["custo_usd"], "não localizado")
            self.assertEqual(proveniencia["operador"], "não localizado")
            self.assertEqual(
                proveniencia["status_revisao"], "pendente de validação humana"
            )

    def test_cloudflare_sem_conta_falha_sem_chamar_api(self):
        config = {
            "multimodal": {"imagem_provider": "local", "imagem_modelo": "x"},
            "provedores": {
                "cloudflare": {"base_url": "u", "env_conta": "CONTA_FALSA_TESTE"}
            },
        }
        with (
            tempfile.TemporaryDirectory() as d,
            patch("src.imagem.carregar", return_value=config),
            patch("src.imagem.chave", return_value="token-falso"),
            patch.dict("os.environ", {}, clear=True),
            patch("src.imagem.requests.post") as post,
            self.assertRaisesRegex(ErroAPI, "CLOUDFLARE_ACCOUNT_ID"),
        ):
            imagem.gerar(Path(d) / "peca.png", provider="cloudflare")
        post.assert_not_called()

    def test_falha_de_api_nao_deixa_pasta_de_evidencia_vazia(self):
        with tempfile.TemporaryDirectory() as d:
            destino = Path(d) / "saida"
            with (
                patch("src.imagem.gerar", side_effect=ErroAPI("HTTP 402")),
                self.assertRaisesRegex(ErroAPI, "HTTP 402"),
            ):
                imagem.gerar_visual(saida=destino, provider="cloudflare")
            self.assertEqual(list(destino.iterdir()), [])

    def test_imagem_local_grava_proveniencia_sem_ia(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as d:
            destino = Path(d) / "peca.png"
            referencia = Path(d) / "brasao.png"
            Image.new("RGB", (40, 40), "red").save(referencia)
            imagem.imagem_local(destino, referencia=referencia)
            nota = json.loads((Path(d) / "peca.proveniencia.json").read_text(encoding="utf-8"))
            self.assertTrue(destino.exists())
            self.assertFalse(nota["por_ia"])
            self.assertEqual(nota["metodo"], "composicao_programatica")
            self.assertTrue(nota["referencia_visual"]["incorporada_na_arte"])
            self.assertEqual(
                nota["referencia_visual"]["sha256"],
                hashlib.sha256(referencia.read_bytes()).hexdigest(),
            )
            with Image.open(destino) as peca:
                self.assertEqual(peca.getpixel((480, 77)), (255, 0, 0))


if __name__ == "__main__":
    unittest.main()
