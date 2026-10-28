"""Interface local: python -m streamlit run src/desafio6/app.py."""

from __future__ import annotations

import json
import hashlib
import sys
import uuid
from pathlib import Path

# Streamlit executa o arquivo como script; permite imports do pacote a partir da raiz.
RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.seguranca import FORMATOS_AUDIO, FORMATOS_IMAGEM, validar_arquivo


def apresentar_ausentes(valor):
    """Formata somente a exibição; o contrato persistido mantém null e sua lista de ausências."""
    if valor is None:
        return "não localizado"
    if isinstance(valor, dict):
        return {k: apresentar_ausentes(v) for k, v in valor.items()}
    if isinstance(valor, list):
        return [apresentar_ausentes(v) for v in valor]
    return valor


def modalidade_da_solicitacao(estado, selecionada: str) -> str:
    """A origem da extração acompanha o texto mesmo após mudar o seletor da interface."""
    origem = estado.get("origem_midia_desafio6")
    if isinstance(origem, dict) and origem.get("modalidade") in {"audio", "imagem"}:
        return origem["modalidade"]
    return {"Texto": "texto", "Áudio": "audio", "Imagem/PDF": "imagem"}[selecionada]


def registrar_origem_midia(estado, *, modalidade: str, caminho: Path, texto: str) -> None:
    if modalidade not in {"audio", "imagem"}:
        raise ValueError("Origem de mídia inválida")
    estado["origem_midia_desafio6"] = {
        "modalidade": modalidade, "arquivo": str(caminho),
        "sha256_original": hashlib.sha256(caminho.read_bytes()).hexdigest(),
        "sha256_bruto": hashlib.sha256(texto.encode("utf-8")).hexdigest(),
    }
    estado["texto_solicitacao"] = texto
    estado["conferencia_criticos"] = False


def iniciar_texto_independente(estado) -> None:
    for chave in ("origem_midia_desafio6", "resultado_desafio6"):
        estado.pop(chave, None)
    estado["texto_solicitacao"] = ""
    estado["conferencia_criticos"] = False


def salvar_arquivo_recebido(nome: str, conteudo: bytes, pasta, *, formatos=None) -> Path:
    """Guarda upload validado em nome gerado; o nome externo nunca determina o caminho."""
    sufixo = Path(nome).suffix.lower()
    formatos = formatos or {".txt", ".pdf"}
    if sufixo not in formatos:
        raise ValueError("Formato de arquivo não permitido")
    if not conteudo or len(conteudo) > 2 * 1024 * 1024:
        raise ValueError("Arquivo vazio ou acima do limite de 2 MB")
    if sufixo == ".txt":
        conteudo.decode("utf-8")
    raiz = Path(pasta).resolve()
    raiz.mkdir(parents=True, exist_ok=True)
    caminho = raiz / (uuid.uuid4().hex + sufixo)
    caminho.write_bytes(conteudo)
    try:
        validar_arquivo(caminho, formatos, max_mb=2)
    except (ValueError, OSError):
        caminho.unlink(missing_ok=True)
        raise
    return caminho


def carregar_catalogo(pasta) -> dict:
    from src.desafio6.acervo import carregar_catalogo_originais

    original = carregar_catalogo_originais()
    arquivo = Path(pasta) / "catalogo_uploads.json"
    extras = json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else {"documentos": []}
    excluidos_path = Path(pasta) / "excluidos.json"
    excluidos = set(json.loads(excluidos_path.read_text(encoding="utf-8"))) if excluidos_path.exists() else set()
    return {"versao": original.get("versao", "1.0"), "documentos": [
        d for d in original["documentos"] + extras.get("documentos", []) if d["id"] not in excluidos
    ]}


def adicionar_upload(pasta, nome: str, conteudo: bytes) -> dict:
    pasta = Path(pasta).resolve()
    caminho = salvar_arquivo_recebido(nome, conteudo, pasta / "uploads")
    documento = {
        "id": "UP_" + caminho.stem[:12], "titulo": Path(nome).stem[:120],
        "versao": "não localizado", "arquivo": str(caminho), "tema": "documento fornecido",
        "modalidade": "texto" if caminho.suffix == ".txt" else "ocr",
        "sha256": hashlib.sha256(conteudo).hexdigest(),
        "prioridade": None, "vigencia": None,
    }
    arquivo = pasta / "catalogo_uploads.json"
    catalogo = json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else {"versao": "1.0", "documentos": []}
    catalogo["documentos"].append(documento)
    temporario = arquivo.with_suffix(".tmp")
    temporario.write_text(json.dumps(catalogo, ensure_ascii=False, indent=2), encoding="utf-8")
    temporario.replace(arquivo)
    return documento


def remover_upload(pasta, documento_id: str) -> bool:
    """Remove somente documentos gerenciados pela interface; originais são protegidos."""
    pasta = Path(pasta).resolve()
    arquivo = pasta / "catalogo_uploads.json"
    if not arquivo.exists():
        return False
    catalogo = json.loads(arquivo.read_text(encoding="utf-8"))
    alvo = next((d for d in catalogo.get("documentos", []) if d.get("id") == documento_id), None)
    if alvo is None:
        return False
    caminho = Path(alvo["arquivo"]).resolve()
    caminho.relative_to((pasta / "uploads").resolve())
    caminho.unlink(missing_ok=True)
    catalogo["documentos"] = [d for d in catalogo["documentos"] if d.get("id") != documento_id]
    arquivo.write_text(json.dumps(catalogo, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def ler_avaliacoes_fornecidas(conteudo, *, max_registros=None) -> list[dict]:
    """Valida registros enviados pelo operador; não cria avaliações nem lê gabaritos."""
    if isinstance(conteudo, bytes):
        conteudo = conteudo.decode("utf-8-sig")
    if not isinstance(conteudo, str) or not conteudo.strip() or len(conteudo.encode("utf-8")) > 2 * 1024 * 1024:
        raise ValueError("Informe um JSON de avaliações não vazio, de até 2 MB")
    try:
        valor = json.loads(conteudo)
    except (ValueError, TypeError):
        raise ValueError("JSON de avaliações inválido") from None
    registros = valor.get("avaliacoes") if isinstance(valor, dict) else valor
    if not isinstance(registros, list) or not registros:
        raise ValueError("Informe uma lista não vazia de avaliações")
    if max_registros is not None and len(registros) > max_registros:
        raise ValueError("A quantidade de avaliações excede o orçamento de chamadas desta execução")
    ids, entradas = set(), []
    for item in registros:
        if not isinstance(item, dict) or set(item) != {"id", "texto"}:
            raise ValueError("Cada avaliação deve conter somente id e texto")
        id_avaliacao, texto = item["id"], item["texto"]
        if not isinstance(id_avaliacao, str) or not id_avaliacao.strip() or len(id_avaliacao) > 100 or id_avaliacao in ids:
            raise ValueError("As avaliações exigem IDs únicos, não vazios e de até 100 caracteres")
        if not isinstance(texto, str) or not texto.strip() or len(texto) > 12000:
            raise ValueError("Texto de avaliação vazio, inválido ou acima de 12000 caracteres")
        ids.add(id_avaliacao)
        entradas.append({"id": id_avaliacao, "texto": texto})
    return entradas


def _mostrar_resultado(st, fluxo, resultado):
    st.subheader("Minuta e evidências")
    if resultado.get("simulada"):
        st.warning("Simulação: esta saída não comprova execução de modelo real e não pode ser aprovada como tal.")
    st.write("Situação:", resultado.get("status", "pendente"))
    ficha = resultado.get("ficha")
    if ficha:
        st.write("Ficha validada")
        st.json(apresentar_ausentes(ficha))
    if resultado.get("resumo"):
        st.write("Resumo:", resultado["resumo"])
    st.markdown(resultado.get("minuta", resultado.get("resposta", "não localizado")))
    for trecho in resultado.get("trechos", []):
        rotulo = f"{trecho.get('documento_id', trecho.get('id', 'Fonte'))} · versão {trecho.get('versao', 'não localizado')}"
        with st.expander(rotulo):
            st.json(trecho)
    if resultado.get("fontes"):
        with st.expander("Fontes e passagens citadas", expanded=True):
            st.json(resultado["fontes"])
    st.caption("Conteúdo produzido com auxílio de IA. Similaridade indica proximidade vetorial; não é garantia de verdade.")
    id_resultado = resultado.get("id")
    if not id_resultado:
        return
    registro = fluxo.revisoes.obter(id_resultado)
    st.write("Revisão:", registro["estado"], "· versão", registro["versao"])
    with st.form("revisao_" + id_resultado):
        decisao = st.selectbox("Decisão", ["revisar", "rejeitar", "aprovar"])
        responsavel = st.text_input("Responsável pela decisão")
        justificativa = st.text_area("Justificativa da decisão")
        conferida = st.checkbox("Li esta versão da minuta e conferi suas fontes.")
        enviar = st.form_submit_button("Registrar revisão", disabled=bool(registro.get("simulada")))
    if enviar:
        if not conferida:
            st.error("Confira a minuta e suas fontes antes de registrar uma decisão.")
        else:
            try:
                atualizado = fluxo.revisoes.registrar_decisao(
                    id_resultado, decisao, responsavel, justificativa,
                    sha256_esperado=registro["sha256_minuta"], simulada=False,
                )
                fluxo._auditar(id_resultado, "revisao", estado=atualizado["estado"],
                               sha256_minuta=atualizado["sha256_minuta"])
                st.success("Decisão registrada: " + atualizado["estado"] + ". Nenhuma resposta foi enviada.")
            except (ValueError, PermissionError) as exc:
                st.error(str(exc))


def main():
    import streamlit as st

    from src.desafio6.fluxo import FluxoDesafio6
    from src.desafio6.metricas import agregar_painel
    from src.desafio6.sentimentos import classificar_avaliacoes

    st.set_page_config(page_title="Desafio 6 · Central de Atendimento", page_icon="📚", layout="wide")
    st.title("Central Inteligente de Atendimento")
    st.caption("Desafio 6 · FIC_DEV · SECITECI / Escola Técnica Estadual de Cuiabá")
    st.info("Protótipo acadêmico para consulta aos documentos fornecidos. Toda minuta exige revisão humana; nenhuma resposta é enviada automaticamente.")
    st.caption("Diego Assunção Leite · Ayron Brhenno Silva Figueiredo · Guilherme da Silva Lessa")
    # Uma nova instância a cada ação reinicia o orçamento da execução e reutiliza o índice persistido.
    fluxo = FluxoDesafio6()
    tabs = st.tabs(["Acervo", "Solicitação e consulta", "Revisões", "Avaliações e painel"])
    with tabs[0]:
        st.subheader("Documentos fornecidos e editais")
        catalogo = carregar_catalogo(fluxo.pasta)
        documentos = catalogo["documentos"]
        opcoes = {d["id"]: f"{d['id']} — {d['titulo']} · v{d['versao']}" for d in documentos}
        ids = st.multiselect("Documentos a indexar", list(opcoes), default=list(opcoes), format_func=opcoes.get)
        selecionado = {"versao": catalogo["versao"], "documentos": [d for d in documentos if d["id"] in ids]}
        st.caption("O acervo reúne os arquivos de dados/originais, exceto brasão e configuração. A indexação pode transmitir texto, áudio ou páginas digitalizadas à API OpenAI. Uploads adicionais: TXT UTF-8 ou PDF de até 2 MB; evite dados pessoais desnecessários.")
        upload = st.file_uploader("Incluir documento fornecido", type=["txt", "pdf"])
        if st.button("Adicionar ao acervo local", disabled=upload is None):
            try:
                adicionar_upload(fluxo.pasta, upload.name, upload.getvalue())
                st.success("Documento incluído. Atualize a indexação para disponibilizar seus trechos.")
                st.rerun()
            except (ValueError, UnicodeError, OSError):
                st.error("Arquivo inválido. Use TXT UTF-8 ou PDF textual dentro do limite.")
        try:
            estado = fluxo.indice.estado(fluxo.catalogo)
            if estado.get("vazio") or estado.get("desatualizado"):
                st.warning("O índice precisa ser criado ou atualizado para a seleção atual.")
            else:
                st.success("Índice persistente disponível.")
            with st.expander("Situação do índice"):
                st.json(estado)
        except (ValueError, OSError, RuntimeError):
            st.warning("Índice indisponível. Crie ou atualize a indexação.")
        if st.button("Indexar seleção", disabled=not ids):
            try:
                with st.spinner("Preparando documentos e embeddings…"):
                    caminho_catalogo = fluxo.pasta / "catalogo_selecionado.json"
                    caminho_catalogo.write_text(json.dumps(selecionado, ensure_ascii=False, indent=2), encoding="utf-8")
                    st.json(fluxo.indexar(caminho_catalogo))
                st.success("Indexação concluída. As próximas consultas reutilizam os vetores.")
            except (ValueError, OSError, RuntimeError):
                st.error("A indexação não foi concluída. Confira os arquivos, a chave local e os limites da execução.")
        excluir_id = st.selectbox("Documento a retirar da busca e dos derivados", [""] + list(opcoes), format_func=lambda x: opcoes.get(x, "Selecione"))
        if st.button("Excluir do índice e dos derivados", disabled=not excluir_id):
            try:
                fluxo.excluir(excluir_id)
                remover_upload(fluxo.pasta, excluir_id)
                st.success("Trechos e derivados excluídos. Os documentos originais foram preservados.")
                st.session_state.pop("resultado_desafio6", None)
            except (ValueError, OSError, RuntimeError):
                st.error("Não foi possível concluir a exclusão; confira os registros locais.")
    with tabs[1]:
        st.subheader("Compreensão e resposta com fontes")
        modalidade = st.radio("Entrada", ["Texto", "Áudio", "Imagem/PDF"], horizontal=True)
        if st.session_state.get("origem_midia_desafio6"):
            st.caption("Este texto mantém vínculo com a mídia original e exige conferência, mesmo ao selecionar Texto.")
            st.button("Iniciar solicitação textual independente", on_click=iniciar_texto_independente, args=(st.session_state,))
        if modalidade != "Texto":
            formatos = FORMATOS_AUDIO if modalidade == "Áudio" else FORMATOS_IMAGEM
            midia = st.file_uploader("Arquivo fornecido para extração", type=[x.lstrip(".") for x in sorted(formatos)], key="midia_desafio6")
            st.caption("Ao extrair, o arquivo ou suas páginas serão processados pela API OpenAI. Use conteúdo autorizado e evite dados sensíveis desnecessários.")
            if st.button("Extrair texto da mídia", disabled=midia is None):
                try:
                    caminho = salvar_arquivo_recebido(midia.name, midia.getvalue(), fluxo.pasta / "entradas", formatos=formatos)
                    with st.spinner("Extraindo texto; nomes, datas e protocolos exigem conferência…"):
                        origem_modalidade = "audio" if modalidade == "Áudio" else "imagem"
                        extracao = fluxo.extrair_midia(caminho, origem_modalidade)
                        texto = extracao["texto"]
                    caminho.with_suffix(caminho.suffix + ".bruto.txt").write_text(texto, encoding="utf-8")
                    caminho.with_suffix(caminho.suffix + ".extracao.json").write_text(json.dumps(extracao, ensure_ascii=False, indent=2), encoding="utf-8")
                    registrar_origem_midia(st.session_state, modalidade=origem_modalidade, caminho=caminho, texto=texto)
                except (ValueError, OSError, RuntimeError):
                    st.error("A extração não foi concluída. Confira o arquivo e a disponibilidade do serviço OpenAI.")
        texto = st.text_area("Solicitação ou texto extraído", height=180, max_chars=12000, key="texto_solicitacao", on_change=lambda: st.session_state.update(conferencia_criticos=False))
        origem_modalidade = modalidade_da_solicitacao(st.session_state, modalidade)
        conferencia = st.checkbox("Conferi nomes, protocolos e datas no arquivo original.", disabled=origem_modalidade == "texto", key="conferencia_criticos")
        pergunta = st.text_input("Pergunta ao acervo institucional", max_chars=2000)
        consultar = st.button("Consultar fontes e preparar minuta", type="primary", disabled=not pergunta.strip())
        if consultar:
            try:
                with st.spinner("Validando dados, recuperando trechos e preparando a minuta…"):
                    if texto.strip():
                        resultado = fluxo.processar(texto, pergunta, modalidade=origem_modalidade, conferencia=conferencia)
                    else:
                        resultado = fluxo.consultar(pergunta)
                st.session_state["resultado_desafio6"] = resultado
            except (ValueError, OSError, RuntimeError):
                st.error("Não foi possível preparar a minuta. Confira as lacunas, o índice e a disponibilidade da API; dados não foram aprovados.")
        resultado = st.session_state.get("resultado_desafio6")
        if resultado:
            try:
                _mostrar_resultado(st, fluxo, resultado)
            except (ValueError, OSError, KeyError):
                st.warning("Esta versão não está disponível para revisão; execute uma nova consulta.")
    with tabs[2]:
        st.subheader("Decisões preservadas")
        registros = fluxo.revisoes.listar()
        filtro = st.multiselect("Estados", ["pendente", "aprovada", "rejeitada", "revisar"])
        painel = agregar_painel(registros, filtros={"estado": filtro} if filtro else None)
        st.metric("Minutas nesta seleção", painel["total"])
        for registro in painel["registros"]:
            with st.expander(f"{registro['id']} · {registro['estado']} · versão {registro['versao']}"):
                st.markdown(registro["minuta"])
                st.json({k: v for k, v in registro.items() if k != "minuta"})
        if not painel["total"]:
            st.caption("Nenhuma minuta nesta seleção.")
    with tabs[3]:
        st.subheader("Avaliações fornecidas pelo operador")
        st.caption("A polaridade descreve a mensagem; não representa diagnóstico, personalidade ou sentimento da população.")
        st.caption("Envie JSON com uma lista de registros contendo somente id e texto, ou um objeto com a lista avaliacoes. O conteúdo será minimizado e classificado pela API OpenAI; não há avaliações pré-preenchidas.")
        entrada_json = st.text_area("Avaliações em JSON", height=120, key="avaliacoes_json")
        upload_json = st.file_uploader("Ou carregar arquivo JSON de avaliações", type=["json"], key="avaliacoes_upload")
        arquivo = fluxo.pasta / "sentimentos.json"
        if not entrada_json.strip() and upload_json is None:
            st.caption("Nenhuma avaliação fornecida. O painel permanece vazio até receber avaliações do operador.")
        if st.button("Classificar avaliações fornecidas", disabled=not entrada_json.strip() and upload_json is None):
            try:
                entradas = ler_avaliacoes_fornecidas(upload_json.getvalue() if upload_json is not None else entrada_json,
                                                     max_registros=fluxo.cliente.orcamento.max_chamadas)
                with st.spinner("Classificando avaliações com a OpenAI…"):
                    resultados = classificar_avaliacoes(entradas, fluxo.cliente)
                arquivo.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
            except (ValueError, OSError, RuntimeError):
                st.error("A classificação não foi concluída; confira os limites e a disponibilidade da API.")
        resultados = json.loads(arquivo.read_text(encoding="utf-8")) if arquivo.exists() else []
        filtro = st.multiselect("Polaridades", ["positiva", "negativa", "neutra", "indeterminada"])
        painel = agregar_painel(resultados, filtros={"polaridade": filtro} if filtro else None)
        st.metric("Avaliações na seleção", painel["total"])
        if painel["por_polaridade"]:
            st.bar_chart(painel["por_polaridade"])
            st.dataframe(painel["registros"], width="stretch")
            st.json(painel["percentuais_polaridade"])
        else:
            st.caption("Sem avaliações nesta seleção; percentuais não calculados porque o denominador é zero.")


if __name__ == "__main__":
    main()
