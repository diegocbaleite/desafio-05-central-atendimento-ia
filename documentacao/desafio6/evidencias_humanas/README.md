# Evidências da demonstração pela equipe

Organização iniciada em 29/10/2026. Os registros abaixo distinguem prints recebidos na conversa, arquivos presentes no projeto e etapas ainda não demonstradas. Uma imagem de indexação não comprova aprovação ou rejeição de minuta.

## Registro 00 — Aviso de índice vazio

- **Arquivo:** [00_aviso_indice_vazio.png](00_aviso_indice_vazio.png), recebido inicialmente como `Anexo do usuário01.png` e renomeado sem alterar seu conteúdo (SHA-256 conferido antes/depois).
- **Requisito relacionado:** RF20 (mensagem de estado).
- **O que a imagem mostra:** aviso para indexar o acervo antes de consultar; sete documentos listados sem indexação; coleção com 0 trechos; perfil `principal` selecionado e top-k 3.
- **Limite da evidência:** mostra a configuração e o aviso da interface; não comprova uma chamada ao LLM nem uma decisão humana.

**Legenda sugerida:** “Estado inicial do acervo: a interface informa que o índice está vazio e orienta a indexação antes de consultas.”

## Registro 01 — Indexação do acervo

- **Arquivo:** [01_indexacao_acervo.png](01_indexacao_acervo.png), recebido inicialmente como `Anexo do usuário02.png` e renomeado sem alterar seu conteúdo (SHA-256 conferido antes/depois).
- **Requisitos relacionados:** RF17 e RF20.
- **Origem:** print enviado pelo usuário na conversa.
- **Arquivo no projeto:** presente e conferido visualmente.
- **O que a imagem mostra:** aba Acervo; coleção `acervo_A`; chunking A; top-k 4; resultado de indexação com DOC-01 a DOC-07 em `adicionados`, `trechos_antes: 0` e `trechos_depois: 25`.
- **Perfil exibido:** `extrativo_local`, explicitamente identificado como não-LLM. O print comprova a operação de indexação exibida; não comprova uma chamada ao modelo generativo.
- **Operador responsável:** não localizado; o campo está vazio na imagem.
- **Observação:** o indicador acima do botão ainda mostra 0 trechos, enquanto o resultado JSON mostra 25 após a operação. Um novo print após atualizar a tela pode complementar este registro.

**Legenda sugerida:** “Indexação do acervo institucional fictício: sete documentos adicionados à coleção acervo_A, com 25 trechos resultantes. Configuração de chunking A e top-k 4.”

## Registro 02 — Preparação da solicitação

- **Nome previsto:** `02_entrada_solicitacao.png`.
- **Requisito relacionado:** RF20 (tela de entrada).
- **Origem:** novo print enviado pelo usuário na conversa.
- **Arquivo no projeto:** não incluído; captura opcional de preparação, substituída para a entrega pelas imagens legíveis do registro 04.
- **O que a imagem mostra:** aba Solicitação, opção Arquivo .txt selecionada, botão Upload, campo de arquivo vazio e botão Processar solicitação desabilitado. Operador responsável preenchido como `Diego`; chunking A e top-k 4.
- **Perfil exibido:** `extrativo_local` (não-LLM).
- **Limite da evidência:** comprova a tela de entrada e o preenchimento do operador; ainda não comprova processamento, ficha, minuta, fontes ou decisão de revisão.

**Legenda sugerida:** “Preparação da entrada de solicitação em arquivo TXT, com identificação do operador responsável. O processamento permanece desabilitado enquanto não há arquivo selecionado.”

## Registro 03 — Solicitação processada e minuta pendente com abstenção

- **Nome previsto:** `02_processamento_minuta_pendente.png`.
- **Requisitos relacionados:** RF14, RF15, RF19 e RF20.
- **Origem:** print enviado pelo usuário após carregar `completa.txt` e processar a solicitação.
- **Arquivo no projeto:** não incluído; captura reduzida substituída para a entrega pelas imagens legíveis do registro 04.
- **O que a imagem mostra:** decisão de entrada `permitir`; ficha no contrato 2.0.0, modo `regras`, válida; categoria `segunda_via_documento`; resumo com 19 palavras; entidades literais e categoria inferida; minuta em estado PENDENTE e identificação de conteúdo automatizado (`principal`, LLM: sim).
- **Resultado RAG exibido:** `sem_evidencia_suficiente`, com os motivos “afirmação sem suporte removida” e “sem evidência suficiente: abstenção”. Não há fonte institucional citada na minuta mostrada. A decisão de entrada `permitir` não é uma aprovação humana.
- **Corroboração local:** a auditoria registra a solicitação `UI-001` e a minuta `M-UI-001-6ee39a04` com RAG sem evidência suficiente. Não foi encontrada decisão de revisão nesta imagem.
- **Legibilidade:** a captura está muito reduzida; recomenda-se guardar também duas imagens em zoom normal, uma da ficha/resumo e outra da minuta/pendências.

**Legenda sugerida:** “Processamento de solicitação fictícia: ficha válida, resumo e classificação apresentados, com minuta pendente de revisão humana. Uma afirmação foi removida pelo verificador, e o sistema se absteve de emitir orientação institucional sem suporte aceito.”

## Registro 04 — Capturas legíveis da ficha e da minuta

- **Arquivos:** [02a_ficha_resumo.png](02a_ficha_resumo.png) e [02b_minuta_abstencao.png](02b_minuta_abstencao.png).
- **Origem:** duas imagens enviadas pelo usuário na conversa, substituindo a necessidade de usar somente a captura reduzida do registro 03.
- **Arquivos no projeto:** presentes, com nomes corretos e conteúdo conferido visualmente. Ambos estão legíveis e correspondem às capturas enviadas. As imagens não foram reconstruídas, recortadas ou regeneradas pelo agente.
- **Primeira captura:** `completa.txt` carregado; entrada permitida; contrato 2.0.0 em modo `regras`, ficha válida; protocolo `2026.000123`, data `02/10/2026`, solicitante Maria Fictícia Albuquerque; categoria `segunda_via_documento`, resumo extrativo de 19 palavras, entidades literais e inferência de categoria; alerta de abstenção.
- **Segunda captura:** minuta “NÃO ENVIADA”, pendente de revisão humana; fatos do solicitante separados das orientações institucionais; orientação sem suporte aceito; motivos de revisão “afirmação sem suporte removida” e “sem evidência suficiente: abstenção”. O rodapé identifica `principal`, LLM: sim.
- **Limite da evidência:** as capturas mostram processamento e pendência, sem comprovar aprovação, rejeição ou revisão já registrada por uma pessoa.

**Legenda da ficha:** “Validação e compreensão de solicitação fictícia: ficha conforme ao contrato, resumo extrativo, categoria e entidades, com distinção entre dados literais e inferência.”

**Legenda da minuta:** “Minuta pendente de revisão humana, sem envio automático. O verificador removeu uma afirmação sem suporte e o sistema se absteve de apresentar orientação institucional.”

## Registro 05 — Pedido de revisão registrado por Diego

- **Captura original:** recebida no chat, com formulário e confirmação do pedido de revisão. Para `05_revisao_rejeitada_ou_revisar.png`, usar a captura posterior do histórico persistido descrita no registro 16.
- **Requisitos relacionados:** RF20 e parte da demonstração RF24/T11.
- **O que a imagem mostra:** opção `revisar`, justificativa preenchida e mensagem “Decisão registrada: revisar. Nada foi enviado ao cidadão.”
- **Persistência confirmada:** leitura do SQLite em modo somente leitura confirmou a minuta `M-UI-001-6ee39a04`, caso `UI-001`, estado `revisar`, operador `Diego`, origem `humana_interface` e transição `pendente → revisar`. O SHA-256 do conteúdo confere com o da decisão.
- **Justificativa registrada:** “A minuta ficou sem orientação fundamentada. Solicito complementação e conferência das fontes.”
- **Evidência estruturada sanitizada:** [revisao_UI001_20261029T232021Z.json](revisao_UI001_20261029T232021Z.json). O agente apenas leu o registro existente; não aprovou, rejeitou ou pediu revisão em nome do operador.
- **Estado do aceite:** há demonstração de um operador executando o fluxo e registrando revisão pela interface (RF20). A aprovação de outra minuta foi registrada posteriormente e está documentada no registro 08.

**Legenda sugerida:** “Revisão humana registrada por Diego: a minuta foi encaminhada para complementação, com justificativa persistida. A operação não envia resposta ao cidadão.”

## Registro 06 — Novo exemplo com minuta fundamentada

- **Arquivos:** [02c_ficha_declaracao.png](02c_ficha_declaracao.png) e [02d_minuta_fundamentada.png](02d_minuta_fundamentada.png), presentes e conferidos visualmente.
- **Entrada:** `dados/solicitacoes/DEMO_RF20_declaracao.txt`, exemplo adicional para demonstração; não substitui `completa.txt` ou os gabaritos.
- **Primeira imagem:** ficha válida no contrato 2.0.0, modo `regras`; pedido específico de segunda via da declaração de matrícula; categoria `segunda_via_documento`; resumo extrativo de 28 palavras.
- **Segunda imagem:** status `fundamentada`; minuta `M-UI-002-02774ae6`, PENDENTE; orientação de emissão em até 5 dias úteis a partir da solicitação, citando o acervo fictício DOC-02 v2.0, seção 1, página 1, trecho `DOC-02:v2.0:A:p1:s1:c0`.
- **Persistência confirmada:** caso UI-002, gerador `principal`, LLM: sim, RAG fundamentado e estado pendente, com hash do conteúdo conferido. [Snapshot somente leitura](minuta_UI002_pendente_20261029T232759Z.json).
- **Limite dessa captura:** o expansor “Fonte” aparece fechado. A imagem com a passagem aberta foi recebida posteriormente e está descrita no registro 07. Não há aprovação registrada nesse snapshot.

**Legenda da ficha:** “Processamento de exemplo fictício específico sobre declaração de matrícula: ficha válida, categoria e resumo apresentados.”

**Legenda da minuta:** “Minuta fundamentada no DOC-02 v2.0, seção 1, página 1, com fonte identificada e estado pendente de revisão humana.”

## Registro 07 — Passagem da fonte aberta

- **Nome opcional:** `02e_fonte_aberta.png` (recebido no chat; arquivo local não incluído). É uma captura complementar; para a entrega, a passagem aberta já está documentada em [03b_fonte_consulta_aberta.png](03b_fonte_consulta_aberta.png), junto à identificação da mesma fonte na minuta em [02d_minuta_fundamentada.png](02d_minuta_fundamentada.png).
- **Requisitos relacionados:** RF19 e RF20.
- **O que a imagem mostra:** status fundamentado; expansor do DOC-02 v2.0, seção 1, página 1, aberto; passagem original identificada por `DOC-02:v2.0:A:p1:s1:c0`; minuta `M-UI-002-02774ae6` em estado PENDENTE.
- **Conferência do conteúdo exibido:** a fonte afirma que a segunda via da declaração de matrícula é emitida em até 5 dias úteis a partir da solicitação, correspondendo à orientação da minuta. Os 20 dias úteis também visíveis referem-se à certidão de conclusão de curso, outro documento.
- **Limite da evidência:** comprova a exibição da passagem para conferência; não comprova, por si só, aprovação humana. Todos os documentos e prazos desse acervo são fictícios para o exercício.
- **Organização posterior:** a tela de Solicitação foi mostrada vazia em uma sessão posterior; isso não apaga a minuta persistida no banco. Não é necessário criar outra solicitação para repetir esta captura. A imagem 03b pertence à aba Consulta, sem ser renomeada ou apresentada como captura da aba Solicitação; ela exibe o mesmo trecho `DOC-02:v2.0:A:p1:s1:c0` citado na minuta 02d. O nome 02e era uma sugestão de organização, não uma exigência de arquivo individual do requisito.

**Legenda sugerida:** “Conferência da orientação contra a passagem original: DOC-02 v2.0, seção 1, página 1. O prazo da declaração de matrícula corresponde à fonte citada; a minuta permanece pendente de decisão humana.”

## Registro 08 — Aprovação humana registrada por Diego

- **Captura original:** recebida no chat, com o formulário e a confirmação da aprovação. Para o arquivo `04_revisao_aprovada.png`, usar a captura posterior do histórico persistido descrita no registro 15; não é necessário guardar as duas imagens para comprovar a mesma decisão.
- **Requisitos relacionados:** RF20 e demonstração humana RF24/T11.
- **O que a imagem mostra:** orientação fundamentada no DOC-02 v2.0, seção 1, página 1; opção `aprovar`, justificativa preenchida e mensagem “Decisão registrada: aprovada. Nada foi enviado ao cidadão.”
- **Persistência confirmada:** leitura do SQLite em modo somente leitura confirmou a minuta `M-UI-002-02774ae6`, caso `UI-002`, estado `aprovada`, operador `Diego`, origem `humana_interface` e transição `pendente → aprovada`, em `2026-10-29T23:54:12.382759+00:00`. O SHA-256 do conteúdo confere com o da decisão.
- **Justificativa registrada:** “Conferi os dados da solicitação e a orientação no DOC-02 v2.0, seção 1, página 1. A minuta está adequada à demonstração fictícia.”
- **Evidência estruturada sanitizada:** [aprovacao_UI002_20261029T235412Z.json](aprovacao_UI002_20261029T235412Z.json). O snapshot anterior, com a minuta ainda pendente, foi preservado. O agente apenas leu a decisão existente, sem aprovar pela pessoa.
- **Estado da demonstração humana:** aprovação de UI-002 e pedido de revisão de UI-001 confirmados. Essas decisões posteriores complementam a evidência humana; não alteram a matriz automática histórica T01–T15, na qual T11 ficou parcial. Ainda é necessário salvar os PNGs recebidos e concluir as demais evidências da entrega.

**Legenda sugerida:** “Aprovação humana registrada por Diego após conferência da orientação no acervo fictício, com justificativa persistida. Aprovar registra a decisão para envio manual; nenhuma resposta foi enviada ao cidadão.”

## Registro 09 — Consulta independente com resposta fundamentada

- **Arquivo:** [03_consulta_trechos_fontes.png](03_consulta_trechos_fontes.png), presente e conferido visualmente. A fonte aberta está descrita no registro 10.
- **Requisitos relacionados:** RF19 e RF20, consulta sem memória conversacional.
- **Pergunta exibida:** “Em quanto tempo é emitida a segunda via da declaração de matrícula?”
- **Resultado exibido:** status `fundamentada`; resposta de até 5 dias úteis a partir da solicitação, citando DOC-02 v2.0, seção 1, página 1, trecho `DOC-02:v2.0:A:p1:s1:c0`.
- **Recuperação exibida:** top-4, limiar 0.35; similaridades 0.740 (DOC-02/seção 1), 0.549 (DOC-01/seção 3), 0.512 (DOC-05/seção 3) e 0.508 (DOC-02/seção 2). A própria interface explica que similaridade mede proximidade e não garante veracidade.
- **Corroboração local:** evento `consulta_rag` de `2026-10-29T23:58:11.725415+00:00`, gerador `principal`, LLM: sim, sem erros, com os mesmos quatro trechos recuperados e uma fonte citada. Latência 3165.1 ms; auditoria com 1119 tokens de entrada e 123 de saída; custo indisponível. [Evento sanitizado](consulta_independente_20261029T235811Z.json), copiado em leitura sem executar nova consulta ao modelo.
- **Limite da captura:** os expansores de fontes citadas e trechos recuperados estão fechados nesta primeira imagem. A passagem da fonte citada foi demonstrada na captura complementar do registro 10. As duas imagens devem ser preservadas em conjunto, pois mostram partes diferentes da tela.

**Legenda sugerida:** “Consulta independente ao acervo fictício, com resposta fundamentada no DOC-02 v2.0 e quatro trechos recuperados identificados por documento e similaridade. A resposta corresponde à declaração de matrícula, com prazo fictício de até 5 dias úteis.”

## Registro 10 — Fonte aberta na consulta independente

- **Arquivo:** [03b_fonte_consulta_aberta.png](03b_fonte_consulta_aberta.png), presente e conferido visualmente.
- **Requisitos relacionados:** RF19 e RF20.
- **O que a imagem mostra:** status `fundamentada`, resposta verificada e expansor do DOC-02 v2.0, seção 1, página 1, aberto, com a passagem original do trecho `DOC-02:v2.0:A:p1:s1:c0`.
- **Conferência:** a frase da resposta corresponde literalmente ao prazo fictício de até 5 dias úteis para a segunda via da declaração de matrícula. Os 20 dias úteis visíveis na mesma passagem referem-se à certidão de conclusão de curso.
- **Complemento ao registro 09:** a primeira captura mostra a pergunta e a lista dos quatro trechos recuperados; esta segunda mostra o conteúdo da fonte citada. A pergunta e a lista completa não estão visíveis nesta segunda imagem. Não se presume que os quatro trechos tenham sido abertos, nem que uma nova consulta tenha sido executada.

**Legenda sugerida:** “Consulta independente com a fonte citada aberta para conferência: a orientação de até 5 dias úteis para a declaração de matrícula corresponde à passagem do DOC-02 v2.0, seção 1, página 1, do acervo fictício.”

## Registro 11 — Painel e tabela de sentimentos com regras locais

- **Arquivos:** [06_painel_sentimentos.png](06_painel_sentimentos.png) (totais e gráfico), [06b_tabela_sentimentos_inicio.png](06b_tabela_sentimentos_inicio.png) (início da tabela) e [06c_tabela_sentimentos_final.png](06c_tabela_sentimentos_final.png) (final da tabela). Os três PNGs estão na pasta e foram conferidos visualmente.
- **Requisitos relacionados:** RF22 e RF23, demonstração do painel e da agregação determinística.
- **Filtros exibidos:** todas as polaridades selecionadas; Requer revisão em `todas`.
- **Resultados exibidos:** 12 IDs únicos; positiva, negativa, neutra e indeterminada com 3 casos cada, ou 3/12 (25,0%) por classe; gráfico coerente com as contagens. Requer revisão: 3/12 (25,0%). Acurácia contra o gabarito: 12/12 (100,0%).
- **Método comprovado na tabela:** `regras_lexicas_v1`, classificação local, sem execução de LLM para estes resultados. A seleção do perfil não está visível nas capturas; o método de cada linha é que identifica o processamento mostrado.
- **Tabela:** as duas capturas complementares mostram AV01–AV12, com polaridade, indicador de revisão, justificativa, método, esperado e texto. AV10, AV11 e AV12 são indeterminadas e requerem revisão: texto misto, possível ironia e falta de contexto, respectivamente.
- **Conferência:** as polaridades e os três indicadores de revisão exibidos correspondem ao gabarito preservado em `dados/gabaritos/desafio6/sentimentos.yaml`. Os 100% se referem somente às 12 avaliações fictícias deste conjunto; não demonstram acurácia geral nem classificação por LLM real.
- **Limite da evidência:** a tabela fica parcialmente visível em cada imagem; as duas partes se complementam. Uma tentativa posterior mostrou aviso vazio (registro 12); depois o filtro com total 3 foi demonstrado no registro 13. Não se presume persistência durável dos resultados de sessão a partir dos prints.

**Legenda do painel:** “Classificação local de 12 avaliações fictícias: três por polaridade (25,0% cada), três casos para revisão (25,0%) e 12/12 rótulos de acordo com o gabarito conhecido. Totais e percentuais agregados por código.”

**Legenda das tabelas:** “Resultados por avaliação, com justificativa, método local e rótulo esperado. Os casos misto, de possível ironia e de falta de contexto são classificados como indeterminados e encaminhados para revisão.”

## Registro 12 — Aviso vazio ao selecionar revisão

- **Nome opcional:** `06e_aviso_vazio_filtro_revisao.png` (recebido no chat; arquivo local pendente).
- **O que a imagem mostra:** todas as polaridades selecionadas, Requer revisão em `sim` e aviso “Conjunto vazio para os filtros atuais (0/0): nenhum percentual é calculado.” Não há tabela ou métricas de três casos nessa captura.
- **Interpretação:** o filtro foi localizado corretamente. A imagem não determina se a sessão ficou sem classificações ou se os dados carregados não correspondiam ao filtro; não comprova o resultado esperado AV10–AV12.
- **Diagnóstico e ajuste:** em teste isolado da interface, os 12 resultados locais foram preservados ao alternar filtros, com 3 casos em `sim` e 9 em `não`. A perda de resultados não foi reproduzida. A interface passou a orientar a classificação quando não há resultados na sessão, mantendo o aviso 0/0 para filtros que realmente não têm correspondências. Ver item 12 do [registro de ajustes](../registro_ajustes.md).
- **Desfecho posterior:** após recarregar as classificações e selecionar `sim`, foi recebida a captura manual com total 3 descrita no registro 13. Isso não determina a causa do aviso vazio anterior. O teste automatizado e a captura manual posterior permanecem identificados separadamente.

## Registro 13 — Filtro de revisão com três avaliações

- **Arquivo:** [06d_painel_filtro_revisao.png](06d_painel_filtro_revisao.png), presente e conferido visualmente.
- **Requisitos relacionados:** RF22 e RF23, filtros e denominadores do painel.
- **O que a imagem mostra:** todas as polaridades selecionadas; Requer revisão em `sim`; total de 3 IDs únicos; indeterminada com 3/3 (100,0%); positiva, negativa e neutra com 0/3 (0,0%) cada; gráfico com contagem 3 para o conjunto filtrado.
- **Conferência:** as contagens e denominadores correspondem ao filtro aplicado sobre os resultados locais anteriormente mostrados, em que AV10, AV11 e AV12 requerem revisão. O denominador mudou de 12 para 3, conforme o conjunto selecionado.
- **Limite da captura:** a tabela com os IDs e o campo método não está visível nesta imagem. Os IDs e o método local estão documentados nas capturas 06b/06c do conjunto completo. O print comprova o estado do filtro e as métricas, sem demonstrar nova classificação por LLM ou decisão humana sobre as avaliações.

**Legenda sugerida:** “Painel filtrado por necessidade de revisão: três avaliações, todas indeterminadas (3/3, 100,0%). As demais polaridades têm 0/3 (0,0%); percentuais calculados sobre o conjunto filtrado.”

## Registro 14 — Auditoria do fluxo e das decisões humanas

- **Arquivo:** [07_auditoria.png](07_auditoria.png), presente e conferido visualmente.
- **Requisitos relacionados:** RF21 e RF24.
- **O que a imagem mostra:** trilha sanitizada com os tipos `consulta_rag`, `decisao_humana` e `solicitacao_processada` selecionados. São visíveis a consulta independente fundamentada, as solicitações com entrada permitida, a consulta anterior com abstenção e as decisões humanas `aprovar` e `revisar`.
- **Corroboração:** [auditoria_fluxo_UI001_UI002.json](auditoria_fluxo_UI001_UI002.json) contém cópia sanitizada de sete eventos já persistidos de UI-001, UI-002 e da consulta independente. A seleção é explícita e não representa todo o histórico. O arquivo registra o hash do log na extração e os IDs de oito testes de orçamento zero que continuam presentes na fonte original.
- **Falhas visíveis:** os eventos com embedding `hash-bow-teste-v1`, orçamento máximo 0, chamadas 0 e erro `OrcamentoExcedido` são bloqueios de testes antes de chamar o LLM. A CLI ignorava o arquivo de auditoria configurado, gravando-os no destino padrão; esse repasse foi corrigido com regressão. A suíte de 201 testes passou sem alterar o hash do histórico manual. Ver item 13 do [registro de ajustes](../registro_ajustes.md). Nenhum evento anterior foi apagado.
- **Leitura dos campos:** `pendente` nas linhas de processamento é o estado naquele momento; as linhas posteriores registram a decisão. Campos `None` correspondem a dados que aquele tipo de evento não fornece à coluna exibida; os estados finais e justificativas estão nos registros sanitizados das decisões. Os horários da tabela usam UTC (`+00:00`).
- **Limite da captura:** há valores longos truncados pela largura da tabela. O print demonstra a consulta da trilha pela interface; os JSONs complementam IDs, estados e hashes. Não é prova de envio ao cidadão, e o protótipo não realiza esse envio.

**Legenda sugerida:** “Trilha de auditoria sanitizada: consultas, processamento e decisões humanas de revisão e aprovação. O histórico preserva a abstenção inicial e os bloqueios de testes de orçamento zero, identificados separadamente dos eventos da demonstração manual.”

## Registro 15 — Histórico da aprovação reaberto na interface

- **Arquivo:** [04_revisao_aprovada.png](04_revisao_aprovada.png), presente e conferido visualmente; corresponde à nova captura do histórico persistido.
- **Requisitos relacionados:** RF20 e RF24/T11, persistência da decisão humana pela interface.
- **Sequência demonstrada:** nas imagens anteriores desta consulta ao histórico, o filtro estava em `aprovada` e a minuta selecionada era `M-UI-002-02774ae6`, caso UI-002, com uma minuta aprovada e uma em revisão. A nova imagem mostra a parte final da minuta e seu Histórico de decisões.
- **O que o histórico mostra:** decisão `aprovar`, estado anterior `pendente`, estado novo `aprovada`, operador `Diego`, justificativa iniciando pela conferência no DOC-02 v2.0, seção 1, página 1, e origem `humana_interface`. A interface informa que a decisão final já está registrada para essa versão.
- **Corroboração:** os campos visíveis correspondem a [aprovacao_UI002_20261029T235412Z.json](aprovacao_UI002_20261029T235412Z.json), que preserva o ID, o horário completo, a justificativa integral e o hash verificado. Não houve novo processamento ou nova decisão para produzir essa captura.
- **Limite da imagem:** o início do horário e o final da justificativa estão cortados pela largura da tabela; o JSON complementa esses campos. O título de minuta pendente pertence ao conteúdo original preservado; o estado atual aparece no seletor e na transição do histórico, sem alterar o texto aprovado ou seu hash.

**Legenda sugerida:** “Aprovação humana persistida e reaberta na interface: transição de pendente para aprovada, registrada por Diego com justificativa e origem humana_interface. A decisão não envia a minuta ao cidadão.”

## Registro 16 — Histórico do pedido de revisão reaberto na interface

- **Arquivo:** [05_revisao_rejeitada_ou_revisar.png](05_revisao_rejeitada_ou_revisar.png), presente e conferido visualmente; corresponde à captura do histórico persistido.
- **Requisitos relacionados:** RF20 e RF24/T11.
- **O que a imagem mostra:** os motivos de abstenção da minuta — afirmação sem suporte removida e ausência de evidência suficiente — e o Histórico de decisões com `revisar`, transição `pendente → revisar`, operador `Diego`, justificativa de complementação/conferência das fontes e origem `humana_interface`.
- **Corroboração:** os dados correspondem ao registro da minuta `M-UI-001-6ee39a04` em [revisao_UI001_20261029T232021Z.json](revisao_UI001_20261029T232021Z.json). Nova leitura do banco confirmou uma única decisão de revisão em UI-001 e uma única aprovação em UI-002, com os hashes do conteúdo preservados. A captura não exige registrar outra decisão.
- **Leitura do formulário abaixo:** a opção `aprovar` aparece selecionada no formulário de uma possível nova decisão. Ela não é o estado persistido da minuta: o histórico mostra `revisar`, confirmado no banco. Não clicar em Registrar decisão humana para produzir esta evidência.
- **Limite da captura:** o início do horário e o fim da justificativa estão cortados pela largura da tabela. O JSON preserva esses campos completos e o vínculo com a minuta. Não houve envio ao cidadão.

**Legenda sugerida:** “Pedido de revisão humana persistido: Diego encaminhou a minuta sem suporte aceito para complementação e conferência das fontes, com transição de pendente para revisar e justificativa registrada.”

## Sequência de organização

| Nº | Nome previsto | Conteúdo a mostrar | Requisitos | Situação |
|---|---|---|---|---|
| 00 | [00_aviso_indice_vazio.png](00_aviso_indice_vazio.png) | Aviso inicial de índice vazio | RF20 | Presente e conferido |
| 01 | [01_indexacao_acervo.png](01_indexacao_acervo.png) | Resultado da indexação | RF17/RF20 | Presente e conferido |
| 02-entrada | `02_entrada_solicitacao.png` | Tela de entrada com operador preenchido, antes do upload | RF20 | Opcional, somente no chat; substituído pelas capturas finais |
| 02-processamento | `02_processamento_minuta_pendente.png` | Ficha válida e minuta pendente com abstenção | RF14/RF15/RF19/RF20 | Somente no chat; captura reduzida substituída pelas imagens abaixo |
| 02a | [02a_ficha_resumo.png](02a_ficha_resumo.png) | Solicitação processada, ficha, resumo e categoria em zoom legível | RF14/RF15/RF20 | Presente e conferido |
| 02b | [02b_minuta_abstencao.png](02b_minuta_abstencao.png) | Minuta pendente com abstenção e motivos de revisão | RF19/RF20 | Presente e conferido |
| 02c | [02c_ficha_declaracao.png](02c_ficha_declaracao.png) | Ficha e resumo do novo caso UI-002 | RF14/RF15/RF20 | Presente e conferido |
| 02d | [02d_minuta_fundamentada.png](02d_minuta_fundamentada.png) + [snapshot](minuta_UI002_pendente_20261029T232759Z.json) | Minuta fundamentada e fonte identificada | RF19/RF20 | Presente e conferido; persistência confirmada |
| 02e | `02e_fonte_aberta.png` | Passagem original do DOC-02 aberta na aba Solicitação | RF19/RF20 | Opcional, somente no chat; fonte coberta para a entrega por 03b, junto à minuta 02d |
| 03 | [03_consulta_trechos_fontes.png](03_consulta_trechos_fontes.png) + [evento da consulta](consulta_independente_20261029T235811Z.json) | Pergunta, resposta, status e trechos recuperados | RF19/RF20 | Presente, conferido visualmente e confirmado na auditoria |
| 03b | [03b_fonte_consulta_aberta.png](03b_fonte_consulta_aberta.png) | Resposta e passagem da fonte citada aberta na consulta independente | RF19/RF20 | Presente e conferido visualmente |
| 04 | [04_revisao_aprovada.png](04_revisao_aprovada.png) + [registro persistido](aprovacao_UI002_20261029T235412Z.json) | Histórico persistido da aprovação de UI-002 por Diego | RF20/RF24 | Presente, conferido visualmente e corroborado no banco |
| 05 | [05_revisao_rejeitada_ou_revisar.png](05_revisao_rejeitada_ou_revisar.png) + [registro persistido](revisao_UI001_20261029T232021Z.json) | Histórico persistido do pedido de revisão de UI-001 por Diego | RF20/RF24 | Presente, conferido visualmente e corroborado no banco |
| 06 | [06_painel_sentimentos.png](06_painel_sentimentos.png) | Gráfico, totais, denominadores e filtros sem restrição | RF22/RF23 | Presente e conferido visualmente |
| 06b | [06b_tabela_sentimentos_inicio.png](06b_tabela_sentimentos_inicio.png) | Primeira parte da tabela, método e justificativas | RF22/RF23 | Presente e conferido visualmente |
| 06c | [06c_tabela_sentimentos_final.png](06c_tabela_sentimentos_final.png) | Final da tabela, incluindo os três casos para revisão | RF22/RF23 | Presente e conferido visualmente |
| 06d | [06d_painel_filtro_revisao.png](06d_painel_filtro_revisao.png) | Filtro `sim`, total 3, denominadores e gráfico; tabela fora do enquadramento | RF22/RF23 | Presente e conferido visualmente |
| 06e | `06e_aviso_vazio_filtro_revisao.png` | Aviso vazio na tentativa anterior com filtro `sim` | RF20 | Opcional; recebido no chat, arquivo local pendente; não comprova o resultado de três casos |
| 07 | [07_auditoria.png](07_auditoria.png) + [recorte sanitizado dos eventos](auditoria_fluxo_UI001_UI002.json) | Eventos registrados do fluxo e das decisões | RF21/RF24 | Presente, conferido visualmente e corroborado no log |

Os nomes sem link continuam planejados: só devem ser tratados como arquivos entregues depois que as imagens estiverem nesta pasta. Os prints recebidos são descritos conforme seu conteúdo, sem presumir etapas ou decisões que não aparecem.

## Próxima etapa na interface

1. O conjunto principal está completo: **15 PNGs presentes e conferidos**, incluindo `05_revisao_rejeitada_ou_revisar.png`, e cinco JSONs válidos. As decisões, os operadores, a origem humana e os hashes dos dois casos foram novamente conferidos no banco em modo somente leitura. Não há outro print pendente desse conjunto.
2. O novo exemplo [DEMO_RF20_declaracao.txt](../../../dados/solicitacoes/DEMO_RF20_declaracao.txt) já foi processado como UI-002, com minuta fundamentada e aprovação humana confirmada. Não é necessário processar ou registrar a decisão novamente.
3. A captura adicional `02e_fonte_aberta.png` é opcional. A fonte aberta já está documentada em 03b, e a minuta que cita esse trecho em 02d; não criar nova solicitação apenas para repetir esse print.
4. A captura `04_revisao_aprovada.png` já está na pasta e foi conferida visualmente, mostrando o histórico da aprovação de UI-002 com operador, justificativa e origem.
5. As duas capturas de Consulta já estão na pasta e foram conferidas visualmente. Não é necessário executar outra consulta para esta evidência.
6. As três capturas do painel e da tabela com método `regras_lexicas_v1` estão presentes e conferidas. O filtro `sim` com total 3 também foi demonstrado posteriormente; não é necessário repetir a classificação para esta evidência.
7. A captura filtrada `06d_painel_filtro_revisao.png` está na pasta e foi conferida. Ela mostra filtro, totais, denominadores e gráfico; as tabelas anteriores complementam os IDs e justificativas.
8. As capturas 04, 05 e 07 estão presentes e conferidas. O pedido de revisão e a aprovação permanecem preservados; não é necessário repetir as decisões ou gerar novas capturas para este conjunto.
9. O registro de uso de IA foi preenchido em nome de Diego Assunção Leite, em 29/10/2026, por sua autorização expressa; ver [uso_da_ia.md](../uso_da_ia.md). O empacotamento continua descrito em [finalização passo a passo](../finalizacao_passo_a_passo.md). As validações de extração, resumo e sentimentos por LLM real permanecem distintas da demonstração local e não são comprovadas por estes prints.

Não incluir `.env` ou credenciais nas imagens. Decisões da equipe não devem ser substituídas por automação ou por decisões de testes simulados.
