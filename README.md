# Desafio 6 — Central Inteligente de Atendimento e Comunicação Institucional

Esta evolução corresponde ao **Desafio Prático 02, versão 2.0 — 2026**, Aulas 08 a 14, e continua o Desafio Prático 01 no mesmo repositório. A autoria e o histórico de Diego Assunção Leite, Ayron Brhenno Silva Figueiredo e Guilherme da Silva Lessa foram preservados. Instituição: SECITECI / Escola Técnica Estadual de Cuiabá; curso FIC_DEV — Programador de Sistemas com IA.

**Acervo atual:** arquivos fornecidos em `dados/originais/`: edital, retificações, texto, áudio e PDF digitalizado. O brasão não participa das perguntas; `casos.yaml` é configuração. A extração do áudio e do PDF digitalizado usa a OpenAI na primeira indexação real. Os originais são preservados e os textos extraídos ficam em `resultados/desafio6/`. O conjunto sintético inicial foi removido a pedido da equipe; suas métricas anteriores são históricas e não avaliam os documentos atuais.

O Desafio 6 acrescenta ficha com JSON Schema e regras de negócio, resumo extrativo, entidades, guardrails, embeddings OpenAI, índice SQLite persistente, RAG com citações verificadas, revisão humana, Streamlit e painel de sentimentos. A documentação abaixo dessa seção preserva o histórico do Desafio 01. Não reutilize métricas históricas como evidência do fluxo novo.

## Executar o Desafio 6

Com Python 3.12+ (ambiente observado: 3.14.6), instale as dependências no ambiente virtual e mantenha `OPENAI_API_KEY` apenas no `.env` ignorado. Se o `.env` já existe, preserve-o; copie `.env.example` somente em uma configuração nova.

```powershell
python -m pip install -r requirements.txt
python -m src.main verificar
python -m src.main desafio6 indexar
python -m src.main desafio6 consultar --pergunta "Quais documentos apresentar para solicitar matrícula?"
python -m streamlit run src/desafio6/app.py --server.address 127.0.0.1
```

Na interface, selecione os documentos fornecidos, indexe, informe solicitação/pergunta, confira a ficha, os trechos e a minuta e registre a decisão com responsável e justificativa. Áudio/OCR exigem conferência de nomes, datas e protocolos. Confira também as retificações e a vigência antes de usar informações dos editais. Cada consulta é independente. Não há envio automático, memória conversacional ou aprovação por IA.

```powershell
# Sem APIs: simulação identificada em pasta separada; não comprova execução de modelo
python -m src.main desafio6 indexar --mock
python -m src.main desafio6 consultar --mock --pergunta "Quais documentos apresentar para solicitar matrícula?"
# A avaliação requer novos casos e gabaritos prévios para os documentos atuais
python -m src.main desafio6 avaliar --mock --dados CAMINHO_DOS_CASOS

# Avaliações reais: consomem créditos da API; preservam falhas e revisão pendente
python -m src.main desafio6 avaliar --dados CAMINHO_DOS_CASOS
python -m src.main desafio6 chunking --perguntas CAMINHO_PERGUNTAS.json
python -m src.main desafio6 sentimentos --avaliacoes CAMINHO_AVALIACOES.json

# Trocar apenas a geração reutiliza o índice de embeddings
python -m src.main desafio6 consultar --modelo gpt-6.1-terra --pergunta "Quem faz a conferência da matrícula?"

# Exclusão usa um ID exibido pelo comando estado e preserva os originais
python -m src.main desafio6 excluir --documento-id ID_DO_DOCUMENTO
python -m src.main desafio6 estado

python -m unittest discover -s testes -t .
python -m src.main --mock --decisoes dados/revisao/decisoes_demo.yaml
python -m src.main desafio6 empacotar
```

O índice, uploads, revisões e evidências locais ficam em `resultados/desafio6/real/` e `resultados/desafio6/simulado/`, ignorados pelo Git. Para avaliar o novo acervo, prepare perguntas e gabaritos independentes antes das chamadas. O pacote de código sai em `dist/desafio-06-central-atendimento-ia.zip`, sem `.env`, índices ou logs locais.

Geração: `gpt-6-luna`; embeddings: `text-embedding-3-small`, 256 dimensões. Configuração em `config/config.yaml`, seção `desafio6`. A busca percorre vetores por cosseno em SQLite, equivalente persistente para acervo pequeno; não é uma busca ANN escalável. Fonte literal, relevância e revisão humana são verificações distintas. A reserva de tokens não é custo medido; uso/custo ausentes permanecem indisponíveis.

Consulte o [relatório do Desafio 6](documentacao/desafio6_relatorio.md), a [matriz RF14–RF24/T01–T15](documentacao/desafio6_matriz.md), os [dados e gabaritos](documentacao/desafio6_dados.md), a [recuperação e RAG](documentacao/desafio6_rag.md) e a [interface/revisão/sentimentos](documentacao/desafio6_interface.md). A implementação não comprova aprovação humana nem homologação institucional.

---

## Histórico do Desafio Prático 01

Protótipo educacional desenvolvido em **Python** para apoiar o tratamento de solicitações fictícias recebidas por **texto, áudio e imagem**. A aplicação valida entradas, transcreve áudio, executa OCR, extrai e classifica informações, gera minutas institucionais, oferece síntese de voz, prepara peças visuais e registra evidências de execução e revisão humana.

> **Atenção:** este projeto é uma demonstração acadêmica, não um sistema oficial de atendimento. **Nenhuma resposta é enviada automaticamente ao cidadão.** Uma pessoa responsável deve revisar informações e minutas antes de qualquer aprovação.

---

**Equipe:** Diego Assunção Leite · Ayron Brhenno Silva Figueiredo · Guilherme da Silva Lessa

**Integração atualizada em 28/10/2026:** OpenAI é o provedor padrão de texto, visão, transcrição, voz e imagem. A chave é carregada de `OPENAI_API_KEY` no `.env` local. Uma chamada real de texto foi concluída; validações OpenAI de STT/OCR/TTS/imagem e revisão humana continuam pendentes. As métricas anteriores deste README pertencem às execuções históricas dos outros provedores. Veja o [registro da integração OpenAI](documentacao/integracao_openai.md).

## 👨‍💻 Identificação

**Equipe e responsabilidades:**

- **Diego Assunção Leite — Estudante 1:** engenharia de prompts, comparação de modelos, critérios de avaliação e documentação.
- **Ayron Brhenno Silva Figueiredo — Estudante 2:** integração por API, segurança, processamento de texto e registro das execuções.
- **Guilherme da Silva Lessa — Estudante 3:** áudio, visão/OCR, geração de imagem, acessibilidade e testes multimodais.

**Curso/módulo:** FIC_DEV — Programador de Sistemas com IA — Inteligência Artificial Generativa (Aulas 01 a 07)\
**Instituição:** SECITECI / Escola Técnica Estadual de Cuiabá\
**Atividade:** Desafio Prático 1 — versão 1.0 (2026)\
**Repositório:** [https://github.com/diegocbaleite/desafio-05-central-atendimento-ia](https://github.com/diegocbaleite/desafio-05-central-atendimento-ia)

---

## 🎯 Objetivo

Construir um protótipo local e reproduzível que seja capaz de:

- Receber e validar solicitações fictícias em texto, áudio e documentos digitalizados.
- Executar transcrição de fala (**STT**) e reconhecimento de caracteres (**OCR**), preservando os arquivos originais e os resultados brutos.
- Extrair protocolo, data, solicitante, assunto e pedido em **JSON**, com evidências, classificação e indicação de dados ausentes.
- Gerar **minutas institucionais** baseadas exclusivamente nos dados disponíveis e sinalizar lacunas com `não localizado`.
- Comparar os prompts **A (zero-shot), B (estruturado) e C (metaprompt)** e justificar o uso de um prompt seguro.
- Permitir que uma pessoa **aprove, rejeite, corrija ou solicite nova geração** de uma minuta.
- Produzir áudio de acessibilidade (**TTS**) somente com aprovação humana válida.
- Produzir uma peça visual de orientação, diferenciando composição local programática de imagem efetivamente gerada por IA.
- Registrar modelo, parâmetros, tempo, falhas, uso de tokens quando disponível, hash e decisões humanas, sem expor credenciais.

---

## 📌 Mapeamento da implementação dos requisitos funcionais (RF01–RF13)

As funcionalidades abaixo estão **implementadas**; isso não significa que todas tenham sido **validadas com serviço real e homologadas**. Consulte a [matriz de requisitos](documentacao/matriz_requisitos.md) para acompanhar as evidências e pendências.

### 🔹 RF01 — Inicialização e configuração

- **Requisito:** executar o projeto de maneira reproduzível, com configuração e segredos separados.
- **Implementação:** `src/main.py` oferece a CLI `python -m src.main`; `config/config.yaml` contém parâmetros não sensíveis; `.env.example` apresenta o modelo das variáveis de ambiente; `src/config.py` carrega a configuração.
- **Validação:** comando `python -m src.main verificar` e testes automatizados.

### 🔹 RF02 — Engenharia de prompts

- **Requisito:** comparar A (zero-shot), B (estruturado) e C (metaprompt), mantendo as mesmas entradas e condições sempre que possível.
- **Implementação:** `prompts/experimento/`, `src/experimento.py`, versões `prompt_B_v2_seguro.md`, `prompt_B_v3_seguro.md`, `prompt_B_v4_seguro.md` e `src/experimento_b_v2_real.py`.
- **Casos atuais:** o experimento usa as entradas textuais `T01`, `X01` e `X02` definidas em `dados/originais/casos.yaml`. Cada execução grava uma matriz nova e preserva as saídas por caso e prompt.
- **Situação:** comparação real concluída com 9/9 chamadas bem-sucedidas para `T01`, `X01` e `X02`. A avaliação RF13 atual está registrada em [avaliação do catálogo atual](documentacao/avaliacao_rf13_catalogo_atual.csv): A = 3,67/10, B = 7,33/10 e C = 5,33/10. O Prompt B foi selecionado para evolução por obter a melhor média relativa, embora suas saídas ainda exijam correção. Não foram reutilizadas notas de conjuntos anteriores.

### 🔹 RF03 — Prompt seguro e conteúdo não confiável

- **Requisito:** tratar conteúdo externo como dados, não como instruções; impedir invenção de informações e sinalizar lacunas.
- **Implementação:** `prompts/sistema_minuta.md`, `src/seguranca.py` e teste de **prompt injection** no caso atual `X01`.
- **Limite:** a detecção heurística por regras/regex e o teste específico não garantem imunidade a qualquer ataque. A revisão humana continua obrigatória.

### 🔹 RF04 — Chamada de API e tratamento de falhas

- **Requisito:** realizar chamadas a modelos com parâmetros configuráveis, timeout, tratamento de erros e proteção de credenciais.
- **Implementação:** `src/cliente.py` integra provedores configuráveis; `src/auditoria.py` preserva registros de execução sem chaves secretas.
- **Evidências:** cliente e retentativas cobertos por testes. O fluxo atual foi executado com serviços reais e registrou chamadas ao Gemini para minutas, comparação A/B/C, OCR e TTS, ao Groq para STT e à Cloudflare para imagem. A rodada A/B/C atual preservou matriz, saídas, tokens, latência e tentativas. Falhas externas são registradas, e valores de custo só são declarados quando fornecidos pelo provedor ou calculados sobre tarifa verificável.

### 🔹 RF05 — Extração estruturada de texto

- **Requisito:** identificar campos, classificar solicitações e manter JSON válido quando faltarem dados.
- **Implementação:** `src/extracao.py` e `src/schemas/extracao.schema.json`; extração local por regras, com evidências, confiança e marcador `não localizado`.
- **Evidência:** testes de solicitações completas e incompletas. A extração dos campos **não** depende de uma chamada externa ao LLM.

### 🔹 RF06 — Transcrição de áudio (STT)

- **Requisito:** transcrever uma mensagem de voz fictícia, preservar o texto bruto e conferir nomes, datas e protocolos.
- **Implementação:** `src/audio.py`, com `faster-whisper` local opcional ou Groq configurado, e avaliação em `src/avaliacao.py`.
- **Situação:** execução real pelo Groq e execução local documentadas. A referência independente de `A01` está vinculada ao catálogo e os campos críticos foram conferidos. Métricas consolidadas: **WER 11,43%** e **CER 5,06%**. Resultado aprovado para demonstração, com referência e transcrição bruta preservadas separadamente.

### 🔹 RF07 — Síntese de voz e acessibilidade (TTS)

- **Requisito:** gerar uma versão falada de uma minuta realmente aprovada, com voz e entonação adequadas.
- **Implementação:** `src/audio.py`, comando `voz`, suporte local a eSpeak e integração Gemini configurada; vinculação da síntese à revisão humana e ao hash da minuta.
- **Situação:** execução real do Gemini TTS concluída e validada para demonstração, com WAV, roteiro falado, duração, hashes, vínculo com a minuta e confirmação auditiva registrados. O áudio representativo tem 29,04 segundos, voz `Kore`, formato mono a 24 kHz e permanece sem uso oficial ou envio ao cidadão.

### 🔹 RF08 — Visão computacional e OCR

- **Requisito:** extrair texto de documento fictício, preservar os originais, identificar incertezas e conferir os dados críticos.
- **Implementação:** `src/visao.py`; Tesseract local para imagem/PDF digitalizado e opção de visão Gemini.
- **Situação:** Tesseract e Gemini foram executados; uma tentativa anterior do Gemini retornou **HTTP 503**, e uma execução posterior foi concluída. A referência independente foi conferida. Métricas da saída remota: **WER 91,89%** e **CER 85,91%**. A revisão corrigiu os campos críticos para código `2026-000142`, data `14/10/2026` e solicitante `MARCOS VINÍCIUS DE ALMEIDA SANTOS`. A execução foi validada, mas a saída bruta foi rejeitada por baixa fidelidade e permanece preservada.

### 🔹 RF09 — Minuta institucional

- **Requisito:** redigir uma minuta baseada somente no contexto disponível, indicando ausências e impedindo envio automático.
- **Implementação:** `src/minuta.py`, `prompts/sistema_minuta.md` e fluxo de aprovação em `src/main.py`.
- **Evidência:** o fluxo gera minutas pendentes para os casos atuais e mantém original, extração, minuta e revisão em artefatos separados. Decisões carregadas de YAML são sempre simulações e não constituem aprovação ou documento oficial GOV.MT.

### 🔹 RF10 — Geração ou edição de imagem

- **Requisito:** criar ou editar peça visual, identificar uso de IA e registrar prompt, modelo, data e revisão.
- **Implementação:** `src/imagem.py`, `prompts/imagem_orientacao.md` e comando `arte`; composição local com **Pillow** e opção de geração com Cloudflare Workers AI / FLUX.
- **Situação:** composição programática local testada e geração real pela API Cloudflare Workers AI / FLUX concluída. Imagem, prompt, modelo, parâmetros, hashes e proveniência estão registrados em `resultados/imagens/`. A revisão visual foi registrada como aprovada para demonstração, mantendo `uso_oficial: false` e a identificação explícita de imagem gerada por IA.

### 🔹 RF11 — Auditoria e rastreabilidade

- **Requisito:** registrar execução, arquivo de origem, modelo, parâmetros, tempo, erros, resultados e decisão humana.
- **Implementação:** `src/auditoria.py` e registros JSONL em `resultados/logs/<id>/`, relacionados aos arquivos e minutas da mesma execução.
- **Limite:** métricas não disponibilizadas pelos provedores devem ser registradas como não medidas/não localizadas, nunca inventadas.

### 🔹 RF12 — LGPD e minimização

- **Requisito:** usar dados fictícios, proteger segredos e minimizar o conteúdo remetido aos provedores.
- **Implementação:** `src/seguranca.py`, `.gitignore`, variáveis em `.env` e [documentação LGPD](documentacao/lgpd.md).
- **Situação:** checklist acadêmico de dados fictícios, retenção, inspeção de registros e autorização de voz concluído em [documentação LGPD](documentacao/lgpd.md). A validação vale para este protótipo e seus dados fictícios; uma implantação real ainda exigiria análise jurídica, contratual, de segurança e de transferência de dados. Ao selecionar Groq ou Gemini, **áudio ou páginas de documentos podem ser transmitidos aos provedores**.

### 🔹 RF13 — Qualidade e revisão humana

- **Requisito:** avaliar fidelidade, completude, formato, linguagem e segurança, classificar erros e registrar decisões.
- **Implementação:** `src/avaliacao.py`, [protocolo RF13](documentacao/protocolo_avaliacao.md) e gabaritos prévios em `dados/gabaritos/`.
- **Situação atual:** os cinco casos possuem gabarito anterior à execução e foram processados em fluxo real. A rodada A/B/C dos três casos textuais recebeu avaliação nos cinco critérios RF13, decisão e justificativa em [avaliação do catálogo atual](documentacao/avaliacao_rf13_catalogo_atual.csv). Foram avaliadas 9/9 saídas, com média geral 5,44/10 e taxa de aprovação direta de **0/9 (0%)**; esse resultado documenta as falhas e sustenta a escolha relativa do Prompt B. Decisões `--mock` e YAML permanecem fora do cálculo.

---

## 📊 Casos atuais e estado da avaliação

| Caso | Modalidade | Finalidade de teste | Estado da evidência |
|---|---|---|---|
| `T01` | texto | Solicitação fictícia de efetivação de matrícula | Entrada, gabarito, execução real A/B/C e avaliação RF13 registradas |
| `A01` | áudio | Mesma solicitação por voz, com conferência de campos críticos | STT real validado; WER 11,43%, CER 5,06% e campos críticos conferidos |
| `I01` | imagem/PDF | Mesma solicitação em documento digitalizado | OCR real avaliado; baixa fidelidade documentada e campos críticos corrigidos pela referência |
| `X01` | texto | Reclamação fictícia com tentativa de injeção de prompt | Detector, fluxo seguro, execução real A/B/C e avaliação da injeção registrados |
| `X02` | texto | Agendamento fictício com campos ausentes | Uso de `não localizado`, execução real A/B/C e avaliação RF13 registrados |

Os gabaritos foram preparados antes das execuções e não devem ser adaptados às saídas. Resultados `mock` demonstram o fluxo, mas não comprovam desempenho de um modelo externo. Consulte o [relatório técnico](documentacao/relatorio_tecnico.md) para o estado consolidado e as pendências.

---

## ⚠️ Decisões técnicas adotadas e limitações

1. **Revisão humana antes de qualquer uso:** o sistema pode produzir minutas, mas não envia respostas automaticamente; aprovações simuladas não são assinaturas ou validações reais.
2. **Preservação dos originais:** entradas, transcrições/OCR brutos, minutas e edições de demonstração ficam separados para permitir comparação e auditoria.
3. **Dados faltantes e alucinações:** usar `não localizado`; não afirmar prazo, deferimento, gratuidade, exigência de protocolo ou encaminhamento sem fonte.
4. **Segurança de prompts:** conteúdo de formulário, PDF e mensagens é dado externo não confiável, inclusive quando contém instruções maliciosas.
5. **Métricas confiáveis:** WER e CER exigem gabarito independente; não transformar simulação em execução real nem preencher custo/tempo inexistentes.
6. **Provedores externos:** disponibilidade, cotas e erros HTTP podem impedir validação real; as pendências de Gemini e Cloudflare estão documentadas.
7. **Uso institucional:** a referência visual ao brasão não comprova compatibilidade ou autorização oficial de documentos GOV.MT.

---

## 🛠️ Tecnologias utilizadas

- **Python** (CI validado com **3.12**; ambiente de desenvolvimento também utilizado com Python 3.14).
- **requests** para chamadas HTTP e integração com provedores.
- **PyYAML** para configuração e casos de teste.
- **jsonschema** para validação do JSON extraído.
- **python-dotenv** para carregamento local de variáveis de ambiente.
- **Pillow** e **pytesseract/Tesseract** para imagens e OCR; **Poppler** para PDF digitalizado.
- **faster-whisper** (opcional, STT local); **Groq**, **Gemini** e **OpenRouter** conforme configuração e credenciais.
- **eSpeak** (TTS offline), **FFmpeg** (ferramentas de áudio) e integração opcional de **Cloudflare Workers AI**.
- **unittest**, **Git/GitHub** e **GitHub Actions** para testes e versionamento.

---

## 📁 Estrutura do projeto

```
desafio-05-central-atendimento-ia/
├── .github/workflows/testes.yml
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── config/
│   └── config.yaml
├── dados/
│   ├── originais/       # texto, áudio, PDF, brasão fictício e casos.yaml
│   ├── gabaritos/       # T01, A01, I01, X01 e X02
│   └── revisao/         # decisões simuladas identificadas
├── prompts/
│   ├── experimento/     # A, B, C, metaprompt e versões B V2/V3/V4
│   ├── sistema_minuta.md
│   └── imagem_orientacao.md
├── src/
│   ├── main.py          # CLI e coordenação do fluxo
│   ├── config.py        # configuração e credenciais
│   ├── cliente.py       # cliente HTTP para modelos
│   ├── extracao.py      # campos, evidências e classificação
│   ├── seguranca.py     # minimização e segurança
│   ├── minuta.py        # geração de minuta
│   ├── audio.py         # STT e TTS
│   ├── visao.py         # OCR/visão
│   ├── imagem.py        # peça visual
│   ├── avaliacao.py     # avaliação e métricas
│   ├── auditoria.py     # registros JSONL
│   ├── experimento.py
│   ├── experimento_b_v2_real.py
│   └── schemas/
├── testes/              # testes unittest e fixtures
├── documentacao/        # relatório, RF13, LGPD e demais evidências
├── auditorias/
└── resultados/           # diretórios criados localmente; não versionar dados sensíveis
    ├── execucoes/
    ├── minutas/
    ├── audios/
    ├── ocr/
    ├── imagens/
    └── logs/
```

---

## ⚙️ Configuração dinâmica (`config/config.yaml`)

A configuração atual do projeto define opções de modelo, provedor, recursos multimodais e segurança. **Exemplo reduzido** do YAML (não contém segredos):

```
llm:
  provider: "openai"
  modelo: "gpt-6-luna"
  reasoning_effort: "none"
  temperatura: 0.2
  max_tokens: 2400
  timeout_s: 45

multimodal:
  stt_provider: "openai"
  stt_modelo: "gpt-transcribe"
  ocr_provider: "openai"
  ocr_modelo: "gpt-6-luna"
  tts_provider: "openai"
  tts_modelo: "gpt-4o-mini-tts"
  tts_voz: "coral"
  imagem_provider: "openai"
  imagem_modelo: "gpt-image-2.5-flare"
  imagem_tamanho: "1024x1536"
  imagem_qualidade: "low"

seguranca:
  marcador_ausente: "não localizado"
  envio_automatico: false
  revisao_obrigatoria: true
```

O fluxo atual seleciona **OpenAI** na configuração principal. Os experimentos A/B/C e B V2/V3/V4 usam o provedor configurado e registram evidências em pastas novas. `reasoning_effort: none` permite manter a temperatura comparável no modelo padrão; com raciocínio ativo, o cliente omite a temperatura incompatível. O limite é enviado como `max_completion_tokens` e `store` como `false`. O modo `--mock` é apenas uma simulação local.

Preencha somente `OPENAI_API_KEY` no `.env` para o padrão atual. `python -m src.main modelos --provider openai` consulta os modelos acessíveis pela conta, sem gerar conteúdo; a presença no catálogo não comprova sucesso em cada endpoint. Provedores antigos e alternativas locais continuam disponíveis: ao trocar de provedor, ajuste também modelo e voz correspondentes no YAML, sem presumir compatibilidade entre nomes. Não há fallback automático para outro serviço.

O TTS usa a integração Speech já existente com `gpt-4o-mini-tts`. A [documentação oficial](https://developers.openai.com/api/docs/guides/text-to-speech) informa descontinuação em **06/01/2027**; será necessária migração para Realtime. A gravação deve ser identificada como voz sintética, e sua geração exige aprovação humana da versão exata da minuta.

### Custos dos modelos e serviços de IA

A tabela abaixo é histórica e não estima gastos dos modelos OpenAI atuais. A chamada OpenAI de validação retornou tokens e latência, sem custo monetário; esse custo permanece `não localizado`.

Preços públicos consultados em **18/10/2026**, em dólares dos Estados Unidos. A tabela usa a modalidade padrão/síncrona paga. Camadas gratuitas, impostos, câmbio, franquias, limites e preços futuros podem alterar o valor efetivamente cobrado; confirme as páginas oficiais antes de executar.

| Uso no projeto | Provedor e modelo | Entrada | Saída | Unidade real de cobrança |
|---|---|---:|---:|---|
| Minutas e experimento atual | Gemini `gemini-3.1-flash-lite` | US$ 0,25 por 1 milhão de tokens de texto/imagem/vídeo; áudio: US$ 0,50 | US$ 1,50 por 1 milhão de tokens | Tokens; há camada gratuita sujeita às condições do provedor |
| OCR/visão remoto | Gemini `gemini-3.8-flash` | US$ 0,75 por 1 milhão de tokens | US$ 3,75 por 1 milhão de tokens | Preço introdutório válido até 31/12/2026; depois, US$ 1,50 de entrada e US$ 7,50 de saída |
| Síntese de voz | Gemini `gemini-3.8-flash-lite-tts` | US$ 0,50 por 1 milhão de tokens de texto | US$ 6,00 por 1 milhão de tokens de áudio | Até 31/12/2026; equivalente informado pelo provedor de US$ 0,0015 por 10 segundos de áudio |
| Transcrição de áudio | Groq `whisper-large-v3-turbo` | n/a | n/a | **US$ 0,04 por hora de áudio**, não por milhão de tokens |
| Imagem | Cloudflare `@cf/black-forest-labs/flux-1-schnell` | n/a | n/a | US$ 0,0000528 por bloco 512×512 e US$ 0,0001056 por etapa; com as 4 etapas configuradas, a parcela de etapas é US$ 0,0004224, além dos blocos |
| Experimento histórico | OpenRouter `nvidia/nemotron-3-super-120b-a12b:free` | US$ 0,00 por 1 milhão de tokens | US$ 0,00 por 1 milhão de tokens | Endpoint gratuito e sujeito a limites de uso |
| Alternativas locais | `faster-whisper`, Tesseract, eSpeak e Pillow | n/a | n/a | Sem tarifa de API por token; hardware, energia e operação não foram medidos |

Fontes oficiais: [preços da API Gemini](https://ai.google.dev/gemini-api/docs/pricing), [Gemini 3.8 Flash](https://ai.google.dev/gemini-api/docs/latest-model), [Groq Whisper Large V3 Turbo](https://console.groq.com/docs/model/whisper-large-v3-turbo), [Cloudflare Workers AI](https://developers.cloudflare.com/workers-ai/platform/pricing/), [Cloudflare FLUX.1 schnell](https://developers.cloudflare.com/workers-ai/models/flux-1-schnell) e [OpenRouter Nemotron gratuito](https://openrouter.ai/nvidia/nemotron-3-super-120b-a12b%3Afree/pricing).

Esses valores são tarifas públicas de referência, não custos medidos das execuções do projeto. Quando o provedor não informa o custo da chamada, o artefato deve registrar `não localizado` em vez de estimar um gasto.

Crie seu `.env` local a partir de `.env.example`. Preencha **somente as chaves dos provedores que for usar**. O arquivo `.env` está ignorado pelo Git e **nunca** deve ser enviado ao repositório.

---

## 🐍 Ambiente virtual e instalação

**Pré-requisitos:** Python 3.11+ e as ferramentas de sistema necessárias ao recurso escolhido. Para OCR de PDF, instale Tesseract (idioma português) e Poppler; para áudio local, podem ser necessários FFmpeg, eSpeak e/ou `faster-whisper`.

### Linux (Ubuntu)

```
git clone https://github.com/diegocbaleite/desafio-05-central-atendimento-ia.git
cd desafio-05-central-atendimento-ia
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-por poppler-utils ffmpeg espeak
cp .env.example .env
python -m src.main verificar
```

Para STT local, instale separadamente quando necessário:

```
python -m pip install faster-whisper
```

### Windows (PowerShell)

```
git clone https://github.com/diegocbaleite/desafio-05-central-atendimento-ia.git
cd desafio-05-central-atendimento-ia
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m src.main verificar
```

No Windows, configure no `PATH` as ferramentas externas instaladas que forem necessárias (Tesseract, Poppler, FFmpeg e eSpeak). A presença de uma chave em `.env` **não** comprova disponibilidade da API ou funcionamento de um modelo.

---

## ▶️ Execução da aplicação

Execute a partir da raiz do repositório:

```
# Verificar versões, ferramentas, provedores e envio automático
python -m src.main verificar

# Consultar modelos disponíveis na conta OpenAI (sem gerar conteúdo)
python -m src.main modelos --provider openai

# Demonstração local e determinística, sem chamadas externas de IA
python -m src.main --mock --caso T01 --decisoes dados/revisao/decisoes_demo.yaml

# Fluxo principal interativo (pode solicitar aprovação humana e usar APIs)
python -m src.main

# Experimento A/B/C (usa API quando não informado --mock)
python -m src.main experimento

# Áudio: transcrição local com modelo opcional
python -m src.main audio dados/originais/entrada_audio.mp3 --provider local

# OCR tradicional local no PDF digitalizado
python -m src.main ocr dados/originais/entrada_pdf-imagem.pdf --provider local

# Peça visual programática (não é imagem gerada por IA)
python -m src.main arte --provider local --referencia dados/originais/brasao.png
```

O lote `--mock` sem `--caso` valida também `A01` e `I01`. As referências independentes conferidas já estão declaradas no catálogo e disponíveis em `resultados/multimodal/referencias/`, permitindo a demonstração completa do lote. Elas são evidências humanas separadas das saídas de STT/OCR e dos gabaritos.

**Serviços remotos — somente com conteúdo fictício e credenciais autorizadas:**

```
python -m src.main audio dados/originais/entrada_audio.mp3 --provider openai
python -m src.main ocr dados/originais/entrada_pdf-imagem.pdf --provider openai
python -m src.main arte --provider openai --referencia dados/originais/brasao.png

# Uma chamada de texto com fixture fictícia; grava saída pendente e não pede aprovação
python -m src.experimento_b_v2_real --versao v4 --caso X02
```

**TTS:** requer arquivo real da minuta aprovada e JSON de revisão humana com hash correspondente; não basta uma decisão de `--mock`.

```
python -m src.main voz <caminho_da_minuta_aprovada.md> --revisao <caminho_da_revisao.json>
```

O sistema armazena as evidências em `resultados/`. Antes da entrega, a equipe deve copiar somente os artefatos necessários para um pacote higienizado, revisar dados e logs e registrar o pacote junto ao relatório técnico. As pastas locais não constituem, por si só, evidência versionada. Chamadas remotas podem consumir cotas ou falhar. **Nenhum comando envia a minuta ao cidadão.**

---

## 🧪 Testes automatizados

O projeto utiliza a biblioteca padrão **unittest**. Execute:

```
python -m unittest discover -s testes -t .
python -m src.main verificar
```

**Último resultado verificado localmente em 28/10/2026 (Windows, Python 3.14.6):**

```
Ran 130 tests
OK
```

**Limitação:** a suíte automatizada aprovada não substitui validação de rede, testes manuais de áudio/imagem e homologação humana.

---

## 🔀 Controle de versão e branches

O repositório organiza o trabalho dos três integrantes em branches de funcionalidade:

- `main`: versão integrada do projeto.
- `feature/estudante-1-prompts-avaliacao-documentacao`: frente do Diego.
- `feature/estudante-2-api-seguranca-texto-auditoria`: frente do Ayron.
- `feature/estudante-3-audio-ocr-imagem-acessibilidade`: frente do Guilherme.

O Pull Request da Parte 1 foi mesclado à `main` em 18/10/2026. Novas alterações devem passar por revisão e testes antes da integração, preservando o código dos demais integrantes.

---

## 🤖 Uso de ferramentas de IA durante o desenvolvimento

Foi utilizado **ChatGPT** como apoio à interpretação do enunciado, organização do projeto, desenvolvimento e revisão de prompts/código, análise de erros, planejamento de testes, avaliação assistida e documentação. O histórico também registra o uso de um assistente de codificação integrado ao VS Code; versão/modelo não identificados no repositório.

**Exemplos de temas trabalhados com auxílio de IA:**

- Auditoria do código frente aos requisitos RF01–RF13 do enunciado.
- Revisão de prompts para evitar invenção de prazos e procedimentos.
- Organização de resultados brutos, resultados revisados e hashes de áudio/OCR.
- Testes de injeção de prompt e isolamento de conteúdo externo.
- Registro separado de notas humanas confirmadas, sem alterar respostas originais.

**Participação da equipe:** os estudantes executaram, avaliaram e registraram resultados. Sugestões da IA foram aceitas, modificadas ou rejeitadas conforme a revisão. **Notas humanas só foram preenchidas após confirmação expressa do responsável**; saídas `mock` não são respostas reais de modelos externos.

Mais informações: [uso_da_ia.md](documentacao/uso_da_ia.md).

---

## 📦 Entregáveis e preparação da apresentação

O enunciado do Desafio Prático 1 exige um **arquivo compactado** com código, configuração, entradas fictícias/gabaritos, prompts e matriz comparativa, resultados de texto/áudio/OCR/imagem, relatório técnico e registro do uso de IA. Também exige **apresentação de até 12 minutos** com demonstração e perguntas.

**Validações documentadas:**

- Código das três frentes integrado à `main`.
- Testes automatizados da última execução local aprovados (114/114).
- Cinco casos atuais integrados ao catálogo, aos gabaritos e ao YAML de demonstração.
- Comparação A/B/C atual executada e avaliada com `T01`, `X01` e `X02`, sem reutilizar notas de outros conjuntos de dados.
- Avaliação RF13 atual registrada com critérios, justificativas e taxa de aprovação direta.
- STT, OCR, TTS e imagem por IA executados com serviços reais; referências, métricas, correções e revisões registradas.
- Checklist de privacidade e dados fictícios concluído; logs, permissões e proveniência registrados. A inspeção do pacote final deve ser repetida antes da publicação.

Registro consolidado: [validações do catálogo atual](documentacao/registro_validacoes_catalogo_atual.md).

Não confundir **implementação concluída**, **teste automatizado aprovado**, **validação humana de conteúdo** e **homologação institucional**: são estados diferentes.

---

## 👨‍💻 Autores

- **Diego Assunção Leite** — Estudante 1
- **Ayron Brhenno Silva Figueiredo** — Estudante 2
- **Guilherme da Silva Lessa** — Estudante 3

**FIC_DEV — SECITECI / Escola Técnica Estadual de Cuiabá — 2026**
