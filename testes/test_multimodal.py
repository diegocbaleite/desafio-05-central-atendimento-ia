"""Teste determinístico de insumos com voz fictícia (sem exposição de pessoas)."""
import json
import unittest
from pathlib import Path
from src.config import ROOT
from src.extracao import extrair
from src.seguranca import detectar
class TestCasos(unittest.TestCase):
    def test_gabaritos_antes_da_execucao(self):
        for n in ("C01","C02","C03","C04","C05","C06"):
            esperado=json.loads((ROOT/f"dados/gabaritos/{n}.json").read_text(encoding="utf-8"))
            self.assertEqual(n,esperado["caso_id"])
    def test_entrada_injecao_c05(self):
        texto=(ROOT/"dados/originais/C05.txt").read_text(encoding="utf-8")
        self.assertTrue(detectar(texto))
    def test_campos_fonte(self):
        f=ROOT/"dados/originais/C01.txt"
        x=extrair(f.read_text(encoding="utf-8"),"C01",str(f),"a"*64,"texto")
        self.assertEqual(x["campos"]["protocolo"]["valor"],"2026.000123")
        self.assertTrue(x["campos"]["protocolo"]["evidencia"])
        self.assertTrue(x["requer_revisao"])
    def test_textos_auxiliares_nao_sao_stt_ocr(self):
        for nome in ("C02_transcricao_ficticia.txt","C03_ocr_ficticio.txt"):
            self.assertIn("fictíci", (ROOT/"dados/originais"/nome).read_text(encoding="utf-8").lower())
if __name__=="__main__": unittest.main()
