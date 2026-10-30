"""Integração OpenAI por transporte simulado; nenhuma chamada real ou chave real."""

import copy
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from src import contrato, guardrails
from src.cliente import _payload, conversar
from src.config import carregar, chave
from src.llm_json import formato_resposta


class TestOpenAI(unittest.TestCase):
    def test_endpoint_parametros_e_tokens_da_openai(self):
        cfg = carregar()
        resposta = Mock(status_code=200, json=lambda: {
            "model": cfg["llm"]["modelo"],
            "choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 21, "completion_tokens": 8},
        })
        with patch("src.cliente.carregar", return_value=cfg), \
                patch("src.cliente.chave", return_value="credencial-ficticia"), \
                patch("src.cliente.requests.post", return_value=resposta) as post:
            r = conversar([{"role": "user", "content": "JSON fictício"}])
        self.assertEqual(post.call_args.args[0], "https://api.openai.com/v1/chat/completions")
        payload = post.call_args.kwargs["json"]
        self.assertIn("max_completion_tokens", payload)
        self.assertNotIn("max_tokens", payload)
        self.assertNotIn("temperature", payload)
        self.assertEqual(payload["reasoning_effort"], "none")
        self.assertEqual(r["provider"], "openai")
        self.assertEqual((r["tokens_entrada"], r["tokens_saida"]), (21, 8))
        self.assertEqual(r["parametros"]["max_completion_tokens"], cfg["llm"]["max_tokens"])

    def test_schema_de_transporte_nao_altera_contrato_local(self):
        schema = copy.deepcopy(contrato.carregar_schema())
        original = copy.deepcopy(schema)
        formato = formato_resposta("solicitacao_v2", schema)
        cfg = carregar()
        payload = _payload([], cfg["llm"]["modelo"], cfg["llm"], formato, provider="openai")
        enviado = payload["response_format"]["json_schema"]["schema"]
        self.assertEqual(enviado["properties"]["versao_schema"], {"enum": ["2.0.0"], "type": "string"})
        self.assertNotIn("uniqueItems", enviado["properties"]["campos_ausentes"])
        self.assertEqual(enviado["properties"]["categoria"]["type"], "string")
        self.assertEqual(schema, original)
        self.assertTrue(contrato.carregar_schema()["properties"]["campos_ausentes"]["uniqueItems"])

    def test_outros_provedores_mantem_formato_anterior(self):
        formato = formato_resposta("solicitacao_v2", contrato.carregar_schema())
        p = _payload([], "modelo-ficticio", {"temperatura": 0.2, "max_tokens": 100},
                     formato, provider="gemini")
        self.assertEqual(p["temperature"], 0.2)
        self.assertEqual(p["max_tokens"], 100)
        self.assertNotIn("max_completion_tokens", p)
        self.assertEqual(p["response_format"], formato)

    def test_chave_openai_e_protegida_pelo_filtro_existente(self):
        cfg = carregar()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "segredo-ficticio-openai"}):
            self.assertEqual(chave(cfg, "openai"), "segredo-ficticio-openai")
            r = guardrails.filtrar_saida("valor: segredo-ficticio-openai", cfg)
        self.assertTrue(r["bloqueado"])
        self.assertNotIn("segredo-ficticio-openai", r["texto"])

    def test_evidencia_llm_registra_modelo_e_tokens_sem_rotular_como_extrativo(self):
        from src.avaliacao_integrada import Avaliacao

        # O transporte é simulado neste teste, identificado nos metadados da saída.
        resposta = {
            "fontes": [], "status": "sem_evidencia_suficiente", "resposta": "Sem evidência.",
            "afirmacoes": [], "afirmacoes_removidas": [], "encaminhar_revisao": True,
            "motivos_revisao": [], "trechos_recuperados": [], "latencia_ms": 1,
            "gerador": {"perfil": "principal", "e_llm": True, "provider": "simulado_teste",
                        "modelo": "modelo-ficticio", "tokens_entrada": 10, "tokens_saida": 5},
        }
        with tempfile.TemporaryDirectory() as tmp, patch("src.avaliacao_integrada.RepositorioRevisao"):
            a = Avaliacao("principal", pasta=Path(tmp))
            a.ix = object()
            with patch("src.avaliacao_integrada.responder", return_value=resposta), \
                    patch("src.avaliacao_integrada.salvar_derivado_rag"), \
                    patch("src.avaliacao_integrada._gravar") as gravar:
                a.avaliar_rag()
            evidencia = gravar.call_args.args[2]
        self.assertNotIn("gerador extrativo", evidencia["metricas"]["observacao"])
        self.assertEqual(evidencia["perguntas"][0]["provider"], "simulado_teste")
        self.assertEqual(evidencia["perguntas"][0]["modelo"], "modelo-ficticio")
        self.assertEqual(evidencia["perguntas"][0]["tokens_entrada"], 10)
        self.assertEqual(evidencia["perguntas"][0]["tokens_saida"], 5)


if __name__ == "__main__":
    unittest.main()
