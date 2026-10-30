"""Índice vetorial persistente de pequena escala, com SQLite e cosseno exato.

Vetores são embeddings do cliente selecionado. O SQLite armazena vetores e
metadados; o cálculo Python percorre os chunks e não é um índice ANN escalável.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path

from ..config import ROOT

VERSAO_INDICE = "sqlite-cosseno-v1"


class IndiceDesatualizado(ValueError):
    """A configuração ou fonte mudou: recriar explicitamente antes de consultar."""


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(valor):
    return json.dumps(valor, ensure_ascii=False, sort_keys=True)


def _cosseno(a, b):
    denominador = math.sqrt(sum(x * x for x in a) * sum(x * x for x in b))
    return sum(x * y for x, y in zip(a, b)) / denominador if denominador else 0.0


def _validar_vetor(vetor, dimensao):
    if not isinstance(vetor, list) or len(vetor) != dimensao:
        raise ValueError("Embedding com dimensão incompatível")
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in vetor):
        raise ValueError("Embedding inválido; esperado vetor numérico finito")
    if not any(vetor):
        raise ValueError("Embedding nulo não permite busca por cosseno")


def _paginas(path: Path):
    if path.suffix.lower() == ".txt":
        return [(None, path.read_text(encoding="utf-8"))]
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(path)
        if reader.is_encrypted:
            raise ValueError("PDF criptografado não suportado")
        if len(reader.pages) > 50:
            raise ValueError("PDF ultrapassa o limite de 50 páginas")
        paginas = [(n, pagina.extract_text() or "") for n, pagina in enumerate(reader.pages, 1)]
        if not any(texto.strip() for _, texto in paginas):
            raise ValueError("PDF sem texto; use o fluxo de OCR e confira a transcrição")
        return paginas
    raise ValueError("Acervo aceita apenas TXT ou PDF textual")


def _secoes(texto: str):
    secao, linhas = "não localizado", []
    for linha in texto.splitlines(keepends=True):
        if re.match(r"^\s*(?:#{1,6}\s+|Se[cç][aã]o(?:\s+\d+|\s*:)|\d+[.)]\s+)", linha, re.IGNORECASE):
            if "".join(linhas).strip():
                yield secao, "".join(linhas).strip()
            secao = linha.strip().lstrip("# ")
            linhas = [linha]
        else:
            linhas.append(linha)
    if "".join(linhas).strip():
        yield secao, "".join(linhas).strip()


def dividir_texto(texto: str, tamanho=90, sobreposicao=20):
    """Chunks por palavras, mantendo trechos literais e a sobreposição declarada."""
    if not isinstance(tamanho, int) or isinstance(tamanho, bool) or tamanho < 10:
        raise ValueError("Tamanho de chunk deve ser inteiro >= 10 palavras")
    if not isinstance(sobreposicao, int) or isinstance(sobreposicao, bool) or not 0 <= sobreposicao < tamanho:
        raise ValueError("Sobreposição deve estar entre zero e tamanho-1")
    palavras = list(re.finditer(r"\S+", texto))
    inicio = 0
    while inicio < len(palavras):
        fim = min(len(palavras), inicio + tamanho)
        yield texto[palavras[inicio].start():palavras[fim - 1].end()]
        if fim == len(palavras):
            break
        inicio = fim - sobreposicao


class IndiceVetorial:
    def __init__(self, pasta, cliente, *, tamanho_chunk=90, sobreposicao=20, top_k=3):
        # Valida a configuração mesmo quando o índice ainda está vazio.
        list(dividir_texto("", tamanho_chunk, sobreposicao))
        self.pasta = Path(pasta).resolve()
        self.pasta.mkdir(parents=True, exist_ok=True)
        self.cliente = cliente
        self.tamanho_chunk, self.sobreposicao = tamanho_chunk, sobreposicao
        if not isinstance(top_k, int) or isinstance(top_k, bool) or not 1 <= top_k <= 20:
            raise ValueError("top_k deve estar entre 1 e 20")
        self.top_k = top_k
        self.db = self.pasta / "indice.sqlite3"
        with self._conectar() as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS meta (chave TEXT PRIMARY KEY, valor TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS documentos (
                    id TEXT PRIMARY KEY, caminho TEXT NOT NULL, sha256 TEXT NOT NULL,
                    metadata TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY, documento_id TEXT NOT NULL REFERENCES documentos(id) ON DELETE CASCADE,
                    pagina INTEGER, secao TEXT NOT NULL, texto TEXT NOT NULL, vetor TEXT NOT NULL);
                CREATE INDEX IF NOT EXISTS chunks_documento ON chunks(documento_id);
                CREATE TABLE IF NOT EXISTS derivados (
                    caminho TEXT NOT NULL, documento_id TEXT NOT NULL,
                    PRIMARY KEY(caminho, documento_id));
            """)

    @contextmanager
    def _conectar(self):
        con = sqlite3.connect(self.db, timeout=10)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def _config(self):
        return {
            "versao_formato": VERSAO_INDICE,
            "modelo_embeddings": self.cliente.modelo_embeddings,
            "dimensao": self.cliente.dimensao,
            "simulado": bool(getattr(self.cliente, "simulado", False)),
            "tamanho_chunk": self.tamanho_chunk,
            "sobreposicao": self.sobreposicao,
            "unidade": "palavras",
        }

    def _meta(self, con):
        return {linha["chave"]: json.loads(linha["valor"]) for linha in con.execute("SELECT * FROM meta")}

    @staticmethod
    def _ler_catalogo(catalogo):
        if isinstance(catalogo, (str, Path)):
            path = Path(catalogo).resolve()
            dados = json.loads(path.read_text(encoding="utf-8"))
            base = path.parent
        else:
            dados, base = catalogo, ROOT
        documentos = dados.get("documentos") if isinstance(dados, dict) else dados
        if not isinstance(documentos, list) or not documentos:
            raise ValueError("Catálogo deve conter uma lista não vazia de documentos")
        vistos, saida = set(), []
        for item in documentos:
            if not isinstance(item, dict) or any(not isinstance(item.get(k), str) or not item[k].strip() for k in ("id", "titulo", "versao", "arquivo")):
                raise ValueError("Documento exige id, título, versão e arquivo")
            if item["id"] in vistos:
                raise ValueError("ID duplicado no catálogo")
            vistos.add(item["id"])
            relativo = Path(item["arquivo"])
            if ".." in relativo.parts:
                raise ValueError("Caminho de documento não pode conter ..")
            caminho = (base / relativo).resolve() if not relativo.is_absolute() else relativo.resolve()
            # Alguns chamadores usam arquivo relativo à raiz do projeto.
            if not caminho.is_file() and not relativo.is_absolute():
                caminho = (ROOT / relativo).resolve()
            if not caminho.is_file() or caminho.suffix.lower() not in {".txt", ".pdf"}:
                raise ValueError("Documento ausente ou formato não suportado")
            if item.get("arquivo_original"):
                original = Path(item["arquivo_original"])
                if not original.is_file() or _hash(original) != item.get("sha256_original"):
                    raise ValueError("Original alterado ou não localizado; reindexação necessária")
            if not 0 < caminho.stat().st_size <= 2 * 1024 * 1024:
                raise ValueError("Documento vazio ou acima de 2 MiB")
            if caminho.suffix.lower() == ".pdf" and not caminho.read_bytes().startswith(b"%PDF-"):
                raise ValueError("Assinatura PDF inválida")
            saida.append((item, caminho))
        return saida

    def indexar(self, catalogo, *, recriar=False):
        """Indexação transacional: falhas não substituem um índice válido anterior."""
        from .guardrails import avaliar_entrada

        documentos = self._ler_catalogo(catalogo)
        with self._conectar() as con:
            meta = self._meta(con)
            existente = {r["id"]: dict(r) for r in con.execute("SELECT * FROM documentos")}
        incompatibilidade = meta.get("configuracao") not in (None, self._config())
        if incompatibilidade and not recriar:
            raise IndiceDesatualizado("Modelo, dimensão ou chunking mudou; reindexe com recriar=True")
        if recriar:
            existente = {}
        novos, mantidos = [], 0
        for item, caminho in documentos:
            sha = _hash(caminho)
            registro = existente.get(item["id"])
            if registro and registro["sha256"] == sha and registro["metadata"] == _json(item):
                mantidos += 1
                continue
            chunks = []
            for pagina, texto in _paginas(caminho):
                if not texto.strip():
                    continue
                protecao = avaliar_entrada(texto, contexto=True)
                if protecao["decisao"] != "permitir":
                    raise ValueError("Documento bloqueado ou encaminhado à revisão pelos guardrails")
                for secao, trecho in _secoes(texto):
                    for pos, chunk in enumerate(dividir_texto(trecho, self.tamanho_chunk, self.sobreposicao)):
                        identificador = hashlib.sha256(_json([item["id"], item["versao"], sha, pagina, secao, pos, chunk, self._config()]).encode()).hexdigest()[:24]
                        chunks.append({"id": identificador, "pagina": pagina, "secao": secao, "texto": chunk})
            if not chunks:
                raise ValueError("Documento não contém texto indexável")
            novos.append((item, caminho, sha, chunks))
        # Um lote para todos os chunks novos: o orçamento contabiliza a chamada
        # inteira, e nenhum conteúdo é enviado antes de validar todo o acervo.
        todos_chunks = [chunk for _, _, _, chunks in novos for chunk in chunks]
        if todos_chunks:
            from src.seguranca import minimizar
            vetores = self.cliente.embeddings([minimizar(c["texto"]) for c in todos_chunks])
            if len(vetores) != len(todos_chunks):
                raise ValueError("Quantidade de embeddings difere dos chunks")
            for chunk, vetor in zip(todos_chunks, vetores):
                _validar_vetor(vetor, self.cliente.dimensao)
                chunk["vetor"] = vetor
        ids_catalogo = {item["id"] for item, _ in documentos}
        removidos = set(existente) - ids_catalogo
        mudou = bool(novos or removidos or recriar or not meta)
        with self._conectar() as con:
            if recriar:
                con.execute("DELETE FROM chunks")
                con.execute("DELETE FROM documentos")
            for doc_id in removidos:
                con.execute("DELETE FROM documentos WHERE id=?", (doc_id,))
            for item, caminho, sha, chunks in novos:
                con.execute("DELETE FROM documentos WHERE id=?", (item["id"],))
                con.execute("INSERT INTO documentos VALUES (?, ?, ?, ?)", (item["id"], str(caminho), sha, _json(item)))
                con.executemany("INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?)", [
                    (c["id"], item["id"], c["pagina"], c["secao"], c["texto"], _json(c["vetor"])) for c in chunks])
            if mudou:
                con.execute("INSERT OR REPLACE INTO meta VALUES ('versao', ?)", (_json(uuid.uuid4().hex),))
            con.execute("INSERT OR REPLACE INTO meta VALUES ('configuracao', ?)", (_json(self._config()),))
        return {**self.estado(), "documentos_atualizados": len(novos), "documentos_mantidos": mantidos, "documentos_removidos": len(removidos)}

    def estado(self, catalogo=None):
        with self._conectar() as con:
            meta = self._meta(con)
            documentos = [dict(r) for r in con.execute("SELECT * FROM documentos ORDER BY id")]
            quantidade = con.execute("SELECT count(*) FROM chunks").fetchone()[0]
        motivos = []
        if meta.get("configuracao") != self._config():
            motivos.append("configuração incompatível ou índice ainda não criado")
        for doc in documentos:
            path = Path(doc["caminho"])
            if not path.is_file() or _hash(path) != doc["sha256"]:
                motivos.append("fonte alterada ou removida: " + doc["id"])
            metadata = json.loads(doc["metadata"])
            if metadata.get("arquivo_original"):
                original = Path(metadata["arquivo_original"])
                if not original.is_file() or _hash(original) != metadata.get("sha256_original"):
                    motivos.append("original alterado ou removido: " + doc["id"])
        if catalogo is not None:
            try:
                atuais = {item["id"]: (_hash(path), _json(item)) for item, path in self._ler_catalogo(catalogo)}
                guardados = {d["id"]: (d["sha256"], d["metadata"]) for d in documentos}
                if atuais != guardados:
                    motivos.append("catálogo diferente do índice")
            except ValueError:
                motivos.append("catálogo inválido")
        return {"versao_indice": meta.get("versao"), "configuracao": meta.get("configuracao"),
                "simulado": bool(getattr(self.cliente, "simulado", False)),
                "documentos": len(documentos), "chunks": quantidade, "vazio": quantidade == 0,
                "desatualizado": bool(motivos), "motivos": motivos,
                "ids_documentos": [d["id"] for d in documentos],
                "similaridade": "cosseno: maior valor indica maior proximidade vetorial; não comprova suporte factual"}

    def _linhas(self):
        with self._conectar() as con:
            linhas = list(con.execute("""SELECT c.*, d.metadata, d.sha256 FROM chunks c
                JOIN documentos d ON c.documento_id=d.id"""))
        saida = []
        for linha in linhas:
            item = dict(linha)
            metadata = json.loads(item.pop("metadata"))
            item["vetor"] = json.loads(item["vetor"])
            item.update({"documento_id": metadata["id"], "titulo": metadata["titulo"],
                         "versao": metadata["versao"], "metadata": metadata,
                         "chunk_id": item["id"]})
            saida.append(item)
        return saida

    def buscar(self, pergunta, top_k=None):
        from .guardrails import avaliar_entrada

        if avaliar_entrada(pergunta)["decisao"] != "permitir":
            raise ValueError("Consulta bloqueada ou encaminhada à revisão pelos guardrails")
        estado = self.estado()
        if estado["desatualizado"]:
            raise IndiceDesatualizado("Índice desatualizado; reindexe antes de consultar")
        if estado["vazio"]:
            return []
        k = self.top_k if top_k is None else top_k
        if not isinstance(k, int) or isinstance(k, bool) or not 1 <= k <= 20:
            raise ValueError("top_k deve estar entre 1 e 20")
        vetor = self.cliente.embeddings([pergunta])[0]
        _validar_vetor(vetor, self.cliente.dimensao)
        saida = []
        for item in self._linhas():
            similaridade = _cosseno(vetor, item.pop("vetor"))
            item["similaridade"] = round(similaridade, 8)
            saida.append(item)
        return sorted(saida, key=lambda c: (-c["similaridade"], c["chunk_id"]))[:k]

    def completar_conflitos(self, trechos):
        grupos = {t["metadata"].get("grupo_politica", t["metadata"].get("conflito_grupo")) for t in trechos if t["metadata"].get("conflito")}
        grupos.discard(None)
        if not grupos:
            return trechos
        encontrados = {t["chunk_id"]: t for t in trechos}
        for item in self._linhas():
            grupo = item["metadata"].get("grupo_politica", item["metadata"].get("conflito_grupo"))
            if grupo in grupos:
                item.pop("vetor")
                item.setdefault("similaridade", None)
                encontrados.setdefault(item["chunk_id"], item)
        return list(encontrados.values())

    def texto_original(self, chunk_id):
        """Contexto completo da seção: um corte de chunk não define uma frase."""
        with self._conectar() as con:
            row = con.execute("""SELECT c.pagina, c.secao, c.texto, d.caminho, d.sha256, d.metadata
                FROM chunks c JOIN documentos d ON c.documento_id=d.id WHERE c.id=?""", (chunk_id,)).fetchone()
        if not row:
            raise ValueError("Chunk inexistente ao conferir passagem")
        path = Path(row["caminho"])
        if not path.is_file() or _hash(path) != row["sha256"]:
            raise IndiceDesatualizado("Fonte alterada antes da conferência da passagem")
        metadata = json.loads(row["metadata"])
        if metadata.get("arquivo_original"):
            original = Path(metadata["arquivo_original"])
            if not original.is_file() or _hash(original) != metadata.get("sha256_original"):
                raise IndiceDesatualizado("Original alterado antes da conferência da passagem")
        for pagina, texto in _paginas(path):
            if pagina != row["pagina"]:
                continue
            for secao, conteudo in _secoes(texto):
                if secao == row["secao"] and row["texto"] in conteudo:
                    return conteudo
        raise IndiceDesatualizado("Passagem não corresponde à seção de origem")

    def registrar_derivado(self, caminho, documentos):
        """Registra artefato gerenciado para invalidar/remover ao excluir sua fonte."""
        path = Path(caminho).resolve()
        # A exclusão opera apenas no diretório gerenciado desta instância.
        if not path.is_relative_to(self.pasta):
            raise ValueError("Derivado deve ficar dentro da pasta gerenciada do índice")
        with self._conectar() as con:
            for doc_id in documentos:
                if not con.execute("SELECT 1 FROM documentos WHERE id=?", (doc_id,)).fetchone():
                    raise ValueError("Documento do derivado não está no índice")
                con.execute("INSERT OR IGNORE INTO derivados VALUES (?, ?)", (str(path), doc_id))

    def excluir(self, documento_id):
        with self._conectar() as con:
            chunks = con.execute("SELECT count(*) FROM chunks WHERE documento_id=?", (documento_id,)).fetchone()[0]
            linhas = list(con.execute("SELECT caminho FROM derivados WHERE documento_id=?", (documento_id,)))
            caminhos = [Path(r["caminho"]).resolve() for r in linhas]
            if any(not p.is_relative_to(self.pasta) or p == self.db for p in caminhos):
                raise ValueError("Caminho de derivado inseguro; exclusão interrompida")
            for path in caminhos:
                if path.is_file():
                    path.unlink()
            for path in caminhos:
                con.execute("DELETE FROM derivados WHERE caminho=?", (str(path),))
            con.execute("DELETE FROM documentos WHERE id=?", (documento_id,))
            if chunks:
                con.execute("INSERT OR REPLACE INTO meta VALUES ('versao', ?)", (_json(uuid.uuid4().hex),))
        return {"documento_id": documento_id, "chunks_excluidos": chunks,
                "derivados_excluidos": len(caminhos), "original_preservado": True,
                "versao_indice": self.estado()["versao_indice"]}


def comparar_chunking(catalogo, perguntas, cliente, pasta, configs=None, top_k=3):
    """Avalia referências prévias sem usá-las para gerar ou ranquear os chunks."""
    if isinstance(perguntas, (str, Path)):
        perguntas = json.loads(Path(perguntas).read_text(encoding="utf-8"))
    itens = perguntas.get("perguntas", []) if isinstance(perguntas, dict) else perguntas
    respondiveis = [q for q in itens if q.get("tipo") in {"respondível", "respondivel"}]
    if len(respondiveis) != 5:
        raise ValueError("Comparação exige exatamente cinco perguntas respondíveis previamente rotuladas")
    configs = configs or [(90, 20), (45, 10)]
    resultados = []
    for n, config in enumerate(configs):
        tamanho, overlap = (config["tamanho"], config["sobreposicao"]) if isinstance(config, dict) else config
        indice = IndiceVetorial(Path(pasta) / f"config_{n + 1}", cliente, tamanho_chunk=tamanho, sobreposicao=overlap, top_k=top_k)
        estado = indice.indexar(catalogo)
        linhas = []
        for q in respondiveis:
            trechos = indice.buscar(q["pergunta"])
            refs = q.get("referencias", [])
            encontrados = [t["chunk_id"] for t in trechos if any(
                r.get("documento_id") == t["documento_id"] and r.get("trecho", "") and r["trecho"] in t["texto"] for r in refs)]
            linhas.append({"id": q["id"], "acertou": bool(encontrados), "chunks_referencia": encontrados,
                           "recuperados": [{k: t[k] for k in ("chunk_id", "documento_id", "similaridade", "texto", "pagina", "secao")} for t in trechos]})
        numerador = sum(linha["acertou"] for linha in linhas)
        resultados.append({"configuracao": {"tamanho": tamanho, "sobreposicao": overlap, "unidade": "palavras", "top_k": top_k},
                           "modelo_embeddings": cliente.modelo_embeddings, "dimensao": cliente.dimensao,
                           "versao_indice": estado["versao_indice"], "perguntas": linhas,
                           "numerador": numerador, "denominador": 5, "taxa": numerador / 5})
    melhor = max(r["numerador"] for r in resultados)
    vencedores = [n + 1 for n, r in enumerate(resultados) if r["numerador"] == melhor]
    return {"resultados": resultados, "escolha": vencedores[0] if len(vencedores) == 1 else None,
            "justificativa": "Maior recuperação medida; conferir preservação do contexto antes de adotar." if len(vencedores) == 1 else "Empate na recuperação; escolha final exige conferir os trechos e a preservação do contexto."}
