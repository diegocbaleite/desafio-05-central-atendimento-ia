"""RF14: contrato versionado, três camadas de validação e no máximo uma correção."""

import json
import unittest
from datetime import date

from src import contrato
from src.estruturacao import estruturar, ficha_por_regras
from src.orcamento import Orcamento, OrcamentoExcedido
from src.seguranca import AUSENTE

TEXTO = (
    "Nome: Maria Fictícia Albuquerque\nProtocolo: 2026.000123\nData: 02/10/2026\n"
    "Assunto: segunda via de certidão\nPedido: Solicito segunda via da certidão.\n"
)
HOJE = date(2026, 10, 27)


def ficha_valida():
    return ficha_por_regras(TEXTO)


class TestContrato(unittest.TestCase):
    def test_ficha_por_regras_e_valida_nas_tres_camadas(self):
        r = contrato.validar(ficha_valida(), TEXTO, HOJE)
        self.assertTrue(r["sintaxe_ok"] and r["esquema_ok"] and r["regras_ok"] and r["valido"], r)

    def test_json_sintatico_nao_basta_e_erros_sao_diferenciados(self):
        base = ficha_valida()
        extra = {**base, "prioridade": "alta"}
        tipo = {**base, "requer_revisao": "sim"}
        ausente = dict(base)
        ausente.pop("categoria")
        for obj, esperado in ((extra, "chave_extra"), (tipo, "tipo_incorreto"), (ausente, "campo_obrigatorio_ausente")):
            bruto = json.dumps(obj, ensure_ascii=False)
            self.assertIsNotNone(contrato.validar_sintaxe(bruto)[0])
            r = contrato.validar(bruto, TEXTO, HOJE)
            self.assertFalse(r["esquema_ok"])
            self.assertEqual({e["tipo"] for e in r["erros_esquema"]}, {esperado})

    def test_json_malformado(self):
        r = contrato.validar('{"protocolo": ', TEXTO, HOJE)
        self.assertFalse(r["sintaxe_ok"])
        self.assertEqual(r["erros_sintaxe"][0]["tipo"], "json_invalido")

    def test_regras_data_impossivel_futura_e_sem_suporte(self):
        casos = {
            "31/02/2026": "data_impossivel",
            "02/10/2027": "data_futura",
        }
        for data, tipo in casos.items():
            r = contrato.validar({**ficha_valida(), "data": data}, TEXTO.replace("02/10/2026", data), HOJE)
            self.assertIn(tipo, {e["tipo"] for e in r["erros_regras"]}, data)
        r = contrato.validar({**ficha_valida(), "protocolo": "2026-000999", "solicitante": "João Inventado"}, TEXTO, HOJE)
        campos = {e["campo"] for e in r["erros_regras"] if e["tipo"] == "dado_sem_suporte"}
        self.assertEqual(campos, {"protocolo", "solicitante"})

    def test_ausencia_coerente_e_revisao_obrigatoria(self):
        f = {**ficha_valida(), "protocolo": None}
        r = contrato.validar(f, TEXTO, HOJE)
        tipos = {e["tipo"] for e in r["erros_regras"]}
        self.assertIn("campos_ausentes_incoerentes", tipos)
        f["campos_ausentes"] = ["protocolo"]
        f["requer_revisao"] = False
        self.assertIn("revisao_obrigatoria", {e["tipo"] for e in contrato.validar(f, TEXTO, HOJE)["erros_regras"]})

    def test_entidade_literal_inventada(self):
        f = ficha_valida()
        f["entidades"].append({"tipo": "local", "valor": "Sinop", "literal": True, "evidencia": "Sinop"})
        self.assertIn("entidade_sem_suporte", {e["tipo"] for e in contrato.validar(f, TEXTO, HOJE)["erros_regras"]})

    def test_data_por_extenso_tem_suporte(self):
        texto = "Meu protocolo é 2026-000142, de 14 de outubro de 2026. Meu nome é Marcos Teste Silva e quero pedir a efetivação da matrícula."
        f = ficha_por_regras(texto)
        self.assertEqual(f["data"], "14/10/2026")
        self.assertTrue(contrato.validar(f, texto, HOJE)["valido"])

    def test_exibicao_de_ausencia(self):
        self.assertEqual(contrato.exibir(None), AUSENTE)
        self.assertEqual(AUSENTE, "não localizado")

    def test_data_impossivel_rotulada_e_mantida_para_bloqueio(self):
        f = ficha_por_regras(TEXTO.replace("02/10/2026", "31/02/2026"))
        self.assertEqual(f["data"], "31/02/2026")


class TestEstruturacaoLLM(unittest.TestCase):
    def _falso(self, respostas, chamadas):
        it = iter(respostas)

        def conversar(mensagens, orcamento=None, response_format=None, **kw):
            chamadas.append({"mensagens": mensagens, "response_format": response_format})
            if orcamento is not None:
                orcamento.reservar("teste")
            return {"texto": next(it), "provider": "teste", "modelo": "teste"}

        return conversar

    def test_valida_na_primeira_tentativa_com_esquema_restrito(self):
        chamadas = []
        r = estruturar(TEXTO, modo="llm", perfil={"saida_estruturada": True}, hoje=HOJE,
                       conversar_fn=self._falso([json.dumps(ficha_valida(), ensure_ascii=False)], chamadas))
        self.assertTrue(r["validacao"]["valido"])
        self.assertEqual(len(r["tentativas"]), 1)
        self.assertEqual(chamadas[0]["response_format"]["type"], "json_schema")
        self.assertIn("<conteudo_externo>", chamadas[0]["mensagens"][1]["content"])

    def test_uma_correcao_e_cerca_markdown(self):
        chamadas = []
        invalida = json.dumps({**ficha_valida(), "extra": 1})
        valida = "```json\n" + json.dumps(ficha_valida(), ensure_ascii=False) + "\n```"
        r = estruturar(TEXTO, modo="llm", perfil={}, hoje=HOJE, conversar_fn=self._falso([invalida, valida], chamadas))
        self.assertTrue(r["validacao"]["valido"])
        self.assertEqual(len(r["tentativas"]), 2)
        self.assertIn("rejeitada pela validação local", chamadas[1]["mensagens"][-1]["content"])

    def test_invalida_duas_vezes_e_rejeitada_sem_terceira_chamada(self):
        chamadas = []
        r = estruturar(TEXTO, modo="llm", perfil={}, hoje=HOJE,
                       conversar_fn=self._falso(['{"a": 1}', '{"b": 2}', '{"c": 3}'], chamadas))
        self.assertFalse(r["validacao"]["valido"])
        self.assertIsNone(r["ficha"])
        self.assertEqual(len(chamadas), 2)

    def test_correcao_consome_orcamento(self):
        orc = Orcamento(max_chamadas=1)
        with self.assertRaises(OrcamentoExcedido):
            estruturar(TEXTO, modo="llm", perfil={}, orcamento=orc, hoje=HOJE,
                       conversar_fn=self._falso(['{"a": 1}', '{"b": 2}'], []))
        self.assertEqual(orc.chamadas, 1)


if __name__ == "__main__":
    unittest.main()
