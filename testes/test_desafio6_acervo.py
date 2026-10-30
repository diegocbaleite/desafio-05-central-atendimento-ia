"""Descoberta e rastreabilidade do acervo fornecido sem chamadas pagas."""

import tempfile
import unittest
from pathlib import Path

from src.desafio6.acervo import carregar_catalogo_originais, preparar_documentos, sha256
from src.desafio6.avaliacao import executar_avaliacao
from src.desafio6.indice import IndiceVetorial
from src.desafio6.servicos import ClienteSimulado


class TestAcervoOriginal(unittest.TestCase):
    def test_descoberta_preserva_arquivos_e_exclui_brasao_e_configuracao(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            (raiz / "documento.txt").write_text("Documento de matrícula fornecido.", encoding="utf-8")
            (raiz / "entrada_audio.mp3").write_bytes(b"ID3fake")
            (raiz / "brasao.png").write_bytes(b"brasao")
            (raiz / "casos.yaml").write_text("casos: []", encoding="utf-8")
            itens = carregar_catalogo_originais(raiz)["documentos"]
            self.assertEqual({Path(i["arquivo"]).name for i in itens}, {"documento.txt", "entrada_audio.mp3"})
            self.assertEqual(len({i["id"] for i in itens}), 2)
            self.assertTrue(all(i["versao"] == "não localizado" for i in itens))

    def test_mock_rotula_referencia_sem_fingir_reconhecimento(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            arquivo = raiz / "entrada_audio.mp3"
            arquivo.write_bytes(b"ID3fake")
            original = sha256(arquivo)
            itens = carregar_catalogo_originais(raiz)["documentos"]
            preparado = preparar_documentos(itens, raiz / "derivados", ClienteSimulado())[0]
            self.assertIn("não é execução", preparado["metodo_extracao"])
            self.assertEqual(preparado["sha256_original"], original)
            self.assertEqual(sha256(arquivo), original)
            self.assertTrue(preparado["requer_conferencia_humana"])

    def test_alteracao_original_invalida_indice_de_derivado(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            arquivo = raiz / "entrada_audio.mp3"
            arquivo.write_bytes(b"ID3fake")
            cliente = ClienteSimulado()
            itens = preparar_documentos(carregar_catalogo_originais(raiz)["documentos"], raiz / "derivados", cliente)
            indice = IndiceVetorial(raiz / "indice", cliente)
            indice.indexar(itens)
            self.assertFalse(indice.estado()["desatualizado"])
            arquivo.write_bytes(b"ID3alterado")
            self.assertTrue(indice.estado()["desatualizado"])

    def test_midia_sem_referencia_nao_e_inventada(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            (raiz / "outro_audio.mp3").write_bytes(b"ID3fake")
            with self.assertRaisesRegex(ValueError, "Sem referência humana"):
                preparar_documentos(carregar_catalogo_originais(raiz)["documentos"], raiz / "derivados", ClienteSimulado())

    def test_avaliacao_exige_novos_dados_e_gabaritos(self):
        with self.assertRaisesRegex(ValueError, "gabaritos prévios"):
            executar_avaliacao(mock=True)

    def test_extracao_com_credencial_nao_e_salva(self):
        class ClienteTeste:
            simulado = False
            cfg = {"multimodal": {"stt_modelo": "modelo-teste"}}
            def transcrever(self, caminho):
                return "OPENAI_API_KEY=credencial-ficticia"
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            (raiz / "audio.mp3").write_bytes(b"ID3fake")
            with self.assertRaisesRegex(ValueError, "credencial"):
                preparar_documentos(carregar_catalogo_originais(raiz)["documentos"], raiz / "derivados", ClienteTeste())
            self.assertEqual(list((raiz / "derivados").glob("*.txt")), [])


if __name__ == "__main__":
    unittest.main()
