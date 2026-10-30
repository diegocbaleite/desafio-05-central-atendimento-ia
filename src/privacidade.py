"""Retenção e exclusão (RF24): documento, vetores e resultados derivados.

Política (protótipo acadêmico, dados fictícios):
- documentos enviados pela interface: mantidos até exclusão explícita;
- vetores: removidos do índice na exclusão do documento (todas as coleções de chunking);
- resultados derivados (respostas RAG salvas que citam o documento): apagados junto;
- minutas já criadas: preservadas (são registro da decisão humana), mas listadas
  no relatório de exclusão para que o operador as reavalie;
- logs: mantêm apenas o evento de exclusão (sem conteúdo) e seguem a retenção de logs.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import yaml

from .config import ROOT


def _remover_de_catalogo_enviados(cfg: dict, doc_id: str, remover_arquivo: bool) -> dict:
    acervo = cfg.get("acervo", {})
    caminho = ROOT / acervo.get("catalogo_enviados", "dados/acervo/enviados/catalogo_enviados.yaml")
    if not caminho.is_file():
        return {"no_catalogo_enviados": False, "arquivo_removido": False}
    dados = yaml.safe_load(caminho.read_text(encoding="utf-8")) or {}
    docs = dados.get("documentos") or []
    alvo = next((d for d in docs if d["id"] == doc_id), None)
    if not alvo:
        return {"no_catalogo_enviados": False, "arquivo_removido": False}
    dados["documentos"] = [d for d in docs if d["id"] != doc_id]
    caminho.write_text(yaml.safe_dump(dados, allow_unicode=True, sort_keys=False), encoding="utf-8")
    removido = False
    if remover_arquivo and (ROOT / alvo["arquivo"]).is_file():
        (ROOT / alvo["arquivo"]).unlink()
        removido = True
    return {"no_catalogo_enviados": True, "arquivo_removido": removido}


def excluir_documento_e_derivados(
    doc_id: str,
    *,
    cfg: dict,
    indices: list,
    repositorio=None,
    pasta_derivados: Path | None = None,
    remover_arquivo_enviado: bool = True,
    arquivo_auditoria=None,
    motivo: str = "solicitação de exclusão",
) -> dict:
    from .auditoria import registrar_d6

    relatorio = {"doc_id": doc_id, "indices": [], "derivados_removidos": [], "minutas_afetadas": []}
    for indice in indices:
        relatorio["indices"].append(indice.excluir_documento(doc_id, motivo))
    pasta = pasta_derivados or ROOT / "resultados" / "rag"
    if pasta.is_dir():
        for arquivo in pasta.rglob("*.json"):
            try:
                conteudo = arquivo.read_text(encoding="utf-8")
            except OSError:
                continue
            if f'"doc_id": "{doc_id}"' in conteudo or f"{doc_id}:v" in conteudo:
                arquivo.unlink()
                relatorio["derivados_removidos"].append(str(arquivo.relative_to(pasta)))
    if repositorio is not None:
        for m in repositorio.listar():
            if any(c.startswith(f"{doc_id}:") for c in m["metadados"].get("chunk_ids", [])):
                relatorio["minutas_afetadas"].append({"id": m["id"], "status": m["status"]})
    relatorio["catalogo_enviados"] = _remover_de_catalogo_enviados(cfg, doc_id, remover_arquivo_enviado)
    registrar_d6(
        "exclusao_documento",
        arquivo=arquivo_auditoria,
        doc_id=doc_id,
        motivo=motivo,
        trechos_removidos={i["colecao"]: i["trechos_removidos"] for i in relatorio["indices"]},
        trechos_restantes={i["colecao"]: i["trechos_restantes"] for i in relatorio["indices"]},
        derivados_removidos=len(relatorio["derivados_removidos"]),
        minutas_afetadas=[m["id"] for m in relatorio["minutas_afetadas"]],
    )
    return relatorio


def aplicar_retencao(pastas: list[Path], dias: int, agora: float | None = None) -> list[str]:
    """Apaga arquivos de resultados mais antigos que `dias` (não toca em originais)."""
    limite = (agora or time.time()) - dias * 86400
    removidos = []
    for pasta in pastas:
        if not pasta.is_dir():
            continue
        for arquivo in pasta.rglob("*"):
            if arquivo.is_file() and arquivo.stat().st_mtime < limite:
                arquivo.unlink()
                removidos.append(str(arquivo))
    return removidos


def salvar_derivado_rag(resposta: dict, nome: str, pasta: Path | None = None) -> Path:
    destino = (pasta or ROOT / "resultados" / "rag") / f"{nome}.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(resposta, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return destino
