"""Inclusão de documentos com texto conferido, STT/OCR e origem preservada."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from uuid import uuid4

import yaml

from . import guardrails
from .config import ROOT
from .seguranca import FORMATOS_AUDIO


def extrair_documento(nome: str, conteudo: bytes, cfg: dict, *, local=False) -> dict:
    """Extrai todas as páginas; nunca salva nem indexa uma extração sem conferência."""
    guardrails.validar_documento(nome, conteudo, cfg)
    extensao = Path(nome).suffix.lower()
    paginas, metodos = [], []
    mm = cfg.get("multimodal", {})
    with tempfile.TemporaryDirectory(prefix="acervo_entrada_") as temporaria:
        entrada = Path(temporaria) / ("entrada" + extensao)
        entrada.write_bytes(conteudo)
        if extensao == ".txt":
            paginas = [{"pagina": None, "texto": conteudo.decode("utf-8")}]
            metodos = ["leitura TXT"]
        elif extensao in FORMATOS_AUDIO:
            from .audio import transcrever

            provider = "local" if local else mm.get("stt_provider", "local")
            paginas = [{"pagina": None, "texto": transcrever(entrada, provider=provider)}]
            metodos = [f"STT:{provider}"]
        elif extensao == ".pdf":
            from pypdf import PdfReader
            from .visao import _imagens_pdf, ler_imagem

            try:
                pdf = PdfReader(entrada)
                if pdf.is_encrypted:
                    raise ValueError("PDF protegido por senha não é aceito")
                quantidade = len(pdf.pages)
                limite = int(cfg.get("guardrails", {}).get("max_paginas_pdf_documento", 10))
                if not 1 <= quantidade <= limite:
                    raise ValueError(f"PDF deve ter entre 1 e {limite} páginas; nenhuma página foi processada")
                textos = [pagina.extract_text() or "" for pagina in pdf.pages]
            except ValueError:
                raise
            except Exception:
                raise ValueError("PDF inválido ou ilegível") from None
            provider = "local" if local else mm.get("ocr_provider", "local")
            for n, texto in enumerate(textos, 1):
                if texto.strip():
                    metodo = "texto PDF"
                else:
                    pasta_pagina = Path(temporaria) / f"pagina_{n}"
                    pasta_pagina.mkdir()
                    imagens = _imagens_pdf(entrada, pasta_pagina, 1, pagina_inicial=n)
                    texto = ler_imagem(imagens[0], provider=provider, modelo=mm.get("ocr_modelo"))
                    metodo = f"OCR:{provider}"
                paginas.append({"pagina": n, "texto": texto})
                metodos.append(metodo)
    if (any(not isinstance(p["texto"], str) for p in paginas)
            or not any(p["texto"].strip() for p in paginas)):
        raise ValueError("Nenhum texto foi extraído; documento não foi salvo")
    if guardrails.contem_segredo(paginas, cfg):
        raise ValueError("Extração bloqueada: possível credencial no conteúdo")
    return {"nome": Path(nome).name, "sha256_original": hashlib.sha256(conteudo).hexdigest(),
            "formato": extensao.lstrip("."), "paginas": paginas, "metodos": metodos}


def salvar_documento(preparado: dict, conteudo: bytes, paginas: list[dict], *,
                     documento_id: str, titulo: str, versao: str, tema: str,
                     conferido: bool, cfg: dict) -> dict:
    """Salva original e texto conferido com catálogo; recusa sobrescritas e texto obsoleto."""
    from .ingestao import carregar_catalogo

    if not conferido:
        raise ValueError("Confira o texto extraído antes de salvar no acervo")
    if hashlib.sha256(conteudo).hexdigest() != preparado["sha256_original"]:
        raise ValueError("Arquivo mudou; extraia e confira o texto novamente")
    if not titulo.strip() or not versao.strip():
        raise ValueError("Informe título e versão")
    if any(d["id"] == documento_id for d in carregar_catalogo(cfg)):
        raise ValueError("ID já existe no acervo; informe um ID único")
    if ([p.get("pagina") for p in paginas] != [p["pagina"] for p in preparado["paginas"]]
            or any(not isinstance(p.get("texto"), str) for p in paginas)
            or not any(p["texto"].strip() for p in paginas)):
        raise ValueError("Preserve as páginas e informe texto não vazio")
    if guardrails.contem_segredo([paginas, titulo, documento_id, versao, tema], cfg):
        raise ValueError("Documento bloqueado: possível credencial no conteúdo")
    guardrails.validar_documento(preparado["nome"], conteudo, cfg)
    pasta = ROOT / cfg["acervo"]["diretorio_enviados"]
    original = guardrails.caminho_upload_seguro(pasta, documento_id + "." + preparado["formato"])
    # O ID é validado pelo mesmo contrato dos uploads textuais.
    guardrails.destino_documento_enviado(pasta, documento_id, ".txt")
    derivado = guardrails.caminho_upload_seguro(pasta, documento_id + ".texto.json")
    dados_texto = {"versao": 1, "sha256_original": preparado["sha256_original"], "paginas": paginas}
    bruto = json.dumps(dados_texto, ensure_ascii=False, indent=2).encode("utf-8")
    relativo = lambda p: p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else p.as_posix()
    item = {"id": documento_id, "titulo": titulo.strip(), "versao": versao.strip(), "tema": tema.strip(),
            "formato": preparado["formato"], "arquivo": relativo(original), "texto_extraido": relativo(derivado),
            "sha256_texto_extraido": hashlib.sha256(bruto).hexdigest(),
            "metodos_extracao": preparado["metodos"], "texto_conferido": True,
            "prioridade": 1, "substitui": []}
    catalogo = ROOT / cfg["acervo"]["catalogo_enviados"]
    dados = yaml.safe_load(catalogo.read_text(encoding="utf-8")) if catalogo.is_file() else {}
    dados = dados or {"documentos": []}
    dados.setdefault("documentos", []).append(item)
    pasta.mkdir(parents=True, exist_ok=True)
    catalogo.parent.mkdir(parents=True, exist_ok=True)
    temporario_catalogo = catalogo.with_name(catalogo.name + "." + uuid4().hex + ".tmp")
    criados = []
    try:
        for caminho, valor in ((original, conteudo), (derivado, bruto)):
            with caminho.open("xb") as arquivo:
                criados.append(caminho)
                arquivo.write(valor)
        temporario_catalogo.write_text(yaml.safe_dump(dados, allow_unicode=True, sort_keys=False), encoding="utf-8")
        temporario_catalogo.replace(catalogo)
    except Exception:
        for caminho in criados:
            caminho.unlink(missing_ok=True)
        raise
    finally:
        temporario_catalogo.unlink(missing_ok=True)
    return item
