"""Parte 3 — evidências multimodais com entradas fictícias e revisão obrigatória.

Executar como: python -m src.guilherme_multimodal verificar|audio|ocr|voz|arte
Não envia respostas a cidadãos nem altera entradas originais.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import uuid

from .config import ROOT, carregar
from .cliente import ErroAPI

MAX_BYTES = 20 * 1024 * 1024
AUDIO = {".mp3", ".wav", ".m4a", ".ogg", ".webm"}
IMAGENS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".pdf"}


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()


def _validar(caminho: str | Path, formatos: set[str]) -> Path:
    p = Path(caminho).expanduser().resolve()
    if not p.is_file() or p.suffix.lower() not in formatos:
        raise ValueError("Arquivo ausente ou extensão não suportada")
    if not 0 < p.stat().st_size <= MAX_BYTES:
        raise ValueError("Arquivo vazio ou acima do limite de 20 MiB")
    if p.suffix.lower() == ".pdf":
        with p.open("rb") as f:
            if not f.read(5).startswith(b"%PDF-"):
                raise ValueError("Arquivo não contém assinatura PDF válida")
    if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
        from PIL import Image
        try:
            with Image.open(p) as img:
                img.verify()
        except (OSError, ValueError) as exc:
            raise ValueError("Imagem inválida ou corrompida") from exc
    return p


def _nova_saida(destino: str | Path | None, tipo: str) -> Path:
    raiz = Path(destino) if destino else ROOT / "resultados" / "guilherme"
    pasta = raiz / f"{tipo}_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}_{uuid.uuid4().hex[:6]}"
    pasta.mkdir(parents=True, exist_ok=False)
    return pasta


def _gravar_json(path: Path, valor: dict) -> None:
    path.write_text(json.dumps(valor, ensure_ascii=False, indent=2), encoding="utf-8")


def _distancia(a: list, b: list) -> int:
    """Distância de Levenshtein com memória O(min(n,m))."""
    if len(a) < len(b):
        a, b = b, a
    anterior = list(range(len(b) + 1))
    for i, item_a in enumerate(a, 1):
        atual = [i]
        for j, item_b in enumerate(b, 1):
            atual.append(min(atual[-1] + 1, anterior[j] + 1,
                             anterior[j - 1] + (item_a != item_b)))
        anterior = atual
    return anterior[-1]


def metricas(referencia: str, extraido: str) -> dict:
    """WER ignora caixa/pontuação; CER preserva caracteres de protocolos e datas."""
    def palavras(s: str) -> list[str]:
        return re.findall(r"\w+", s.casefold(), flags=re.UNICODE)
    ref_p, obs_p = palavras(referencia), palavras(extraido)
    ref_c = list(" ".join(referencia.casefold().split()))
    obs_c = list(" ".join(extraido.casefold().split()))
    w_err = _distancia(ref_p, obs_p)
    c_err = _distancia(ref_c, obs_c)
    return {
        "wer": round(w_err / len(ref_p), 4) if ref_p else None,
        "cer": round(c_err / len(ref_c), 4) if ref_c else None,
        "erros_palavras": w_err,
        "palavras_referencia": len(ref_p),
        "erros_caracteres": c_err,
        "caracteres_referencia": len(ref_c),
        "aviso": "WER/CER só são comparáveis quando o gabarito representa exatamente esta modalidade.",
    }


def _avaliacao(bruto: str, gabarito: str | Path | None, revisado: str | Path | None,
               pasta: Path) -> dict:
    resultado = {"revisao_humana": "pendente", "metricas": "não medidas"}
    if gabarito:
        referencia = Path(gabarito).read_text(encoding="utf-8")
        resultado["metricas"] = {"bruta": metricas(referencia, bruto)}
    if revisado:
        texto_revisado = Path(revisado).read_text(encoding="utf-8")
        (pasta / "texto_revisado_humano.txt").write_text(texto_revisado, encoding="utf-8")
        resultado["revisao_humana"] = "texto revisado fornecido; confirmar autoria e conferência"
        if gabarito:
            resultado["metricas"]["revisada"] = metricas(referencia, texto_revisado)
    else:
        (pasta / "PENDENTE_REVISAO.md").write_text(
            "Conferir nome, protocolo, datas, dados e trechos incertos com o ORIGINAL; "
            "registrar revisão humana separadamente. Não corrigir automaticamente.\n",
            encoding="utf-8")
    return resultado


def duracao_audio(caminho: Path) -> float | None:
    if not shutil.which("ffprobe"):
        return None
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(caminho)],
            check=True, capture_output=True, text=True, timeout=30)
        return round(float(r.stdout.strip()), 2)
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def _whisper_local(caminho: Path, modelo: str) -> str:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("STT local requer 'pip install faster-whisper' e modelo previamente obtido") from exc
    engine = WhisperModel(modelo, device="cpu", compute_type="int8")
    partes, _ = engine.transcribe(str(caminho), language="pt", vad_filter=True)
    return " ".join(p.text.strip() for p in partes).strip()


def avaliar_audio(caminho, *, provider="local", modelo_local="small", permitir_api=False,
                  gabarito=None, revisado=None, saida=None, transcritor_teste=None) -> Path:
    entrada = _validar(caminho, AUDIO)
    if provider not in {"local", "groq"} and transcritor_teste is None:
        raise ValueError("Provedor STT suportado: local ou groq")
    if provider == "groq" and not permitir_api and transcritor_teste is None:
        raise PermissionError("Envio de áudio a provedor externo exige --autorizar-api e dados fictícios")
    pasta = _nova_saida(saida, "stt")
    inicio = time.monotonic()
    if transcritor_teste is not None:
        bruto = transcritor_teste(entrada)
        origem_execucao, modelo = "simulação de teste", "mock"
    elif provider == "groq":
        from .multimodal import transcrever
        bruto = transcrever(entrada, provider="groq")
        origem_execucao, modelo = "API real (Groq)", carregar()["multimodal"]["stt_modelo"]
    else:
        bruto = _whisper_local(entrada, modelo_local)
        origem_execucao, modelo = "modelo local", modelo_local
    if not isinstance(bruto, str) or not bruto.strip():
        raise ValueError("Transcrição vazia; não será tratada como válida")
    (pasta / "transcricao_bruta.txt").write_text(bruto, encoding="utf-8")
    dados = _avaliacao(bruto, gabarito, revisado, pasta)
    duracao = duracao_audio(entrada)
    if duracao is None:
        dados["duracao_audio_nota"] = "não medida: ffprobe ausente ou falhou"
    _gravar_json(pasta / "resultado.json", {
        "tipo": "STT", "entrada": entrada.name, "sha256_original": _hash(entrada),
        "idioma": "pt", "duracao_audio_s": duracao,
        "provedor": provider, "modelo": modelo, "execucao": origem_execucao,
        "duracao_processamento_s": round(time.monotonic() - inicio, 3),
        "data_utc": datetime.now(timezone.utc).isoformat(),
        "arquivo_bruto": "transcricao_bruta.txt", "requer_revisao_humana": True,
        **dados,
    })
    return pasta


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
        raise RuntimeError("Nenhuma página do PDF pôde ser convertida")
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
    for palavra, confiança in zip(dados.get("text", []), dados.get("conf", [])):
        if not palavra.strip():
            continue
        try:
            conf = float(confiança)
        except (TypeError, ValueError):
            continue
        if 0 <= conf < 55 and len(incertos) < 30:
            incertos.append({"fragmento": palavra, "confianca_ocr": round(conf, 1)})
    return texto, incertos


def avaliar_ocr(caminho, *, idioma="por", psm=6, limite_paginas=3,
                gabarito=None, revisado=None, saida=None, motor_teste=None) -> Path:
    entrada = _validar(caminho, IMAGENS)
    if not 1 <= limite_paginas <= 10:
        raise ValueError("O limite de páginas deve estar entre 1 e 10")
    if psm not in range(3, 14):
        raise ValueError("PSM do Tesseract inválido")
    inicio = time.monotonic()
    pasta = _nova_saida(saida, "ocr")
    trechos, paginas, texto_para_metrica = [], [], []
    with tempfile.TemporaryDirectory(prefix="guilherme_ocr_") as temporaria:
        temp = Path(temporaria)
        imagens = (_imagens_pdf(entrada, temp, limite_paginas)
                   if entrada.suffix.lower() == ".pdf" else [entrada])
        for n, imagem in enumerate(imagens, 1):
            if motor_teste:
                texto, incertos = motor_teste(imagem, idioma, psm)
            else:
                texto, incertos = _ocr_imagem(imagem, idioma, psm)
            trechos.append(f"[Página {n}]\n{texto.strip()}")
            texto_para_metrica.append(texto.strip())
            paginas.append({"pagina": n, "trechos_incertos": incertos})
    bruto = "\n\n".join(trechos)
    (pasta / "ocr_bruto.txt").write_text(bruto, encoding="utf-8")
    avaliacao = _avaliacao("\n\n".join(texto_para_metrica), gabarito, revisado, pasta)
    _gravar_json(pasta / "resultado.json", {
        "tipo": "OCR", "entrada": entrada.name, "sha256_original": _hash(entrada),
        "idioma": idioma, "motor": "Tesseract" if motor_teste is None else "mock",
        "configuracao": {"psm": psm, "limite_paginas": limite_paginas},
        "paginas": paginas, "duracao_processamento_s": round(time.monotonic()-inicio, 3),
        "data_utc": datetime.now(timezone.utc).isoformat(),
        "arquivo_bruto": "ocr_bruto.txt", "requer_revisao_humana": True,
        **avaliacao,
    })
    return pasta


def gerar_voz(minuta, revisao, *, saida=None, provider="espeak", permitir_api=False,
              sintetizador_teste=None) -> Path:
    """Só sintetiza com aprovação humana DOCUMENTADA, não uma decisão mock/YAML."""
    origem = Path(minuta).resolve()
    texto = origem.read_text(encoding="utf-8")
    parecer = json.loads(Path(revisao).read_text(encoding="utf-8"))
    if (parecer.get("decisao") != "aprovar" or parecer.get("simulada") is not False
        or parecer.get("origem") != "revisao_humana"
        or not parecer.get("revisor") or not parecer.get("data_revisao")
        or parecer.get("sha256_minuta") != _hash(origem)):
        raise PermissionError("TTS bloqueado: aprovação humana válida e hash da minuta são obrigatórios")
    if provider != "espeak" and not permitir_api and sintetizador_teste is None:
        raise PermissionError("TTS remoto exige --autorizar-api")
    pasta = _nova_saida(saida, "tts")
    aviso = ("Atenção: esta minuta contém informações não localizadas, "
             "que exigem verificação humana. " if "não localizado" in texto.casefold() else "")
    locucao = aviso + re.sub(r"[#*_`]+", " ", texto)
    (pasta / "roteiro_falado.txt").write_text(locucao, encoding="utf-8")
    destino = pasta / ("voz.mp3" if provider != "espeak" else "voz.wav")
    if sintetizador_teste:
        arquivo_audio = sintetizador_teste(locucao, destino)
        origem_audio = "mock"
    else:
        from .multimodal import sintetizar
        arquivo_audio = sintetizar(locucao, destino, provider=provider)
        origem_audio = "local" if provider == "espeak" else "API"
    if not arquivo_audio or not Path(arquivo_audio).exists():
        raise RuntimeError("Síntese de voz não gerou arquivo verificável")
    _gravar_json(pasta / "resultado.json", {
        "tipo": "TTS", "modelo_ou_motor": provider, "execucao": origem_audio,
        "minuta_sha256": _hash(origem), "aviso_ausencias_incluido": bool(aviso),
        "arquivo_audio": Path(arquivo_audio).name, "hash_audio": _hash(Path(arquivo_audio)),
        "duracao_audio_s": duracao_audio(Path(arquivo_audio)),
        "observacao": "Aprovação registrada em arquivo; conferir identidade e decisão do revisor.",
        "data_utc": datetime.now(timezone.utc).isoformat(),
    })
    return pasta


def gerar_visual(*, saida=None, referencia=None, permitir_api=False, gerador_teste=None) -> Path:
    from .arte_ia import gerar
    cfg = carregar()
    p = cfg["multimodal"]["imagem_provider"]
    if p != "local" and not permitir_api and gerador_teste is None:
        raise PermissionError("Imagem gerada por API exige --autorizar-api")
    pasta = _nova_saida(saida, "arte")
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
        "tipo": "PECA_VISUAL", "arquivo": img.name, "sha256": _hash(img),
        "por_ia": dados["por_ia"], "metodo": dados.get("metodo"),
        "modelo": dados.get("modelo", "não localizado"),
        "revisao_humana": "pendente", "uso_oficial": False,
        "aviso": "Material de demonstração; não constitui comunicação oficial.",
        "data_utc": datetime.now(timezone.utc).isoformat(),
    }
    if referencia:
        origem = _validar(referencia, IMAGENS)
        info["referencia_visual"] = {"arquivo": origem.name, "sha256": _hash(origem),
                                    "incorporada_na_arte": False}
    _gravar_json(pasta / "revisao_visual.json", info)
    return pasta


def main(argv=None):
    parser = argparse.ArgumentParser(description="Parte 3 — Guilherme: STT, OCR, TTS, arte (sem envio automático)")
    sub = parser.add_subparsers(dest="comando", required=True)
    sub.add_parser("verificar")
    pa = sub.add_parser("audio")
    pa.add_argument("entrada"); pa.add_argument("--provider", choices=["local", "groq"], default="local")
    pa.add_argument("--modelo-local", default="small")
    pa.add_argument("--autorizar-api", action="store_true")
    pa.add_argument("--gabarito"); pa.add_argument("--revisado")
    po = sub.add_parser("ocr")
    po.add_argument("entrada"); po.add_argument("--gabarito"); po.add_argument("--revisado")
    po.add_argument("--psm", type=int, default=6)
    pt = sub.add_parser("voz")
    pt.add_argument("minuta"); pt.add_argument("--revisao", required=True)
    pt.add_argument("--provider", default="espeak"); pt.add_argument("--autorizar-api", action="store_true")
    pi = sub.add_parser("arte")
    pi.add_argument("--referencia"); pi.add_argument("--autorizar-api", action="store_true")
    opts = parser.parse_args(argv)
    try:
        if opts.comando == "verificar":
            print(json.dumps({"tesseract": bool(shutil.which("tesseract")),
                              "pdftoppm": bool(shutil.which("pdftoppm")),
                              "ffprobe": bool(shutil.which("ffprobe")),
                              "espeak": bool(shutil.which("espeak")),
                              "envio_automatico": False}, ensure_ascii=False, indent=2))
            return
        if opts.comando == "audio":
            pasta = avaliar_audio(opts.entrada, provider=opts.provider, modelo_local=opts.modelo_local,
                                 permitir_api=opts.autorizar_api, gabarito=opts.gabarito,
                                 revisado=opts.revisado)
        elif opts.comando == "ocr":
            pasta = avaliar_ocr(opts.entrada, gabarito=opts.gabarito, revisado=opts.revisado, psm=opts.psm)
        elif opts.comando == "voz":
            pasta = gerar_voz(opts.minuta, opts.revisao, provider=opts.provider,
                             permitir_api=opts.autorizar_api)
        else:
            pasta = gerar_visual(referencia=opts.referencia, permitir_api=opts.autorizar_api)
        print("Evidências locais:", pasta)
        print("Nenhum envio externo de respostas foi realizado.")
    except (ValueError, RuntimeError, PermissionError, OSError, ErroAPI) as exc:
        parser.exit(status=2, message=f"Falha: {type(exc).__name__}: {exc}\n")


if __name__ == "__main__":
    main()
