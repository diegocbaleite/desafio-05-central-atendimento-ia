"""Auditoria JSONL, com campos técnicos, sem prompt bruto nem segredos."""

import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .config import ROOT


def nova_execucao():
    return uuid.uuid4().hex[:12]


def sha256_arquivo(caminho):
    h = hashlib.sha256()
    with Path(caminho).open("rb") as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()


def nova_saida(destino, tipo):
    """Pasta única por execução para evidências de mídia; nunca sobrescreve."""
    raiz = Path(destino) if destino else ROOT / "resultados" / "multimodal"
    pasta = raiz / f"{tipo}_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}_{uuid.uuid4().hex[:6]}"
    pasta.mkdir(parents=True, exist_ok=False)
    return pasta


def gravar_json(caminho, valor):
    Path(caminho).write_text(
        json.dumps(valor, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def registrar(execucao, caso, etapa, **campos):
    pasta = ROOT / "resultados" / "execucoes" / execucao
    pasta.mkdir(parents=True, exist_ok=True)
    registro = {
        "id_execucao": execucao,
        "caso": caso,
        "etapa": etapa,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        **campos,
    }
    with (pasta / "auditoria.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False, default=str) + "\n")
    return pasta
