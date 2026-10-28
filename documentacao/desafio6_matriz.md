# Desafio 6 — matriz RF14–RF24 e testes T01–T15

**Histórico:** a matriz e métricas abaixo foram produzidas com o conjunto sintético anterior, removido a pedido do usuário. Não demonstram acurácia dos documentos atuais em `dados/originais/`; novos casos e gabaritos precisam ser preparados antes de uma nova avaliação.

Estados distintos: **I** implementado; **S** testado com simulação; **R** execução real observada; **H** conferência humana. I/S/R não implicam H. Baseline: 130 testes; evolução integrada: 218 testes. Para resultados medidos e falhas, ver [relatório](desafio6_relatorio.md) e [evidência real](../docs/evidencias/desafio6/real/avaliacao_3ac210a30801.json).

| RF | Implementação principal | Estado | Evidência e pendência |
|---|---|---|---|
| RF14 | `contratos.py`, `schemas/ficha.schema.json`, `nlp.py` | I/S/R; H pendente | Seis fichas reais; R04 omitiu data; esquema bloqueia tipo/extra/null/calendar/coerência |
| RF15 | `nlp.py`, conjunto de solicitações/gabaritos | I/S/R; H pendente | Categoria 6/6; resumo extrativo e entidades; conferir completude além das métricas |
| RF16 | `guardrails.py`, `servicos.py`, validações nas demais camadas | I/S; limites usados em R | Três ataques locais, budget/retry/arquivo/escopo; não é defesa universal contra injeção |
| RF17 | `indice.py` | I/S/R | Seis docs/13 chunks reais; reinício/idempotência e incompatibilidade testados |
| RF18 | `indice.comparar_chunking` | I/S/R; H pendente | 90/20 e 45/10, top-3, ambas 5/5; empate, sem vencedor inventado |
| RF19 | `rag.py`, `fluxo.py` | I/S/R; H pendente | Oito perguntas; 4/5 respondíveis, 2/2 abstenções, conflito correto; Q03 bloqueada |
| RF20 | `app.py` | I/S; operação humana pendente | AppTest indexa/consulta/classifica; formulários reais precisam ser operados por pessoa |
| RF21 | `servicos.py`, config, auditoria em `fluxo.py` | I/S/R parcial | OpenAI real; troca de geração simulada mantém índice; segunda geração real não executada |
| RF22 | `sentimentos.py` | I/S/R; H pendente | 11/12; ironia S11 divergente, confiança não estimada |
| RF23 | `metricas.py`, `avaliacao.py`, testes | I/S/R parcial | Denominadores e falhas explícitos; regressão antiga simulada, sem nova API multimodal |
| RF24 | `revisao.py`, `fluxo.excluir/limpar_expirados` | I/S; H pendente | Hash/estado/exclusão/retenção testados; aprovação e rejeição humanas reais ainda ausentes |

## Matriz mínima de cenários

Esperados abaixo derivam do enunciado/gabaritos prévios, não de alterações feitas para coincidir com saídas. IDs T01–T15 desta matriz pertencem ao Desafio 6; não devem ser confundidos com os IDs de solicitações do catálogo antigo.

| ID | RF correto | Entrada / esperado prévio | Obtido / situação | Evidência |
|---|---|---|---|---|
| T01 | RF14 | Mesmo JSON com extra, tipo incorreto ou obrigatório ausente; barrar minuta | Testes aprovados; JSON sintático distinguido de esquema | `test_desafio6_contratos`, `comparar_json_esquema` |
| T02 | RF14 | Data impossível, valor sem fonte e negação omitida; bloquear | Testes aprovados; nenhuma minuta liberada | `test_desafio6_contratos`, `test_desafio6_rag` |
| T03 | RF15 | Seis solicitações e referências anteriores | Categoria real 6/6; R04 divergiu em data; H pendente | Evidência real, seção `nlp` e `metricas.nlp` |
| T04 | RF16 | Três ataques em solicitação/acervo/segredo; bloquear ou revisar | 3/3 encaminhados sem modelo nem segredo | `test_desafio6_servicos`, evidência `ataques` |
| T05 | RF16 | Fora de escopo, arquivo excessivo, orçamento esgotado | Testes aprovados; bloqueio antes de nova requisição | `test_desafio6_servicos` |
| T06 | RF17 | Reiniciar e reindexar mesmo corpus | Testes aprovados: sem duplicata, fonte/config alterada exige reindexar | `test_desafio6_rag` |
| T07 | RF18 | Duas configs, mesmas cinco perguntas, embedding/top-k iguais | Real: 5/5 em ambas; empate | Evidência `chunking`, configurações e trechos preservados |
| T08 | RF19 | Cinco perguntas respondíveis com todas afirmações sustentadas | Real: 4/5; Q03 bloqueada após recuperar referência | Evidência `rag`, Q01–Q05; sem aprovação humana |
| T09 | RF19 | Duas perguntas sem evidência; abster-se | Real: 2/2 | Evidência Q06/Q07 |
| T10 | RF19 | Fontes contraditórias sem precedência válida | Real: conflito e revisão | Evidência Q08; testes de prioridade/vigência |
| T11 | RF20/RF24 | Aprovar e rejeitar/revisar na UI com justificativas/hash | Mecanismo/S aprovados; **H pendente**, nenhum revisor inventado | `test_desafio6_interface`; operar formulário da interface |
| T12 | RF21 | Troca de geração e falha auditada sem reconstruir índice | Simulação aprovada; segunda configuração real pendente | `test_desafio6_fluxo` |
| T13 | RF23 | Filtro, ID duplicado, conjunto vazio | Testes aprovados, denominador zero retorna indisponível | `test_desafio6_interface`, `metricas.py` |
| T14 | RF24 | Excluir documento/vetores/derivados e consultar novamente | Testes aprovados; fonte canônica preservada, tombstone impede retorno | `test_desafio6_rag`, `test_desafio6_fluxo` |
| T15 | RF23 | Regressão textual e áudio/OCR do Desafio 01 | Suíte antiga preservada; lote antigo mock com cinco casos; nova execução multimodal real não refeita | `test_multimodal`, `test_fluxo_revisao`, comando antigo `--mock`; R03/R04 identificados como referências |

O PDF rotula T01/T02 como RF15, T03 como RF16 e T04 como RF17. Os cenários foram preservados; o vínculo acima segue as definições formais RF14/RF15/RF16. Não houve renumeração dos cenários nem mudança de sentido.
