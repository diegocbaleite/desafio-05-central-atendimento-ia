"""Ficha de compreensão (RF15): resumo, categoria e entidades, sem completar lacunas.

O caminho padrão é local e determinístico (regras), portanto NÃO é IA generativa; o
caminho `resumir_llm` usa o provedor configurado e passa pelas mesmas verificações.
"""

from __future__ import annotations

import re

from .extracao import CATEGORIAS as TERMOS_CATEGORIA
from .seguranca import AUSENTE, minimizar
from .texto import contar_palavras, frases, normalizar, numeros

LIMITE_RESUMO = 100
_NOME = r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-zà-ÿA-ZÁÉÍÓÚÂÊÔÃÕÇ]+"
_CONECTOR = r"(?:de|da|do|dos|das|e|DE|DA|DO|DOS|DAS|E)"
_NOME_COMPLETO = _NOME + r"(?:[ \t]+(?:" + _CONECTOR + r"[ \t]+)?" + _NOME + r"){1,6}"
_GATILHOS_PESSOA = re.compile(
    r"(?:meu nome [ée]|^[ \t]*nome[ \t]*:|nome da (?:minha )?m[ãa]e(?:[ \t]*[ée]|,)?"
    r"|atenciosamente,?[ \t]*\n)[ \t]*(?P<nome>(?-i:" + _NOME_COMPLETO + r"))",
    re.IGNORECASE | re.MULTILINE,
)
_ORGAOS = [
    re.compile(r"\bEscola T[ée]cnica Estadual de " + _NOME + r"(?:[ \t]+" + _NOME + r")*"),
    re.compile(
        r"\bSecretaria(?:[ \t]+(?:de|da|do)[ \t]+Estado)?(?:[ \t]+(?:de|da|do|dos|das))?"
        r"[ \t]+" + _NOME + r"(?:[ \t]+(?:" + _CONECTOR + r"[ \t]+)?" + _NOME + r")*"
    ),
    re.compile(r"\bOuvidoria(?:[ \t]+" + _NOME + r")*"),
    re.compile(r"\b(?:SECITECI|SEDUC|DETRAN|ETEC)(?:[-/]MT)?\b"),
]
_LOCAIS = (
    "Cuiabá", "Várzea Grande", "Rondonópolis", "Sinop", "Tangará da Serra",
    "Cáceres", "Barra do Garças", "Primavera do Leste", "Mato Grosso",
)
_PROTOCOLO = re.compile(r"\b(20\d{2})\s*([.-])\s*(\d{3})[-.\s]?\s*(\d{3})\b")
_DATA = re.compile(r"\b(\d{2})/(\d{2})/(\d{4})\b")
_DATA_EXTENSO = re.compile(
    r"\b(\d{1,2})\s+de\s+(janeiro|fevereiro|março|marco|abril|maio|junho|julho|agosto|"
    r"setembro|outubro|novembro|dezembro)\s+de\s+(\d{4})\b",
    re.IGNORECASE,
)
_MESES = {
    "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3, "abril": 4, "maio": 5,
    "junho": 6, "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10,
    "novembro": 11, "dezembro": 12,
}
_MILHAR_COM_UNIDADE = re.compile(
    r"(?<![\d.,])\d{1,3}(?:\.\d{3})+(?=(?:,\d+)?\s*"
    r"(?:horas?|dias?|meses|anos?|reais|unidades?|vagas?|alunos?|pessoas?)\b)",
    re.IGNORECASE,
)


def _adicionar(lista, vistos, tipo, valor, evidencia):
    chave = (tipo, normalizar(valor))
    if chave not in vistos:
        vistos.add(chave)
        lista.append({"tipo": tipo, "valor": valor, "literal": True, "evidencia": evidencia})


def extrair_entidades(texto: str) -> list[dict]:
    """Somente entidades presentes literalmente; cada uma traz o trecho de evidência."""
    entidades: list[dict] = []
    vistos: set = set()
    for m in _GATILHOS_PESSOA.finditer(texto):
        _adicionar(entidades, vistos, "pessoa", m.group("nome").strip(), m.group(0).strip())
    faixas_orgao = []
    for padrao in _ORGAOS:
        for m in padrao.finditer(texto):
            faixas_orgao.append((m.start(), m.end()))
            _adicionar(entidades, vistos, "orgao", m.group(0).strip(), m.group(0).strip())
    for local in _LOCAIS:
        for m in re.finditer(r"\b" + re.escape(local) + r"\b", texto, re.IGNORECASE):
            if any(a <= m.start() < b for a, b in faixas_orgao):
                continue  # convenção do gabarito: local dentro do nome do órgão não conta
            _adicionar(entidades, vistos, "local", local, m.group(0))
    for m in _DATA.finditer(texto):
        dia, mes, ano = (int(g) for g in m.groups())
        if 1 <= dia <= 31 and 1 <= mes <= 12:
            _adicionar(entidades, vistos, "data", m.group(0), m.group(0))
    for m in _DATA_EXTENSO.finditer(texto):
        valor = f"{int(m.group(1)):02d}/{_MESES[m.group(2).lower()]:02d}/{m.group(3)}"
        _adicionar(entidades, vistos, "data", valor, m.group(0))
    for m in _PROTOCOLO.finditer(texto):
        valor = f"{m.group(1)}{m.group(2)}{m.group(3)}{m.group(4)}"
        _adicionar(entidades, vistos, "protocolo", valor, m.group(0))
    return entidades


def categorizar(pedido: str | None, texto: str) -> tuple[str, str]:
    """Categoria documentada; sem pedido identificável -> 'revisao' (não adivinhar)."""
    if not pedido:
        return "revisao", "Nenhum pedido identificável no texto; exige leitura humana."
    for base, origem in ((pedido, "pedido"), (texto, "texto completo")):
        baixo = base.lower()
        for categoria, termos_ in TERMOS_CATEGORIA.items():
            achado = next((t for t in termos_ if t in baixo), None)
            if achado:
                return categoria, f"Termo '{achado}' encontrado no {origem}."
    return "outros", "Pedido identificado, mas sem termo de categoria documentada."


def resumir_local(texto: str, ficha: dict) -> str:
    """Resumo extrativo (não-LLM) com no máximo 100 palavras e sem dados pessoais extras."""
    partes = [
        f"Solicitante: {ficha.get('solicitante') or AUSENTE}.",
        f"Protocolo: {ficha.get('protocolo') or AUSENTE}.",
        f"Data: {ficha.get('data') or AUSENTE}.",
        f"Assunto: {ficha.get('assunto') or AUSENTE}.",
    ]
    if ficha.get("pedido"):
        partes.append("Pedido: " + ficha["pedido"].rstrip(".") + ".")
    else:
        corpo = [f for f in frases(minimizar(texto)) if contar_palavras(f) > 3]
        partes.append("Pedido não identificado. Trecho original: " + " ".join(corpo[:2]))
    resumo = " ".join(partes)
    palavras = resumo.split()
    if len(palavras) > LIMITE_RESUMO:
        resumo = " ".join(palavras[: LIMITE_RESUMO - 1]) + " […]"
    return resumo


def fatos_sem_suporte(resumo: str, original: str) -> list[str]:
    """Números/datas do resumo ausentes do original (indício de invenção).

    Datas normalizadas a partir de datas por extenso do original ("14 de outubro de
    2026" -> 14/10/2026) contam como suportadas.
    """
    datas_original = {e["valor"] for e in extrair_entidades(original) if e["tipo"] == "data"}
    sem_datas_suportadas = _DATA.sub(lambda m: "" if m.group(0) in datas_original else m.group(0), resumo)
    # Quantidades em português podem usar ponto de milhar: 1.200 horas = 1200 horas.
    # Restringe a equivalência a números com unidade; protocolos/versões não mudam.
    sem_milhar = lambda t: _MILHAR_COM_UNIDADE.sub(lambda m: m.group(0).replace(".", ""), t)
    base = set(numeros(sem_milhar(original)))
    return sorted(n for n in numeros(sem_milhar(sem_datas_suportadas)) if n not in base)


def compreender(texto: str, ficha: dict, resumo: str | None = None, metodo="extrativo_local") -> dict:
    resumo = resumo if resumo is not None else resumir_local(texto, ficha)
    inferencias = []
    if ficha.get("categoria"):
        inferencias.append(
            {"campo": "categoria", "valor": ficha["categoria"], "base": "classificação por termos documentados"}
        )
    if ficha.get("assunto") and not re.search(r"(?im)^\s*assunto\s*:", texto):
        inferencias.append(
            {"campo": "assunto", "valor": ficha["assunto"], "base": "derivado do pedido; não rotulado no original"}
        )
    return {
        "resumo": resumo,
        "palavras": contar_palavras(resumo),
        "limite_palavras": LIMITE_RESUMO,
        "metodo_resumo": metodo,
        "categoria": ficha.get("categoria"),
        "entidades_literais": [e for e in ficha.get("entidades", []) if e["literal"]],
        "inferencias": inferencias,
        "fatos_sem_suporte": fatos_sem_suporte(resumo, texto),
    }


def resumir_llm(texto: str, ficha: dict, perfil: dict, orcamento=None, conversar_fn=None) -> tuple[str, dict]:
    """Resumo por LLM; o chamador ainda confere limite de palavras e fatos sem suporte."""
    from .cliente import conversar
    from .prompts import carregar_prompt
    from .seguranca import delimitar

    conversar_fn = conversar_fn or conversar
    prompt = carregar_prompt("resumo_v1")
    resposta = conversar_fn(
        [
            {"role": "system", "content": prompt["texto"]},
            {"role": "user", "content": delimitar(minimizar(texto))},
        ],
        modelo=perfil.get("modelo"),
        provider=perfil.get("provider"),
        orcamento=orcamento,
        parametros={"temperatura": perfil.get("temperatura"), "max_tokens": perfil.get("max_tokens")},
    )
    resumo = resposta["texto"].strip()
    palavras = resumo.split()
    if len(palavras) > LIMITE_RESUMO:
        resumo = " ".join(palavras[: LIMITE_RESUMO - 1]) + " […]"
    meta = {k: v for k, v in resposta.items() if k != "texto"}
    meta.update({"prompt": prompt["arquivo"], "prompt_sha256": prompt["sha256"]})
    return resumo, meta


def _tem_termo(texto: str, termos_alternativos) -> bool:
    base = normalizar(texto)
    return any(normalizar(t) in base for t in termos_alternativos)


def avaliar_solicitacao(sid: str, ficha: dict, compreensao: dict, gab: dict, original: str) -> dict:
    """Compara ficha e resumo com o gabarito prévio; registra omissões e erros."""
    campos = {}
    for campo in ("protocolo", "data", "solicitante"):
        esperado, obtido = gab.get(campo), ficha.get(campo)
        campos[campo] = {
            "esperado": esperado,
            "obtido": obtido,
            "ok": (esperado is None and obtido is None)
            or (esperado is not None and obtido is not None and normalizar(esperado) == normalizar(obtido)),
        }
    entidades = {}
    for tipo, esperados in gab.get("entidades", {}).items():
        esp = {normalizar(v) for v in esperados}
        obt = {normalizar(e["valor"]) for e in ficha.get("entidades", []) if e["tipo"] == tipo}
        entidades[tipo] = {
            "corretas": sorted(esp & obt),
            "omitidas": sorted(esp - obt),
            "incorretas": sorted(obt - esp),
        }
    fatos = [
        {"fato": f["fato"], "presente": _tem_termo(compreensao["resumo"], f["termos"])}
        for f in gab.get("fatos_essenciais", [])
    ]
    total_esp = sum(len(v) for v in gab.get("entidades", {}).values())
    corretas = sum(len(v["corretas"]) for v in entidades.values())
    incorretas = sum(len(v["incorretas"]) for v in entidades.values())
    return {
        "id": sid,
        "categoria_esperada": gab["categoria"],
        "categoria_obtida": ficha.get("categoria"),
        "categoria_ok": ficha.get("categoria") == gab["categoria"],
        "campos": campos,
        "campos_ausentes_ok": set(ficha.get("campos_ausentes", [])) == set(gab.get("campos_ausentes", [])),
        "entidades": entidades,
        "entidades_corretas": corretas,
        "entidades_esperadas": total_esp,
        "entidades_incorretas": incorretas,
        "fatos": fatos,
        "fatos_omitidos": [f["fato"] for f in fatos if not f["presente"]],
        "fatos_sem_suporte": compreensao["fatos_sem_suporte"],
        "resumo_palavras": compreensao["palavras"],
        "resumo_dentro_limite": compreensao["palavras"] <= LIMITE_RESUMO,
    }
