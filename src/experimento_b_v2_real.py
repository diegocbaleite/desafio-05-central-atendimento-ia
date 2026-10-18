"""Executa somente o Prompt B V2 com OpenRouter real; sem homologação automática.

Uso: python -m src.experimento_b_v2_real
Pré-requisitos: .env local com OPENROUTER_API_KEY válida; dados fictícios.
Resultados locais ignorados pelo Git: resultados/execucoes/prompts_b_v2_real/.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from pathlib import Path

from .cliente import ErroAPI, conversar
from .config import ROOT, carregar, chave
from .experimento import _pasta_unica
from .seguranca import delimitar, minimizar


ARQUIVOS = {
    "C01": "dados/originais/C01.txt",
    "C05": "dados/originais/C05.txt",
    "C06": "dados/originais/C06.txt",
}
PROMPT = "prompts/experimento/prompt_B_v2_seguro.md"
COLUNAS = [
    "caso", "versao_prompt", "provider", "modelo", "status", "erro",
    "temperatura", "max_tokens", "timeout_s", "latencia_s",
    "tokens_entrada", "tokens_saida", "custo_usd", "sha256_original",
    "sha256_prompt", "arquivo_saida", "decisao_humana",
]


def preparar_mensagens(prompt: str, entrada: str) -> list[dict[str, str]]:
    """Não insere a entrada externa no papel system (evita elevar privilégios)."""
    if "{{solicitacao}}" not in prompt:
        raise ValueError("Prompt B V2 não contém o marcador {{solicitacao}}")
    sistema = prompt.replace(
        "{{solicitacao}}",
        "[ver mensagem do usuário delimitada como conteudo_externo]",
    )
    usuario = minimizar(delimitar(entrada))
    return [
        {"role": "system", "content": sistema},
        {"role": "user", "content": usuario},
    ]


def executar(casos: list[str] | None = None, modelo: str | None = None, *, somente_checar: bool = False) -> tuple[Path | None, bool]:
    """Faz chamadas REAIS e devolve (pasta, sucesso_total), sem alterar arquivos históricos."""
    cfg = carregar()
    provedor = "openrouter"
    modelo = modelo or cfg["llm"]["modelo"]
    if not isinstance(modelo, str) or not modelo.strip():
        raise ValueError("Modelo não configurado")
    token = chave(cfg, provedor)
    if not token:
        raise RuntimeError(
            "OPENROUTER_API_KEY ausente no .env local. Não cole a chave no chat nem faça commit do .env."
        )
    raiz = ROOT / "resultados/execucoes/prompts_b_v2_real"
    prompt_path = ROOT / PROMPT
    prompt = prompt_path.read_text(encoding="utf-8")
    if "{{solicitacao}}" not in prompt:
        raise ValueError("Prompt B V2 inválido: marcador {{solicitacao}} ausente")
    ids = casos or list(ARQUIVOS)
    for caso in ids:
        if caso not in ARQUIVOS:
            raise ValueError("Caso não previsto no experimento: " + caso)
        if not (ROOT / ARQUIVOS[caso]).is_file():
            raise FileNotFoundError("Entrada fictícia ausente: " + ARQUIVOS[caso])
    print("Provedor: openrouter | Modelo solicitado:", modelo)
    print("Casos:", ", ".join(ids), "| Token configurado: sim (valor oculto)")
    print("Envio automático de respostas a cidadãos: NÃO")
    if somente_checar:
        print("Pré-verificação concluída. Nenhuma chamada real foi efetuada.")
        return None, True

    pasta = _pasta_unica(raiz)
    (pasta / "prompt_B_v2_utilizado.md").write_text(prompt, encoding="utf-8")
    sha_prompt = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    parametros = {
        "modo": "real", "provider": provedor, "modelo_solicitado": modelo,
        "temperatura": cfg["llm"]["temperatura"],
        "max_tokens": cfg["llm"]["max_tokens"], "timeout_s": cfg["llm"]["timeout_s"],
        "sha256_prompt": sha_prompt,
        "revisao_humana": "pendente",
        "observacao": "Saídas novas do B V2; não substituir a matriz original A/B/C.",
    }
    (pasta / "parametros.json").write_text(
        json.dumps(parametros, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    linhas = []

    def salvar_csv() -> None:
        with (pasta / "matriz_B_v2.csv").open("w", encoding="utf-8", newline="") as arquivo:
            gravador = csv.DictWriter(arquivo, fieldnames=COLUNAS)
            gravador.writeheader()
            gravador.writerows(linhas)

    salvar_csv()
    for caso in ids:
        origem = ROOT / ARQUIVOS[caso]
        texto = origem.read_text(encoding="utf-8")
        hash_original = hashlib.sha256(origem.read_bytes()).hexdigest()
        mensagens = preparar_mensagens(prompt, texto)
        inicio = time.perf_counter()
        status = "falha"
        erro = ""
        resposta = {}
        arquivo_saida = ""
        try:
            # Configuração real; não usar mock e não gerar o prompt C.
            resposta = conversar(mensagens, modelo=modelo, provider=provedor)
            if not resposta.get("texto", "").strip():
                raise ErroAPI("Modelo não retornou texto utilizável")
            arquivo_saida = caso + "_prompt_B_v2_saida.txt"
            (pasta / arquivo_saida).write_text(resposta["texto"], encoding="utf-8")
            status = "sucesso"
        except ErroAPI as exc:
            # O cliente não deve expor chaves; uma segunda barreira remove o token.
            erro = str(exc).replace(token, "[CREDENCIAL_REMOVIDA]")[:300]
        linha = {
            "caso": caso, "versao_prompt": "B_v2", "provider": provedor,
            "modelo": resposta.get("modelo", modelo), "status": status, "erro": erro,
            "temperatura": cfg["llm"]["temperatura"],
            "max_tokens": cfg["llm"]["max_tokens"],
            "timeout_s": cfg["llm"]["timeout_s"],
            "latencia_s": round(time.perf_counter() - inicio, 3),
            "tokens_entrada": resposta.get("tokens_entrada", ""),
            "tokens_saida": resposta.get("tokens_saida", ""),
            "custo_usd": "não localizado", "sha256_original": hash_original,
            "sha256_prompt": sha_prompt, "arquivo_saida": arquivo_saida,
            "decisao_humana": "",
        }
        linhas.append(linha)
        salvar_csv()  # Mantém falhas e resultados parciais sem apagar outras rodadas.
        print(f"{caso}/B_v2: {status}" + (f" — {erro}" if erro else ""))

    completo = all(linha["status"] == "sucesso" for linha in linhas)
    print("Evidências locais:", pasta)
    print("Matriz:", pasta / "matriz_B_v2.csv")
    print("Revisão humana: PENDENTE; nenhuma resposta foi enviada a cidadãos.")
    return pasta, completo


def main() -> int:
    p = argparse.ArgumentParser(description="Executa Prompt B V2 com modelo real OpenRouter.")
    p.add_argument("--caso", action="append", choices=list(ARQUIVOS),
                   help="Executar só casos específicos (repetível); padrão: C01,C05,C06")
    p.add_argument("--modelo", help="Modelo OpenRouter opcional; padrão do config.yaml")
    p.add_argument("--checar", action="store_true",
                   help="Apenas verifica chave/entradas/prompt, sem chamada de API")
    a = p.parse_args()
    try:
        _, sucesso = executar(a.caso, a.modelo, somente_checar=a.checar)
    except (ValueError, RuntimeError, FileNotFoundError) as exc:
        print("Não foi possível executar:", str(exc))
        return 2
    return 0 if sucesso else 1


if __name__ == "__main__":
    raise SystemExit(main())
