"""CLI do Desafio 6: python -m src.main desafio6 --help."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.config import ROOT

from .avaliacao import executar_avaliacao
from .fluxo import CATALOGO, FluxoDesafio6
from .indice import comparar_chunking
from .sentimentos import classificar_avaliacoes
from .servicos import ClienteOpenAI, ClienteSimulado


def main(argv=None):
    p = argparse.ArgumentParser(description="Desafio 6 / Prático 02 — central local com fontes e revisão humana")
    p.add_argument("acao", choices=("indexar", "consultar", "processar", "avaliar", "chunking", "sentimentos", "excluir", "revisar", "estado", "limpar-expirados", "empacotar"))
    p.add_argument("--mock", action="store_true", help="simulação explícita sem modelos nem APIs reais")
    p.add_argument("--pergunta")
    p.add_argument("--entrada", help="TXT de solicitação ou transcrição já conferida")
    p.add_argument("--texto", help="solicitação fictícia textual")
    p.add_argument("--modalidade", default="texto", choices=("texto", "audio", "ocr"))
    p.add_argument("--conferencia", action="store_true", help="operador confirma conferência dos dados STT/OCR no original")
    p.add_argument("--catalogo", type=Path)
    p.add_argument("--recriar", action="store_true")
    p.add_argument("--pasta", type=Path, help="pasta local de índice, derivados e auditoria")
    p.add_argument("--modelo", help="modelo de geração OpenAI; não altera embeddings nem reconstrói índice")
    p.add_argument("--documento-id")
    p.add_argument("--id")
    p.add_argument("--decisao", choices=("aprovar", "rejeitar", "revisar"))
    p.add_argument("--responsavel")
    p.add_argument("--justificativa")
    p.add_argument("--hash", dest="sha256")
    p.add_argument("--dias", type=int, default=30, help="retenção explícita de artefatos locais")
    a = p.parse_args(argv)
    try:
        if a.acao == "empacotar":
            from .pacote import empacotar
            print(empacotar())
            return 0
        if a.acao == "avaliar":
            caminho = executar_avaliacao(mock=a.mock, pasta=a.pasta)
            relatorio = json.loads(caminho.read_text(encoding="utf-8"))
            print(json.dumps({"evidencia": str(caminho), "simulada": a.mock,
                              "metricas": relatorio.get("metricas"), "falhas": relatorio["falhas"],
                              "revisao_humana": "pendente"}, ensure_ascii=False, indent=2))
            return 1 if relatorio["falhas"] else 0
        cliente = ClienteSimulado() if a.mock else ClienteOpenAI(modelo=a.modelo)
        fluxo = FluxoDesafio6(cliente, pasta=a.pasta)
        if a.acao == "indexar":
            resultado = fluxo.indexar(a.catalogo, recriar=a.recriar)
        elif a.acao == "estado":
            resultado = fluxo.indice.estado(fluxo.catalogo)
        elif a.acao == "consultar":
            if not a.pergunta:
                raise ValueError("Informe --pergunta")
            resultado = fluxo.consultar(a.pergunta)
        elif a.acao == "processar":
            if not a.pergunta or not (a.texto or a.entrada):
                raise ValueError("Informe --pergunta e --texto ou --entrada")
            texto = a.texto or Path(a.entrada).read_text(encoding="utf-8")
            resultado = fluxo.processar(texto, a.pergunta, modalidade=a.modalidade, conferencia=a.conferencia)
        elif a.acao == "excluir":
            if not a.documento_id:
                raise ValueError("Informe --documento-id")
            resultado = fluxo.excluir(a.documento_id)
        elif a.acao == "limpar-expirados":
            resultado = fluxo.limpar_expirados(a.dias)
        elif a.acao == "revisar":
            if not all((a.id, a.decisao, a.responsavel, a.justificativa, a.sha256)):
                raise ValueError("Revisão exige --id, --decisao, --responsavel, --justificativa e --hash da minuta atual")
            resultado = fluxo.revisoes.registrar_decisao(a.id, a.decisao, a.responsavel, a.justificativa,
                                                        sha256_esperado=a.sha256, simulada=a.mock)
            fluxo._auditar(a.id, "revisao_registrada", decisao=a.decisao, simulada=a.mock,
                           sha256_minuta=a.sha256)  # Identidade e justificativa ficam no registro de revisão.
        elif a.acao == "chunking":
            resultado = comparar_chunking(a.catalogo or CATALOGO, ROOT / "dados/desafio6/perguntas.json",
                                          cliente, fluxo.pasta / "comparacao_chunking")
            resultado.update(simulada=a.mock, orcamento=cliente.orcamento.resumo(), chamadas=cliente.chamadas)
            (fluxo.pasta / "chunking.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            itens = json.loads((ROOT / "dados/desafio6/avaliacoes.json").read_text(encoding="utf-8"))["avaliacoes"]
            resultado = classificar_avaliacoes(itens, cliente)
            (fluxo.pasta / "sentimentos.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        # Não imprimir corpos de resposta, prompts ou credenciais em diagnósticos.
        from .servicos import ErroServico
        seguro = str(exc) if isinstance(exc, (ValueError, PermissionError, ErroServico)) else "Falha local; consulte o estado e as evidências"
        print(json.dumps({"erro": type(exc).__name__, "mensagem": seguro[:250]}, ensure_ascii=False))
        return 2
