# 🏛️ Central Inteligente de Atendimento e Comunicação Institucional

Protótipo desenvolvido em **Python** para receber solicitações fictícias por texto, transcrição de áudio ou OCR, validar dados, produzir resumo e classificação, consultar um acervo institucional por busca vetorial e preparar minutas com fontes para revisão humana.

O projeto disponibiliza uma interface **Streamlit**, extração estruturada com **JSON Schema**, guardrails, índice vetorial persistente, RAG, painel de sentimentos e trilha de auditoria. Corresponde ao **Desafio 6 — Desafio Prático 02, versão 2.0 (2026)**, em continuidade ao Desafio Prático 01.

> Nenhuma resposta é enviada automaticamente ao cidadão. As minutas exigem decisão humana e justificativa. Os dados do conjunto de avaliação são fictícios.

---

## 👨‍💻 Identificação

**Alunos:**

- Diego Assunção Leite
- Ayron Brhenno Silva Figueiredo
- Guilherme da Silva Lessa

**Curso:** FIC_DEV — Programador de Sistemas com IA.

**Módulo:** Inteligência Artificial Generativa — Aulas 08 a 14.

**Instituição:** SECITECI / Escola Técnica Estadual de Cuiabá.

**Atividade:** Desafio Prático 02 — versão 2.0 (2026).

**Repositório:** [desafio-05-central-atendimento-ia](https://github.com/diegocbaleite/desafio-05-central-atendimento-ia).

A evolução preserva o histórico do Desafio 01 e a autoria dos integrantes. Os requisitos continuam a numeração anterior: **RF14 a RF24**. Memória conversacional e persona da Aula 15 ficam fora do escopo obrigatório.

---

## 🎯 Objetivo

Desenvolver uma aplicação modular capaz de:

- Receber solicitações textuais e reaproveitar transcrições de áudio/OCR do Desafio 01.
- Extrair dados em contrato versionado, validar esquema e conferir regras de negócio.
- Resumir solicitações em até 100 palavras, classificar categorias e extrair entidades literais.
- Aplicar proteção à entrada, ao acervo recuperado e à saída, com limites de chamadas e tokens.
- Indexar documentos fictícios em TXT/PDF, com embeddings e metadados rastreáveis.
- Comparar duas configurações de chunking e medir o acerto de recuperação.
- Gerar respostas fundamentadas, com citações verificáveis, abstenção e encaminhamento de conflitos.
- Registrar aprovação, rejeição ou pedido de revisão pela interface Streamlit.
- Classificar doze avaliações de atendimento e agregar indicadores por código.
- Preservar auditoria, demonstrar exclusão de documentos e reexecutar o fluxo anterior.

---

## 📌 Mapeamento da Implementação dos Requisitos Funcionais

O detalhamento refere-se ao fluxo principal em `src/app.py`. Implementação, teste simulado, execução real e decisão humana são estados distintos. Consulte a [matriz detalhada](documentacao/desafio6/matriz_requisitos_d6.md).

### 🔹 RF14 — Extração Estruturada e Validação

- **Requisito:** Converter solicitações em contrato versionado e bloquear estruturas inválidas antes da minuta.
- **Implementação:** `src/contrato.py`, `src/estruturacao.py`, `src/llm_json.py` e `src/schemas/solicitacao.v2.schema.json` validam campos, tipos, ausências e regras de negócio. Saída restrita quando suportada, com no máximo uma correção. Ausências são `null` no contrato e “não localizado” na interface.
- **Validação e limites:** Comparação de JSON sintático/esquema e seis fichas com gabaritos; rodadas LLM e retestes identificados.

### 🔹 RF15 — Sumarização, Classificação e Entidades

- **Requisito:** Produzir resumo de até 100 palavras, categoria e entidades sem completar dados por suposição.
- **Implementação:** `src/nlp.py` separa entidades literais de inferências e compara categorias, entidades e fatos essenciais com gabaritos.
- **Validação e limites:** Seis solicitações avaliadas; resultados por regras locais e por LLM apresentados separadamente.

### 🔹 RF16 — Guardrails, Moderação e Limites

- **Requisito:** Controlar entrada, conteúdo recuperado e saída, incluindo ataques e consumo de recursos.
- **Implementação:** `src/guardrails.py`, `src/orcamento.py` e `src/cliente.py` aplicam limites, proteção de segredos, verificação de conteúdo e no máximo uma repetição transitória.
- **Validação e limites:** Três ataques registrados. ATQ02 teve encaminhamento seguro, com limitação literal de recuperação declarada.

### 🔹 RF17 — Embeddings e Índice Vetorial

- **Requisito:** Manter índice persistente com metadados, top-k configurável e reindexação sem duplicatas.
- **Implementação:** `src/ingestao.py`, `src/embeddings.py` e `src/indice.py` usam fastembed e Chroma; registram documento, versão, hash, página/seção e trecho. Mudança de embedding exige recriação.
- **Validação e limites:** Persistência e reindexação documentadas; modelo real local usado nas avaliações históricas.

### 🔹 RF18 — Chunking e Recuperação

- **Requisito:** Comparar duas configurações com as mesmas cinco perguntas, embedding e top-k.
- **Implementação:** Configurações A/B em `config/config.yaml` e avaliação em `src/avaliacao_integrada.py`, com taxas, resultados por pergunta e justificativa.
- **Validação e limites:** Comparação preservada em `documentacao/desafio6/evidencias/rf18_chunking.json`; seções curtas limitam a discriminação.

### 🔹 RF19 — Geração Fundamentada com RAG

- **Requisito:** Responder com fontes verificáveis e abster-se quando faltar evidência ou houver conflito não resolvido.
- **Implementação:** `src/rag.py` e `src/geracao.py` separam recuperação/geração, delimitam contexto e verificam as afirmações contra citações. Fatos do solicitante são separados das orientações do acervo.
- **Validação e limites:** Oito consultas reais históricas, com cinco respondíveis, duas sem resposta e uma contraditória; falhas anteriores preservadas.

### 🔹 RF20 — Assistente de Documentos em Streamlit

- **Requisito:** Oferecer seleção/indexação de documentos, solicitação, consulta, fontes e revisão pela interface.
- **Implementação:** `src/app.py`, `src/pipeline.py` e `src/revisao.py` exibem ficha, resumo, categoria, minuta, evidências e decisões persistidas.
- **Validação e limites:** Testes headless e capturas da operação humana, incluindo aprovação e pedido de revisão.

### 🔹 RF21 — Provedor Configurável e Auditoria

- **Requisito:** Separar geração da recuperação e registrar origem, parâmetros, falhas, latência e decisões.
- **Implementação:** Perfis em `config/config.yaml`; adaptadores em `src/geracao.py` e `src/cliente.py`; eventos sanitizados em `src/auditoria.py`. Trocar a geração preserva o índice.
- **Validação e limites:** Perfis principal, extrativo local e simulado identificados. Tokens/latência quando disponíveis; custo monetário indisponível.

### 🔹 RF22 — Classificação de Sentimentos

- **Requisito:** Retornar ID, polaridade, justificativa e necessidade de revisão para doze avaliações.
- **Implementação:** `src/sentimento.py` e esquema próprio admitem positiva, negativa, neutra e indeterminada, com regras para mensagens mistas, ironia e falta de contexto.
- **Validação e limites:** Doze avaliações conferidas contra gabarito; incerteza explícita, sem inferir personalidade ou diagnóstico.

### 🔹 RF23 — Avaliação Integrada e Regressão

- **Requisito:** Executar T01–T15 e calcular indicadores com numeradores/denominadores, preservando o fluxo anterior.
- **Implementação:** `src/avaliacao_integrada.py` e `src/metricas.py` avaliam recuperação, sustentação, abstenção, categorias e sentimentos; tratam filtros, duplicatas e conjunto vazio.
- **Validação e limites:** Regressão textual e áudio/OCR reaproveitados. T11 automático permanece parcial por usar simulações, complementado por evidências humanas.

### 🔹 RF24 — Privacidade e Revisão Humana

- **Requisito:** Minimizar dados, definir retenção/exclusão e exigir decisão humana antes de aprovação.
- **Implementação:** `src/privacidade.py`, `src/revisao.py` e exclusão no índice removem vetores/derivados e preservam decisões. Resultados: 90 dias; logs: 180 dias.
- **Validação e limites:** Exclusão demonstrada; UI-002 aprovada e UI-001 enviada para revisão pelo operador, sem envio automático.

---

## ⚠️ Decisões Adotadas para Tratar Dados Inválidos

1. **Bloqueio antes da minuta:** esquema inválido ou regra de negócio incoerente impede a geração e preserva o erro para revisão.
2. **Ausência explícita:** dados ausentes não são inventados; o contrato usa `null`, e a interface apresenta “não localizado”.
3. **Conteúdo não confiável:** instruções em solicitações/documentos não autorizam ações nem alteram regras do sistema.
4. **Abstenção e conflito:** falta de suporte produz abstenção; divergência sem regra suficiente é encaminhada ao operador.
5. **Rastreabilidade:** fontes, versões, trechos, falhas e decisões ficam associados à execução; logs são sanitizados.
6. **Revisão humana:** aprovar não envia a resposta. Decisões simuladas não são apresentadas como humanas.

---

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Aplicação |
|---|---|
| Python 3.12+ | CLI, regras de negócio, processamento e testes |
| Streamlit | Interface local, revisão e painel |
| JSON Schema / jsonschema | Contratos e validação |
| fastembed | Embeddings locais com modelo multilingual MiniLM |
| ChromaDB | Índice vetorial persistente |
| Requests | Integração HTTP com provedores |
| PyYAML / python-dotenv | Configuração e carregamento de credenciais |
| pypdf | Leitura de PDF textual |
| Pillow / pytesseract | Recursos de imagem e OCR reaproveitados |
| unittest / unittest.mock | Suíte automatizada e transportes simulados |
| Git / GitHub | Histórico, branches e integração |

---

## 📁 Estrutura do Projeto

| Caminho | Conteúdo |
|---|---|
| `config/config.yaml` | Provedores, geração, recuperação, limites e retenção |
| `dados/acervo/` | Documentos fictícios e catálogo do fluxo avaliado |
| `dados/solicitacoes/`, `dados/avaliacoes/`, `dados/ataques/` | Casos de avaliação |
| `dados/gabaritos/desafio6/` | Referências e parâmetros prévios |
| `dados/originais/` | Entradas preservadas do projeto |
| `prompts/d6/` | Prompts versionados da entrega |
| `src/` | CLI, interface, contratos, NLP, RAG, revisão e auditoria |
| `src/desafio6/` | Implementação paralela preservada na integração |
| `testes/` | Testes unitários e de integração |
| `scripts/` | Geração de acervo, relatórios e pacote |
| `documentacao/desafio6/` | Matrizes, relatórios, evidências e uso de IA |
| `documentacao/desafio1/` | Documentação histórica |
| `indice/`, `resultados/`, `entrega/` | Artefatos locais; índice, bancos e logs locais não entram no ZIP |

---

## ⚙️ Configuração Dinâmica

O arquivo [config/config.yaml](config/config.yaml) separa geração e recuperação:

| Seção | Responsabilidade |
|---|---|
| `llm`, `provedores` | Endpoint, modelo, timeout e repetições |
| `geracao.perfis` | Principal (LLM), extrativo local (não-LLM) e simulado (mock) |
| `estruturacao` | Modo de compreensão; regras locais por padrão |
| `recuperacao` | Modelo de embedding, chunking A/B, top-k e limiares |
| `guardrails` | Limites de arquivos, entrada, chamadas e tokens |
| `revisao`, `auditoria`, `privacidade` | Persistência, rastreabilidade e retenção |

O perfil principal está configurado com OpenAI e `gpt-6-luna`. O embedding local usa `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, dimensão 384. Estes são os valores versionados do projeto; acesso ao modelo depende da conta/provedor.

Credenciais ficam somente no `.env` ignorado pelo Git. O modelo de variáveis é `.env.example`, sem valores. Em ambiente novo, copie-o para `.env`; preserve um `.env` já existente. A geração principal requer `OPENAI_API_KEY` e pode consumir créditos. O gerador extrativo não chama LLM; a primeira indexação ainda precisa baixar o modelo de embedding.

### Fluxo principal e implementação paralela

A entrega avaliada usa **`src/app.py`**, os comandos diretos `indexar`, `consultar`, `avaliar` e as configurações `geracao`/`recuperacao`. Seu acervo é `dados/acervo/`, com gabaritos em `dados/gabaritos/desafio6/` e evidências em `documentacao/desafio6/`.

A integração preserva também a implementação paralela da main em `src/desafio6/`, acessível por `python -m src.main desafio6 --help` e `python -m streamlit run src/desafio6/app.py`. Ela usa a seção `desafio6` do YAML, embeddings OpenAI e outro catálogo. **Os resultados medidos da entrega não avaliam esse catálogo paralelo.** Seu [README anterior](documentacao/desafio1/README_main_pre_merge.md) foi preservado como referência. Para a entrega e apresentação, siga os comandos abaixo, sem alternar os dois fluxos.

---

## 🐍 Ambiente Virtual e Instalação

### 1. Baixar a main

```bash
git clone https://github.com/diegocbaleite/desafio-05-central-atendimento-ia.git
cd desafio-05-central-atendimento-ia
```

Se já possui um clone, entre na pasta que contém o repositório antes de usar `git checkout main` e `git pull origin main`. Um ZIP extraído não contém `.git`.

### 2. Criar e ativar o ambiente

No Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

No Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependências

```bash
python -m pip install -r requirements.txt
python -m src.main verificar
```

Pré-requisitos: Git e Python 3.12+. Integração conferida em Python 3.12.14/Linux. A primeira indexação requer rede para baixar o modelo aberto e espaço para o cache. Embeddings são locais; consultas ao perfil LLM enviam os trechos recuperados ao provedor.

Novos processamentos de mídia dependem do provedor ou das ferramentas opcionais: Tesseract/Poppler para OCR, FFmpeg/faster-whisper para áudio local e eSpeak para síntese local. O fluxo textual não depende dessas ferramentas. O enunciado permite reaproveitar STT/OCR anteriores.

---

## ▶️ Execução da Aplicação

### Indexação e interface

```bash
python -m src.main indexar
python -m src.main status-indice
python -m streamlit run src/app.py --server.address 127.0.0.1
```

O índice Chroma fica em `indice/`, fora do versionamento. Reindexar o mesmo acervo não cria duplicatas; trocar o modelo de embedding exige `python -m src.main indexar --recriar`. Trocar apenas o perfil de geração preserva o índice.

Na interface, percorra Acervo → Solicitação → Consulta → Revisão → Sentimentos → Auditoria. Confira ficha, fatos do solicitante, trechos e fontes antes de decidir. Os estados são `pendente`, `aprovada`, `rejeitada` e `revisar`. Cada consulta é independente.

### Exemplos de CLI

```bash
# Consulta local sem chamada ao LLM; requer índice e modelo de embedding
python -m src.main consultar "Qual o prazo para a segunda via da declaração de matrícula?" --gerador extrativo_local

# Consulta com o perfil principal configurado; requer chave e pode consumir créditos
python -m src.main consultar "Qual o prazo para a segunda via da declaração de matrícula?"

# Regressão do Desafio 01, identificada como simulação
python -m src.main --mock --decisoes dados/revisao/decisoes_demo.yaml

# Testes sem credenciais e sem chamadas pagas
python -m unittest discover -s testes -t .

# Avaliação local em diretório próprio; não substitui as decisões humanas
python -m src.main avaliar --gerador extrativo_local

# Ajuda e catálogo de modelos da conta (a consulta ao catálogo requer chave)
python -m src.main --help
python -m src.main modelos --provider openai
```

`excluir-documento --doc DOC-06` demonstra remoção dos vetores e derivados; `indexar --doc DOC-06` permite reincluir explicitamente. Faça a demonstração em cópia de trabalho. Dados originais e gabaritos não devem ser adaptados às saídas.

---

## 🧪 Testes Automatizados (unittest)

A suíte cobre contratos, regras de negócio, guardrails, orçamento, persistência, citações, revisão, sentimentos, interface e regressão das duas implementações.

```bash
python -m unittest discover -s testes -t .
```

**Última validação técnica registrada em 30/10/2026:** 322 testes aprovados na integração e no ZIP extraído, com Python 3.12.14/Linux. Na cópia extraída:

```text
Ran 322 tests in 11.174s
OK
```

Esta reorganização do README não altera código nem representa nova execução da suíte. Testes usam transportes simulados e embeddings determinísticos próprios de teste; não comprovam chamadas reais. A indexação real não foi reproduzida neste ambiente devido ao download do modelo; há reprodução histórica documentada.

### Resultados funcionais e evidências

| Frente | Evidência disponível |
|---|---|
| RF14–RF15: esquema, regras de negócio e NLP | Seis solicitações e gabaritos; comparação de JSON sintático/esquema; [validação complementar com LLM](documentacao/desafio6/validacao_complementar_llm_2026-10-29.md) |
| RF16: proteção em camadas e limites | Três ataques, bloqueio de segredo antes da chamada e encaminhamento para revisão; ATQ02 mantém limitação de recuperação declarada |
| RF17–RF18: persistência e chunking | Sete documentos (seis regulares e um adversarial), três temas, TXT/PDF; comparação A/B nas mesmas cinco perguntas com embedding real local |
| RF19: RAG e citações | [Oito consultas reais](documentacao/desafio6/reajuste_rag_openai_2026-10-29.md): 5/5 respondíveis completas, 12/12 fatos essenciais, 2/2 abstenções corretas e conflito encaminhado |
| RF20/RF24: interface e revisão | [15 capturas e registros humanos](documentacao/desafio6/evidencias_humanas/README.md), com uma minuta aprovada e outra enviada para revisão |
| RF21: geração e auditoria | Adaptadores configuráveis, perfil extrativo identificado, tokens/latência quando disponíveis, logs sanitizados; custo monetário indisponível |
| RF22–RF23: sentimentos e regressão | Doze avaliações, métricas com denominadores, filtros/duplicatas/conjunto vazio, regressão textual e áudio/OCR reaproveitados |

**Integração de 30/10/2026: 322 testes aprovados.** As 210 aprovações e as avaliações anteriores permanecem registros históricos. A matriz automática histórica tem 14 aprovados e T11 parcial porque usa decisões simuladas; os registros humanos posteriores complementam RF20/RF24 sem reclassificar simulações.

As métricas de LLM acima são das evidências versionadas de 29/10/2026. Nesta integração não foram feitas novas chamadas pagas. Os números pertencem a um conjunto pequeno e conhecido, com reajustes e retestes declarados; não medem generalização. As métricas locais/extrativas permanecem separadas das chamadas reais.

---

## 🔀 Controle de Versão e Branches

- **`main`:** versão integrada do projeto, incluindo a entrega do Desafio 6.
- **`entrega-desafio6-2026-10-30`:** branch usada para consolidar código, evidências e documentação da entrega.
- **`feature/estudante-1-prompts-avaliacao-documentacao`:** frente de trabalho do Diego.
- **`feature/estudante-2-api-seguranca-texto-auditoria`:** frente de trabalho do Ayron.
- **`feature/estudante-3-audio-ocr-imagem-acessibilidade`:** frente de trabalho do Guilherme.

O [PR #4](https://github.com/diegocbaleite/desafio-05-central-atendimento-ia/pull/4) foi mesclado na `main` em 30/10/2026, pelo commit `87d353e`, preservando o histórico. Os nomes das branches de funcionalidade documentam a organização da equipe, sem exigir que todas permaneçam ativas.

---

## 🤖 Uso de Ferramentas de IA

ChatGPT e agentes de codificação foram utilizados como apoio ao planejamento, implementação, correções, testes, documentação e operações de Git/GitHub. A responsabilidade pela solução permanece com a equipe.

### Finalidades

- Interpretar o enunciado e relacionar requisitos, testes e evidências.
- Organizar contratos, módulos, prompts, recuperação, guardrails e revisão.
- Investigar falhas e propor correções verificáveis.
- Executar testes, conferir artefatos e preparar documentação/pacote.
- Resolver conflitos e integrar a entrega na `main`.

### Exemplos de solicitações desta etapa

- “Pode arrumar o README e ver se o desafio está completo e pode entregar?”
- “Pode me ajudar a fazer o merge da branch entrega para a main?”
- “Verificar se eu fiz certo o merge e está tudo na main.”
- “Pode arrumar o README [...] com o modelo que vou te mostrar?”

### Sugestões aceitas, modificadas e rejeitadas

Foram adotados orçamento de chamadas, verificação literal das citações e identificação separada de simulações. A quarentena e os prompts foram ajustados após falhas declaradas. A proposta de usar texto livre do LLM quando apenas as citações coincidiam foi rejeitada por permitir afirmações não verificadas. Detalhes em [uso de IA](documentacao/desafio6/uso_da_ia.md) e [registro de ajustes](documentacao/desafio6/registro_ajustes.md).

### Participação dos discentes

Diego operou a interface e registrou as decisões humanas de UI-001/UI-002, conforme evidências. A realização de testes por Ayron e Guilherme em 30/10/2026 foi informada por Diego; comandos e resultados individuais não foram localizados. Os testes técnicos executados pelo agente permanecem identificados como tal, sem atribuir aos alunos validações não demonstradas.

---

## ⚠️ Limitações e Riscos Residuais

- ATQ02 foi encaminhado com segurança, mas o trecho malicioso específico não entrou no top-4: critério literal de quarentena parcial.
- A recuperação omitiu um subpedido da S04, com abstenção registrada. A comparação de chunking discrimina pouco por usar seções curtas.
- A interface usa extração/resumo por regras por padrão. As rodadas LLM estão documentadas separadamente; a consolidação de S02/S06 inclui retestes após correção do prompt.
- Não houve nova geração de áudio/imagem nesta etapa; o enunciado permite reaproveitar STT/OCR. Custos não retornados pelo provedor permanecem indisponíveis.
- Retenção configurada: resultados por 90 dias e logs por 180 dias, com aplicação por código. O protótipo exige revisão humana e não representa homologação institucional.

---

## 📦 Entregáveis e Apresentação

Após versionar as alterações:

```bash
python scripts/gerar_zip_entrega.py
```

O ZIP `entrega/desafio-06-central-atendimento-ia.zip` exporta o último commit, com código, dados fictícios, gabaritos, prompts, relatórios e evidências versionadas. Exclui `.env`, ambiente virtual, índices, bancos e logs locais. O script verifica nomes proibidos e padrões de credenciais. Descompacte em outra pasta e execute os testes antes da submissão. Índices são recriados pelos comandos de instalação/indexação; não entram no pacote.

O enunciado prevê apresentação de **até 15 minutos**, seguida de perguntas e verificação prática. Qualquer integrante deve compreender o fluxo completo. A entrega inclui dados fictícios, gabaritos prévios, comparação de JSON/esquema, chunking, oito consultas RAG, três ataques, doze avaliações, regressão, revisão humana e relatório técnico, com limites declarados.

### Documentação de apoio

- [Conferência atual e parecer de entrega](documentacao/desafio6/parecer_entrega_integrada_2026-10-30.md).
- [Matriz RF14–RF24](documentacao/desafio6/matriz_requisitos_d6.md) e [matriz T01–T15](documentacao/desafio6/evidencias/matriz_T01_T15.md).
- [Relatório técnico](documentacao/desafio6/relatorio_tecnico.md), [arquitetura/integração](documentacao/desafio6/integracao_main_2026-10-30.md) e [uso de IA](documentacao/desafio6/uso_da_ia.md).
- [Privacidade e retenção](documentacao/desafio6/privacidade_retencao.md), [resultados locais](documentacao/desafio6/resultados_avaliacao.md) e [ajustes/falhas preservados](documentacao/desafio6/registro_ajustes.md).
- [Roteiro da apresentação de até 15 minutos](documentacao/desafio6/roteiro_apresentacao_15min.md).
- [Histórico do Desafio 01](documentacao/desafio1/README_desafio1.md).

---

## 👨‍💻 Autores

- **Diego Assunção Leite**
- **Ayron Brhenno Silva Figueiredo**
- **Guilherme da Silva Lessa**

**FIC_DEV — Programador de Sistemas com IA — SECITECI / Escola Técnica Estadual de Cuiabá — 2026.**
