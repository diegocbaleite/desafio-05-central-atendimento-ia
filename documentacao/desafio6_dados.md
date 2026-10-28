# Desafio 6 — contratos, NLP e dados prévios

Esta evolução corresponde ao Desafio Prático 02, versão 2.0/2026, Aulas 08–14. Mantém a autoria de Diego Assunção Leite, Ayron Brhenno Silva Figueiredo e Guilherme da Silva Lessa, SECITECI / Escola Técnica Estadual de Cuiabá, curso FIC_DEV. Por instrução posterior explícita do usuário, o acervo funcional passa a usar os arquivos fornecidos em `dados/originais/`, excluindo o brasão; os documentos sintéticos criados inicialmente deixam de compor o acervo. Nenhum gabarito anterior ou original foi modificado.

## Contrato RF14

`src/desafio6/schemas/ficha.schema.json`, versão **2.0**, proíbe chaves extras e exige protocolo, data, solicitante, assunto, pedido, categoria, entidades, campos ausentes e necessidade de revisão. Ausências são `null`; somente a apresentação usa `não localizado`. O formato da data é DD/MM/AAAA. A versão 1.0 da extração anterior continua em seu módulo original; não se misturam contratos.

O esquema comprova tipos e presença de campos. A validação local acrescenta calendário, data da solicitação distinta de nascimento/início do curso, protocolo presente, assunto/pedido/solicitante e entidades literais. A lista de ausências deve corresponder exatamente aos campos nulos. Intenção explícita ambígua exige categoria `revisao`. `comparar_json_esquema()` demonstra separadamente sintaxe, esquema e regras de negócio, incluindo extra, tipo incorreto, obrigatório ausente e valor sem suporte.

## NLP RF15

`analisar_solicitacao()` recebe o cliente isolado, solicita saída restrita pelo esquema e valida localmente. Uma falha de contrato/semântica permite uma única correção; uma segunda falha bloqueia a saída. Erros de autenticação/transporte não provocam correção adicional. O orçamento do cliente também se aplica à correção.

O resumo é **extrativo**, com até 100 palavras: seleciona frases ou linhas completas do original, na mesma ordem, preservando cada palavra, rótulo, pontuação e negação. A validação rejeita apagar “não” ou destacar apenas “foi aprovado” de uma frase negativa. É uma limitação deliberada e verificável para reduzir fatos inventados; não comprova, sozinha, completude nem qualidade semântica entre frases e seu contexto mais amplo. As entidades são literais de pessoas, órgãos, locais, datas e protocolos; datas numéricas ou por extenso também precisam de calendário possível. `inferencias` permanece vazio; não se completam lacunas por suposição. Resultados precisam de revisão humana.

Categorias: `efetivacao_matricula`, `segunda_via_documento`, `andamento_processo`, `atualizacao_cadastral`, `agendamento`, `reclamacao`, `outros` e `revisao`. Categorias incertas exigem revisão. A avaliação compara categorias e entidades com o gabarito e registra omissões de fatos essenciais. Essa medição por texto não substitui o julgamento humano.

Para áudio/OCR, a ficha pode ser analisada, mas `apta_para_minuta` permanece falsa até uma confirmação humana explícita dos campos críticos. Referência conferida, saída bruta, correção e nova transcrição são coisas distintas. `ficha_local_simulada()` usa regras locais e nunca lê o gabarito; sua saída é apoio de teste, não chamada a um LLM.

## Acervo fornecido e preservação

O acervo funcional utiliza os arquivos de `dados/originais/` fornecidos pelo usuário: edital e retificações em PDF, entrada textual, áudio e formulário digitalizado. O arquivo `casos.yaml` fornece metadados de origem/modalidade; o brasão não participa da recuperação. A indexação deve preservar o original e registrar hash, nome, ID, versão, seção/página e origem da transcrição/OCR. Texto extraído de edital real não pode ser apresentado como documento institucional sintético.

Referências conferidas antigas de STT/OCR permanecem evidências históricas; não comprovam nova execução desses motores. A saída bruta I01 rejeitada não deve ser substituída pelos campos corrigidos. Conferência e correção humanas precisam manter vínculo com a versão da entrada.

Os arquivos fornecidos não constituem automaticamente seis solicitações independentes, oito perguntas RAG rotuladas e doze avaliações de atendimento. Sem esses conjuntos e gabaritos prévios específicos, as métricas correspondentes permanecem pendentes. Não completar essa lacuna com solicitações, avaliações ou respostas esperadas inventadas. Perguntas/gabaritos do acervo antigo não podem ser reutilizados como se avaliassem os editais atuais; um conflito entre edital e retificações exige conferir sua vigência e relação explícita antes de escolher fonte.

Somente gabaritos novos fornecidos ou conferidos antes da execução podem avaliar as novas entradas. Os gabaritos antigos de `dados/gabaritos/` permanecem preservados e restritos aos respectivos casos anteriores. Notas, polaridades, aprovação ou participação humana não são preenchidas pelo agente.

## Fixtures exclusivas dos testes

Os cenários sintéticos necessários aos testes de contrato foram isolados em `testes/apoio_desafio6.py`. Não integram o acervo funcional nem evidências dos documentos fornecidos. `preparar_dados(raiz)` exige caminho explícito em um subdiretório temporário e recusa sobrescrever arquivos; não escreve em `dados/originais/`, `dados/reais/` ou outro diretório permanente do projeto. Não existe execução automática ou caminho padrão para gerar corpus sintético. Os testes usam `TemporaryDirectory` e apagam suas fixtures ao terminar.

Essas fixtures verificam erros controlados de esquema, calendário, ausência, negação, orçamento e ataques sem depender de APIs ou alterar o material do usuário. Sucesso nesses testes não mede fidelidade do OCR, precisão de recuperação dos editais nem desempenho de modelo real. O gerador e seus rótulos foram definidos antes das chamadas de teste e não são adaptados a saídas do modelo.

## Validação local

`python -m unittest testes.test_desafio6_contratos testes.test_desafio6_servicos` verificou **31 testes aprovados** após a migração para fixtures temporárias. Os testes de NLP usam cliente simulado e assim não comprovam execução OpenAI. A cobertura mínima do corpus sintético existe somente como cenário unitário, sem comprovar a quantidade de entradas ou gabaritos disponíveis no acervo funcional. O relatório integrado deve registrar separadamente resultados reais e humanos. As inconsistências de RF na matriz do PDF são mapeadas assim: T01/T02 → RF14, T03 → RF15, T04 → RF16; IDs e cenários permanecem iguais aos do enunciado.
