"""Experimento controlado A/B/C; nunca sobrescreve evidências anteriores."""

import csv
import json
import time
from datetime import UTC, datetime

from .cliente import ErroAPI, conversar
from .config import ROOT, carregar
from .seguranca import delimitar, minimizar

CAMPOS = [
    "caso",
    "prompt",
    "provider",
    "modelo",
    "status",
    "erro",
    "temperatura",
    "max_tokens",
    "latencia_s",
    "tokens_entrada",
    "tokens_saida",
    "custo_usd",
    "tentativas",
    "fidelidade_humana",
    "completude_humana",
    "formato_humano",
    "linguagem_humana",
    "seguranca_humana",
    "total_humano",
    "decisao_humana",
    "revisor_humano",
    "data_revisao",
    "justificativa_humana",
    "tom_1a5_humano",
    "lacunas_humano",
    "injecao_obedecida_humano",
    "minutos_ate_utilizavel_humano",
]


def _pasta_unica(base):
    base.mkdir(parents=True, exist_ok=True)
    identificador = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    pasta = base / identificador
    pasta.mkdir(exist_ok=False)
    return pasta


def executar(mock=False, metaprompt_v2=False):
    cfg = carregar()
    origem = ROOT / "prompts/experimento"
    prompt_a = (origem / "prompt_A.md").read_text(encoding="utf-8")
    prompt_b = (origem / "prompt_B.md").read_text(encoding="utf-8")
    nome_meta = "metaprompt_v2_atendimento.md" if metaprompt_v2 else "metaprompt.md"
    meta = (origem / nome_meta).read_text(encoding="utf-8")
    provider = "mock" if mock else cfg["llm"]["provider"]
    pasta = _pasta_unica(
        ROOT / "resultados/experimento_prompts" / ("mock" if mock else "real")
    )
    (pasta / "metaprompt_fonte.md").write_text(meta, encoding="utf-8")
    linhas = []

    def gravar():
        with (pasta / "matriz.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CAMPOS)
            w.writeheader()
            w.writerows(linhas)

    if provider == "mock":
        prompt_c = (origem / "prompt_C_modelo_exemplo.md").read_text(encoding="utf-8")
        meta_metaprompt = {
            "provider": "mock",
            "modelo": "mock",
            "status": "simulado",
            "duracao_s": 0,
            "tokens_entrada": None,
            "tokens_saida": None,
            "custo_usd": None,
            "tentativas": 0,
        }
    else:
        try:
            resposta_meta = conversar(
                [{"role": "user", "content": meta}], provider=provider
            )
            prompt_c = resposta_meta["texto"]
            meta_metaprompt = {
                k: resposta_meta.get(k)
                for k in (
                    "provider",
                    "modelo",
                    "duracao_s",
                    "tokens_entrada",
                    "tokens_saida",
                    "custo_usd",
                    "tentativas",
                )
            }
            meta_metaprompt["status"] = "sucesso"
        except ErroAPI as exc:
            meta_metaprompt = {
                "provider": provider,
                "modelo": cfg["llm"]["modelo"],
                "status": "falha",
                "erro": str(exc)[:300],
            }
            (pasta / "metaprompt_execucao.json").write_text(
                json.dumps(meta_metaprompt, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (pasta / "erro_metaprompt.txt").write_text(
                "Falha ao gerar o Prompt C; nenhuma comparação foi executada.\n"
                + str(exc)[:300],
                encoding="utf-8",
            )
            gravar()
            print("Falha de geração do metaprompt. Registro:", pasta)
            return {
                "pasta": str(pasta),
                "sucesso_total": False,
                "total": 0,
                "falhas": 1,
            }
    (pasta / "metaprompt_execucao.json").write_text(
        json.dumps(meta_metaprompt, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (pasta / "prompt_C_utilizado.md").write_text(prompt_c, encoding="utf-8")
    from .main import carregar_casos

    casos = {
        c["id"]: c
        for c in carregar_casos()
        if c.get("modalidade", "texto") == "texto"
    }
    if not casos:
        raise ValueError("Nenhum caso textual em casos.yaml para o experimento A/B/C")
    for nome in casos:
        entrada = (ROOT / casos[nome]["arquivo"]).read_text(encoding="utf-8")
        seguro = minimizar(delimitar(entrada))
        for metodo, prompt in (("A", prompt_a), ("B", prompt_b), ("C", prompt_c)):
            inicio = time.perf_counter()
            try:
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
                status, erro = "sucesso", ""
                (pasta / f"{nome}_prompt_{metodo}_saida.txt").write_text(
                    resposta["texto"], encoding="utf-8"
                )
            except ErroAPI as exc:
                status, erro = "falha", str(exc)[:300]
                resposta = {
                    "provider": provider,
                    "modelo": cfg["llm"]["modelo"],
                    "tokens_entrada": None,
                    "tokens_saida": None,
                    "custo_usd": None,
                    "tentativas": None,
                }
                print(f"{nome}/{metodo}: {erro}")
            linhas.append(
                {
                    "caso": nome,
                    "prompt": metodo,
                    "provider": resposta["provider"],
                    "modelo": resposta["modelo"],
                    "status": status,
                    "erro": erro,
                    "temperatura": cfg["llm"]["temperatura"],
                    "max_tokens": cfg["llm"]["max_tokens"],
                    "latencia_s": round(time.perf_counter() - inicio, 3),
                    "tokens_entrada": resposta["tokens_entrada"],
                    "tokens_saida": resposta["tokens_saida"],
                    "custo_usd": resposta.get("custo_usd"),
                    "tentativas": resposta.get("tentativas"),
                    "fidelidade_humana": "",
                    "completude_humana": "",
                    "formato_humano": "",
                    "linguagem_humana": "",
                    "seguranca_humana": "",
                    "total_humano": "",
                    "decisao_humana": "",
                    "revisor_humano": "",
                    "data_revisao": "",
                    "justificativa_humana": "",
                    "tom_1a5_humano": "",
                    "lacunas_humano": "",
                    "injecao_obedecida_humano": "",
                    "minutos_ate_utilizavel_humano": "",
                }
            )
            gravar()  # preserva resultados parciais sem mascarar falhas
    print("Matriz:", pasta / "matriz.csv", "- preencher colunas humanas após avaliação")
    falhas = sum(linha["status"] != "sucesso" for linha in linhas)
    return {
        "pasta": str(pasta),
        "sucesso_total": falhas == 0,
        "total": len(linhas),
        "falhas": falhas,
    }
