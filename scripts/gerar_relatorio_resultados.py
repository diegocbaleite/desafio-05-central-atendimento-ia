"""Gera documentacao/desafio6/resultados_avaliacao.md a partir das evidências JSON publicadas.

Uso: python scripts/gerar_relatorio_resultados.py
Os números vêm exclusivamente de documentacao/desafio6/evidencias/*.json (nenhum valor digitado).
"""

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "documentacao" / "desafio6" / "evidencias"


def carregar(nome):
    return json.loads((EV / nome).read_text(encoding="utf-8"))


def celula(valor, limite=160):
    texto = str(valor).replace("|", "/").replace("\n", " ")
    return texto if len(texto) <= limite else texto[: limite - 1] + "…"


def tabela(cabecalho, linhas):
    saida = ["| " + " | ".join(cabecalho) + " |", "|" + "---|" * len(cabecalho)]
    saida += ["| " + " | ".join(celula(c) for c in linha) + " |" for linha in linhas]
    return "\n".join(saida)


def main():
    resumo = carregar("resumo.json")
    j = carregar("rf14_comparacao_json.json")
    n = carregar("rf15_nlp_solicitacoes.json")
    at = carregar("rf16_ataques.json")
    t5 = carregar("rf16_t05_limites.json")
    t6 = carregar("rf17_t06_persistencia.json")
    ch = carregar("rf18_chunking.json")
    rag = carregar("rf19_rag_oito_perguntas.json")
    t11 = carregar("rf20_rf24_t11_revisao.json")
    t12 = carregar("rf21_t12_troca_gerador.json")
    se = carregar("rf22_sentimentos.json")
    t13 = carregar("rf23_t13_agregacao.json")
    t14 = carregar("rf24_t14_exclusao.json")
    t15 = carregar("rf23_t15_regressao.json")
    textos_av = {a["id"]: a["texto"] for a in yaml.safe_load((ROOT / "dados/avaliacoes/avaliacoes.yaml").read_text(encoding="utf-8"))["avaliacoes"]}
    gab_se = yaml.safe_load((ROOT / "dados/gabaritos/desafio6/sentimentos.yaml").read_text(encoding="utf-8"))["avaliacoes"]

    p = []
    p.append("# Resultados da avaliação — Desafio 6 (Desafio Prático 02)\n")
    p.append(
        f"Gerado por `scripts/gerar_relatorio_resultados.py` a partir de `documentacao/desafio6/evidencias/` "
        f"(execução `{resumo['id_execucao']}`, {resumo['data_utc'][:19]} UTC, {resumo['duracao_s']} s).\n"
    )
    p.append(
        f"> **Natureza das evidências:** gerador `{resumo['gerador']['perfil']}` (LLM: {resumo['gerador']['e_llm']}); "
        f"embedding local real `{resumo['embedding']}`. Nenhuma chamada a LLM real foi concluída (sem credencial). "
        "Extração e sentimentos usam **regras locais**; trechos marcados como SIMULADO usam respostas fixas. "
        "As regras foram escritas conhecendo o conjunto de teste: as métricas são otimistas e não medem generalização.\n"
    )

    p.append("## RF14 — JSON sintático × esquema × regras de negócio\n")
    p.append(f"Caso base: {j['caso_base']}.\n")
    p.append(tabela(
        ["Variante", "JSON sintático", "Esquema", "Regras", "Minuta permitida", "Tipos de erro"],
        [[v["variante"], v["json_sintatico_valido"], v["esquema_valido"], v["regras_validas"], v["minuta_permitida"], ", ".join(v["tipos_de_erro"]) or "—"]
         for v in j["variantes"]],
    ))
    li, lc = j["llm_simulado_invalido_duas_vezes"], j["llm_simulado_corrigido_na_segunda"]
    p.append(
        f"\n- LLM SIMULADO inválido duas vezes: válido={li['valido']}, {li['tentativas']} tentativas, "
        f"{li['chamadas_no_orcamento']} chamadas contadas no orçamento (correção incluída).\n"
        f"- LLM SIMULADO corrigido na 2ª tentativa: válido={lc['valido']}, {lc['tentativas']} tentativas.\n"
        f"- Fluxo completo com data 31/02/2026: decisão `{j['fluxo_T02_data_impossivel']['decisao']}`, "
        f"minuta gerada={j['fluxo_T02_data_impossivel']['minuta_gerada']}.\n"
    )

    p.append("## RF15 — Resumo, categoria e entidades (6 solicitações)\n")
    m = n["metricas"]
    p.append(tabela(["Métrica", "Resultado"], [
        ["Acurácia de categoria", m["acuracia_categoria"]["texto"]],
        ["Campos críticos (protocolo, data, solicitante)", m["campos_criticos_corretos"]["texto"]],
        ["Campos ausentes corretos", m["campos_ausentes_corretos"]["texto"]],
        ["Entidades esperadas encontradas", m["entidades_recall"]["texto"]],
        ["Entidades incorretas (extras)", m["entidades_incorretas"]],
        ["Fatos essenciais presentes no resumo", m["fatos_essenciais_presentes"]["texto"]],
        ["Resumos com fato sem suporte", m["resumos_com_fato_sem_suporte"]],
        ["Resumos com até 100 palavras", m["resumos_dentro_de_100_palavras"]["texto"]],
        ["Decisão de entrada igual ao gabarito", m["decisao_correta"]["texto"]],
    ]))
    p.append("")
    p.append(tabela(
        ["ID", "Categoria (esp./obt.)", "Decisão (esp./obt.)", "Omissões", "Fatos sem suporte", "Palavras", "Status RAG da minuta"],
        [[s["id"], f"{s['categoria_esperada']} / {s['categoria_obtida']}", f"{s['decisao_esperada']} / {s['decisao_obtida']}",
          ", ".join(s["fatos_omitidos"]) or "—", ", ".join(s["fatos_sem_suporte"]) or "—", s["resumo_palavras"], s["status_rag_minuta"]]
         for s in n["solicitacoes"]],
    ))
    p.append("\nResumos produzidos (extrativos, não-LLM):\n")
    for s in n["solicitacoes"]:
        p.append(f"- **{s['id']}**: {s['resumo']}")

    p.append("\n## RF16 — Ataques e limites\n")
    a1, a2, a3 = at["ATQ01"], at["ATQ02"], at["ATQ03"]
    p.append(tabela(["Ataque", "Esperado", "Obtido", "Verificações"], [
        ["ATQ01 injeção na solicitação", a1["esperado"], a1["decisao"],
         f"alerta={a1['alerta_injecao']}; 'DEFERIDO' nas orientações={a1['orientacao_contem_deferido']}; prazo 2 dias={a1['orientacao_contem_prazo_2_dias']}"],
        ["ATQ02 injeção no acervo (DOC-07)", a2["esperado"], f"{a2['status']} / revisão={a2['encaminhar_revisao']}",
         f"trechos suspeitos na indexação={a2['trechos_suspeitos_doc07_na_indexacao']}; quarentena no top-k={len(a2['quarentena_no_top_k'])}; "
         f"suspeito no contexto={a2['trecho_suspeito_no_contexto']}; DEFERIDO/1 dia={a2['resposta_contem_deferido_ou_1_dia']}"],
        ["ATQ03 pedido de segredo", a3["esperado"], a3["decisao_fluxo"],
         f"chamadas ao modelo={a3['chamadas_ao_modelo']}; canário nas saídas={a3['canario_nas_saidas']}; nos logs={a3['canario_nos_logs']}; "
         f"LLM simulado vazando: canário exibido={a3['gerador_simulado_que_tenta_vazar']['canario_na_resposta_exibida']}"],
    ]))
    p.append(
        f"\nObservação ATQ02: o trecho malicioso não entrou no top-k desta pergunta; a revisão foi acionada pela regra de "
        f"documento suspeito (ajuste nº 2 de `registro_ajustes.md`). Motivos: {'; '.join(a2['motivos_revisao'])}.\n"
    )
    p.append(f"- T05 fora de escopo: decisão `{t5['fora_de_escopo']['decisao']}` (similaridade com o acervo {t5['fora_de_escopo']['sinais']['similaridade_acervo']}).")
    p.append(f"- T05 arquivo: {t5['arquivo_excessivo']}; {t5['tipo_nao_permitido']}.")
    p.append(f"- T05 orçamento: {t5['limite_chamadas']['resultado']} ({t5['limite_chamadas']['chamadas_realizadas']}/{t5['limite_chamadas']['maximo']}; {t5['limite_chamadas']['natureza']}).\n")

    p.append("## RF17 — Persistência e reindexação\n")
    np_ = t6["novo_processo"]
    p.append(
        f"- Primeira indexação: {t6['primeira_indexacao']['trechos_depois']} trechos ({len(t6['primeira_indexacao']['adicionados'])} documentos).\n"
        f"- Novo processo Python (reinício): antes={np_.get('antes')}, depois de reindexar={np_.get('depois')}, "
        f"documentos sem alteração={len(np_.get('sem_alteracao', []))}; consulta após reinício: {np_.get('top')}.\n"
        f"- Troca do modelo de embedding: `{t6['troca_de_modelo_exige_reindexacao']}`.\n"
        f"- Manifesto: modelo `{t6['manifesto']['embedding_modelo']}`, dimensão {t6['manifesto']['dimensao']}, "
        f"índice v{t6['manifesto']['versao_indice']}, chunking {t6['manifesto']['chunking']}.\n"
    )

    p.append("## RF18 — Comparação de chunking\n")
    p.append(f"Unidade: **{ch['unidade']}** · embedding `{ch['embedding']}` · top-{ch['top_k']} · mesmas 5 perguntas.\n")
    linhas = []
    for rot, c in ch["configuracoes"].items():
        linhas.append([rot, c["tamanho"], c["sobreposicao"], c["trechos"], c["media_palavras_por_trecho"], c["acerto_recuperacao"]["texto"], ", ".join(c["falhas"]) or "—"])
    p.append(tabela(["Config", "Tamanho", "Sobreposição", "Trechos", "Palavras/trecho", "Acerto", "Falhas"], linhas))
    p.append("")
    ids = [q["id"] for q in next(iter(ch["configuracoes"].values()))["por_pergunta"]]
    p.append(tabela(["Pergunta"] + [f"{r}: posição do 1º acerto" for r in ch["configuracoes"]],
                    [[i] + [next(q["posicao_primeiro_acerto"] for q in c["por_pergunta"] if q["id"] == i) or "não" for c in ch["configuracoes"].values()] for i in ids]))
    p.append(f"\n**Escolhida: {ch['escolhida']['configuracao']}** — {ch['escolhida']['motivo']}. As seções do acervo têm até ~80 palavras e "
             "nenhum trecho cruza seção, por isso A e B geram quase os mesmos trechos; a comparação é pouco discriminativa neste acervo.\n")

    p.append("## RF19 — Oito consultas RAG\n")
    mr = rag["metricas"]
    p.append(tabela(["Métrica", "Resultado"], [
        ["Respondíveis fundamentadas com a fonte esperada", mr["respondiveis_fundamentadas_com_fonte_correta"]["texto"]],
        ["Respostas com todas as afirmações sustentadas", mr["respostas_com_todas_afirmacoes_sustentadas"]["texto"]],
        ["Fatos essenciais nas respondíveis", mr["fatos_essenciais_nas_respondiveis"]["texto"]],
        ["Abstenção correta (P06, P07)", mr["abstencao_correta"]["texto"]],
        ["Caso contraditório (registrado à parte)", json.dumps(mr["caso_contraditorio"], ensure_ascii=False)],
    ]))
    p.append(f"\n> {mr['observacao']}.\n")
    for q in rag["perguntas"]:
        p.append(f"### {q['id']} ({q['tipo']}) — {q['pergunta']}\n")
        p.append(f"- Status: esperado `{q['status_esperado']}`, obtido `{q['status_obtido']}`; encaminhar ao operador: {q['encaminhar_revisao']}")
        p.append(f"- Resposta: {celula(q['resposta'], 600)}")
        for f in q["fontes"]:
            p.append(f"- Fonte: {f['local']} · `{f['chunk_id']}`")
        p.append("- Top-k: " + "; ".join(f"#{t['posicao']} `{t['chunk_id']}` sim={t['similaridade']}" + (" (quarentena)" if t["em_quarentena"] else "") for t in q["trechos_recuperados"]))
        p.append("")

    p.append("## RF20/RF24 — Revisão (T11)\n")
    p.append(f"- Estados após reabrir o banco: {t11['estados_apos_reabrir']}; 2ª decisão: {t11['segunda_decisao']}; sem justificativa: {t11['decisao_sem_justificativa']}.")
    p.append(f"- {t11['aviso']}. **A demonstração humana pela interface continua pendente.**\n")

    p.append("## RF21 — Troca de gerador e falha (T12)\n")
    p.append(tabela(["Gerador", "Status", "Erro"], [[e["gerador"], e["status"], (e["erros"] or ["—"])[0]] for e in t12["execucoes"]]))
    p.append(f"\nÍndice antes/depois (hash do manifesto, trechos): {t12['indice_antes'] == t12['indice_depois']} — {t12['indice_depois'][1]} trechos; falhas auditadas: {t12['eventos_falha_auditados']}.\n")

    p.append("## RF22 — Sentimentos (12 avaliações)\n")
    ag = se["agregado"]
    p.append(f"Método: {se['metodo']}. Acurácia: **{ag['acuracia']['texto']}**; incertos sinalizados para revisão: {ag['incertos_sinalizados']['texto']}.\n")
    p.append(tabela(["ID", "Texto", "Esperado", "Obtido", "Revisão", "Justificativa"],
                    [[r["id"], textos_av[r["id"]], gab_se[r["id"]]["polaridade"], r["polaridade"], r["requer_revisao"], r["justificativa"]] for r in se["resultados"]]))
    p.append("\nMatriz de confusão (linhas = esperado, colunas = obtido):\n")
    pols = list(ag["matriz_confusao"])
    p.append(tabela(["esperado \\ obtido"] + pols, [[e] + [ag["matriz_confusao"][e][o] for o in pols] for e in pols]))
    p.append(f"\nT13: duplicata → total {t13['duplicata']['total']} (removido {t13['duplicata']['ids_removidos']}); filtro positiva → {t13['filtro_positiva']['total']}; "
             f"filtro sem resultado → `{t13['filtro_sem_resultado']['positiva']}`; lista vazia → `{t13['lista_vazia']['acuracia']}`.\n")

    p.append("## RF24 — Exclusão (T14)\n")
    rel = t14["relatorio_exclusao"]
    p.append(f"- Antes: {t14['antes']}\n- Removidos: {rel['indices'][0]['trechos_removidos']} trechos, restantes {rel['indices'][0]['trechos_restantes']}; derivados apagados: {rel['derivados_removidos']}\n"
             f"- Depois: {t14['depois']}\n- Reindexação não recria o excluído: {t14['reindexacao_apos_exclusao']['ignorados_excluidos']}\n")

    p.append("## RF23 — Regressão (T15)\n")
    p.append(tabela(["Caso", "Modalidade", "Decisão", "Minuta", "Status RAG", "Revisão (simulada)", "Campos"],
                    [[x["caso"], x["modalidade"], x["decisao_entrada"], x["minuta_gerada"], x["status_rag"], x["estado_revisao"], x["campos"]] for x in t15["fluxo_desafio6"]]))
    p.append(f"\nCLI do Desafio 01: `{t15['cli_desafio01']['comando']}` → código {t15['cli_desafio01']['codigo_saida']}. {t15['observacao']}.\n")

    p.append("## Matriz T01–T15\n")
    p.append("Ver [`evidencias/matriz_T01_T15.md`](evidencias/matriz_T01_T15.md) (também em CSV e JSON). "
             f"Situação: {resumo['matriz_situacao']}. Logs sanitizados: [`evidencias/auditoria_sanitizada.jsonl`](evidencias/auditoria_sanitizada.jsonl).\n")
    destino = ROOT / "documentacao" / "desafio6" / "resultados_avaliacao.md"
    destino.write_text("\n".join(p) + "\n", encoding="utf-8")
    print(destino.relative_to(ROOT))


if __name__ == "__main__":
    sys.exit(main())
