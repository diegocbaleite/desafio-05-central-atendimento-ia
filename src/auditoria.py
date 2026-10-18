"""Auditoria JSONL, com campos técnicos, sem prompt bruto nem segredos."""

import json
import time
import uuid

from .config import ROOT


def nova_execucao():
    return uuid.uuid4().hex[:12]


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
