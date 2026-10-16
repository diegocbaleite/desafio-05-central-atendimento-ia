"""Áudio, OCR, documento e peça visual local."""
from pathlib import Path
from .config import carregar, chave
from .cliente import ErroAPI
def ler_imagem(caminho):
    try:
        from PIL import Image, ImageOps, ImageEnhance
        import pytesseract
    except ImportError as e: raise RuntimeError("Instale pillow e pytesseract") from e
    imagem=Image.open(caminho).convert("L")
    imagem=ImageEnhance.Contrast(ImageOps.autocontrast(imagem)).enhance(1.5)
    return pytesseract.image_to_string(imagem,lang="por")
def transcrever(caminho, provider=None):
    import requests
    cfg=carregar(); provider=provider or cfg["multimodal"]["stt_provider"]
    if provider=="mock": raise ErroAPI("STT simulado exige transcrição fictícia explícita; não é áudio real")
    token=chave(cfg,provider)
    if not token: raise ErroAPI("Chave STT ausente")
    perfil=cfg["provedores"][provider]
    with open(caminho,"rb") as f:
        r=requests.post(perfil["base_url"].rstrip("/")+"/audio/transcriptions",
          headers={"Authorization":"Bearer "+token},
          data={"model":cfg["multimodal"]["stt_modelo"],"language":"pt"},
          files={"file":(Path(caminho).name,f)},timeout=120)
    if not r.ok: raise ErroAPI("Falha STT HTTP "+str(r.status_code))
    return r.json().get("text","")
def sintetizar(texto, destino, provider=None):
    import requests
    cfg=carregar(); provider=provider or cfg["multimodal"]["tts_provider"]
    if provider=="mock": return None
    token=chave(cfg,provider)
    if not token: raise ErroAPI("Chave TTS ausente")
    perfil=cfg["provedores"][provider]
    r=requests.post(perfil["base_url"].rstrip("/")+"/audio/speech",
      headers={"Authorization":"Bearer "+token},
      json={"model":cfg["multimodal"]["tts_modelo"],"voice":cfg["multimodal"]["tts_voz"],
            "input":texto[:4000],"response_format":"mp3"},timeout=120)
    if not r.ok: raise ErroAPI("Falha TTS HTTP "+str(r.status_code))
    Path(destino).write_bytes(r.content)
    return str(destino)
def imagem_local(destino):
    from PIL import Image, ImageDraw
    im=Image.new("RGB",(900,1200),"white"); d=ImageDraw.Draw(im)
    d.rectangle((35,35,865,1165),outline="#243c57",width=7)
    d.text((85,100),"INFORMACAO AO CIDADAO",fill="#243c57")
    d.text((85,250),"Atendimento institucional",fill="#243c57")
    d.text((85,330),"Confirme o protocolo e seus dados.",fill="#243c57")
    d.text((85,420),"Uma pessoa revisa cada minuta.",fill="#243c57")
    d.text((85,530),"Nenhuma resposta e enviada automaticamente.",fill="#243c57")
    d.rectangle((70,1010,830,1090),fill="#243c57")
    d.text((90,1035),"COMPOSICAO DIGITAL FICTICIA - SEM IA",fill="white")
    Path(destino).parent.mkdir(parents=True,exist_ok=True)
    im.save(destino)
    return str(destino)
