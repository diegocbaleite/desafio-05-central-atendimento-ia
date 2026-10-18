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
| Esqueleto Python, API configurável, testes, extração, JSON Schema, rastreabilidade | Implementado; **75 testes unitários passaram** em 18/10/2026 (Windows, Python 3.14.6) |
| T01/A01/I01: material fornecido (texto, áudio, PDF digitalizado) com gabaritos prévios | Incluídos em `dados/originais/` e `dados/gabaritos/`; conferência humana dos gabaritos pendente |
| X01/X02: entradas sintéticas de injeção e de campos ausentes | Em `testes/fixtures/` (listadas em `casos.yaml`) |
| A01: áudio e STT | STT local (faster-whisper) e Groq implementados em `src/audio.py`; o pipeline guarda a transcrição bruta e metadados no mesmo caso da execução; **WER/CER de referência derivada do próprio modelo não é avaliação independente** |
| I01: PDF digitalizado e OCR | OCR local (Tesseract) integrado ao fluxo principal; quando o OCR reconhece os rótulos `CÓDIGO`, `NOME` e `DATA MATRÍCULA`, as regras extraem esses campos. A leitura manuscrita pode falhar e exige conferência humana no original |
| Imagem institucional (timbre/GOV.MT) | `dados/originais/brasao.png` é citado na minuta; **compatibilidade com documentos GOV.MT não validada oficialmente** |
| Experimento A/B/C com modelo real | Matriz local registra **9/9 respostas**; **avaliação humana e custo por chamada pendentes** |
| Peça visual RF10 | Integração Cloudflare Workers AI / `@cf/black-forest-labs/flux-1-schnell` implementada e testada só com simulação; a cota grátis do Workers AI é de 10.000 neurons por dia; **nenhuma imagem real foi gerada ainda** |
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

As chaves de API ficam **somente no `.env`**, que está no `.gitignore`; `.env.example` lista `OPENROUTER_API_KEY`, `GROQ_API_KEY`, `GEMINI_API_KEY`, `CLOUDFLARE_API_KEY` e `CLOUDFLARE_ACCOUNT_ID`, todas vazias. `CLOUDFLARE_API_KEY` deve conter um API Token Cloudflare com permissão para Workers AI (não a Global API Key). Caminhos, modelos e parâmetros não sensíveis ficam em `config/config.yaml`. O modo de demonstração (`--mock`) não usa APIs de modelo.

## Comandos
```bash
python -m src.main #comando padrão
python -m unittest discover -s testes -t .
python -m src.main verificar
python -m src.main --mock --caso T01
python -m src.main --mock --decisoes dados/revisao/decisoes_demo.yaml
python -m src.main experimento
python -m src.main ocr dados/originais/entrada_pdf-imagem.pdf
python -m src.main audio dados/originais/entrada_audio.mp3 --provider local
python -m src.main audio dados/originais/entrada_audio.mp3 --provider groq
python -m src.main voz resultados/execucoes/<id>/<caso>/minuta_aprovada.md --revisao resultados/execucoes/<id>/<caso>/revisao.json
python -m src.main arte --referencia dados/originais/brasao.png
python -m src.main arte --provider cloudflare # FLUX.1 schnell; consome a cota diária gratuita do Workers AI
```
O comando sem argumentos (`python -m src.main`) processa os casos de `dados/originais/casos.yaml`; `audio`, `ocr`, `voz` e `arte` gravam evidências em `resultados/multimodal/<tipo>_<data>_<id>/` (texto bruto, metadados, hash e revisão pendente). No pipeline principal, STT/OCR brutos e seus metadados também ficam em `resultados/execucoes/<id>/<caso>/`, vinculados à mesma execução. O código de saída é **diferente de zero quando algum caso falha** (útil em automação). Ao final, o resumo JSON traz a **taxa de aprovação direta** com denominador explícito: só entram casos com decisão humana real; decisões simuladas (`--mock` ou `--decisoes`) ficam fora do cálculo.

### Extração antes da minuta
Os campos são extraídos localmente por regras explícitas em `src/extracao.py`; o LLM **não** extrai nem corrige esses campos. Ele recebe apenas `assunto` e `pedido` para redigir o corpo, depois que a extração é validada e salva em `extracao.json`. No formulário I01, `CÓDIGO` é usado como protocolo, `NOME` como solicitante e `DATA MATRÍCULA` como data da solicitação; o extrator só preenche esses campos se o OCR conseguir ler os rótulos e valores, e a conferência humana no original continua obrigatória. Para texto sem rótulos, o extrator tenta identificar o assunto nos pedidos reconhecidos e reúne pedidos introduzidos por “solicito”, “peço” ou “quero pedir”. O protocolo falado aceita separadores adicionais entre dígitos e números decimais como `1.200` não encerram o pedido. Datas ditas por extenso em português são normalizadas, mas continuam sujeitas à conferência: uma data sem rótulo tem confiança média e datas de nascimento não são tratadas como data da solicitação. Antes de avaliar a minuta, confira o `extracao.json`; para exercitar o fluxo sem chamar APIs, use `python -m src.main --mock --caso T01`.

### Revisão humana
Sem `--decisoes`, A CLI pede, para cada minuta, a decisão (`aprovar`, `rejeitar`, `corrigir` ou `nova`), o **responsável** e a **justificativa**; nada é preenchido pelo código. A auditoria registra revisor, justificativa, data, versão e SHA-256 da minuta. `nova` gera outra versão (`minuta_v2.md`…), que precisa ser revisada de novo; uma aprovação vale somente para a versão aprovada (`minuta_aprovada.md` + `revisao.json`, no formato aceito por `python -m src.main voz`). Para casos de áudio e imagem, a CLI exige antes da minuta a **conferência individual de protocolo, data e solicitante com o original**: cada valor pode ser confirmado ou corrigido; `não localizado` exige confirmação explícita. Correções ficam em `conferencia_campos_criticos.json` e `extracao_revisada.json`, sem sobrescrever a extração bruta. `--decisoes` reproduz **decisões fictícias e prefixadas**, não validação humana: são registradas como simuladas e não criam minuta aprovada nem acionam TTS. O comando `arte` usa Pillow local por padrão; `--provider cloudflare` seleciona a geração de imagem pelo Workers AI (`@cf/black-forest-labs/flux-1-schnell`; requer `CLOUDFLARE_API_KEY` e `CLOUDFLARE_ACCOUNT_ID` no `.env`). O plano gratuito inclui até 10.000 neurons por dia; acima da cota, as chamadas podem falhar no Workers Free ou gerar cobrança conforme o plano. A API não é usada com `--mock`.

### Envio a provedores externos
O modo `--mock` não chama APIs. Fora dele, o envio de dados depende dos provedores selecionados no comando ou configurados em `config/config.yaml`; no padrão atual, `multimodal.stt_provider` é `groq`, então o fluxo principal envia o áudio original ao Groq. Para manter o STT local, configure `local` e instale `faster-whisper`. OCR (Tesseract) e eSpeak funcionam offline; TTS e imagem também usam seus provedores configurados. Na geração da minuta com LLM real, apenas `assunto` e `pedido` seguem ao provedor, com CPF, e-mail e telefone substituídos por marcadores. Use somente dados fictícios; não envie os arquivos de `dados/originais/` a serviços externos sem confirmar que não contêm dados pessoais reais.
Para usar LLM real no pipeline, configure `llm.provider` como `openrouter`, `groq` ou `gemini`, selecione um modelo disponível e configure a variável correspondente no `.env`. A configuração inicial usa OpenRouter. Valide disponibilidade/compatibilidade e o nível de gratuidade do modelo antes da aula. A aplicação nunca deve imprimir a chave. Resultados ficam em `resultados/execucoes/<id>/`, ignorados pelo git por privacidade.

O cliente LLM registra temperatura, limite de tokens e timeout efetivos junto aos metadados da minuta. STT, TTS e geração de imagem não fazem retentativas automáticas; em caso de falha, confira o erro/quota antes de repetir manualmente a operação, pois uma nova chamada pode consumir limite do provedor.

# Requisitos Funcionais — RF01 a RF13
| RF | Como demonstrar | Evidência |
|---|---|---|
| RF01 Configuração | `verificar` | README, versões, `.env.example`, config |
| RF02 Engenharia de prompts | `experimento` A/B/C em condições controladas | `prompts/experimento/`, matriz |
| RF03 Segurança | injeção em X01 não deve ser obedecida | `src/seguranca.py`, `prompts/sistema_minuta.md`, testes |
| RF04 API | simular falhas, realizar chamada real | `src/cliente.py`, auditoria |
| RF05 JSON | T01 (completo) e X02 (lacunas) | `src/extracao.py`, JSON Schema |
| RF06 STT | áudio A01 | transcrição bruta/revisada, WER (`src/audio.py`, `src/avaliacao.py`) |
| RF07 TTS | somente para minuta aprovada | áudio salvo e roteiro |
| RF08 OCR | PDF digitalizado I01 | OCR bruto/revisado, CER (`src/visao.py`, `src/avaliacao.py`) |
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
Equivalência com a estrutura sugerida no enunciado: `config.json` → `config/config.yaml`; `llm_client.py` → `src/cliente.py`; `prompts.py` → `prompts/*.md` (carregados e com hash registrado); `audio.py`/`vision.py` → `src/audio.py` (STT e TTS) e `src/visao.py` (OCR); `image_generation.py` → `src/imagem.py`; `audit.py` → `src/auditoria.py`; `dados/processados/` e `resultados/{minutas,audios,imagens,logs}` → `resultados/execucoes/<id>/<caso>/` (extração, minutas versionadas, `revisao.json`, `auditoria.jsonl`) e `resultados/multimodal/` (STT, OCR, TTS, arte).

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

Ao usar `--mock`, não há medição de desempenho de modelos generativos: a minuta é determinística e, para o áudio A01, é lida a transcrição de referência indicada em `casos.yaml` (texto conferido por pessoa, **não** transcrição do modelo); o OCR de PDF/imagem continua sendo real e local. Para uma demonstração multimodal real, configure as credenciais e use `python -m src.main audio|ocr|voz|arte` conforme `documentacao/parte3_guilherme.md`.

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
python -m unittest discover -s testes -t .
python -m src.main verificar
python -m src.main --mock
```

`dados/revisao/decisoes_demo.yaml` define as decisões simuladas por caso (valores em branco fazem a CLI pedir a decisão no terminal). Os casos de execução e seus gabaritos ficam em `dados/originais/casos.yaml` e `dados/gabaritos/`; entradas sintéticas auxiliares usadas somente nos testes ficam em `testes/fixtures/`.

Registrar separadamente as **execuções com IA real**, a matriz A/B/C, o WER/CER, as avaliações de Diego, Ayron e Guilherme e as evidências da peça visual antes de declarar o trabalho finalizado.

# Autores

**Diego · Ayron · Guilherme**  
FIC_DEV — SECITECI / Escola Técnica Estadual de Cuiabá — 2026
