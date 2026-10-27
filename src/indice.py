"""Índice vetorial persistente em Chroma com manifesto JSON (RF17/RF24).

- Cada configuração de chunking tem sua coleção (`acervo_A`, `acervo_B`).
- IDs de trecho são determinísticos (documento+versão+config+página+seção+n) e o
  manifesto guarda o SHA-256 de cada documento: reindexar o mesmo acervo não duplica.
- Trocar o modelo de embedding (ou a versão do índice) exige `recriar=True`.
- Distância de cosseno do Chroma: 0 = mesma direção; similaridade = 1 - distância.
  Similaridade alta indica proximidade semântica, NÃO garante que o trecho responda.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .ingestao import dividir, ler_paginas, sha256_arquivo


def _agora():
    return datetime.now(timezone.utc).isoformat()


class ReindexacaoExigida(RuntimeError):
    """O índice foi criado com outro modelo/dimensão/versão e não pode ser consultado."""


class IndiceVetorial:
    def __init__(self, diretorio, rotulo: str, chunking: dict, embedder, versao_indice: str):
        import chromadb
        from chromadb.config import Settings

        self.diretorio = Path(diretorio)
        self.diretorio.mkdir(parents=True, exist_ok=True)
        self.rotulo = rotulo
        self.chunking = chunking
        self.embedder = embedder
        self.versao_indice = str(versao_indice)
        self.nome_colecao = f"acervo_{rotulo}"
        self.caminho_manifesto = self.diretorio / f"manifesto_{rotulo}.json"
        self._cliente = chromadb.PersistentClient(
            path=str(self.diretorio / "chroma"), settings=Settings(anonymized_telemetry=False)
        )

    @classmethod
    def de_config(cls, cfg: dict, embedder, rotulo: str | None = None, diretorio=None):
        from .config import ROOT

        r = cfg["recuperacao"]
        rotulo = rotulo or r.get("configuracao_chunking", "A")
        return cls(
            diretorio or ROOT / r.get("diretorio_indice", "indice"),
            rotulo,
            r["chunking"][rotulo],
            embedder,
            r.get("versao_indice", "1"),
        )

    # ------------------------------------------------------------------ manifesto
    def manifesto(self) -> dict:
        if self.caminho_manifesto.is_file():
            return json.loads(self.caminho_manifesto.read_text(encoding="utf-8"))
        return {"documentos": {}, "excluidos": {}, "historico_exclusoes": []}

    def _salvar_manifesto(self, dados: dict) -> None:
        dados["atualizado_em"] = _agora()
        self.caminho_manifesto.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

    def _colecao(self):
        return self._cliente.get_or_create_collection(
            self.nome_colecao,
            embedding_function=None,
            metadata={
                "hnsw:space": "cosine",
                "embedding_modelo": self.embedder.nome,
                "versao_indice": self.versao_indice,
                "config_chunking": self.rotulo,
            },
        )

    def contar(self) -> int:
        return self._colecao().count()

    def motivo_reindexacao(self) -> str | None:
        m = self.manifesto()
        if not m.get("embedding_modelo"):
            return None
        if m["embedding_modelo"] != self.embedder.nome:
            return f"modelo de embedding mudou ({m['embedding_modelo']} -> {self.embedder.nome})"
        if self.embedder.dimensao and m.get("dimensao") and m["dimensao"] != self.embedder.dimensao:
            return f"dimensão mudou ({m['dimensao']} -> {self.embedder.dimensao})"
        if str(m.get("versao_indice")) != self.versao_indice:
            return f"versão do índice mudou ({m.get('versao_indice')} -> {self.versao_indice})"
        if m.get("chunking") and m["chunking"] != self.chunking:
            return "parâmetros de chunking mudaram"
        return None

    def status(self, catalogo: list[dict]) -> dict:
        m = self.manifesto()
        motivo = self.motivo_reindexacao()
        docs = m.get("documentos", {})
        excluidos = set(m.get("excluidos", {}))
        nao_indexados, desatualizados = [], []
        for doc in catalogo:
            if doc["id"] in excluidos:
                continue
            atual = docs.get(doc["id"])
            if atual is None:
                nao_indexados.append(doc["id"])
            elif atual["sha256"] != sha256_arquivo(doc["caminho"]) or atual["versao"] != doc["versao"]:
                desatualizados.append(doc["id"])
        orfaos = sorted(set(docs) - {d["id"] for d in catalogo})
        if motivo:
            estado = "reindexacao_exigida"
        elif not docs:
            estado = "vazio"
        elif nao_indexados or desatualizados or orfaos:
            estado = "desatualizado"
        else:
            estado = "ok"
        return {
            "estado": estado,
            "motivo": motivo,
            "colecao": self.nome_colecao,
            "embedding_modelo": m.get("embedding_modelo", self.embedder.nome),
            "dimensao": m.get("dimensao"),
            "versao_indice": m.get("versao_indice", self.versao_indice),
            "chunking": m.get("chunking", self.chunking),
            "trechos": self.contar(),
            "documentos_indexados": sorted(docs),
            "nao_indexados": nao_indexados,
            "desatualizados": desatualizados,
            "orfaos": orfaos,
            "excluidos": sorted(excluidos),
            "atualizado_em": m.get("atualizado_em"),
        }

    # ------------------------------------------------------------------ escrita
    def indexar(self, catalogo: list[dict], recriar: bool = False, reincluir=()) -> dict:
        motivo = self.motivo_reindexacao()
        if motivo and not recriar:
            raise ReindexacaoExigida(motivo + "; execute a indexação com recriar=True (--recriar)")
        if recriar:
            try:
                self._cliente.delete_collection(self.nome_colecao)
            except Exception:  # coleção inexistente
                pass
            m = {"documentos": {}, "excluidos": self.manifesto().get("excluidos", {}), "historico_exclusoes": self.manifesto().get("historico_exclusoes", [])}
        else:
            m = self.manifesto()
        for doc_id in reincluir:
            m.get("excluidos", {}).pop(doc_id, None)
        colecao = self._colecao()
        antes = colecao.count()
        relatorio = {"adicionados": [], "atualizados": [], "sem_alteracao": [], "ignorados_excluidos": []}
        for doc in catalogo:
            if doc["id"] in m.get("excluidos", {}):
                relatorio["ignorados_excluidos"].append(doc["id"])
                continue
            sha = sha256_arquivo(doc["caminho"])
            atual = m["documentos"].get(doc["id"])
            if atual and atual["sha256"] == sha and atual["versao"] == doc["versao"]:
                relatorio["sem_alteracao"].append(doc["id"])
                continue
            if atual:
                colecao.delete(where={"doc_id": doc["id"]})
            trechos = dividir(
                {**doc, "sha256": sha},
                ler_paginas(doc["caminho"]),
                self.rotulo,
                int(self.chunking["tamanho"]),
                int(self.chunking["sobreposicao"]),
                self.chunking.get("unidade", "palavras"),
            )
            vetores = self.embedder.embed([t["texto"] for t in trechos])
            colecao.upsert(
                ids=[t["id"] for t in trechos],
                embeddings=vetores,
                documents=[t["texto"] for t in trechos],
                metadatas=[t["metadados"] for t in trechos],
            )
            m["documentos"][doc["id"]] = {
                "versao": doc["versao"],
                "titulo": doc["titulo"],
                "arquivo": doc["arquivo"],
                "sha256": sha,
                "trechos": len(trechos),
                "suspeitos": sum(1 for t in trechos if t["metadados"]["suspeito_injecao"]),
                "indexado_em": _agora(),
            }
            relatorio["atualizados" if atual else "adicionados"].append(doc["id"])
        m.update(
            {
                "embedding_modelo": self.embedder.nome,
                # Sem documentos novos o modelo não gera vetores: preserva a dimensão já registrada.
                "dimensao": self.embedder.dimensao or m.get("dimensao"),
                "versao_indice": self.versao_indice,
                "config_chunking": self.rotulo,
                "chunking": self.chunking,
                "criado_em": m.get("criado_em") or _agora(),
            }
        )
        self._salvar_manifesto(m)
        relatorio.update({"trechos_antes": antes, "trechos_depois": colecao.count(), "colecao": self.nome_colecao})
        return relatorio

    def excluir_documento(self, doc_id: str, motivo: str = "solicitação de exclusão") -> dict:
        colecao = self._colecao()
        removidos = len(colecao.get(where={"doc_id": doc_id}, include=[])["ids"])
        colecao.delete(where={"doc_id": doc_id})
        restantes = len(colecao.get(where={"doc_id": doc_id}, include=[])["ids"])
        m = self.manifesto()
        m["documentos"].pop(doc_id, None)
        registro = {"doc_id": doc_id, "em": _agora(), "trechos_removidos": removidos, "motivo": motivo}
        m.setdefault("excluidos", {})[doc_id] = registro
        m.setdefault("historico_exclusoes", []).append(registro)
        self._salvar_manifesto(m)
        return {**registro, "trechos_restantes": restantes, "colecao": self.nome_colecao}

    # ------------------------------------------------------------------ leitura
    def buscar(self, pergunta: str, top_k: int = 4) -> list[dict]:
        motivo = self.motivo_reindexacao()
        if motivo:
            raise ReindexacaoExigida(motivo)
        colecao = self._colecao()
        total = colecao.count()
        if total == 0:
            return []
        r = colecao.query(
            query_embeddings=self.embedder.embed([pergunta]),
            n_results=min(int(top_k), total),
            include=["documents", "metadatas", "distances"],
        )
        saida = []
        for posicao, (cid, texto, meta, dist) in enumerate(
            zip(r["ids"][0], r["documents"][0], r["metadatas"][0], r["distances"][0]), start=1
        ):
            saida.append(
                {
                    "posicao": posicao,
                    "chunk_id": cid,
                    "texto": texto,
                    "metadados": meta,
                    "distancia_cosseno": round(float(dist), 4),
                    "similaridade": round(1.0 - float(dist), 4),
                }
            )
        return saida
