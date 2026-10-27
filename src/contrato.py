"""Contrato versionado da solicitação (RF14): sintaxe JSON, esquema e regras de negócio.

Três camadas distintas, que o relatório compara:
1. JSON sintático  — `json.loads` aceita qualquer objeto bem formado;
2. Esquema         — tipos, chaves extras, obrigatórios e domínios (JSON Schema 2020-12);
3. Regras          — datas reais, valores presentes no original e coerência interna.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from functools import lru_cache

from jsonschema import Draft202012Validator

from .config import ROOT
from .seguranca import AUSENTE
from .texto import normalizar, sem_acento, termos

VERSAO_SCHEMA = "2.0.0"
ARQUIVO_SCHEMA = "src/schemas/solicitacao.v2.schema.json"
CAMPOS = ("protocolo", "data", "solicitante", "assunto", "pedido")
CATEGORIAS = (
    "segunda_via_documento",
    "andamento_processo",
    "atualizacao_cadastral",
    "agendamento",
    "reclamacao",
    "efetivacao_matricula",
    "outros",
    "revisao",
)
_TIPO_ERRO = {
    "additionalProperties": "chave_extra",
    "type": "tipo_incorreto",
    "required": "campo_obrigatorio_ausente",
    "enum": "valor_fora_do_dominio",
    "const": "valor_fora_do_dominio",
    "pattern": "formato_invalido",
    "minLength": "formato_invalido",
    "maxLength": "formato_invalido",
    "uniqueItems": "formato_invalido",
}
_MESES = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4, "maio": 5, "junho": 6,
    "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}


@lru_cache(maxsize=1)
def carregar_schema() -> dict:
    return json.loads((ROOT / ARQUIVO_SCHEMA).read_text(encoding="utf-8"))


def exibir(valor) -> str:
    """Representação para a interface: null vira 'não localizado'."""
    return AUSENTE if valor is None or valor == "" else str(valor)


def validar_sintaxe(texto: str):
    try:
        return json.loads(texto), []
    except (TypeError, ValueError) as exc:
        return None, [{"tipo": "json_invalido", "campo": None, "mensagem": str(exc)[:200]}]


def validar_esquema(obj) -> list[dict]:
    erros = []
    for erro in Draft202012Validator(carregar_schema()).iter_errors(obj):
        caminho = "/".join(str(p) for p in erro.absolute_path) or "(raiz)"
        mensagem = erro.message
        if erro.validator == "additionalProperties":
            extras = sorted(set(erro.instance) - set(erro.schema.get("properties", {})))
            mensagem = "chave(s) não prevista(s): " + ", ".join(extras)
        elif erro.validator == "required":
            mensagem = "campo obrigatório ausente: " + mensagem.split("'")[1]
        erros.append(
            {
                "tipo": _TIPO_ERRO.get(erro.validator, "outro"),
                "campo": caminho,
                "mensagem": mensagem[:200],
            }
        )
    return sorted(erros, key=lambda e: (e["tipo"], e["campo"]))


def _datas_no_texto(texto: str) -> set[str]:
    datas = set(re.findall(r"\b\d{2}/\d{2}/\d{4}\b", texto))
    base = sem_acento(texto.lower())
    for dia, mes, ano in re.findall(
        r"\b(\d{1,2})\s+de\s+(" + "|".join(_MESES) + r")\s+de\s+(\d{4})\b", base
    ):
        datas.add(f"{int(dia):02d}/{_MESES[mes]:02d}/{ano}")
    return datas


def _so_alfanumerico(texto: str) -> str:
    return re.sub(r"[^0-9a-z]", "", normalizar(texto))


def _suporte_termos(valor: str, original: str, minimo: float = 0.5) -> bool:
    alvo = set(termos(valor))
    if not alvo:
        return normalizar(valor) in normalizar(original)
    presentes = alvo & set(termos(original))
    return len(presentes) / len(alvo) >= minimo


def validar_regras(obj: dict, original: str, hoje: date | None = None) -> list[dict]:
    """Regras de negócio: só rodam sobre objeto já conforme ao esquema."""
    hoje = hoje or date.today()
    erros = []

    def erro(tipo, campo, mensagem):
        erros.append({"tipo": tipo, "campo": campo, "mensagem": mensagem})

    if obj["data"] is not None:
        try:
            valor = datetime.strptime(obj["data"], "%d/%m/%Y").date()
        except ValueError:
            erro("data_impossivel", "data", f"data inexistente no calendário: {obj['data']}")
        else:
            if valor.year < 2000:
                erro("data_fora_do_intervalo", "data", "data anterior a 2000")
            elif valor > hoje:
                erro("data_futura", "data", "data da solicitação posterior à data atual")
        if obj["data"] not in _datas_no_texto(original):
            erro("dado_sem_suporte", "data", "data não aparece na entrada original")

    if obj["protocolo"] is not None:
        if _so_alfanumerico(obj["protocolo"]) not in _so_alfanumerico(original):
            erro("dado_sem_suporte", "protocolo", "protocolo não aparece na entrada original")

    if obj["solicitante"] is not None:
        nomes = [p for p in normalizar(obj["solicitante"]).split() if len(p) > 2]
        texto = normalizar(original)
        if not nomes or any(not re.search(r"\b" + re.escape(p) + r"\b", texto) for p in nomes):
            erro("dado_sem_suporte", "solicitante", "nome não aparece na entrada original")

    for campo in ("assunto", "pedido"):
        if obj[campo] is not None and not _suporte_termos(obj[campo], original):
            erro("dado_sem_suporte", campo, "termos do campo não sustentados pelo original")

    nulos = {c for c in CAMPOS if obj[c] is None}
    if nulos != set(obj["campos_ausentes"]):
        erro(
            "campos_ausentes_incoerentes",
            "campos_ausentes",
            f"nulos={sorted(nulos)} declarados={sorted(obj['campos_ausentes'])}",
        )

    for i, ent in enumerate(obj["entidades"]):
        if not ent["literal"]:
            continue
        if not normalizar(ent["valor"]) in normalizar(original) and not (
            ent["tipo"] == "data" and ent["valor"] in _datas_no_texto(original)
        ) and not (
            ent["tipo"] == "protocolo"
            and _so_alfanumerico(ent["valor"]) in _so_alfanumerico(original)
        ):
            erro("entidade_sem_suporte", f"entidades/{i}", f"{ent['tipo']} literal ausente do original")
        elif ent["evidencia"] and normalizar(ent["evidencia"]) not in normalizar(original):
            erro("entidade_sem_suporte", f"entidades/{i}", "evidência não é trecho do original")

    if (nulos or obj["categoria"] == "revisao") and not obj["requer_revisao"]:
        erro("revisao_obrigatoria", "requer_revisao", "lacuna ou ambiguidade exige revisão humana")
    return erros


def validar(entrada, original: str, hoje: date | None = None) -> dict:
    """Valida texto JSON (str) ou objeto já decodificado nas três camadas."""
    if isinstance(entrada, str):
        obj, erros_sintaxe = validar_sintaxe(entrada)
    else:
        obj, erros_sintaxe = entrada, []
    resultado = {
        "versao_schema": VERSAO_SCHEMA,
        "sintaxe_ok": not erros_sintaxe,
        "esquema_ok": False,
        "regras_ok": False,
        "valido": False,
        "erros_sintaxe": erros_sintaxe,
        "erros_esquema": [],
        "erros_regras": [],
        "objeto": obj,
    }
    if erros_sintaxe:
        return resultado
    resultado["erros_esquema"] = validar_esquema(obj)
    resultado["esquema_ok"] = not resultado["erros_esquema"]
    if resultado["esquema_ok"]:
        resultado["erros_regras"] = validar_regras(obj, original, hoje)
        resultado["regras_ok"] = not resultado["erros_regras"]
    resultado["valido"] = resultado["esquema_ok"] and resultado["regras_ok"]
    return resultado


def resumo_erros(resultado: dict) -> list[str]:
    return [
        f"{e['tipo']}: {e['campo']}: {e['mensagem']}"
        for chave in ("erros_sintaxe", "erros_esquema", "erros_regras")
        for e in resultado.get(chave, [])
    ]
