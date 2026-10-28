"""Classificação auditável de avaliações fictícias; não infere atributos dos autores."""

from __future__ import annotations

from datetime import datetime, timezone

import jsonschema

from src.config import ROOT
from src.seguranca import delimitar, detectar, minimizar

from .guardrails import avaliar_entrada, hash_texto, validar_saida


POLARIDADES = ("positiva", "negativa", "neutra", "indeterminada")
ESQUEMA_SENTIMENTO = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "polaridade": {"type": "string", "enum": list(POLARIDADES)},
        "justificativa": {"type": "string", "minLength": 1, "maxLength": 300},
        "necessita_revisao": {"type": "boolean"},
    },
    "required": ["polaridade", "justificativa", "necessita_revisao"],
}


def classificar_avaliacoes(avaliacoes: list[dict], cliente) -> list[dict]:
    """Não lê gabaritos; cada registro usa uma chamada sujeita ao orçamento do cliente."""
    sistema = (ROOT / "prompts/desafio6/sentimentos.md").read_text(encoding="utf-8")
    resultados, vistos = [], set()
    for item in avaliacoes:
        id_avaliacao = item.get("id")
        texto = item.get("texto")
        if not isinstance(id_avaliacao, str) or not id_avaliacao.strip() or id_avaliacao in vistos:
            raise ValueError("Avaliações exigem IDs únicos e não vazios")
        if not isinstance(texto, str) or not texto.strip() or len(texto) > 12000:
            raise ValueError("Avaliação vazia, inválida ou acima do limite")
        vistos.add(id_avaliacao)
        if avaliar_entrada(texto, contexto=True)["decisao"] != "permitir":
            resposta = {
                "polaridade": "indeterminada",
                "justificativa": "Conteúdo com instruções adversariais; conferir avaliação manualmente.",
                "necessita_revisao": True,
            }
        else:
            resposta = cliente.gerar_json(sistema, delimitar(minimizar(texto)),
                                          ESQUEMA_SENTIMENTO, nome="sentimento_v1")
            try:
                jsonschema.validate(resposta, ESQUEMA_SENTIMENTO)
            except jsonschema.ValidationError as exc:
                raise ValueError("Classificação de sentimento inválida conforme o esquema") from exc
            if resposta["polaridade"] == "indeterminada":
                resposta["necessita_revisao"] = True
            if validar_saida(resposta["justificativa"])["decisao"] != "permitir" or detectar(resposta["justificativa"]):
                raise ValueError("Justificativa contém dados indevidos ou instruções")
        resultados.append({
            "id": id_avaliacao, **resposta, "simulada": bool(getattr(cliente, "simulado", False)),
            "modelo": getattr(cliente, "modelo", "não localizado"),
            "data_utc": datetime.now(timezone.utc).isoformat(), "versao_prompt": "sentimentos-v1",
            "sha256_entrada": hash_texto(texto),
            "confianca": None, "confianca_nota": "não estimada; não representa probabilidade nem sentimento da população",
        })
    return resultados
