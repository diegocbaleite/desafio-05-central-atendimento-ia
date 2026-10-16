"""Cliente HTTP genérico OpenAI-compatible; não registra chaves."""

import time

import requests

from .config import carregar, chave


class ErroAPI(RuntimeError):
    pass


def conversar(mensagens, modelo=None, provider=None):
    cfg = carregar()
    conf = cfg["llm"]
    provider = provider or conf["provider"]
    modelo = modelo or conf["modelo"]
    if provider == "mock":
        return {
            "texto": "MINUTA SIMULADA: revisar informações e confirmar dados disponíveis.",
            "modelo": "mock",
            "provider": "mock",
            "duracao_s": 0,
            "tokens_entrada": None,
            "tokens_saida": None,
            "custo_usd": None,
        }
    perfil = cfg["provedores"].get(provider)
    if not perfil:
        raise ErroAPI("Provedor desconhecido")
    token = chave(cfg, provider)
    if not token:
        raise ErroAPI("Chave ausente; configure o .env")
    inicio = time.monotonic()
    erro = None
    for tentativa in range(3):
        try:
            r = requests.post(
                perfil["base_url"].rstrip("/") + "/chat/completions",
                headers={"Authorization": "Bearer " + token},
                json={
                    "model": modelo,
                    "messages": mensagens,
                    "temperature": conf["temperatura"],
                    "max_tokens": conf["max_tokens"],
                },
                timeout=conf["timeout_s"],
            )
        except (requests.Timeout, requests.ConnectionError) as exc:
            erro = type(exc).__name__
        else:
            if r.status_code in (401, 403):
                raise ErroAPI("Autenticação recusada")
            if r.status_code == 429 or r.status_code >= 500:
                erro = "HTTP " + str(r.status_code)
            elif r.status_code >= 400:
                raise ErroAPI("Requisição inválida: HTTP " + str(r.status_code))
            else:
                try:
                    data = r.json()
                    texto = data["choices"][0]["message"]["content"].strip()
                except (KeyError, TypeError, ValueError, IndexError, AttributeError):
                    raise ErroAPI("Resposta vazia ou inválida")
                if not texto:
                    raise ErroAPI("Resposta vazia")
                usage = data.get("usage") or {}
                return {
                    "texto": texto,
                    "provider": provider,
                    "modelo": data.get("model", modelo),
                    "duracao_s": round(time.monotonic() - inicio, 3),
                    "tokens_entrada": usage.get("prompt_tokens"),
                    "tokens_saida": usage.get("completion_tokens"),
                    "custo_usd": None,
                }
        if tentativa < 2:
            time.sleep(tentativa + 1)
    raise ErroAPI("Indisponível/limite de requisições: " + str(erro))
