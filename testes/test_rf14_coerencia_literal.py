"""RF14: mudanças de sentido não podem passar do contrato para uma minuta.

Transportes simulados, sem chaves ou chamadas reais. Originais/gabaritos intactos.
"""
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

from src import contrato
from src.config import carregar
from src.estruturacao import ficha_por_regras
from src.geracao import criar_gerador
from src.orcamento import Orcamento
from src.pipeline import processar_solicitacao
from src.revisao import RepositorioRevisao

HOJE = date(2026, 10, 30)
CABECALHO = (
    "Nome: Maria Fictícia Albuquerque\nProtocolo: 2026.000123\n"
    "Data: 02/10/2026\nAssunto: matrícula\n"
)


class TestCoerenciaLiteral(unittest.TestCase):
    def test_rejeita_inversao_negacao_restricao_condicao_e_subpedido(self):
        casos = [
            ("Não solicito cancelamento da matrícula.", "Solicito cancelamento da matrícula."),
            ("Solicito cancelamento da matrícula.", "Não solicito cancelamento da matrícula."),
            ("Nunca solicito cancelamento da matrícula.", "Solicito cancelamento da matrícula."),
            ("Solicito apenas segunda via da certidão.", "Solicito segunda via da certidão."),
            ("Solicito cancelamento somente se houver autorização.", "Solicito cancelamento."),
            ("Solicito segunda via da certidão; peço informações sobre matrícula.",
             "Solicito segunda via da certidão."),
            ("Solicito segunda via da certidão.", "Solicito segunda via da certidão em 999 dias."),
        ]
        for pedido, alterado in casos:
            with self.subTest(pedido=pedido, alterado=alterado):
                original = CABECALHO + "Pedido: " + pedido
                ficha = ficha_por_regras(original)
                self.assertTrue(contrato.validar(ficha, original, HOJE)["valido"])
                ficha["pedido"] = alterado
                r = contrato.validar(ficha, original, HOJE)
                self.assertTrue(r["esquema_ok"])
                self.assertFalse(r["valido"])
                self.assertIn(("dado_sem_suporte", "pedido"),
                              {(e["tipo"], e["campo"]) for e in r["erros_regras"]})

    def test_pedido_livre_preserva_negacao_e_restricao(self):
        for pedido in ("Não solicito cancelamento da matrícula.",
                       "Nunca solicito cancelamento da matrícula.",
                       "Apenas solicito segunda via da certidão."):
            with self.subTest(pedido=pedido):
                original = CABECALHO + pedido
                ficha = ficha_por_regras(original)
                self.assertEqual(ficha["pedido"], pedido.rstrip("."))
                self.assertTrue(contrato.validar(ficha, original, HOJE)["valido"])
                ficha["pedido"] = pedido.split(" ", 1)[1]
                self.assertFalse(contrato.validar(ficha, original, HOJE)["valido"])

    def test_nao_aceita_frase_positiva_em_outro_campo(self):
        original = (CABECALHO + "Pedido: Não solicito cancelamento da matrícula.\n"
                    "Observação: Solicito cancelamento da matrícula.")
        ficha = ficha_por_regras(original)
        ficha["pedido"] = "Solicito cancelamento da matrícula."
        self.assertFalse(contrato.validar(ficha, original, HOJE)["valido"])

    def test_assunto_tambem_deve_preservar_restricao(self):
        original = CABECALHO.replace("Assunto: matrícula", "Assunto: matrícula sem cancelamento")
        original += "Pedido: Solicito segunda via da certidão."
        ficha = ficha_por_regras(original)
        ficha["assunto"] = "matrícula"
        self.assertFalse(contrato.validar(ficha, original, HOJE)["valido"])

    def test_nao_converte_pergunta_em_afirmacao(self):
        original = CABECALHO + "Pedido: Solicito cancelamento da matrícula?"
        ficha = ficha_por_regras(original)
        ficha["pedido"] = "Solicito cancelamento da matrícula."
        self.assertFalse(contrato.validar(ficha, original, HOJE)["valido"])

    def test_normalizacao_visual_nao_altera_palavras(self):
        original = CABECALHO + "Pedido: Não solicito cancelamento da matrícula."
        ficha = ficha_por_regras(original)
        ficha["pedido"] = "NÃO  SOLICITO cancelamento da matrícula"
        self.assertTrue(contrato.validar(ficha, original, HOJE)["valido"])

    def _executar_pipeline(self, corrigir):
        original = CABECALHO + "Pedido: Não solicito cancelamento da matrícula."
        correta = ficha_por_regras(original)
        incorreta = {**correta, "pedido": "Solicito cancelamento da matrícula."}
        cfg = carregar()
        ix = Mock()
        ix.buscar.return_value = [{"similaridade": 0.8}]
        orcamento = Orcamento(5)
        respostas = iter([incorreta, correta if corrigir else incorreta])

        def simular(*args, orcamento, **kwargs):
            orcamento.reservar("transporte simulado RF14")
            return {"texto": json.dumps(next(respostas)), "provider": "simulado_teste",
                    "modelo": "teste-rf14", "tokens_entrada": 1, "tokens_saida": 1}

        rag = {"status": "sem_evidencia_suficiente", "afirmacoes": [], "fontes": [],
               "conflito": None, "motivos_revisao": ["sem evidência"],
               "trechos_recuperados": [], "quarentena": [], "erros": []}
        with tempfile.TemporaryDirectory() as d, patch("src.pipeline.rag.responder", return_value=rag) as consultar:
            repo = RepositorioRevisao(Path(d) / "revisao.sqlite3")
            resultado = processar_solicitacao(
                original, caso_id="TESTE_NEGACAO", modalidade="texto", cfg=cfg,
                indice=ix, gerador=criar_gerador(cfg, "extrativo_local"), repositorio=repo,
                orcamento=orcamento, modo_estruturacao="llm", conversar_fn=simular,
                hoje=HOJE, arquivo_auditoria=Path(d) / "auditoria.jsonl")
            if corrigir:
                self.assertEqual(resultado["status_minuta"], "pendente")
                self.assertIn("Pedido: Não solicito cancelamento", resultado["minuta"])
                self.assertEqual(len(repo.listar()), 1)
                consultar.assert_called_once()
            else:
                self.assertEqual(resultado["decisao"], "bloquear")
                self.assertIsNone(resultado["minuta"])
                self.assertIsNone(resultado["minuta_id"])
                self.assertEqual(repo.listar(), [])
                consultar.assert_not_called()
            self.assertEqual(resultado["estruturacao"]["tentativas"], 2)
            self.assertEqual(orcamento.chamadas, 2)

    def test_duas_saidas_incoerentes_bloqueiam_antes_do_rag_e_da_minuta(self):
        self._executar_pipeline(corrigir=False)

    def test_uma_correcao_fiel_permite_minuta_pendente(self):
        self._executar_pipeline(corrigir=True)
