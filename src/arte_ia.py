"""RF10 — geração real (quando autorizada e com cota); nunca confundir com arte local."""
from __future__ import annotations
import base64
import datetime as dt
import json
from pathlib import Path
import requests
from .config import ROOT,carregar,chave
from .cliente import ErroAPI
from .multimodal import imagem_local

def gerar(destino=None):
    cfg=carregar()
    caminho=Path(destino or ROOT/"resultados"/"peca_visual.png")
    if cfg["multimodal"]["imagem_provider"]=="local": return imagem_local(caminho)
    if cfg["multimodal"]["imagem_provider"]!="openai": raise ErroAPI("Provedor de imagem inválido")
    token=chave(cfg,"openai")
    if not token: raise ErroAPI("OPENAI_API_KEY ausente para geração real da imagem")
    prompt=(ROOT/"prompts"/"imagem_orientacao.md").read_text(encoding="utf-8")
    modelo=cfg["multimodal"]["imagem_modelo"]
    try:
        r=requests.post("https://api.openai.com/v1/images/generations",
          headers={"Authorization":"Bearer "+token},
          json={"model":modelo,"prompt":prompt,"size":"1024x1536","quality":"medium"},timeout=180)
    except requests.RequestException as e: raise ErroAPI("Falha de conexão com gerador de imagens: "+type(e).__name__) from e
    if not r.ok: raise ErroAPI("Geração de imagens indisponível: HTTP "+str(r.status_code))
    try: img=base64.b64decode(r.json()["data"][0]["b64_json"],validate=True)
    except (ValueError,KeyError,IndexError,TypeError) as e: raise ErroAPI("Imagem retornada em formato inesperado") from e
    if not img.startswith(b"\x89PNG"): raise ErroAPI("Gerador não retornou arquivo PNG esperado")
    # Inserir selo mesmo que o modelo o tenha omitido; nunca dizer que a imagem é oficial.
    from PIL import Image,ImageDraw,ImageFont
    import io
    im=Image.open(io.BytesIO(img)).convert("RGB")
    d=ImageDraw.Draw(im);w,h=im.size
    d.rectangle((0,h-115,w,h),fill="#122d47")
    for fonte in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",):
        if Path(fonte).exists(): break
    else: fonte=None
    f=ImageFont.truetype(fonte,27) if fonte else ImageFont.load_default()
    d.text((25,h-85),"Imagem gerada por IA — ilustração fictícia",font=f,fill="white")
    caminho.parent.mkdir(parents=True,exist_ok=True);im.save(caminho)
    nota={"metodo":"geracao_api","por_ia":True,"provider":"openai","modelo":modelo,
        "data":dt.datetime.now(dt.timezone.utc).isoformat(),"prompt":"prompts/imagem_orientacao.md",
        "arquivo":str(caminho),"status_revisao":"pendente de validação humana"}
    (caminho.parent/(caminho.stem+".proveniencia.json")).write_text(
        json.dumps(nota,ensure_ascii=False,indent=2),encoding="utf-8")
    return str(caminho)
