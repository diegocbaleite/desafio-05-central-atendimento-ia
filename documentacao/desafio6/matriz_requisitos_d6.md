# Matriz de requisitos RF14–RF24 — Desafio 6

Estados usados (um não implica o outro): **implementado** · **testado (automatizado/simulado)** · **validado com serviço real** · **validado por pessoa**.

| RF | Implementação | Testes automatizados | Evidência | Estado | Pendência |
|---|---|---|---|---|---|
| RF14 Extração e validação | `contrato.py`, `schemas/solicitacao.v2.schema.json`, `estruturacao.py`, `llm_json.py` | `test_d6_contrato_estruturacao.py` | `evidencias/rf14_comparacao_json.json` (T01, T02) | implementado; testado (regras locais + LLM simulado) | Extração com LLM real e compatibilidade do esquema com o modo estruturado do Gemini |
| RF15 Resumo, categoria, entidades | `nlp.py` | `test_d6_nlp_guardrails.py` | `evidencias/rf15_nlp_solicitacoes.json` (T03) | implementado; testado (regras locais, resumo extrativo) | Resumo por LLM real (`nlp.resumir_llm`) |
| RF16 Guardrails e limites | `guardrails.py`, `orcamento.py`, `cliente.py` | `test_d6_nlp_guardrails.py`, `test_cliente_retry.py` | `evidencias/rf16_ataques.json`, `rf16_t05_limites.json` (T04, T05) | implementado; testado (local + simulações) | Repetir os ataques com LLM real |
| RF17 Embeddings e índice | `ingestao.py`, `embeddings.py`, `indice.py` | `test_d6_indice_rag.py` | `evidencias/rf17_t06_persistencia.json` (T06) | implementado; testado com **modelo real local** (2 processos) | — |
| RF18 Chunking | `config.yaml` (A/B), `avaliacao_integrada.comparar_chunking` | `test_d6_indice_rag.TestChunking` | `evidencias/rf18_chunking.json` (T07) | implementado; medido com modelo real local | Comparação pouco discriminativa (seções curtas) |
| RF19 RAG fundamentado | `rag.py`, `geracao.py`, `prompts/d6/rag_resposta_v1.md` | `test_d6_indice_rag.TestRAG` | `evidencias/rf19_rag_oito_perguntas.json`, `rag_respostas/` (T08–T10) | implementado; testado com gerador extrativo e LLM simulado | Oito perguntas com LLM real |
| RF20 Streamlit | `app.py` | `test_d6_app_streamlit.py` (headless) | servidor iniciado (`/_stcore/health` = ok); consulta com modelo real executada sem navegador | implementado; testado | Demonstração por pessoa da equipe |
| RF21 Provedor e auditoria | `config.yaml → geracao`, `geracao.py`, `cliente.py`, `auditoria.registrar_d6` | `test_d6_indice_rag` (troca/falha), `test_d6_nlp_guardrails` (mascaramento) | `evidencias/rf21_t12_troca_gerador.json`, `auditoria_sanitizada.jsonl` (T12) | implementado; testado | Registrar tokens/latência de uma chamada real |
| RF22 Sentimentos | `sentimento.py`, `schemas/sentimento.schema.json`, `prompts/d6/sentimento_v1.md` | `test_d6_revisao_sentimento_pipeline.py` | `evidencias/rf22_sentimentos.json` | implementado; testado (regras locais + LLM simulado) | Classificação por LLM real |
| RF23 Avaliação e regressão | `avaliacao_integrada.py`, `metricas.py` | `test_d6_revisao_sentimento_pipeline.TestMetricasSentimento` | `evidencias/matriz_T01_T15.*`, `rf23_t13_agregacao.json`, `rf23_t15_regressao.json` | implementado; executado (14 aprovados, 1 parcial) | — |
| RF24 Privacidade e revisão | `privacidade.py`, `revisao.py`, `indice.excluir_documento` | `test_d6_indice_rag` (exclusão), `test_d6_revisao_sentimento_pipeline` (revisão, retenção) | `evidencias/rf24_t14_exclusao.json`, `rf20_rf24_t11_revisao.json` | implementado; testado com decisões simuladas | **Uma aprovação e uma rejeição/revisão humanas reais** na interface |

## Inconsistências de RF na matriz de testes do PDF

A seção 11 do PDF associa alguns cenários a RFs que não correspondem ao conteúdo da seção 7. Os IDs e cenários foram mantidos e o vínculo coerente foi registrado (também em `dados/gabaritos/desafio6/matriz_testes.yaml`):

| Teste | RF no PDF | Vínculo coerente | Motivo |
|---|---|---|---|
| T01 | RF15 | RF14 | JSON/esquema é extração estruturada |
| T02 | RF15 | RF14 | Data impossível e dado sem suporte são regras de negócio da extração |
| T03 | RF16 | RF15 | Resumo, categoria e entidades |
| T04 | RF17 | RF16 | Ataques são guardrails |
| T13 | RF23 | RF22/RF23 | A agregação avaliada é a do painel de sentimentos |
