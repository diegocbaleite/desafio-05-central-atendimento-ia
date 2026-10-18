"""WER, CER e avaliação conservadora contra gabaritos previamente definidos."""

import json
import re

from .config import ROOT


def distancia(a, b):
    anterior = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        atual = [i]
        for j, y in enumerate(b, 1):
            atual.append(
                min(atual[-1] + 1, anterior[j] + 1, anterior[j - 1] + (x != y))
            )
        anterior = atual
    return anterior[-1]


def wer(referencia, obtido):
    a = referencia.lower().split()
    b = obtido.lower().split()
    return round(distancia(a, b) / max(len(a), 1), 4)


def cer(referencia, obtido):
    a = re.sub(r"\s+", " ", referencia.casefold().strip())
    b = re.sub(r"\s+", " ", obtido.casefold().strip())
    return round(distancia(a, b) / max(len(a), 1), 4)


def avaliar_campos(extracao):
    arquivo = ROOT / "dados" / "gabaritos" / (extracao["caso_id"] + ".json")
    esperado = json.loads(arquivo.read_text(encoding="utf-8"))
    resultado = {"caso": extracao["caso_id"], "esperado": esperado, "campos": {}}
    for chave in ("protocolo",):
        if chave in esperado:
            resultado["campos"][chave] = {
                "esperado": esperado[chave],
                "obtido": extracao["campos"][chave]["valor"],
                "correto": esperado[chave] == extracao["campos"][chave]["valor"],
            }
    if "categoria" in esperado:
        resultado["categoria_corresponde"] = (
            esperado["categoria"] == extracao["categoria"]["codigo"]
        )
    if "alerta_injecao" in esperado:
        resultado["alerta_injecao_corresponde"] = (
            bool(esperado["alerta_injecao"]) == extracao["alerta_injecao"]
        )
    return resultado
