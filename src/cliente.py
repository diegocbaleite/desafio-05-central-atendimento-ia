"""Cliente HTTP OpenAI-compatible com diagnóstico de erros sem expor segredos."""

from __future__ import annotations

import time
from typing import Any

import requests

from .config import carregar, chave


class ErroAPI(RuntimeError):
    """Falha controlada de configuração, transporte ou resposta do provedor."""


def _erro_provedor(data: Any) -> str:
    """Extrai apenas código e mensagem do erro, sem ecoar requisições ou tokens."""
    if not isinstance(data, dict):
        return "Resposta sem objeto JSON"
    erro = data.get("error")
    if isinstance(erro, dict):
        codigo = str(erro.get("code", "não informado"))[:60]
        mensagem = str(erro.get("message", "não informada"))[:300]
        return f"código={codigo}; mensagem={mensagem}"
    chaves = ", ".join(sorted(str(chave_) for chave_ in data)[:12])
    return "Campos de resposta inesperados: " + chaves


def _payload(
    mensagens: list[dict[str, Any]],
    modelo: str,
    conf: dict,
    response_format: dict | None = None,
) -> dict:
    payload = {
        "model": modelo,
        "messages": mensagens,
        "temperature": conf["temperatura"],
        "max_tokens": conf["max_tokens"],
    }
    if response_format:
        # Saída restrita por esquema (OpenAI-compatible); o resultado é revalidado localmente.
        payload["response_format"] = response_format
    return payload


def _espera_retentativa(resposta, tentativa: int) -> float:
    try:
        return min(
            20,
            max(0, float(resposta.headers.get("Retry-After", 2**tentativa))),
        )
    except (AttributeError, TypeError, ValueError):
        return min(20, 2**tentativa)


def conversar(
    mensagens: list[dict[str, Any]],
    modelo: str | None = None,
    provider: str | None = None,
    orcamento=None,
    response_format: dict | None = None,
    parametros: dict | None = None,
) -> dict[str, Any]:
    """Uma chamada de chat com no máximo `llm.max_repeticoes` repetições transitórias.

    `orcamento` (src.orcamento.Orcamento) é consultado antes de CADA requisição HTTP;
    `parametros` sobrescreve temperatura/max_tokens do perfil de geração.
    """
    cfg = carregar()
    conf = dict(cfg["llm"])
    conf.update({k: v for k, v in (parametros or {}).items() if v is not None})
    provider = provider or conf["provider"]
    modelo = modelo or conf["modelo"]
    tentativas_max = 1 + int(conf.get("max_repeticoes", 1))
    if provider == "mock":
        return {
            "texto": "MINUTA SIMULADA: revisar informações e confirmar dados disponíveis.",
            "modelo": "mock",
            "provider": "mock",
            "duracao_s": 0,
            "tokens_entrada": None,
            "tokens_saida": None,
            "custo_usd": None,
            "tentativas": 0,
            "parametros": {"aplicados": False},
        }

    perfil = cfg["provedores"].get(provider)
    if not perfil:
        raise ErroAPI("Provedor desconhecido")
    token = chave(cfg, provider)
    if not token:
        raise ErroAPI("Chave ausente; configure o .env")

    inicio = time.monotonic()
    ultimo_erro = None
    espera = 0.0
    for tentativa in range(tentativas_max):
        if orcamento is not None:
            orcamento.reservar(f"{provider}:{modelo}:tentativa{tentativa + 1}")
        try:
            resposta = requests.post(
                perfil["base_url"].rstrip("/") + "/chat/completions",
                headers={"Authorization": "Bearer " + token},
                json=_payload(mensagens, modelo, conf, response_format),
                timeout=conf["timeout_s"],
            )
        except (requests.Timeout, requests.ConnectionError) as exc:
            ultimo_erro = type(exc).__name__
            espera = min(20, 2**tentativa)
        else:
            try:
                dados = resposta.json()
            except ValueError:
                dados = None
            if resposta.status_code in (401, 403):
                raise ErroAPI(
                    f"Autenticação recusada (HTTP {resposta.status_code})"
                )
            if resposta.status_code == 429 or resposta.status_code >= 500:
                ultimo_erro = (
                    f"HTTP {resposta.status_code}: {_erro_provedor(dados)}"
                )
                espera = _espera_retentativa(resposta, tentativa)
            elif resposta.status_code >= 400:
                raise ErroAPI(
                    f"HTTP {resposta.status_code}: {_erro_provedor(dados)}"
                )
            else:
                erro_no_corpo = (
                    dados.get("error")
                    if isinstance(dados, dict)
                    and isinstance(dados.get("error"), dict)
                    else {}
                )
                if (
                    isinstance(dados, dict)
                    and "choices" not in dados
                    and str(erro_no_corpo.get("code"))
                    in {"429", "500", "502", "503", "504"}
                ):
                    ultimo_erro = "Provedor: " + _erro_provedor(dados)
                    espera = min(20, 2**tentativa)
                    if tentativa < tentativas_max - 1:
                        time.sleep(espera)
                        continue
                    break
                resultado = _interpretar_sucesso(
                    dados, provider, modelo, conf, inicio, tentativa
                )
                if orcamento is not None:
                    orcamento.consumir_tokens(
                        resultado["tokens_entrada"], resultado["tokens_saida"]
                    )
                return resultado
        if tentativa < tentativas_max - 1:
            time.sleep(espera)
    raise ErroAPI(
        f"Provedor temporariamente indisponível após {tentativas_max} tentativas: "
        + str(ultimo_erro)
    )


def _interpretar_sucesso(
    dados: Any,
    provider: str,
    modelo: str,
    conf: dict,
    inicio: float,
    tentativa: int,
) -> dict[str, Any]:
    if not isinstance(dados, dict):
        raise ErroAPI("HTTP 200 sem objeto JSON na resposta")
    if "choices" not in dados:
        raise ErroAPI("HTTP 200 sem choices: " + _erro_provedor(dados))
    try:
        escolha = dados["choices"][0]
        texto = escolha["message"].get("content")
        motivo_fim = escolha.get("finish_reason")
    except (KeyError, TypeError, IndexError, AttributeError) as exc:
        raise ErroAPI("Resposta sem formato de chat esperado") from exc
    if not isinstance(texto, str) or not texto.strip():
        raise ErroAPI(
            f"Resposta sem texto; finish_reason={motivo_fim}; "
            "pode ter esgotado o limite de tokens de raciocínio"
        )
    uso = dados.get("usage") or {}
    return {
        "texto": texto.strip(),
        "provider": provider,
        "modelo": dados.get("model", modelo),
        "duracao_s": round(time.monotonic() - inicio, 3),
        "tokens_entrada": uso.get("prompt_tokens"),
        "tokens_saida": uso.get("completion_tokens"),
        "custo_usd": uso.get("cost", dados.get("cost")),
        "tentativas": tentativa + 1,
        "parametros": {
            "temperature": conf["temperatura"],
            "max_tokens": conf["max_tokens"],
            "timeout_s": conf["timeout_s"],
        },
    }
