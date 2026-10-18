"""CLI: python -m src.main verificar | processar | experimento | imagem | audio | ocr | voz | arte."""

import argparse
import hashlib
import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

import jsonschema

from .auditoria import nova_execucao, registrar
from .audio import avaliar_audio, gerar_voz, sintetizar, transcrever
from .avaliacao import avaliar_campos, taxa_aprovacao
from .cliente import ErroAPI
from .config import ROOT, carregar, chave
from .extracao import extrair
from .imagem import gerar, gerar_visual, imagem_local
from .minuta import redigir
from .visao import avaliar_ocr, ler_imagem

DECISOES = ("aprovar", "rejeitar", "corrigir", "nova")
MAX_NOVAS_GERACOES = 3
CAMPOS_CRITICOS = ("protocolo", "data_solicitacao", "solicitante")
BIBLIOTECAS = (
    "requests",
    "PyYAML",
    "jsonschema",
    "python-dotenv",
    "pillow",
    "pytesseract",
)
FERRAMENTAS = ("tesseract", "pdftoppm", "espeak", "ffprobe")


def _mensagem_erro(exc):
    if isinstance(exc, (ErroAPI, ValueError, RuntimeError, PermissionError)):
        return str(exc)[:200]
    if isinstance(exc, jsonschema.ValidationError):
        return "Saída inválida conforme JSON Schema"
    return "Falha no processamento; conteúdo da solicitação omitido"


def preparar_entrada(path, modo, mock=False, referencia=None, permitir_api=False):
    if modo == "texto":
        return path.read_text(encoding="utf-8")
    if modo == "imagem":
        return ler_imagem(path)
    if modo == "audio":
        if mock:
            # O modo mock lê somente uma referência explicitamente rotulada;
            # não afirma ter transcrito o arquivo de áudio.
            trans = (
                Path(referencia)
                if referencia
                else path.parent
                / (path.name.split("_audio")[0] + "_transcricao_ficticia.txt")
            )
            if not trans.exists():
                raise ValueError(
                    "Transcrição fictícia de referência ausente: " + str(trans)
                )
            return trans.read_text(encoding="utf-8")
        return transcrever(path, permitir_api=permitir_api)
    raise ValueError("Modalidade inválida")


def carregar_casos():
    import yaml

    caminho = ROOT / carregar().get("projeto", {}).get(
        "casos", "dados/originais/casos.yaml"
    )
    return yaml.safe_load(caminho.read_text(encoding="utf-8"))["casos"]


def _gravar_bytes(caminho, texto):
    """Grava sem conversão de quebras de linha para que o SHA-256 do arquivo seja estável."""
    caminho.write_bytes(texto.encode("utf-8"))


def _sha256_texto(texto):
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _ler_terminal(pergunta):
    try:
        return input(pergunta).strip()
    except EOFError as exc:
        raise ValueError(
            "Decisão humana necessária; nenhum resultado foi aprovado"
        ) from exc


def _conferir_campos_criticos(caso, ext, execucao, simulacao):
    """RF06/RF08: dados críticos de STT/OCR exigem conferência humana antes da minuta."""
    if caso["modalidade"] not in ("audio", "imagem"):
        return None
    if simulacao:
        registrar(
            execucao, caso["id"], "conferencia_campos_criticos", status="simulada"
        )
        return {"status": "simulada"}
    print("\n--- Conferência com o ORIGINAL (" + caso["id"] + ") ---")
    for nome in CAMPOS_CRITICOS:
        print(f"  {nome}: {ext['campos'][nome]['valor']}")
    confirmou = _ler_terminal(
        "Os campos acima conferem com o original? [sim/nao]: "
    ).lower()
    responsavel = _ler_terminal("Responsável pela conferência: ")
    if confirmou not in ("sim", "s") or not responsavel:
        registrar(
            execucao,
            caso["id"],
            "conferencia_campos_criticos",
            status="bloqueada",
            responsavel=responsavel or None,
        )
        raise ValueError(
            "Conferência humana dos campos críticos não confirmada; minuta não gerada"
        )
    conferencia = {
        "status": "confirmada",
        "responsavel": responsavel,
        "data": date.today().isoformat(),
    }
    registrar(execucao, caso["id"], "conferencia_campos_criticos", **conferencia)
    return conferencia


def _decisao_humana(caso_id, minuta, versao):
    """Pede decisão, responsável e justificativa; nada é inferido ou preenchido pelo código."""
    while True:
        print(f"\n--- {caso_id} (versão {versao}) ---\n{minuta}\n")
        decisao = _ler_terminal(
            "Decisão humana [aprovar/rejeitar/corrigir/nova]: "
        ).lower()
        if decisao in DECISOES:
            break
        print("Decisão inválida; escolha aprovar, rejeitar, corrigir ou nova.")
    revisor = _ler_terminal("Responsável pela decisão: ")
    justificativa = _ler_terminal("Justificativa: ")
    if not revisor or not justificativa:
        raise ValueError(
            "Responsável e justificativa são obrigatórios; nenhuma decisão registrada"
        )
    return decisao, revisor, justificativa


def executar_caso(
    caso, execucao, mock=False, decisao=None, decisao_simulada=False, permitir_api=False
):
    entrada = ROOT / caso["arquivo"]
    if not entrada.is_file():
        raise ValueError(
            "Arquivo de entrada não encontrado: " + caso["arquivo"]
            + " (confira dados/originais/casos.yaml)"
        )
    simulacao = decisao_simulada or mock
    if decisao is not None and not simulacao:
        raise ValueError(
            "Decisão fornecida por código deve ser marcada como simulada; "
            "decisão humana real só é obtida no terminal"
        )
    referencia = caso.get("transcricao_referencia")
    texto = preparar_entrada(
        entrada,
        caso["modalidade"],
        mock,
        ROOT / referencia if referencia else None,
        permitir_api,
    )
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
    avaliacao = avaliar_campos(ext, caso["id"])
    if avaliacao is not None:
        registrar(execucao, caso["id"], "avaliacao_gabarito", resultado=avaliacao)
    conferencia = _conferir_campos_criticos(caso, ext, execucao, simulacao)
    provider = "mock" if mock else carregar()["llm"]["provider"]
    versao = 1
    revisor = justificativa = None
    while True:
        minuta, meta = redigir(ext, caso["arquivo"], provider=provider)
        sha_minuta = _sha256_texto(minuta)
        _gravar_bytes(pasta_caso / "minuta_pendente.md", minuta)
        _gravar_bytes(pasta_caso / f"minuta_v{versao}.md", minuta)
        registrar(
            execucao,
            caso["id"],
            "geracao_minuta",
            versao_minuta=versao,
            sha256_minuta=sha_minuta,
            **meta,
        )
        if decisao is None:
            decisao, revisor, justificativa = _decisao_humana(
                caso["id"], minuta, versao
            )
        if decisao not in DECISOES:
            raise ValueError("Decisão inválida")
        if decisao_simulada:
            estado_revisao = "decisao_simulada"
        elif mock:
            estado_revisao = "revisao_mock"
        else:
            estado_revisao = "revisao_humana"
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
            revisor=revisor,
            justificativa=justificativa,
            data_revisao=None if simulacao else date.today().isoformat(),
            versao_minuta=versao,
            sha256_minuta=sha_minuta,
        )
        # Nova geração invalida qualquer decisão anterior: a próxima versão é revisada de novo.
        if decisao == "nova" and not simulacao and versao <= MAX_NOVAS_GERACOES:
            versao += 1
            decisao = None
            continue
        break
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
            _gravar_bytes(pasta_caso / "minuta_aprovada.md", minuta)
            # Mesmo formato exigido por audio.gerar_voz.
            (pasta_caso / "revisao.json").write_text(
                json.dumps(
                    {
                        "decisao": "aprovar",
                        "simulada": False,
                        "origem": "revisao_humana",
                        "revisor": revisor,
                        "justificativa": justificativa,
                        "data_revisao": date.today().isoformat(),
                        "versao_minuta": versao,
                        "sha256_minuta": sha_minuta,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            # Áudio somente após revisão/aprovação; nunca enviar a terceiros.
            texto_aprovado = minuta.replace(
                "# MINUTA — NÃO ENVIADA",
                "Minuta aprovada para demonstração, não enviada",
            )
            aprovada_intacta = (
                hashlib.sha256((pasta_caso / "minuta_aprovada.md").read_bytes()).hexdigest()
                == sha_minuta
            )
            if not mock and aprovada_intacta:
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
        "versao_minuta": versao,
        "sha256_minuta": sha_minuta,
        "conferencia_campos_criticos": conferencia,
        "avaliacao_gabarito": avaliacao,
    }
    (pasta_caso / "resultado.json").write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return resumo


def _verificar(cfg):
    print("Python", platform.python_version(), "sistema", platform.system())
    for distribuicao in BIBLIOTECAS:
        try:
            print(distribuicao, importlib.metadata.version(distribuicao))
        except importlib.metadata.PackageNotFoundError:
            print(distribuicao, "não instalado")
    for ferramenta in FERRAMENTAS:
        print(
            "ferramenta",
            ferramenta,
            "disponível" if shutil.which(ferramenta) else "ausente",
        )
    for nome in cfg["provedores"]:
        print("chave", nome, "configurada" if chave(cfg, nome) else "ausente")
    print("envio automatico:", cfg["seguranca"]["envio_automatico"])


COMANDOS_MIDIA = ("audio", "ocr", "voz", "arte")


def _comando_midia(a):
    """STT, OCR, voz e arte: gravam evidências em resultados/ e nunca enviam respostas."""
    try:
        if a.comando in ("audio", "ocr", "voz") and not a.entrada:
            raise ValueError("Informe o arquivo de entrada do comando " + a.comando)
        if a.comando == "audio":
            pasta = avaliar_audio(
                a.entrada,
                provider=a.provider or "local",
                modelo_local=a.modelo_local,
                permitir_api=a.autorizar_api,
                gabarito=a.gabarito,
                revisado=a.revisado,
            )
        elif a.comando == "ocr":
            pasta = avaliar_ocr(
                a.entrada, psm=a.psm, gabarito=a.gabarito, revisado=a.revisado
            )
        elif a.comando == "voz":
            if not a.revisao:
                raise ValueError("O comando voz exige --revisao (JSON da aprovação humana)")
            pasta = gerar_voz(
                a.entrada,
                a.revisao,
                provider=a.provider or "espeak",
                permitir_api=a.autorizar_api,
            )
        else:
            pasta = gerar_visual(
                referencia=a.referencia, permitir_api=a.autorizar_api
            )
    except (ValueError, RuntimeError, OSError, ErroAPI) as exc:
        print(f"Falha: {type(exc).__name__}: {_mensagem_erro(exc)}")
        return 2
    print("Evidências locais:", pasta)
    print("Nenhum envio externo de respostas foi realizado.")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "comando",
        nargs="?",
        choices=["verificar", "processar", "experimento", "imagem", *COMANDOS_MIDIA],
        default="processar",
    )
    p.add_argument(
        "entrada",
        nargs="?",
        help="audio/ocr: arquivo a processar; voz: minuta aprovada (.md)",
    )
    p.add_argument("--mock", action="store_true", help="simulação sem APIs reais")
    p.add_argument("--metaprompt-v2", action="store_true", help="experimento separado usando metaprompt revisado")
    p.add_argument("--caso", action="append")
    p.add_argument(
        "--decisoes",
        help="YAML contendo decisões de DEMONSTRAÇÃO; não é revisão de servidor real",
    )
    p.add_argument(
        "--autorizar-api",
        action="store_true",
        help="autoriza o envio de dados fictícios a provedores externos (áudio, voz, arte)",
    )
    p.add_argument("--provider", help="audio: local|groq; voz: espeak ou provedor TTS")
    p.add_argument("--modelo-local", default="small", help="audio local (Whisper)")
    p.add_argument("--gabarito", help="referência prévia da MESMA modalidade (audio/ocr)")
    p.add_argument("--revisado", help="texto revisado por pessoa (audio/ocr)")
    p.add_argument("--psm", type=int, default=6, help="ocr: modo de página do Tesseract")
    p.add_argument("--revisao", help="voz: JSON da aprovação humana da minuta")
    p.add_argument("--referencia", help="arte: imagem de referência (não é incorporada)")
    a = p.parse_args()
    cfg = carregar()
    if a.comando == "verificar":
        _verificar(cfg)
        return 0
    if a.comando in COMANDOS_MIDIA:
        return _comando_midia(a)
    if a.comando == "imagem":
        if a.mock:
            caminho = imagem_local(ROOT / "resultados/peca_visual.png")
        else:
            caminho = gerar(ROOT / "resultados/peca_visual.png")
        print(caminho)
        return 0
    if a.comando == "experimento":
        from .experimento import executar

        executar(mock=a.mock, metaprompt_v2=a.metaprompt_v2)
        return 0
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
                    permitir_api=a.autorizar_api,
                )
            )
        except (
            ErroAPI,
            ValueError,
            RuntimeError,
            OSError,
            EOFError,
            jsonschema.ValidationError,
        ) as exc:
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
            {
                "execucao": execucao,
                "casos": resumo,
                "taxa_aprovacao": taxa_aprovacao(resumo),
                "falhas": falhas,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
