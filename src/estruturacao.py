"""Converte a solicitação no contrato v2 (RF14) por regras locais ou por LLM."""

from __future__ import annotations

import re

from . import contrato, nlp
from .extracao import extrair
from .seguranca import AUSENTE, delimitar, detectar, minimizar

_DATA_ROTULADA = re.compile(r"(?im)^\s*data[^:\n]{0,30}:\s*(\d{2}/\d{2}/\d{4})")


def _valor(campo: dict) -> str | None:
    return None if campo["valor"] == AUSENTE else campo["valor"]


def ficha_por_regras(texto: str, modalidade: str = "texto") -> dict:
    """Reaproveita src/extracao.py (Desafio 01) e acrescenta entidades e categoria."""
    ext = extrair(texto, "D6", "memoria", "0" * 64, "texto")
    c = ext["campos"]
    data = _valor(c["data_solicitacao"])
    if data is None:
        # Data rotulada mas impossível (ex.: 31/02) é mantida para a regra de negócio barrar.
        m = _DATA_ROTULADA.search(texto)
        data = m.group(1) if m else None
    ficha = {
        "versao_schema": contrato.VERSAO_SCHEMA,
        "protocolo": _valor(c["protocolo"]),
        "data": data,
        "solicitante": _valor(c["solicitante"]),
        "assunto": _valor(c["assunto"]),
        "pedido": _valor(c["pedido"]),
    }
    ficha["categoria"], justificativa = nlp.categorizar(ficha["pedido"], texto)
    ficha["entidades"] = nlp.extrair_entidades(texto)
    ficha["campos_ausentes"] = [k for k in contrato.CAMPOS if ficha[k] is None]
    motivos = []
    if ficha["campos_ausentes"]:
        motivos.append("Campos ausentes: " + ", ".join(ficha["campos_ausentes"]))
    if ficha["categoria"] == "revisao":
        motivos.append(justificativa)
    if detectar(texto):
        motivos.append("Possível instrução maliciosa no conteúdo")
    if modalidade in ("audio", "imagem"):
        motivos.append("Origem STT/OCR: conferir protocolo, data e nome com o original")
    ficha["requer_revisao"] = bool(motivos)
    ficha["motivos_revisao"] = motivos
    return ficha


def estruturar(
    texto: str,
    *,
    modo: str = "regras",
    modalidade: str = "texto",
    perfil: dict | None = None,
    orcamento=None,
    conversar_fn=None,
    hoje=None,
) -> dict:
    """Devolve ficha validada (ou o erro) sem lançar exceção para dados inválidos."""
    if modo == "regras":
        ficha = ficha_por_regras(texto, modalidade)
        validacao = contrato.validar(ficha, texto, hoje)
        return {"modo": "regras", "ficha": ficha, "validacao": validacao, "tentativas": []}
    if modo != "llm":
        raise ValueError("modo de estruturação inválido: " + str(modo))
    from .llm_json import chamar_json, formato_resposta
    from .prompts import carregar_prompt

    prompt = carregar_prompt("extracao_estruturada_v1")
    mensagens = [
        {"role": "system", "content": prompt["texto"]},
        {"role": "user", "content": delimitar(minimizar(texto))},
    ]
    saida = chamar_json(
        mensagens,
        lambda bruto: contrato.validar(bruto, texto, hoje),
        perfil or {},
        orcamento=orcamento,
        conversar_fn=conversar_fn,
        response_format=formato_resposta("solicitacao_v2", contrato.carregar_schema()),
    )
    validacao = saida["resultado"]
    return {
        "modo": "llm",
        "ficha": validacao["objeto"] if saida["valido"] else None,
        "validacao": validacao,
        "tentativas": saida["tentativas"],
        "prompt": {"arquivo": prompt["arquivo"], "sha256": prompt["sha256"]},
    }
