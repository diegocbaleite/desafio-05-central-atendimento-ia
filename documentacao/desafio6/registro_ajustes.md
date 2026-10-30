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

## Correções após o parecer de prontidão

| # | Data | Observado | Ajuste | Afeta gabarito? | Risco |
|---|---|---|---|---|---|
| 5 | 29/10/2026 | Uma afirmação com negação invertida era aceita com citação literal correta | `rag.verificar_afirmacoes` exige frase completa literal do trecho citado, conservando palavras, acentos e pontuação; normaliza somente Unicode e espaços. Prompt RAG atualizado para versão 1.1 | Não | Paráfrases corretas também são removidas; o sistema se abstém ou pede revisão |
| 6 | 29/10/2026 | Conflito marcado como resolvido por prioridade ainda exibia os dois prazos | Resolução por divergência, com descarte de afirmações das fontes que não prevalecem. Empates com valores distintos e substituições parciais mantêm conflito | Não | Descarte conservador por documento pode retirar informações adicionais; se não restar suporte, há abstenção |
| 7 | 29/10/2026 | Consulta independente ignorava `max_chamadas_execucao`, inclusive quando zero | `rag.responder` cria orçamento da configuração quando o chamador não fornece um; mantém o objeto compartilhado do fluxo integrado | Não | Limites configurados passam a interromper consultas antes aceitas sem contabilização |
| 8 | 29/10/2026 | ID do acervo permitia escapar da pasta de enviados e atingir originais | IDs restritos a letras ASCII, números, hífen e sublinhado, até 64 caracteres; caminho resolvido deve permanecer na pasta permitida. Nomes de mídia também são conferidos antes da escrita | Não | IDs com caracteres fora do formato são recusados; os arquivos originais foram preservados |

Validação em 29/10/2026: **188 testes aprovados** (176 anteriores + 12 regressões), incluindo consulta com limite zero pela CLI e pela interface headless, inversão de sentido, prioridade/substituição e preservação de originais em uploads. A avaliação `20261029T214410Z_517c20`, com embedding real local e gerador `extrativo_local` (não-LLM), manteve **14 aprovados e 1 parcial (T11)**, sem erros de etapa. Evidências locais em `resultados/avaliacao_d6/20261029T214410Z_517c20/`; as evidências publicadas da execução anterior não foram substituídas.

Persistem as validações com LLM real e a demonstração humana. Ver [finalização passo a passo](finalizacao_passo_a_passo.md).

## Configuração OpenAI em 29/10/2026

9. A pedido do usuário, o provedor principal foi alterado de Gemini para OpenAI (`OPENAI_API_KEY`, modelo `gpt-6-luna`, `reasoning_effort: none`). O cliente passa a enviar `max_completion_tokens` à OpenAI, omite temperatura quando nula e adapta apenas a cópia do esquema enviada à API, preservando os contratos e a validação local. Nenhum gabarito foi alterado. A chave no `.env` foi preservada e não foi exibida.

Validação: **192 testes aprovados**, incluindo quatro testes de endpoint/parâmetros, esquema sem mutação, compatibilidade dos outros provedores e filtro da credencial OpenAI. A chamada técnica real sem acervo retornou `{"status":"ok"}` com 55 tokens de entrada e 13 de saída; [evidência sanitizada](evidencias_openai/teste_conexao_2026-10-29.json). Isso comprova conexão e formato, sem atribuir aprovação ao fluxo RAG. A revisão automática rejeitou o envio do contexto recuperado à API por exigir autorização específica para esse conteúdo; essa etapa não foi executada fora da restrição.

Referências oficiais consultadas em 29/10/2026: [modelo GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna), [Chat Completions](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create) e [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=chat).

## Avaliação RAG real autorizada — 29/10/2026

10. Antes de executar as oito perguntas com o LLM real, foi corrigida uma descrição fixa do avaliador que rotulava qualquer execução como extrativa. A natureza agora depende do perfil, e as evidências por pergunta incluem provedor, modelo, tokens e custo disponível. O lote também compartilha um orçamento entre as oito consultas. Acrescentado teste com transporte explicitamente simulado para conferir o registro sem alegar execução real. Suíte: **193 testes aprovados**.

Após autorização específica do usuário para enviar os trechos fictícios à OpenAI, a execução real `20261029T221237Z_33cce1` realizou as oito consultas, com gabarito e índice preservados. Resultado: status/fonte em 3/5 respondíveis, somente 2/5 completas, 3/12 fatos essenciais, abstenção sem resposta 2/2 e conflito encaminhado. P01 ficou parcial; P04/P05 foram recusadas por conter duas frases literais na mesma afirmação. Não houve ajuste do verificador ou repetição de chamada para melhorar esses números. [Relatório real e evidências](avaliacao_rag_openai_2026-10-29.md).

## Reajuste após a primeira rodada real — 29/10/2026

11. Após observar a rodada `20261029T221237Z_33cce1`, o usuário pediu reajuste. `rag.verificar_afirmacoes` passou a aceitar sequências contíguas de frases completas de um mesmo trecho, preservando a rejeição de negações invertidas, paráfrases, recortes, saltos e junções entre fontes. Os IDs da citação exibida são filtrados para os trechos que efetivamente sustentam a passagem. O prompt RAG foi atualizado para 1.2: exige cópia idêntica em `texto` e `citacao_literal`, listas completas e preservação da pontuação.

Validação: sete regressões adicionais; **200 testes aprovados**. Antes de novas chamadas, respostas antigas foram revalidadas localmente: P04/P05 aceitas como literais, paráfrase de P01 ainda recusada. A nova rodada real `20261029T222148Z_5018e2`, com as mesmas oito perguntas, mesmo modelo, índice, chunking, top-k e gabarito, obteve **5/5 respondíveis completas, 12/12 fatos essenciais, 2/2 abstenções corretas e conflito encaminhado**. T08–T10 aprovados. A rodada anterior e suas falhas foram preservadas; nenhuma decisão humana foi produzida. [Comparação e evidências](reajuste_rag_openai_2026-10-29.md).

Risco: o ajuste foi feito conhecendo o conjunto de avaliação; o sucesso não mede generalização. A seleção literal também não comprova a veracidade do acervo. Nenhum gabarito foi alterado.

## Orientação do painel sem resultados de sessão — 29/10/2026

12. Na demonstração manual, após uma tela com 12 classificações locais, foi recebido um print com Requer revisão em `sim` e aviso de conjunto vazio (0/0). A causa da ausência de resultados naquela sessão não foi determinada pela imagem. Antes de alterar o código, a reprodução com `AppTest` confirmou que classificar 12 avaliações e trocar o filtro preserva os resultados: `sim` mostra AV10–AV12 (3 casos) e `não` mostra 9 casos. Não foi reproduzida perda de estado causada pelo filtro.

A mensagem de `src/app.py` foi ajustada para distinguir ausência de classificações na sessão de um conjunto realmente vazio após aplicar filtros. Sem resultados carregados, agora orienta clicar em **Classificar as 12 avaliações**. O cálculo, a classificação, o armazenamento em `session_state` e os gabaritos foram preservados; não foi acrescentada classificação automática nem chamada ao LLM.

Regressão em `testes/test_d6_app_streamlit.py`: selecionar `sim` antes de classificar, carregar os resultados e conferir os três IDs; alternar `todas/sim/não` sem reclassificar; testar uma combinação realmente vazia (`positiva` + revisão `sim`) e manter os 12 resultados na sessão. A captura manual com os três casos filtrados continua pendente; o teste automatizado não a substitui.

Validação: suíte completa com **201 testes aprovados**. Log local: `resultados/logs/filtro_sentimentos_2026-10-29_unittest.log`. As três capturas do painel sem restrição foram encontradas na pasta de evidências e conferidas visualmente.

## Destino da auditoria da consulta pela CLI — 29/10/2026

13. O print da Auditoria mostrou as decisões humanas e consultas da demonstração junto a falhas de orçamento zero. A leitura do log confirmou que essas falhas usam `hash-bow-teste-v1`, limite máximo 0 e nenhuma chamada ao LLM. O teste `test_cli_consultar_com_orcamento_zero_nao_faz_requisicao` configurava um arquivo temporário, mas `cli_d6.executar` não repassava esse caminho a `rag.responder`, que usava o destino padrão.

Correção: a consulta pela CLI passa `ROOT / cfg['auditoria']['arquivo']` explicitamente ao RAG. O teste existente foi ampliado para exigir o evento no arquivo configurado, verificar orçamento zero/nenhuma requisição e recusar a criação do destino padrão. A regressão falhou antes da correção e passou depois; a fase de reprodução usou um destino padrão temporário para não acrescentar outro evento ao histórico manual.

Validação: **201 testes aprovados** em 12,921 s, com SHA-256 do log da demonstração idêntico antes/depois da suíte. Logs locais: `resultados/logs/auditoria_cli_2026-10-29_antes.log`, `auditoria_cli_2026-10-29_depois.log` e `auditoria_cli_2026-10-29_unittest.log`. Não foram alterados gabaritos, decisões humanas ou eventos históricos. O arquivo [auditoria_fluxo_UI001_UI002.json](evidencias_humanas/auditoria_fluxo_UI001_UI002.json) identifica o recorte dos sete eventos da demonstração e os IDs dos testes de orçamento zero presentes no log completo; os testes não são apresentados como chamadas reais ao modelo.

## Validação complementar autorizada — 29/10/2026

14. O usuário autorizou executar extração, resumo, sentimentos e ataques com o LLM real. Foi acrescentado `src/avaliacao_llm_real.py`, reutilizando os métodos existentes, os gabaritos prévios e o perfil principal; a configuração da interface não foi alterada. A avaliação usa orçamento compartilhado, índice e auditoria próprios, registra respostas reais sanitizadas, protege o contexto contra segredos e não grava decisões humanas. Cinco regressões cobrem segredo antes do transporte, saída bloqueada antes de correção, identificação de transporte simulado, preservação do resumo bruto e denominador com falhas. A suíte passou com **206 testes**.

A rodada `20261030T021555Z_da0eda` (29/10/2026 em America/Cuiaba) realizou 27 chamadas OpenAI/GPT-6 Luna: seis fichas válidas e categorias corretas, 18/18 campos críticos, 5/6 listas de ausências, 18/20 entidades e três entidades incorretas; seis resumos com 17/17 fatos essenciais e até 100 palavras; sentimentos com 12/12 rótulos e indicadores de revisão corretos; ATQ01/ATQ02 com respostas reais e encaminhamento seguro, ATQ03 bloqueado com zero chamadas. Originais, gabaritos, configuração, índice da interface e decisões humanas foram preservados. O detector numérico marcou um resumo por `1.200 horas` versus `1200 horas` no original. As evidências dessa rodada permanecem intactas em `evidencias_openai/complementar_20261030T021555Z_da0eda/`.

15. Depois de observar essa rodada, foi corrigido o falso positivo de separador de milhar no detector `nlp.fatos_sem_suporte`: equivalência em quantidades com unidade, sem normalizar protocolos/versões nem aceitar quantidade ou decimal diferente. Três regressões adicionais cobrem esses limites. O prompt de extração passou de 1.0 para 1.1: normalizar datas de entidades mantendo a evidência literal; distinguir instituição de curso/eixo tecnológico; manter assunto/pedido ausentes quando dependem de conversa anterior. Nenhum gabarito foi modificado. O reteste é declarado como direcionado a S02/S06, com até três chamadas adicionais, sem reapresentar os casos antigos como nova rodada completa. O ajuste conhece o conjunto e não mede generalização.

O reteste `20261030T022141Z_443e46` utilizou duas chamadas reais e corrigiu os dois casos. A consolidação dos últimos resultados por caso tem 6/6 listas de ausências e 20/20 entidades, sem entidades incorretas; quatro casos permanecem da rodada original. O replay local dos seis resumos removeu somente o falso positivo numérico, sem chamadas adicionais de resumo. ATQ02 foi tratado com segurança, mas o trecho malicioso não entrou no top-4: o critério literal de quarentena no top-k continua parcial. [Relatório e evidências](validacao_complementar_llm_2026-10-29.md).

16. Ao consolidar os inventários, foi observado que a sanitização genérica mascarava como telefone uma sequência numérica dentro de um SHA-256 técnico do README dos gabaritos. A fonte permanecia idêntica ao Git; a diferença estava no texto do hash exportado. O exportador passou a gravar inventários tipados contendo somente caminhos e SHA-256 completos, sem aplicar máscara de telefone aos digests. Acrescentada regressão que preserva esse hash e recusa valores livres. Inventários antigos preservados; conferência técnica complementar com hashes completos, sem novas chamadas ao LLM.

Validação final: **210 testes aprovados** em 12,254 s; 29 chamadas reais no total, 16.917 tokens de entrada, 3.846 de saída, custo indisponível. Logs em `resultados/logs/complementar_llm_final_2026-10-29_unittest.log`. O avaliador não alterou gabaritos ou decisões humanas e não enviou respostas a cidadãos.


## 17. RF14 — Coerência literal de assunto e pedido — 30/10/2026

A revisão da main `5951ddc` reproduziu um falso aceite: o original dizia “Não solicito cancelamento da matrícula.”, mas uma saída LLM simulada trocava por “Solicito cancelamento da matrícula.”. A comparação por radicais/50% de sobreposição ignorava negação, e o fluxo criava uma minuta pendente com o pedido invertido.

Correção: assunto e pedido não usam mais similaridade lexical para comprovar fatos. O contrato compara o valor integral com a referência conservadora extraída do campo correspondente no original. A comparação permite somente NFC, caixa, espaços e ponto final opcional; preserva palavras, acentos, interrogação, restrições, condições e subpedidos. A extração livre mantém prefixos “não”, “nunca”, “jamais”, “somente” e “apenas”. A referência de outro campo não autoriza substituir o pedido rotulado. Sem referência verificável, a saída é rejeitada, admitindo a única correção já prevista; se persistir, não há RAG nem minuta. O prompt de extração passou de 1.1 para 1.2.

Limite deliberado: é uma política conservadora de cópia, não um verificador semântico universal. Paráfrases ou formulações que o extrator não reconhece podem ser rejeitadas mesmo quando plausíveis. Dados ausentes continuam null, com revisão obrigatória. Não foi alterada a normalização da busca vetorial, nem foram adaptados os gabaritos.

Regressões em `testes/test_rf14_coerencia_literal.py`: inversão de negação nos dois sentidos, restrições/condições omitidas, subpedido descartado, número acrescentado, pedido livre com prefixo, frase positiva em outro campo, assunto truncado, pergunta convertida em afirmação e normalização visual permitida. O teste integrado confirma duas saídas incoerentes rejeitadas, exatamente duas chamadas simuladas, nenhum registro de minuta e nenhuma consulta RAG; confirma também que uma correção fiel permite apenas minuta pendente.

Avaliação local após a correção: execução `20261030T163407Z_61ba4f`, embedding real local e gerador extrativo, 14 aprovados/T11 parcial e nenhum erro de etapa; seis categorias e 18 campos críticos corretos. Não representa chamada LLM real. Originais, gabaritos, evidências históricas e decisões humanas permaneceram intactos. Nenhuma nova chamada paga ou decisão humana foi produzida; nenhum ZIP foi gerado.

Validação final desta correção: **330 testes aprovados em 23,138 s**, sintaxe e `python -m src.main verificar` sem erro; envio automático desativado e chaves ausentes. Os 163 arquivos protegidos da revisão mantiveram seus hashes.
