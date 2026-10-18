"""Revisão humana, conferência de campos críticos, bloqueios e códigos de saída da CLI."""

import hashlib
import json
import sys
import tempfile
import unittest
import warnings
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

from src import avaliacao, main
from src.minuta import redigir

EXT = {
    "campos": {
        "protocolo": {"valor": "2026-000142"},
        "data_solicitacao": {"valor": "14/10/2026"},
        "solicitante": {"valor": "Pessoa Fictícia"},
    },
    "campos_ausentes": [],
    "categoria": {"codigo": "outros"},
    "alerta_injecao": False,
}


class _Ambiente:
    """Raiz temporária com entrada e schema; isola gravações e a auditoria."""

    def __init__(self, modalidade="texto"):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self.tmp.name)
        arquivo = self.raiz / "dados" / "originais" / "T99.txt"
        arquivo.parent.mkdir(parents=True)
        arquivo.write_text("texto fictício", encoding="utf-8")
        schema = self.raiz / "src" / "schemas"
        schema.mkdir(parents=True)
        origem = main.ROOT / "src" / "schemas" / "extracao.schema.json"
        (schema / "extracao.schema.json").write_bytes(origem.read_bytes())
        self.pasta_execucao = self.raiz / "resultados" / "execucao"
        self.caso = {
            "id": "T99",
            "arquivo": "dados/originais/T99.txt",
            "modalidade": modalidade,
        }
        self.eventos = []

    def registrar(self, *args, **kwargs):
        self.eventos.append((args, kwargs))
        return self.pasta_execucao

    def patches(self, redigir_mock, sintetizar_mock=None):
        return (
            patch("src.main.ROOT", self.raiz),
            patch("src.main.registrar", side_effect=self.registrar),
            patch("src.main.preparar_entrada", return_value="texto fictício"),
            patch("src.main.extrair", return_value=EXT),
            patch("src.main.redigir", redigir_mock),
            patch("src.main.sintetizar", sintetizar_mock or (lambda *a, **k: None)),
            patch("jsonschema.validate"),
        )

    def executar(self, redigir_mock, entradas, sintetizar_mock=None, **kwargs):
        ctx = self.patches(redigir_mock, sintetizar_mock)
        for c in ctx:
            c.start()
        try:
            with (
                patch("builtins.input", side_effect=entradas),
                redirect_stdout(StringIO()),
            ):
                return main.executar_caso(self.caso, "execucao", **kwargs)
        finally:
            for c in ctx:
                c.stop()

    def limpar(self):
        self.tmp.cleanup()


class TestAprovacaoHumana(unittest.TestCase):
    def setUp(self):
        self.amb = _Ambiente()
        self.addCleanup(self.amb.limpar)

    def test_aprovacao_registra_responsavel_justificativa_e_hash(self):
        sintetizar = Mock(return_value="audio.mp3")
        resumo = self.amb.executar(
            lambda *a, **k: ("# MINUTA — NÃO ENVIADA\ncorpo", {}),
            ["aprovar", "Revisor Teste", "Conferido na fonte"],
            sintetizar,
        )
        pasta_caso = self.amb.pasta_execucao / "T99"
        aprovada = (pasta_caso / "minuta_aprovada.md").read_bytes()
        revisao = json.loads((pasta_caso / "revisao.json").read_text(encoding="utf-8"))
        self.assertEqual(resumo["estado_revisao"], "aprovada")
        self.assertEqual(revisao["revisor"], "Revisor Teste")
        self.assertEqual(revisao["justificativa"], "Conferido na fonte")
        self.assertFalse(revisao["simulada"])
        self.assertEqual(revisao["sha256_minuta"], hashlib.sha256(aprovada).hexdigest())
        sintetizar.assert_called_once()
        evento = next(k for a, k in self.amb.eventos if a[2] == "revisao_humana")
        self.assertEqual(evento["revisor"], "Revisor Teste")

    def test_decisao_sem_responsavel_ou_justificativa_e_recusada(self):
        with self.assertRaisesRegex(ValueError, "obrigatórios"):
            self.amb.executar(
                lambda *a, **k: ("# MINUTA", {}), ["aprovar", "", "justificativa"]
            )
        self.assertFalse(
            (self.amb.pasta_execucao / "T99" / "minuta_aprovada.md").exists()
        )

    def test_rejeicao_nao_cria_minuta_aprovada_nem_audio(self):
        sintetizar = Mock(return_value="audio.mp3")
        resumo = self.amb.executar(
            lambda *a, **k: ("# MINUTA", {}),
            ["rejeitar", "Revisor Teste", "Contém dado inventado"],
            sintetizar,
        )
        self.assertEqual(resumo["estado_revisao"], "rejeitada")
        self.assertFalse(
            (self.amb.pasta_execucao / "T99" / "minuta_aprovada.md").exists()
        )
        sintetizar.assert_not_called()

    def test_nova_geracao_exige_nova_decisao_sobre_a_nova_versao(self):
        versoes = iter([("# v1", {}), ("# v2", {})])
        resumo = self.amb.executar(
            lambda *a, **k: next(versoes),
            ["nova", "R1", "Faltou lacuna", "aprovar", "R2", "Agora correta"],
        )
        pasta_caso = self.amb.pasta_execucao / "T99"
        revisao = json.loads((pasta_caso / "revisao.json").read_text(encoding="utf-8"))
        self.assertEqual(resumo["versao_minuta"], 2)
        self.assertTrue((pasta_caso / "minuta_v1.md").exists())
        self.assertEqual((pasta_caso / "minuta_aprovada.md").read_bytes(), b"# v2")
        self.assertEqual(revisao["versao_minuta"], 2)
        self.assertEqual(revisao["sha256_minuta"], hashlib.sha256(b"# v2").hexdigest())

    def test_decisao_por_codigo_exige_marcacao_de_simulacao(self):
        with self.assertRaisesRegex(ValueError, "simulada"):
            self.amb.executar(
                lambda *a, **k: ("# MINUTA", {}), [], decisao="aprovar"
            )

    def test_entrada_ausente_tem_mensagem_acionavel(self):
        (self.amb.raiz / "dados" / "originais" / "T99.txt").unlink()
        with self.assertRaisesRegex(ValueError, "casos.yaml"):
            self.amb.executar(lambda *a, **k: ("# MINUTA", {}), [])


class TestConferenciaDeCamposCriticos(unittest.TestCase):
    def setUp(self):
        self.amb = _Ambiente(modalidade="audio")
        self.addCleanup(self.amb.limpar)

    def test_minuta_bloqueada_sem_confirmacao(self):
        redigir_mock = Mock(return_value=("# MINUTA", {}))
        with self.assertRaisesRegex(ValueError, "não confirmada"):
            self.amb.executar(redigir_mock, ["nao", "Revisor Teste"])
        redigir_mock.assert_not_called()
        status = [
            k["status"]
            for a, k in self.amb.eventos
            if a[2] == "conferencia_campos_criticos"
        ]
        self.assertEqual(status, ["bloqueada"])

    def test_confirmacao_registra_responsavel(self):
        resumo = self.amb.executar(
            lambda *a, **k: ("# MINUTA", {}),
            ["sim", "Revisor Teste", "rejeitar", "Revisor Teste", "Fora do escopo"],
        )
        self.assertEqual(resumo["conferencia_campos_criticos"]["status"], "confirmada")
        self.assertEqual(
            resumo["conferencia_campos_criticos"]["responsavel"], "Revisor Teste"
        )

    def test_simulacao_fica_rotulada_e_nao_pede_confirmacao(self):
        resumo = self.amb.executar(
            lambda *a, **k: ("# MINUTA", {}), [], mock=True, decisao="aprovar"
        )
        self.assertEqual(resumo["conferencia_campos_criticos"], {"status": "simulada"})


class TestCli(unittest.TestCase):
    def _executar(self, argv):
        saida = StringIO()
        with (
            patch.object(sys, "argv", ["main", *argv]),
            patch("src.main.registrar"),
            patch("src.main.nova_execucao", return_value="exec"),
            redirect_stdout(saida),
        ):
            return main.main(), saida.getvalue()

    def test_codigo_de_saida_1_quando_algum_caso_falha(self):
        caso = {"id": "T99", "arquivo": "x", "modalidade": "texto"}
        with (
            patch("src.main.carregar_casos", return_value=[caso]),
            patch("src.main.executar_caso", side_effect=ValueError("falha controlada")),
        ):
            codigo, saida = self._executar(["--mock"])
        self.assertEqual(codigo, 1)
        self.assertIn("falha controlada", saida)

    def test_codigo_de_saida_0_e_taxa_sem_decisao_humana_real(self):
        caso = {"id": "T99", "arquivo": "x", "modalidade": "texto"}
        resumo = {"caso": "T99", "decisao": "aprovar", "simulada": True}
        with (
            patch("src.main.carregar_casos", return_value=[caso]),
            patch("src.main.executar_caso", return_value=resumo),
        ):
            codigo, saida = self._executar(["--mock"])
        taxa = json.loads(saida)["taxa_aprovacao"]
        self.assertEqual(codigo, 0)
        self.assertIsNone(taxa["taxa_aprovacao_direta"])
        self.assertEqual(taxa["excluidas_simuladas"], 1)

    def test_verificar_mostra_versoes_e_ferramentas_sem_aviso(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            codigo, saida = self._executar(["verificar"])
        self.assertEqual(codigo, 0)
        self.assertIn("jsonschema", saida)
        self.assertIn("ferramenta tesseract", saida)
        self.assertIn("envio automatico: False", saida)

    def test_comando_de_midia_sem_entrada_falha_com_mensagem(self):
        codigo, saida = self._executar(["audio"])
        self.assertEqual(codigo, 2)
        self.assertIn("Informe o arquivo", saida)

    def test_voz_exige_json_de_aprovacao_humana(self):
        codigo, saida = self._executar(["voz", "minuta.md"])
        self.assertEqual(codigo, 2)
        self.assertIn("--revisao", saida)

    def test_audio_despacha_com_autorizacao_explicita(self):
        with patch("src.main.avaliar_audio", return_value=Path("pasta")) as avaliar:
            codigo, saida = self._executar(
                ["audio", "fala.mp3", "--provider", "groq", "--autorizar-api"]
            )
        self.assertEqual(codigo, 0)
        self.assertEqual(avaliar.call_args.kwargs["provider"], "groq")
        self.assertTrue(avaliar.call_args.kwargs["permitir_api"])
        self.assertIn("Nenhum envio externo", saida)

    def test_audio_remoto_no_fluxo_principal_exige_autorizacao(self):
        with tempfile.TemporaryDirectory() as d:
            arq = Path(d) / "fala.mp3"
            arq.write_bytes(b"ID3fake")
            with patch(
                "src.audio.carregar", return_value={"multimodal": {"stt_provider": "groq"}}
            ):
                with self.assertRaises(PermissionError):
                    main.preparar_entrada(arq, "audio")


class TestAvaliacao(unittest.TestCase):
    def test_taxa_exclui_simuladas_e_explicita_denominador(self):
        taxa = avaliacao.taxa_aprovacao(
            [
                {"decisao": "aprovar", "simulada": False},
                {"decisao": "rejeitar", "simulada": False},
                {"decisao": "aprovar", "simulada": True},
            ]
        )
        self.assertEqual(taxa["total_com_decisao_humana"], 2)
        self.assertEqual(taxa["taxa_aprovacao_direta"], 0.5)
        self.assertEqual(taxa["excluidas_simuladas"], 1)

    def test_protocolo_incorreto_e_erro_critico(self):
        ext = {
            "campos": {
                "protocolo": {"valor": "2026-000999"},
                "data_solicitacao": {"valor": "14/10/2026"},
            },
            "categoria": {"codigo": "efetivacao_matricula"},
            "alerta_injecao": False,
        }
        r = avaliacao.avaliar_campos(ext, "T01")
        self.assertEqual(r["campos"]["protocolo"]["gravidade"], "critica")
        self.assertIsNone(r["campos"]["data_solicitacao"]["gravidade"])

    def test_sem_gabarito_devolve_none(self):
        self.assertIsNone(avaliacao.avaliar_campos({}, "NAO_EXISTE"))


class TestMinutaEPrompt(unittest.TestCase):
    EXTRACAO = {
        "campos": {
            "solicitante": {"valor": "Pessoa Fictícia"},
            "protocolo": {"valor": "2026-000142"},
            "assunto": {"valor": "não localizado"},
            "pedido": {"valor": "solicito matrícula"},
        },
        "campos_ausentes": ["assunto"],
    }

    def test_minuta_cita_timbre_sem_alegar_validacao_oficial(self):
        minuta, _ = redigir(self.EXTRACAO, "origem.txt", provider="mock")
        self.assertIn("Timbre institucional", minuta)
        self.assertIn("não validada oficialmente", minuta)

    @patch("src.minuta.conversar")
    def test_prompt_versionado_e_hash_registrado(self, conversar):
        conversar.return_value = {"texto": "corpo", "provider": "x", "modelo": "m"}
        _, meta = redigir(self.EXTRACAO, "origem.txt", provider="openrouter")
        sistema = conversar.call_args.args[0][0]["content"]
        self.assertIn("PERSONA:", sistema)
        self.assertEqual(meta["prompt_arquivo"], "prompts/sistema_minuta.md")
        self.assertEqual(
            meta["prompt_sha256"], hashlib.sha256(sistema.encode("utf-8")).hexdigest()
        )


if __name__ == "__main__":
    unittest.main()
