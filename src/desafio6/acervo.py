"""Descoberta dos documentos fornecidos, sem modificar a pasta de originais."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from pypdf import PdfReader

from src.config import ROOT
from src.seguranca import FORMATOS_AUDIO

ORIGINAIS = ROOT / "dados/originais"
FORMATOS = {".txt", ".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"} | FORMATOS_AUDIO


def sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def carregar_catalogo_originais(raiz: Path | None = None) -> dict:
    """Lista documentos e mídias, excluindo o brasão e arquivos de configuração."""
    raiz = Path(raiz or ORIGINAIS).resolve()
    documentos = []
    for caminho in sorted(raiz.iterdir(), key=lambda p: p.name.casefold()):
        if not caminho.is_file() or caminho.name.casefold() in {"brasao.png", "brasão.png"}:
            continue
        if caminho.suffix.lower() not in FORMATOS:
            continue
        if caminho.is_symlink() or not caminho.resolve().is_relative_to(raiz):
            raise ValueError("Originais não podem apontar para arquivos externos")
        modalidade = "audio" if caminho.suffix.lower() in FORMATOS_AUDIO else "imagem" if caminho.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff"} else "documento"
        documentos.append({"id": "ORIG_" + hashlib.sha256(caminho.name.encode("utf-8")).hexdigest()[:12],
                           "titulo": caminho.stem, "versao": "não localizado", "arquivo": str(caminho),
                           "modalidade": modalidade, "sha256_original": sha256(caminho),
                           "arquivo_original": str(caminho), "origem": "documento fornecido"})
    return {"versao": "originais-1", "documentos": documentos}


def preparar_documentos(documentos, pasta: Path, cliente) -> list[dict]:
    """Cria texto derivado para áudio/PDF digitalizado, com cache vinculado ao hash.

    O mock usa somente as referências humanas existentes, identificadas como tal.
    Nenhuma transcrição simulada é apresentada como reconhecimento de IA.
    """
    from src.visao import _imagens_pdf
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    preparados = []
    for documento in documentos:
        item = dict(documento)
        caminho = Path(item["arquivo"]).resolve()
        hash_original = sha256(caminho)
        if item.get("sha256_original") and item["sha256_original"] != hash_original:
            raise ValueError("Documento original mudou; atualize o catálogo")
        item.update(arquivo_original=str(caminho), sha256_original=hash_original)
        sufixo = caminho.suffix.lower()
        precisa_audio = sufixo in FORMATOS_AUDIO
        precisa_ocr = sufixo in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
        if sufixo == ".pdf":
            pdf = PdfReader(caminho)
            paginas = [p.extract_text() or "" for p in pdf.pages]
            if any(not p.strip() for p in paginas) and any(p.strip() for p in paginas):
                raise ValueError("PDF misto exige OCR de páginas específicas antes da indexação")
            precisa_ocr = not any(p.strip() for p in paginas)
        if not precisa_audio and not precisa_ocr:
            preparados.append(item)
            continue
        modelo = "referencia-humana" if cliente.simulado else (
            cliente.cfg["multimodal"]["stt_modelo"] if precisa_audio else cliente.cfg["multimodal"]["ocr_modelo"]
        )
        chave = hashlib.sha256((hash_original + modelo + ("simulado" if cliente.simulado else "real")).encode()).hexdigest()
        derivado = pasta / (chave + ".txt")
        metadados = pasta / (chave + ".json")
        if derivado.exists() and metadados.exists():
            anterior = json.loads(metadados.read_text(encoding="utf-8"))
            if anterior.get("sha256_texto") != sha256(derivado):
                raise ValueError("Texto derivado alterado; revisão necessária")
        else:
            if cliente.simulado:
                nome = "referencia_audio_conferida.txt" if precisa_audio and caminho.name == "entrada_audio.mp3" else "referencia_ocr_conferida.txt" if precisa_ocr and caminho.name == "entrada_pdf-imagem.pdf" else None
                if not nome:
                    raise ValueError("Sem referência humana para simular esta mídia; execute a extração real")
                texto = (ROOT / "resultados/multimodal/referencias" / nome).read_text(encoding="utf-8")
                metodo = "referência humana anterior; não é execução de STT/OCR"
            elif precisa_audio:
                texto = cliente.transcrever(caminho)
                metodo = "transcrição OpenAI; conferência humana pendente"
            else:
                with tempfile.TemporaryDirectory(prefix="acervo_ocr_") as temporaria:
                    imagens = _imagens_pdf(caminho, Path(temporaria), 10) if sufixo == ".pdf" else [caminho]
                    texto = "\n\n".join(cliente.ler_pagina(imagem) for imagem in imagens)
                metodo = "OCR OpenAI; conferência humana pendente"
            if not isinstance(texto, str) or not texto.strip():
                raise ValueError("Extração vazia; documento não foi indexado")
            from .guardrails import SEGREDOS
            if SEGREDOS.search(texto):
                raise ValueError("Extração contém possível credencial; conteúdo não foi salvo")
            derivado.write_text(texto, encoding="utf-8")
            metadados.write_text(json.dumps({"sha256_original": hash_original, "sha256_texto": sha256(derivado),
                                             "modelo": modelo, "metodo": metodo}, ensure_ascii=False, indent=2), encoding="utf-8")
        item.update(arquivo=str(derivado), metodo_extracao=json.loads(metadados.read_text(encoding="utf-8"))["metodo"],
                    requer_conferencia_humana=True, pagina_original=1 if sufixo == ".pdf" else None)
        preparados.append(item)
    return preparados
