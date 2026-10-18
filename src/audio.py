"""Áudio: STT (Whisper local ou API), TTS e versão falada da minuta aprovada.

Nada aqui envia respostas a cidadãos; áudio de entrada só vai a provedor externo
com autorização explícita e a locução só é gerada para minuta aprovada por pessoa.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from .auditoria import gravar_json, nova_saida, sha256_arquivo
from .avaliacao import avaliar_texto_extraido
from .cliente import ErroAPI
from .config import carregar, chave
from .seguranca import FORMATOS_AUDIO, validar_arquivo


def _whisper_local(caminho: Path, modelo: str) -> str:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "STT local requer 'pip install faster-whisper' e modelo previamente obtido"
        ) from exc
    engine = WhisperModel(modelo, device="cpu", compute_type="int8")
    partes, _ = engine.transcribe(str(caminho), language="pt", vad_filter=True)
    return " ".join(p.text.strip() for p in partes).strip()


def transcrever(caminho, provider=None, *, modelo_local="small", permitir_api=False):
    """Transcreve áudio. Provedor externo exige permitir_api=True (áudio é dado pessoal)."""
    entrada = validar_arquivo(caminho, FORMATOS_AUDIO, 20)
    cfg = carregar()
    provider = provider or cfg["multimodal"]["stt_provider"]
    if provider == "mock":
        raise ErroAPI(
            "STT fictício não transcreve áudio; use referência explicitamente rotulada"
        )
    if provider == "local":
        return _whisper_local(entrada, modelo_local)
    if not permitir_api:
        raise PermissionError(
            "Envio de áudio a provedor externo exige --autorizar-api e dados fictícios"
        )
    token = chave(cfg, provider)
    if not token:
        raise ErroAPI("Falta chave de STT; configure .env ou use --mock")
    perfil = cfg["provedores"].get(provider)
    if not perfil:
        raise ErroAPI("Provedor STT não cadastrado")
    with entrada.open("rb") as f:
        try:
            r = requests.post(
                perfil["base_url"].rstrip("/") + "/audio/transcriptions",
                headers={"Authorization": "Bearer " + token},
                data={"model": cfg["multimodal"]["stt_modelo"], "language": "pt"},
                files={"file": (entrada.name, f)},
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
    cfg = carregar()
    provider = provider or cfg["multimodal"]["tts_provider"]
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    # Áudio só é chamado após aprovação pela camada de revisão.
    if provider == "mock":
        return None
    if len(texto) > 3500:
        raise ErroAPI(
            "Texto excede o limite de 3500 caracteres para TTS; áudio não foi gerado"
        )
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
                texto.replace("#", " ").replace("*", " "),
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
                "input": texto,
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


def avaliar_audio(caminho, *, provider="local", modelo_local="small", permitir_api=False,
                  gabarito=None, revisado=None, saida=None, transcritor_teste=None) -> Path:
    """STT com transcrição bruta preservada, métricas contra referência e revisão pendente."""
    entrada = validar_arquivo(caminho, FORMATOS_AUDIO, 20)
    if provider not in {"local", "groq"} and transcritor_teste is None:
        raise ValueError("Provedor STT suportado: local ou groq")
    inicio = time.monotonic()
    if transcritor_teste is not None:
        bruto = transcritor_teste(entrada)
        origem_execucao, modelo = "simulação de teste", "mock"
    else:
        bruto = transcrever(entrada, provider, modelo_local=modelo_local,
                            permitir_api=permitir_api)
        if provider == "groq":
            origem_execucao, modelo = "API real (Groq)", carregar()["multimodal"]["stt_modelo"]
        else:
            origem_execucao, modelo = "modelo local", modelo_local
    if not isinstance(bruto, str) or not bruto.strip():
        raise ValueError("Transcrição vazia; não será tratada como válida")
    pasta = nova_saida(saida, "stt")
    (pasta / "transcricao_bruta.txt").write_text(bruto, encoding="utf-8")
    dados = avaliar_texto_extraido(bruto, gabarito, revisado, pasta)
    duracao = duracao_audio(entrada)
    if duracao is None:
        dados["duracao_audio_nota"] = "não medida: ffprobe ausente ou falhou"
    gravar_json(pasta / "resultado.json", {
        "tipo": "STT", "entrada": entrada.name, "sha256_original": sha256_arquivo(entrada),
        "idioma": "pt", "duracao_audio_s": duracao,
        "provedor": provider, "modelo": modelo, "execucao": origem_execucao,
        "duracao_processamento_s": round(time.monotonic() - inicio, 3),
        "data_utc": datetime.now(timezone.utc).isoformat(),
        "arquivo_bruto": "transcricao_bruta.txt", "requer_revisao_humana": True,
        **dados,
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
        or parecer.get("sha256_minuta") != sha256_arquivo(origem)):
        raise PermissionError("TTS bloqueado: aprovação humana válida e hash da minuta são obrigatórios")
    if provider != "espeak" and not permitir_api and sintetizador_teste is None:
        raise PermissionError("TTS remoto exige --autorizar-api")
    pasta = nova_saida(saida, "tts")
    aviso = ("Atenção: esta minuta contém informações não localizadas, "
             "que exigem verificação humana. " if "não localizado" in texto.casefold() else "")
    locucao = aviso + re.sub(r"[#*_`]+", " ", texto)
    (pasta / "roteiro_falado.txt").write_text(locucao, encoding="utf-8")
    destino = pasta / ("voz.mp3" if provider != "espeak" else "voz.wav")
    if sintetizador_teste:
        arquivo_audio = sintetizador_teste(locucao, destino)
        origem_audio = "mock"
    else:
        arquivo_audio = sintetizar(locucao, destino, provider=provider)
        origem_audio = "local" if provider == "espeak" else "API"
    if not arquivo_audio or not Path(arquivo_audio).exists():
        raise RuntimeError("Síntese de voz não gerou arquivo verificável")
    gravar_json(pasta / "resultado.json", {
        "tipo": "TTS", "modelo_ou_motor": provider, "execucao": origem_audio,
        "minuta_sha256": sha256_arquivo(origem), "aviso_ausencias_incluido": bool(aviso),
        "arquivo_audio": Path(arquivo_audio).name, "hash_audio": sha256_arquivo(Path(arquivo_audio)),
        "duracao_audio_s": duracao_audio(Path(arquivo_audio)),
        "observacao": "Aprovação registrada em arquivo; conferir identidade e decisão do revisor.",
        "data_utc": datetime.now(timezone.utc).isoformat(),
    })
    return pasta
