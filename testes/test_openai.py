"""Contratos HTTP OpenAI e revisão: testes simulados, sem consumir créditos."""

import base64
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests
from PIL import Image

from src import audio, cliente, imagem, main, visao
from src.config import carregar


class TestOpenAI(unittest.TestCase):
    def setUp(self):
        self.cfg = carregar()

    def test_texto_parametros_e_uso_reais_do_payload(self):
        resposta = Mock(status_code=200)
        resposta.json.return_value = {
            "model": "gpt-6-luna", "usage": {"prompt_tokens": 20, "completion_tokens": 8},
            "choices": [{"message": {"content": "Minuta fictícia"}}],
        }
        with patch.object(cliente, "chave", return_value="token-ficticio"), \
             patch.object(cliente.requests, "post", return_value=resposta) as post:
            resultado = cliente.conversar([{"role": "user", "content": "Pedido fictício"}])
        self.assertTrue(post.call_args.args[0].endswith("/chat/completions"))
        payload = post.call_args.kwargs["json"]
        self.assertNotIn("max_tokens", payload)
        self.assertEqual(payload["max_completion_tokens"], 2400)
        self.assertEqual(payload["reasoning_effort"], "none")
        self.assertEqual(payload["temperature"], 0.2)
        self.assertIs(payload["store"], False)
        self.assertEqual(resultado["tokens_entrada"], 20)
        self.assertIsNone(resultado["custo_usd"])
        self.assertEqual(resultado["parametros"]["max_completion_tokens"], 2400)
        self.assertNotIn("token-ficticio", json.dumps(resultado))

    def test_raciocinio_ativo_omite_temperatura_incompativel(self):
        conf = {**self.cfg["llm"], "reasoning_effort": "low"}
        payload = cliente._payload([], "gpt-6.1-sol", conf, "openai")
        self.assertNotIn("temperature", payload)
        self.assertEqual(payload["reasoning_effort"], "low")

    def test_modelo_sem_raciocinio_nao_recebe_esforco(self):
        payload = cliente._payload([], "gpt-4.1-mini", self.cfg["llm"], "openai")
        self.assertNotIn("reasoning_effort", payload)

    def test_chave_ausente_bloqueia_sem_rede(self):
        with patch.object(cliente, "chave", return_value=""), \
             patch.object(cliente.requests, "post") as post:
            with self.assertRaisesRegex(cliente.ErroAPI, "Chave ausente"):
                cliente.conversar([])
            post.assert_not_called()

    def test_falhas_http_e_resposta_vazia_sem_expor_chave(self):
        for status in (400, 401, 403, 200):
            with self.subTest(status=status):
                resposta = Mock(status_code=status)
                resposta.json.return_value = {"error": {"message": "token-ficticio"}}
                with patch.object(cliente, "chave", return_value="token-ficticio"), \
                     patch.object(cliente.requests, "post", return_value=resposta) as post:
                    with self.assertRaises(cliente.ErroAPI) as erro:
                        cliente.conversar([])
                    self.assertNotIn("token-ficticio", str(erro.exception))
                    self.assertEqual(post.call_count, 1)

    def test_timeout_e_limite_tem_tentativas_limitadas(self):
        for falha in (requests.Timeout(), Mock(status_code=429, headers={"Retry-After": "0"},
                                             json=lambda: {"error": {"code": 429}})):
            with self.subTest(falha=type(falha).__name__):
                efeito = [falha] * 3
                with patch.object(cliente, "chave", return_value="token-ficticio"), \
                     patch.object(cliente.requests, "post", side_effect=efeito) as post, \
                     patch.object(cliente.time, "sleep"):
                    with self.assertRaisesRegex(cliente.ErroAPI, "3 tentativas"):
                        cliente.conversar([])
                    self.assertEqual(post.call_count, 3)

    def test_catalogo_consulta_conta_sem_geracao(self):
        resposta = Mock(ok=True, json=lambda: {"data": [{"id": "b"}, {"id": "a"}, {"id": "a"}]})
        with patch.object(cliente, "chave", return_value="token-ficticio"), \
             patch.object(cliente.requests, "get", return_value=resposta) as get, \
             patch.object(cliente.requests, "post") as post:
            self.assertEqual(cliente.listar_modelos("openai"), ["a", "b"])
            self.assertEqual(get.call_args.args[0], "https://api.openai.com/v1/models")
            post.assert_not_called()

    def test_catalogo_invalido_ou_autenticacao_recusada(self):
        for resposta in (Mock(ok=False, status_code=401), Mock(ok=True, json=lambda: {"data": "invalido"})):
            with patch.object(cliente, "chave", return_value="token-ficticio"), \
                 patch.object(cliente.requests, "get", return_value=resposta):
                with self.assertRaises(cliente.ErroAPI):
                    cliente.listar_modelos("openai")

    def test_stt_openai_envia_idioma_e_preserva_original(self):
        with tempfile.TemporaryDirectory() as d:
            arq = Path(d) / "ficticio.mp3"
            arq.write_bytes(b"ID3ficticio")
            resposta = Mock(ok=True, json=lambda: {"text": "Pedido fictício"})
            with patch.object(audio, "chave", return_value="token-ficticio"), \
                 patch.object(audio.requests, "post", return_value=resposta) as post:
                texto = audio.transcrever(arq)
            self.assertEqual(texto, "Pedido fictício")
            self.assertEqual(post.call_args.kwargs["data"], {"model": "gpt-transcribe", "languages[]": "pt"})
            self.assertTrue(post.call_args.args[0].endswith("/audio/transcriptions"))
            self.assertEqual(arq.read_bytes(), b"ID3ficticio")

    def test_stt_nao_textual_e_falha_controlada(self):
        with tempfile.TemporaryDirectory() as d:
            arq = Path(d) / "ficticio.mp3"
            arq.write_bytes(b"ID3ficticio")
            with patch.object(audio, "chave", return_value="token-ficticio"), \
                 patch.object(audio.requests, "post", return_value=Mock(ok=True, json=lambda: {"text": None})):
                with self.assertRaisesRegex(cliente.ErroAPI, "texto vazio"):
                    audio.transcrever(arq)

    def test_ocr_openai_encaminha_imagem_e_mantem_revisao_pendente(self):
        with tempfile.TemporaryDirectory() as d:
            arq = Path(d) / "ficticia.png"
            Image.new("RGB", (40, 40), "white").save(arq)
            with patch.object(visao, "conversar", return_value={"texto": "Protocolo: não localizado"}) as chamada:
                pasta = visao.avaliar_ocr(arq, provider="openai", saida=Path(d) / "saida")
            meta = json.loads((pasta / "resultado.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["provedor"], "openai")
            self.assertTrue(meta["requer_revisao_humana"])
            self.assertEqual(chamada.call_args.kwargs["provider"], "openai")
            self.assertTrue(chamada.call_args.args[0][0]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,"))

    def test_tts_openai_valida_mp3_e_parametros(self):
        with tempfile.TemporaryDirectory() as d:
            resposta = Mock(ok=True, headers={"Content-Type": "audio/mpeg"}, content=b"ID3ficticio")
            with patch.object(audio, "chave", return_value="token-ficticio"), \
                 patch.object(audio.requests, "post", return_value=resposta) as post:
                arq = audio.sintetizar("Minuta fictícia", Path(d) / "voz.mp3")
            self.assertEqual(Path(arq).read_bytes(), b"ID3ficticio")
            self.assertEqual(post.call_args.kwargs["json"]["model"], "gpt-4o-mini-tts")
            self.assertEqual(post.call_args.kwargs["json"]["voice"], "coral")

    def test_imagem_openai_decodifica_base64_e_registra_proveniencia(self):
        buffer = io.BytesIO()
        Image.new("RGB", (400, 400), "white").save(buffer, format="PNG")
        resposta = Mock(ok=True, json=lambda: {
            "data": [{"b64_json": base64.b64encode(buffer.getvalue()).decode("ascii")}],
            "usage": {"input_tokens": 10, "output_tokens": 20},
        })
        with tempfile.TemporaryDirectory() as d:
            destino = Path(d) / "arte.png"
            with patch.object(imagem, "chave", return_value="token-ficticio"), \
                 patch.object(imagem.requests, "post", return_value=resposta) as post:
                imagem.gerar(destino)
            meta = json.loads(destino.with_suffix(".proveniencia.json").read_text(encoding="utf-8"))
            self.assertEqual(post.call_args.args[0], "https://api.openai.com/v1/images/generations")
            self.assertNotIn("steps", post.call_args.kwargs["json"])
            self.assertEqual(post.call_args.kwargs["json"]["n"], 1)
            self.assertEqual(meta["provider"], "openai")
            self.assertEqual(meta["tokens_saida"], 20)
            self.assertEqual(meta["status_revisao"], "pendente de validação humana")

    def test_cli_audio_respeita_provedor_configurado(self):
        with patch.object(main, "avaliar_audio", return_value="saida") as avaliar, \
             patch("sys.argv", ["main", "audio", "ficticio.mp3"]):
            self.assertEqual(main.main(), 0)
            self.assertIsNone(avaliar.call_args.kwargs["provider"])

    def test_tts_openai_bloqueia_revisao_simulada_antes_da_rede(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            minuta = raiz / "minuta.md"
            minuta.write_text("Minuta fictícia", encoding="utf-8")
            revisao = raiz / "revisao.json"
            revisao.write_text(json.dumps({"decisao": "aprovar", "simulada": True}), encoding="utf-8")
            with patch.object(audio.requests, "post") as post:
                with self.assertRaisesRegex(PermissionError, "aprovação humana"):
                    audio.gerar_voz(minuta, revisao, provider="openai", saida=raiz / "saida")
                post.assert_not_called()

    def test_imagem_vazia_nao_vira_evidencia_de_ia(self):
        with tempfile.TemporaryDirectory() as d:
            destino = Path(d) / "arte.png"
            with patch.object(imagem, "chave", return_value="token-ficticio"), \
                 patch.object(imagem.requests, "post", return_value=Mock(ok=True, json=lambda: {"data": []})):
                with self.assertRaisesRegex(cliente.ErroAPI, "não retornou imagem"):
                    imagem.gerar(destino)
                self.assertFalse(destino.exists())
                self.assertFalse(destino.with_suffix(".proveniencia.json").exists())


if __name__ == "__main__":
    unittest.main()
