# Desafio 6 — índice vetorial e geração com fontes

**Acervo atual:** os arquivos de `dados/originais/`, exceto brasão e configuração. Resultados anteriores nesta documentação referem-se ao conjunto sintético removido e não avaliam os editais fornecidos.

## Arquitetura e estado de implementação

`src/desafio6/indice.py` implementa um índice persistente equivalente para o pequeno
acervo acadêmico: SQLite armazena cada embedding em JSON e seus metadados, e Python
calcula o cosseno exato para selecionar top-k. Não é Chroma/FAISS nem uma busca ANN;
o custo de cada consulta cresce com a quantidade de chunks, sendo inadequado a um
acervo grande sem substituição do mecanismo de busca.

Os embeddings são produzidos pelo cliente injetado. O adaptador real usa a API
OpenAI configurada; os testes usam embeddings falsos explicitamente identificados.
Persistência ou funcionamento dos testes não comprova execução real de um modelo.

`IndiceVetorial(pasta, cliente, tamanho_chunk=90, sobreposicao=20, top_k=3)` oferece:

- `indexar(catalogo, recriar=False)`: lê TXT e PDF textual, valida o acervo e gera um
  único lote para todos os chunks novos. Reindexar conteúdo e metadados idênticos
  mantém a versão e não chama embeddings. Alteração de modelo, dimensão ou chunking
  exige `recriar=True`; trocar apenas o gerador não invalida o índice.
- `estado(catalogo=None)`: informa versão, documentos, chunks, fonte alterada,
  configuração incompatível e necessidade de reindexar. A consulta de catálogo é
  opcional para identificar inclusões/remoções ainda não aplicadas.
- `buscar(pergunta, top_k=None)`: retorna trechos literais, cosseno e rastreabilidade.
  O maior cosseno indica maior proximidade vetorial, sem garantir relevância,
  correção ou suporte factual.
- `registrar_derivado(caminho, documentos)`: associa um artefato gerenciado às fontes.
- `excluir(documento_id)`: remove seus vetores, elimina derivados registrados e muda
  a versão; o texto/PDF de origem é preservado. Assim, a operação não modifica os
  originais nem destrói o conjunto acadêmico de referência.

O catálogo contém ID, título, versão e arquivo; o caminho é relativo à pasta do
catálogo, com compatibilidade para caminhos da raiz do projeto. Uploads gerenciados
podem usar caminho absoluto. O índice guarda ID e versão documental, hash SHA-256,
página no PDF, seção quando identificável, chunk ID, modelo, dimensão, parâmetros de
chunking e versão única de indexação. PDF sem camada textual é rejeitado: deve passar
pelo fluxo anterior de OCR e conferência dos dados críticos.

A divisão usa **palavras**, mantém substrings exatas da origem e nunca mistura
páginas ou seções. A gravação dos novos vetores é transacional: falha de validação,
guardrail ou embedding não substitui os dados anteriores. O fechamento de cada conexão
SQLite é explícito para não manter arquivos bloqueados no Windows.

## Geração e verificação de suporte

`src/desafio6/rag.py:responder(pergunta, indice, cliente, solicitacao=None)` separa
os fatos da solicitação do contexto documental. A pergunta, os fatos e as passagens
ficam em uma mensagem de dados delimitada; apenas o prompt versionado tem papel de
instrução. Não se disponibilizam ferramentas, segredos ou envio ao modelo.

O modelo escolhe passagens por JSON restrito `{status, afirmacoes:[{chunk_id,trecho}]}`.
O código valida o esquema, exige que **cada afirmação seja uma passagem literal**
do chunk indicado e monta a minuta apenas com essas passagens. A existência do ID,
sozinha, não aprova uma citação. Texto inventado, chunk desconhecido, dado indevido
ou instrução maliciosa bloqueiam a saída. Essa abordagem prioriza verificabilidade;
não oferece a fluidez de uma paráfrase institucional abstrativa.

A passagem precisa corresponder a frases completas ou à seção inteira:
uma substring isolada pode excluir “não” ou uma condição e inverter o sentido.
Há teste específico em que a fonte diz que o sistema **não confirma** o deferimento,
mas o modelo tenta recortar apenas a oração afirmativa; a saída é bloqueada.
As fronteiras são conferidas relendo a seção/página original completa, com seu hash;
mesmo uma seleção do chunk inteiro é rejeitada se truncar uma frase. O fim de um
chunk por palavras não é tratado como fim de frase. Um teste também rejeita a
seleção que corta uma condição no limite do chunk.

Também há uma barreira lexical mínima para não interpretar qualquer vizinho vetorial
como evidência. Ela é heurística e não substitui revisão temática/semântica. A
correspondência literal sustenta a citação; **relevância, completude e adequação ao
caso ainda exigem avaliação humana**. As métricas devem conservar essas limitações
e não apresentar citações literais como homologação de uma resposta completa.

Os três estados são `fundamentada`, `sem evidência suficiente` e `conflito de fontes`.
Toda resposta fica pendente de revisão humana. O modelo pode abster-se mesmo quando
foram encontrados vizinhos vetoriais. Grupos explicitamente contraditórios são
consultados em conjunto; sem precedência documentada suficiente, são apresentados
os dois documentos e o caso segue para revisão. A marca de conflito aplica-se à
política consultada, evitando ativá-la por vocabulário administrativo genérico.

Pedidos quantitativos de prazo ou valor recebem uma barreira adicional: uma frase
verdadeira sobre matrícula que não informa dias/data ou valor monetário não responde
à pergunta quantitativa e resulta em abstenção. A regra é deliberadamente conservadora
e pode abster-se em uma resposta não numérica válida; essa limitação deve ser medida.
Uma prioridade numérica não resolve conflitos se a vigência for uma string ambígua:
o intervalo precisa ser expresso como `{inicio: "AAAA-MM-DD", fim: null ou data}` e
estar ativo. Sem isso, o resultado permanece conflito e revisão humana.

Os guardrails são aplicados antes de indexar, à pergunta, ao contexto recuperado e
às passagens de saída. Fichas inválidas e saídas multimodais sem conferência humana
não podem alcançar a minuta. Nenhuma etapa envia conteúdo ao cidadão ou registra
aprovação por conta própria.

O endpoint RAG também revalida o esquema inteiro da análise e a coerência local de
campos, calendário, resumo e metadados, sem confiar em uma flag `valida`. Opcionalmente
`responder(..., original=texto)` refaz a validação literal contra a fonte; o controlador
deve preservar essa verificação ao integrar fichas. Flags ou propriedades adicionais
não documentadas são rejeitadas antes de qualquer embedding/geração.

## Falha observada e correção de segurança

Uma verificação simulada inicial das oito perguntas encontrou Q06 com status
`fundamentada`: o seletor local citou corretamente “A ausência de documento não
autoriza o sistema a afirmar que a matrícula foi deferida.”, mas essa frase não
informava o prazo em dias pedido. As outras sete classificações de status coincidiram
com o gabarito prévio. Foi corrigida a validação de pedidos quantitativos, sem alterar
qualquer documento ou gabarito. A nova verificação simulada retornou os oito status
esperados; isso não constitui validação real nem aprovação humana do conteúdo.

## Comparação de chunking

`comparar_chunking(catalogo, perguntas, cliente, pasta, configs=[(90,20),(45,10)],
top_k=3)` constrói dois índices separados, usa o mesmo modelo/dimensão e mede as
cinco perguntas respondíveis previamente rotuladas. O gabarito é usado apenas depois
da recuperação, nunca como entrada do embedding ou da seleção de resposta.

Acerto significa ao menos um chunk top-k do documento de referência contendo seu
trecho literal. Cada configuração informa resultados por pergunta, numerador,
denominador **5**, taxa e trechos recuperados. Um vencedor só é indicado se houver
diferença medida; empate preserva a escolha pendente de inspeção do contexto. Uma
execução nova demanda até 12 chamadas sem retentativas: dois lotes de indexação e
dez embeddings de pergunta. Falhas e retentativas respeitam o orçamento do cliente.

## Testes e limites de exclusão

`python -m unittest testes.test_desafio6_rag -v` testa persistência após reinício,
idempotência, fonte alterada, mudança de embedding, troca apenas de gerador,
chunking literal, comparação, citações inventadas, abstenção, conflito, ataques,
vetor inválido e exclusão de vetores/derivados. São testes **simulados**, sem chamadas
pagas. O controlador registra separadamente as execuções reais.

Por segurança, derivados registrados devem permanecer dentro da pasta gerenciada
do índice; caminhos resolvidos fora dela ou o próprio banco não são excluídos.
Arquivos que não foram registrados não são removidos por essa API. O controlador
deve vincular todas as saídas e decisões derivadas às fontes para completar a política
de retenção. A exclusão remove resultados gerenciados e impede recuperação do
documento, mas não solicita apagamento remoto de dados já transmitidos à OpenAI.
