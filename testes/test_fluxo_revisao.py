"""Revisão humana, conferência de campos críticos, bloqueios e códigos de saída da CLI."""

import hashlib
import json
import sys
import tempfile
import unittest
import warnings
import copy
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from src import avaliacao, main
from src.cliente import ErroAPI
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
        self.pasta_minutas = self.raiz / "resultados" / "minutas" / "execucao"
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
            patch(
                "src.main.gerar_voz",
                sintetizar_mock or (lambda *a, **k: Path("resultados/audios/tts_teste")),
            ),
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
        sintetizar = Mock(return_value=Path("resultados/audios/tts_teste"))
        resumo = self.amb.executar(
            lambda *a, **k: ("# MINUTA — NÃO ENVIADA\ncorpo", {}),
            ["aprovar", "Revisor Teste", "Conferido na fonte"],
            sintetizar,
        )
        pasta_caso = self.amb.pasta_minutas / "T99"
        aprovada = (pasta_caso / "minuta_aprovada.md").read_bytes()
        revisao = json.loads((pasta_caso / "revisao.json").read_text(encoding="utf-8"))
        self.assertEqual(resumo["estado_revisao"], "aprovada")
        self.assertEqual(revisao["revisor"], "Revisor Teste")
        self.assertEqual(revisao["justificativa"], "Conferido na fonte")
        self.assertFalse(revisao["simulada"])
        self.assertEqual(revisao["sha256_minuta"], hashlib.sha256(aprovada).hexdigest())
        sintetizar.assert_called_once()
        self.assertEqual(
            sintetizar.call_args.kwargs["saida"],
            self.amb.raiz / "resultados" / "audios",
        )
        self.assertEqual(
            resumo["pasta_audio"], str(Path("resultados/audios/tts_teste"))
        )
        evento = next(k for a, k in self.amb.eventos if a[2] == "revisao_humana")
        self.assertEqual(evento["revisor"], "Revisor Teste")

    def test_decisao_sem_responsavel_ou_justificativa_e_recusada(self):
        with self.assertRaisesRegex(ValueError, "obrigatórios"):
            self.amb.executar(
                lambda *a, **k: ("# MINUTA", {}), ["aprovar", "", "justificativa"]
            )
        self.assertFalse(
            (self.amb.pasta_minutas / "T99" / "minuta_aprovada.md").exists()
        )

    def test_rejeicao_nao_cria_minuta_aprovada_nem_audio(self):
        sintetizar = Mock(return_value=Path("resultados/audios/tts_teste"))
        resumo = self.amb.executar(
            lambda *a, **k: ("# MINUTA", {}),
            ["rejeitar", "Revisor Teste", "Contém dado inventado"],
            sintetizar,
        )
        self.assertEqual(resumo["estado_revisao"], "rejeitada")
        self.assertFalse(
            (self.amb.pasta_minutas / "T99" / "minuta_aprovada.md").exists()
        )
        sintetizar.assert_not_called()

    def test_nova_geracao_exige_nova_decisao_sobre_a_nova_versao(self):
        versoes = iter([("# v1", {}), ("# v2", {})])
        resumo = self.amb.executar(
            lambda *a, **k: next(versoes),
            ["nova", "R1", "Faltou lacuna", "aprovar", "R2", "Agora correta"],
        )
        pasta_caso = self.amb.pasta_minutas / "T99"
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
        with self.assertRaisesRegex(ValueError, "Responsável"):
            self.amb.executar(redigir_mock, ["", "", "", ""])
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
            ["", "", "", "Revisor Teste", "rejeitar", "Revisor Teste", "Fora do escopo"],
        )
        conferencia = resumo["conferencia_campos_criticos"]
        if conferencia is None:
            self.fail("Conferência deveria estar registrada")
        self.assertEqual(conferencia["status"], "confirmada")
        self.assertEqual(
            conferencia["responsavel"], "Revisor Teste"
        )

    def test_correcao_de_campo_critico_e_usada_na_minuta_sem_alterar_extracao_bruta(self):
        entrada_redigir = []

        def redigir_mock(ext, *args, **kwargs):
            entrada_redigir.append(ext)
            return "# MINUTA", {}

        self.amb.executar(
            redigir_mock,
            [
                "2026-000999",
                "",
                "",
                "Revisor Teste",
                "rejeitar",
                "Revisor Teste",
                "Valor conferido no original",
            ],
        )
        self.assertEqual(entrada_redigir[0]["campos"]["protocolo"]["valor"], "2026-000999")
        self.assertEqual(EXT["campos"]["protocolo"]["valor"], "2026-000142")
        pasta_caso = self.amb.pasta_execucao / "T99"
        original = json.loads((pasta_caso / "extracao.json").read_text(encoding="utf-8"))
        revisada = json.loads(
            (pasta_caso / "extracao_revisada.json").read_text(encoding="utf-8")
        )
        conferencia = json.loads(
            (pasta_caso / "conferencia_campos_criticos.json").read_text(encoding="utf-8")
        )
        self.assertEqual(original["campos"]["protocolo"]["valor"], "2026-000142")
        self.assertEqual(revisada["campos"]["protocolo"]["valor"], "2026-000999")
        self.assertIsNone(revisada["campos"]["protocolo"]["evidencia"])
        self.assertTrue(conferencia["campos"]["protocolo"]["corrigido"])

    def test_campo_ausente_exige_confirmacao_explicita(self):
        ext = copy.deepcopy(EXT)
        ext["campos"]["protocolo"]["valor"] = "não localizado"
        with patch("builtins.input", side_effect=["", ""]):
            with self.assertRaisesRegex(ValueError, "confirme esse estado"):
                main._conferir_campos_criticos(
                    self.amb.caso, ext, "execucao", simulacao=False
                )

    def test_campo_ausente_aceita_valor_na_segunda_pergunta(self):
        ext = copy.deepcopy(EXT)
        ext["campos"]["protocolo"]["valor"] = "não localizado"
        entradas = ["", "2026-000142", "", ""] + ["Revisor Teste"]
        with patch("builtins.input", side_effect=entradas):
            conferencia = main._conferir_campos_criticos(
                self.amb.caso, ext, "execucao", simulacao=False
            )
        self.assertEqual(
            conferencia["campos"]["protocolo"]["valor_confirmado"], "2026-000142"
        )

    def test_simulacao_fica_rotulada_e_nao_pede_confirmacao(self):
        resumo = self.amb.executar(
            lambda *a, **k: ("# MINUTA", {}), [], mock=True, decisao="aprovar"
        )
        self.assertEqual(resumo["conferencia_campos_criticos"], {"status": "simulada"})

    def test_pipeline_preserva_transcricao_bruta_e_parametros_stt(self):
        self.amb.executar(
            lambda *a, **k: ("# MINUTA", {}),
            [
                "",
                "",
                "",
                "Revisor Teste",
                "rejeitar",
                "Revisor Teste",
                "Fora do escopo",
            ],
        )
        pasta_caso = self.amb.pasta_execucao / "T99"
        self.assertEqual(
            (pasta_caso / "transcricao_bruta.txt").read_text(encoding="utf-8"),
            "texto fictício",
        )
        metadados = json.loads(
            (pasta_caso / "entrada_multimodal.json").read_text(encoding="utf-8")
        )
        self.assertEqual(metadados["provedor"], "groq")
        self.assertEqual(metadados["modelo"], "whisper-large-v3-turbo")
        self.assertTrue(metadados["requer_revisao_humana"])

    def test_pipeline_preserva_ocr_bruto_e_parametros(self):
        ambiente = _Ambiente(modalidade="imagem")
        self.addCleanup(ambiente.limpar)
        ambiente.executar(
            lambda *a, **k: ("# MINUTA", {}),
            [
                "",
                "",
                "",
                "Revisor Teste",
                "rejeitar",
                "Revisor Teste",
                "Fora do escopo",
            ],
        )
        pasta_caso = ambiente.pasta_execucao / "T99"
        self.assertEqual(
            (pasta_caso / "ocr_bruto.txt").read_text(encoding="utf-8"),
            "texto fictício",
        )
        metadados = json.loads(
            (pasta_caso / "entrada_multimodal.json").read_text(encoding="utf-8")
        )
        self.assertEqual(metadados["provedor"], "gemini")
        self.assertEqual(metadados["modelo"], "gemini-3.8-flash")
        self.assertEqual(metadados["parametros"]["psm"], "não aplicado")
        self.assertEqual(metadados["parametros"]["dpi_pdf"], 300)


class TestCli(unittest.TestCase):
    def _executar(self, argv):
        saida = StringIO()
        with (
            patch.object(sys, "argv", ["main", *argv]),
            patch("src.main.registrar"),
            patch("src.main.nova_execucao", return_value="exec"),
            patch(
                "src.main.gerar_visual",
                return_value=Path("resultados/imagens/arte_teste"),
            ),
            redirect_stdout(saida),
        ):
            return main.main(), saida.getvalue()

    def test_mock_arte_ignora_provedor_pago(self):
        args = SimpleNamespace(
            comando="arte", provider="cloudflare", mock=True, referencia=None
        )
        with (
            patch("src.main.gerar_visual", return_value=Path("arte")) as gerar,
            patch("builtins.print"),
        ):
            codigo = main._comando_midia(args)
        self.assertEqual(codigo, 0)
        self.assertEqual(gerar.call_args.kwargs["provider"], "local")
        self.assertEqual(
            gerar.call_args.kwargs["saida"], main.ROOT / "resultados" / "imagens"
        )
        self.assertEqual(
            gerar.call_args.kwargs["referencia"],
            main.ROOT / "dados" / "originais" / "brasao.png",
        )

    def test_codigo_de_saida_1_quando_algum_caso_falha(self):
        caso = {"id": "T99", "arquivo": "x", "modalidade": "texto"}
        with (
            patch("src.main.carregar_casos", return_value=[caso]),
            patch("src.main.executar_caso", side_effect=ValueError("falha controlada")),
        ):
            codigo, saida = self._executar(["--mock"])
        self.assertEqual(codigo, 1)
        self.assertIn("falha controlada", saida)

    def test_experimento_propaga_falha_para_codigo_de_saida(self):
        with (
            patch.object(sys, "argv", ["main", "experimento"]),
            patch("src.experimento.executar", return_value={"sucesso_total": False}),
            redirect_stdout(StringIO()),
        ):
            self.assertEqual(main.main(), 1)

    def test_falha_de_tts_torna_execucao_incompleta(self):
        caso = {"id": "T99", "arquivo": "x", "modalidade": "texto"}
        resumo = {
            "caso": "T99",
            "decisao": "aprovar",
            "simulada": False,
            "status_tts": "falha",
            "erro_tts": "serviço indisponível",
        }
        with (
            patch("src.main.carregar_casos", return_value=[caso]),
            patch("src.main.executar_caso", return_value=resumo),
        ):
            codigo, saida = self._executar([])
        self.assertEqual(codigo, 1)
        self.assertIn("FalhaTTS", saida)

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

    def test_fluxo_padrao_gera_imagem_institucional_em_resultados_imagens(self):
        saida = StringIO()
        with (
            patch.object(sys, "argv", ["main"]),
            patch(
                "src.main.carregar",
                return_value={
                    "multimodal": {"imagem_provider": "local"},
                    "projeto": {"timbre": "dados/originais/brasao.png"},
                },
            ),
            patch("src.main.carregar_casos", return_value=[]),
            patch("src.main.nova_execucao", return_value="exec"),
            patch("src.main.registrar"),
            patch(
                "src.main.gerar_visual",
                return_value=Path("resultados/imagens/arte_teste"),
            ) as gerar,
            redirect_stdout(saida),
        ):
            codigo = main.main()
        self.assertEqual(codigo, 0)
        self.assertEqual(
            gerar.call_args.kwargs["saida"], main.ROOT / "resultados" / "imagens"
        )
        self.assertEqual(gerar.call_args.kwargs["provider"], "local")
        self.assertEqual(
            json.loads(saida.getvalue())["imagem_institucional"],
            str(Path("resultados/imagens/arte_teste")),
        )

    def test_falha_da_imagem_institucional_retorna_codigo_1(self):
        saida = StringIO()
        with (
            patch.object(sys, "argv", ["main"]),
            patch("src.main.carregar_casos", return_value=[]),
            patch("src.main.nova_execucao", return_value="exec"),
            patch("src.main.registrar"),
            patch("src.main.gerar_visual", side_effect=ErroAPI("indisponível")),
            redirect_stdout(saida),
        ):
            codigo = main.main()
        texto = saida.getvalue()
        resumo = json.loads(texto[texto.index("{") :])
        self.assertEqual(codigo, 1)
        self.assertEqual(resumo["imagem_institucional"], "não localizado")
        self.assertEqual(resumo["falhas"][0]["caso"], "IMAGEM_INSTITUCIONAL")

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

    def test_audio_despacha_sem_sinalizador_de_autorizacao(self):
        with patch("src.main.avaliar_audio", return_value=Path("pasta")) as avaliar:
            codigo, saida = self._executar(
                ["audio", "fala.mp3", "--provider", "groq"]
            )
        self.assertEqual(codigo, 0)
        self.assertEqual(avaliar.call_args.kwargs["provider"], "groq")
        self.assertEqual(
            avaliar.call_args.kwargs["saida"], main.ROOT / "resultados" / "audios"
        )
        self.assertIn("Nenhum envio externo", saida)

    def test_ocr_e_voz_usam_diretorios_especificos(self):
        ocr_args = SimpleNamespace(
            comando="ocr",
            entrada="formulario.png",
            psm=6,
            gabarito=None,
            revisado=None,
            provider="local",
        )
        voz_args = SimpleNamespace(
            comando="voz",
            entrada="minuta.md",
            revisao="revisao.json",
            provider="espeak",
        )
        with (
            patch(
                "src.main.carregar",
                return_value={"multimodal": {"ocr_modelo": "modelo-teste"}},
            ),
            patch("src.main.avaliar_ocr", return_value=Path("ocr")) as avaliar,
            patch("src.main.gerar_voz", return_value=Path("voz")) as gerar,
            patch("builtins.print"),
        ):
            self.assertEqual(main._comando_midia(ocr_args), 0)
            self.assertEqual(main._comando_midia(voz_args), 0)
        self.assertEqual(
            avaliar.call_args.kwargs["saida"], main.ROOT / "resultados" / "ocr"
        )
        self.assertEqual(
            gerar.call_args.kwargs["saida"], main.ROOT / "resultados" / "audios"
        )

    def test_fluxo_principal_encaminha_audio_ao_provedor_configurado(self):
        with tempfile.TemporaryDirectory() as d:
            arq = Path(d) / "fala.mp3"
            arq.write_bytes(b"ID3fake")
            with patch("src.main.transcrever", return_value="transcrição fictícia") as stt:
                texto = main.preparar_entrada(arq, "audio")
            self.assertEqual(texto, "transcrição fictícia")
            stt.assert_called_once_with(arq)


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

    def test_compara_todos_os_elementos_presentes_no_gabarito(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            pasta = raiz / "dados/gabaritos"
            pasta.mkdir(parents=True)
            (pasta / "T99.json").write_text(
                json.dumps(
                    {
                        "protocolo": "não localizado",
                        "data_solicitacao": "não localizado",
                        "solicitante": "Pessoa Fictícia",
                        "assunto": "agendamento",
                        "pedido": "marcar atendimento",
                        "categoria": "agendamento",
                        "alerta_injecao": False,
                        "ausentes": ["protocolo", "data_solicitacao"],
                        "decisao_esperada": "aprovar com lacunas sinalizadas",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            extracao = {
                "campos": {
                    "protocolo": {"valor": "não localizado"},
                    "data_solicitacao": {"valor": "não localizado"},
                    "solicitante": {"valor": "Pessoa Fictícia"},
                    "assunto": {"valor": "agendamento"},
                    "pedido": {"valor": "marcar atendimento"},
                },
                "categoria": {"codigo": "agendamento"},
                "alerta_injecao": False,
                "campos_ausentes": ["data_solicitacao", "protocolo"],
            }
            with patch("src.avaliacao.ROOT", raiz):
                resultado = avaliacao.avaliar_campos(extracao, "T99")
        self.assertTrue(all(campo["correto"] for campo in resultado["campos"].values()))
        self.assertTrue(resultado["campos_ausentes"]["correto"])
        self.assertEqual(resultado["gravidade_geral"], None)
        self.assertIn("revisão humana", resultado["observacao_decisao"])


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
