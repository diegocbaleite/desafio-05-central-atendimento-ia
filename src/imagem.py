"""Peça visual (RF10): composição local identificada como não-IA ou geração por API com proveniência.

Composição Pillow nunca é apresentada como imagem gerada por IA; toda peça nasce com
nota de proveniência e revisão humana pendente.
"""

from __future__ import annotations

import base64
import datetime as dt
import io
import json
from pathlib import Path

import requests

from .auditoria import gravar_json, nova_saida, sha256_arquivo
from .cliente import ErroAPI
from .config import ROOT, carregar, chave
from .seguranca import FORMATOS_IMAGEM, validar_arquivo

FONTE_DEJAVU = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTES_LOCAIS = (FONTE_DEJAVU, "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf")


def imagem_local(destino):
    """Arte por PILLOW = COMPOSIÇÃO PROGRAMÁTICA, não IA generativa."""
    from PIL import Image, ImageDraw, ImageFont

    def fonte(n):
        for p in FONTES_LOCAIS:
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
    gravar_json(
        destino.parent / (destino.stem + ".proveniencia.json"),
        {
            "metodo": "composicao_programatica",
            "por_ia": False,
            "ferramenta": "Pillow",
            "data": dt.datetime.now(dt.UTC).isoformat(),
            "aviso": "Ilustração fictícia, sem IA generativa",
        },
    )
    return str(destino)


def gerar(destino=None):
    """Imagem conforme multimodal.imagem_provider: local (Pillow) ou geração real via OpenAI."""
    cfg = carregar()
    caminho = Path(destino or ROOT / "resultados" / "peca_visual.png")
    if cfg["multimodal"]["imagem_provider"] == "local":
        return imagem_local(caminho)
    if cfg["multimodal"]["imagem_provider"] != "openai":
        raise ErroAPI("Provedor de imagem inválido")
    token = chave(cfg, "openai")
    if not token:
        raise ErroAPI("OPENAI_API_KEY ausente para geração real da imagem")
    prompt = (ROOT / "prompts" / "imagem_orientacao.md").read_text(encoding="utf-8")
    modelo = cfg["multimodal"]["imagem_modelo"]
    try:
        r = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers={"Authorization": "Bearer " + token},
            json={
                "model": modelo,
                "prompt": prompt,
                "size": "1024x1536",
                "quality": "medium",
            },
            timeout=180,
        )
    except requests.RequestException as e:
        raise ErroAPI(
            "Falha de conexão com gerador de imagens: " + type(e).__name__
        ) from e
    if not r.ok:
        raise ErroAPI("Geração de imagens indisponível: HTTP " + str(r.status_code))
    try:
        img = base64.b64decode(r.json()["data"][0]["b64_json"], validate=True)
    except (ValueError, KeyError, IndexError, TypeError) as e:
        raise ErroAPI("Imagem retornada em formato inesperado") from e
    if not img.startswith(b"\x89PNG"):
        raise ErroAPI("Gerador não retornou arquivo PNG esperado")
    # Inserir selo mesmo que o modelo o tenha omitido; nunca dizer que a imagem é oficial.
    from PIL import Image, ImageDraw, ImageFont

    im = Image.open(io.BytesIO(img)).convert("RGB")
    d = ImageDraw.Draw(im)
    w, h = im.size
    d.rectangle((0, h - 115, w, h), fill="#122d47")
    f = (
        ImageFont.truetype(FONTE_DEJAVU, 27)
        if Path(FONTE_DEJAVU).exists()
        else ImageFont.load_default()
    )
    d.text(
        (25, h - 85), "Imagem gerada por IA — ilustração fictícia", font=f, fill="white"
    )
    caminho.parent.mkdir(parents=True, exist_ok=True)
    im.save(caminho)
    gravar_json(
        caminho.parent / (caminho.stem + ".proveniencia.json"),
        {
            "metodo": "geracao_api",
            "por_ia": True,
            "provider": "openai",
            "modelo": modelo,
            "data": dt.datetime.now(dt.UTC).isoformat(),
            "prompt": "prompts/imagem_orientacao.md",
            "arquivo": str(caminho),
            "status_revisao": "pendente de validação humana",
        },
    )
    return str(caminho)


def gerar_visual(*, saida=None, referencia=None, gerador_teste=None) -> Path:
    """Gera a peça com revisão visual pendente usando o provedor configurado."""
    cfg = carregar()
    p = cfg["multimodal"]["imagem_provider"]
    pasta = nova_saida(saida, "arte")
    caminho = pasta / "orientacao.png"
    produzido = gerador_teste(caminho) if gerador_teste else gerar(caminho)
    img = Path(produzido)
    nota = img.with_name(img.stem + ".proveniencia.json")
    if not img.exists() or not nota.exists():
        raise RuntimeError("Imagem ou nota de proveniência não foi criada")
    dados = json.loads(nota.read_text(encoding="utf-8"))
    if not isinstance(dados.get("por_ia"), bool):
        raise RuntimeError("Proveniência da arte não especifica se houve IA")
    info = {
        "tipo": "PECA_VISUAL", "arquivo": img.name, "sha256": sha256_arquivo(img),
        "por_ia": dados["por_ia"], "metodo": dados.get("metodo"),
        "modelo": dados.get("modelo", "não localizado"),
        "revisao_humana": "pendente", "uso_oficial": False,
        "aviso": "Material de demonstração; não constitui comunicação oficial.",
        "data_utc": dt.datetime.now(dt.UTC).isoformat(),
    }
    if referencia:
        origem = validar_arquivo(referencia, FORMATOS_IMAGEM, 20)
        info["referencia_visual"] = {"arquivo": origem.name, "sha256": sha256_arquivo(origem),
                                    "incorporada_na_arte": False}
    gravar_json(pasta / "revisao_visual.json", info)
    return pasta
