"""CLI: python -m src.main verificar | processar | experimento | imagem."""

import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path

import jsonschema

from .auditoria import nova_execucao, registrar
from .cliente import ErroAPI
from .config import ROOT, carregar, chave
from .extracao import extrair
from .minuta import redigir
from .multimodal import imagem_local, ler_imagem, sintetizar, transcrever


def _mensagem_erro(exc):
    if isinstance(exc, (ErroAPI, ValueError)):
        return str(exc)[:200]
    if isinstance(exc, jsonschema.ValidationError):
        return "Saída inválida conforme JSON Schema"
    return "Falha no processamento; conteúdo da solicitação omitido"


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


def executar_caso(caso, execucao, mock=False, decisao=None, decisao_simulada=False):
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
        while decisao not in ("aprovar", "rejeitar", "corrigir", "nova"):
            print("\n--- " + caso["id"] + " ---\n" + minuta + "\n")
            try:
                decisao = input(
                    "Decisão humana [aprovar/rejeitar/corrigir/nova]: "
                ).strip().lower()
            except EOFError as exc:
                raise ValueError(
                    "Decisão humana necessária; nenhum resultado foi aprovado"
                ) from exc
            if decisao not in ("aprovar", "rejeitar", "corrigir", "nova"):
                print("Decisão inválida; escolha aprovar, rejeitar, corrigir ou nova.")
    if decisao not in ("aprovar", "rejeitar", "corrigir", "nova"):
        raise ValueError("Decisão inválida")
    simulacao = decisao_simulada or mock
    if decisao_simulada:
        estado_revisao = "decisao_simulada"
    elif mock:
        estado_revisao = "revisao_mock"
    else:
        estado_revisao = "revisao_humana"
    if simulacao:
        estado = "decisao_simulada"
    elif decisao == "aprovar":
        estado = "aprovada"
    elif decisao == "corrigir":
        estado = "correcao_pendente"
    elif decisao == "nova":
        estado = "nova_geracao_pendente"
    else:
        estado = "rejeitada"

    if not simulacao and decisao in ("aprovar", "corrigir"):
        if decisao == "corrigir":
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
                    arquivo_audio = sintetizar(
                        texto_aprovado, pasta_caso / "minuta_acessivel.mp3"
                    )
                    if arquivo_audio:
                        registrar(
                            execucao,
                            caso["id"],
                            "tts",
                            arquivo=arquivo_audio,
                            status="sucesso",
                        )
                    else:
                        registrar(
                            execucao,
                            caso["id"],
                            "tts_nao_gerado",
                            status="mock",
                        )
                except (ErroAPI, OSError, subprocess.CalledProcessError) as exc:
                    registrar(
                        execucao,
                        caso["id"],
                        "tts_falha",
                        erro=type(exc).__name__,
                        detalhe=(
                            _mensagem_erro(exc)
                            if isinstance(exc, ErroAPI)
                            else "Falha na síntese de áudio"
                        ),
                    )
            (pasta_caso / "roteiro_acessivel.txt").write_text(
                texto_aprovado, encoding="utf-8"
            )
    registrar(
        execucao,
        caso["id"],
        estado_revisao,
        decisao=decisao,
        simulada=simulacao,
        origem=(
            "arquivo_yaml"
            if decisao_simulada
            else "terminal_mock"
            if mock
            else "terminal"
        ),
    )
    resumo = {
        "caso": caso["id"],
        "decisao": decisao,
        "estado_revisao": estado,
        "decisao_simulada": decisao_simulada,
        "execucao_mock": mock,
        "simulada": simulacao,
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
        choices=["verificar", "processar", "experimento", "imagem", "arquivos"],
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
        if a.mock:
            caminho = imagem_local(ROOT / "resultados/peca_visual.png")
        else:
            from .arte_ia import gerar

            caminho = gerar(ROOT / "resultados/peca_visual.png")
        print(caminho)
        return
    if a.comando == "arquivos":
        from .extracao_llm import extrair_pasta

        print("Parte do sistema: extração multimodal de arquivos.")
        print(
            "Fluxo: validação da entrada, leitura/OCR/transcrição, "
            "estruturação dos campos, validação do JSON e auditoria."
        )
        resultados = extrair_pasta(progresso=print)
        for nome, r in resultados.items():
            print("==", nome)
            if "erro" in r:
                print("ERRO:", r["erro"])
                continue
            for k, v in r["campos"].items():
                print(f"  {k}: {v['valor']} ({v['confianca']})")
            print("  categoria:", r["categoria"]["codigo"], "| revisão humana obrigatória")
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
    falhas = []
    for caso in carregar_casos():
        if a.caso and caso["id"] not in a.caso:
            continue
        simulada = caso["id"] in decisoes and decisoes[caso["id"]] is not None
        try:
            resumo.append(
                executar_caso(
                    caso,
                    execucao,
                    a.mock,
                    decisoes.get(caso["id"]),
                    decisao_simulada=simulada,
                )
            )
        except (ErroAPI, ValueError, OSError, EOFError, jsonschema.ValidationError) as exc:
            falha = {
                "caso": caso["id"],
                "erro": type(exc).__name__,
                "detalhe": _mensagem_erro(exc),
            }
            registrar(
                execucao,
                caso["id"],
                "falha_caso",
                erro=falha["erro"],
                detalhe=falha["detalhe"],
            )
            falhas.append(falha)
            print(
                f"Falha no caso {caso['id']}: {type(exc).__name__}: "
                f"{_mensagem_erro(exc)}"
            )
    print(
        json.dumps(
            {"execucao": execucao, "casos": resumo, "falhas": falhas},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
