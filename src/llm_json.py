"""Chamada LLM com saída JSON: esquema restrito quando suportado, validação local
e no máximo UMA tentativa de correção (RF14/RF16). A correção consome orçamento."""

from __future__ import annotations

import re
from typing import Callable


def _sem_cerca(texto: str) -> str:
    """Remove cerca ```json ... ``` (não altera o conteúdo do objeto)."""
    m = re.fullmatch(r"\s*```(?:json)?\s*(.*?)\s*```\s*", texto, re.DOTALL)
    return m.group(1) if m else texto


def formato_resposta(nome: str, schema: dict) -> dict:
    return {"type": "json_schema", "json_schema": {"name": nome, "schema": schema, "strict": True}}


def chamar_json(
    mensagens: list[dict],
    validar: Callable[[str], dict],
    perfil: dict,
    *,
    orcamento=None,
    conversar_fn=None,
    response_format: dict | None = None,
) -> dict:
    """`validar(texto)` devolve dict com 'valido' e erros (ver src.contrato.validar)."""
    from .cliente import conversar
    from .contrato import resumo_erros

    conversar_fn = conversar_fn or conversar
    usar_formato = response_format if perfil.get("saida_estruturada") else None
    historico = list(mensagens)
    tentativas = []
    for numero in (1, 2):
        resposta = conversar_fn(
            historico,
            modelo=perfil.get("modelo"),
            provider=perfil.get("provider"),
            orcamento=orcamento,
            response_format=usar_formato,
            parametros={"temperatura": perfil.get("temperatura"), "max_tokens": perfil.get("max_tokens")},
        )
        bruto = resposta["texto"]
        resultado = validar(_sem_cerca(bruto))
        tentativas.append(
            {
                "tentativa": numero,
                "valido": resultado["valido"],
                "erros": resumo_erros(resultado),
                "metadados": {k: v for k, v in resposta.items() if k != "texto"},
            }
        )
        if resultado["valido"]:
            return {"valido": True, "resultado": resultado, "tentativas": tentativas, "saida_bruta": bruto}
        if numero == 1:
            historico = historico + [
                {"role": "assistant", "content": bruto},
                {
                    "role": "user",
                    "content": "A saída anterior foi rejeitada pela validação local: "
                    + "; ".join(resumo_erros(resultado))[:1500]
                    + ". Corrija e responda somente com o JSON válido, sem inventar dados.",
                },
            ]
    return {"valido": False, "resultado": resultado, "tentativas": tentativas, "saida_bruta": bruto}
