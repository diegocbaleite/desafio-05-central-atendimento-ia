"""Casos, gabaritos prévios e fixtures sintéticos (sem pessoas reais)."""

import json
import unittest

import yaml

from src.avaliacao import avaliar_campos
from src.config import ROOT
from src.extracao import extrair
from src.seguranca import detectar

FIXTURES = ROOT / "testes" / "fixtures"


def _casos():
    return yaml.safe_load(
        (ROOT / "dados/originais/casos.yaml").read_text(encoding="utf-8")
    )["casos"]


class TestCasos(unittest.TestCase):
    def test_todo_caso_tem_gabarito_e_entrada(self):
        for caso in _casos():
            esperado = json.loads(
                (ROOT / f"dados/gabaritos/{caso['id']}.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(caso["id"], esperado["caso_id"])
            self.assertEqual(caso["modalidade"], esperado["modalidade"])
            self.assertTrue((ROOT / caso["arquivo"]).is_file(), caso["arquivo"])

    def test_cobre_texto_audio_e_imagem(self):
        self.assertEqual(
            {"texto", "audio", "imagem"}, {c["modalidade"] for c in _casos()}
        )

    def test_entrada_com_injecao_e_detectada(self):
        texto = (FIXTURES / "injecao.txt").read_text(encoding="utf-8")
        self.assertTrue(detectar(texto))

    def test_campos_fixture_completa(self):
        f = FIXTURES / "completa.txt"
        x = extrair(f.read_text(encoding="utf-8"), "X00", str(f), "a" * 64, "texto")
        self.assertEqual(x["campos"]["protocolo"]["valor"], "2026.000123")
        self.assertEqual(
            x["campos"]["solicitante"]["valor"], "Maria Fictícia Albuquerque"
        )
        self.assertTrue(x["campos"]["protocolo"]["evidencia"])
        self.assertTrue(x["requer_revisao"])

    def test_lacunas_sao_sinalizadas(self):
        f = FIXTURES / "lacunas.txt"
        x = extrair(f.read_text(encoding="utf-8"), "X02", str(f), "b" * 64, "texto")
        self.assertEqual(
            x["campos_ausentes"], ["protocolo", "solicitante", "data_solicitacao"]
        )

    def test_texto_fornecido_confere_com_gabarito_previo(self):
        caso = next(c for c in _casos() if c["id"] == "T01")
        entrada = ROOT / caso["arquivo"]
        x = extrair(
            entrada.read_text(encoding="utf-8"), "T01", caso["arquivo"], "c" * 64, "texto"
        )
        r = avaliar_campos(x)
        self.assertTrue(r["campos"]["protocolo"]["correto"])
        self.assertTrue(r["campos"]["data_solicitacao"]["correto"])
        self.assertTrue(r["categoria_corresponde"])
        self.assertTrue(r["alerta_injecao_corresponde"])

    def test_texto_sem_rotulos_extrai_assunto_e_pedidos_multiplo(self):
        entrada = ROOT / "dados/originais/entrada_texto.txt"
        x = extrair(
            entrada.read_text(encoding="utf-8"),
            "T01",
            str(entrada),
            "f" * 64,
            "texto",
        )
        self.assertEqual(
            x["campos"]["assunto"]["valor"],
            "efetivação da minha matrícula no curso Técnico em Enfermagem",
        )
        self.assertIn(
            "solicito a efetivação da minha matrícula",
            x["campos"]["pedido"]["valor"],
        )
        self.assertIn(
            "Peço que me informem quais documentos",
            x["campos"]["pedido"]["valor"],
        )
        self.assertIn(
            "Peço que me informem quais documentos",
            x["campos"]["pedido"]["evidencia"],
        )
        self.assertNotIn("123.456.789-00", x["campos"]["pedido"]["evidencia"])
        self.assertEqual(x["campos"]["data_solicitacao"]["valor"], "14/10/2026")

    def test_data_falada_por_extenso_e_normalizada(self):
        texto = (
            "Meu protocolo é 2026-000142, de 14 de outubro de 2026. "
            "Meu nome é Maria Fictícia Albuquerque."
        )
        x = extrair(texto, "X05", "x", "1" * 64, "audio")
        self.assertEqual(x["campos"]["data_solicitacao"]["valor"], "14/10/2026")
        self.assertEqual(x["campos"]["data_solicitacao"]["confianca"], "media")
        self.assertIn(
            "14 de outubro de 2026",
            x["campos"]["data_solicitacao"]["evidencia"],
        )

    def test_stt_protocolo_separado_e_decimal_no_pedido(self):
        texto = (
            "Meu protocolo é 2026-000-142 de 14 de outubro de 2026. "
            "Quero pedir a efetivação da matrícula no curso técnico com "
            "carga horária de 1.200 horas no turno. "
            "Peço que informem quais documentos preciso apresentar."
        )
        x = extrair(texto, "X07", "x", "3" * 64, "audio")
        self.assertEqual(x["campos"]["protocolo"]["valor"], "2026-000142")
        self.assertIn("1.200 horas", x["campos"]["pedido"]["valor"])
        self.assertIn("Peço que informem", x["campos"]["pedido"]["valor"])

    def test_data_de_nascimento_nao_vira_data_da_solicitacao(self):
        texto = "Nasci em 12/08/2008 e peço a matrícula."
        x = extrair(texto, "X03", "x", "d" * 64, "texto")
        self.assertEqual(x["campos"]["data_solicitacao"]["valor"], "não localizado")

    def test_data_de_nascimento_por_extenso_nao_vira_data_da_solicitacao(self):
        texto = "Nasci em 12 de agosto de 2008 e peço a matrícula."
        x = extrair(texto, "X06", "x", "2" * 64, "audio")
        self.assertEqual(x["campos"]["data_solicitacao"]["valor"], "não localizado")

    def test_protocolo_falado_e_reconhecido(self):
        x = extrair("Bom dia, meu protocolo é 2026-000142.", "X04", "x", "e" * 64, "audio")
        self.assertEqual(x["campos"]["protocolo"]["valor"], "2026-000142")


if __name__ == "__main__":
    unittest.main()
