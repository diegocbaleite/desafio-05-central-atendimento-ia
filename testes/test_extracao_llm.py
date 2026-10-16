"""Testes locais da extração por LLM; nenhuma chamada externa é realizada."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from src.cliente import ErroAPI
from src.extracao_llm import (
    _campo_verificavel,
    _gemini_ler,
    _json_da_resposta,
    _validar_entrada,
    extrair_arquivo,
)


class TestValidacaoEntrada(unittest.TestCase):
    def test_rejeita_arquivo_fora_da_pasta_permitida(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp) / "entrada"
            fora = Path(temp) / "fora.txt"
            base.mkdir()
            fora.write_text("conteúdo fictício", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "dentro da pasta"):
                _validar_entrada(fora, base)

    def test_rejeita_arquivo_maior_que_limite(self):
        with tempfile.TemporaryDirectory() as temp:
            arquivo = Path(temp) / "entrada.txt"
            arquivo.write_text("12345", encoding="utf-8")
            with patch("src.extracao_llm.MAX_ARQUIVO_BYTES", 4):
                with self.assertRaisesRegex(ValueError, "14 MiB"):
                    _validar_entrada(arquivo, temp)


class TestValidacaoEvidencias(unittest.TestCase):
    def test_valor_precisa_constar_na_evidencia(self):
        texto = "FICHA DE MATRÍCULA"
        self.assertFalse(
            _campo_verificavel(
                "Solicitação de matrícula", "FICHA DE MATRÍCULA", texto
            )
        )

    def test_json_invalido_e_rejeitado_sem_tentativa_duplicada(self):
        with self.assertRaises(ErroAPI):
            _json_da_resposta('{"campos": }')


class TestGeminiAPI(unittest.TestCase):
    @patch("src.extracao_llm.time.sleep")
    @patch("src.extracao_llm.requests.post")
    @patch("src.extracao_llm.chave", return_value="token-falso")
    @patch("src.extracao_llm.carregar", return_value={})
    def test_retentativa_429_e_metadados(self, carregar, chave, post, sleep):
        ok = Mock(
            status_code=200,
            ok=True,
            json=lambda: {
                "candidates": [{"content": {"parts": [{"text": "texto transcrito"}]}}],
                "usageMetadata": {"promptTokenCount": 12, "candidatesTokenCount": 8},
            },
        )
        limite = Mock(status_code=429, ok=False, headers={"Retry-After": "0"})
        post.side_effect = [limite, ok]

        with tempfile.TemporaryDirectory() as temp:
            arquivo = Path(temp) / "entrada.mp3"
            arquivo.write_bytes(b"audio ficticio")
            texto, meta = _gemini_ler(arquivo, "gemini-teste", 1)

        self.assertEqual(texto, "texto transcrito")
        self.assertEqual(meta["tentativas"], 2)
        self.assertEqual(meta["tokens_entrada"], 12)
        self.assertEqual(meta["tokens_saida"], 8)
        self.assertEqual(post.call_args.kwargs["headers"]["x-goog-api-key"], "token-falso")
        self.assertEqual(post.call_count, 2)
        sleep.assert_called_once_with(0)


class TestExtracaoAuditada(unittest.TestCase):
    def test_registra_falha_sem_registrar_conteudo_da_entrada(self):
        with tempfile.TemporaryDirectory() as temp:
            raiz = Path(temp) / "entrada"
            raiz.mkdir()
            arquivo = raiz / "falha.txt"
            arquivo.write_text("conteúdo fictício privado", encoding="utf-8")
            with (
                patch(
                    "src.extracao_llm._estruturar",
                    side_effect=ErroAPI("OpenRouter indisponível"),
                ),
                patch("src.extracao_llm.registrar") as audit,
            ):
                with self.assertRaises(ErroAPI):
                    extrair_arquivo(
                        arquivo,
                        saida=Path(temp) / "saida",
                        pasta_entrada=raiz,
                        execucao="execucao-falha",
                    )

        falhas = [
            chamada.kwargs
            for chamada in audit.call_args_list
            if chamada.args[2] == "erro"
        ]
        self.assertEqual(len(falhas), 1)
        self.assertEqual(falhas[0]["fase"], "estruturacao")
        self.assertEqual(falhas[0]["provider"], "openrouter")
        self.assertNotIn("conteúdo fictício privado", str(falhas[0]))

    def test_minimiza_antes_do_openrouter_e_registra_metadados(self):
        texto = (
            "Protocolo: 2026-000142\n"
            "Data: 14/10/2026\n"
            "Meu nome é Ana Silva\n"
            "Assunto: Consulta de atendimento\n"
            "Pedido: Solicito andamento do processo\n"
            "CPF: 123.456.789-00\n"
            "E-mail: ana.teste@example.com"
        )
        campos = {
            "protocolo": {
                "valor": "2026-000142",
                "evidencia": "Protocolo: 2026-000142",
                "confianca": "alta",
            },
            "data_solicitacao": {
                "valor": "14/10/2026",
                "evidencia": "Data: 14/10/2026",
                "confianca": "alta",
            },
            "solicitante": {
                "valor": "Ana Silva",
                "evidencia": "Meu nome é Ana Silva",
                "confianca": "alta",
            },
            "assunto": {
                "valor": "Consulta de atendimento",
                "evidencia": "Assunto: Consulta de atendimento",
                "confianca": "alta",
            },
            "pedido": {
                "valor": "Solicito andamento do processo",
                "evidencia": "Pedido: Solicito andamento do processo",
                "confianca": "alta",
            },
        }
        modelo_resposta = {
            "texto": json.dumps(
                {
                    "campos": campos,
                    "categoria": {
                        "codigo": "andamento_processo",
                        "justificativa": "pedido do usuário",
                    },
                }
            ),
            "provider": "openrouter",
            "modelo": "modelo-teste",
            "duracao_s": 1.25,
            "tokens_entrada": 100,
            "tokens_saida": 50,
            "custo_usd": None,
        }

        with tempfile.TemporaryDirectory() as temp:
            raiz = Path(temp) / "entrada"
            saida = Path(temp) / "saida"
            raiz.mkdir()
            arquivo = raiz / "pedido.txt"
            arquivo.write_text(texto, encoding="utf-8")
            with (
                patch("src.extracao_llm.conversar", return_value=modelo_resposta) as call,
                patch("src.extracao_llm.registrar") as audit,
            ):
                resultado = extrair_arquivo(
                    arquivo,
                    saida=saida,
                    pasta_entrada=raiz,
                    execucao="execucao-teste",
                )
                self.assertTrue((saida / "pedido.txt.texto_fonte.txt").exists())
                json_saida = json.loads(
                    (saida / "pedido.txt.extracao_llm.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(
                    json_saida["execucao"]["id_execucao"], "execucao-teste"
                )
                self.assertEqual(
                    json_saida["execucao"]["chamadas"][1]["tokens_entrada"], 100
                )
                self.assertTrue(
                    any(
                        c.args[2] == "api_estruturacao"
                        for c in audit.call_args_list
                    )
                )

        mensagens = call.call_args.args[0]
        conteudo_enviado = mensagens[1]["content"]
        self.assertNotIn("123.456.789-00", conteudo_enviado)
        self.assertNotIn("ana.teste@example.com", conteudo_enviado)
        self.assertEqual(resultado["campos"]["pedido"]["valor"], campos["pedido"]["valor"])
        self.assertEqual(resultado["campos"]["solicitante"]["valor"], "Ana Silva")


if __name__ == "__main__":
    unittest.main()
