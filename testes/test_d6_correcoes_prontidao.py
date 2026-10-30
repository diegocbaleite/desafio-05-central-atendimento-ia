"""Regressões dos contraexemplos da revisão de prontidão; somente dados fictícios."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from src import guardrails
from src.geracao import GeradorMock, criar_gerador
from src.rag import detectar_conflito, idf_do_indice, responder, verificar_afirmacoes
from testes.d6_apoio import IndiceTemporario


class TestSuporteLiteral(unittest.TestCase):
    def verificar(self, fonte, texto, citacao=None):
        return verificar_afirmacoes(
            [{"texto": texto, "citacao_literal": citacao or fonte, "chunk_ids": ["c1"]}],
            [{"chunk_id": "c1", "texto": fonte}],
        )[0]

    def test_rejeita_insercao_e_remocao_de_negacao(self):
        positiva = "A declaração é emitida em até 5 dias úteis."
        negativa = "A declaração não é emitida em até 5 dias úteis."
        for fonte, texto in ((positiva, negativa), (negativa, positiva)):
            with self.subTest(fonte=fonte):
                self.assertFalse(self.verificar(fonte, texto)["sustentada"])

    def test_rejeita_recorte_que_remove_condicao_ou_excecao(self):
        for fonte, texto in (
            ("Se houver agendamento, o atendimento ocorre às 8h.", "O atendimento ocorre às 8h."),
            ("O atendimento ocorre às 8h, exceto feriados.", "O atendimento ocorre às 8h."),
            ("Não é obrigatório apresentar documento.", "é obrigatório apresentar documento."),
        ):
            with self.subTest(fonte=fonte):
                self.assertFalse(self.verificar(fonte, texto)["sustentada"])

    def test_aceita_frase_completa_e_espacos_de_pdf(self):
        fonte = "O atendimento é gratuito. A declaração é emitida\nem até 5 dias úteis."
        frase = "A declaração é emitida em até 5 dias úteis."
        self.assertTrue(self.verificar(fonte, frase, frase)["sustentada"])

    def test_aceita_sequencia_contigua_de_frases_completas(self):
        passagem = "O atendimento é gratuito. A declaração fica disponível em 5 dias úteis."
        fonte = "Consulte o portal. " + passagem + " Guarde seu protocolo."
        self.assertTrue(self.verificar(fonte, passagem, passagem)["sustentada"])

    def test_rejeita_salto_de_frase_intermediaria(self):
        fonte = "O atendimento é gratuito. A gratuidade não abrange cópias. Consulte a secretaria."
        texto = "O atendimento é gratuito. Consulte a secretaria."
        self.assertFalse(self.verificar(fonte, texto)["sustentada"])

    def test_sequencia_nao_admite_negacao_invertida_ou_parafrase(self):
        fonte = "A taxa não é cobrada. Apresente os documentos: identidade; CPF; comprovante."
        for texto in (
            fonte.replace("não é", "é"),
            fonte.replace("identidade; CPF; comprovante", "identidade, CPF e comprovante"),
        ):
            with self.subTest(texto=texto):
                self.assertFalse(self.verificar(fonte, texto)["sustentada"])

    def test_nao_junta_frases_de_trechos_diferentes(self):
        r = verificar_afirmacoes([
            {"texto": "O atendimento é gratuito. A declaração fica pronta em 5 dias úteis.",
             "citacao_literal": "O atendimento é gratuito.", "chunk_ids": ["c1", "c2"]},
        ], [{"chunk_id": "c1", "texto": "O atendimento é gratuito."},
            {"chunk_id": "c2", "texto": "A declaração fica pronta em 5 dias úteis."}])[0]
        self.assertFalse(r["sustentada"])

    def test_cita_apenas_o_trecho_que_sustenta_a_passagem(self):
        frase = "A declaração fica pronta em 5 dias úteis."
        r = verificar_afirmacoes([
            {"texto": frase, "citacao_literal": frase, "chunk_ids": ["c1", "c2"]},
        ], [{"chunk_id": "c1", "texto": "O atendimento é gratuito."},
            {"chunk_id": "c2", "texto": frase}])[0]
        self.assertTrue(r["sustentada"])
        self.assertEqual(r["chunk_ids"], ["c2"])

    def test_citacao_nao_pode_vir_de_outro_trecho(self):
        r = verificar_afirmacoes([
            {"texto": "A declaração fica pronta em 5 dias úteis.",
             "citacao_literal": "O atendimento é gratuito.", "chunk_ids": ["c1", "c2"]},
        ], [{"chunk_id": "c1", "texto": "O atendimento é gratuito."},
            {"chunk_id": "c2", "texto": "A declaração fica pronta em 5 dias úteis."}])[0]
        self.assertFalse(r["sustentada"])
        self.assertIn("citacao_literal_fora_do_trecho_da_afirmacao", r["motivos"])


class TestCaminhosUpload(unittest.TestCase):
    def test_id_malicioso_nao_altera_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp)
            original = raiz / "dados/originais/entrada_texto.txt"
            original.parent.mkdir(parents=True)
            original.write_text("original fictício preservado", encoding="utf-8")
            pasta = raiz / "dados/acervo/enviados"
            pasta.mkdir(parents=True)
            for doc_id in ("../../originais/entrada_texto", "..\\..\\originais\\entrada_texto",
                           "C:\\originais\\entrada_texto", "/originais/entrada_texto", "DOC.08", "DOC:08"):
                with self.subTest(doc_id=doc_id), self.assertRaises(ValueError):
                    guardrails.destino_documento_enviado(pasta, doc_id, ".txt").write_bytes(b"alterado")
            self.assertEqual(original.read_text(encoding="utf-8"), "original fictício preservado")
            self.assertEqual(list(pasta.iterdir()), [])

    def test_documento_valido_fica_na_pasta_correta(self):
        with tempfile.TemporaryDirectory() as tmp:
            pasta = Path(tmp) / "enviados"
            self.assertEqual(guardrails.destino_documento_enviado(pasta, "DOC-08_v2", ".pdf"),
                             pasta.resolve() / "DOC-08_v2.pdf")

    def test_midias_rejeitam_caminhos_e_nomes_reservados(self):
        with tempfile.TemporaryDirectory() as tmp:
            for nome in ("../original.mp3", "..\\original.mp3", "/tmp/audio.wav", "C:\\audio.wav",
                         "audio.wav:segredo", "CON.mp3", "foto.png.", ""):
                with self.subTest(nome=nome), self.assertRaises(ValueError):
                    guardrails.caminho_upload_seguro(Path(tmp), nome)
            self.assertEqual(guardrails.caminho_upload_seguro(Path(tmp), "áudio fictício.mp3"),
                             Path(tmp).resolve() / "áudio fictício.mp3")


class TestRespostaRAG(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = IndiceTemporario()
        cls.t.indice.indexar(cls.t.catalogo)
        cls.gerador = criar_gerador(cls.t.cfg, "extrativo_local")

    @classmethod
    def tearDownClass(cls):
        cls.t.fechar()

    def consultar(self, pergunta, gerador=None, indice=None, **kwargs):
        return responder(pergunta, indice=indice or self.t.indice,
                         gerador=gerador or self.gerador, cfg=self.t.cfg, auditar=False, **kwargs)

    def test_negacao_invertida_nao_chega_a_resposta_exibida(self):
        pergunta = "Em quanto tempo é emitida a segunda via da declaração de matrícula?"
        base = self.consultar(pergunta)
        a = dict(base["afirmacoes"][0])
        a["texto"] = a["texto"].replace("é emitida", "não é emitida")
        gerador = GeradorMock("simulado", {"tipo": "mock"}, saida={
            "status": "fundamentada", "resposta": a["texto"], "afirmacoes": [a],
        })
        r = self.consultar(pergunta, gerador=gerador)
        self.assertEqual(r["status"], "sem_evidencia_suficiente")
        self.assertTrue(r["encaminhar_revisao"])
        self.assertEqual(r["afirmacoes"], [])
        self.assertNotIn("não é emitida", r["resposta"])
        self.assertEqual(len(r["afirmacoes_removidas"]), 1)

    def test_duas_frases_literais_geram_resposta_fundamentada(self):
        pergunta = "Como acompanho o andamento da minha solicitação?"
        hit = next(h for h in self.t.indice.buscar(pergunta, 4)
                   if "andamento da solicitação pode ser consultado" in h["texto"])
        gerador = GeradorMock("simulado", {"tipo": "mock"}, saida={
            "status": "fundamentada", "resposta": hit["texto"], "afirmacoes": [
                {"texto": hit["texto"], "citacao_literal": hit["texto"], "chunk_ids": [hit["chunk_id"]]},
            ],
        })
        r = self.consultar(pergunta, gerador=gerador)
        self.assertEqual(r["status"], "fundamentada")
        self.assertIn("portal", r["resposta"])
        self.assertIn("protocolo", r["resposta"])
        self.assertEqual(r["afirmacoes_removidas"], [])

    def test_resposta_respeita_prioridade_e_substituicao(self):
        pergunta = "Qual é o prazo de resposta para uma reclamação registrada na ouvidoria?"
        base = self.t.indice.buscar(pergunta, 4)
        for modo in ("prioridade", "substituicao"):
            with self.subTest(modo=modo):
                trechos = []
                for h in base:
                    meta = dict(h["metadados"])
                    if meta["doc_id"] == "DOC-03":
                        if modo == "prioridade":
                            meta["prioridade"] = 2
                        else:
                            meta["substitui"] = "DOC-05"
                    trechos.append({**h, "metadados": meta})
                with patch.object(self.t.indice, "buscar", return_value=trechos):
                    r = self.consultar(pergunta)
                self.assertEqual(r["status"], "fundamentada")
                self.assertTrue(r["conflito"]["resolvido"])
                self.assertIn("15 dias úteis", r["resposta"])
                self.assertNotIn("10 dias úteis", r["resposta"])
                self.assertNotIn("DOC-05", {f["doc_id"] for f in r["fontes"]})

    def test_empate_na_maior_prioridade_e_substituicao_parcial_mantem_conflito(self):
        pergunta = "Qual é o prazo de resposta para uma reclamação registrada na ouvidoria?"
        trechos = [h for h in self.t.indice.buscar(pergunta, 4)
                   if h["metadados"]["doc_id"] in ("DOC-03", "DOC-05")]
        idf = idf_do_indice(self.t.indice)
        # Uma terceira fonte ainda diverge após DOC-03 substituir DOC-05.
        terceiro = {**trechos[0], "chunk_id": "terceiro", "texto":
                    "Reclamações registradas na ouvidoria recebem resposta em até 20 dias úteis.",
                    "metadados": {**trechos[0]["metadados"], "doc_id": "DOC-08", "prioridade": 1, "substitui": ""}}
        parcial = [{**h, "metadados": {**h["metadados"], "substitui":
                    "DOC-05" if h["metadados"]["doc_id"] == "DOC-03" else ""}} for h in trechos]
        self.assertFalse(detectar_conflito(pergunta, parcial + [terceiro], idf, 0.5)["resolvido"])
        # Duas fontes empatadas acima da terceira continuam em conflito.
        empatados = [{**h, "metadados": {**h["metadados"], "prioridade": 2}} for h in trechos]
        self.assertFalse(detectar_conflito(pergunta, empatados + [terceiro], idf, 0.5)["resolvido"])

    def test_cli_consultar_com_orcamento_zero_nao_faz_requisicao(self):
        from copy import deepcopy
        from src.cli_d6 import executar

        cfg = deepcopy(self.t.cfg)
        cfg["guardrails"]["max_chamadas_execucao"] = 0
        cfg["auditoria"]["arquivo"] = str(self.t.pasta / "cli_aud.jsonl")
        args = SimpleNamespace(comando="consultar", entrada="Qual é o prazo da segunda via da declaração?",
                               chunking=None, gerador="principal", top_k=4)
        with patch("src.cli_d6.carregar", return_value=cfg), \
                patch("src.cli_d6._indice", return_value=self.t.indice), \
                patch("src.cliente.carregar", return_value=cfg), \
                patch("src.auditoria.ROOT", self.t.pasta / "fallback_nao_configurado"), \
                patch("src.cliente.chave", return_value="token-ficticio"), \
                patch("src.cliente.requests.post") as post, redirect_stdout(io.StringIO()):
            codigo = executar(args)
        self.assertEqual(codigo, 2)
        post.assert_not_called()
        destino_auditoria = self.t.pasta / "cli_aud.jsonl"
        self.assertTrue(destino_auditoria.is_file(), "A CLI deve usar o arquivo de auditoria configurado")
        evento = json.loads(destino_auditoria.read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual(evento["tipo"], "consulta_rag")
        self.assertEqual(evento["status"], "falha")
        self.assertEqual(evento["orcamento"]["chamadas"], 0)
        self.assertFalse((self.t.pasta / "fallback_nao_configurado").exists())

    def test_consulta_independente_conta_correcao_no_mesmo_orcamento(self):
        from copy import deepcopy

        cfg = deepcopy(self.t.cfg)
        cfg["guardrails"]["max_chamadas_execucao"] = 1
        resposta = Mock(status_code=200, json=lambda: {
            "choices": [{"message": {"content": "{}"}}],
        })
        with patch("src.cliente.carregar", return_value=cfg), \
                patch("src.cliente.chave", return_value="token-ficticio"), \
                patch("src.cliente.requests.post", return_value=resposta) as post:
            r = responder("Qual é o prazo da segunda via da declaração?", indice=self.t.indice,
                          gerador=criar_gerador(cfg, "principal"), cfg=cfg, auditar=False)
        self.assertEqual(post.call_count, 1)
        self.assertEqual(r["status"], "falha")
        self.assertTrue(any("Orçamento" in erro for erro in r["erros"]))


if __name__ == "__main__":
    unittest.main()
