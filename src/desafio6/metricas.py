"""Contagens determinísticas; métricas sempre expõem numerador e denominador."""

from __future__ import annotations

from collections import Counter


def proporcao(numerador: int, denominador: int) -> dict:
    if denominador < 0 or numerador < 0 or numerador > denominador:
        raise ValueError("Numerador/denominador incoerentes")
    return {
        "numerador": numerador, "denominador": denominador,
        "percentual": round(100 * numerador / denominador, 2) if denominador else None,
    }


def deduplicar(registros: list[dict]) -> list[dict]:
    """Último registro de cada ID prevalece; ausência de ID é erro, não dado novo."""
    unicos = {}
    for registro in registros:
        id_registro = registro.get("id")
        if not isinstance(id_registro, str) or not id_registro.strip():
            raise ValueError("Cada registro do painel exige ID")
        unicos[id_registro] = registro
    return list(unicos.values())


def agregar_painel(registros: list[dict], *, filtros: dict | None = None) -> dict:
    filtrados = deduplicar(registros)
    for campo, permitido in (filtros or {}).items():
        if permitido is not None:
            valores = set(permitido) if isinstance(permitido, (list, set, tuple)) else {permitido}
            filtrados = [r for r in filtrados if r.get(campo) in valores]
    polaridades = Counter(r.get("polaridade", "não localizado") for r in filtrados)
    estados = Counter(r.get("estado", "pendente") for r in filtrados)
    revisao = sum(bool(r.get("necessita_revisao", False)) for r in filtrados)
    simulados = sum(bool(r.get("simulada", False)) for r in filtrados)
    return {
        "total": len(filtrados), "por_polaridade": dict(polaridades), "por_estado": dict(estados),
        "revisao": proporcao(revisao, len(filtrados)), "simuladas": simulados,
        "percentuais_polaridade": {k: proporcao(v, len(filtrados)) for k, v in sorted(polaridades.items())},
        "registros": filtrados,
    }


def comparar_rotulos(obtidos: list[dict], esperados: list[dict], *, campo: str = "polaridade") -> dict:
    observados = {r["id"]: r for r in deduplicar(obtidos)}
    referencias = deduplicar(esperados)
    linhas = []
    for esperado in referencias:
        obtido = observados.get(esperado["id"])
        linhas.append({
            "id": esperado["id"], "esperado": esperado.get(campo),
            "obtido": obtido.get(campo) if obtido else None,
            "correto": bool(obtido and obtido.get(campo) == esperado.get(campo)),
            "revisao_esperada": esperado.get("necessita_revisao"),
            "revisao_obtida": obtido.get("necessita_revisao") if obtido else None,
        })
    return {"acuracia": proporcao(sum(l["correto"] for l in linhas), len(linhas)), "casos": linhas}


def metricas_rag(resultados: list[dict], perguntas: list[dict]) -> dict:
    """Consome flags de verificação explícitas; ID de fonte existente não conta como suporte."""
    mapa = {r["id"]: r for r in deduplicar(resultados)}
    respondiveis, sem_resposta, conflitos = [], [], []
    for p in perguntas:
        tipo = p.get("tipo", p.get("status_esperado"))
        if tipo in {"respondível", "respondível_com_fontes", "respondiveis", "respondivel", "fundamentada"}:
            respondiveis.append(p)
        elif tipo in {"sem_resposta", "sem evidência suficiente", "sem_evidencia"}:
            sem_resposta.append(p)
        elif tipo in {"conflito", "conflito de fontes", "contraditoria"}:
            conflitos.append(p)
    recuperadas = sum(mapa.get(p["id"], {}).get("recuperacao_correta") is True for p in respondiveis)
    sustentadas = sum(mapa.get(p["id"], {}).get("todas_afirmacoes_sustentadas") is True for p in respondiveis)
    abstencoes = sum(mapa.get(p["id"], {}).get("status") == "sem evidência suficiente" for p in sem_resposta)
    return {
        "recuperacao_top_k": proporcao(recuperadas, len(respondiveis)),
        "afirmacoes_sustentadas": proporcao(sustentadas, len(respondiveis)),
        "abstencao_correta": proporcao(abstencoes, len(sem_resposta)),
        "conflitos": [{"id": p["id"], "obtido": mapa.get(p["id"], {}).get("status")} for p in conflitos],
    }
