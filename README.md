# Central Inteligente de Atendimento e Comunicação Institucional

**Desafio Prático 1 — Inteligência Artificial Generativa (FIC_DEV, Aulas 01 a 07)**  
**Equipe:** Diego Assunção Leite · Ayron · Guilherme  
**Instituição:** SECITECI — Escola Técnica Estadual de Cuiabá | **Versão:** 1.0 (2026)  

> **Protótipo educacional, sem atendimento real.** Não há envio automático para cidadão. Os documentos são fictícios e toda aprovação tem que passar por uma pessoa responsável.

## Objetivo
Receber solicitações fictícias em **texto, áudio e imagem**, transcrever ou aplicar OCR, extrair campos e classificá-los em JSON, produzir **minutas** fundamentadas apenas nas fontes disponíveis, gerar versão acessível em áudio e peça visual identificada quanto à proveniência. Registrar erros, modelos, custos disponíveis e decisões humanas.

## Integrantes e atribuições sugeridas
| Integrante | Frente inicial |
|---|---|
| Diego | Engenharia de Prompts, métricas, revisão dos gabaritos e relatório |
| Ayron | Integração Python/API, segurança, tratamento de erros e auditoria |
| Guilherme | STT/TTS, OCR, peça visual, testes e acessibilidade |

A distribuição é sugerida: **todos devem compreender o projeto inteiro**.

## Estado verificável
| Componente | Status |
|---|---|
| Esqueleto Python, API configurável, testes, extração, JSON Schema, rastreabilidade | Implementado; 65 testes unitários passam localmente (Windows, Python 3.14) — repetir no ambiente de entrega |
| T01/A01/I01: material fornecido (texto, áudio, PDF digitalizado) com gabaritos prévios | Incluídos em `dados/originais/` e `dados/gabaritos/`; conferência humana dos gabaritos pendente |
| X01/X02: entradas sintéticas de injeção e de campos ausentes | Em `testes/fixtures/` (listadas em `casos.yaml`) |
| A01: áudio e STT | STT local (faster-whisper) e Groq implementados em `src/guilherme_multimodal.py`; evidências da equipe em `resultados/guilherme/`; **WER/CER de referência derivada do próprio modelo não é avaliação independente** |
| I01: PDF digitalizado e OCR | OCR local (Tesseract) integrado ao fluxo principal; o OCR **não reconhece os campos manuscritos** do PDF, portanto I01 exige conferência humana |
| Imagem institucional (timbre/GOV.MT) | `dados/originais/brasao.png` é citado na minuta; **compatibilidade com documentos GOV.MT não validada oficialmente** |
| Experimento A/B/C com modelo real | Matriz local registra **9/9 respostas**; **avaliação humana e custo por chamada pendentes** |
| Peça visual RF10 | CLI aceita gerador OpenAI configurável; configuração atual é local e **geração por IA não demonstrada** |
| Decisão humana | CLI interativa exige **responsável e justificativa**, registra hash/versão da minuta e permite nova geração; decisões em YAML são **simulação**, não assinatura de servidor |
| Relatório de custos e aprovação | Modelos em `documentacao/`; preencher apenas com dados medidos |

Estados por requisito (planejado, implementado, testado com simulação, validado com serviço real, validado por pessoa): [documentacao/matriz_requisitos.md](documentacao/matriz_requisitos.md).

**Não confundir `mock` com resultado de IA real.** Não declare testes passando nem áudio/arte gerados por IA sem evidência da execução.

## Preparar o ambiente
Requer **Python 3.11 ou superior** (testado com 3.14.6 no Windows; o CI usa 3.12). Dependências Python em `requirements.txt` (`requests`, `PyYAML`, `jsonschema`, `python-dotenv`, `pillow`, `pytesseract`); `faster-whisper` é opcional para STT local. Ferramentas de sistema: Tesseract com idioma `por` (OCR), Poppler/`pdftoppm` (OCR de PDF), `espeak` (TTS offline) e FFmpeg/`ffprobe` (duração do áudio; se ausente, a duração é registrada como "não medida").

### Ubuntu
```bash
git clone https://github.com/diegocbaleite/desafio-05-central-atendimento-ia.git
cd desafio-05-central-atendimento-ia
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
sudo apt update && sudo apt install tesseract-ocr tesseract-ocr-por poppler-utils espeak ffmpeg
cp .env.example .env
python -m src.main verificar
```

### Windows (PowerShell)
```powershell
git clone https://github.com/diegocbaleite/desafio-05-central-atendimento-ia.git
cd desafio-05-central-atendimento-ia
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m src.main verificar
```
No Windows, instale Tesseract (com o idioma português) e Poppler e coloque-os no `PATH` (por exemplo com `winget`); `espeak` e FFmpeg são opcionais. O comando `verificar` mostra as versões de Python e das bibliotecas, quais ferramentas de sistema foram encontradas e quais chaves estão configuradas (sem exibi-las).

As chaves de API ficam **somente no `.env`**, que está no `.gitignore`; `.env.example` lista as variáveis usadas (`OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `GROQ_API_KEY`, `GEMINI_API_KEY`). Caminhos, modelos e parâmetros não sensíveis ficam em `config/config.yaml`. O modo de demonstração (`--mock`) não usa APIs de modelo.

## Comandos
```bash
python -m unittest discover -s testes -t .
python -m src.main verificar
python -m src.main --mock --caso T01
python -m src.main --mock --decisoes dados/revisao/decisoes_demo.yaml
python -m src.main experimento --mock
python -m src.main experimento
python -m src.main imagem
python -m src.main arquivos --autorizar-api   # envia arquivos a provedores externos: só com dados fictícios
```
O comando sem argumentos (`python -m src.main`) processa os casos de `dados/originais/casos.yaml`. O código de saída é **diferente de zero quando algum caso falha** (útil em automação). Ao final, o resumo JSON traz a **taxa de aprovação direta** com denominador explícito: só entram casos com decisão humana real; decisões simuladas (`--mock` ou `--decisoes`) ficam fora do cálculo.

### Revisão humana
Sem `--decisoes`, a CLI pede, para cada minuta, a decisão (`aprovar`, `rejeitar`, `corrigir` ou `nova`), o **responsável** e a **justificativa**; nada é preenchido pelo código. A auditoria registra revisor, justificativa, data, versão e SHA-256 da minuta. `nova` gera outra versão (`minuta_v2.md`…), que precisa ser revisada de novo; uma aprovação vale somente para a versão aprovada (`minuta_aprovada.md` + `revisao.json`, no formato aceito por `python -m src.guilherme_multimodal voz`). Para casos de áudio e imagem, a CLI exige antes da minuta a **conferência de protocolo, data e solicitante com o original**. `--decisoes` reproduz **decisões fictícias e prefixadas**, não validação humana: são registradas como simuladas e não criam minuta aprovada nem acionam TTS. A opção `imagem --mock` força a composição local; sem `--mock`, o comando segue `multimodal.imagem_provider` (local por padrão, OpenAI somente se configurado).

### Extração por provedores externos (`arquivos`)
O comando `python -m src.main arquivos` **é bloqueado sem `--autorizar-api`**, porque envia PDF e áudio originais ao Gemini e o texto minimizado ao OpenRouter. Use a opção somente após confirmar que todos os arquivos da pasta `dados/originais/` (configurável em `extracao_llm.pasta_entrada`) são fictícios. Com a autorização, a CLI informa que está no fluxo de extração multimodal e mostra as etapas por arquivo: validação da entrada, leitura local ou OCR/transcrição com Gemini, estruturação dos campos pelo provedor configurado, validação de evidências e JSON Schema e gravação/auditoria.

Para usar LLM real no pipeline, configure `llm.provider` como `openrouter`, `groq`, `openai` ou `gemini`, selecione um modelo disponível e configure a variável correspondente no `.env`. A configuração inicial usa OpenRouter. Valide disponibilidade/compatibilidade do modelo antes da aula. A aplicação nunca deve imprimir a chave. Resultados ficam em `resultados/execucoes/<id>/`, ignorados pelo git por privacidade.

Na extração por provedores, PDF e áudio são enviados ao Gemini para leitura; texto transcrito e texto simples seguem minimizados (CPF, e-mail e telefone substituídos) ao OpenRouter para estruturar o JSON. Arquivos são limitados a 14 MiB e não podem sair da pasta de entrada autorizada. A transcrição é salva localmente e a auditoria registra provedor, modelo, latência, tokens disponíveis, hash e falhas, sem guardar prompts nem credenciais. Saídas ficam em `resultados/arquivos_fornecidos/` e são ignoradas pelo git. **Não use documentos, vozes ou dados reais:** a leitura remota de PDF/áudio transmite o original ao Gemini; para dados reais, substitua por OCR/STT local e faça avaliação de privacidade antes do uso.

# Requisitos Funcionais — RF01 a RF13
| RF | Como demonstrar | Evidência |
|---|---|---|
| RF01 Configuração | `verificar` | README, versões, `.env.example`, config |
| RF02 Engenharia de prompts | `experimento` A/B/C em condições controladas | `prompts/experimento/`, matriz |
| RF03 Segurança | injeção em X01 não deve ser obedecida | `src/seguranca.py`, `prompts/sistema_minuta.md`, testes |
| RF04 API | simular falhas, realizar chamada real | `src/cliente.py`, auditoria |
| RF05 JSON | T01 (completo) e X02 (lacunas) | `src/extracao.py`, JSON Schema |
| RF06 STT | áudio A01 | transcrição bruta/revisada, WER (`src/guilherme_multimodal.py`) |
| RF07 TTS | somente para minuta aprovada | áudio salvo e roteiro |
| RF08 OCR | PDF digitalizado I01 | OCR bruto/revisado, CER (`src/guilherme_multimodal.py`, `src/multimodal.py`) |
| RF09 Minuta | campos com evidência, timbre citado e sem inventar prazo | `src/minuta.py` |
| RF10 Imagem | peça visual, prompt completo e proveniência | nota de geração e imagem |
| RF11 Auditoria | rastrear caso, versão do prompt (hash), modelo, duração, decisão humana | JSONL |
| RF12 LGPD | uso fictício e minimização | `documentacao/lgpd.md` |
| RF13 Avaliação | gabarito × obtido com gravidade, taxa de aprovação, caso aprovado e rejeitado | `src/avaliacao.py`, `documentacao/protocolo_avaliacao.md` |

# Estrutura do projeto
```text
config/           parâmetros não sensíveis (config.yaml)
dados/originais/  entradas fornecidas pela equipe + casos.yaml, intocadas pelo processamento
dados/gabaritos/  resultados esperados fixados antes da execução
dados/revisao/    simulações de decisão (rotuladas)
prompts/          extração, minuta, A/B/C, prompt de imagem
src/              código, cliente HTTP, OCR/STT/TTS, regras, auditoria, CLI
testes/           testes automatizados; fixtures/ guarda entradas sintéticas de teste
resultados/       saídas de execução (não versionar dados/segredos reais)
documentacao/     arquitetura, LGPD, avaliação, 12 horas, relatório, uso de IA, matriz de requisitos
```
Equivalência com a estrutura sugerida no enunciado: `config.json` → `config/config.yaml`; `llm_client.py` → `src/cliente.py`; `prompts.py` → `prompts/*.md` (carregados e com hash registrado); `audio.py`/`vision.py` → `src/multimodal.py` e `src/guilherme_multimodal.py`; `image_generation.py` → `src/arte_ia.py`; `audit.py` → `src/auditoria.py`; `dados/processados/` e `resultados/{minutas,audios,imagens,logs}` → `resultados/execucoes/<id>/<caso>/` (extração, minutas versionadas, `revisao.json`, `auditoria.jsonl`) e `resultados/guilherme/` (STT, OCR, TTS, arte).

# Segurança, custos e limitações
- A entrada externa é dado **não confiável**. A detecção de injeção por expressões regulares não é completa.
- Campos ausentes ou sem valor sustentado pela própria evidência tornam-se **`não localizado`**. Valores críticos ainda precisam ser conferidos na fonte por uma pessoa; texto gerado pelo modelo pode alucinar.
- **Jamais** usar nomes, CPFs, vozes ou fotografias de pessoas reais nas demonstrações. Nunca publicar `.env`.
- Sem valor oficial conferido de preço, custo é **indisponível**: não inventar tarifas. Registre tokens/latência reais quando a API fornecer.
- A composição local com Pillow é **gráfica programática**, e não imagem criada por IA. Diferencie no relatório.
- Este repositório é **protótipo pedagógico**, não sistema pronto para produção, integração com GOV.MT ou envio de atos oficiais.

# Documentação e entregáveis
Consulte `documentacao/plano_projeto.md`, `lgpd.md`, `protocolo_avaliacao.md`, `roteiro_12h.md`, `relatorio_tecnico.md` e `uso_da_ia.md`. Gere o ZIP excluindo `.env`, ambientes virtuais, credenciais e arquivos pessoais reais. Todos os integrantes devem revisar o resultado antes de entregar.

---

# Execução do pipeline

O processo percorre validação da entrada, reconhecimento de texto/voz quando pertinente, extração com evidências, classificação, minuta de resposta, conferência, aprovação ou rejeição, geração de acessibilidade e auditoria. **Nenhuma etapa envia a minuta ao cidadão.**

Ao usar `--mock`, não há medição de desempenho de modelos generativos: a minuta é determinística e, para o áudio A01, é lida a transcrição de referência indicada em `casos.yaml` (texto conferido por pessoa, **não** transcrição do modelo); o OCR de PDF/imagem continua sendo real e local. Para uma demonstração multimodal real, configure as credenciais e use `python -m src.guilherme_multimodal` (STT, OCR, voz e arte) conforme `documentacao/parte3_guilherme.md`.

# Testes automatizados

```bash
python -m unittest discover -s testes -t .
```

O projeto inclui testes básicos, verificações de segurança e testes de insumos fictícios. **A aprovação do conjunto completo precisa ser confirmada no ambiente local ou no GitHub Actions**; a existência dos testes não prova que todos passaram.

# Controle de versão

A `main` contém a versão integrada em construção. Para contribuições da equipe, sugerem-se branches:
- `feature/diego-api-seguranca-auditoria`
- `feature/ayron-prompts-avaliacao`
- `feature/guilherme-audio-ocr-imagens`

Os nomes acima são uma proposta, **não** branches que já tenham sido criadas.

# Checklist final de validação

```bash
git status -sb
python -m unittest discover -s testes -t .
python -m src.main verificar
python -m src.main --mock --decisoes dados/revisao/decisoes_demo.yaml
```

`dados/revisao/decisoes_demo.yaml` define as decisões simuladas por caso (valores em branco fazem a CLI pedir a decisão no terminal). O script `testes/gerar_dados_ficticios.py` é legado: gera ativos sintéticos adicionais que **não** fazem parte de `casos.yaml`.

Registrar separadamente as **execuções com IA real**, a matriz A/B/C, o WER/CER, as avaliações de Diego, Ayron e Guilherme e as evidências da peça visual antes de declarar o trabalho finalizado.

# Autores

**Diego · Ayron · Guilherme**  
FIC_DEV — SECITECI / Escola Técnica Estadual de Cuiabá — 2026
