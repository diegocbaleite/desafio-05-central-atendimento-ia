"""Entrada multimodal validada; STT real por API, TTS real ou eSpeak, OCR local."""

from __future__ import annotations

import shutil
import subprocess
import wave
from pathlib import Path

from .cliente import ErroAPI
from .config import carregar, chave


def validar_arquivo(caminho, permitidas, max_mb):
    p = Path(caminho)
    if not p.exists() or not p.is_file():
        raise ValueError("Arquivo de entrada não encontrado: " + str(p))
    if p.suffix.lower() not in permitidas:
        raise ValueError("Extensão não permitida: " + p.suffix)
    if p.stat().st_size > max_mb * 1024 * 1024 or p.stat().st_size == 0:
        raise ValueError("Arquivo vazio ou muito grande")
    if p.suffix == ".wav":
        with wave.open(str(p), "rb") as w:
            return round(w.getnframes() / max(1, w.getframerate()), 2)
    return None


def ler_imagem(caminho):
    validar_arquivo(caminho, {".png", ".jpg", ".jpeg", ".tif", ".tiff"}, 10)
    import pytesseract
    from PIL import Image, ImageEnhance, ImageOps

    with Image.open(caminho) as src:
        img = ImageEnhance.Contrast(ImageOps.autocontrast(src.convert("L"))).enhance(
            1.5
        )
    return pytesseract.image_to_string(img, lang="por", config="--psm 6")


def transcrever(caminho, provider=None):
    import requests

    validar_arquivo(caminho, {".wav", ".mp3", ".m4a", ".ogg", ".webm"}, 20)
    cfg = carregar()
    provider = provider or cfg["multimodal"]["stt_provider"]
    if provider == "mock":
        raise ErroAPI(
            "STT fictício não transcreve áudio; use referência explicitamente rotulada"
        )
    token = chave(cfg, provider)
    if not token:
        raise ErroAPI("Falta chave de STT; configure .env ou use --mock")
    perfil = cfg["provedores"].get(provider)
    if not perfil:
        raise ErroAPI("Provedor STT não cadastrado")
    with open(caminho, "rb") as f:
        try:
            r = requests.post(
                perfil["base_url"].rstrip("/") + "/audio/transcriptions",
                headers={"Authorization": "Bearer " + token},
                data={"model": cfg["multimodal"]["stt_modelo"], "language": "pt"},
                files={"file": (Path(caminho).name, f)},
                timeout=120,
            )
        except requests.RequestException as e:
            raise ErroAPI("Falha de conexão STT: " + type(e).__name__) from e
    if not r.ok:
        raise ErroAPI("STT indisponível HTTP " + str(r.status_code))
    try:
        texto = r.json()["text"]
    except (ValueError, KeyError, TypeError) as e:
        raise ErroAPI("STT retornou transcrição inválida") from e
    if not texto.strip():
        raise ErroAPI("STT devolveu texto vazio")
    return texto


def sintetizar(texto, destino, provider=None):
    import requests

    cfg = carregar()
    provider = provider or cfg["multimodal"]["tts_provider"]
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    # Áudio só é chamado após aprovação pela camada de revisão.
    if provider == "mock":
        return None
    if provider == "espeak":
        if not shutil.which("espeak"):
            raise ErroAPI("Instale espeak para TTS offline")
        destino = destino.with_suffix(".wav")
        subprocess.run(
            [
                "espeak",
                "-v",
                "pt-br",
                "-s",
                "145",
                "-w",
                str(destino),
                texto[:3500].replace("#", " ").replace("*", " "),
            ],
            check=True,
        )
        return str(destino)
    token = chave(cfg, provider)
    if not token:
        raise ErroAPI("Falta chave TTS: configure .env")
    perfil = cfg["provedores"].get(provider)
    if not perfil:
        raise ErroAPI("Provedor TTS não cadastrado")
    try:
        r = requests.post(
            perfil["base_url"].rstrip("/") + "/audio/speech",
            headers={"Authorization": "Bearer " + token},
            json={
                "model": cfg["multimodal"]["tts_modelo"],
                "voice": cfg["multimodal"]["tts_voz"],
                "input": texto[:3500],
                "response_format": "mp3",
            },
            timeout=120,
        )
    except requests.RequestException as e:
        raise ErroAPI("Falha TTS: " + type(e).__name__) from e
    if not r.ok:
        raise ErroAPI("TTS indisponível HTTP " + str(r.status_code))
    destino = destino.with_suffix(".mp3")
    destino.write_bytes(r.content)
    return str(destino)


def imagem_local(destino):
    """Arte por PILLOW = COMPOSIÇÃO PROGRAMÁTICA, não IA generativa."""
    from PIL import Image, ImageDraw, ImageFont

    def fonte(n):
        for p in (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ):
            if Path(p).exists():
                return ImageFont.truetype(p, n)
        return ImageFont.load_default()

    im = Image.new("RGB", (960, 1440), "white")
    d = ImageDraw.Draw(im)
    d.rectangle((55, 55, 905, 1360), outline="#214562", width=9)
    d.text((90, 110), "ATENDIMENTO AO CIDADÃO", font=fonte(37), fill="#214562")
    d.text((90, 290), "• Documentos e protocolos", font=fonte(28), fill="#214562")
    d.text((90, 385), "• Conferência de informações", font=fonte(28), fill="#214562")
    d.text((90, 480), "• Revisão por servidor", font=fonte(28), fill="#214562")
    d.text((90, 720), "Nenhuma resposta é enviada", font=fonte(28), fill="#214562")
    d.text((90, 768), "automaticamente.", font=fonte(28), fill="#214562")
    d.rectangle((80, 1170, 880, 1320), fill="#214562")
    d.text((100, 1195), "COMPOSIÇÃO DIGITAL FICTÍCIA", font=fonte(26), fill="white")
    d.text((100, 1250), "PROGRAMÁTICA — SEM IA", font=fonte(25), fill="white")
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    im.save(destino)
    import datetime
    import json

    (destino.parent / (destino.stem + ".proveniencia.json")).write_text(
        json.dumps(
            {
                "metodo": "composicao_programatica",
                "por_ia": False,
                "ferramenta": "Pillow",
                "data": datetime.datetime.now(datetime.UTC).isoformat(),
                "aviso": "Ilustração fictícia, sem IA generativa",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return str(destino)
