"""RF14: esquema, calendário e suporte literal são verificações distintas."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import jsonschema

VERSAO_SCHEMA = "2.0"
CAMPOS = ("protocolo", "data", "solicitante", "assunto", "pedido")
CATEGORIAS = (
    "efetivacao_matricula", "segunda_via_documento", "andamento_processo",
    "atualizacao_cadastral", "agendamento", "reclamacao", "outros", "revisao",
)
MESES = ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro")


class ErroContrato(ValueError):
    """Saída não pode seguir para minuta; mensagem contém só regras violadas."""


def esquema_ficha() -> dict:
    return json.loads((Path(__file__).parent / "schemas/ficha.schema.json").read_text(encoding="utf-8"))


def esquema_analise() -> dict:
    return {
        "type": "object", "additionalProperties": False,
        "required": ["ficha", "resumo", "inferencias"],
        "properties": {
            "ficha": esquema_ficha(),
            "resumo": {"type": "string", "minLength": 1},
            "inferencias": {"type": "array", "maxItems": 0, "items": {"type": "string"}},
        },
    }


def normalizar(texto: str) -> str:
    return " ".join(texto.casefold().split())


def _datas_fonte(texto: str) -> set[str]:
    datas = set()
    for valor in re.findall(r"\b\d{1,2}/\d{1,2}/\d{4}\b", texto):
        try:
            datas.add(datetime.strptime(valor, "%d/%m/%Y").strftime("%d/%m/%Y"))
        except ValueError:
            pass
    for dia, mes, ano in re.findall(r"\b(\d{1,2}) de ([\wç]+) de (\d{4})\b", texto.casefold()):
        if mes not in MESES:
            continue
        try:
            datas.add(datetime(int(ano), MESES.index(mes) + 1, int(dia)).strftime("%d/%m/%Y"))
        except ValueError:
            pass
    return datas


def _protocolo_presente(valor: str, texto: str) -> bool:
    esperado = re.sub(r"[\s.-]", "", valor).casefold()
    candidatos = re.findall(r"\b20\d{2}\s*[.-]\s*\d{3}(?:\s*[.-]?\s*)\d{3}\b", texto)
    return any(re.sub(r"[\s.-]", "", item).casefold() == esperado for item in candidatos)


def validar_ficha(ficha: dict, texto: str) -> dict:
    """Rejeita formato, calendário e valores sem trecho de origem."""
    try:
        jsonschema.Draft202012Validator(esquema_ficha()).validate(ficha)
    except jsonschema.ValidationError as exc:
        caminho = ".".join(map(str, exc.absolute_path)) or "raiz"
        raise ErroContrato(f"Esquema inválido em {caminho}: {exc.validator}") from exc
    ausentes = [campo for campo in CAMPOS if ficha[campo] is None]
    if set(ficha["campos_ausentes"]) != set(ausentes) or len(ficha["campos_ausentes"]) != len(ausentes):
        raise ErroContrato("Lista de campos ausentes incoerente com valores null")
    if ausentes and not ficha["necessita_revisao"]:
        raise ErroContrato("Ausências exigem revisão")
    fonte = normalizar(texto)
    for campo in CAMPOS:
        valor = ficha[campo]
        if valor is None:
            continue
        if not valor.strip() or normalizar(valor) == "não localizado":
            raise ErroContrato(f"Campo {campo}: ausência deve ser null")
        if campo == "data":
            try:
                datetime.strptime(valor, "%d/%m/%Y")
            except ValueError as exc:
                raise ErroContrato("Data impossível ou formato inválido") from exc
            if valor not in _datas_fonte(texto):
                raise ErroContrato("Data sem suporte no original")
            # Presença no texto não basta: nascimento/início de curso não são a solicitação.
            from ..extracao import extrair
            identificada = extrair(texto, "validacao", "memoria", "nao_aplicado", "texto")["campos"]["data_solicitacao"]["valor"]
            if identificada != "não localizado" and identificada != valor:
                raise ErroContrato("Data diverge da data da solicitação identificada no original")
        elif campo == "protocolo":
            if not _protocolo_presente(valor, texto):
                raise ErroContrato("Protocolo sem suporte no original")
        elif normalizar(valor) not in fonte:
            raise ErroContrato(f"Campo {campo} sem suporte literal no original")
    for tipo, valores in ficha["entidades"].items():
        for valor in valores:
            if not valor.strip() or normalizar(valor) not in fonte:
                raise ErroContrato(f"Entidade {tipo} sem suporte literal no original")
            if tipo == "datas" and re.search(r"\b\d{1,2}/\d{1,2}/\d{4}\b|\b\d{1,2} de \w+ de \d{4}\b", valor, re.IGNORECASE):
                if not _datas_fonte(valor):
                    raise ErroContrato("Entidade datas contém calendário impossível")
    if ficha["categoria"] in {"outros", "revisao"} and not ficha["necessita_revisao"]:
        raise ErroContrato("Categoria incerta exige revisão")
    if "não sei" in fonte and " ou " in fonte and ficha["categoria"] != "revisao":
        raise ErroContrato("Intenção ambígua exige categoria revisao")
    return ficha


def validar_analise(analise: dict, texto: str) -> dict:
    try:
        jsonschema.Draft202012Validator(esquema_analise()).validate(analise)
    except jsonschema.ValidationError as exc:
        raise ErroContrato("Análise incompatível com esquema: " + str(exc.validator)) from exc
    validar_ficha(analise["ficha"], texto)
    resumo = analise["resumo"]
    if len(resumo.split()) > 100:
        raise ErroContrato("Resumo excede 100 palavras")
    # Só unidades completas, nunca palavras soltas: remover uma negação pode inverter
    # a afirmação mesmo que todas as palavras restantes estejam presentes na fonte.
    restante = normalizar(resumo)
    for unidade in unidades_extrativas(texto):
        unidade = normalizar(unidade)
        if restante == unidade:
            restante = ""
            break
        if restante.startswith(unidade + " "):
            restante = restante[len(unidade):].lstrip()
    if restante:
        raise ErroContrato("Resumo deve selecionar frases ou linhas completas do original, preservando negações")
    return analise


def unidades_extrativas(texto: str) -> list[str]:
    """Frases ou linhas completas; pontuação decimal sem espaço não divide números."""
    return [parte.strip() for parte in re.split(r"\n+|(?<=[.!?])\s+", texto.strip()) if parte.strip()]


def apresentar_valor(valor):
    """Somente apresentação usa o marcador; dados ausentes continuam null."""
    return "não localizado" if valor is None else valor


def comparar_json_esquema(texto_json: str, original: str) -> dict:
    resultado = {"json_sintatico": False, "esquema_valido": False, "negocio_valido": False}
    try:
        ficha = json.loads(texto_json)
    except (ValueError, TypeError):
        return resultado
    resultado["json_sintatico"] = True
    resultado["esquema_valido"] = jsonschema.Draft202012Validator(esquema_ficha()).is_valid(ficha)
    if resultado["esquema_valido"]:
        try:
            validar_ficha(ficha, original)
            resultado["negocio_valido"] = True
        except ErroContrato:
            pass
    return resultado
