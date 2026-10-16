"""Não chama APIs reais: garante trilha de execução e evita sobrescritas."""
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src import experimento

class TestExperimento(unittest.TestCase):
    def test_diretorios_distintos(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            a=experimento._pasta_unica(base)
            b=experimento._pasta_unica(base)
            self.assertNotEqual(a,b)
            self.assertTrue(a.is_dir())
            self.assertTrue(b.is_dir())

    @patch("src.experimento.ROOT")
    @patch("src.experimento.carregar_casos")
    @patch("src.experimento.carregar")
    @patch("src.experimento.conversar")
    def test_erro_de_uma_chamada_nao_apaga_evidencias(self, conversar, carregar, casos, raiz):
        from src.config import ROOT
        from shutil import copytree
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            (base/"prompts/experimento").mkdir(parents=True)
            for nome in ("prompt_A.md","prompt_B.md","metaprompt.md"):
                (base/"prompts/experimento"/nome).write_text("Minuta {{solicitacao}}",encoding="utf-8")
            (base/"dados").mkdir()
            (base/"dados"/"caso.txt").write_text("Agendamento fictício",encoding="utf-8")
            raiz.__truediv__.side_effect=lambda parte: base/parte
            carregar.return_value={"llm":{"provider":"openrouter","modelo":"modelo-teste","temperatura":0.2}}
            casos.return_value=[{"id":n,"arquivo":"dados/caso.txt"} for n in ("C01","C05","C06")]
            contador=[0]
            def resposta(*args,**kwargs):
                contador[0]+=1
                if contador[0]==2:
                    raise experimento.ErroAPI("falha simulada")
                return {"texto":"resposta de teste","provider":"openrouter","modelo":"modelo-teste",
                        "tokens_entrada":2,"tokens_saida":3}
            conversar.side_effect=resposta
            experimento.executar()
            saidas=list((base/"resultados/experimento_prompts/real").glob("*/matriz.csv"))
            self.assertEqual(len(saidas),1)
            with saidas[0].open(encoding="utf-8") as f:
                linhas=list(csv.DictReader(f))
            self.assertEqual(len(linhas),9)
            self.assertEqual(sum(x["status"]=="falha" for x in linhas),1)
            self.assertTrue((saidas[0].parent/"C01_prompt_B_saida.txt").exists())
            self.assertFalse((saidas[0].parent/"C01_prompt_A_saida.txt").exists())

if __name__=="__main__":
    unittest.main()
