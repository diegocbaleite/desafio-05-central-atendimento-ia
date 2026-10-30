"""Revisão humana persistente vinculada à versão exata de cada minuta."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .guardrails import SEGREDOS, validar_saida


ESTADOS = ("pendente", "aprovada", "rejeitada", "revisar")
DECISOES = {"aprovar": "aprovada", "rejeitar": "rejeitada", "revisar": "revisar"}


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


class RepositorioRevisoes:
    """Guarda apenas derivados locais; nenhum método envia a minuta a terceiros."""

    def __init__(self, pasta):
        self.pasta = Path(pasta).resolve()
        self.pasta.mkdir(parents=True, exist_ok=True)

    def _arquivo(self, id_execucao: str) -> Path:
        if not isinstance(id_execucao, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", id_execucao):
            raise ValueError("Identificador de revisão inválido")
        return self.pasta / (id_execucao + ".json")

    def _gravar(self, caminho: Path, registro: dict) -> None:
        temporario = caminho.with_suffix(".tmp")
        temporario.write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")
        temporario.replace(caminho)

    def obter(self, id_execucao: str) -> dict:
        registro = json.loads(self._arquivo(id_execucao).read_text(encoding="utf-8"))
        if registro.get("sha256_minuta") != _hash(registro.get("minuta", "")):
            raise ValueError("Minuta alterada fora do fluxo; revisão inválida")
        if registro.get("estado") not in ESTADOS:
            raise ValueError("Estado de revisão inválido")
        return registro

    def salvar_minuta(self, id_execucao: str, conteudo: str, *, simulada: bool = False,
                      documentos=None, metadados=None) -> dict:
        if not isinstance(conteudo, str) or not conteudo.strip():
            raise ValueError("A minuta deve conter texto")
        if validar_saida(conteudo)["decisao"] != "permitir":
            raise ValueError("Minuta contém dados indevidos; revisão bloqueada")
        arquivo = self._arquivo(id_execucao)
        anterior = self.obter(id_execucao) if arquivo.exists() else None
        sha = _hash(conteudo)
        if anterior and anterior["sha256_minuta"] == sha and anterior["simulada"] == bool(simulada):
            return anterior
        historico = list(anterior.get("historico", [])) if anterior else []
        if anterior:
            historico.append({
                "tipo": "versao_substituida", "versao": anterior["versao"],
                "sha256_minuta": anterior["sha256_minuta"], "estado": anterior["estado"],
                "data_utc": _agora(),
            })
        metadados = metadados or {}
        # Não persiste metadados arbitrários do chamador: mantém apenas evidências técnicas.
        permitidos = {"status", "fontes", "versao_schema", "versao_prompt", "versao_indice"}
        registro = {
            "id": id_execucao, "versao": 1 if anterior is None else anterior["versao"] + 1,
            "minuta": conteudo, "sha256_minuta": sha, "estado": "pendente",
            "simulada": bool(simulada), "documentos": sorted(set(documentos or [])),
            "metadados": {k: v for k, v in metadados.items() if k in permitidos},
            "criada_em": anterior["criada_em"] if anterior else _agora(),
            "atualizada_em": _agora(), "revisao": None, "historico": historico,
            "participacao_ia": True, "envio_automatico": False,
        }
        self._gravar(arquivo, registro)
        return registro

    def registrar_decisao(self, id_execucao: str, decisao: str, responsavel: str,
                         justificativa: str, *, sha256_esperado: str,
                         simulada: bool = False) -> dict:
        if decisao not in DECISOES:
            raise ValueError("Decisão inválida; use aprovar, rejeitar ou revisar")
        if not isinstance(responsavel, str) or not responsavel.strip():
            raise ValueError("Informe a pessoa responsável pela revisão")
        if not isinstance(justificativa, str) or not justificativa.strip():
            raise ValueError("Informe a justificativa da decisão")
        if len(responsavel) > 120 or len(justificativa) > 2000:
            raise ValueError("Responsável ou justificativa excede o limite")
        if SEGREDOS.search(responsavel) or SEGREDOS.search(justificativa):
            raise ValueError("Não informe credenciais na revisão")
        registro = self.obter(id_execucao)
        if sha256_esperado != registro["sha256_minuta"]:
            raise ValueError("A minuta mudou; confira a versão atual antes de revisar")
        if registro["simulada"] and not simulada:
            raise PermissionError("Saída simulada não pode receber aprovação humana real neste fluxo")
        revisao = {
            "decisao": decisao, "responsavel": responsavel.strip(),
            "justificativa": justificativa.strip(), "data_utc": _agora(),
            "versao": registro["versao"], "sha256_minuta": sha256_esperado,
            "simulada": bool(simulada),
            "origem": "simulacao" if simulada else "revisao_humana",
        }
        registro["historico"].append({"tipo": "decisao", **revisao})
        registro["revisao"] = revisao
        registro["estado"] = "pendente" if simulada else DECISOES[decisao]
        registro["atualizada_em"] = _agora()
        self._gravar(self._arquivo(id_execucao), registro)
        return registro

    def listar(self) -> list[dict]:
        return [self.obter(p.stem) for p in sorted(self.pasta.glob("*.json")) if p.stem != "exclusoes"]

    def excluir_derivados(self, documento_id: str) -> list[str]:
        removidos = []
        for registro in self.listar():
            if documento_id in registro.get("documentos", []):
                self._arquivo(registro["id"]).unlink()
                removidos.append(registro["id"])
        if removidos:
            self._registrar_exclusao("documento", removidos)
        return removidos

    def _registrar_exclusao(self, motivo: str, ids: list[str]) -> None:
        # Registro contém IDs e motivo, sem texto excluído nem identidade do operador.
        with (self.pasta / "exclusoes.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"motivo": motivo, "ids": ids, "data_utc": _agora()}) + "\n")

    def limpar_expirados(self, dias: int = 30) -> list[str]:
        if isinstance(dias, bool) or not isinstance(dias, int) or dias < 1:
            raise ValueError("Retenção deve ser um número positivo de dias")
        limite = datetime.now(timezone.utc) - timedelta(days=dias)
        removidos = []
        for registro in self.listar():
            if datetime.fromisoformat(registro["atualizada_em"]) < limite:
                self._arquivo(registro["id"]).unlink()
                removidos.append(registro["id"])
        if removidos:
            self._registrar_exclusao("retencao", removidos)
        return removidos
