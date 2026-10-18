"""Visão: OCR local (Tesseract) de imagens e PDFs digitalizados, com trechos incertos.

OCR local preserva privacidade e custo; o original nunca é modificado e a revisão
humana dos campos críticos é obrigatória.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from .auditoria import gravar_json, nova_saida, sha256_arquivo
from .avaliacao import avaliar_texto_extraido
from .seguranca import FORMATOS_IMAGEM, validar_arquivo


def _imagens_pdf(caminho: Path, pasta_temporaria: Path, limite_paginas: int) -> list[Path]:
    if not shutil.which("pdftoppm"):
        raise RuntimeError("Instale poppler-utils (pdftoppm) para OCR de PDF local")
    prefixo = pasta_temporaria / "pagina"
    try:
        subprocess.run(
            ["pdftoppm", "-f", "1", "-l", str(limite_paginas), "-r", "200",
             "-gray", "-png", str(caminho), str(prefixo)],
            check=True, capture_output=True, timeout=90)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("Falha ao renderizar páginas do PDF") from exc
    imagens = sorted(pasta_temporaria.glob("pagina-*.png"))
    if not imagens:
        raise RuntimeError("Nenhuma página foi renderizada do PDF")
    return imagens


def _ocr_imagem(caminho: Path, idioma: str, psm: int) -> tuple[str, list[dict]]:
    from PIL import Image, ImageEnhance, ImageOps
    import pytesseract
    with Image.open(caminho) as original:
        gray = ImageOps.autocontrast(original.convert("L"))
        processada = ImageEnhance.Contrast(gray).enhance(1.3)
        texto = pytesseract.image_to_string(processada, lang=idioma, config=f"--psm {psm}")
        dados = pytesseract.image_to_data(
            processada, lang=idioma, config=f"--psm {psm}",
            output_type=pytesseract.Output.DICT)
    incertos = []
    for palavra, confianca in zip(dados.get("text", []), dados.get("conf", [])):
        if not palavra.strip():
            continue
        try:
            conf = float(confianca)
        except (TypeError, ValueError):
            continue
        if 0 <= conf < 55 and len(incertos) < 30:
            incertos.append({"fragmento": palavra, "confianca_ocr": round(conf, 1)})
    return texto, incertos


def _ocr_paginas(entrada: Path, idioma, psm, limite_paginas, motor=None):
    """Lista de (texto, trechos incertos) por página; PDF é renderizado em temporária."""
    with tempfile.TemporaryDirectory(prefix="ocr_") as temporaria:
        imagens = (_imagens_pdf(entrada, Path(temporaria), limite_paginas)
                   if entrada.suffix.lower() == ".pdf" else [entrada])
        return [(motor or _ocr_imagem)(imagem, idioma, psm) for imagem in imagens]


def ler_imagem(caminho, idioma="por", psm=6, limite_paginas=3) -> str:
    """Texto OCR de imagem ou PDF digitalizado (até limite_paginas páginas)."""
    entrada = validar_arquivo(caminho, FORMATOS_IMAGEM, 20)
    paginas = _ocr_paginas(entrada, idioma, psm, limite_paginas)
    return "\n\n".join(texto.strip() for texto, _ in paginas)


def avaliar_ocr(caminho, *, idioma="por", psm=6, limite_paginas=3,
                gabarito=None, revisado=None, saida=None, motor_teste=None) -> Path:
    """OCR com texto bruto preservado, trechos incertos, métricas e revisão pendente."""
    entrada = validar_arquivo(caminho, FORMATOS_IMAGEM, 20)
    if not 1 <= limite_paginas <= 10:
        raise ValueError("O limite de páginas deve estar entre 1 e 10")
    if psm not in range(3, 14):
        raise ValueError("PSM do Tesseract inválido")
    inicio = time.monotonic()
    paginas_ocr = _ocr_paginas(entrada, idioma, psm, limite_paginas, motor_teste)
    pasta = nova_saida(saida, "ocr")
    trechos, paginas, texto_para_metrica = [], [], []
    for n, (texto, incertos) in enumerate(paginas_ocr, 1):
        trechos.append(f"[Página {n}]\n{texto.strip()}")
        texto_para_metrica.append(texto.strip())
        paginas.append({"pagina": n, "trechos_incertos": incertos})
    bruto = "\n\n".join(trechos)
    (pasta / "ocr_bruto.txt").write_text(bruto, encoding="utf-8")
    avaliacao = avaliar_texto_extraido("\n\n".join(texto_para_metrica), gabarito, revisado, pasta)
    gravar_json(pasta / "resultado.json", {
        "tipo": "OCR", "entrada": entrada.name, "sha256_original": sha256_arquivo(entrada),
        "idioma": idioma, "motor": "Tesseract" if motor_teste is None else "mock",
        "configuracao": {"psm": psm, "limite_paginas": limite_paginas},
        "paginas": paginas, "duracao_processamento_s": round(time.monotonic() - inicio, 3),
        "data_utc": datetime.now(timezone.utc).isoformat(),
        "arquivo_bruto": "ocr_bruto.txt", "requer_revisao_humana": True,
        **avaliacao,
    })
    return pasta
