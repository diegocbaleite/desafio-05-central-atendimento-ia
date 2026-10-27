"""Leitura do acervo (TXT e PDF textual), seções, páginas e chunking (RF17/RF18)."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import yaml

from .config import ROOT
from .guardrails import avaliar_trecho

_SECAO = re.compile(r"^\s*(Seção\s+(\d+)\s+[—-]\s+.+?)\s*$")


def sha256_arquivo(caminho: Path) -> str:
    return hashlib.sha256(Path(caminho).read_bytes()).hexdigest()


def _ler_yaml_documentos(caminho: Path) -> list[dict]:
    if not caminho.is_file():
        return []
    dados = yaml.safe_load(caminho.read_text(encoding="utf-8")) or {}
    return list(dados.get("documentos") or [])


def carregar_catalogo(cfg: dict, incluir_enviados: bool = True) -> list[dict]:
    """Catálogo versionado + documentos enviados pela interface (não versionados)."""
    acervo = cfg.get("acervo", {})
    entradas = _ler_yaml_documentos(ROOT / acervo.get("catalogo", "dados/acervo/catalogo.yaml"))
    if incluir_enviados and acervo.get("catalogo_enviados"):
        for item in _ler_yaml_documentos(ROOT / acervo["catalogo_enviados"]):
            item["enviado"] = True
            entradas.append(item)
    ids = [e["id"] for e in entradas]
    duplicados = {i for i in ids if ids.count(i) > 1}
    if duplicados:
        raise ValueError("IDs duplicados no catálogo: " + ", ".join(sorted(duplicados)))
    for e in entradas:
        e["caminho"] = ROOT / e["arquivo"]
        e["versao"] = str(e["versao"])
    return entradas


def ler_paginas(caminho: Path) -> list[tuple[int | None, str]]:
    """TXT -> uma unidade sem página; PDF -> uma unidade por página (texto extraível)."""
    caminho = Path(caminho)
    if caminho.suffix.lower() == ".txt":
        return [(None, caminho.read_text(encoding="utf-8"))]
    if caminho.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        paginas = [(i + 1, p.extract_text() or "") for i, p in enumerate(PdfReader(str(caminho)).pages)]
        if not any(t.strip() for _, t in paginas):
            raise ValueError("PDF sem texto extraível (digitalizado?): use OCR antes de indexar")
        return paginas
    raise ValueError("Formato não suportado no acervo: " + caminho.suffix)


def _blocos(paginas):
    """Gera (pagina, secao, numero_secao, texto) ignorando o cabeçalho antes da 1ª seção.

    Uma seção que continua na página seguinte vira um novo bloco com a nova página,
    para que a citação aponte a página correta.
    """
    secao = numero = None
    for pagina, texto in paginas:
        linhas = []
        for linha in texto.splitlines():
            m = _SECAO.match(linha)
            if m:
                if secao and linhas:
                    yield pagina, secao, numero, " ".join(linhas)
                secao, numero, linhas = m.group(1), int(m.group(2)), []
            elif secao and linha.strip():
                linhas.append(linha.strip())
        if secao and linhas:
            yield pagina, secao, numero, " ".join(linhas)


def dividir(doc: dict, paginas, rotulo: str, tamanho: int, sobreposicao: int, unidade="palavras") -> list[dict]:
    """Janelas de `tamanho` palavras com `sobreposicao`; nunca cruzam seção ou página."""
    if unidade != "palavras":
        raise ValueError("Unidade de chunking suportada: palavras")
    if not 0 <= sobreposicao < tamanho:
        raise ValueError("Sobreposição deve ser >= 0 e menor que o tamanho")
    sha_doc = doc.get("sha256") or sha256_arquivo(doc["caminho"])
    trechos = []
    passo = tamanho - sobreposicao
    for pagina, secao, numero, texto in _blocos(paginas):
        palavras = texto.split()
        inicio, n = 0, 0
        while True:
            janela = " ".join(palavras[inicio : inicio + tamanho])
            pagina_id = pagina or 0
            chunk_id = f"{doc['id']}:v{doc['versao']}:{rotulo}:p{pagina_id}:s{numero}:c{n}"
            analise = avaliar_trecho(janela)
            trechos.append(
                {
                    "id": chunk_id,
                    "texto": janela,
                    "metadados": {
                        "doc_id": doc["id"],
                        "titulo": doc["titulo"],
                        "versao": doc["versao"],
                        "tema": doc.get("tema", ""),
                        "formato": doc.get("formato", Path(doc["arquivo"]).suffix.lstrip(".")),
                        "arquivo": doc["arquivo"],
                        "sha256_documento": sha_doc,
                        "pagina": pagina_id if pagina else -1,
                        "secao": secao,
                        "chunk_id": chunk_id,
                        "chunk_indice": n,
                        "sha256_trecho": hashlib.sha256(janela.encode("utf-8")).hexdigest(),
                        "unidade": unidade,
                        "tamanho": tamanho,
                        "sobreposicao": sobreposicao,
                        "config_chunking": rotulo,
                        "suspeito_injecao": analise["suspeito"],
                        "motivos_suspeita": "; ".join(analise["motivos"])[:300],
                        "vigencia_inicio": str(doc.get("vigencia_inicio", "")),
                        "prioridade": int(doc.get("prioridade", 1)),
                        "substitui": ",".join(doc.get("substitui") or []),
                    },
                }
            )
            if inicio + tamanho >= len(palavras):
                break
            inicio += passo
            n += 1
    # Um documento com qualquer trecho suspeito é tratado como não confiável por inteiro:
    # seus trechos limpos podem ser recuperados, mas a resposta vai para revisão humana.
    documento_suspeito = any(t["metadados"]["suspeito_injecao"] for t in trechos)
    for t in trechos:
        t["metadados"]["documento_suspeito"] = documento_suspeito
    return trechos


def descrever_local(meta: dict) -> str:
    """Rótulo de citação: documento, versão, seção e página (quando houver)."""
    pagina = meta.get("pagina", -1)
    local = f"{meta['doc_id']} v{meta['versao']}, {meta['secao']}"
    return local + (f", p. {pagina}" if isinstance(pagina, int) and pagina > 0 else "")
