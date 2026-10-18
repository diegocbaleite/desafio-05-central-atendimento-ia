"""Consistência entre o catálogo atual, a demonstração e a documentação ativa."""

import csv
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from src.config import ROOT
from src import main


class TestDocumentacaoCasos(unittest.TestCase):
    def test_catalogo_rejeita_id_desconhecido(self):
        with self.assertRaisesRegex(ValueError, "não encontrado"):
            main.carregar_casos(["CASO_INEXISTENTE"])

    def test_catalogo_valida_referencia_multimodal_declarada(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            (raiz / "dados/originais").mkdir(parents=True)
            (raiz / "dados/originais/audio.mp3").write_bytes(b"ID3fake")
            (raiz / "dados/originais/casos.yaml").write_text(
                "casos:\n"
                "  - id: A99\n"
                "    modalidade: audio\n"
                "    arquivo: dados/originais/audio.mp3\n"
                "    transcricao_referencia: referencias/ausente.txt\n",
                encoding="utf-8",
            )
            with (
                patch("src.main.ROOT", raiz),
                patch(
                    "src.main.carregar",
                    return_value={"projeto": {"casos": "dados/originais/casos.yaml"}},
                ),
            ):
                with self.assertRaisesRegex(ValueError, "referência de mock ausente"):
                    main.carregar_casos(exigir_referencias=True)

    def test_catalogo_rejeita_yaml_malformado(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            (raiz / "dados/originais").mkdir(parents=True)
            (raiz / "dados/originais/casos.yaml").write_text(
                "casos: [id: T01", encoding="utf-8"
            )
            with (
                patch("src.main.ROOT", raiz),
                patch(
                    "src.main.carregar",
                    return_value={"projeto": {"casos": "dados/originais/casos.yaml"}},
                ),
            ):
                with self.assertRaisesRegex(ValueError, "YAML inválido"):
                    main.carregar_casos()

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

    def test_referencias_multimodais_declaradas_existem_e_nao_estao_vazias(self):
        casos = yaml.safe_load(
            (ROOT / "dados/originais/casos.yaml").read_text(encoding="utf-8")
        )["casos"]

        referencias = {
            "A01": "transcricao_referencia",
            "I01": "ocr_referencia",
        }
        casos_por_id = {caso["id"]: caso for caso in casos}

        for caso_id, campo in referencias.items():
            with self.subTest(caso=caso_id):
                caminho_relativo = casos_por_id[caso_id].get(campo)
                self.assertIsNotNone(caminho_relativo)
                caminho = ROOT / caminho_relativo
                self.assertTrue(caminho.is_file())
                self.assertTrue(caminho.read_text(encoding="utf-8").strip())

    def test_avaliacao_rf13_atual_cobre_todos_os_casos_e_prompts_textuais(self):
        caminho = ROOT / "documentacao/avaliacao_rf13_catalogo_atual.csv"
        with caminho.open(encoding="utf-8", newline="") as arquivo:
            linhas = list(csv.DictReader(arquivo))

        combinacoes = {(linha["caso"], linha["prompt"]) for linha in linhas}
        esperadas = {
            (caso, prompt)
            for caso in ("T01", "X01", "X02")
            for prompt in ("A", "B", "C")
        }
        self.assertEqual(esperadas, combinacoes)
        self.assertEqual(9, len(linhas))
        for linha in linhas:
            notas = [
                int(linha[campo])
                for campo in (
                    "fidelidade",
                    "completude",
                    "formato",
                    "linguagem",
                    "seguranca",
                )
            ]
            self.assertTrue(all(0 <= nota <= 2 for nota in notas))
            self.assertEqual(sum(notas), int(linha["total"]))

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
