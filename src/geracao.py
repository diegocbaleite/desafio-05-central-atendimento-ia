"""Adaptadores de GERAÇÃO (RF21), isolados da recuperação.

Trocar o perfil (config `geracao.perfil_ativo` ou parâmetro --gerador) não toca no índice.
- llm        : provedor configurado (cliente.py), JSON validado e citações conferidas.
- extrativo  : seleciona frases literais dos trechos; determinístico, NÃO é LLM.
- mock       : saída fixa para testes; identificado como simulado.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache

from jsonschema import Draft202012Validator

from .config import ROOT
from .ingestao import descrever_local
from .texto import frases, termos

INDISPONIVEL = "indisponível"


@lru_cache(maxsize=1)
def _schema_rag() -> dict:
    return json.loads((ROOT / "src/schemas/rag_resposta.schema.json").read_text(encoding="utf-8"))


def validar_resposta_rag(texto: str) -> dict:
    """Mesma estrutura de retorno de src.contrato.validar (sintaxe e esquema)."""
    resultado = {"valido": False, "erros_sintaxe": [], "erros_esquema": [], "erros_regras": [], "objeto": None}
    try:
        obj = json.loads(texto)
    except ValueError as exc:
        resultado["erros_sintaxe"] = [{"tipo": "json_invalido", "campo": None, "mensagem": str(exc)[:200]}]
        return resultado
    resultado["objeto"] = obj
    resultado["erros_esquema"] = [
        {"tipo": e.validator, "campo": "/".join(map(str, e.absolute_path)) or "(raiz)", "mensagem": e.message[:200]}
        for e in Draft202012Validator(_schema_rag()).iter_errors(obj)
    ]
    resultado["valido"] = not resultado["erros_esquema"]
    return resultado


def cobertura(pergunta: str, texto: str, idf: dict | None = None) -> float:
    """Fração (ponderada por IDF) dos termos da pergunta presentes no texto."""
    q = {t for t in termos(pergunta) if not t.isdigit()}
    if not q:
        return 0.0
    presentes = q & set(termos(texto))
    peso = (lambda t: (idf or {}).get(t, (idf or {}).get("__ausente__", 1.0)))
    total = sum(peso(t) for t in q)
    return sum(peso(t) for t in presentes) / total if total else 0.0


def _metadados_locais(perfil_nome: str, perfil: dict) -> dict:
    return {
        "perfil": perfil_nome,
        "tipo": perfil.get("tipo"),
        "e_llm": False,
        "provider": "local",
        "modelo": perfil.get("descricao", perfil.get("tipo")),
        "tokens_entrada": INDISPONIVEL,
        "tokens_saida": INDISPONIVEL,
        "custo_usd": INDISPONIVEL,
        "observacao": "execução local sem provedor: tokens e custo não se aplicam; latência medida",
    }


class GeradorExtrativo:
    def __init__(self, nome: str, perfil: dict, max_frases: int = 3):
        self.nome, self.perfil, self.max_frases = nome, perfil, max_frases
        self.e_llm = False

    def gerar(self, pergunta, trechos, fatos_solicitante=None, idf=None, cobertura_minima=0.5, **_):
        candidatas = []
        for t in trechos:
            for frase in frases(t["texto"]):
                c = cobertura(pergunta, frase, idf)
                if c >= cobertura_minima:
                    candidatas.append((c, t["similaridade"], frase, t))
        candidatas.sort(key=lambda x: (x[0], x[1]), reverse=True)
        escolhidas, vistas = [], set()
        for c, _sim, frase, t in candidatas:
            if frase not in vistas:
                vistas.add(frase)
                escolhidas.append({"texto": frase, "chunk_ids": [t["chunk_id"]], "citacao_literal": frase, "cobertura": round(c, 3)})
            if len(escolhidas) == self.max_frases:
                break
        resposta = " ".join(
            f"{a['texto']} [{descrever_local(next(t['metadados'] for t in trechos if t['chunk_id'] == a['chunk_ids'][0]))}]"
            for a in escolhidas
        )
        return {
            "status_sugerido": "fundamentada" if escolhidas else "sem_evidencia_suficiente",
            "resposta": resposta,
            "afirmacoes": escolhidas,
            "divergencias": [],
            "metadados": _metadados_locais(self.nome, self.perfil),
        }


class GeradorMock:
    """Saída configurada pelo teste. Nunca usar como evidência de modelo real."""

    def __init__(self, nome: str, perfil: dict, saida: dict | None = None, erro: Exception | None = None):
        self.nome, self.perfil, self.saida, self.erro = nome, perfil, saida, erro
        self.e_llm = False

    def gerar(self, pergunta, trechos, **_):
        if self.erro:
            raise self.erro
        saida = dict(self.saida or {"status": "sem_evidencia_suficiente", "resposta": "", "afirmacoes": [], "divergencias": []})
        return {
            "status_sugerido": saida["status"],
            "resposta": saida["resposta"],
            "afirmacoes": saida["afirmacoes"],
            "divergencias": saida.get("divergencias", []),
            "metadados": {**_metadados_locais(self.nome, self.perfil), "tipo": "mock", "simulado": True},
        }


def _neutralizar_tags(texto: str) -> str:
    return re.sub(
        r"</?\s*(trecho|contexto_institucional|pergunta|fatos_do_solicitante)[^>]*>",
        "[tag neutralizada]",
        texto,
        flags=re.IGNORECASE,
    )


class GeradorLLM:
    def __init__(self, nome: str, perfil: dict):
        self.nome, self.perfil = nome, perfil
        self.e_llm = True

    def montar_mensagens(self, pergunta, trechos, fatos_solicitante=None) -> tuple[list[dict], dict]:
        from .prompts import carregar_prompt
        from .seguranca import minimizar

        prompt = carregar_prompt("rag_resposta_v1")
        blocos = []
        for t in trechos:
            m = t["metadados"]
            blocos.append(
                f'<trecho id="{t["chunk_id"]}" documento="{m["doc_id"]}" versao="{m["versao"]}" '
                f'secao="{m["secao"]}" pagina="{m["pagina"] if m["pagina"] > 0 else "n/a"}">\n'
                f"{_neutralizar_tags(t['texto'])}\n</trecho>"
            )
        usuario = (
            f"<pergunta>\n{_neutralizar_tags(minimizar(pergunta))}\n</pergunta>\n"
            f"<fatos_do_solicitante>\n{_neutralizar_tags(minimizar(fatos_solicitante or 'nenhum'))}\n</fatos_do_solicitante>\n"
            "<contexto_institucional>\n" + "\n".join(blocos) + "\n</contexto_institucional>"
        )
        return [{"role": "system", "content": prompt["texto"]}, {"role": "user", "content": usuario}], prompt

    def gerar(self, pergunta, trechos, fatos_solicitante=None, orcamento=None, conversar_fn=None, **_):
        from .llm_json import chamar_json, formato_resposta

        mensagens, prompt = self.montar_mensagens(pergunta, trechos, fatos_solicitante)
        saida = chamar_json(
            mensagens,
            validar_resposta_rag,
            self.perfil,
            orcamento=orcamento,
            conversar_fn=conversar_fn,
            response_format=formato_resposta("rag_resposta_v1", _schema_rag()),
        )
        meta_ultima = saida["tentativas"][-1]["metadados"]
        metadados = {
            "perfil": self.nome,
            "tipo": "llm",
            "e_llm": True,
            "provider": meta_ultima.get("provider"),
            "modelo": meta_ultima.get("modelo"),
            "tokens_entrada": sum((t["metadados"].get("tokens_entrada") or 0) for t in saida["tentativas"]) or INDISPONIVEL,
            "tokens_saida": sum((t["metadados"].get("tokens_saida") or 0) for t in saida["tentativas"]) or INDISPONIVEL,
            "custo_usd": meta_ultima.get("custo_usd") or INDISPONIVEL,
            "tentativas_json": len(saida["tentativas"]),
            "prompt": prompt["arquivo"],
            "prompt_sha256": prompt["sha256"],
        }
        if not saida["valido"]:
            return {
                "status_sugerido": "sem_evidencia_suficiente",
                "resposta": "",
                "afirmacoes": [],
                "divergencias": [],
                "erro_validacao": [e for t in saida["tentativas"] for e in t["erros"]],
                "metadados": metadados,
            }
        obj = saida["resultado"]["objeto"]
        return {
            "status_sugerido": obj["status"],
            "resposta": obj["resposta"],
            "afirmacoes": obj["afirmacoes"],
            "divergencias": obj["divergencias"],
            "metadados": metadados,
        }


def criar_gerador(cfg: dict, nome: str | None = None):
    g = cfg["geracao"]
    nome = nome or g["perfil_ativo"]
    if nome not in g["perfis"]:
        raise ValueError(f"Perfil de geração desconhecido: {nome}")
    perfil = g["perfis"][nome]
    tipo = perfil["tipo"]
    if tipo == "llm":
        return GeradorLLM(nome, perfil)
    if tipo == "extrativo":
        return GeradorExtrativo(nome, perfil)
    if tipo == "mock":
        return GeradorMock(nome, perfil)
    raise ValueError("Tipo de gerador desconhecido: " + tipo)
