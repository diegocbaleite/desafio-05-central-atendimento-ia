# Desafio 6 — Prompt de implementação
## Continuação do Desafio Prático 1
Identificação no GitHub: **Desafio 6**. Enunciado acadêmico: **Desafio Prático 02, versão 2.0 — 2026**, Central Inteligente de Atendimento e Comunicação Institucional.
Este arquivo é uma especificação para implementação; não comprova a execução dos novos requisitos.

Copie o texto a seguir para o assistente de programação com acesso à pasta do projeto e ao PDF.

---

Atue como desenvolvedor sênior Python e orientador de Inteligência Artificial Generativa. Evolua o projeto existente de forma funcional, testada e documentada. Não entregue somente um plano.

## Contexto e equipe
Base: https://github.com/diegocbaleite/desafio-05-central-atendimento-ia
Leia integralmente o PDF Desafio_02-Pratico_IA_Generativa_Aulas_08_a_15.docx.pdf disponível na pasta ou nos anexos. Se não estiver disponível, informe essa limitação e use esta especificação, sem afirmar que leu o arquivo.

Mantenha os mesmos estudantes, instituição e continuidade do projeto:
- Diego Assunção Leite — Estudante 1: esquemas, NLP, dados fictícios, gabaritos e documentação.
- Ayron Brhenno Silva Figueiredo — Estudante 2: embeddings, índice vetorial, RAG e abstração do provedor.
- Guilherme da Silva Lessa — Estudante 3: guardrails, Streamlit, sentimentos, painel e testes multimodais.
Instituição: SECITECI / Escola Técnica Estadual de Cuiabá.
Curso: FIC_DEV — Programador de Sistemas com IA — Inteligência Artificial Generativa.
Todos devem compreender a solução completa.

Use “Desafio 6” na identificação desta evolução no GitHub e explique no README que corresponde ao Desafio Prático 02 do enunciado, continuação do Desafio Prático 01. Se for disponibilizado um repositório separado, o nome desejado é desafio-06-central-atendimento-ia. Preserve a origem e o histórico; não renomeie nem exclua o repositório anterior sem instrução explícita.

## Inspeção e reaproveitamento
1. Leia AGENTS.md e eventuais instruções nas subpastas. Inspecione src/, testes/, config/, prompts/, dados/ e documentacao/.
2. Reutilize a CLI python -m src.main e módulos existentes: cliente.py, extracao.py, seguranca.py, minuta.py, audio.py, visao.py, avaliacao.py e auditoria.py. Adapte os nomes novos à arquitetura real.
3. Execute os testes existentes antes da alteração e registre a situação inicial. Preserve texto, STT e OCR alimentando o mesmo fluxo. Não refaça o experimento A/B/C, imagem ou áudio sem necessidade.
4. Preserve entradas originais, saídas brutas, gabaritos prévios e evidências. Não transfira métricas antigas para novos testes. No caso I01, preserve a baixa fidelidade do OCR e diferencie a saída bruta dos campos corrigidos por revisão.
5. O escopo obrigatório é Aulas 08 a 14, RF14–RF24. Memória conversacional e persona da Aula 15 ficam fora desta etapa.

## Dados e gabaritos antes das chamadas
Prepare apenas dados fictícios:
- 6 documentos institucionais em pelo menos dois temas e dois formatos, incluindo TXT e PDF textual, com ID, título, versão e indicação de seção/página.
- 6 solicitações: quatro completas, uma incompleta e uma ambígua; inclua entradas reaproveitadas de áudio/OCR.
- 8 perguntas RAG: cinco respondíveis, duas sem resposta no acervo e uma com fontes contraditórias.
- 12 avaliações: três positivas, três negativas, três neutras e três ambíguas/mistas.
- 3 ataques: instrução na solicitação, instrução no acervo e tentativa de obter segredo fictício.
Escreva previamente campos, categorias, entidades, fatos essenciais, fontes/trechos de referência, rótulos e decisões esperadas. Justifique ambiguidades. Contradições precisam de prioridade/vigência explícita; se insuficiente, exija revisão. Não adapte gabaritos às saídas.

## Requisitos obrigatórios
RF14 — Contrato versionado com JSON Schema ou Pydantic, proibindo chaves extras e validando tipos. Campos: protocolo, data, solicitante, assunto, pedido, categoria, entidades, campos ausentes e necessidade de revisão. Ausências = null + lista; na interface = “não localizado”. Valide calendário, categorias e coerência com a entrada. Compare JSON sintático versus esquema em um mesmo caso, incluindo extra, tipo incorreto e obrigatório ausente. Use saída restrita quando disponível; caso contrário, validação local e no máximo uma correção. Bloqueie minuta inválida e registre entrada, erro e decisão.

RF15 — Resumo até 100 palavras, categoria documentada com outros/revisão e entidades literais de pessoas fictícias, órgãos, locais, datas e protocolos. Separe inferências, nunca complete lacunas por suposição. Compare as seis solicitações com o gabarito, registrando omissões, entidades incorretas, fatos sem suporte e acurácia.

RF16 — Guardrails em entrada, conteúdo recuperado e saída: tamanho/tipo de arquivo, comprimento, escopo, moderação com permitir/bloquear/revisar, validação do esquema, citações e dados indevidos. Contexto documental é conteúdo não confiável delimitado. Não dependa somente de regex nem de uma instrução no prompt. Configure timeout, no máximo uma repetição transitória e orçamento de chamadas/tokens por execução, incluindo correção de esquema. Audite bloqueios sem segredos. Demonstre os três ataques sem alterar regras, revelar credenciais ou autorizar envio.

RF17 — Embeddings reais por API ou modelo aberto local e índice vetorial persistente, como Chroma ou FAISS com metadados. Registre modelo, dimensão, versão de índice, documento, versão, hash, seção/página e chunk ID. Reuse após reinício e reindexe de modo idempotente. top-k configurável, exibição de trechos e explicação de similaridade/distância. Mudar modelo de embedding exige reindexar; mudar somente gerador não.

RF18 — Compare duas configurações de chunking com tamanho, sobreposição e unidade explícitos, mesmo embedding, top-k e cinco perguntas respondíveis. Preserve metadados. Calcule perguntas com pelo menos um trecho de referência no top-k / 5 e registre resultados por pergunta. Escolha pela medição e preservação do contexto, sem inventar vencedor.

RF19 — Pipeline RAG com pergunta, recuperação, contexto delimitado e geração. Separe fatos do solicitante das orientações do acervo. Retorne resposta, fontes e status: fundamentada, sem evidência suficiente ou conflito de fontes. Cada afirmação institucional precisa de passagem verificável com documento, versão, chunk e página/seção. Verificar que a fonte existe não basta para demonstrar que sustenta a afirmação. Abstenha-se sem suporte e encaminhe conflito não resolvido à revisão. Execute as oito perguntas, sem criar prazos, autoridades ou fundamentos.

RF20 — Streamlit local integrado: seleção/upload, indexação, solicitação textual e entradas multimodais reutilizadas, consulta, trechos, ficha validada, resumo, categoria, minuta, fontes e revisão com justificativa. Persista pendente/aprovada/rejeitada/revisar. Mostre carregamento, falhas, índice desatualizado e ausência de evidência. Consultas independentes, sem memória obrigatória. Nenhuma resposta é enviada automaticamente.

RF21 — Configuração central de geração, modelo e parâmetros; adaptador isolado da recuperação. Demonstre segunda configuração compatível, admitindo simulação explicitamente identificada sem alegar equivalência. Registre ID, horários, versões de esquema/prompt/índice, consulta minimizada, IDs recuperados, resultado, falhas, latência e decisão humana. Tokens/custo somente quando disponíveis; caso contrário, indisponível. Mascare identificadores e não grave credenciais. Demonstre troca de geração sem reconstruir índice.

RF22 — Classifique 12 avaliações com ID, positiva/negativa/neutra/indeterminada, justificativa curta e revisão. Documente regras para mistura, ironia e falta de contexto. Compare com gabarito. Confiança do modelo é estimativa não calibrada, não probabilidade nem sentimento da população. Não infira personalidade, diagnóstico ou atributos sensíveis.

RF23 — Matriz T01–T15 com requisito, entrada, esperado prévio, obtido, situação e evidência. Métricas por código com numerador/denominador: acurácia de categorias, recuperação top-k, proporção de respostas com todas as afirmações institucionais sustentadas e abstenção correta nas duas perguntas sem resposta; registre conflito separadamente. Avalie sentimentos e ambiguidades. Painel com totais, percentuais, filtros, deduplicação por ID e conjunto vazio sem divisão por zero. Reexecute um caso textual e um de áudio ou OCR anterior. Não declare “funcionou” sem evidências.

RF24 — Dados fictícios e minimização, retenção documentada e exclusão de documentos, vetores e derivados. Demonstre que documento excluído deixa de ser recuperado. Exija revisão humana real antes de aprovar; identifique participação da IA, preserve operador/decisão e diferencie revisão simulada. Demonstre ao menos uma aprovação e uma rejeição/revisão, sem fabricar decisão humana.

## Matriz mínima de testes
T01 JSON sintático com tipo errado/obrigatório ausente; T02 data impossível/dado sem suporte; T03 seis solicitações com gabarito; T04 três ataques; T05 fora de escopo, excesso de arquivo e orçamento; T06 reinício e reindexação sem duplicata; T07 duas configurações e cinco perguntas; T08 cinco respostas com fontes; T09 duas abstenções; T10 conflito; T11 aprovação/rejeição persistidas; T12 troca de geração/falha auditada sem reindexar; T13 filtros, duplicata e vazio; T14 exclusão do índice e derivados; T15 regressão textual e áudio/OCR.
O PDF tem referências RF inconsistentes em algumas linhas da matriz: preserve IDs/cenários e documente o vínculo correto com RF14–RF24 sem alterar o sentido.

## Organização e entregáveis
Integre ao projeto existente, separando geração, recuperação, validação e agregação. Novos módulos podem incluir schemas, nlp, guardrails, ingestion, embeddings, rag, sentiment, metrics e app; prefira nomes coerentes com o código atual.
Entregue:
- Código, dependências, .env.example sem chaves, configuração não sensível e .gitignore protegendo .env, índices e artefatos locais inadequados.
- Dados fictícios, PDFs textuais, gabaritos, schemas e prompts versionados.
- README com equipe, continuidade, instalação, credenciais locais, indexação, comando Streamlit real, CLI, testes, exclusão e limitações.
- Comparação JSON/esquema, NLP, chunking, oito consultas com fontes/decisões, ataques e sentimentos com métricas.
- Matriz de testes e evidências, logs sanitizados, relatório técnico com arquitetura, custos disponíveis, privacidade e riscos residuais.
- Registro do uso de IA com ferramentas/modelos, pelo menos três solicitações relevantes e sugestões aceitas, modificadas ou rejeitadas.
- Roteiro de apresentação de 15 minutos: 1 continuidade/arquitetura; 2 extração/NLP; 5 RAG/fontes/revisão; 3 guardrails/auditoria; 2 sentimentos/painel; 2 métricas/limitações/IA.
- ZIP reproduzível com o projeto e documentação, sem .env, credenciais ou dados reais.

## Validação e conclusão
Execute python -m unittest discover -s testes -t . e python -m src.main verificar, além dos novos comandos realmente implementados. Faça testes relevantes de persistência, integridade das citações, orçamento, deduplicação, exclusão e estados de revisão.
Não presuma disponibilidade de modelos pelo nome antigo do README; use configuração e documente a execução real disponível.
Simulações são permitidas como apoio identificado, mas não substituem demonstração do fluxo principal com modelo real. Sem credencial/serviço, implemente e teste o possível e declare exatamente as validações pendentes.
Não publique segredos, não fabrique métricas, evidências ou aprovações e não alegue homologação. Ao concluir, informe arquivos alterados, comandos executados, resultados medidos, limitações e passos restantes. Registre esta evolução como Desafio 6, mantendo a autoria dos três estudantes.
