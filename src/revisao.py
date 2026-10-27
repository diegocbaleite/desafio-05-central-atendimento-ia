"""Revisão humana persistida (RF20/RF24) em SQLite (biblioteca padrão).

Estados: pendente -> aprovada | rejeitada | revisar; "revisar" volta a aceitar decisão.
"aprovada" e "rejeitada" são finais para aquela versão (alterar = nova minuta).
Aprovar NÃO envia nada: significa apenas "liberada para envio manual pelo servidor".
Decisões com origem "simulada_teste" existem só para testes e nunca contam como humanas.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

ESTADOS = ("pendente", "aprovada", "rejeitada", "revisar")
DECISOES = {"aprovar": "aprovada", "rejeitar": "rejeitada", "revisar": "revisar"}
ORIGENS_HUMANAS = ("humana_interface", "humana_cli")
ORIGENS = ORIGENS_HUMANAS + ("simulada_teste",)
_ACEITA_DECISAO = ("pendente", "revisar")


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


class RepositorioRevisao:
    def __init__(self, caminho):
        self.caminho = Path(caminho)
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        with self._conexao() as c:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS minutas (
                    id TEXT PRIMARY KEY, caso_id TEXT NOT NULL, criada_em TEXT NOT NULL,
                    status TEXT NOT NULL, conteudo TEXT NOT NULL, sha256 TEXT NOT NULL,
                    gerador TEXT, ia_participou INTEGER NOT NULL, modalidade TEXT,
                    metadados TEXT
                );
                CREATE TABLE IF NOT EXISTS decisoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, minuta_id TEXT NOT NULL,
                    decisao TEXT NOT NULL, status_anterior TEXT NOT NULL, status_novo TEXT NOT NULL,
                    operador TEXT NOT NULL, justificativa TEXT NOT NULL, origem TEXT NOT NULL,
                    sha256_minuta TEXT NOT NULL, decidida_em TEXT NOT NULL,
                    FOREIGN KEY(minuta_id) REFERENCES minutas(id)
                );
                """
            )

    def _conexao(self):
        c = sqlite3.connect(self.caminho)
        c.row_factory = sqlite3.Row
        return c

    def criar_minuta(self, caso_id, conteudo, *, gerador, ia_participou=True, modalidade=None, metadados=None) -> str:
        minuta_id = f"M-{caso_id}-{uuid.uuid4().hex[:8]}"
        with self._conexao() as c:
            c.execute(
                "INSERT INTO minutas VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    minuta_id, caso_id, _agora(), "pendente", conteudo,
                    hashlib.sha256(conteudo.encode("utf-8")).hexdigest(), gerador,
                    int(bool(ia_participou)), modalidade,
                    json.dumps(metadados or {}, ensure_ascii=False, default=str),
                ),
            )
        return minuta_id

    def obter(self, minuta_id) -> dict | None:
        with self._conexao() as c:
            linha = c.execute("SELECT * FROM minutas WHERE id=?", (minuta_id,)).fetchone()
        if not linha:
            return None
        item = dict(linha)
        item["metadados"] = json.loads(item["metadados"] or "{}")
        item["ia_participou"] = bool(item["ia_participou"])
        return item

    def listar(self, status: str | None = None) -> list[dict]:
        sql, args = "SELECT id FROM minutas", ()
        if status:
            sql, args = sql + " WHERE status=?", (status,)
        with self._conexao() as c:
            ids = [r["id"] for r in c.execute(sql + " ORDER BY criada_em DESC", args)]
        return [self.obter(i) for i in ids]

    def historico(self, minuta_id) -> list[dict]:
        with self._conexao() as c:
            return [dict(r) for r in c.execute("SELECT * FROM decisoes WHERE minuta_id=? ORDER BY id", (minuta_id,))]

    def registrar_decisao(self, minuta_id, decisao, operador, justificativa, origem) -> dict:
        if decisao not in DECISOES:
            raise ValueError("Decisão deve ser: " + ", ".join(DECISOES))
        if origem not in ORIGENS:
            raise ValueError("Origem de decisão inválida")
        operador, justificativa = (operador or "").strip(), (justificativa or "").strip()
        if len(operador) < 3 or len(justificativa) < 5:
            raise ValueError("Operador e justificativa são obrigatórios; nenhuma decisão registrada")
        with self._conexao() as c:
            linha = c.execute("SELECT status, sha256 FROM minutas WHERE id=?", (minuta_id,)).fetchone()
            if not linha:
                raise ValueError("Minuta inexistente")
            if linha["status"] not in _ACEITA_DECISAO:
                raise ValueError(f"Minuta já está '{linha['status']}'; gere nova versão para nova decisão")
            novo = DECISOES[decisao]
            registro = {
                "minuta_id": minuta_id,
                "decisao": decisao,
                "status_anterior": linha["status"],
                "status_novo": novo,
                "operador": operador,
                "justificativa": justificativa,
                "origem": origem,
                "sha256_minuta": linha["sha256"],
                "decidida_em": _agora(),
            }
            c.execute("UPDATE minutas SET status=? WHERE id=?", (novo, minuta_id))
            c.execute(
                "INSERT INTO decisoes (minuta_id, decisao, status_anterior, status_novo, operador, "
                "justificativa, origem, sha256_minuta, decidida_em) VALUES (?,?,?,?,?,?,?,?,?)",
                tuple(registro.values()),
            )
        registro["envio_automatico"] = False
        return registro

    def contagem(self) -> dict:
        """Estados atuais e decisões separadas por origem (humana x simulada)."""
        with self._conexao() as c:
            estados = {r["status"]: r["n"] for r in c.execute("SELECT status, COUNT(*) n FROM minutas GROUP BY status")}
            origens = {r["origem"]: r["n"] for r in c.execute("SELECT origem, COUNT(*) n FROM decisoes GROUP BY origem")}
        return {"estados": {e: estados.get(e, 0) for e in ESTADOS}, "decisoes_por_origem": origens}
