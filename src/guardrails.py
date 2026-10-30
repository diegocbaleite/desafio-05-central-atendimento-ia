"""Guardrails em camadas (RF16): entrada, conteúdo recuperado e saída.

Nenhuma camada é suficiente sozinha. A proteção combina: (1) regras documentadas de
entrada; (2) separação estrutural — segredos NUNCA entram no prompt e o contexto é
delimitado como dado; (3) quarentena de trechos suspeitos do acervo; (4) validação de
esquema e de citações na saída; (5) filtro de segredos/dados pessoais na saída;
(6) limites de tamanho, chamadas e tokens; (7) revisão humana obrigatória.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from .seguranca import detectar, minimizar
from .texto import termos

DECISOES = ("permitir", "revisar", "bloquear")
_ORDEM = {d: i for i, d in enumerate(DECISOES)}

# Radicais (src.texto.raiz) do vocabulário de atendimento da secretaria fictícia.
VOCABULARIO_ESCOPO = {
    "matri", "docum", "certi", "decla", "proto", "atend", "agend", "solic", "curso",
    "escol", "secre", "recla", "cadas", "prazo", "segun", "trans", "turno", "ouvid",
    "andam", "aula", "falta", "tranc", "inscr", "pedid", "respo", "manif", "servi",
    "histo", "ficha", "cance", "remar", "porta", "regis", "dado", "priva", "elimi",
    "cidad", "orien", "estud", "tecni", "conta",
}
_INJECAO_EXTRA = [
    r"a partir de agora",
    r"voc[eê] agora [ée]",
    r"novas? instru[cç][oõ]es",
    r"modo (?:desenvolvedor|developer|admin)",
    r"instru[cç][aã]o para o assistente",
    r"(?:assistente|modelo) de ia\s*:",
    r"aja como",
    r"todos os pedidos est[aã]o deferidos",
]
_PEDIDO_SEGREDO = re.compile(
    r"(?:informe|mostre|revele|diga|passe|exiba|liste|imprima|envie|qual (?:[ée]|o valor))"
    r".{0,80}(?:chave|api[ _-]?key|token|senha|segredo|credencia|vari[aá]vel de ambiente|\.env"
    r"|prompt (?:de|do) sistema|system prompt|instru[cç][oõ]es internas)",
    re.IGNORECASE | re.DOTALL,
)
_NOME_VARIAVEL_SECRETA = re.compile(r"\b[A-Z][A-Z0-9_]{2,}_(?:KEY|TOKEN|SECRET|SENHA|DEMO)\b")
_INSULTOS = re.compile(r"\b(idiota|imbecil|vagabund[oa]s?|incompetentes?|lixo)\b", re.IGNORECASE)
_AMEACAS = re.compile(
    r"\b(vou (?:matar|quebrar|explodir|agredir)|ameaço|amea[cç]a de morte)\b", re.IGNORECASE
)
_PADROES_CHAVE = [
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
    re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"\bgsk_[A-Za-z0-9]{16,}"),
    re.compile(r"\bCANARIO-[0-9a-f]{8,}\b"),
]


def _motivo(codigo, camada, decisao, detalhe):
    return {"codigo": codigo, "camada": camada, "decisao": decisao, "detalhe": detalhe}


def _decidir(motivos: list[dict]) -> str:
    if not motivos:
        return "permitir"
    return max((m["decisao"] for m in motivos), key=_ORDEM.__getitem__)


def sinais_injecao(texto: str) -> list[str]:
    achados = list(detectar(texto))
    achados += [p for p in _INJECAO_EXTRA if re.search(p, texto, re.IGNORECASE)]
    return achados


def pede_segredo(texto: str) -> bool:
    return bool(_PEDIDO_SEGREDO.search(texto) or _NOME_VARIAVEL_SECRETA.search(texto))


def avaliar_entrada(texto: str, cfg: dict, similaridade_acervo: float | None = None) -> dict:
    """Decisão permitir/revisar/bloquear para uma solicitação ou pergunta."""
    g = cfg.get("guardrails", {})
    limite = int(g.get("max_caracteres_entrada", 4000))
    motivos = []
    texto = texto or ""
    if not texto.strip():
        motivos.append(_motivo("entrada_vazia", "entrada", "bloquear", "texto vazio"))
    if len(texto) > limite:
        motivos.append(
            _motivo("entrada_excessiva", "entrada", "bloquear", f"{len(texto)} > {limite} caracteres")
        )
    if pede_segredo(texto):
        motivos.append(
            _motivo("tentativa_obter_segredo", "entrada", "bloquear", "pedido de credencial, segredo ou prompt interno")
        )
    injecao = sinais_injecao(texto)
    if injecao:
        motivos.append(
            _motivo("instrucao_maliciosa", "entrada", "revisar", f"{len(injecao)} padrão(ões) de injeção")
        )
    if _AMEACAS.search(texto):
        motivos.append(_motivo("ameaca", "moderacao", "bloquear", "conteúdo ameaçador"))
    elif _INSULTOS.search(texto):
        motivos.append(_motivo("linguagem_ofensiva", "moderacao", "revisar", "insulto identificado"))
    termos_texto = set(termos(texto))
    no_escopo_lexico = bool(termos_texto & VOCABULARIO_ESCOPO)
    limiar = float(g.get("limiar_escopo_semantico", 0.35))
    no_escopo_semantico = similaridade_acervo is not None and similaridade_acervo >= limiar
    if texto.strip() and not (no_escopo_lexico or no_escopo_semantico):
        motivos.append(
            _motivo("fora_de_escopo", "escopo", "bloquear", "sem relação com os serviços de atendimento do acervo")
        )
    elif texto.strip() and len(termos_texto) < 2:
        motivos.append(_motivo("conteudo_insuficiente", "escopo", "revisar", "texto curto demais para análise"))
    return {
        "decisao": _decidir(motivos),
        "motivos": motivos,
        "sinais": {
            "escopo_lexico": no_escopo_lexico,
            "similaridade_acervo": similaridade_acervo,
            "padroes_injecao": len(injecao),
        },
    }


def validar_documento(nome: str, conteudo: bytes, cfg: dict) -> None:
    """Tipo, tamanho e assinatura de documento enviado ao acervo; lança ValueError."""
    g = cfg.get("guardrails", {})
    formatos = set(g.get("formatos_documento", [".txt", ".pdf"]))
    max_mb = float(g.get("max_mb_documento", 2))
    extensao = Path(nome).suffix.lower()
    if extensao not in formatos:
        raise ValueError(f"Formato não permitido: {extensao or '(sem extensão)'}")
    if not conteudo:
        raise ValueError("Arquivo vazio")
    if len(conteudo) > max_mb * 1024 * 1024:
        raise ValueError(f"Arquivo acima do limite de {max_mb:g} MiB")
    if extensao == ".pdf" and not conteudo.startswith(b"%PDF-"):
        raise ValueError("Arquivo sem assinatura PDF válida")
    if extensao == ".txt":
        try:
            conteudo.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("TXT precisa estar em UTF-8") from exc


def caminho_upload_seguro(pasta: Path, nome: str) -> Path:
    """Resolve um único nome de arquivo, sem permitir sair da pasta de uploads."""
    if (not nome or nome in (".", "..") or nome.endswith((".", " "))
            or re.search(r'[<>:"/\\|?*\x00-\x1f]', nome)):
        raise ValueError("Nome de arquivo inválido: informe somente o nome, sem caminhos")
    reservado = nome.split(".", 1)[0].upper()
    if reservado in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
                     *(f"LPT{i}" for i in range(1, 10))}:
        raise ValueError("Nome de arquivo reservado pelo sistema")
    base = Path(pasta).resolve()
    destino = (base / nome).resolve()
    if not destino.is_relative_to(base):
        raise ValueError("Destino do upload fora da pasta permitida")
    return destino


def destino_documento_enviado(pasta: Path, documento_id: str, extensao: str) -> Path:
    """ID do acervo não é caminho; o formato aceito é ASCII, até 64 caracteres."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", documento_id or ""):
        raise ValueError("ID inválido: use até 64 letras, números, hífen ou sublinhado")
    if extensao not in (".txt", ".pdf"):
        raise ValueError("Formato de documento não permitido")
    return caminho_upload_seguro(pasta, documento_id + extensao)


def avaliar_trecho(texto: str) -> dict:
    """Conteúdo do acervo é não confiável: instruções ou pedidos de segredo -> quarentena."""
    motivos = sinais_injecao(texto)
    if pede_segredo(texto) or re.search(r"revel\w+ .{0,40}chave", texto, re.IGNORECASE):
        motivos.append("pedido_de_segredo")
    return {"suspeito": bool(motivos), "motivos": motivos}


def segredos_conhecidos(cfg: dict) -> list[str]:
    """Valores de credenciais presentes no ambiente (para filtrar saídas e logs)."""
    nomes = [p.get("env_chave") for p in cfg.get("provedores", {}).values()]
    nomes += [p.get("env_conta") for p in cfg.get("provedores", {}).values()]
    nomes.append(cfg.get("guardrails", {}).get("segredo_env_demo", "SEGREDO_FICTICIO_DEMO"))
    valores = [os.getenv(n, "") for n in nomes if n]
    return [v for v in valores if len(v) >= 8]


def filtrar_saida(texto: str, cfg: dict) -> dict:
    """Bloqueia saída com segredo e mascara dados pessoais (CPF, e-mail, telefone)."""
    motivos = []
    for segredo in segredos_conhecidos(cfg):
        if segredo in texto:
            motivos.append("segredo_configurado_na_saida")
    if any(p.search(texto) for p in _PADROES_CHAVE):
        motivos.append("padrao_de_credencial_na_saida")
    if motivos:
        return {"texto": "[SAÍDA BLOQUEADA PELO GUARDRAIL DE SAÍDA]", "bloqueado": True, "motivos": motivos}
    mascarado = minimizar(texto)
    if mascarado != texto:
        motivos.append("dados_pessoais_mascarados")
    if re.search(r"\bdeferid[oa]s?\b", texto, re.IGNORECASE):
        motivos.append("afirma_deferimento_revisar")
    return {"texto": mascarado, "bloqueado": False, "motivos": motivos}
