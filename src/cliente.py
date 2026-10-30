"""Cliente HTTP OpenAI-compatible com diagnóstico de erros sem expor segredos."""

from __future__ import annotations

import time
from copy import deepcopy
from typing import Any

import requests

from .config import carregar, chave


class ErroAPI(RuntimeError):
    """Falha controlada de configuração, transporte ou resposta do provedor."""


def _erro_provedor(data: Any, segredo: str = "") -> str:
    """Extrai apenas código e mensagem do erro, sem ecoar requisições ou tokens."""
    if not isinstance(data, dict):
        return "Resposta sem objeto JSON"
    erro = data.get("error")
    if isinstance(erro, dict):
        codigo = str(erro.get("code", "não informado"))
        mensagem = str(erro.get("message", "não informada"))
        if segredo:
            codigo = codigo.replace(segredo, "[CREDENCIAL_REMOVIDA]")
            mensagem = mensagem.replace(segredo, "[CREDENCIAL_REMOVIDA]")
        return f"código={codigo[:60]}; mensagem={mensagem[:300]}"
    chaves = ", ".join(sorted(str(chave_) for chave_ in data)[:12])
    return "Campos de resposta inesperados: " + chaves


def _schema_openai(schema: dict) -> dict:
    """Adapta somente o esquema de transporte; a validação local mantém o contrato.

    O subconjunto da API usa enum para constantes e não aplica uniqueItems.
    Essa última regra continua sendo verificada localmente, inclusive na correção.
    """
    s = deepcopy(schema)
    for chave_ in ("$schema", "$id", "uniqueItems"):
        s.pop(chave_, None)
    if "const" in s:
        s["enum"] = [s.pop("const")]
    if "enum" in s and "type" not in s:
        tipos = {str: "string", bool: "boolean", int: "integer", float: "number", type(None): "null"}
        encontrados = list(dict.fromkeys(tipos[type(v)] for v in s["enum"]))
        s["type"] = encontrados[0] if len(encontrados) == 1 else encontrados
    for grupo in ("properties", "$defs", "definitions"):
        if grupo in s:
            s[grupo] = {k: _schema_openai(v) for k, v in s[grupo].items()}
    if isinstance(s.get("items"), dict):
        s["items"] = _schema_openai(s["items"])
    for grupo in ("anyOf", "oneOf", "allOf"):
        if grupo in s:
            s[grupo] = [_schema_openai(v) for v in s[grupo]]
    return s


def _payload(
    mensagens: list[dict[str, Any]],
    modelo: str,
    conf: dict,
    response_format: dict | None = None,
    provider: str | None = None,
) -> dict:
    if isinstance(response_format, str) and provider is None:
        provider, response_format = response_format, None
    limite = "max_completion_tokens" if provider == "openai" else "max_tokens"
    payload = {
        "model": modelo,
        "messages": mensagens,
        limite: conf["max_tokens"],
    }
    if conf.get("temperatura") is not None:
        payload["temperature"] = conf["temperatura"]
    if provider == "openai":
        payload["store"] = False
        if modelo.startswith(("gpt-5", "gpt-6", "o1", "o3", "o4")):
            esforco = conf.get("reasoning_effort", "low")
            payload["reasoning_effort"] = esforco
            if esforco != "none":
                payload.pop("temperature", None)
    if response_format:
        # Saída restrita por esquema (OpenAI-compatible); o resultado é revalidado localmente.
        payload["response_format"] = deepcopy(response_format)
        if provider == "openai" and response_format.get("type") == "json_schema":
            formato = payload["response_format"]["json_schema"]
            formato["schema"] = _schema_openai(formato["schema"])
    return payload


def listar_modelos(provider: str | None = None) -> list[str]:
    """Consulta o catálogo da conta; não gera conteúdo nem imprime credenciais."""
    cfg = carregar()
    provider = provider or cfg["llm"]["provider"]
    perfil = cfg["provedores"].get(provider)
    if not perfil:
        raise ErroAPI("Provedor desconhecido")
    token = chave(cfg, provider)
    if not token:
        raise ErroAPI("Chave ausente; configure o .env")
    try:
        resposta = requests.get(
            perfil["base_url"].rstrip("/") + "/models",
            headers={"Authorization": "Bearer " + token},
            timeout=cfg["llm"]["timeout_s"],
        )
    except requests.RequestException as exc:
        raise ErroAPI("Falha ao consultar modelos: " + type(exc).__name__) from exc
    if not resposta.ok:
        raise ErroAPI(f"Consulta de modelos recusada (HTTP {resposta.status_code})")
    try:
        dados = resposta.json()["data"]
        if not isinstance(dados, list):
            raise TypeError
        modelos = [item["id"] for item in dados]
        if not all(isinstance(item, str) and item.strip() for item in modelos):
            raise TypeError
        return sorted(set(modelos))
    except (ValueError, KeyError, TypeError) as exc:
        raise ErroAPI("Catálogo de modelos inválido") from exc


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
                json=_payload(mensagens, modelo, conf, response_format, provider=provider),
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
                    f"HTTP {resposta.status_code}: {_erro_provedor(dados, token)}"
                )
                espera = _espera_retentativa(resposta, tentativa)
            elif resposta.status_code >= 400:
                raise ErroAPI(
                    f"HTTP {resposta.status_code}: {_erro_provedor(dados, token)}"
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
                    ultimo_erro = "Provedor: " + _erro_provedor(dados, token)
                    espera = min(20, 2**tentativa)
                    if tentativa < tentativas_max - 1:
                        time.sleep(espera)
                        continue
                    break
                resultado = _interpretar_sucesso(
                    dados, provider, modelo, conf, inicio, tentativa, token
                )
                resultado["parametros"] = {k: v for k, v in _payload(mensagens, modelo, conf, response_format, provider=provider).items() if k not in {"model", "messages"}}
                resultado["parametros"]["timeout_s"] = conf["timeout_s"]
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
    token: str = "",
) -> dict[str, Any]:
    if not isinstance(dados, dict):
        raise ErroAPI("HTTP 200 sem objeto JSON na resposta")
    if "choices" not in dados:
        raise ErroAPI("HTTP 200 sem choices: " + _erro_provedor(dados, token))
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
    parametros = {
        "max_completion_tokens" if provider == "openai" else "max_tokens": conf["max_tokens"],
        "timeout_s": conf["timeout_s"],
    }
    if conf.get("temperatura") is not None:
        parametros["temperature"] = conf["temperatura"]
    if provider == "openai" and conf.get("reasoning_effort") is not None:
        parametros["reasoning_effort"] = conf["reasoning_effort"]
    return {
        "texto": texto.strip(),
        "provider": provider,
        "modelo": dados.get("model", modelo),
        "duracao_s": round(time.monotonic() - inicio, 3),
        "tokens_entrada": uso.get("prompt_tokens"),
        "tokens_saida": uso.get("completion_tokens"),
        "custo_usd": uso.get("cost", dados.get("cost")),
        "tentativas": tentativa + 1,
        "parametros": parametros,
    }
