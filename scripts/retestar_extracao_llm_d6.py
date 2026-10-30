"""Reteste declarado de S02/S06 após observar a rodada complementar de 29/10/2026.

Sem --executar apenas descreve o plano. Limite de 3 chamadas adicionais, incluindo
correções/repetições, para manter o total da validação em até 30 chamadas.
"""

import argparse
import json
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.avaliacao_llm_real import TrilhaChamadas, comparar_ficha, gravar, gravar_inventario, inventario, ler_yaml
from src.config import carregar
from src.estruturacao import estruturar
from src.guardrails import segredos_conhecidos
from src.orcamento import Orcamento


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executar", action="store_true")
    args = parser.parse_args()
    if not args.executar:
        print("Prévia sem rede: retestar SOMENTE extração S02/S06, prompt 1.1, máximo 3 chamadas adicionais.")
        return 0
    cfg = carregar()
    perfil = cfg["geracao"]["perfis"]["principal"]
    if perfil["tipo"] != "llm":
        raise ValueError("Reteste exige o perfil LLM real")
    id_ = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:6]
    pasta = ROOT / "documentacao/desafio6/evidencias_openai" / f"reteste_extracao_{id_}"
    pasta.mkdir(parents=True, exist_ok=False)
    antes = inventario()
    gravar_inventario(pasta / "inventario_antes.json", antes)
    trilha = TrilhaChamadas(cfg, pasta)
    orc = Orcamento(min(3, cfg["guardrails"]["max_chamadas_execucao"]), 42086)
    gab = ler_yaml("dados/gabaritos/desafio6/solicitacoes.yaml")["solicitacoes"]
    catalogo = {s["id"]: s for s in ler_yaml("dados/solicitacoes/solicitacoes.yaml")["solicitacoes"]}
    resultados = []
    for sid in ("S02", "S06"):
        s = catalogo[sid]
        texto = (ROOT / s["arquivo"]).read_text(encoding="utf-8")
        registro = {"id": sid, "valida": False}
        try:
            r = estruturar(texto, modo="llm", modalidade=s["modalidade"], perfil=perfil,
                           orcamento=orc, conversar_fn=trilha.para("extracao", sid), hoje=date(2026, 10, 29))
            registro.update(resultado=r, valida=r["validacao"]["valido"])
            if registro["valida"]:
                registro["comparacao"] = comparar_ficha(sid, r["ficha"], gab[sid], texto)
        except Exception as exc:
            registro["erro"] = f"{type(exc).__name__}: {exc}"
        resultados.append(registro)
        gravar(pasta / f"{sid}.json", registro, segredos_conhecidos(cfg))
        print(sid, "válida:", registro["valida"], flush=True)
    depois = inventario()
    gravar_inventario(pasta / "inventario_depois.json", depois)
    resumo = {"id": id_, "natureza": "LLM real — reteste direcionado após observar os erros; não é nova rodada completa",
              "rodada_anterior": "20261030T021555Z_da0eda", "prompt_versao": "1.1", "casos": ["S02", "S06"],
              "provider": perfil["provider"], "modelo_solicitado": perfil["modelo"], "orcamento": orc.resumo(),
              "resultados": resultados, "envio_automatico": False, "decisoes_humanas_criadas": 0,
              "arquivos_protegidos_alterados": [k for k in antes.keys() | depois.keys() if antes.get(k) != depois.get(k)]}
    gravar(pasta / "resumo_reteste.json", resumo, segredos_conhecidos(cfg))
    print("EVIDENCIAS=" + pasta.relative_to(ROOT).as_posix(), flush=True)
    print(json.dumps({"chamadas": orc.chamadas, "tokens": orc.tokens,
                      "alterados": resumo["arquivos_protegidos_alterados"]}, ensure_ascii=False), flush=True)
    return 1 if resumo["arquivos_protegidos_alterados"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
