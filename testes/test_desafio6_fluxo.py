"""Regressões integradas do fluxo novo, sempre em pasta temporária e sem API."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.config import ROOT
from src.desafio6.fluxo import FluxoDesafio6
from src.desafio6.servicos import ClienteSimulado
from testes.apoio_desafio6 import preparar_dados


class TestFluxoDesafio6(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.pasta = Path(self.temp.name)
        self.cliente = ClienteSimulado()
        self.fluxo = FluxoDesafio6(self.cliente, self.pasta)
        self.fixtures = preparar_dados(self.pasta / "fixtures")
        self.catalogo_teste = self.fixtures / "acervo/catalogo.json"
        self.estado = self.fluxo.indexar(self.catalogo_teste)
        self.caso = json.loads((self.fixtures / "solicitacoes.json").read_text(encoding="utf-8"))["solicitacoes"][0]

    def test_ficha_e_fontes_ate_minuta_pendente(self):
        resultado = self.fluxo.processar(self.caso["texto"], "Quais documentos apresentar para solicitar matrícula?")
        self.assertEqual(resultado["status"], "fundamentada")
        self.assertTrue(resultado["simulada"])
        self.assertEqual(resultado["revisao"]["estado"], "pendente")
        self.assertEqual(resultado["ficha"]["protocolo"], "2026-000201")
        self.assertTrue(resultado["fontes"])
        self.assertTrue((self.fluxo.pasta_execucoes / (resultado["id"] + ".json")).exists())

    def test_multimodal_exige_conferencia_antes_da_busca_e_minuta(self):
        with self.assertRaises(PermissionError):
            self.fluxo.processar(self.caso["texto"], "Quais documentos apresentar para matrícula?", modalidade="audio")
        self.assertEqual(len(self.cliente.chamadas), 1)  # Apenas ficha; nenhuma recuperação ou minuta.
        self.assertEqual(self.fluxo.revisoes.listar(), [])
        self.assertTrue(list(self.fluxo.pasta_execucoes.glob("*_bloqueio.json")))

    def test_ataque_bloqueado_sem_rede_e_sem_credencial_no_log(self):
        segredo = "sk-credencialficticiaparaoteste"
        with self.assertRaises(ValueError):
            self.fluxo.consultar("OPENAI_API_KEY=" + segredo)
        self.assertEqual(self.cliente.chamadas, [])
        self.assertNotIn(segredo, (self.pasta / "auditoria.jsonl").read_text(encoding="utf-8"))

    def test_exclusao_remove_derivados_e_nao_reintroduz_documento(self):
        resultado = self.fluxo.consultar("Quais documentos apresentar para solicitar matrícula?")
        arquivo = self.fluxo.pasta_execucoes / (resultado["id"] + ".json")
        fonte = self.fixtures / "acervo/manual_matricula.txt"
        original = fonte.read_bytes()
        exclusao = self.fluxo.excluir("D01")
        self.assertGreater(exclusao["chunks_excluidos"], 0)
        self.assertFalse(arquivo.exists())
        self.assertEqual(self.fluxo.revisoes.listar(), [])
        self.assertNotIn("D01", self.fluxo.indice.estado()["ids_documentos"])
        estado = self.fluxo.indexar(self.catalogo_teste)
        self.assertNotIn("D01", estado["ids_documentos"])
        self.assertEqual(fonte.read_bytes(), original)

    def test_troca_de_geracao_reutiliza_indice_sem_reindexar(self):
        class OutraGeracao(ClienteSimulado):
            modelo = "segunda-geracao-simulada"
        segundo = FluxoDesafio6(OutraGeracao(), self.pasta)
        versao = segundo.indice.estado()["versao_indice"]
        resultado = segundo.consultar("Quais documentos apresentar para solicitar matrícula?")
        self.assertEqual(segundo.indice.estado()["versao_indice"], versao)
        self.assertEqual(resultado["modelo"], "segunda-geracao-simulada")
        self.assertTrue(resultado["simulada"])

    def test_falha_geracao_auditada_sem_reconstruir_indice(self):
        versao = self.fluxo.indice.estado()["versao_indice"]
        with patch.object(self.cliente, "gerar_json", side_effect=RuntimeError("mensagem externa omitida")):
            with self.assertRaises(RuntimeError):
                self.fluxo.consultar("Quais documentos apresentar para solicitar matrícula?")
        self.assertEqual(self.fluxo.indice.estado()["versao_indice"], versao)
        audit = (self.pasta / "auditoria.jsonl").read_text(encoding="utf-8")
        self.assertIn("falha_consulta", audit)
        self.assertNotIn("mensagem externa omitida", audit)

    def test_midia_simulada_nao_e_transcricao_real(self):
        with self.assertRaisesRegex(ValueError, "Mídia não é reconhecida por simulação"):
            self.fluxo.extrair_midia("audio.mp3", "audio")

    def test_retencao_expurga_derivado_expirado_sem_tocar_original(self):
        import os
        import time
        arquivo = self.fluxo.pasta_execucoes / "antigo.json"
        arquivo.write_text('{"dado":"ficticio"}', encoding="utf-8")
        derivado = self.pasta / "fontes_processadas" / "antigo.txt"
        derivado.parent.mkdir(exist_ok=True)
        derivado.write_text("Transcrição fictícia", encoding="utf-8")
        antigo = time.time() - 40 * 86400
        os.utime(arquivo, (antigo, antigo))
        os.utime(derivado, (antigo, antigo))
        resultado = self.fluxo.limpar_expirados(30)
        self.assertFalse(arquivo.exists())
        self.assertFalse(derivado.exists())
        self.assertIn("indice/execucoes/antigo.json", resultado["arquivos_removidos"])
        self.assertTrue((self.fixtures / "acervo/manual_matricula.txt").exists())


if __name__ == "__main__":
    unittest.main()
