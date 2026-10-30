"""Agregação determinística por código (RF22/RF23): numerador, denominador e vazio seguro."""

from __future__ import annotations

from collections import Counter


def proporcao(numerador: int, denominador: int) -> dict:
    if denominador == 0:
        return {
            "numerador": numerador,
            "denominador": 0,
            "valor": None,
            "texto": "0/0 — conjunto vazio (indefinido)",
        }
    valor = numerador / denominador
    return {
        "numerador": numerador,
        "denominador": denominador,
        "valor": round(valor, 4),
        "texto": f"{numerador}/{denominador} ({valor * 100:.1f}%)".replace(".", ",", 1),
    }


def deduplicar_por_id(itens: list[dict], chave: str = "id") -> tuple[list[dict], list[str]]:
    """Mantém a ÚLTIMA ocorrência de cada ID (reprocessamento substitui o anterior)."""
    ultimos: dict = {}
    contagem = Counter(i[chave] for i in itens)
    for item in itens:
        ultimos[item[chave]] = item
    return list(ultimos.values()), sorted(k for k, n in contagem.items() if n > 1)


def filtrar(itens: list[dict], **criterios) -> list[dict]:
    """Critério com valor None é ignorado; lista/tupla/conjunto = qualquer um dos valores."""
    saida = []
    for item in itens:
        ok = True
        for campo, valor in criterios.items():
            if valor is None:
                continue
            if isinstance(valor, (list, tuple, set)):
                ok = ok and (not valor or item.get(campo) in valor)
            else:
                ok = ok and item.get(campo) == valor
        if ok:
            saida.append(item)
    return saida


POLARIDADES = ("positiva", "negativa", "neutra", "indeterminada")


def agregar_sentimentos(resultados: list[dict], gabarito: dict | None = None, **filtros) -> dict:
    unicos, duplicados = deduplicar_por_id(resultados)
    selecionados = filtrar(unicos, **filtros)
    total = len(selecionados)
    contagem = Counter(r["polaridade"] for r in selecionados)
    saida = {
        "total": total,
        "ids_duplicados_removidos": duplicados,
        "filtros": {k: v for k, v in filtros.items() if v is not None},
        "por_polaridade": {p: proporcao(contagem.get(p, 0), total) for p in POLARIDADES},
        "requer_revisao": proporcao(sum(1 for r in selecionados if r.get("requer_revisao")), total),
    }
    if gabarito is not None:
        com_gab = [r for r in selecionados if r["id"] in gabarito]
        acertos = [r for r in com_gab if r["polaridade"] == gabarito[r["id"]]["polaridade"]]
        matriz = {e: {o: 0 for o in POLARIDADES} for e in POLARIDADES}
        for r in com_gab:
            matriz[gabarito[r["id"]]["polaridade"]][r["polaridade"]] += 1
        saida["acuracia"] = proporcao(len(acertos), len(com_gab))
        saida["matriz_confusao"] = matriz
        incertos = [r for r in com_gab if gabarito[r["id"]].get("requer_revisao")]
        saida["incertos_sinalizados"] = proporcao(sum(1 for r in incertos if r.get("requer_revisao")), len(incertos))
        saida["erros"] = [
            {"id": r["id"], "esperado": gabarito[r["id"]]["polaridade"], "obtido": r["polaridade"]}
            for r in com_gab
            if r["polaridade"] != gabarito[r["id"]]["polaridade"]
        ]
    return saida
