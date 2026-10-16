"""Comparação A/B/C com parâmetros comuns e avaliação posterior."""

import csv
import time

from .cliente import conversar
from .config import ROOT, carregar
from .seguranca import delimitar, minimizar


def executar(mock=False):
    cfg = carregar()
    prompt_dir = ROOT / "prompts/experimento"
    prompt_a = (prompt_dir / "prompt_A.md").read_text(encoding="utf-8")
    prompt_b = (prompt_dir / "prompt_B.md").read_text(encoding="utf-8")
    meta = (prompt_dir / "metaprompt.md").read_text(encoding="utf-8")
    provider = "mock" if mock else cfg["llm"]["provider"]
    if provider == "mock":
        prompt_c = (prompt_dir / "prompt_C_modelo_exemplo.md").read_text(
            encoding="utf-8"
        )
    else:
        prompt_c = conversar([{"role": "user", "content": meta}], provider=provider)[
            "texto"
        ]
    pasta = ROOT / "resultados/experimento_prompts"
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "prompt_C_utilizado.md").write_text(prompt_c, encoding="utf-8")
    linhas = []
    for nome in ("C01", "C05", "C06"):
        casos = {
            c["id"]: c
            for c in __import__(
                "src.main", fromlist=["carregar_casos"]
            ).carregar_casos()
        }
        texto = (ROOT / casos[nome]["arquivo"]).read_text(encoding="utf-8")
        for metodo, prompt in (("A", prompt_a), ("B", prompt_b), ("C", prompt_c)):
            seguro = minimizar(delimitar(texto))
            inicio = time.perf_counter()
            resposta = conversar(
                [
                    {
                        "role": "system",
                        "content": prompt.replace(
                            "{{solicitacao}}",
                            "[a solicitação está na mensagem do usuário]",
                        ),
                    },
                    {"role": "user", "content": seguro},
                ],
                provider=provider,
            )
            pasta.joinpath(nome + "_prompt_" + metodo + "_saida.txt").write_text(
                resposta["texto"], encoding="utf-8"
            )
            linhas.append(
                {
                    "caso": nome,
                    "prompt": metodo,
                    "provider": resposta["provider"],
                    "modelo": resposta["modelo"],
                    "temperatura": cfg["llm"]["temperatura"],
                    "latencia_s": round(time.perf_counter() - inicio, 3),
                    "tokens_entrada": resposta["tokens_entrada"],
                    "tokens_saida": resposta["tokens_saida"],
                    "fidelidade_humana": "",
                    "formato_humano": "",
                    "tom_1a5_humano": "",
                    "lacunas_humano": "",
                    "injecao_obedecida_humano": "",
                    "minutos_ate_utilizavel_humano": "",
                }
            )
    with (pasta / "matriz.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=linhas[0])
        w.writeheader()
        w.writerows(linhas)
    print("Matriz:", pasta / "matriz.csv", "- preencher colunas humanas após avaliação")
