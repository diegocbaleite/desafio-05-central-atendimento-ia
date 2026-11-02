"""Regressões de segredos: somente credenciais fictícias e HTTP simulado."""

import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests

from src import cliente, guardrails
from src.config import carregar
from src.desafio6.servicos import ClienteOpenAI, ErroServico
from src.geracao import GeradorLLM
from src.llm_json import chamar_json
from src.orcamento import Orcamento
from src.rag import responder


class TestProtecaoSegredos(unittest.TestCase):
    def setUp(self):
        self.cfg = copy.deepcopy(carregar())
        self.segredo = "credencial-ficticia-auditoria-82910"
        self.addCleanup(patch.stopall)
        patch.dict(os.environ, {"OPENAI_API_KEY": self.segredo}).start()
        patch("src.cliente.carregar", return_value=self.cfg).start()
        patch("src.cliente.chave", return_value=self.segredo).start()
        self.post = patch("src.cliente.requests.post").start()
        self.post.return_value = self.resposta("{}")
        self.orcamento = Orcamento(5, 60000)

    @staticmethod
    def resposta(texto):
        return Mock(status_code=200, ok=True, headers={}, json=lambda: {
            "choices": [{"message": {"content": texto}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 2},
        })

    def test_segredo_em_mensagem_ou_esquema_bloqueia_antes_do_orcamento(self):
        for mensagens, formato in (
            ([{"role": "user", "content": self.segredo}], None),
            ([{"role": "user", "content": [{"type": "text", "text": self.segredo}]}], None),
            ([], {"type": "json_schema", "json_schema": {"schema": {
                "type": "string", "description": self.segredo}}}),
        ):
            with self.subTest(formato=bool(formato)):
                with self.assertRaises(cliente.ErroAPI) as erro:
                    cliente.conversar(mensagens, response_format=formato, orcamento=self.orcamento)
                self.assertNotIn(self.segredo, str(erro.exception))
        self.post.assert_not_called()
        self.assertEqual(self.orcamento.chamadas, 0)

    def test_credencial_de_outro_provedor_e_padrao_nao_configurado(self):
        padrao = "sk-" + "x" * 24
        outra = "credencial-ficticia-outro-provedor"
        with patch.dict(os.environ, {"GROQ_API_KEY": outra}):
            for valor in (outra, padrao):
                with self.subTest(origem="configurada" if valor == outra else "padrao"):
                    with self.assertRaises(cliente.ErroAPI) as erro:
                        cliente.conversar([{"role": "user", "content": valor}])
                    self.assertNotIn(valor, str(erro.exception))
        self.post.assert_not_called()

    def test_confere_novamente_antes_de_repetir_falha_transitoria(self):
        mensagens = [{"role": "user", "content": "Solicitacao ficticia de matricula"}]

        def timeout_com_mudanca(*args, **kwargs):
            mensagens[0]["content"] = self.segredo
            raise requests.Timeout()

        self.post.side_effect = timeout_com_mudanca
        with patch("src.cliente.time.sleep"), self.assertRaises(cliente.ErroAPI) as erro:
            cliente.conversar(mensagens, orcamento=self.orcamento)
        self.assertNotIn(self.segredo, str(erro.exception))
        self.assertEqual(self.post.call_count, 1)
        self.assertEqual(self.orcamento.chamadas, 1)

    def test_segredo_na_resposta_nao_chega_ao_validador_nem_a_correcao(self):
        for texto in (self.segredo, json.dumps({"valor": self.segredo})):
            with self.subTest(saida_json=texto.startswith("{")):
                self.post.reset_mock()
                self.post.return_value = self.resposta(texto)
                validar = Mock(return_value={"valido": False})
                with self.assertRaises(cliente.ErroAPI) as erro:
                    chamar_json([{"role": "user", "content": "Pedido ficticio"}],
                                validar, self.cfg["geracao"]["perfis"]["principal"])
                self.assertNotIn(self.segredo, str(erro.exception))
                self.assertEqual(self.post.call_count, 1)
                validar.assert_not_called()

    def test_json_com_escape_unicode_nao_oculta_credencial(self):
        segredo = "credencial-fictícia-com-acentuação"
        with patch.dict(os.environ, {"OPENAI_API_KEY": segredo}), \
             patch("src.cliente.chave", return_value=segredo):
            self.post.return_value = self.resposta(json.dumps({"valor": segredo}))
            with self.assertRaises(cliente.ErroAPI) as erro:
                cliente.conversar([{"role": "user", "content": "Pedido ficticio"}])
            self.assertNotIn(segredo, str(erro.exception))
        self.assertEqual(self.post.call_count, 1)

    def test_erro_http_nao_expoe_credencial_de_outro_provedor(self):
        outra = "credencial-ficticia-outro-provedor"
        self.post.return_value = Mock(status_code=400, json=lambda: {
            "error": {"message": outra}})
        with patch.dict(os.environ, {"GROQ_API_KEY": outra}):
            with self.assertRaises(cliente.ErroAPI) as erro:
                cliente.conversar([{"role": "user", "content": "Pedido ficticio"}])
            self.assertNotIn(outra, str(erro.exception))
        self.assertEqual(self.post.call_count, 1)

    def test_json_invalido_sem_segredo_continua_com_uma_correcao(self):
        self.post.side_effect = [self.resposta("invalido"), self.resposta("{}")]
        def validar(texto):
            return {"valido": texto == "{}", "erros_sintaxe": [],
                    "erros_esquema": [], "erros_regras": []}
        resultado = chamar_json([{"role": "user", "content": "Pedido ficticio"}],
                                validar, self.cfg["geracao"]["perfis"]["principal"],
                                orcamento=self.orcamento)
        self.assertTrue(resultado["valido"])
        self.assertEqual(self.post.call_count, 2)
        self.assertEqual(self.orcamento.chamadas, 2)

    def test_entrada_com_segredo_bloqueia_sem_consulta_ao_indice(self):
        indice, gerador = Mock(), Mock()
        indice.nome_colecao, indice.versao_indice = "teste", "1"
        resultado = responder("Matricula " + self.segredo, indice=indice,
                              gerador=gerador, cfg=self.cfg, auditar=False)
        self.assertEqual(resultado["status"], "bloqueada")
        indice.buscar.assert_not_called()
        gerador.gerar.assert_not_called()
        self.assertEqual(guardrails.avaliar_entrada(
            "Matricula " + self.segredo, self.cfg)["decisao"], "bloquear")

    def test_padrao_nao_configurado_na_entrada_e_omitido_da_auditoria(self):
        segredo = "sk-" + "y" * 24
        indice, gerador = Mock(), Mock()
        indice.nome_colecao, indice.versao_indice = "teste", "1"
        with tempfile.TemporaryDirectory() as pasta:
            auditoria = Path(pasta) / "auditoria.jsonl"
            resultado = responder("Matricula " + segredo, indice=indice, gerador=gerador,
                                  cfg=self.cfg, arquivo_auditoria=auditoria)
            self.assertNotIn(segredo, auditoria.read_text(encoding="utf-8"))
        self.assertEqual(resultado["status"], "bloqueada")
        indice.buscar.assert_not_called()
        self.post.assert_not_called()

    def test_rag_bloqueia_segredo_em_indice_preexistente_sem_exibir_ou_auditar(self):
        for campo in ("texto", "titulo", "chunk_id"):
            with self.subTest(campo=campo):
                trecho = {"chunk_id": "DOC-TESTE:v1:A:p0:s1:c0", "texto": "Orientacao ficticia de matricula.",
                          "similaridade": 0.9, "distancia_cosseno": 0.1, "posicao": 1,
                          "metadados": {"doc_id": "DOC-TESTE", "titulo": "Documento ficticio",
                                        "versao": "1", "secao": "Matricula", "pagina": -1,
                                        "suspeito_injecao": False, "documento_suspeito": False}}
                alvo = trecho["metadados"] if campo == "titulo" else trecho
                alvo[campo] += " " + self.segredo
                indice = SimpleNamespace(nome_colecao="teste_segredo", versao_indice="1",
                                         embedder=SimpleNamespace(nome="simulado"), buscar=lambda *a: [trecho])
                with tempfile.TemporaryDirectory() as pasta:
                    auditoria = Path(pasta) / "auditoria.jsonl"
                    resultado = responder("Como solicitar matricula?", indice=indice, cfg=self.cfg,
                        gerador=GeradorLLM("principal", self.cfg["geracao"]["perfis"]["principal"]),
                        arquivo_auditoria=auditoria, orcamento=self.orcamento)
                    self.assertNotIn(self.segredo, auditoria.read_text(encoding="utf-8"))
                self.assertEqual(resultado["status"], "bloqueada")
                self.assertTrue(resultado["quarentena"])
                self.assertNotIn(self.segredo, json.dumps(resultado))
        self.post.assert_not_called()
        self.assertEqual(self.orcamento.chamadas, 0)

    def test_adaptador_llm_direto_tambem_bloqueia_contexto(self):
        gerador = GeradorLLM("principal", self.cfg["geracao"]["perfis"]["principal"])
        with self.assertRaises(cliente.ErroAPI):
            gerador.gerar("Matricula " + self.segredo, [])
        self.post.assert_not_called()

    def test_adaptador_paralelo_bloqueia_geracao_e_embeddings(self):
        with patch("src.desafio6.servicos.chave", return_value=self.segredo):
            for endpoint, payload in (
                ("/chat/completions", {"messages": [{"content": self.segredo}]}),
                ("/embeddings", {"input": [self.segredo]}),
            ):
                with self.subTest(endpoint=endpoint):
                    servico = ClienteOpenAI(cfg=self.cfg)
                    with self.assertRaises(ErroServico) as erro:
                        servico._requisitar(endpoint, payload, tokens=100)
                    self.assertNotIn(self.segredo, str(erro.exception))
                    self.assertEqual(servico.orcamento.chamadas, 0)
        self.post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
