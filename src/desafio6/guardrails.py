"""Limites e política conservadora; complementados por esquema e verificação de fontes."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from src.seguranca import detectar, minimizar

MAX_CARACTERES = 12000
MAX_ARQUIVO_BYTES = 2 * 1024 * 1024
TERMOS_ESCOPO = (
    "atendimento", "agend", "matr", "document", "secretaria", "protocolo",
    "cadastro", "certid", "solicit", "pedido", "processo", "curso", "inscri",
    "horário", "horario", "cidad", "canal", "comprovante", "cancel", "serviço",
    "servico", "reclama", "avalia", "segunda via", "triagem", "correção", "correcao",
    "consult", "andamento", "vaga", "edital", "retifica", "sele", "técnic", "tecnic",
    "escola", "cronograma", "classifica", "cota", "certifica", "etec", "unidade",
)
SEGREDOS = re.compile(
    r"\bsk-[A-Za-z0-9_-]{10,}|\b(?:OPENAI_API_KEY|api_key|senha|token|segredo)\s*[:=]\s*[^\s,;]+",
    re.IGNORECASE,
)
ATAQUE = re.compile(
    r"ignore.{0,70}(?:instru|regra)|desconsidere.{0,70}(?:instru|regra)|"
    r"(?:revele|mostrar|mostre|imprima|obtenha|retorne|qual).{0,70}(?:segredo|senha|api.?key|token|credencial)|"
    r"(?:envie|enviar|execute|executar).{0,70}(?:email|e-mail|whatsapp|comando)|"
    r"(?:system|developer|assistant)\s*:|</?(?:system|developer|conteudo_externo)",
    re.IGNORECASE | re.DOTALL,
)


def avaliar_entrada(texto: str, *, contexto: bool = False) -> dict:
    """Regras de moderação acadêmicas: permitir, bloquear ou encaminhar para revisão.

    Não é serviço de moderação nem garantia contra toda injeção. Nenhum conteúdo
    externo ganha ferramentas ou papel de sistema. As demais camadas validam os dados.
    """
    if not isinstance(texto, str) or not texto.strip():
        return {"decisao": "bloquear", "motivos": ["entrada_vazia_ou_tipo_invalido"]}
    if len(texto) > MAX_CARACTERES:
        return {"decisao": "bloquear", "motivos": ["limite_caracteres"]}
    if "\x00" in texto:
        return {"decisao": "bloquear", "motivos": ["caractere_binario"]}
    if SEGREDOS.search(texto):
        return {"decisao": "bloquear", "motivos": ["possivel_credencial"]}
    if detectar(texto) or ATAQUE.search(texto):
        return {"decisao": "revisar", "motivos": ["instrucao_externa_ou_pedido_de_segredo"]}
    if not contexto and not any(t in texto.casefold() for t in TERMOS_ESCOPO):
        return {"decisao": "revisar", "motivos": ["escopo_nao_identificado"]}
    return {"decisao": "permitir", "motivos": []}


def validar_saida(texto: str) -> dict:
    if not isinstance(texto, str) or not texto.strip():
        return {"decisao": "bloquear", "motivos": ["saida_vazia"]}
    if SEGREDOS.search(texto) or minimizar(texto) != texto:
        return {"decisao": "bloquear", "motivos": ["dado_indevido_na_saida"]}
    if re.search(r"\b(?:enviado automaticamente|deferimento confirmado|protocolo real emitido)\b", texto, re.I):
        return {"decisao": "bloquear", "motivos": ["acao_oficial_indevida"]}
    return {"decisao": "permitir", "motivos": []}


def validar_documento(caminho: str | Path) -> Path:
    p = Path(caminho).resolve()
    if not p.is_file() or p.suffix.lower() not in {".txt", ".pdf"}:
        raise ValueError("Acervo aceita somente TXT e PDF textual")
    if not 0 < p.stat().st_size <= MAX_ARQUIVO_BYTES:
        raise ValueError("Documento vazio ou acima do limite de 2 MiB")
    with p.open("rb") as arquivo:
        inicio = arquivo.read(5)
    if p.suffix.lower() == ".pdf" and inicio != b"%PDF-":
        raise ValueError("Assinatura PDF inválida")
    return p


def sanitizar(texto: str) -> str:
    """Consulta minimizada para log; documentos/saídas têm armazenamento separado."""
    texto = SEGREDOS.sub("[CREDENCIAL]", str(texto))
    texto = minimizar(texto)
    texto = re.sub(r"\b\d{4}[-. ]\d{3}[-. ]?\d{3}\b", "[PROTOCOLO]", texto)
    texto = re.sub(r"(?im)^\s*(?:nome|solicitante)\s*:[^\n]+", "Solicitante: [IDENTIFICADOR]", texto)
    return texto[:500]


def hash_texto(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()
