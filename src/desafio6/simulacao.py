"""Regras locais para demonstração rotulada; nunca usam os gabaritos."""

from __future__ import annotations

import json
import re


def _externo(conteudo):
    prefixo, sufixo = "<conteudo_externo>\n", "\n</conteudo_externo>"
    if conteudo.startswith(prefixo) and conteudo.endswith(sufixo):
        return conteudo[len(prefixo):-len(sufixo)]
    return conteudo


def gerar(nome, conteudo, esquema):
    texto = _externo(conteudo)
    if nome in {"solicitacao", "analise_solicitacao"}:
        from .nlp import ficha_local_simulada
        return ficha_local_simulada(texto)
    if nome == "resposta_rag":
        from .rag import _termos
        dados = json.loads(texto)
        termos = _termos(dados["pergunta"])
        candidatos = []
        for doc in dados["contexto_documental"]:
            for linha in doc["texto"].splitlines():
                if linha.startswith("#") or len(linha.split()) < 5:
                    continue
                for frase in re.split(r"(?<=[.!?])\s+", linha):
                    score = len(termos & _termos(frase))
                    if score >= 2:
                        candidatos.append((score, doc["chunk_id"], frase))
        candidatos.sort(key=lambda item: -item[0])
        afirmacoes = [{"chunk_id": c, "trecho": t} for _, c, t in candidatos[:2]]
        return {"status": "fundamentada" if afirmacoes else "sem evidência suficiente", "afirmacoes": afirmacoes}
    if nome == "sentimento_v1":
        inferior = texto.casefold()
        positivo = any(p in inferior for p in ("excelente", "obrigad", "bem atend", "gostei", "gentil", "ótimo"))
        negativo = any(p in inferior for p in ("péssim", "confus", "insatisfeit", "ruim", "não resolve", "não gostei", "perdida"))
        incerto = (positivo and negativo) or "que maravilha" in inferior or len(texto.split()) < 4
        polaridade = "indeterminada" if incerto else "negativa" if negativo else "positiva" if positivo else "neutra"
        return {"polaridade": polaridade, "justificativa": "Simulação por regras lexicais; classificação sujeita à revisão.",
                "necessita_revisao": incerto}
    raise ValueError("Não existe simulador para este contrato")
