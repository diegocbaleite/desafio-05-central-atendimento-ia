"""Pacote reproduzível com lista explícita de arquivos e inspeção de credenciais."""

from __future__ import annotations

import os
import zipfile
from pathlib import Path

from src.config import ROOT


def empacotar(destino=None) -> Path:
    arquivos = {ROOT / nome for nome in ("README.md", "requirements.txt", ".env.example", ".gitignore", ".streamlit/config.toml", "AGENTS.md", "desafio-expert.agents.md")}
    for pasta in ("src", "testes", "config", "prompts", "documentacao", "desafio-06", "dados/gabaritos", "dados/revisao"):
        for p in (ROOT / pasta).rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts and p.suffix.lower() not in {".pyc", ".tmp"}:
                arquivos.add(p)
    # Inclui os arquivos fornecidos, inclusive editais; o brasão não entra no acervo.
    for p in (ROOT / "dados/originais").iterdir():
        if p.is_file():
            arquivos.add(p)
    for p in (ROOT / "resultados/multimodal/referencias").glob("*.txt"):
        arquivos.add(p)
    permitidos = []
    segredos = [v for k, v in os.environ.items() if "API_KEY" in k and len(v) >= 12]
    for p in sorted(arquivos):
        if not p.is_file():
            continue
        if p.is_symlink() or not p.resolve().is_relative_to(ROOT.resolve()):
            raise ValueError("Arquivo externo ou link simbólico não pode entrar no pacote")
        if p.name.startswith(".env") and p.name != ".env.example":
            raise ValueError("Credenciais locais não podem entrar no pacote")
        conteudo = p.read_bytes()
        if any(segredo.encode() in conteudo for segredo in segredos):
            raise ValueError("Pacote bloqueado: credencial detectada; valor omitido")
        permitidos.append((p.relative_to(ROOT).as_posix(), conteudo))
    destino = Path(destino or ROOT / "dist/desafio-06-central-atendimento-ia.zip")
    destino.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destino, "w", compression=zipfile.ZIP_DEFLATED) as arquivo:
        for nome, conteudo in permitidos:
            info = zipfile.ZipInfo(nome, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            arquivo.writestr(info, conteudo)
    return destino
