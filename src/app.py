"""Assistente de documentos — Desafio 6 (RF20). Execute: streamlit run src/app.py

Protótipo local para revisão humana. Nenhuma resposta é enviada automaticamente.
Variáveis opcionais (usadas pelos testes): D6_EMBEDDING_PROVIDER, D6_DIR_INDICE, D6_BANCO_REVISAO,
D6_ARQUIVO_AUDITORIA.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402
import yaml  # noqa: E402

from src import contrato, guardrails  # noqa: E402
from src.config import carregar  # noqa: E402

st.set_page_config(page_title="Central Inteligente — Desafio 6", page_icon="🏛️", layout="wide")


@st.cache_resource
def recursos():
    from src.embeddings import criar_embedder
    from src.revisao import RepositorioRevisao

    cfg = carregar()
    if os.getenv("D6_EMBEDDING_PROVIDER"):
        cfg["recuperacao"]["embedding_provider"] = os.environ["D6_EMBEDDING_PROVIDER"]
        cfg["recuperacao"]["embedding_modelo"] = "hash-bow-teste-v1"
    banco = Path(os.getenv("D6_BANCO_REVISAO") or ROOT / cfg["revisao"]["banco"])
    return cfg, criar_embedder(cfg), RepositorioRevisao(banco)


def indice(cfg, embedder, rotulo):
    from src.indice import IndiceVetorial

    return IndiceVetorial.de_config(cfg, embedder, rotulo, diretorio=os.getenv("D6_DIR_INDICE") or None)


def arquivo_auditoria(cfg):
    return Path(os.getenv("D6_ARQUIVO_AUDITORIA") or ROOT / cfg["auditoria"]["arquivo"])


def selo_status(status: str) -> None:
    textos = {
        "fundamentada": ("success", "✅ Fundamentada — afirmações conferidas contra os trechos citados."),
        "sem_evidencia_suficiente": ("warning", "⚠️ Sem evidência suficiente — o sistema se absteve; encaminhar ao operador."),
        "conflito_de_fontes": ("error", "⛔ Conflito de fontes — divergência sem regra de prioridade; revisão humana obrigatória."),
        "bloqueada": ("error", "🛑 Bloqueada pelos guardrails."),
        "falha": ("error", "❌ Falha no processamento (registrada na auditoria)."),
    }
    tipo, texto = textos.get(status, ("info", status))
    getattr(st, tipo)(texto)


def mostrar_trechos(trechos: list[dict]) -> None:
    st.caption(
        "Similaridade = 1 − distância de cosseno (0 a 1; maior = mais próximo em significado). "
        "É uma medida de proximidade, **não** garantia de que o trecho responda ou seja verdadeiro."
    )
    for t in trechos:
        rotulo = f"#{t.get('posicao', '')} {t['local']} — similaridade {t['similaridade']:.3f}"
        if t.get("em_quarentena"):
            rotulo += " — 🚫 QUARENTENA (instrução suspeita; não usado)"
        elif t.get("abaixo_limiar"):
            rotulo += " — abaixo do limiar"
        with st.expander(rotulo):
            st.write(t["trecho"])
            st.caption(f"chunk_id: `{t['chunk_id']}` · distância de cosseno: {t.get('distancia_cosseno', '—')}")


def mostrar_rag(r: dict) -> None:
    selo_status(r["status"])
    st.markdown("**Resposta (somente afirmações verificadas):**")
    st.write(r["resposta"])
    if r.get("fontes"):
        st.markdown("**Fontes citadas**")
        for f in r["fontes"]:
            with st.expander(f"{f['local']} · `{f['chunk_id']}`"):
                st.write(f["trecho"])
    if r.get("afirmacoes_removidas"):
        st.warning(f"{len(r['afirmacoes_removidas'])} afirmação(ões) do gerador removida(s) por falta de suporte.")
    if r.get("motivos_revisao"):
        st.info("Motivos para revisão: " + "; ".join(r["motivos_revisao"]))
    if r.get("erros"):
        st.error("Erros: " + "; ".join(r["erros"]))


def main():
    cfg, embedder, repo = recursos()
    perfis = list(cfg["geracao"]["perfis"])
    with st.sidebar:
        st.header("Configuração")
        perfil = st.selectbox("Perfil de geração", perfis, index=perfis.index("extrativo_local") if "extrativo_local" in perfis else 0)
        dados_perfil = cfg["geracao"]["perfis"][perfil]
        st.caption(f"Tipo: `{dados_perfil['tipo']}` — " + dados_perfil.get("descricao", f"{dados_perfil.get('provider')} / {dados_perfil.get('modelo')}"))
        if dados_perfil["tipo"] == "mock":
            st.warning("Perfil SIMULADO: não representa um modelo real.")
        rotulos = list(cfg["recuperacao"]["chunking"])
        rotulo = st.selectbox("Chunking", rotulos, index=rotulos.index(cfg["recuperacao"]["configuracao_chunking"]))
        top_k = st.slider("top-k", 1, 10, int(cfg["recuperacao"]["top_k"]))
        operador = st.text_input("Operador responsável (obrigatório para decidir)")
        st.divider()
        st.markdown("🔒 **Nenhuma resposta é enviada automaticamente.** Aprovar = liberar para envio manual.")
    from src.geracao import criar_gerador
    from src.indice import ReindexacaoExigida
    from src.ingestao import carregar_catalogo

    ix = indice(cfg, embedder, rotulo)
    gerador = criar_gerador(cfg, perfil)
    try:
        catalogo = carregar_catalogo(cfg)
        status = ix.status(catalogo)
    except Exception as exc:  # catálogo corrompido ou índice ilegível
        st.error(f"Falha ao ler acervo/índice: {exc}")
        return

    st.title("🏛️ Central Inteligente de Atendimento — Assistente de Documentos")
    st.caption("Desafio 6 (Desafio Prático 02) · dados exclusivamente fictícios · protótipo para revisão humana")
    if status["estado"] == "reindexacao_exigida":
        st.error(f"Índice exige reindexação: {status['motivo']}. Use 'Recriar índice' na aba Acervo.")
    elif status["estado"] == "vazio":
        st.warning("Índice vazio: indexe o acervo na aba Acervo antes de consultar.")
    elif status["estado"] == "desatualizado":
        st.warning(
            "Índice desatualizado — não indexados: {0}; alterados: {1}; órfãos: {2}.".format(
                ", ".join(status["nao_indexados"]) or "—", ", ".join(status["desatualizados"]) or "—", ", ".join(status["orfaos"]) or "—"
            )
        )

    abas = st.tabs(["📚 Acervo", "📝 Solicitação", "🔎 Consulta", "✅ Revisão", "📊 Sentimentos", "🧾 Auditoria"])

    # ------------------------------------------------------------------ Acervo
    with abas[0]:
        st.subheader("Acervo institucional fictício")
        m = ix.manifesto()["documentos"]
        st.dataframe(
            [
                {"id": d["id"], "título": d["titulo"], "versão": d["versao"], "formato": d.get("formato"),
                 "tema": d.get("tema"), "indexado": d["id"] in m, "trechos": m.get(d["id"], {}).get("trechos", 0),
                 "suspeitos": m.get(d["id"], {}).get("suspeitos", 0), "excluído": d["id"] in status["excluidos"]}
                for d in catalogo
            ],
            width="stretch",
        )
        st.caption(f"Coleção `{status['colecao']}` · {status['trechos']} trechos · embedding `{status['embedding_modelo']}` "
                   f"(dimensão {status['dimensao']}) · índice v{status['versao_indice']} · chunking {status['chunking']}")
        c1, c2 = st.columns(2)
        if c1.button("Indexar acervo (sem duplicar)"):
            with st.spinner("Gerando embeddings e indexando..."):
                try:
                    st.json(ix.indexar(catalogo))
                except ReindexacaoExigida as exc:
                    st.error(str(exc))
        if c2.button("Recriar índice (troca de embedding)"):
            with st.spinner("Recriando índice..."):
                st.json(ix.indexar(catalogo, recriar=True))
        with st.expander("Incluir documento (TXT ou PDF textual, fictício)"):
            arq = st.file_uploader("Arquivo", type=["txt", "pdf"], key="up_doc")
            novo_id = st.text_input("ID (ex.: DOC-08)")
            titulo = st.text_input("Título")
            versao = st.text_input("Versão", value="1.0")
            tema = st.text_input("Tema", value="atendimento_cidadao")
            if st.button("Salvar no acervo") and arq is not None:
                try:
                    conteudo = arq.getvalue()
                    guardrails.validar_documento(arq.name, conteudo, cfg)
                    if not novo_id or not titulo or any(d["id"] == novo_id for d in catalogo):
                        raise ValueError("Informe ID único e título")
                    pasta = ROOT / cfg["acervo"]["diretorio_enviados"]
                    destino = guardrails.destino_documento_enviado(pasta, novo_id, Path(arq.name).suffix.lower())
                    pasta.mkdir(parents=True, exist_ok=True)
                    destino.write_bytes(conteudo)
                    cat_path = ROOT / cfg["acervo"]["catalogo_enviados"]
                    dados = (yaml.safe_load(cat_path.read_text(encoding="utf-8")) if cat_path.is_file() else None) or {"documentos": []}
                    dados["documentos"].append({"id": novo_id, "titulo": titulo, "versao": versao, "tema": tema,
                                                "formato": destino.suffix.lstrip("."), "arquivo": str(destino.relative_to(ROOT)).replace("\\", "/"),
                                                "prioridade": 1, "substitui": []})
                    cat_path.write_text(yaml.safe_dump(dados, allow_unicode=True, sort_keys=False), encoding="utf-8")
                    st.success("Documento salvo. O índice ficou desatualizado: clique em 'Indexar acervo'.")
                except ValueError as exc:
                    st.error(f"Documento recusado: {exc}")
        with st.expander("Excluir documento do índice (RF24)"):
            alvo = st.selectbox("Documento", [d["id"] for d in catalogo], key="del_doc")
            confirmar = st.checkbox("Confirmo a exclusão dos vetores e resultados derivados deste documento")
            if st.button("Excluir") and confirmar:
                from src.privacidade import excluir_documento_e_derivados

                indices = [indice(cfg, embedder, r) for r in cfg["recuperacao"]["chunking"]]
                st.json(excluir_documento_e_derivados(alvo, cfg=cfg, indices=indices, repositorio=repo,
                                                      arquivo_auditoria=arquivo_auditoria(cfg)))

    # ------------------------------------------------------------------ Solicitação
    with abas[1]:
        st.subheader("Nova solicitação")
        modo = st.radio(
            "Entrada",
            ["Texto digitado", "Arquivo .txt", "Transcrição de áudio reaproveitada (Desafio 01)",
             "OCR reaproveitado (Desafio 01)", "Novo áudio (STT)", "Nova imagem/PDF (OCR)"],
            horizontal=False,
        )
        texto, modalidade = "", "texto"
        if modo == "Texto digitado":
            texto = st.text_area("Texto da solicitação", height=180)
        elif modo == "Arquivo .txt":
            up = st.file_uploader("Solicitação (.txt)", type=["txt"], key="up_sol")
            texto = up.getvalue().decode("utf-8", errors="replace") if up else ""
        elif modo.startswith("Transcrição"):
            texto = (ROOT / "resultados/multimodal/referencias/referencia_audio_conferida.txt").read_text(encoding="utf-8")
            modalidade = "audio"
            st.text_area("Transcrição preservada (somente leitura)", texto, height=150, disabled=True)
        elif modo.startswith("OCR reaproveitado"):
            texto = (ROOT / "resultados/multimodal/referencias/referencia_ocr_conferida.txt").read_text(encoding="utf-8")
            modalidade = "imagem"
            st.text_area("Texto OCR conferido (somente leitura)", texto, height=150, disabled=True)
        else:
            tipos = ["mp3", "wav", "m4a", "ogg"] if "áudio" in modo else ["png", "jpg", "jpeg", "pdf"]
            up = st.file_uploader("Arquivo", type=tipos, key="up_mm")
            modalidade = "audio" if "áudio" in modo else "imagem"
            if up is not None and st.button("Transcrever / extrair texto"):
                try:
                    temp = guardrails.caminho_upload_seguro(ROOT / "resultados" / "arquivos_fornecidos", up.name)
                    temp.parent.mkdir(parents=True, exist_ok=True)
                    temp.write_bytes(up.getvalue())
                    with st.spinner("Processando mídia..."):
                        if modalidade == "audio":
                            from src.audio import transcrever

                            st.session_state["texto_mm"] = transcrever(temp)
                        else:
                            from src.visao import ler_imagem

                            mm = cfg["multimodal"]
                            st.session_state["texto_mm"] = ler_imagem(temp, provider=mm.get("ocr_provider", "local"), modelo=mm.get("ocr_modelo"))
                except Exception as exc:
                    st.error(f"Falha no STT/OCR (credencial ou ferramenta ausente?): {type(exc).__name__}: {str(exc)[:200]}")
            texto = st.text_area("Texto extraído — revise nomes, datas e protocolos antes de processar",
                                 st.session_state.get("texto_mm", ""), height=150)
        if st.button("Processar solicitação", type="primary", disabled=not texto.strip()):
            from src.orcamento import Orcamento
            from src.pipeline import processar_solicitacao

            with st.spinner("Validando, estruturando, consultando o acervo e preparando a minuta..."):
                try:
                    r = processar_solicitacao(
                        texto, caso_id=f"UI-{len(repo.listar()) + 1:03d}", modalidade=modalidade, cfg=cfg, indice=ix,
                        gerador=gerador, repositorio=repo, orcamento=Orcamento.de_config(cfg),
                        arquivo_auditoria=arquivo_auditoria(cfg),
                    )
                    st.session_state["ultima_solicitacao"] = r
                except Exception as exc:
                    st.error(f"Falha no processamento: {type(exc).__name__}: {str(exc)[:200]}")
        r = st.session_state.get("ultima_solicitacao")
        if r:
            cor = {"permitir": "success", "revisar": "warning", "bloquear": "error"}[r["decisao"]]
            getattr(st, cor)(f"Decisão de entrada: **{r['decisao']}**")
            if r["motivos"]:
                st.write("Motivos: " + "; ".join(r["motivos"]))
            est = r.get("estruturacao")
            if est:
                st.markdown(f"**Ficha estruturada** (contrato v{contrato.VERSAO_SCHEMA}, modo `{est['modo']}`, válida: {est['valido']})")
                ficha = est["ficha"] or {}
                st.table({"campo": list(contrato.CAMPOS), "valor": [contrato.exibir(ficha.get(c)) for c in contrato.CAMPOS]})
                if est["erros"]:
                    st.error("Erros de validação: " + "; ".join(est["erros"]))
            comp = r.get("compreensao")
            if comp:
                st.markdown(f"**Categoria:** `{comp['categoria']}` · **Resumo** ({comp['palavras']}/{comp['limite_palavras']} palavras, {comp['metodo_resumo']}):")
                st.write(comp["resumo"])
                c1, c2 = st.columns(2)
                c1.markdown("**Entidades literais (com evidência)**")
                c1.dataframe([{k: e[k] for k in ("tipo", "valor", "evidencia")} for e in comp["entidades_literais"]] or [{"tipo": "—", "valor": "nenhuma", "evidencia": ""}])
                c2.markdown("**Inferências (não literais)**")
                c2.dataframe(comp["inferencias"] or [{"campo": "—", "valor": "nenhuma", "base": ""}])
            if r.get("rag"):
                selo_status(r["rag"]["status"])
                for f in r["rag"]["fontes"]:
                    with st.expander(f"Fonte: {f['local']} · `{f['chunk_id']}`"):
                        st.write(f["trecho"])
            if r.get("minuta"):
                st.markdown(f"**Minuta `{r['minuta_id']}` — estado: PENDENTE** (decida na aba Revisão)")
                st.markdown(r["minuta"])

    # ------------------------------------------------------------------ Consulta
    with abas[2]:
        st.subheader("Consulta independente ao acervo (sem memória conversacional)")
        pergunta = st.text_input("Pergunta")
        if st.button("Consultar", disabled=not pergunta.strip()):
            from src.rag import responder

            with st.spinner("Recuperando trechos e verificando citações..."):
                st.session_state["ultima_consulta"] = responder(
                    pergunta, indice=ix, gerador=gerador, cfg=cfg, top_k=top_k, arquivo_auditoria=arquivo_auditoria(cfg)
                )
        rc = st.session_state.get("ultima_consulta")
        if rc:
            mostrar_rag(rc)
            if rc.get("trechos_recuperados"):
                st.markdown(f"**Trechos recuperados (top-{rc['top_k']}, limiar {rc['limiar_similaridade']})**")
                mostrar_trechos(rc["trechos_recuperados"])
            st.caption(f"Gerador: {rc['gerador'].get('perfil')} (LLM: {rc['gerador'].get('e_llm')}) · latência {rc['latencia_ms']} ms · "
                       f"tokens: {rc['gerador'].get('tokens_entrada', 'indisponível')} / custo: {rc['gerador'].get('custo_usd', 'indisponível')}")

    # ------------------------------------------------------------------ Revisão
    with abas[3]:
        st.subheader("Revisão humana das minutas")
        cont = repo.contagem()
        cols = st.columns(4)
        for col, (estado, n) in zip(cols, cont["estados"].items()):
            col.metric(estado, n)
        filtro = st.selectbox("Filtrar por estado", ["todos", "pendente", "revisar", "aprovada", "rejeitada"])
        minutas = repo.listar(None if filtro == "todos" else filtro)
        if not minutas:
            st.info("Nenhuma minuta neste estado.")
        else:
            escolha = st.selectbox("Minuta", [m["id"] for m in minutas],
                                   format_func=lambda i: f"{i} — {next(m['status'] for m in minutas if m['id'] == i)}")
            m = repo.obter(escolha)
            st.caption(f"Caso {m['caso_id']} · criada {m['criada_em']} · gerador `{m['gerador']}` · "
                       f"IA/automação participou: {'sim' if m['ia_participou'] else 'não'} · SHA-256 {m['sha256'][:16]}…")
            st.markdown(m["conteudo"])
            hist = repo.historico(escolha)
            if hist:
                st.markdown("**Histórico de decisões**")
                st.dataframe([{k: h[k] for k in ("decidida_em", "decisao", "status_anterior", "status_novo", "operador", "justificativa", "origem")} for h in hist])
            if m["status"] in ("pendente", "revisar"):
                decisao = st.radio("Decisão", ["aprovar", "rejeitar", "revisar"], horizontal=True)
                justificativa = st.text_area("Justificativa (obrigatória)")
                if st.button("Registrar decisão humana"):
                    try:
                        reg = repo.registrar_decisao(escolha, decisao, operador, justificativa, "humana_interface")
                        from src.auditoria import registrar_d6

                        registrar_d6("decisao_humana", arquivo=arquivo_auditoria(cfg), minuta_id=escolha,
                                     decisao_humana=reg["decisao"], status_novo=reg["status_novo"], origem=reg["origem"],
                                     sha256_minuta=reg["sha256_minuta"], operador_informado=bool(operador))
                        st.success(f"Decisão registrada: {reg['status_novo']}. Nada foi enviado ao cidadão.")
                    except ValueError as exc:
                        st.error(str(exc))
            else:
                st.info("Decisão final registrada para esta versão. Alterações exigem nova minuta.")

    # ------------------------------------------------------------------ Sentimentos
    with abas[4]:
        st.subheader("Painel de sentimentos das avaliações fictícias")
        st.caption("Rótulos descrevem o TEXTO, não a pessoa. Confiança declarada por modelo é estimativa não calibrada. "
                   "Totais e percentuais são contagens determinísticas por código.")
        from src.metricas import POLARIDADES, agregar_sentimentos
        from src.sentimento import classificar_llm, classificar_local

        avals = yaml.safe_load((ROOT / "dados/avaliacoes/avaliacoes.yaml").read_text(encoding="utf-8"))["avaliacoes"]
        gab = yaml.safe_load((ROOT / "dados/gabaritos/desafio6/sentimentos.yaml").read_text(encoding="utf-8"))["avaliacoes"]
        if st.button("Classificar as 12 avaliações"):
            with st.spinner("Classificando..."):
                try:
                    if dados_perfil["tipo"] == "llm":
                        from src.orcamento import Orcamento

                        orc = Orcamento.de_config(cfg)
                        st.session_state["sentimentos"] = [classificar_llm(a["id"], a["texto"], dados_perfil, orc) for a in avals]
                    else:
                        st.session_state["sentimentos"] = [classificar_local(a["id"], a["texto"]) for a in avals]
                except Exception as exc:
                    st.error(f"Falha na classificação: {type(exc).__name__}: {str(exc)[:200]}")
        resultados = st.session_state.get("sentimentos", [])
        c1, c2 = st.columns(2)
        pols = c1.multiselect("Polaridade", POLARIDADES, default=list(POLARIDADES))
        rev = c2.selectbox("Requer revisão", ["todas", "sim", "não"])
        ag = agregar_sentimentos(resultados, gab, polaridade=pols or None,
                                 requer_revisao=None if rev == "todas" else rev == "sim")
        if not resultados:
            st.info("Nenhuma avaliação classificada nesta sessão. "
                    "Clique em 'Classificar as 12 avaliações' para carregar o painel.")
        elif ag["total"] == 0:
            st.info("Conjunto vazio para os filtros atuais (0/0): nenhum percentual é calculado.")
        else:
            cols = st.columns(len(POLARIDADES) + 1)
            cols[0].metric("Total (IDs únicos)", ag["total"])
            for col, p in zip(cols[1:], POLARIDADES):
                col.metric(p, ag["por_polaridade"][p]["numerador"], ag["por_polaridade"][p]["texto"], delta_color="off")
            st.bar_chart({p: ag["por_polaridade"][p]["numerador"] for p in POLARIDADES})
            st.write(f"Requer revisão: {ag['requer_revisao']['texto']} · Acurácia vs. gabarito: {ag['acuracia']['texto']}")
            if ag["ids_duplicados_removidos"]:
                st.caption("IDs duplicados removidos: " + ", ".join(ag["ids_duplicados_removidos"]))
            textos = {a["id"]: a["texto"] for a in avals}
            st.dataframe([{**{k: r.get(k) for k in ("id", "polaridade", "requer_revisao", "justificativa", "metodo")},
                           "esperado": gab.get(r["id"], {}).get("polaridade"), "texto": textos.get(r["id"])}
                          for r in resultados if (not pols or r["polaridade"] in pols)
                          and (rev == "todas" or r["requer_revisao"] == (rev == "sim"))], width="stretch")

    # ------------------------------------------------------------------ Auditoria
    with abas[5]:
        st.subheader("Trilha de auditoria (sanitizada)")
        caminho = arquivo_auditoria(cfg)
        if not caminho.is_file():
            st.info("Ainda não há eventos de auditoria.")
        else:
            eventos = [json.loads(l) for l in caminho.read_text(encoding="utf-8").splitlines()[-200:] if l.strip()]
            tipos = sorted({e["tipo"] for e in eventos})
            escolhidos = st.multiselect("Tipos", tipos, default=tipos)
            st.dataframe([{k: e.get(k) for k in ("registrado_em", "tipo", "status", "decisao_entrada", "latencia_ms", "erros", "decisao_humana")}
                          for e in reversed(eventos) if e["tipo"] in escolhidos], width="stretch")
            st.caption("Identificadores mascarados; credenciais nunca são registradas. Tokens/custo: 'indisponível' quando o provedor não informa.")


main()
