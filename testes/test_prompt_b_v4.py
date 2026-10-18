"""Regressões da versão B V4: sem APIs externas nem aprovação humana simulada."""
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src import experimento_b_v2_real as modulo


class TestPromptBV4(unittest.TestCase):
    def test_prompt_real_possui_regras_sobre_lacunas(self):
        path = modulo.ROOT / modulo.PROMPTS["v4"]
        texto = path.read_text(encoding="utf-8")
        for trecho in (
            "{{solicitacao}}",
            "tipo de certidão",
            "descrição concreta",
            "não sei o número do protocolo",
            "não localizado na solicitação",
            "revisão humana",
        ):
            self.assertIn(trecho.casefold(), texto.casefold())

    @patch.object(modulo, "ROOT")
    @patch.object(modulo, "chave", return_value="token-falso")
    @patch.object(modulo, "carregar")
    @patch.object(modulo, "conversar")
    def test_v4_separada_preserva_evidencia_de_outras_versoes(
        self, conversar, carregar, chave, root
    ):
        with tempfile.TemporaryDirectory() as temporario:
            base = Path(temporario)
            arquivo_prompt = base / modulo.PROMPTS["v4"]
            arquivo_prompt.parent.mkdir(parents=True, exist_ok=True)
            arquivo_prompt.write_text("Regras: {{solicitacao}}", encoding="utf-8")
            origem = base / modulo.ARQUIVOS["C06"]
            origem.parent.mkdir(parents=True, exist_ok=True)
            origem.write_text("Quero agendar, mas não sei o protocolo.", encoding="utf-8")
            root.__truediv__.side_effect = lambda nome: base / nome
            carregar.return_value = {
                "llm": {"modelo": "modelo-falso", "temperatura": 0.2,
                        "max_tokens": 2400, "timeout_s": 45}
            }
            conversar.return_value = {
                "texto": "MINUTA — NÃO ENVIADA", "modelo": "modelo-falso",
                "tokens_entrada": 10, "tokens_saida": 8
            }
            pasta, sucesso = modulo.executar(["C06"], versao="v4")
            self.assertTrue(sucesso)
            self.assertEqual(conversar.call_count, 1)
            self.assertEqual(pasta.parent.name, "prompts_b_v4_real")
            self.assertTrue((pasta / "prompt_B_v4_utilizado.md").is_file())
            self.assertTrue((pasta / "C06_prompt_B_v4_saida.txt").is_file())
            self.assertFalse((base / "resultados/execucoes/prompts_b_v3_real").exists())
            with (pasta / "matriz_B_v4.csv").open(encoding="utf-8", newline="") as f:
                linhas = list(csv.DictReader(f))
            self.assertEqual(len(linhas), 1)
            self.assertEqual(linhas[0]["versao_prompt"], "B_v4")
            self.assertEqual(linhas[0]["status"], "sucesso")
            self.assertEqual(linhas[0]["decisao_humana"], "")

    @patch.object(modulo, "ROOT")
    @patch.object(modulo, "chave", return_value="token-falso")
    @patch.object(modulo, "carregar")
    @patch.object(modulo, "conversar")
    def test_checar_v4_nao_chama_api(self, conversar, carregar, chave, root):
        with tempfile.TemporaryDirectory() as temporario:
            base = Path(temporario)
            arquivo_prompt = base / modulo.PROMPTS["v4"]
            arquivo_prompt.parent.mkdir(parents=True, exist_ok=True)
            arquivo_prompt.write_text("Texto {{solicitacao}}", encoding="utf-8")
            origem = base / modulo.ARQUIVOS["C01"]
            origem.parent.mkdir(parents=True, exist_ok=True)
            origem.write_text("Pedido fictício", encoding="utf-8")
            root.__truediv__.side_effect = lambda nome: base / nome
            carregar.return_value = {"llm": {"modelo": "modelo-falso"}}
            pasta, sucesso = modulo.executar(["C01"], versao="v4", somente_checar=True)
            self.assertIsNone(pasta)
            self.assertTrue(sucesso)
            conversar.assert_not_called()


if __name__ == "__main__":
    unittest.main()
