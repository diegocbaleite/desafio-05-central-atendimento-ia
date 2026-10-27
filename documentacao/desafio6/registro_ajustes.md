# Registro de ajustes — Desafio 6

Os gabaritos (`dados/gabaritos/desafio6/`) e os parâmetros prévios foram versionados no
commit `dados(d6)` **antes** dos avaliadores. Este arquivo registra toda mudança de
código ou de regra feita **depois** de observar uma execução, para que as métricas
finais possam ser lidas sabendo o que foi ajustado com conhecimento do conjunto de teste.

| # | Data | Observado | Ajuste | Afeta gabarito? | Risco |
|---|---|---|---|---|---|
| 1 | 27/10/2026 | 1ª execução do RAG (gerador extrativo): resposta da P01 trazia só o 1º item da lista de documentos, porque `frases()` cortava em `;` | `src/texto.py`: frases passam a ser separadas só por `.`, `!` e `?` (listas com `;` ficam inteiras) | Não | Baixo; correção genérica de tokenização |
| 2 | 27/10/2026 | ATQ02: o trecho malicioso do DOC-07 foi marcado na indexação, mas não entrou no top-4; a resposta citou a outra seção do mesmo documento sem pedir revisão | Regra nova: documento com qualquer trecho suspeito recebe `documento_suspeito=true` em todos os trechos; se um deles for **citado**, a consulta vai para revisão | Não. O critério do gabarito ("trecho em quarentena no top-k") continua sendo medido e relatado separadamente | Regra criada após ver o caso de teste; pode gerar revisões extras em uso real |

| 3 | 27/10/2026 | 1ª avaliação integrada: T03 "parcial" porque o resumo da S02 trazia "14/10/2026" e o verificador não achou "10" no original (a data é falada "14 de outubro de 2026") | `nlp.fatos_sem_suporte`: datas normalizadas a partir de datas do original (inclusive por extenso) contam como suportadas | Não | Baixo; era falso positivo do verificador, não do resumo |
| 4 | 27/10/2026 | Revisão do caminho de vazamento no ATQ03: o RAG exibia o texto livre do LLM quando todas as afirmações eram sustentadas | A resposta exibida passa a ser sempre montada das afirmações verificadas; texto livre e afirmações removidas passam pelo filtro de saída antes de serem guardados | Não | Reduz fluidez da resposta de um LLM real (fica mais "colada" às fontes) |

Nenhum gabarito foi alterado.
