"""Inclusão de mídia fictícia: extração simulada, conferência, fontes e exclusão."""

import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pypdf import PdfWriter

from src.acervo_upload import extrair_documento, salvar_documento
from src.config import ROOT
from src.embeddings import EmbedderHash
from src.indice import IndiceVetorial
from src.ingestao import carregar_catalogo
from src.privacidade import excluir_documento_e_derivados, _remover_de_catalogo_enviados
from testes.d6_apoio import cfg_teste


def pdf_ficticio(paginas):
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    writer = PdfWriter()
    for texto in paginas:
        pagina = writer.add_blank_page(width=300, height=300)
        if texto:
            fonte = DictionaryObject({NameObject("/Type"): NameObject("/Font"),
                                      NameObject("/Subtype"): NameObject("/Type1"),
                                      NameObject("/BaseFont"): NameObject("/Helvetica")})
            pagina[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({
                NameObject("/F1"): writer._add_object(fonte)})})
            stream = DecodedStreamObject()
            stream.set_data(("BT /F1 12 Tf 20 20 Td (" + texto + ") Tj ET").encode("ascii"))
            pagina[NameObject("/Contents")] = writer._add_object(stream)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


class TestAcervoUpload(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.tmp.cleanup)
        self.pasta = Path(self.tmp.name)
        self.cfg = cfg_teste()
        catalogo = self.pasta / "catalogo_original.yaml"
        catalogo.write_text("documentos: []\n", encoding="utf-8")
        self.cfg["acervo"].update(catalogo=str(catalogo),
            catalogo_enviados=str(self.pasta / "enviados/catalogo.yaml"),
            diretorio_enviados=str(self.pasta / "enviados"))

    def salvar(self, preparado, conteudo, **kwargs):
        return salvar_documento(preparado, conteudo, preparado["paginas"], documento_id="DOC-08",
            titulo="Orientacoes ficticias", versao="1.0", tema="atendimento", cfg=self.cfg,
            conferido=kwargs.pop("conferido", True), **kwargs)

    def test_audio_transcrito_conferido_indexado_e_excluido_com_derivado(self):
        audio = b"ID3audio-ficticio"
        with patch("src.audio.transcrever", return_value="O agendamento ficticio exige documento.") as stt:
            preparado = extrair_documento("orientacao.mp3", audio, self.cfg)
        stt.assert_called_once()
        self.assertFalse(Path(stt.call_args.args[0]).exists())  # temporário removido
        with self.assertRaisesRegex(ValueError, "Confira"):
            self.salvar(preparado, audio, conferido=False)
        item = self.salvar(preparado, audio)
        original, derivado = Path(item["arquivo"]), Path(item["texto_extraido"])
        self.assertEqual(original.read_bytes(), audio)
        docs = carregar_catalogo(self.cfg)
        ix = IndiceVetorial.de_config(self.cfg, EmbedderHash(), diretorio=self.pasta / "indice")
        resultado = ix.indexar(docs)
        self.assertGreater(resultado["trechos_depois"], 0)
        hits = ix.buscar("agendamento documento", 4)
        self.assertEqual(hits[0]["metadados"]["doc_id"], "DOC-08")
        self.assertEqual(hits[0]["metadados"]["pagina"], -1)
        rel = excluir_documento_e_derivados("DOC-08", cfg=self.cfg, indices=[ix],
            arquivo_auditoria=self.pasta / "auditoria.jsonl")
        self.assertEqual(rel["indices"][0]["trechos_restantes"], 0)
        self.assertFalse(original.exists())
        self.assertFalse(derivado.exists())
        self.assertEqual(carregar_catalogo(self.cfg), [])

    def test_limite_streamlit_e_acervo_10mib_com_fronteira_inclusiva(self):
        import tomllib
        from src.guardrails import validar_documento

        streamlit = tomllib.loads((ROOT / ".streamlit/config.toml").read_text(encoding="utf-8"))
        self.assertEqual(streamlit["server"]["maxUploadSize"], 10)
        self.assertEqual(self.cfg["guardrails"]["max_mb_documento"], 10)
        limite = 10 * 1024 * 1024
        audio = b"ID3" + b"0" * (limite - 3)
        with patch("src.audio.transcrever", return_value="Transcricao ficticia.") as stt:
            preparado = extrair_documento("audio.mp3", audio, self.cfg)
        stt.assert_called_once()
        self.assertEqual(preparado["paginas"][0]["texto"], "Transcricao ficticia.")
        with patch("src.audio.transcrever") as stt:
            with self.assertRaisesRegex(ValueError, "10 MiB"):
                extrair_documento("audio.mp3", audio + b"0", self.cfg)
            stt.assert_not_called()
        validar_documento("texto.txt", b"0" * limite, self.cfg)
        with self.assertRaisesRegex(ValueError, "10 MiB"):
            validar_documento("texto.txt", b"0" * (limite + 1), self.cfg)

    def test_pdf_misto_ocr_somente_na_pagina_sem_texto_e_fontes_preservadas(self):
        bruto = pdf_ficticio(["Orientacao textual ficticia.", None, "Ultima pagina ficticia."])
        with patch("src.visao._imagens_pdf", return_value=[self.pasta / "pagina.png"]) as render, \
             patch("src.visao.ler_imagem", return_value="Atendimento ficticio por agendamento.") as ocr:
            preparado = extrair_documento("misto.pdf", bruto, self.cfg, local=True)
        self.assertEqual([p["pagina"] for p in preparado["paginas"]], [1, 2, 3])
        self.assertEqual(preparado["metodos"], ["texto PDF", "OCR:local", "texto PDF"])
        self.assertEqual(render.call_args.kwargs["pagina_inicial"], 2)
        self.assertEqual(render.call_args.args[2], 1)
        self.assertEqual(ocr.call_args.kwargs["provider"], "local")
        self.salvar(preparado, bruto)
        docs = carregar_catalogo(self.cfg)
        ix = IndiceVetorial.de_config(self.cfg, EmbedderHash(), diretorio=self.pasta / "indice")
        ix.indexar(docs)
        hits = ix.buscar("atendimento agendamento", 1)
        self.assertEqual(hits[0]["metadados"]["pagina"], 2)
        self.assertIn("Atendimento ficticio", hits[0]["texto"])

    def test_pdf_digitalizado_nao_trunca_no_limite_antigo_de_tres_paginas(self):
        with patch("src.visao._imagens_pdf", return_value=[self.pasta / "pagina.png"]) as render, \
             patch("src.visao.ler_imagem", return_value="Texto ficticio de pagina."):
            preparado = extrair_documento("digitalizado.pdf", pdf_ficticio([None] * 4), self.cfg)
        self.assertEqual(len(preparado["paginas"]), 4)
        self.assertEqual([c.kwargs["pagina_inicial"] for c in render.call_args_list], [1, 2, 3, 4])

    def test_limite_pdf_e_audio_invalido_impedem_processamento(self):
        self.cfg["guardrails"]["max_paginas_pdf_documento"] = 1
        with patch("src.visao.ler_imagem") as ocr:
            with self.assertRaisesRegex(ValueError, "entre 1 e 1"):
                extrair_documento("excessivo.pdf", pdf_ficticio([None, None]), self.cfg)
            ocr.assert_not_called()
        with patch("src.audio.transcrever") as stt:
            with self.assertRaisesRegex(ValueError, "assinatura"):
                extrair_documento("falso.mp3", b"nao e audio", self.cfg)
            stt.assert_not_called()

    def test_falha_ou_extracao_vazia_nao_salva_documentos(self):
        for efeito in (RuntimeError("falha ficticia"), ""):
            with self.subTest(tipo=type(efeito).__name__):
                with patch("src.audio.transcrever", side_effect=efeito if isinstance(efeito, Exception) else None,
                           return_value=efeito):
                    with self.assertRaises((ValueError, RuntimeError)):
                        extrair_documento("audio.mp3", b"ID3ficticio", self.cfg)
        self.assertFalse((self.pasta / "enviados").exists())

    def test_segredo_na_extracao_ou_no_texto_editado_nao_e_salvo(self):
        segredo = "credencial-ficticia-acervo-82910"
        with patch.dict(os.environ, {"OPENAI_API_KEY": segredo}):
            with patch("src.audio.transcrever", return_value=segredo):
                with self.assertRaisesRegex(ValueError, "credencial"):
                    extrair_documento("audio.mp3", b"ID3ficticio", self.cfg)
            preparado = extrair_documento("texto.txt", b"Documento ficticio.", self.cfg)
            preparado["paginas"][0]["texto"] = segredo
            with self.assertRaisesRegex(ValueError, "credencial"):
                self.salvar(preparado, b"Documento ficticio.")
        self.assertFalse((self.pasta / "enviados").exists())

    def test_texto_ou_original_alterado_exige_nova_conferencia_sem_perder_vetores(self):
        preparado = extrair_documento("texto.txt", b"Documento ficticio para agendamento.", self.cfg)
        item = self.salvar(preparado, b"Documento ficticio para agendamento.")
        docs = carregar_catalogo(self.cfg)
        ix = IndiceVetorial.de_config(self.cfg, EmbedderHash(), diretorio=self.pasta / "indice")
        ix.indexar(docs)
        antes = ix.contar()
        Path(item["texto_extraido"]).write_text("alterado", encoding="utf-8")
        self.assertIn("DOC-08", ix.status(docs)["desatualizados"])
        with self.assertRaisesRegex(ValueError, "alterado"):
            ix.indexar(docs)
        self.assertEqual(ix.contar(), antes)

    def test_upload_trocado_id_duplicado_e_arquivo_existente_nao_sobrescrevem(self):
        preparado = extrair_documento("texto.txt", b"Documento ficticio.", self.cfg)
        with self.assertRaisesRegex(ValueError, "mudou"):
            self.salvar(preparado, b"Outro documento.")
        item = self.salvar(preparado, b"Documento ficticio.")
        with self.assertRaisesRegex(ValueError, "ID"):
            self.salvar(preparado, b"Documento ficticio.")
        self.assertEqual(Path(item["arquivo"]).read_bytes(), b"Documento ficticio.")

    def test_falha_no_catalogo_desfaz_apenas_arquivos_criados_na_operacao(self):
        preparado = extrair_documento("texto.txt", b"Documento ficticio.", self.cfg)
        with patch("src.acervo_upload.Path.replace", side_effect=OSError("falha ficticia")):
            with self.assertRaises(OSError):
                self.salvar(preparado, b"Documento ficticio.")
        self.assertEqual(list((self.pasta / "enviados").iterdir()), [])

    def test_exclusao_de_derivado_nao_pode_apontar_para_fora_dos_enviados(self):
        import yaml

        preparado = extrair_documento("texto.txt", b"Documento ficticio.", self.cfg)
        item = self.salvar(preparado, b"Documento ficticio.")
        protegido = self.pasta / "original_protegido.txt"
        protegido.write_bytes(b"original")
        catalogo = Path(self.cfg["acervo"]["catalogo_enviados"])
        dados = yaml.safe_load(catalogo.read_text(encoding="utf-8"))
        dados["documentos"][0]["texto_extraido"] = str(protegido)
        catalogo.write_text(yaml.safe_dump(dados), encoding="utf-8")
        antes = catalogo.read_bytes()
        with self.assertRaisesRegex(ValueError, "fora da pasta"):
            _remover_de_catalogo_enviados(self.cfg, "DOC-08", True)
        self.assertEqual(protegido.read_bytes(), b"original")
        self.assertTrue(Path(item["arquivo"]).exists())
        self.assertEqual(catalogo.read_bytes(), antes)


if __name__ == "__main__":
    unittest.main()
