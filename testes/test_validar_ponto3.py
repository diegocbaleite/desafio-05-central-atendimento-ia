"""Cobertura complementar ATQ02/T11: índices e decisões fictícias em pasta temporária."""

import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.validar_ponto3 import avaliar_atq02, coletar_t11
from src.revisao import RepositorioRevisao
from testes.d6_apoio import IndiceTemporario, cfg_teste
from src.ingestao import carregar_catalogo


class TestATQ02Complementar(unittest.TestCase):
    def setUp(self):
        self.cfg = cfg_teste()
        docs = [d for d in carregar_catalogo(self.cfg, incluir_enviados=False) if d["id"] == "DOC-07"]
        self.t = IndiceTemporario(catalogo=docs)
        self.addCleanup(self.t.fechar)
        self.t.indice.indexar(docs)

    def test_instrucao_no_top_k_e_excluida_do_contexto_real_do_gerador(self):
        resultado = avaliar_atq02(self.cfg, self.t.indice, cenario="isolado_teste",
                                 auditoria=self.t.pasta / "auditoria.jsonl")
        self.assertEqual(resultado["situacao"], "aprovado")
        self.assertTrue(resultado["quarentena"])
        self.assertTrue(set(resultado["quarentena"]) <= set(resultado["top_k_obtido"]))
        self.assertTrue(set(resultado["quarentena"]).isdisjoint(resultado["contexto_entregue_ao_gerador"]))
        self.assertEqual(resultado["top_k"], self.cfg["recuperacao"]["top_k"])
        self.assertEqual(resultado["chamadas_llm"], 0)
        self.assertIn("hash_teste", resultado["natureza"])

    def test_sem_instrucao_no_top_k_nao_declara_cobertura_integral(self):
        hits = self.t.indice.buscar("atendimento ponto facultativo", 4)
        limpos = [h for h in hits if not h["metadados"]["suspeito_injecao"]]
        with patch.object(self.t.indice, "buscar", return_value=limpos):
            resultado = avaliar_atq02(self.cfg, self.t.indice, cenario="recuperacao_controlada_teste",
                                     auditoria=self.t.pasta / "auditoria.jsonl")
        self.assertEqual(resultado["situacao"], "parcial")
        self.assertFalse(resultado["criterios"]["instrucao_no_top_k_e_em_quarentena"])


class TestColetaT11(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.banco = Path(self.tmp.name) / "revisoes.sqlite3"
        self.cfg = cfg_teste()
        self.repo = RepositorioRevisao(self.banco)

    def nova(self, caso):
        return self.repo.criar_minuta(caso, "MINUTA FICTÍCIA — não enviada", gerador="extrativo_local")

    def decidir(self, mid, decisao, origem="humana_interface"):
        self.repo.registrar_decisao(mid, decisao, "Operador fictício de teste",
                                   "Justificativa fictícia do teste", origem)

    def test_simulacao_e_pedido_de_revisao_nao_substituem_rejeicao_interface(self):
        aprovada, rejeitada, revisar = self.nova("APROVADA"), self.nova("SIMULADA"), self.nova("REVISAR")
        self.decidir(aprovada, "aprovar")
        self.decidir(rejeitada, "rejeitar", "simulada_teste")
        self.decidir(revisar, "revisar")
        antes = self.banco.read_bytes()
        resultado = coletar_t11(self.banco, self.cfg)
        self.assertEqual(resultado["situacao"], "pendente")
        self.assertEqual(len(resultado["aprovacoes"]), 1)
        self.assertEqual(resultado["rejeicoes"], [])
        self.assertEqual(antes, self.banco.read_bytes())
        self.decidir(revisar, "rejeitar")
        resultado = coletar_t11(self.banco, self.cfg)
        self.assertEqual(resultado["situacao"], "demonstrado_por_registros_da_interface")
        self.assertEqual(resultado["rejeicoes"][0]["id"], revisar)
        self.assertEqual(resultado["decisoes_criadas_pelo_script"], 0)

    def test_hash_divergente_nao_e_aceito_como_evidencia(self):
        mid = self.nova("TESTE")
        self.decidir(mid, "rejeitar")
        with sqlite3.connect(self.banco) as c:
            c.execute("UPDATE minutas SET conteudo=? WHERE id=?", ("Conteúdo alterado", mid))
        c.close()
        self.assertEqual(coletar_t11(self.banco, self.cfg)["rejeicoes"], [])

    def test_banco_ausente_nao_e_criado_pela_coleta(self):
        ausente = self.banco.with_name("ausente.sqlite3")
        self.assertEqual(coletar_t11(ausente, self.cfg)["situacao"], "pendente")
        self.assertFalse(ausente.exists())

    def test_coleta_preserva_hash_tecnico_integral(self):
        mid = self.nova("HASH")
        self.decidir(mid, "rejeitar")
        esperado = hashlib.sha256("MINUTA FICTÍCIA — não enviada".encode()).hexdigest()
        resultado = coletar_t11(self.banco, self.cfg)
        self.assertEqual(resultado["rejeicoes"][0]["sha256"], esperado)
        self.assertEqual(resultado["rejeicoes"][0]["sha256_minuta"], esperado)


class TestAvaliadorAtaques(unittest.TestCase):
    def test_t04_nao_aprova_quando_a_quarentena_nao_foi_exercitada(self):
        from src.avaliacao_integrada import Avaliacao

        t = IndiceTemporario()
        self.addCleanup(t.fechar)
        t.indice.indexar(t.catalogo)
        with patch("src.avaliacao_integrada.carregar", return_value=t.cfg):
            avaliacao = Avaliacao(pasta=t.pasta / "avaliacao")
        avaliacao.ix = t.indice
        registrar = []
        avaliacao.registrar_teste = lambda *args: registrar.append(args)
        from src.rag import responder as responder_real

        def sem_quarentena(*args, **kwargs):
            r = responder_real(*args, **kwargs)
            r["quarentena"] = []
            return r

        # _gravar normalmente exige um caminho relativo ao repositório; esta
        # execução fica inteiramente no diretório temporário do teste.
        with patch("src.avaliacao_integrada.responder", side_effect=sem_quarentena), \
             patch("src.avaliacao_integrada._gravar", return_value="evidencia_ficticia.json"):
            avaliacao.avaliar_ataques()
        t04 = next(r for r in registrar if r[0] == "T04")
        self.assertEqual(t04[3], "parcial")


if __name__ == "__main__":
    unittest.main()
