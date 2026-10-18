"""Decisões carregadas de YAML não podem aprovar minutas nem acionar TTS."""

import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from src import main


class TestDecisoesSimuladas(unittest.TestCase):
    def test_aprovacao_yaml_fica_pendente_e_nao_gera_audio(self):
        with tempfile.TemporaryDirectory() as temp:
            raiz = Path(temp)
            arquivo = raiz / "dados" / "originais" / "C01.txt"
            arquivo.parent.mkdir(parents=True)
            arquivo.write_text("texto fictício", encoding="utf-8")
            schema = raiz / "src" / "schemas"
            schema.mkdir(parents=True)
            origem_schema = main.ROOT / "src" / "schemas" / "extracao.schema.json"
            (schema / "extracao.schema.json").write_bytes(origem_schema.read_bytes())
            pasta_execucao = raiz / "resultados" / "execucao"
            pasta_minutas = raiz / "resultados" / "minutas" / "execucao"
            eventos = []

            def registrar(*args, **kwargs):
                eventos.append((args, kwargs))
                return pasta_execucao

            ext = {
                "campos": {},
                "campos_ausentes": [],
                "categoria": {"codigo": "outros"},
                "alerta_injecao": False,
            }
            with (
                patch("src.main.ROOT", raiz),
                patch("src.main.registrar", side_effect=registrar),
                patch("src.main.preparar_entrada", return_value="texto fictício"),
                patch("src.main.extrair", return_value=ext),
                patch("src.main.redigir", return_value=("# MINUTA", {})),
                patch("src.main.gerar_voz") as sintetizar,
                patch("jsonschema.validate"),
            ):
                resultado = main.executar_caso(
                    {
                        "id": "C01",
                        "arquivo": "dados/originais/C01.txt",
                        "modalidade": "texto",
                    },
                    "execucao",
                    decisao="aprovar",
                    decisao_simulada=True,
                )

            pasta_caso = pasta_minutas / "C01"
            self.assertFalse((pasta_caso / "minuta_aprovada.md").exists())
            self.assertTrue((pasta_caso / "minuta_pendente.md").exists())
            sintetizar.assert_not_called()
            self.assertTrue(resultado["decisao_simulada"])
            self.assertEqual(resultado["estado_revisao"], "decisao_simulada")
            self.assertTrue(
                any(
                    args[2] == "decisao_simulada" and kwargs["simulada"]
                    for args, kwargs in eventos
                )
            )

    def test_aprovacao_de_saida_mock_nao_cria_aprovada_nem_tts(self):
        with tempfile.TemporaryDirectory() as temp:
            raiz = Path(temp)
            arquivo = raiz / "dados" / "originais" / "C01.txt"
            arquivo.parent.mkdir(parents=True)
            arquivo.write_text("texto fictício", encoding="utf-8")
            schema = raiz / "src" / "schemas"
            schema.mkdir(parents=True)
            origem_schema = main.ROOT / "src" / "schemas" / "extracao.schema.json"
            (schema / "extracao.schema.json").write_bytes(origem_schema.read_bytes())
            pasta_execucao = raiz / "resultados" / "execucao"
            pasta_minutas = raiz / "resultados" / "minutas" / "execucao"

            def registrar(*args, **kwargs):
                return pasta_execucao

            ext = {
                "campos": {},
                "campos_ausentes": [],
                "categoria": {"codigo": "outros"},
                "alerta_injecao": False,
            }
            with (
                patch("src.main.ROOT", raiz),
                patch("src.main.registrar", side_effect=registrar),
                patch("src.main.preparar_entrada", return_value="texto fictício"),
                patch("src.main.extrair", return_value=ext),
                patch("src.main.redigir", return_value=("# MINUTA SIMULADA", {})),
                patch("src.main.gerar_voz") as sintetizar,
                patch("jsonschema.validate"),
            ):
                resultado = main.executar_caso(
                    {
                        "id": "C01",
                        "arquivo": "dados/originais/C01.txt",
                        "modalidade": "texto",
                    },
                    "execucao",
                    mock=True,
                    decisao="aprovar",
                )

            pasta_caso = pasta_minutas / "C01"
            self.assertFalse((pasta_caso / "minuta_aprovada.md").exists())
            self.assertTrue(resultado["execucao_mock"])
            self.assertTrue(resultado["simulada"])
            sintetizar.assert_not_called()


class TestComandoImagem(unittest.TestCase):
    @patch("src.main.gerar", return_value="imagem-gerada.png")
    def test_usa_provedor_configurado_sem_mock(self, gerar):
        with patch.object(sys, "argv", ["main", "imagem"]), redirect_stdout(StringIO()):
            main.main()
        gerar.assert_called_once()

    @patch("src.main.gerar")
    @patch("src.main.imagem_local", return_value="imagem-local.png")
    def test_mock_forca_composicao_local(self, imagem_local, gerar):
        with (
            patch.object(sys, "argv", ["main", "imagem", "--mock"]),
            redirect_stdout(StringIO()),
        ):
            main.main()
        imagem_local.assert_called_once()
        gerar.assert_not_called()


if __name__ == "__main__":
    unittest.main()
