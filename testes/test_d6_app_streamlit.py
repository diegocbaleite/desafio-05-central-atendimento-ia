"""RF20: a interface Streamlit carrega, indexa e registra decisão humana (teste headless)."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from streamlit.testing.v1 import AppTest
except ImportError:  # streamlit é dependência do Desafio 6
    AppTest = None

from src.config import ROOT


@unittest.skipIf(AppTest is None, "streamlit não instalado")
class TestApp(unittest.TestCase):
    def setUp(self):
        from streamlit import cache_resource

        cache_resource.clear()
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        base = Path(self.tmp.name)
        self.env = patch.dict(os.environ, {
            "D6_EMBEDDING_PROVIDER": "hash_teste",
            "D6_DIR_INDICE": str(base / "indice"),
            "D6_BANCO_REVISAO": str(base / "rev.sqlite3"),
            "D6_ARQUIVO_AUDITORIA": str(base / "aud.jsonl"),
        })
        self.env.start()

    def tearDown(self):
        from streamlit import cache_resource

        cache_resource.clear()
        self.env.stop()
        self.tmp.cleanup()

    def test_sentimentos_preserva_resultados_ao_filtrar_e_orienta_sessao_vazia(self):
        from src.sentimento import classificar_local

        with patch("src.sentimento.classificar_local", wraps=classificar_local) as classificar:
            at = AppTest.from_file(str(ROOT / "src" / "app.py"), default_timeout=120).run()
            self.assertFalse(at.exception, at.exception)
            self.assertTrue(any("Nenhuma avaliação classificada nesta sessão" in i.value for i in at.info))
            # O filtro pode ser escolhido antes de carregar os resultados da sessão.
            next(s for s in at.selectbox if s.label == "Requer revisão").select("sim").run()
            self.assertFalse(at.exception, at.exception)
            self.assertTrue(any("Classificar as 12 avaliações" in i.value for i in at.info))
            next(b for b in at.button if b.label == "Classificar as 12 avaliações").click().run()
            self.assertFalse(at.exception, at.exception)
            self.assertEqual(next(m.value for m in at.metric if m.label == "Total (IDs únicos)"), "3")
            tabela = next(d.value for d in at.dataframe if "metodo" in d.value.columns)
            self.assertEqual(tabela["id"].tolist(), ["AV10", "AV11", "AV12"])
            self.assertTrue(tabela["requer_revisao"].all())
            self.assertEqual(set(tabela["polaridade"]), {"indeterminada"})
            for filtro, total in (("todas", "12"), ("sim", "3"), ("não", "9")):
                with self.subTest(filtro=filtro):
                    next(s for s in at.selectbox if s.label == "Requer revisão").select(filtro).run()
                    self.assertFalse(at.exception, at.exception)
                    self.assertEqual(len(at.session_state["sentimentos"]), 12)
                    self.assertEqual(next(m.value for m in at.metric if m.label == "Total (IDs únicos)"), total)
            # Há dados na sessão, mas esta combinação realmente não tem correspondências.
            next(s for s in at.selectbox if s.label == "Requer revisão").select("sim").run()
            next(s for s in at.multiselect if s.label == "Polaridade").set_value(["positiva"]).run()
            self.assertFalse(at.exception, at.exception)
            self.assertTrue(any("Conjunto vazio para os filtros atuais (0/0)" in i.value for i in at.info))
            self.assertFalse(any("Nenhuma avaliação classificada nesta sessão" in i.value for i in at.info))
            self.assertEqual(len(at.session_state["sentimentos"]), 12)
            self.assertEqual(classificar.call_count, 12)  # Alterar filtros não classifica novamente.

    def test_consulta_independente_respeita_limite_zero(self):
        from testes.d6_apoio import cfg_teste

        cfg = cfg_teste()
        cfg["guardrails"]["max_chamadas_execucao"] = 0
        with patch("src.config.carregar", return_value=cfg):
            at = AppTest.from_file(str(ROOT / "src" / "app.py"), default_timeout=120).run()
            next(b for b in at.button if b.label == "Indexar acervo (sem duplicar)").click().run()
            at.sidebar.selectbox[0].select("principal").run()
            next(t for t in at.text_input if t.label == "Pergunta").set_value(
                "Qual é o prazo da segunda via da declaração?"
            ).run()
            with patch("src.cliente.chave", return_value="token-ficticio"), \
                    patch("src.cliente.requests.post") as post:
                next(b for b in at.button if b.label == "Consultar").click().run()
        self.assertFalse(at.exception, at.exception)
        post.assert_not_called()
        self.assertEqual(at.session_state["ultima_consulta"]["status"], "falha")
        self.assertTrue(any("Orçamento" in e for e in at.session_state["ultima_consulta"]["erros"]))

    def test_fluxo_minimo_na_interface(self):
        at = AppTest.from_file(str(ROOT / "src" / "app.py"), default_timeout=120)
        at.run()
        self.assertFalse(at.exception, at.exception)
        self.assertIn("Índice vazio", " ".join(w.value for w in at.warning))
        at.button[0].click().run()  # Indexar acervo
        self.assertFalse(at.exception, at.exception)
        # Processa uma solicitação digitada e verifica a minuta pendente.
        at.text_area[0].set_value(
            "Nome: Maria Fictícia Albuquerque\nProtocolo: 2026.000123\nData: 02/10/2026\n"
            "Assunto: segunda via de certidão\nPedido: Solicito segunda via da certidão."
        ).run()
        processar = next(b for b in at.button if b.label == "Processar solicitação")
        processar.click().run()
        self.assertFalse(at.exception, at.exception)
        self.assertTrue(any("PENDENTE" in m.value for m in at.markdown))
        # Decisão humana pela aba Revisão (operador + justificativa obrigatórios).
        at.text_input(key="operador_revisao").set_value("Operadora de Teste")
        justificativa = next(t for t in at.text_area if t.label.startswith("Justificativa"))
        justificativa.set_value("Conferido com o original no teste da interface")
        next(b for b in at.button if b.label == "Registrar decisão humana").click().run()
        self.assertFalse(at.exception, at.exception)
        self.assertTrue(any("Nada foi enviado" in s.value for s in at.success))
        from src.revisao import RepositorioRevisao

        repo = RepositorioRevisao(os.environ["D6_BANCO_REVISAO"])
        decisoes = repo.contagem()["decisoes_por_origem"]
        self.assertEqual(decisoes, {"humana_interface": 1})

    def test_revisao_orienta_campos_invalidos_e_envia_formulario_completo(self):
        from src.revisao import RepositorioRevisao

        repo = RepositorioRevisao(os.environ["D6_BANCO_REVISAO"])
        mid = repo.criar_minuta("TESTE-REV", "# MINUTA FICTÍCIA — NÃO ENVIADA", gerador="extrativo_local")
        at = AppTest.from_file(str(ROOT / "src" / "app.py"), default_timeout=120).run()
        self.assertFalse(at.exception, at.exception)
        self.assertFalse(at.sidebar.text_input)
        self.assertIn("3 caracteres", at.text_input(key="operador_revisao").help)
        self.assertIn("5 caracteres", next(t for t in at.text_area if t.label.startswith("Justificativa")).help)

        for operador, justificativa, campo in (
            ("   ", "Conferido com a fonte fictícia", "operador (mínimo de 3 caracteres)"),
            ("Operadora de Teste", " ok ", "justificativa (mínimo de 5 caracteres)"),
        ):
            with self.subTest(campo=campo):
                at.text_input(key="operador_revisao").set_value(operador)
                next(t for t in at.text_area if t.label.startswith("Justificativa")).set_value(justificativa)
                next(b for b in at.button if b.label == "Registrar decisão humana").click().run()
                self.assertFalse(at.exception, at.exception)
                self.assertTrue(any(campo in e.value for e in at.error))
                self.assertEqual(repo.obter(mid)["status"], "pendente")
                self.assertEqual(repo.historico(mid), [])
                self.assertFalse(Path(os.environ["D6_ARQUIVO_AUDITORIA"]).exists())

        at.text_input(key="operador_revisao").set_value("Operadora de Teste")
        next(t for t in at.text_area if t.label.startswith("Justificativa")).set_value("Conferido com a fonte fictícia")
        next(r for r in at.radio if r.label == "Decisão").set_value("revisar")
        next(b for b in at.button if b.label == "Registrar decisão humana").click().run()
        self.assertFalse(at.exception, at.exception)
        self.assertTrue(any("Nada foi enviado" in s.value for s in at.success))
        historico = repo.historico(mid)
        self.assertEqual(len(historico), 1)
        self.assertEqual(historico[0]["operador"], "Operadora de Teste")
        self.assertEqual(historico[0]["justificativa"], "Conferido com a fonte fictícia")
        self.assertEqual(repo.obter(mid)["status"], "revisar")
        auditoria = Path(os.environ["D6_ARQUIVO_AUDITORIA"]).read_text(encoding="utf-8")
        self.assertIn("decisao_humana", auditoria)
        self.assertNotIn("Operadora de Teste", auditoria)
        self.assertNotIn("Conferido com a fonte fictícia", auditoria)


if __name__ == "__main__":
    unittest.main()
