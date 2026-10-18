"""Áudio: STT (Whisper local ou API), TTS e versão falada da minuta aprovada.

Nada aqui envia respostas a cidadãos; provedores remotos seguem a configuração,
e a locução só é gerada para minuta aprovada por pessoa.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
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


def _parametros_tts(cfg):
    multimodal = cfg.get("multimodal", {})
    return {
        "voz_remota": multimodal.get("tts_voz", "coral"),
        "voz_local": multimodal.get("tts_voz_local", "pt-br"),
        "velocidade": int(multimodal.get("tts_velocidade", 145)),
        "tom": int(multimodal.get("tts_tom", 45)),
        "volume": int(multimodal.get("tts_volume", 100)),
        "pausa_palavras_ms": int(multimodal.get("tts_pausa_palavras_ms", 5)),
        "instrucoes": multimodal.get(
            "tts_instrucoes",
            "Fale em português brasileiro, com tom institucional e ritmo moderado.",
        ),
    }


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


def _sintetizar_gemini(texto: str, destino: Path, cfg, token: str, perfil, parametros) -> str:
    """Usa o esquema nativo Gemini 3.8 TTS e preserva o WAV retornado."""
    base_url = perfil.get("base_url_nativa") or perfil["base_url"]
    base_url = base_url.rstrip("/")
    if base_url.endswith("/openai"):
        base_url = base_url[:-len("/openai")]
    payload = {
        "model": cfg["multimodal"]["tts_modelo"],
        "input": [{
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": texto,
                "annotations": [{
                    "type": "speech_metadata",
                    "style": parametros["instrucoes"],
                }],
            }],
        }],
        "response_format": {"type": "audio", "mime_type": "audio/wav"},
        "generation_config": {
            "speech_config": [{"voice": parametros["voz_remota"]}],
        },
    }
    try:
        resposta = requests.post(
            base_url + "/interactions",
            headers={"x-goog-api-key": token, "Content-Type": "application/json"},
            json=payload,
            timeout=120,
        )
    except requests.RequestException as exc:
        raise ErroAPI("Falha TTS Gemini: " + type(exc).__name__) from exc
    if not resposta.ok:
        raise ErroAPI("TTS Gemini indisponível HTTP " + str(resposta.status_code))
    try:
        dados = resposta.json()
        audios = [
            item["data"]
            for etapa in dados["steps"]
            if etapa.get("type") == "model_output"
            for item in etapa.get("content", [])
            if item.get("type") == "audio" and item.get("data")
        ]
        wav_bytes = base64.b64decode(audios[-1], validate=True)
    except (ValueError, KeyError, IndexError, TypeError, binascii.Error) as exc:
        raise ErroAPI("TTS Gemini retornou áudio inválido") from exc
    if not (wav_bytes.startswith(b"RIFF") and wav_bytes[8:12] == b"WAVE"):
        raise ErroAPI("TTS Gemini não retornou o WAV solicitado")

    wav = destino.with_suffix(".wav")
    wav.write_bytes(wav_bytes)
    return str(wav)


def transcrever(caminho, provider=None, *, modelo_local="small"):
    """Transcreve áudio com o provedor selecionado ou configurado."""
    entrada = validar_arquivo(caminho, FORMATOS_AUDIO, 20)
    cfg = carregar()
    provider = provider or cfg["multimodal"]["stt_provider"]
    if provider == "mock":
        raise ErroAPI(
            "STT fictício não transcreve áudio; use referência explicitamente rotulada"
        )
    if provider == "local":
        return _whisper_local(entrada, modelo_local)
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
    parametros = _parametros_tts(cfg)
    if provider == "espeak":
        if not shutil.which("espeak"):
            raise ErroAPI("Instale espeak para TTS offline")
        destino = destino.with_suffix(".wav")
        subprocess.run(
            [
                "espeak",
                "-v",
                parametros["voz_local"],
                "-s",
                str(parametros["velocidade"]),
                "-p",
                str(parametros["tom"]),
                "-a",
                str(parametros["volume"]),
                "-g",
                str(parametros["pausa_palavras_ms"]),
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
    if provider == "gemini":
        return _sintetizar_gemini(texto, destino, cfg, token, perfil, parametros)
    try:
        r = requests.post(
            perfil["base_url"].rstrip("/") + "/audio/speech",
            headers={"Authorization": "Bearer " + token},
            json={
                "model": cfg["multimodal"]["tts_modelo"],
                "voice": parametros["voz_remota"],
                "input": texto,
                "instructions": parametros["instrucoes"],
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


def avaliar_audio(caminho, *, provider="local", modelo_local="small",
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
        bruto = transcrever(entrada, provider, modelo_local=modelo_local)
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


def gerar_voz(minuta, revisao, *, saida=None, provider="espeak",
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
    pasta = nova_saida(saida, "tts")
    aviso = ("Atenção: esta minuta contém informações não localizadas, "
             "que exigem verificação humana. " if "não localizado" in texto.casefold() else "")
    locucao = aviso + re.sub(r"[#*_`]+", " ", texto)
    (pasta / "roteiro_falado.txt").write_text(locucao, encoding="utf-8")
    destino = pasta / ("voz.wav" if provider in {"espeak", "gemini"} else "voz.mp3")
    if sintetizador_teste:
        arquivo_audio = sintetizador_teste(locucao, destino)
        origem_audio = "mock"
    else:
        arquivo_audio = sintetizar(locucao, destino, provider=provider)
        origem_audio = "local" if provider == "espeak" else "API"
    if not arquivo_audio or not Path(arquivo_audio).exists():
        raise RuntimeError("Síntese de voz não gerou arquivo verificável")
    cfg = carregar()
    parametros = _parametros_tts(cfg)
    gravar_json(pasta / "resultado.json", {
        "tipo": "TTS", "provedor": provider,
        "modelo_ou_motor": (provider if provider == "espeak"
                            else cfg["multimodal"].get("tts_modelo", "não localizado")),
        "execucao": origem_audio,
        "minuta_sha256": sha256_arquivo(origem), "aviso_ausencias_incluido": bool(aviso),
        "aviso_ausencias_texto": aviso.strip() or None,
        "roteiro_falado_sha256": hashlib.sha256(locucao.encode("utf-8")).hexdigest(),
        "arquivo_audio": Path(arquivo_audio).name, "hash_audio": sha256_arquivo(Path(arquivo_audio)),
        "formato_audio": Path(arquivo_audio).suffix.lstrip(".").lower(),
        "voz": parametros["voz_local"] if provider == "espeak" else parametros["voz_remota"],
        "instrucoes_entonacao": parametros["instrucoes"],
        "parametros_locais": ({
            "velocidade": parametros["velocidade"],
            "tom": parametros["tom"],
            "volume": parametros["volume"],
            "pausa_palavras_ms": parametros["pausa_palavras_ms"],
        } if provider == "espeak" else None),
        "duracao_audio_s": duracao_audio(Path(arquivo_audio)),
        "observacao": "Aprovação registrada em arquivo; conferir identidade e decisão do revisor.",
        "correspondencia_com_texto": "pendente de validação auditiva humana",
        "data_utc": datetime.now(timezone.utc).isoformat(),
    })
    return pasta
