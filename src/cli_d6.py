"""Comandos de CLI do Desafio 6 (chamados por src/main.py).

indexar | status-indice | consultar | solicitacao | excluir-documento | sentimentos | avaliar
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from .config import ROOT, carregar

COMANDOS_D6 = ("indexar", "status-indice", "consultar", "solicitacao", "excluir-documento", "sentimentos", "avaliar")


def _imprimir(valor):
    print(json.dumps(valor, ensure_ascii=False, indent=2, default=str))


def _indice(cfg, rotulo=None):
    from .embeddings import criar_embedder
    from .indice import IndiceVetorial

    return IndiceVetorial.de_config(cfg, criar_embedder(cfg), rotulo)


def executar(a) -> int:
    from .cliente import ErroAPI
    from .indice import ReindexacaoExigida
    from .orcamento import OrcamentoExcedido

    cfg = carregar()
    try:
        if a.comando == "indexar":
            from .ingestao import carregar_catalogo

            catalogo = carregar_catalogo(cfg)
            rotulos = [a.chunking] if a.chunking else list(cfg["recuperacao"]["chunking"])
            for rotulo in rotulos:
                rel = _indice(cfg, rotulo).indexar(catalogo, recriar=a.recriar, reincluir=[a.doc] if a.doc else ())
                _imprimir(rel)
            return 0
        if a.comando == "status-indice":
            from .ingestao import carregar_catalogo

            _imprimir(_indice(cfg, a.chunking).status(carregar_catalogo(cfg)))
            return 0
        if a.comando == "consultar":
            from .geracao import criar_gerador
            from .rag import responder

            if not a.entrada:
                raise ValueError('Informe a pergunta: python -m src.main consultar "sua pergunta"')
            r = responder(a.entrada, indice=_indice(cfg, a.chunking), gerador=criar_gerador(cfg, a.gerador), cfg=cfg, top_k=a.top_k)
            _imprimir({k: r[k] for k in ("status", "resposta", "fontes", "trechos_recuperados", "quarentena",
                                          "encaminhar_revisao", "motivos_revisao", "gerador", "erros", "latencia_ms")})
            print("Similaridade = 1 - distância de cosseno (maior = mais próximo). Não é garantia de veracidade.")
            return 0 if r["status"] != "falha" else 2
        if a.comando == "solicitacao":
            from .geracao import criar_gerador
            from .orcamento import Orcamento
            from .pipeline import processar_solicitacao
            from .revisao import RepositorioRevisao

            if not a.entrada:
                raise ValueError("Informe o arquivo .txt da solicitação (texto, transcrição ou OCR)")
            caminho = Path(a.entrada)
            texto = caminho.read_text(encoding="utf-8")
            r = processar_solicitacao(
                texto, caso_id=a.caso_id or caminho.stem, modalidade=a.modalidade, cfg=cfg,
                indice=_indice(cfg, a.chunking), gerador=criar_gerador(cfg, a.gerador),
                repositorio=RepositorioRevisao(ROOT / cfg["revisao"]["banco"]), orcamento=Orcamento.de_config(cfg),
            )
            _imprimir({k: r[k] for k in ("caso_id", "decisao", "motivos", "minuta_id", "status_minuta")})
            if r["minuta"]:
                print(r["minuta"])
                print("Minuta PENDENTE. Decida pela interface: streamlit run src/app.py (nada é enviado).")
            return 0
        if a.comando == "excluir-documento":
            from .embeddings import criar_embedder
            from .indice import IndiceVetorial
            from .privacidade import excluir_documento_e_derivados
            from .revisao import RepositorioRevisao

            if not a.doc:
                raise ValueError("Informe --doc DOC-XX")
            emb = criar_embedder(cfg)
            indices = [IndiceVetorial.de_config(cfg, emb, r) for r in cfg["recuperacao"]["chunking"]]
            _imprimir(excluir_documento_e_derivados(a.doc, cfg=cfg, indices=indices,
                                                    repositorio=RepositorioRevisao(ROOT / cfg["revisao"]["banco"])))
            print(f"Para reincluir: python -m src.main indexar --doc {a.doc}")
            return 0
        if a.comando == "sentimentos":
            from .metricas import agregar_sentimentos
            from .sentimento import classificar_llm, classificar_local

            avals = yaml.safe_load((ROOT / "dados/avaliacoes/avaliacoes.yaml").read_text(encoding="utf-8"))["avaliacoes"]
            gab = yaml.safe_load((ROOT / "dados/gabaritos/desafio6/sentimentos.yaml").read_text(encoding="utf-8"))["avaliacoes"]
            if a.gerador and cfg["geracao"]["perfis"][a.gerador]["tipo"] == "llm":
                from .orcamento import Orcamento

                orc, perfil = Orcamento.de_config(cfg), cfg["geracao"]["perfis"][a.gerador]
                resultados = [classificar_llm(x["id"], x["texto"], perfil, orc) for x in avals]
            else:
                resultados = [classificar_local(x["id"], x["texto"]) for x in avals]
            destino = ROOT / "resultados" / "sentimentos" / "ultimo.json"
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
            _imprimir(agregar_sentimentos(resultados, gab))
            return 0
        if a.comando == "avaliar":
            from .avaliacao_integrada import Avaliacao, publicar_evidencias

            avaliacao = Avaliacao(a.gerador or "extrativo_local")
            resumo = avaliacao.executar()
            _imprimir(resumo)
            print("Evidências:", avaliacao.pasta)
            if a.publicar_evidencias:
                print("Publicadas em:", publicar_evidencias(avaliacao.pasta))
            return 0 if not resumo["erros_de_etapa"] else 1
    except (ValueError, OSError, ErroAPI, ReindexacaoExigida, OrcamentoExcedido) as exc:
        print(f"Falha: {type(exc).__name__}: {str(exc)[:300]}")
        return 2
    raise ValueError("Comando desconhecido")
