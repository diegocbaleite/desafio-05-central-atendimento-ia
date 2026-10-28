"""Execuções de avaliação separadas dos gabaritos e da decisão humana."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.config import ROOT

from .fluxo import CATALOGO, FluxoDesafio6
from .guardrails import avaliar_entrada, hash_texto
from .indice import comparar_chunking
from .metricas import comparar_rotulos, metricas_rag, proporcao
from .nlp import analisar_solicitacao, avaliar_solicitacoes
from .sentimentos import classificar_avaliacoes
from .servicos import ClienteOpenAI, ClienteSimulado

DADOS = ROOT / "dados/desafio6"


def _ler(nome, chave):
    return json.loads((DADOS / nome).read_text(encoding="utf-8"))[chave]


def executar_avaliacao(*, mock=False, pasta=None):
    """Cada cenário possui seu orçamento; todo resultado registra se foi simulado.

    Gabaritos são carregados apenas pelo avaliador, nunca pelo cliente ou pela busca.
    Falhas são mantidas no denominador, sem alterar a referência após a execução.
    """
    factory = ClienteSimulado if mock else ClienteOpenAI
    fluxo = FluxoDesafio6(factory(), pasta=pasta)
    id_execucao = "avaliacao_" + uuid.uuid4().hex[:12]
    destino = fluxo.pasta / "avaliacoes" / id_execucao
    destino.mkdir(parents=True)
    manifest = {str(p.relative_to(DADOS)): hash_texto(p.read_text(encoding="utf-8"))
                for p in DADOS.rglob("*.json")}
    relatorio = {"id": id_execucao, "data_utc": datetime.now(timezone.utc).isoformat(),
                 "simulada": mock, "revisao_humana": "pendente", "manifesto_previo": manifest,
                 "orcamento_por_cenario": "máximo 12 chamadas e 60000 tokens reservados, incluindo retries/correção",
                 "nlp": [], "rag": [], "sentimentos": [], "falhas": []}
    arquivo = destino / "resultado.json"

    def salvar():
        arquivo.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8")

    salvar()  # Preserva o manifesto anterior às chamadas.
    try:
        relatorio["indexacao"] = fluxo.indexar()
    except Exception as exc:
        relatorio["falhas"].append({"etapa": "indexacao", "erro": type(exc).__name__})
        salvar()
        return arquivo
    for caso in _ler("solicitacoes.json", "solicitacoes"):
        cliente = factory()
        try:
            analise = analisar_solicitacao(caso["texto"], cliente, modalidade=caso["modalidade"], conferencia=False)
            relatorio["nlp"].append({"id": caso["id"], "analise": analise, "simulada": mock,
                                      "chamadas": cliente.chamadas, "orcamento": cliente.orcamento.resumo(),
                                      "saidas_estruturadas": cliente.saidas_estruturadas})
        except Exception as exc:
            relatorio["falhas"].append({"etapa": "nlp", "id": caso["id"], "erro": type(exc).__name__,
                                       "chamadas": cliente.chamadas})
        salvar()
    perguntas = _ler("perguntas.json", "perguntas")
    for pergunta in perguntas:
        try:
            resultado = fluxo.consultar(pergunta["pergunta"])
            resultado["id_execucao"] = resultado["id"]
            resultado["id"] = pergunta["id"]
            resultado["recuperacao_correta"] = any(
                ref["documento_id"] == trecho["documento_id"] and ref["trecho"] in trecho["trecho"]
                for ref in pergunta["referencias"] for trecho in resultado["trechos"]
            )
            resultado["todas_afirmacoes_sustentadas"] = (
                resultado["status"] == "fundamentada" and bool(resultado["afirmacoes"])
                and all(a["sustentada"] for a in resultado["afirmacoes"])
            )
            relatorio["rag"].append(resultado)
        except Exception as exc:
            relatorio["falhas"].append({"etapa": "rag", "id": pergunta["id"], "erro": type(exc).__name__})
        salvar()
    for avaliacao in _ler("avaliacoes.json", "avaliacoes"):
        cliente = factory()
        try:
            resultado = classificar_avaliacoes([avaliacao], cliente)[0]
            resultado["chamadas"] = cliente.chamadas
            relatorio["sentimentos"].append(resultado)
        except Exception as exc:
            relatorio["falhas"].append({"etapa": "sentimentos", "id": avaliacao["id"], "erro": type(exc).__name__})
        salvar()
    gabaritos = json.loads((DADOS / "gabaritos.json").read_text(encoding="utf-8"))
    nlp = avaliar_solicitacoes(relatorio["nlp"], gabaritos["solicitacoes"])
    nlp["acuracia_com_falhas"] = proporcao(nlp["categorias_corretas"], len(gabaritos["solicitacoes"]))
    relatorio["metricas"] = {"nlp": nlp, "rag": metricas_rag(relatorio["rag"], perguntas),
                             "sentimentos": comparar_rotulos(relatorio["sentimentos"], gabaritos["avaliacoes"])}
    relatorio["ataques"] = [{"id": a["id"], "obtido": avaliar_entrada(a["texto"], contexto=a.get("origem") == "acervo"),
                               "simulada": False, "metodo": "guardrails locais, sem geração"}
                              for a in _ler("ataques.json", "ataques")]
    cliente = factory()
    try:
        relatorio["chunking"] = comparar_chunking(CATALOGO, perguntas, cliente, destino / "chunking")
        relatorio["chunking"]["simulada"] = mock
        relatorio["chunking"]["chamadas"] = cliente.chamadas
        relatorio["chunking"]["orcamento"] = cliente.orcamento.resumo()
    except Exception as exc:
        relatorio["falhas"].append({"etapa": "chunking", "erro": type(exc).__name__, "chamadas": cliente.chamadas})
    relatorio["referencias_preservadas"] = all(
        hash_texto((DADOS / p).read_text(encoding="utf-8")) == sha for p, sha in manifest.items()
    )
    relatorio["revisoes_humanas_reais"] = len([r for r in fluxo.revisoes.listar() if r.get("revisao") and not r["revisao"]["simulada"]])
    relatorio["observacao"] = "Métricas automáticas não equivalem à revisão humana; suporte mede identidade de passagens, não completude semântica."
    salvar()
    return arquivo
