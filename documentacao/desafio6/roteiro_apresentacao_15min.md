# Roteiro de apresentação — até 15 minutos

Preparação (antes de começar): `python -m src.main indexar`, `streamlit run src/app.py` aberto no navegador, terminal na raiz do projeto e [`resultados_avaliacao.md`](resultados_avaliacao.md) aberto. Qualquer integrante deve conseguir conduzir qualquer bloco.

| Tempo | Bloco | Quem (sugestão) | O que mostrar |
|---|---|---|---|
| 0:00–1:00 | Continuidade e arquitetura | Diego | Desafio 6 = Desafio Prático 02, continuação do 01 (histórico preservado); diagrama do README; recuperação separada da geração |
| 1:00–3:00 | Extração, validação e NLP | Diego | Aba Solicitação com S03 (ficha válida) e S05 (“não localizado”); tabela JSON sintático × esquema × regras (RF14); T02: data 31/02 bloqueia a minuta; resumo ≤100 palavras e entidades literais × inferências |
| 3:00–8:00 | Índice, RAG, fontes, ausência de evidência e revisão | Ayron | Aba Acervo (status, 25 trechos, dimensão 384; reindexar não duplica); Consulta P02 (fundamentada, fonte DOC-02 p. 1, similaridade explicada); P06 (abstenção); P08 (conflito DOC-03 × DOC-05 → revisão); trocar o perfil de geração sem reindexar; aba Revisão: **aprovar uma minuta e rejeitar/pedir revisão de outra, com justificativa (decisão humana real)** |
| 8:00–11:00 | Guardrails, ataque e auditoria | Guilherme | ATQ03 bloqueado sem chamar o modelo; ATQ01 vai para revisão sem “DEFERIDO”; DOC-07 em quarentena; aba Auditoria (logs mascarados); T05: fora de escopo, arquivo grande, orçamento |
| 11:00–13:00 | Sentimentos e agregação | Guilherme | Aba Sentimentos: 12 avaliações, filtros, totais com denominador, conjunto vazio; regras para mista/ironia/sem contexto; confiança não calibrada |
| 13:00–15:00 | Métricas, limitações e uso de IA | Ayron/Diego | Matriz T01–T15 (14 aprovados, 1 parcial); por que os 100% são otimistas; LLM real pendente; registro do uso de IA e ajustes pós-execução |

## Perguntas prováveis

- *Por que o JSON válido não basta?* — Mostrar as variantes: todas passam em `json.loads`; o esquema barra tipo e campo; as regras barram data impossível e dado inventado.
- *Similaridade alta garante a resposta?* — Não: P06/P07 tiveram trechos com similaridade de 0,42–0,51 e o sistema se absteve pela cobertura de termos.
- *O que acontece se o LLM inventar um prazo?* — `verificar_afirmacoes` remove a afirmação (número sem suporte) e encaminha à revisão (teste `test_gerador_llm_simulado_com_afirmacao_inventada`).
- *Como excluir um documento?* — `python -m src.main excluir-documento --doc DOC-06` e consultar de novo.

## Verificação prática rápida

```bash
python -m unittest discover -s testes -t .
python -m src.main consultar "Qual é o prazo de resposta para uma reclamação registrada na ouvidoria?" --gerador extrativo_local
python -m src.main avaliar
```
