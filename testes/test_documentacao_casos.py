"""Consistência entre o catálogo atual, a demonstração e a documentação ativa."""

import re
import unittest

import yaml

from src.config import ROOT


class TestDocumentacaoCasos(unittest.TestCase):
    def test_decisoes_demo_usam_exatamente_os_casos_atuais(self):
        casos = yaml.safe_load(
            (ROOT / "dados/originais/casos.yaml").read_text(encoding="utf-8")
        )["casos"]
        decisoes = yaml.safe_load(
            (ROOT / "dados/revisao/decisoes_demo.yaml").read_text(encoding="utf-8")
        )

        self.assertEqual({caso["id"] for caso in casos}, set(decisoes))
        self.assertTrue(
            set(decisoes.values()).issubset({"aprovar", "rejeitar", "corrigir", "nova"})
        )

    def test_documentacao_ativa_nao_cita_identificadores_substituidos(self):
        arquivos = [
            ROOT / "README.md",
            ROOT / "documentacao/matriz_requisitos.md",
            ROOT / "documentacao/lgpd.md",
            ROOT / "documentacao/protocolo_avaliacao.md",
            ROOT / "documentacao/relatorio_tecnico.md",
            ROOT / "documentacao/uso_da_ia.md",
        ]

        for arquivo in arquivos:
            with self.subTest(arquivo=arquivo.name):
                texto = arquivo.read_text(encoding="utf-8")
                self.assertIsNone(re.search(r"\bC0[1-9]\b", texto))


if __name__ == "__main__":
    unittest.main()
