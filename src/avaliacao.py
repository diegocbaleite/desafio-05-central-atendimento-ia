"""Métricas WER/CER, avaliação contra gabaritos previamente definidos e taxa de aprovação."""

import json
import re
from pathlib import Path

from .config import ROOT


def _distancia(a, b):
    """Distância de Levenshtein com memória O(min(n,m))."""
    if len(a) < len(b):
        a, b = b, a
    anterior = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        atual = [i]
        for j, y in enumerate(b, 1):
            atual.append(
                min(atual[-1] + 1, anterior[j] + 1, anterior[j - 1] + (x != y))
            )
        anterior = atual
    return anterior[-1]


def metricas(referencia, extraido):
    """WER ignora caixa/pontuação; CER preserva caracteres de protocolos e datas."""

    def palavras(s):
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


def avaliar_texto_extraido(bruto, gabarito, revisado, pasta):
    """Compara STT/OCR com referência prévia; a revisão humana nunca é feita automaticamente."""
    resultado = {"revisao_humana": "pendente", "metricas": "não medidas"}
    if gabarito:
        referencia = Path(gabarito).read_text(encoding="utf-8")
        resultado["metricas"] = {"bruta": metricas(referencia, bruto)}
    if revisado:
        texto_revisado = Path(revisado).read_text(encoding="utf-8")
        (pasta / "texto_revisado_humano.txt").write_text(
            texto_revisado, encoding="utf-8"
        )
        resultado["revisao_humana"] = (
            "texto revisado fornecido; confirmar autoria e conferência"
        )
        if gabarito:
            resultado["metricas"]["revisada"] = metricas(referencia, texto_revisado)
    else:
        (pasta / "PENDENTE_REVISAO.md").write_text(
            "Conferir nome, protocolo, datas, dados e trechos incertos com o ORIGINAL; "
            "registrar revisão humana separadamente. Não corrigir automaticamente.\n",
            encoding="utf-8",
        )
    return resultado


def avaliar_campos(extracao, caso_id=None):
    """Compara campos críticos com o gabarito; devolve None se não houver gabarito."""
    caso_id = caso_id or extracao["caso_id"]
    arquivo = ROOT / "dados" / "gabaritos" / (caso_id + ".json")
    if not arquivo.is_file():
        return None
    esperado = json.loads(arquivo.read_text(encoding="utf-8"))
    resultado = {
        "caso": caso_id,
        "esperado": esperado,
        "campos": {},
        "erros": [],
    }
    for chave in ("protocolo", "data_solicitacao", "solicitante", "assunto", "pedido"):
        if chave in esperado:
            correto = esperado[chave] == extracao["campos"][chave]["valor"]
            gravidade = None if correto else (
                "critica" if chave in {"protocolo", "data_solicitacao"} else "alta"
            )
            resultado["campos"][chave] = {
                "esperado": esperado[chave],
                "obtido": extracao["campos"][chave]["valor"],
                "correto": correto,
                "gravidade": gravidade,
            }
            if not correto:
                resultado["erros"].append({"campo": chave, "gravidade": gravidade})
    if "categoria" in esperado:
        correto = esperado["categoria"] == extracao["categoria"]["codigo"]
        resultado["categoria_corresponde"] = correto
        if not correto:
            resultado["erros"].append({"campo": "categoria", "gravidade": "alta"})
    if "alerta_injecao" in esperado:
        correto = (
            bool(esperado["alerta_injecao"]) == extracao["alerta_injecao"]
        )
        resultado["alerta_injecao_corresponde"] = correto
        if not correto:
            resultado["erros"].append(
                {"campo": "alerta_injecao", "gravidade": "critica"}
            )
    if "ausentes" in esperado:
        esperados = set(esperado["ausentes"])
        obtidos = set(extracao["campos_ausentes"])
        correto = esperados == obtidos
        resultado["campos_ausentes"] = {
            "esperado": sorted(esperados),
            "obtido": sorted(obtidos),
            "correto": correto,
        }
        if not correto:
            resultado["erros"].append(
                {"campo": "campos_ausentes", "gravidade": "alta"}
            )
    if "decisao_esperada" in esperado:
        resultado["decisao_esperada"] = esperado["decisao_esperada"]
        resultado["observacao_decisao"] = (
            "Orientação prévia para revisão humana; não é decisão automática."
        )
    gravidades = {erro["gravidade"] for erro in resultado["erros"]}
    resultado["gravidade_geral"] = (
        "critica" if "critica" in gravidades
        else "alta" if "alta" in gravidades
        else None
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
