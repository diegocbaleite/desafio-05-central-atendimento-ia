"""CLI: python -m src.main verificar | processar | experimento | imagem."""

import argparse
import hashlib
import json
import platform
from pathlib import Path

from .auditoria import nova_execucao, registrar
from .config import ROOT, carregar, chave
from .extracao import extrair
from .minuta import redigir
from .multimodal import imagem_local, ler_imagem, sintetizar, transcrever


def preparar_entrada(path, modo, mock=False):
    if modo == "texto":
        return path.read_text(encoding="utf-8")
    if modo == "imagem":
        return ler_imagem(path)
    if modo == "audio":
        if mock:
            # O modo mock lê somente uma referência fictícia explicitamente rotulada;
            # não afirma ter transcrito o arquivo de áudio.
            trans = path.parent / (
                path.name.split("_audio")[0] + "_transcricao_ficticia.txt"
            )
            if not trans.exists():
                raise ValueError(
                    "Transcrição fictícia de referência ausente: " + str(trans)
                )
            return trans.read_text(encoding="utf-8")
        return transcrever(path)
    raise ValueError("Modalidade inválida")


def carregar_casos():
    import yaml

    return yaml.safe_load(
        (ROOT / "dados/originais/casos.yaml").read_text(encoding="utf-8")
    )["casos"]


def executar_caso(caso, execucao, mock=False, decisao=None):
    import jsonschema

    entrada = ROOT / caso["arquivo"]
    texto = preparar_entrada(entrada, caso["modalidade"], mock)
    hash_arquivo = hashlib.sha256(entrada.read_bytes()).hexdigest()
    pasta = registrar(
        execucao,
        caso["id"],
        "entrada",
        arquivo=caso["arquivo"],
        sha256=hash_arquivo,
        modalidade=caso["modalidade"],
    )
    pasta_caso = pasta / caso["id"]
    pasta_caso.mkdir(parents=True, exist_ok=True)
    ext = extrair(texto, caso["id"], caso["arquivo"], hash_arquivo, caso["modalidade"])
    schema = json.loads(
        (ROOT / "src/schemas/extracao.schema.json").read_text(encoding="utf-8")
    )
    jsonschema.validate(ext, schema)
    (pasta_caso / "extracao.json").write_text(
        json.dumps(ext, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    registrar(
        execucao,
        caso["id"],
        "extracao",
        categoria=ext["categoria"]["codigo"],
        ausentes=ext["campos_ausentes"],
        alerta_injecao=ext["alerta_injecao"],
    )
    provider = "mock" if mock else carregar()["llm"]["provider"]
    minuta, meta = redigir(ext, caso["arquivo"], provider=provider)
    (pasta_caso / "minuta_pendente.md").write_text(minuta, encoding="utf-8")
    registrar(execucao, caso["id"], "geracao_minuta", **meta)
    if decisao is None:
        print("\n--- " + caso["id"] + " ---\n" + minuta + "\n")
        decisao = (
            input("Decisão humana [aprovar/rejeitar/corrigir/nova]: ").strip().lower()
        )
    if decisao not in ("aprovar", "rejeitar", "corrigir", "nova"):
        raise ValueError("Decisão inválida")
    if decisao in ("aprovar", "corrigir"):
        if decisao == "corrigir":
            # Uma correção manual deve substituir o arquivo pendente ANTES de executar a aprovação.
            (pasta_caso / "PENDENTE_CORRECAO.txt").write_text(
                "Revisor deve corrigir a minuta e executar novamente.", encoding="utf-8"
            )
        else:
            (pasta_caso / "minuta_aprovada.md").write_text(minuta, encoding="utf-8")
            # Áudio somente após revisão/aprovação; nunca enviar a terceiros.
            texto_aprovado = minuta.replace(
                "# MINUTA — NÃO ENVIADA",
                "Minuta aprovada para demonstração, não enviada",
            )
            if not mock:
                try:
                    sintetizar(texto_aprovado, pasta_caso / "minuta_acessivel.mp3")
                except Exception as exc:
                    registrar(
                        execucao, caso["id"], "tts_falha", erro=type(exc).__name__
                    )
            (pasta_caso / "roteiro_acessivel.txt").write_text(
                texto_aprovado, encoding="utf-8"
            )
    registrar(execucao, caso["id"], "revisao_humana", decisao=decisao)
    resumo = {
        "caso": caso["id"],
        "decisao": decisao,
        "categoria": ext["categoria"]["codigo"],
        "alerta_injecao": ext["alerta_injecao"],
        "ausentes": ext["campos_ausentes"],
    }
    (pasta_caso / "resultado.json").write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return resumo


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "comando",
        nargs="?",
        choices=["verificar", "processar", "experimento", "imagem"],
        default="processar",
    )
    p.add_argument("--mock", action="store_true", help="simulação sem APIs reais")
    p.add_argument("--metaprompt-v2", action="store_true", help="experimento separado usando metaprompt revisado")
    p.add_argument("--caso", action="append")
    p.add_argument(
        "--decisoes",
        help="YAML contendo decisões de DEMONSTRAÇÃO; não é revisão de servidor real",
    )
    a = p.parse_args()
    cfg = carregar()
    if a.comando == "verificar":
        print("Python", platform.python_version(), "sistema", platform.system())
        for k in ("jsonschema", "yaml", "requests", "PIL"):
            try:
                m = __import__(k)
                print(k, getattr(m, "__version__", "instalado"))
            except ImportError:
                print(k, "não instalado")
        for nome in cfg["provedores"]:
            print("chave", nome, "configurada" if chave(cfg, nome) else "ausente")
        print("envio automatico:", cfg["seguranca"]["envio_automatico"])
        return
    if a.comando == "imagem":
        print(imagem_local(ROOT / "resultados/peca_visual.png"))
        return
    if a.comando == "experimento":
        from .experimento import executar

        executar(mock=a.mock, metaprompt_v2=a.metaprompt_v2)
        return
    import yaml

    decisoes = {}
    if a.decisoes:
        decisoes = yaml.safe_load(Path(a.decisoes).read_text(encoding="utf-8")) or {}
        print("ATENÇÃO: decisões carregadas de arquivo, apenas para demonstração.")
    execucao = nova_execucao()
    resumo = []
    for caso in carregar_casos():
        if a.caso and caso["id"] not in a.caso:
            continue
        resumo.append(executar_caso(caso, execucao, a.mock, decisoes.get(caso["id"])))
    print(
        json.dumps(
            {"execucao": execucao, "casos": resumo}, ensure_ascii=False, indent=2
        )
    )


if __name__ == "__main__":
    main()
