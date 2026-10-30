"""Peça visual (RF10): composição local identificada como não-IA ou geração por API com proveniência.

Composição Pillow nunca é apresentada como imagem gerada por IA; toda peça nasce com
nota de proveniência e revisão humana pendente.
"""

from __future__ import annotations

import base64
import datetime as dt
import hashlib
import io
import json
import os
import time
from pathlib import Path

import requests

from .auditoria import gravar_json, nova_saida, sha256_arquivo
from .cliente import ErroAPI
from .config import ROOT, carregar, chave
from .seguranca import FORMATOS_IMAGEM, validar_arquivo

LIMITE_PROMPT_CLOUDFLARE = 2048
FONTE_DEJAVU = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTES_LOCAIS = (
    FONTE_DEJAVU,
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
)


def _post_com_retentativas(url: str, **kwargs):
    ultimo_erro = "não localizado"
    for tentativa in range(3):
        try:
            resposta = requests.post(url, **kwargs)
        except (requests.Timeout, requests.ConnectionError) as exc:
            ultimo_erro = type(exc).__name__
            espera = min(20, 2**tentativa)
        else:
            if resposta.ok:
                return resposta
            if resposta.status_code != 429 and resposta.status_code < 500:
                return resposta
            ultimo_erro = f"HTTP {resposta.status_code}"
            try:
                espera = min(
                    20,
                    max(0, float(resposta.headers.get("Retry-After", 2**tentativa))),
                )
            except (AttributeError, TypeError, ValueError):
                espera = min(20, 2**tentativa)
        if tentativa < 2:
            time.sleep(espera)
    raise ErroAPI(
        "Gerador de imagens temporariamente indisponível após 3 tentativas: "
        + ultimo_erro
    )


def _fonte(tamanho):
    from PIL import ImageFont

    for caminho in FONTES_LOCAIS:
        if Path(caminho).exists():
            return ImageFont.truetype(caminho, tamanho)
    return ImageFont.load_default()


def _incorporar_referencia(imagem, referencia):
    """Insere uma cópia redimensionada da referência, preservando o original."""
    from PIL import Image

    origem = validar_arquivo(referencia, FORMATOS_IMAGEM, 20)
    with Image.open(origem) as arquivo:
        brasao = arquivo.convert("RGBA")
    limite = (
        max(1, int(imagem.width * 0.28)),
        max(1, int(imagem.height * 0.24)),
    )
    brasao.thumbnail(limite, Image.Resampling.LANCZOS)
    posicao = ((imagem.width - brasao.width) // 2, max(10, int(imagem.height * 0.04)))
    imagem.paste(brasao, posicao, brasao)
    return origem


def _dados_referencia(origem):
    if origem is None:
        return None
    return {
        "arquivo": origem.name,
        "sha256": sha256_arquivo(origem),
        "incorporada_na_arte": True,
    }


def imagem_local(destino, referencia=None):
    """Arte por PILLOW = COMPOSIÇÃO PROGRAMÁTICA, não IA generativa."""
    from PIL import Image, ImageDraw

    im = Image.new("RGB", (960, 1440), "white")
    d = ImageDraw.Draw(im)
    d.rectangle((55, 55, 905, 1360), outline="#214562", width=9)
    origem = _incorporar_referencia(im, referencia) if referencia else None
    deslocamento = 300 if origem else 0
    d.text(
        (90, 110 + deslocamento),
        "ATENDIMENTO AO CIDADÃO",
        font=_fonte(37),
        fill="#214562",
    )
    d.text((90, 290 + deslocamento), "• Documentos e protocolos", font=_fonte(28), fill="#214562")
    d.text((90, 385 + deslocamento), "• Conferência de informações", font=_fonte(28), fill="#214562")
    d.text((90, 480 + deslocamento), "• Revisão por servidor", font=_fonte(28), fill="#214562")
    d.text((90, 820), "Nenhuma resposta é enviada", font=_fonte(28), fill="#214562")
    d.text((90, 868), "automaticamente.", font=_fonte(28), fill="#214562")
    d.rectangle((80, 1170, 880, 1320), fill="#214562")
    d.text((100, 1195), "COMPOSIÇÃO DIGITAL FICTÍCIA", font=_fonte(26), fill="white")
    d.text((100, 1250), "PROGRAMÁTICA — SEM IA", font=_fonte(25), fill="white")
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    im.save(destino)
    proveniencia = {
        "metodo": "composicao_programatica",
        "por_ia": False,
        "ferramenta": "Pillow",
        "data": dt.datetime.now(dt.UTC).isoformat(),
        "aviso": "Ilustração fictícia, sem IA generativa",
    }
    if origem:
        proveniencia["referencia_visual"] = _dados_referencia(origem)
    gravar_json(destino.parent / (destino.stem + ".proveniencia.json"), proveniencia)
    return str(destino)


def gerar(destino=None, *, provider=None, referencia=None):
    """Gera arte local ou usa explicitamente um provedor de imagem configurado."""
    cfg = carregar()
    provider = provider or cfg["multimodal"]["imagem_provider"]
    caminho = Path(destino or ROOT / "resultados" / "peca_visual.png")
    if provider == "local":
        return imagem_local(caminho, referencia=referencia)
    if provider not in {"cloudflare", "openai"}:
        raise ErroAPI("Provedor de imagem inválido")
    item = cfg["provedores"][provider]
    token = chave(cfg, provider)
    conta = os.getenv(item.get("env_conta", ""), "")
    if not token or (provider == "cloudflare" and not conta):
        raise ErroAPI(
            "OPENAI_API_KEY é necessária para geração real da imagem" if provider == "openai"
            else "CLOUDFLARE_API_KEY e CLOUDFLARE_ACCOUNT_ID são necessários para geração real da imagem"
        )
    prompt = (ROOT / "prompts" / "imagem_orientacao.md").read_text(encoding="utf-8")
    if provider == "cloudflare" and len(prompt) > LIMITE_PROMPT_CLOUDFLARE:
        raise ErroAPI("Prompt de imagem excede o limite do modelo (2048 caracteres)")
    modelo = cfg["multimodal"]["imagem_modelo"]
    parametros = {"prompt": prompt, "steps": 4}
    url = f"{item['base_url'].rstrip('/')}/accounts/{conta}/ai/run/{modelo}"
    if provider == "openai":
        url = item["base_url"].rstrip("/") + "/images/generations"
        parametros = {
            "model": modelo, "prompt": prompt, "n": 1,
            "size": cfg["multimodal"].get("imagem_tamanho", "1024x1536"),
            "quality": cfg["multimodal"].get("imagem_qualidade", "low"),
        }
    try:
        r = _post_com_retentativas(
            url,
            headers={"Authorization": "Bearer " + token},
            json=parametros,
            timeout=180,
        )
    except requests.RequestException as e:
        raise ErroAPI(
            "Falha de conexão com gerador de imagens: " + type(e).__name__
        ) from e
    if not r.ok:
        raise ErroAPI("Geração de imagens indisponível: HTTP " + str(r.status_code))
    try:
        dados_api = r.json()
    except ValueError as e:
        raise ErroAPI("Gerador retornou JSON inválido") from e
    if not isinstance(dados_api, dict):
        raise ErroAPI("Gerador retornou formato inesperado")
    if provider == "openai":
        try:
            codificado = dados_api["data"][0]["b64_json"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ErroAPI("Gerador não retornou imagem base64") from exc
    else:
        resultado = dados_api.get("result", dados_api)
        if not isinstance(resultado, dict):
            raise ErroAPI("Gerador não retornou imagem")
        codificado = resultado.get("image")
    if not isinstance(codificado, str) or not codificado:
        raise ErroAPI("Gerador retornou imagem sem dados")
    try:
        img = base64.b64decode(codificado, validate=True)
    except (ValueError, TypeError) as e:
        raise ErroAPI("Imagem retornada em formato inesperado") from e
    from PIL import Image, ImageDraw

    try:
        with Image.open(io.BytesIO(img)) as original:
            im = original.convert("RGB")
    except (OSError, ValueError) as e:
        raise ErroAPI("Gerador retornou dados que não são uma imagem válida") from e
    origem = _incorporar_referencia(im, referencia) if referencia else None
    d = ImageDraw.Draw(im)
    w, h = im.size
    d.rectangle((0, h - 115, w, h), fill="#122d47")
    f = _fonte(27)
    d.text(
        (25, h - 85), "Imagem gerada por IA — ilustração fictícia", font=f, fill="white"
    )
    caminho.parent.mkdir(parents=True, exist_ok=True)
    im.save(caminho)
    uso = dados_api.get("usage") or {}
    if not isinstance(uso, dict):
        uso = {}
    proveniencia = {
            "metodo": "geracao_api",
            "por_ia": True,
            "provider": provider,
            "modelo": modelo,
            "data": dt.datetime.now(dt.UTC).isoformat(),
            "prompt": "prompts/imagem_orientacao.md",
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "parametros": {k: v for k, v in parametros.items() if k not in {"model", "prompt"}},
            "tokens_entrada": uso.get("input_tokens", "não localizado"),
            "tokens_saida": uso.get("output_tokens", "não localizado"),
            "custo_usd": "não localizado",
            "arquivo": str(caminho),
            "operador": "não localizado",
            "status_revisao": "pendente de validação humana",
        }
    if origem:
        proveniencia["referencia_visual"] = _dados_referencia(origem)
    gravar_json(caminho.parent / (caminho.stem + ".proveniencia.json"), proveniencia)
    return str(caminho)


def gerar_visual(*, saida=None, referencia=None, gerador_teste=None, provider=None) -> Path:
    """Gera a peça com revisão visual pendente usando o provedor configurado."""
    pasta = nova_saida(saida, "arte")
    caminho = pasta / "orientacao.png"
    try:
        if gerador_teste:
            produzido = gerador_teste(caminho)
        elif referencia:
            produzido = gerar(caminho, provider=provider, referencia=referencia)
        else:
            produzido = gerar(caminho, provider=provider)
    except ErroAPI:
        if not any(pasta.iterdir()):
            pasta.rmdir()
        raise
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
        "provider": dados.get("provider", "não localizado"),
        "modelo": dados.get("modelo", "não localizado"),
        "custo_usd": dados.get("custo_usd", "não localizado"),
        "tokens_entrada": dados.get("tokens_entrada", "não localizado"),
        "tokens_saida": dados.get("tokens_saida", "não localizado"),
        "revisao_humana": "pendente", "uso_oficial": False,
        "aviso": "Material de demonstração; não constitui comunicação oficial.",
        "data_utc": dt.datetime.now(dt.UTC).isoformat(),
    }
    if dados.get("referencia_visual"):
        info["referencia_visual"] = dados["referencia_visual"]
    gravar_json(pasta / "revisao_visual.json", info)
    return pasta
