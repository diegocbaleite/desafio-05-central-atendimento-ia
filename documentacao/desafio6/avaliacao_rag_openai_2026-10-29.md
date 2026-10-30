# Avaliação real do RAG com OpenAI — 29/10/2026

**Oito perguntas executadas com LLM real. O fluxo ainda tem limitações de qualidade.** Nas cinco perguntas respondíveis, P02 e P03 ficaram completas, P01 ficou parcial e P04/P05 tiveram abstenção por bloqueio do verificador. As duas perguntas sem resposta e o conflito foram tratados corretamente.

Execução `20261029T221237Z_33cce1`, OpenAI `gpt-6-luna`, perfil `principal`, `reasoning_effort: none`, saída estruturada. Embedding real local `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, chunking A, top-4. O usuário autorizou explicitamente o envio dos trechos fictícios do acervo para estas oito consultas. A chave foi usada somente na autenticação e não foi exibida nem publicada.

## Resultados por pergunta

| ID | Cenário | Status esperado | Status obtido | Fatos essenciais | Situação observada |
|---|---|---|---|---|---|
| P01 | Documentos de matrícula | fundamentada | fundamentada | 1/5 | Parcial: a lista principal foi removida; restou a orientação sobre responsável legal |
| P02 | Segunda via de declaração | fundamentada | fundamentada | 1/1 | Completa, com DOC-02 |
| P03 | Antecedência do agendamento | fundamentada | fundamentada | 1/1 | Completa, com DOC-04 |
| P04 | Cancelamento por faltas | fundamentada | sem_evidencia_suficiente | 0/3 | Fonte recuperada, mas duas frases literais juntas foram recusadas |
| P05 | Acompanhamento de solicitação | fundamentada | sem_evidencia_suficiente | 0/2 | Fonte recuperada, mas duas frases literais juntas foram recusadas |
| P06 | Taxa ausente do acervo | sem_evidencia_suficiente | sem_evidencia_suficiente | não se aplica | Abstenção correta, encaminhada para revisão |
| P07 | Transporte ausente do acervo | sem_evidencia_suficiente | sem_evidencia_suficiente | não se aplica | Abstenção correta, encaminhada para revisão |
| P08 | Prazos contraditórios | conflito_de_fontes | conflito_de_fontes | não se aplica | DOC-03 × DOC-05, encaminhado para revisão |

## Métricas e recursos

| Medida | Resultado |
|---|---|
| Respondíveis com status e documento esperado | 3/5 (60%) |
| Respondíveis com todos os fatos essenciais | 2/5 (40%) |
| Fatos essenciais presentes nas respondíveis | 3/12 (25%) |
| Respostas fundamentadas sem afirmação removida | 2/3; a P01 teve uma afirmação removida |
| Abstenção correta nas perguntas sem resposta | 2/2 |
| Conflito não resolvido tratado corretamente | 1/1 |
| Chamadas reais realizadas | 8 |
| Tokens de entrada / saída | 7.894 / 1.201; total 9.095 |
| Soma das latências das consultas | 22.503,5 ms |
| Custo monetário | indisponível; não estimado |
| T08 / T09 / T10 desta rodada | reprovado / aprovado / aprovado |

O critério automático de status e documento marca P01 como correta, mas a conferência dos fatos mostra a incompletude. Por isso, **3/5 não significa três respostas completas**. A métrica de ausência de remoções também não significa que uma afirmação rejeitada foi exibida: o filtro retirou essas afirmações da resposta.

## Limitações encontradas

1. **P01:** o modelo copiou a passagem corretamente em `citacao_literal`, mas reescreveu a lista em `texto`, alterando pontuação e palavras. A política conservadora rejeitou essa afirmação. A resposta final contém apenas a orientação para menores de idade e não cobre a lista solicitada.
2. **P04 e P05:** o modelo juntou duas frases completas, copiadas literalmente do trecho. O verificador atual aceita uma única frase por afirmação e rejeitou o conjunto. São abstenções por limitação de formato do verificador; as informações estavam no acervo recuperado.
3. Não foi feita uma nova chamada ao modelo para tentar melhorar os resultados. Os resultados desta primeira rodada real permanecem preservados.
4. Esta rodada cobre apenas as oito consultas RAG. Extração por LLM, sentimentos por LLM e decisão humana na interface não foram executados nesta autorização.

## Integridade e evidências

- Gabarito e manifesto do índice tiveram seus SHA-256 conferidos antes/depois e permaneceram iguais. O índice continuou com 25 trechos.
- Nenhum original, gabarito, configuração de chunking ou limiar foi alterado para acomodar o resultado.
- A avaliação anterior com `extrativo_local` e a matriz completa T01–T15 foram preservadas. Esta é uma rodada separada, com natureza **LLM real**.
- A suíte passou com **193 testes**. O teste adicional cobre a identificação de modelo/provedor/tokens e impede que uma evidência de perfil LLM seja rotulada como extrativa. Testes automatizados não substituem a revisão humana.
- Nenhuma decisão humana foi executada pelo agente e nenhuma resposta foi enviada a cidadãos.

Evidências sanitizadas: [resumo e integridade](evidencias_openai/rag_20261029T221237Z_33cce1/resumo_rag_real.json), [perguntas e métricas](evidencias_openai/rag_20261029T221237Z_33cce1/rf19_rag_oito_perguntas.json), [auditoria](evidencias_openai/rag_20261029T221237Z_33cce1/auditoria_sanitizada.jsonl) e [respostas completas por pergunta](evidencias_openai/rag_20261029T221237Z_33cce1/respostas/).

O próximo ajuste de qualidade deve permitir sequências contíguas de frases completas verificadas, preservando o bloqueio de negações invertidas, recortes e paráfrases. Esse ajuste precisa de regressões e registro próprio; qualquer nova avaliação deve manter esta rodada como histórico. A revisão humana T11 continua pendente da equipe.
