"""Cliente HTTP OpenAI-compatible com diagnóstico de erros sem expor segredos."""
import time
import requests
from .config import carregar, chave

class ErroAPI(RuntimeError):
    pass

def _erro_provedor(data):
    """Extrai apenas código e mensagem do erro, sem ecoar requisições ou tokens."""
    if not isinstance(data, dict):
        return "Resposta sem objeto JSON"
    error = data.get("error")
    if isinstance(error, dict):
        codigo = str(error.get("code", "não informado"))[:60]
        msg = str(error.get("message", "não informada"))[:300]
        return f"código={codigo}; mensagem={msg}"
    return "Campos de resposta inesperados: " + ", ".join(sorted(str(k) for k in data.keys())[:12])

def conversar(mensagens, modelo=None, provider=None):
    cfg=carregar(); conf=cfg["llm"]
    provider=provider or conf["provider"]; modelo=modelo or conf["modelo"]
    if provider=="mock":
        return {"texto":"MINUTA SIMULADA: revisar informações e confirmar dados disponíveis.",
                "modelo":"mock","provider":"mock","duracao_s":0,
                "tokens_entrada":None,"tokens_saida":None,"custo_usd":None,
                "tentativas":0,"parametros":{"aplicados":False}}
    perfil=cfg["provedores"].get(provider)
    if not perfil: raise ErroAPI("Provedor desconhecido")
    token=chave(cfg,provider)
    if not token: raise ErroAPI("Chave ausente; configure o .env")
    inicio=time.monotonic()
    erro=None
    espera=0
    for tentativa in range(3):
        try:
            r=requests.post(perfil["base_url"].rstrip("/")+"/chat/completions",
                headers={"Authorization":"Bearer "+token},
                json={"model":modelo,"messages":mensagens,
                      "temperature":conf["temperatura"],"max_tokens":conf["max_tokens"]},
                timeout=conf["timeout_s"])
        except (requests.Timeout,requests.ConnectionError) as exc:
            erro=type(exc).__name__
            espera=min(20,2**tentativa)
        else:
            try: data=r.json()
            except ValueError: data=None
            if r.status_code in (401,403):
                raise ErroAPI(f"Autenticação recusada (HTTP {r.status_code})")
            if r.status_code==429 or r.status_code>=500:
                erro=f"HTTP {r.status_code}: {_erro_provedor(data)}"
                try: espera=min(20,max(0,float(r.headers.get("Retry-After",2**tentativa))))
                except (ValueError,TypeError): espera=min(20,2**tentativa)
            elif r.status_code>=400:
                raise ErroAPI(f"HTTP {r.status_code}: {_erro_provedor(data)}")
            else:
                if not isinstance(data,dict):
                    raise ErroAPI("HTTP 200 sem objeto JSON na resposta")
                if "choices" not in data:
                    detail=_erro_provedor(data)
                    err=data.get("error") if isinstance(data.get("error"),dict) else {}
                    if str(err.get("code")) in ("429","500","502","503","504"):
                        erro="Provedor: "+detail
                        espera=min(20,2**tentativa)
                        if tentativa<2:
                            time.sleep(espera)
                            continue
                        break
                    raise ErroAPI("HTTP 200 sem choices: "+detail)
                try:
                    choice=data["choices"][0]
                    message=choice["message"]
                    texto=message.get("content")
                    finish_reason=choice.get("finish_reason")
                except (KeyError,TypeError,IndexError,AttributeError):
                    raise ErroAPI("Resposta sem formato de chat esperado")
                if not isinstance(texto,str) or not texto.strip():
                    raise ErroAPI(f"Resposta sem texto; finish_reason={finish_reason}; "
                                  "pode ter esgotado o limite de tokens de raciocínio")
                usage=data.get("usage") or {}
                return {"texto":texto.strip(),"provider":provider,
                        "modelo":data.get("model",modelo),
                        "duracao_s":round(time.monotonic()-inicio,3),
                        "tokens_entrada":usage.get("prompt_tokens"),
                        "tokens_saida":usage.get("completion_tokens"),
                        "custo_usd":usage.get("cost",data.get("cost")),
                        "tentativas":tentativa+1,
                        "parametros":{"temperature":conf["temperatura"],
                                      "max_tokens":conf["max_tokens"],
                                      "timeout_s":conf["timeout_s"]}}
        if tentativa<2: time.sleep(espera)
    raise ErroAPI("Provedor temporariamente indisponível após 3 tentativas: "+str(erro))
