# Gabaritos do Desafio 6 (Desafio Prático 02)

Escritos pela equipe **antes** da implementação dos avaliadores e de qualquer execução de
modelo, e versionados em commit próprio (ver `git log -- dados/gabaritos/desafio6`).
**Não devem ser alterados para coincidir com saídas obtidas.** Se um gabarito estiver
errado, a correção precisa ser registrada em `documentacao/desafio6/registro_ajustes.md`
com motivo, data e responsável, preservando o valor anterior.

| Arquivo | Conteúdo |
|---|---|
| `solicitacoes.yaml` | Campos esperados, categoria, entidades, fatos essenciais e decisão das 6 solicitações (RF14/RF15) |
| `rag_perguntas.yaml` | 8 perguntas, status esperado, fontes, trechos de referência e fatos (RF18/RF19) |
| `sentimentos.yaml` | Rótulo esperado, justificativa e regras para as 12 avaliações (RF22) |
| `ataques.yaml` | Decisão esperada para os 3 ataques (RF16) |
| `matriz_testes.yaml` | Resultado esperado de T01–T15, copiado do PDF, com vínculo RF corrigido (RF23) |
| `parametros_previos.yaml` | Embedding, top-k, chunking A/B e limiares de abstenção fixados antes da execução |

Convenções: ausência = `null` no JSON e "não localizado" na interface. Fatos essenciais são
conferidos por termos alternativos (qualquer um basta), sem acento e sem diferenciar
maiúsculas. Entidades dentro do nome de um órgão (ex.: "Cuiabá" em "Escola Técnica
Estadual de Cuiabá") não são contadas como local separado.
