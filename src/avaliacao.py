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


def avaliar_campos(extracao, caso_id=None):
    """Compara campos críticos com o gabarito; devolve None se não houver gabarito."""
    caso_id = caso_id or extracao["caso_id"]
    arquivo = ROOT / "dados" / "gabaritos" / (caso_id + ".json")
    if not arquivo.is_file():
        return None
    esperado = json.loads(arquivo.read_text(encoding="utf-8"))
    resultado = {"caso": caso_id, "esperado": esperado, "campos": {}}
    for chave in ("protocolo", "data_solicitacao"):
        if chave in esperado:
            correto = esperado[chave] == extracao["campos"][chave]["valor"]
            resultado["campos"][chave] = {
                "esperado": esperado[chave],
                "obtido": extracao["campos"][chave]["valor"],
                "correto": correto,
                # Protocolo ou data incorretos são erros críticos (protocolo_avaliacao.md).
                "gravidade": None if correto else "critica",
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


def taxa_aprovacao(resumos):
    """Taxa simples de aprovação direta; decisões simuladas ficam fora do denominador."""
    reais = [r for r in resumos if not r.get("simulada")]
    aprovadas = sum(1 for r in reais if r.get("decisao") == "aprovar")
    return {
        "denominador": "casos com minuta e decisão humana real (exclui simulados/mock)",
        "total_com_decisao_humana": len(reais),
        "aprovadas_sem_correcao": aprovadas,
        "excluidas_simuladas": len(resumos) - len(reais),
        "taxa_aprovacao_direta": round(aprovadas / len(reais), 4) if reais else None,
    }
