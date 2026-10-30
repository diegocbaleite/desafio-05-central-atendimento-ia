# Reajuste do RAG e nova avaliação real — 29/10/2026

**T08, T09 e T10 aprovados na nova rodada real.** As cinco respondíveis tiveram respostas completas com fontes esperadas, os 12 fatos essenciais foram encontrados, as duas perguntas sem resposta tiveram abstenção e o conflito continuou encaminhado para revisão.

Execução `20261029T222148Z_5018e2`, OpenAI `gpt-6-luna`, perfil `principal`, `reasoning_effort: none`, prompt RAG versão **1.2**. Foram repetidas as mesmas oito perguntas, com o mesmo embedding real local, índice A e top-4, após o usuário autorizar o envio dos trechos fictícios e solicitar o reajuste.

## O que foi alterado

1. `src/rag.py`: uma afirmação pode conter uma sequência de frases completas e consecutivas de um mesmo trecho. Não são aceitos recortes internos, saltos de frases, combinação de trechos diferentes, paráfrases ou negações invertidas. A comparação conserva palavras, acentos e pontuação e normaliza somente Unicode e espaços.
2. A citação exibida passa a conter somente os IDs dos trechos que realmente sustentam a passagem. Uma citação de outro trecho não valida a afirmação.
3. `prompts/d6/rag_resposta_v1.md`, versão 1.2: o modelo seleciona passagens; `texto` e `citacao_literal` devem ser a mesma cópia da fonte. Listas devem preservar todos os itens e a pontuação, e a orientação principal não pode ser substituída apenas por uma exceção.

Os ajustes foram feitos após observar a primeira rodada. Isso está registrado no item 11 de `registro_ajustes.md`. Não foram alterados gabaritos, documentos originais, embedding, chunking, limiares ou modelo para acomodar os resultados.

## Comparação das duas rodadas reais

| Medida | Antes: `20261029T221237Z_33cce1` | Após: `20261029T222148Z_5018e2` |
|---|---|---|
| Respondíveis com status e fonte esperados | 3/5 | 5/5 |
| Respondíveis com todos os fatos essenciais | 2/5 | 5/5 |
| Fatos essenciais nas respondíveis | 3/12 | 12/12 |
| Respostas fundamentadas sem afirmações removidas | 2/3 | 5/5 |
| Abstenção correta sem resposta no acervo | 2/2 | 2/2 |
| Conflito encaminhado corretamente | 1/1 | 1/1 |
| T08 / T09 / T10 | reprovado / aprovado / aprovado | aprovado / aprovado / aprovado |

| Pergunta | Status após o ajuste | Fatos essenciais |
|---|---|---|
| P01 — documentos de matrícula | fundamentada | 5/5 |
| P02 — segunda via | fundamentada | 1/1 |
| P03 — antecedência do agendamento | fundamentada | 1/1 |
| P04 — cancelamento por faltas | fundamentada | 3/3 |
| P05 — acompanhamento | fundamentada | 2/2 |
| P06 — taxa ausente | sem_evidencia_suficiente | não se aplica |
| P07 — transporte ausente | sem_evidencia_suficiente | não se aplica |
| P08 — prazos contraditórios | conflito_de_fontes | não se aplica |

## Validação e recursos

- **200 testes automatizados aprovados**, incluindo sete regressões novas: sequência literal aceita, omissão intermediária rejeitada, negação/paráfrase rejeitadas, combinação de fontes bloqueada, vínculo entre afirmação e citação e resposta final com múltiplas frases.
- Antes de novas chamadas, as respostas antigas foram revalidadas localmente: P04/P05 passaram a ser aceitas; a paráfrase antiga de P01 continuou rejeitada. Essa revalidação é identificada como local e não é execução nova de LLM.
- A rodada real posterior realizou **8 chamadas**, com **8.950 tokens de entrada e 1.160 de saída** (10.110 no total). Soma das latências: **19.833,6 ms**. Custo monetário indisponível, sem estimativa.
- SHA-256 do gabarito e do manifesto do índice conferidos antes/depois e preservados. O índice manteve 25 trechos. A chave ficou somente no `.env` e na autenticação.
- A [primeira rodada real](avaliacao_rag_openai_2026-10-29.md) e seus arquivos permanecem preservados. A matriz completa anterior T01–T15 continua identificada como avaliação extrativa/simulada; esta rodada real cobre somente T08–T10.

Evidências: [resumo e integridade](evidencias_openai/rag_20261029T222148Z_5018e2/resumo_rag_real.json), [oito perguntas e métricas](evidencias_openai/rag_20261029T222148Z_5018e2/rf19_rag_oito_perguntas.json), [auditoria](evidencias_openai/rag_20261029T222148Z_5018e2/auditoria_sanitizada.jsonl), [respostas completas](evidencias_openai/rag_20261029T222148Z_5018e2/respostas/) e [revalidação local das respostas antigas](evidencias_openai/rag_20261029T222148Z_5018e2/revalidacao_local_respostas_anteriores.json).

## Limites e pendências

Os ajustes foram desenvolvidos conhecendo os casos avaliados. Os resultados comprovam o funcionamento neste conjunto e nesta rodada; não medem generalização nem garantem repetição idêntica do modelo. A política continua extrativa nas afirmações exibidas: uma paráfrase correta pode ser removida, e a veracidade do próprio acervo não é comprovada pela correspondência literal.

A revisão humana pela interface (T11), a conferência final pela equipe e o ZIP de entrega continuam pendentes. Extração e sentimentos com LLM real não foram executados nesta rodada. Nenhuma decisão humana foi produzida pelo agente e nenhuma resposta foi enviada a cidadãos.
