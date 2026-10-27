"""Polaridade de avaliações de atendimento (RF22).

`classificar_local` é um classificador por REGRAS léxicas documentadas (não é IA);
`classificar_llm` usa o provedor configurado com saída JSON validada. Em ambos, o rótulo
descreve o texto, nunca a pessoa, e "confiança" de modelo é estimativa NÃO calibrada.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache

from jsonschema import Draft202012Validator

from .config import ROOT
from .texto import normalizar

METODO_LOCAL = "regras_lexicas_v1"
_POSITIVOS = (
    "bem atendid", "excelente", "otimo", "rapido", "educad", "atencios", "paciencia",
    "resolveu", "gostei", "eficiente", "facil", "obrigad", "parabens", "satisfeit",
    "antes do prazo", "recomendo",
)
_NEGATIVOS = (
    "pessimo", "ruim", "demor", "esperei", "fila", "ninguem", "nao recebi",
    "nenhuma resposta", "descaso", "grosseir", "sem solucao", "continua sem", "caiu",
    "tive que voltar", "absurd", "nao resolveu", "nao gostei", "perdi",
)
_ELOGIO_IRONICO = ("parabens", "excelente", "otimo", "que maravilha")
_FATO_NEGATIVO = ("esperei", "so esperei", "ninguem", "de novo", "mais uma vez")
_DEPENDE_CONTEXTO = re.compile(r"\b(aquilo|aquele|aquela|isso ai|tanto faz)\b")
_INFERENCIA_SENSIVEL = re.compile(
    r"\b(personalidade|diagn[oó]stic|depress|ansios|transtorno|idade|g[eê]nero|ra[cç]a|religi|"
    r"orienta[cç][aã]o sexual|defici[eê]ncia|agressiv[oa] por natureza)\w*",
    re.IGNORECASE,
)


def _achados(base: str, termos) -> list[str]:
    return [t for t in termos if t in base]


def classificar_local(id_: str, texto: str) -> dict:
    base = normalizar(texto)
    # Negação simples: "não gostei"/"não resolveu" não contam como positivo.
    sem_negados = re.sub(r"\bnao (gostei|resolveu|foi rapido|foi educad\w*)", " ", base)
    pos = _achados(sem_negados, _POSITIVOS)
    neg = _achados(base, _NEGATIVOS)
    ironia = bool(_achados(base, _ELOGIO_IRONICO)) and bool(_achados(base, _FATO_NEGATIVO))
    if ironia:
        rotulo, revisao, motivo = "indeterminada", True, "ironia provável: elogio acompanhado de fato negativo"
    elif pos and neg:
        rotulo, revisao, motivo = "indeterminada", True, f"mista: elogio ({pos[0]}) e crítica ({neg[0]})"
    elif pos:
        rotulo, revisao, motivo = "positiva", False, f"termos favoráveis: {', '.join(pos[:3])}"
    elif neg:
        rotulo, revisao, motivo = "negativa", False, f"termos desfavoráveis: {', '.join(neg[:3])}"
    elif _DEPENDE_CONTEXTO.search(base):
        rotulo, revisao, motivo = "indeterminada", True, "falta de contexto: depende de conversa anterior"
    else:
        rotulo, revisao, motivo = "neutra", False, "relato factual sem juízo de valor"
    return {
        "id": id_,
        "polaridade": rotulo,
        "justificativa": motivo,
        "requer_revisao": revisao,
        "metodo": METODO_LOCAL,
        "confianca_declarada": None,
        "observacao_confianca": "não se aplica: classificador por regras não estima confiança",
    }


@lru_cache(maxsize=1)
def _schema() -> dict:
    return json.loads((ROOT / "src/schemas/sentimento.schema.json").read_text(encoding="utf-8"))


def _validar(texto: str, id_: str) -> dict:
    resultado = {"valido": False, "erros_sintaxe": [], "erros_esquema": [], "erros_regras": [], "objeto": None}
    try:
        obj = json.loads(texto)
    except ValueError as exc:
        resultado["erros_sintaxe"] = [{"tipo": "json_invalido", "campo": None, "mensagem": str(exc)[:200]}]
        return resultado
    resultado["objeto"] = obj
    resultado["erros_esquema"] = [
        {"tipo": e.validator, "campo": "/".join(map(str, e.absolute_path)) or "(raiz)", "mensagem": e.message[:200]}
        for e in Draft202012Validator(_schema()).iter_errors(obj)
    ]
    if not resultado["erros_esquema"]:
        if obj["id"] != id_:
            resultado["erros_regras"].append({"tipo": "id_divergente", "campo": "id", "mensagem": "ID diferente do enviado"})
        if _INFERENCIA_SENSIVEL.search(obj["justificativa"]):
            resultado["erros_regras"].append(
                {"tipo": "inferencia_sensivel", "campo": "justificativa", "mensagem": "justificativa infere característica da pessoa"}
            )
    resultado["valido"] = not (resultado["erros_esquema"] or resultado["erros_regras"])
    return resultado


def classificar_llm(id_: str, texto: str, perfil: dict, orcamento=None, conversar_fn=None) -> dict:
    from .llm_json import chamar_json, formato_resposta
    from .prompts import carregar_prompt
    from .seguranca import minimizar

    prompt = carregar_prompt("sentimento_v1")
    corpo = minimizar(texto).replace("</avaliacao>", "[tag neutralizada]")
    saida = chamar_json(
        [
            {"role": "system", "content": prompt["texto"]},
            {"role": "user", "content": f'<avaliacao id="{id_}">\n{corpo}\n</avaliacao>'},
        ],
        lambda bruto: _validar(bruto, id_),
        perfil,
        orcamento=orcamento,
        conversar_fn=conversar_fn,
        response_format=formato_resposta("sentimento_v1", _schema()),
    )
    if not saida["valido"]:
        return {
            "id": id_, "polaridade": "indeterminada", "requer_revisao": True,
            "justificativa": "saída do modelo inválida após 1 correção; classificar manualmente",
            "metodo": "llm", "confianca_declarada": None, "erros": [e for t in saida["tentativas"] for e in t["erros"]],
        }
    obj = saida["resultado"]["objeto"]
    return {
        **obj,
        "metodo": f"llm:{perfil.get('provider')}:{perfil.get('modelo')}",
        "observacao_confianca": "estimativa declarada pelo modelo, não calibrada; não é probabilidade de acerto",
        "prompt_sha256": prompt["sha256"],
    }
