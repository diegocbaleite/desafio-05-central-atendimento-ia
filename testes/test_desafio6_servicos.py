"""Orçamento e barreiras de serviço com HTTP simulado, sem crédito nem segredo real."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from src.desafio6.guardrails import avaliar_entrada, sanitizar, validar_documento, validar_saida
from src.desafio6.servicos import ClienteOpenAI, ErroServico, LimiteOrcamento, Orcamento
from testes.apoio_desafio6 import carregar_conjunto, preparar_dados

ESQUEMA = {"type": "object", "properties": {"ok": {"type": "boolean"}},
           "additionalProperties": False, "required": ["ok"]}


class TestServicoDesafio6(unittest.TestCase):
    def test_orcamento_impede_rede_antes_do_limite(self):
        cliente = ClienteOpenAI(orcamento=Orcamento(max_chamadas=0))
        with patch("src.desafio6.servicos.chave", return_value="credencial-ficticia"), \
             patch("src.desafio6.servicos.requests.post") as post:
            with self.assertRaises(LimiteOrcamento):
                cliente.gerar_json("Instrução", "Dado", ESQUEMA)
            post.assert_not_called()

    def test_retry_transitorio_conta_e_respeita_teto(self):
        cliente = ClienteOpenAI(orcamento=Orcamento(max_chamadas=1))
        with patch("src.desafio6.servicos.chave", return_value="credencial-ficticia"), \
             patch("src.desafio6.servicos.requests.post", side_effect=requests.Timeout()) as post, \
             patch("src.desafio6.servicos.time.sleep"):
            with self.assertRaises(LimiteOrcamento):
                cliente.gerar_json("Instrução", "Dado", ESQUEMA)
            self.assertEqual(post.call_count, 1)
            self.assertEqual(cliente.orcamento.chamadas, 1)

    def test_apenas_uma_repeticao_transitoria(self):
        cliente = ClienteOpenAI()
        falha = Mock(ok=False, status_code=503)
        with patch("src.desafio6.servicos.chave", return_value="credencial-ficticia"), \
             patch("src.desafio6.servicos.requests.post", return_value=falha) as post, \
             patch("src.desafio6.servicos.time.sleep"):
            with self.assertRaisesRegex(ErroServico, "503"):
                cliente.gerar_json("Instrução", "Dado", ESQUEMA)
            self.assertEqual(post.call_count, 2)

    def test_erro_nao_ecoa_corpo_com_segredo(self):
        cliente = ClienteOpenAI()
        falha = Mock(ok=False, status_code=401, text="credencial-ficticia")
        with patch("src.desafio6.servicos.chave", return_value="credencial-ficticia"), \
             patch("src.desafio6.servicos.requests.post", return_value=falha) as post:
            with self.assertRaises(ErroServico) as erro:
                cliente.gerar_json("Instrução", "Dado", ESQUEMA)
            self.assertNotIn("credencial-ficticia", str(erro.exception))
            self.assertNotIn("credencial-ficticia", json.dumps(cliente.chamadas))
            self.assertEqual(post.call_count, 1)

    def test_esquema_restrito_e_tokens_medidos(self):
        cliente = ClienteOpenAI()
        sucesso = Mock(ok=True, status_code=200, json=lambda: {
            "choices": [{"message": {"content": '{"ok":true}'}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 8, "completion_tokens": 3, "total_tokens": 11},
        })
        with patch("src.desafio6.servicos.chave", return_value="credencial-ficticia"), \
             patch("src.desafio6.servicos.requests.post", return_value=sucesso) as post:
            self.assertEqual(cliente.gerar_json("Sistema", "Dados", ESQUEMA), {"ok": True})
            payload = post.call_args.kwargs["json"]
            self.assertIs(payload["response_format"]["json_schema"]["strict"], True)
            self.assertIs(payload["store"], False)
            self.assertEqual(cliente.orcamento.tokens_medidos, 11)
            self.assertIsNone(cliente.chamadas[-1]["custo_usd"])

    def test_resposta_invalida_ou_truncada_bloqueia(self):
        for escolha in ({"message": {"content": '{"ok":"sim"}'}},
                        {"message": {"content": '{"ok":true}'}, "finish_reason": "length"}):
            cliente = ClienteOpenAI()
            sucesso = Mock(ok=True, status_code=200, json=lambda: {"choices": [escolha]})
            with patch("src.desafio6.servicos.chave", return_value="credencial-ficticia"), \
                 patch("src.desafio6.servicos.requests.post", return_value=sucesso):
                with self.assertRaises(ErroServico):
                    cliente.gerar_json("Sistema", "Dados", ESQUEMA)

    def test_embeddings_dimensao_e_ordenacao(self):
        cliente = ClienteOpenAI()
        vetor = [1.0] + [0.0] * (cliente.dimensao - 1)
        sucesso = Mock(ok=True, status_code=200, json=lambda: {"data": [
            {"index": 1, "embedding": vetor}, {"index": 0, "embedding": vetor}],
            "usage": {"prompt_tokens": 8, "total_tokens": 8}})
        with patch("src.desafio6.servicos.chave", return_value="credencial-ficticia"), \
             patch("src.desafio6.servicos.requests.post", return_value=sucesso):
            self.assertEqual(len(cliente.embeddings(["doc um", "doc dois"])), 2)

    def test_embeddings_falsos_ou_nan_rejeitados(self):
        for vetor in ([0.0] * 256, [float("nan")] * 256, [1.0]):
            cliente = ClienteOpenAI()
            sucesso = Mock(ok=True, status_code=200, json=lambda: {"data": [{"index": 0, "embedding": vetor}]})
            with patch("src.desafio6.servicos.chave", return_value="credencial-ficticia"), \
                 patch("src.desafio6.servicos.requests.post", return_value=sucesso):
                with self.assertRaises(ErroServico):
                    cliente.embeddings(["texto fictício"])

    def test_stt_multipart_repete_rebobinando_arquivo(self):
        cliente = ClienteOpenAI()
        lidos = []
        def responder(url, **kwargs):
            lidos.append(kwargs["files"]["file"][-1].read())
            if len(lidos) == 1:
                return Mock(ok=False, status_code=503)
            return Mock(ok=True, status_code=200, json=lambda: {"text": "Solicitação fictícia de atendimento"})
        with tempfile.TemporaryDirectory() as d:
            arq = Path(d) / "entrada.mp3"
            arq.write_bytes(b"ID3ficticio")
            with patch("src.desafio6.servicos.chave", return_value="credencial-ficticia"), \
                 patch("src.desafio6.servicos.requests.post", side_effect=responder), \
                 patch("src.desafio6.servicos.time.sleep"):
                self.assertIn("fictícia", cliente.transcrever(arq))
            self.assertEqual(lidos, [b"ID3ficticio", b"ID3ficticio"])
            self.assertEqual(cliente.orcamento.chamadas, 2)

    def test_saida_bruta_com_credencial_nao_e_persistida(self):
        cliente = ClienteOpenAI()
        esquema = {"type": "object", "properties": {"texto": {"type": "string"}}, "required": ["texto"], "additionalProperties": False}
        sucesso = Mock(ok=True, status_code=200, json=lambda: {
            "choices": [{"message": {"content": '{"texto":"credencial-ficticia"}'}}]})
        with patch("src.desafio6.servicos.chave", return_value="credencial-ficticia"), \
             patch("src.desafio6.servicos.requests.post", return_value=sucesso):
            with self.assertRaisesRegex(ErroServico, "dado indevido"):
                cliente.gerar_json("Sistema", "Dados", esquema)
        self.assertNotIn("credencial-ficticia", json.dumps(cliente.saidas_estruturadas))


class TestGuardrailsDesafio6(unittest.TestCase):
    def test_ataques_nao_recebem_permissao(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = preparar_dados(Path(d) / "fixtures")
            ataques = carregar_conjunto("ataques", raiz)["ataques"]
            for ataque in ataques:
                self.assertNotEqual(avaliar_entrada(ataque["texto"], contexto=True)["decisao"], "permitir")

    def test_fora_de_escopo_tipo_e_excesso(self):
        for entrada in (None, "", "a" * 12001, "Como está o tempo amanhã?"):
            self.assertNotEqual(avaliar_entrada(entrada)["decisao"], "permitir")
        self.assertEqual(avaliar_entrada("Que identificação é necessária para consultar o andamento?")["decisao"], "permitir")

    def test_arquivo_excessivo_e_segredo_bloqueados(self):
        with tempfile.TemporaryDirectory() as d:
            arquivo = Path(d) / "excesso.txt"
            arquivo.write_bytes(b"x" * (2 * 1024 * 1024 + 1))
            with self.assertRaises(ValueError):
                validar_documento(arquivo)
        self.assertEqual(avaliar_entrada("OPENAI_API_KEY=credencial-ficticia")["decisao"], "bloquear")
        self.assertEqual(validar_saida("CPF: 000.111.222-33")["decisao"], "bloquear")

    def test_log_mascara_identificadores(self):
        texto = sanitizar("Nome: Pessoa Fictícia\nProtocolo: 2026-000123\nOPENAI_API_KEY=credencial-ficticia")
        self.assertNotIn("Pessoa Fictícia", texto)
        self.assertNotIn("2026-000123", texto)
        self.assertNotIn("credencial-ficticia", texto)


if __name__ == "__main__":
    unittest.main()
