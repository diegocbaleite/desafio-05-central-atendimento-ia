"""Teto de chamadas e tokens por execução (RF16). Correções de esquema também consomem."""

from __future__ import annotations


class OrcamentoExcedido(RuntimeError):
    """A execução atingiu o limite configurado; nenhuma nova chamada é feita."""


class Orcamento:
    def __init__(self, max_chamadas: int, max_tokens: int | None = None):
        if max_chamadas < 0:
            raise ValueError("max_chamadas deve ser >= 0")
        self.max_chamadas = max_chamadas
        self.max_tokens = max_tokens
        self.chamadas = 0
        self.tokens = 0
        self.tokens_indisponiveis = 0
        self.motivos: list[str] = []

    @classmethod
    def de_config(cls, cfg: dict) -> "Orcamento":
        g = cfg.get("guardrails", {})
        return cls(int(g.get("max_chamadas_execucao", 30)), g.get("max_tokens_execucao"))

    def reservar(self, motivo: str) -> None:
        """Chamar ANTES de cada requisição HTTP (inclui repetição e correção)."""
        if self.chamadas >= self.max_chamadas:
            raise OrcamentoExcedido(
                f"Orçamento de chamadas esgotado ({self.chamadas}/{self.max_chamadas})"
            )
        if self.max_tokens is not None and self.tokens >= self.max_tokens:
            raise OrcamentoExcedido(
                f"Orçamento de tokens esgotado ({self.tokens}/{self.max_tokens})"
            )
        self.chamadas += 1
        self.motivos.append(motivo)

    def consumir_tokens(self, entrada: int | None, saida: int | None) -> None:
        if entrada is None and saida is None:
            # Provedor não informou uso: registramos a indisponibilidade, sem estimar.
            self.tokens_indisponiveis += 1
            return
        self.tokens += int(entrada or 0) + int(saida or 0)

    def resumo(self) -> dict:
        return {
            "chamadas": self.chamadas,
            "max_chamadas": self.max_chamadas,
            "tokens": self.tokens,
            "max_tokens": self.max_tokens,
            "chamadas_sem_tokens_informados": self.tokens_indisponiveis,
            "motivos": list(self.motivos),
        }
