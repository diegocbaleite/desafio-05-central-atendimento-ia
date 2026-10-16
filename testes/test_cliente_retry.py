"""Testes do comportamento diante de limites do OpenRouter (sem usar API real)."""
import unittest
from unittest.mock import patch, Mock
from src.cliente import conversar, ErroAPI

class TestRateLimit(unittest.TestCase):
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
        self.assertEqual(conversar([{"role":"user","content":"teste"}],provider="openrouter")["texto"],"OK")
        self.assertEqual(post.call_count,2)

if __name__=="__main__":
    unittest.main()
