"""Conteúdo externo é dado não confiável, jamais instrução."""

import re
from pathlib import Path

AUSENTE = "não localizado"
FORMATOS_AUDIO = {".mp3", ".wav", ".m4a", ".ogg", ".webm"}
FORMATOS_IMAGEM = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".pdf"}
PADROES = [
    r"ignore.{0,80}(instruções|instrucoes|regras|instructions|rules|previous|prior)",
    r"disregard.{0,80}(instructions|rules|previous|prior)",
    r"(^|\n)\s*(sistema|system)\s*:",
    r"revele.{0,50}(prompt|segredo|chave)",
    r"reveal.{0,60}(prompt|system|secret|key)",
    r"(?i)deferido.{0,35}(prazo|dias)",
    r"desconsidere.{0,60}(instruções|instrucoes|regras)",
]


def detectar(texto):
    return [p for p in PADROES if re.search(p, texto, re.IGNORECASE)]


def delimitar(texto):
    texto = re.sub(
        r"</?conteudo_externo[^>]*>",
        "[tag externa neutralizada]",
        texto,
        flags=re.IGNORECASE,
    )
    return "<conteudo_externo>\n" + texto + "\n</conteudo_externo>"


def minimizar(texto):
    texto = re.sub(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b", "[CPF]", texto)
    texto = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[EMAIL]", texto)
    texto = re.sub(r"\(?\d{2}\)?\s?9\d{4}-?\d{4}", "[TELEFONE]", texto)
    return texto


def validar_arquivo(caminho, formatos, max_mb=20):
    """Valida existência, extensão, tamanho e assinatura (PDF/imagem); devolve o Path resolvido."""
    p = Path(caminho).expanduser().resolve()
    if not p.is_file() or p.suffix.lower() not in formatos:
        raise ValueError("Arquivo ausente ou extensão não suportada")
    if not 0 < p.stat().st_size <= max_mb * 1024 * 1024:
        raise ValueError(f"Arquivo vazio ou acima do limite de {max_mb} MiB")
    sufixo = p.suffix.lower()
    if sufixo == ".pdf":
        with p.open("rb") as f:
            if not f.read(5).startswith(b"%PDF-"):
                raise ValueError("Arquivo não contém assinatura PDF válida")
    elif sufixo in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
        from PIL import Image

        try:
            with Image.open(p) as img:
                img.verify()
        except (OSError, ValueError) as exc:
            raise ValueError("Imagem inválida ou corrompida") from exc
    return p
