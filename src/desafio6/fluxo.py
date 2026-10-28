"""Coordenação do Desafio 6, reutilizando entrada, segurança e revisão do projeto."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from src.config import ROOT, carregar

from .contratos import VERSAO_SCHEMA
from .guardrails import avaliar_entrada, hash_texto, sanitizar, validar_saida
from .indice import IndiceDesatualizado, IndiceVetorial
from .nlp import analisar_solicitacao
from .rag import VERSAO_PROMPT, responder
from .revisao import RepositorioRevisoes
from .servicos import ClienteOpenAI, Orcamento

CATALOGO = ROOT / "dados/desafio6/acervo/catalogo.json"


class FluxoDesafio6:
    def __init__(self, cliente=None, pasta=None):
        self.cliente = cliente or ClienteOpenAI()
        self.pasta = Path(pasta or ROOT / "resultados/desafio6" / (
            "simulado" if self.cliente.simulado else "real"
        )).resolve()
        self.pasta.mkdir(parents=True, exist_ok=True)
        cfg = carregar().get("desafio6", {}).get("chunking", {})
        self.indice = IndiceVetorial(self.pasta / "indice", self.cliente,
                                    tamanho_chunk=cfg.get("tamanho", 90),
                                    sobreposicao=cfg.get("sobreposicao", 20), top_k=cfg.get("top_k", 3))
        self.revisoes = RepositorioRevisoes(self.pasta / "revisoes")
        self.pasta_execucoes = self.indice.pasta / "execucoes"
        self.pasta_execucoes.mkdir(exist_ok=True)

    @property
    def catalogo(self):
        ativo = self.pasta / "catalogo_ativo.json"
        return ativo if ativo.exists() else CATALOGO

    def _iniciar(self):
        orc = self.cliente.orcamento
        self.cliente.orcamento = Orcamento(orc.max_chamadas, orc.max_tokens)
        self.cliente.chamadas.clear()
        self.cliente.saidas_estruturadas.clear()
        return uuid.uuid4().hex[:16], datetime.now(timezone.utc).isoformat()

    def _auditar(self, id_execucao, etapa, **dados):
        registro = {"id": id_execucao, "data_utc": datetime.now(timezone.utc).isoformat(),
                    "etapa": etapa, "simulada": self.cliente.simulado,
                    "versao_schema": VERSAO_SCHEMA, "versao_prompt": VERSAO_PROMPT,
                    "modelo_geracao": self.cliente.modelo,
                    "modelo_embeddings": self.cliente.modelo_embeddings, **dados}
        with (self.pasta / "auditoria.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False, default=str) + "\n")

    def _permitir(self, texto, id_execucao, *, contexto=False):
        protecao = avaliar_entrada(texto, contexto=contexto)
        if protecao["decisao"] != "permitir":
            self._auditar(id_execucao, "entrada_bloqueada", decisao=protecao["decisao"],
                          motivos=protecao["motivos"], sha256_entrada=hash_texto(str(texto)))
            raise ValueError("Entrada exige revisão: " + ", ".join(protecao["motivos"]))

    def indexar(self, catalogo=None, *, recriar=False):
        id_execucao, _ = self._iniciar()
        origem = catalogo or CATALOGO
        if isinstance(origem, (str, Path)):
            path = Path(origem).resolve()
            dados = json.loads(path.read_text(encoding="utf-8"))
            base = path.parent
        else:
            dados, base = origem, ROOT
        excluidos_path = self.pasta / "excluidos.json"
        excluidos = set(json.loads(excluidos_path.read_text(encoding="utf-8"))) if excluidos_path.exists() else set()
        documentos = []
        for item in dados["documentos"]:
            if item["id"] in excluidos:
                continue
            novo = dict(item)
            caminho = Path(novo["arquivo"])
            novo["arquivo"] = str(caminho if caminho.is_absolute() else (base / caminho).resolve())
            documentos.append(novo)
        try:
            resultado = self.indice.indexar({"documentos": documentos}, recriar=recriar)
        except Exception as exc:
            self._auditar(id_execucao, "falha_indexacao", erro=type(exc).__name__, chamadas=self.cliente.chamadas)
            raise
        ativo = self.pasta / "catalogo_ativo.json"
        ativo.write_text(json.dumps({"versao": "1.0", "documentos": documentos}, ensure_ascii=False, indent=2), encoding="utf-8")
        self._auditar(id_execucao, "indexacao", resultado=resultado, chamadas=self.cliente.chamadas,
                      orcamento=self.cliente.orcamento.resumo())
        return resultado

    def _gravar_resultado(self, id_execucao, inicio, pergunta, resultado, analise=None):
        fontes_ids = sorted({f["documento_id"] for f in resultado.get("fontes", [])})
        recuperados = sorted({f["documento_id"] for f in resultado.get("trechos_recuperados", [])})
        # Também invalidar derivados que contêm trechos recuperados e não apenas citados.
        vinculados = sorted(set(fontes_ids + recuperados))
        minuta = resultado["resposta"]
        protecao = validar_saida(minuta)
        if protecao["decisao"] != "permitir":
            raise ValueError("Saída bloqueada pelos guardrails")
        registro = {"id": id_execucao, "inicio_utc": inicio,
                    "fim_utc": datetime.now(timezone.utc).isoformat(),
                    "consulta_minimizada": sanitizar(pergunta), "sha256_consulta": hash_texto(pergunta),
                    **resultado, "minuta": minuta, "trechos": resultado.get("trechos_recuperados", []),
                    "simulada": self.cliente.simulado, "estado": "pendente", "documentos": vinculados,
                    "versao_schema": VERSAO_SCHEMA, "modelo": self.cliente.modelo,
                    "chamadas": list(self.cliente.chamadas), "orcamento": self.cliente.orcamento.resumo()}
        registro["saidas_estruturadas"] = list(self.cliente.saidas_estruturadas)
        # O adapter RAG minimiza; para auditoria substituímos por máscara mais restrita.
        registro["consulta_minimizada"] = sanitizar(pergunta)
        if analise:
            registro.update({"ficha": analise["ficha"], "resumo": analise["resumo"],
                             "analise": analise, "categoria": analise["ficha"]["categoria"]})
        revisao = self.revisoes.salvar_minuta(id_execucao, minuta, simulada=self.cliente.simulado,
                                             documentos=vinculados,
                                             metadados={"status": resultado["status"], "fontes": fontes_ids,
                                                        "versao_schema": VERSAO_SCHEMA,
                                                        "versao_prompt": VERSAO_PROMPT,
                                                        "versao_indice": resultado["versao_indice"]})
        registro.update(revisao=revisao, sha256_minuta=revisao["sha256_minuta"])
        arquivo = self.pasta_execucoes / (id_execucao + ".json")
        arquivo.write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")
        self.indice.registrar_derivado(arquivo, vinculados)
        self._auditar(id_execucao, "resultado", inicio_utc=inicio,
                      consulta=sanitizar(pergunta), sha256_consulta=hash_texto(pergunta),
                      status=resultado["status"], ids_recuperados=[t["chunk_id"] for t in registro["trechos"]],
                      versao_indice=resultado["versao_indice"], arquivo=arquivo.name,
                      chamadas=self.cliente.chamadas, orcamento=self.cliente.orcamento.resumo())
        return registro

    def _responder(self, id_execucao, inicio, pergunta, analise=None, original=None):
        estado = self.indice.estado(self.catalogo)
        if estado["desatualizado"]:
            raise IndiceDesatualizado("Índice desatualizado; indexe o acervo antes de consultar")
        resultado = responder(pergunta, self.indice, self.cliente, solicitacao=analise, original=original)
        return self._gravar_resultado(id_execucao, inicio, pergunta, resultado, analise)

    def processar(self, texto, pergunta, *, modalidade="texto", conferencia=False):
        id_execucao, inicio = self._iniciar()
        self._permitir(texto, id_execucao)
        self._permitir(pergunta, id_execucao)
        try:
            analise = analisar_solicitacao(texto, self.cliente, modalidade=modalidade, conferencia=conferencia)
            if not analise["apta_para_minuta"]:
                raise PermissionError("Conferência humana dos dados STT/OCR necessária antes da minuta")
            return self._responder(id_execucao, inicio, pergunta, analise, original=texto)
        except Exception as exc:
            # Entrada permitida fica em área local separada, minimizada; erro sem payload.
            arquivo = self.pasta_execucoes / (id_execucao + "_bloqueio.json")
            arquivo.write_text(json.dumps({"id": id_execucao, "entrada": sanitizar(texto),
                                           "sha256_entrada": hash_texto(texto), "erro": type(exc).__name__,
                                           "decisao": "bloquear_minuta", "simulada": self.cliente.simulado},
                                          ensure_ascii=False, indent=2), encoding="utf-8")
            self._auditar(id_execucao, "falha_processamento", erro=type(exc).__name__,
                          decisao="bloquear_minuta", chamadas=self.cliente.chamadas)
            raise

    def consultar(self, pergunta):
        id_execucao, inicio = self._iniciar()
        self._permitir(pergunta, id_execucao)
        try:
            return self._responder(id_execucao, inicio, pergunta)
        except Exception as exc:
            self._auditar(id_execucao, "falha_consulta", erro=type(exc).__name__, chamadas=self.cliente.chamadas)
            raise

    def excluir(self, documento_id):
        id_execucao, _ = self._iniciar()
        resultado = self.indice.excluir(documento_id)
        resultado["revisoes_excluidas"] = self.revisoes.excluir_derivados(documento_id)
        arquivo = self.pasta / "excluidos.json"
        ids = set(json.loads(arquivo.read_text(encoding="utf-8"))) if arquivo.exists() else set()
        ids.add(documento_id)
        arquivo.write_text(json.dumps(sorted(ids)), encoding="utf-8")
        if self.catalogo != CATALOGO:
            dados = json.loads(self.catalogo.read_text(encoding="utf-8"))
            dados["documentos"] = [d for d in dados["documentos"] if d["id"] != documento_id]
            self.catalogo.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
        self._auditar(id_execucao, "exclusao", documento_id=documento_id, resultado=resultado)
        return resultado

    def extrair_midia(self, caminho, modalidade):
        """Reutiliza validadores/renderização; novo adaptador aplica orçamento e retries D6."""
        import tempfile
        from src.seguranca import FORMATOS_AUDIO, FORMATOS_IMAGEM, validar_arquivo
        from src.visao import _imagens_pdf
        if self.cliente.simulado:
            raise ValueError("Mídia não é reconhecida por simulação; use referências fictícias identificadas")
        if modalidade not in {"audio", "imagem", "ocr"}:
            raise ValueError("Modalidade de mídia inválida")
        id_execucao, inicio = self._iniciar()
        entrada = validar_arquivo(caminho, FORMATOS_AUDIO if modalidade == "audio" else FORMATOS_IMAGEM, 2)
        try:
            if modalidade == "audio":
                texto = self.cliente.transcrever(entrada)
            else:
                with tempfile.TemporaryDirectory(prefix="desafio6_ocr_") as temporaria:
                    imagens = _imagens_pdf(entrada, Path(temporaria), 3) if entrada.suffix.lower() == ".pdf" else [entrada]
                    texto = "\n\n".join(self.cliente.ler_pagina(p) for p in imagens)
            protecao = avaliar_entrada(texto)
            metadados = {"id": id_execucao, "inicio_utc": inicio, "modalidade": modalidade,
                         "modelo": self.cliente.chamadas[-1].get("modelo"),
                         "chamadas": self.cliente.chamadas, "orcamento": self.cliente.orcamento.resumo(),
                         "requer_conferencia_humana": True, "guardrails": protecao, "simulada": False}
            self._auditar(id_execucao, "extracao_midia", modalidade=modalidade,
                          sha256_texto=hash_texto(texto), decisao=protecao["decisao"], chamadas=self.cliente.chamadas)
            # Nunca salvar credenciais retornadas como texto reconhecido.
            if protecao["decisao"] == "bloquear":
                raise ValueError("Extração bloqueada pelos guardrails; conferir o original localmente")
            return {"texto": texto, "metadados": metadados}
        except Exception as exc:
            self._auditar(id_execucao, "falha_midia", erro=type(exc).__name__, chamadas=self.cliente.chamadas)
            raise

    def limpar_expirados(self, dias=30):
        """Expurgo explícito de artefatos locais; nunca percorre originais nem o .env."""
        from datetime import timedelta
        if type(dias) is not int or dias < 1:
            raise ValueError("Retenção exige quantidade positiva de dias")
        limite = (datetime.now(timezone.utc) - timedelta(days=dias)).timestamp()
        raiz = self.pasta.resolve()
        removidos = []
        # Inclui índice, consultas, uploads, avaliações e revisões. Logs de auditoria
        # guardam apenas IDs/horários/métricas e seguem retenção independente documentada.
        for nome in ("indice", "uploads", "entradas", "avaliacoes", "revisoes", "comparacao_chunking"):
            pasta = raiz / nome
            if not pasta.exists():
                continue
            candidatos = [p for p in pasta.rglob("*") if p.is_file() and p.stat().st_mtime < limite]
            # Verifica TODOS os destinos antes de remover qualquer arquivo.
            for p in candidatos:
                if p.is_symlink() or not p.resolve().is_relative_to(raiz):
                    raise ValueError("Destino de retenção fora da pasta local; operação bloqueada")
            for p in candidatos:
                p.unlink()
                removidos.append(p.relative_to(raiz).as_posix())
        for nome in ("sentimentos.json", "chunking.json", "catalogo_uploads.json"):
            p = raiz / nome
            if p.exists() and p.stat().st_mtime < limite:
                if p.is_symlink() or not p.resolve().is_relative_to(raiz):
                    raise ValueError("Destino inseguro de retenção")
                p.unlink()
                removidos.append(nome)
        self._auditar(uuid.uuid4().hex[:16], "retencao", dias=dias, arquivos_removidos=removidos)
        return {"retencao_dias": dias, "arquivos_removidos": removidos, "originais_preservados": True}
