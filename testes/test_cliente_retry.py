"""Testes do comportamento diante de limites do OpenRouter (sem usar API real)."""
import unittest
from unittest.mock import patch, Mock
from src.cliente import conversar, ErroAPI

class TestRateLimit(unittest.TestCase):
    def test_metadados_registram_parametros_efetivos_da_chamada(self):
        config = {
            "llm": {
                "provider": "gemini",
                "modelo": "gemini-test",
                "temperatura": 0.2,
                "max_tokens": 1200,
                "timeout_s": 30,
            },
            "provedores": {
                "gemini": {"base_url": "https://api.example.test/v1"}
            },
        }
        resposta = Mock(
            status_code=200,
            json=lambda: {
                "model": "gemini-test",
                "choices": [{"message": {"content": "Minuta fictícia"}}],
                "usage": {},
            },
        )
        with (
            patch("src.cliente.carregar", return_value=config),
            patch("src.cliente.chave", return_value="token-falso"),
            patch("src.cliente.requests.post", return_value=resposta) as post,
        ):
            resultado = conversar(
                [{"role": "user", "content": "Conteúdo fictício"}]
            )
        self.assertEqual(
            resultado["parametros"],
            {"temperature": 0.2, "max_tokens": 1200, "timeout_s": 30},
        )
        self.assertEqual(
            post.call_args.kwargs["json"]["temperature"], 0.2
        )
        self.assertEqual(post.call_args.kwargs["json"]["max_tokens"], 1200)

    @patch("src.cliente.chave", return_value="token-de-teste")
    @patch("src.cliente.time.sleep")
    @patch("src.cliente.requests.post")
    def test_429_com_retry_after(self, post, sleep, chave):
        post.return_value=Mock(status_code=429,headers={"Retry-After":"0"},
            json=lambda: {"error":{"code":429,"message":"Provider returned error"}})
        with self.assertRaisesRegex(ErroAPI,"429"):
            conversar([{"role":"user","content":"teste"}],provider="openrouter")
        self.assertEqual(post.call_count,3)
        self.assertEqual(sleep.call_count,2)

    @patch("src.cliente.chave", return_value="token-de-teste")
    @patch("src.cliente.time.sleep")
    @patch("src.cliente.requests.post")
    def test_502_200_retentativa(self, post, sleep, chave):
        post.side_effect=[
            Mock(status_code=200,headers={},json=lambda:{"error":{"code":502,"message":"Busy"}}),
            Mock(status_code=200,headers={},json=lambda:{"choices":[{"message":{"content":"OK"}}],"usage":{}})
        ]
        resposta=conversar([{"role":"user","content":"teste"}],provider="openrouter")
        self.assertEqual(resposta["texto"],"OK")
        self.assertEqual(resposta["tentativas"],2)
        self.assertEqual(post.call_count,2)

if __name__=="__main__":
    unittest.main()
