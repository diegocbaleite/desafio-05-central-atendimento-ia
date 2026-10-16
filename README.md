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
| Esqueleto Python, API configurável, testes, extração, JSON Schema, rastreabilidade | Implementado; executar testes no ambiente de apresentação |
| C01/C05/C06: textos fictícios e gabaritos | Incluídos |
| C02: áudio com ruído e STT | Há roteiro/transcrição de referência; **gravação/execução real devem ser comprovadas** |
| C03: formulário e OCR | Há transcrição fictícia de referência; **imagem e execução do OCR devem ser comprovadas** |
| C04: timbre compatível com GOV.MT | **Produzir/inspecionar timbre fictício**, sem uso indevido de símbolo oficial |
| Experimento A/B/C com modelo real | Código preparado; **pendente medição real e avaliação humana** |
| Peça visual RF10 | Arte local por código não é arte produzida por IA; **execução com gerador de IA pendente se exigida** |
| Decisão humana | CLI interativa disponível; decisões em YAML são **simulação**, não assinatura de servidor |
| Relatório de custos e aprovação | Modelos em `documentacao/`; preencher apenas com dados medidos |

**Não confundir `mock` com resultado de IA real.** Não declare testes passando nem áudio/arte gerados por IA sem evidência da execução.

## Preparar o ambiente — Ubuntu
```bash
git clone https://github.com/diegocbaleite/desafio-05-central-atendimento-ia.git
cd desafio-05-central-atendimento-ia
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
sudo apt update && sudo apt install tesseract-ocr tesseract-ocr-por espeak
cp .env.example .env
python -m src.main verificar
```
No Windows, use `.venv\Scripts\activate` e instale Tesseract com idioma português. As chaves de API ficam **somente no `.env`**, que está no `.gitignore`. O modo de demonstração é offline.

## Comandos
```bash
python -m unittest discover -s testes -t .
python -m src.main verificar
python -m src.main --mock --caso C01
python -m src.main --mock --decisoes dados/revisao/decisoes_demo.yaml
python -m src.main experimento --mock
python -m src.main experimento
python -m src.main imagem
python -m src.main arquivos
```
`--decisoes` reproduz **decisões fictícias e prefixadas**, não validação humana. Sem a opção, a CLI pergunta a decisão no terminal.

Para usar LLM real: ajuste `llm.provider` de `mock` para `groq`, `openai` ou `gemini` em `config/config.yaml`, ajuste `llm.modelo` e a chave correspondente no `.env`. Valide disponibilidade/compatibilidade do modelo antes da aula. A aplicação nunca deve imprimir a chave. Resultados ficam em `resultados/execucoes/<id>/`, ignorados pelo git por privacidade.

Para extrair arquivos fictícios da pasta `arquivos/`, configure as chaves Gemini e OpenRouter e execute `python -m src.main arquivos`. PDF e áudio são enviados ao Gemini para leitura; texto transcrito e texto simples seguem minimizados (CPF, e-mail e telefone substituídos) ao OpenRouter para estruturar o JSON. Arquivos são limitados a 14 MiB e não podem sair da pasta de entrada autorizada. A transcrição é salva localmente e a auditoria registra provedor, modelo, latência, tokens disponíveis, hash e falhas, sem guardar prompts nem credenciais. Saídas ficam em `resultados/arquivos_fornecidos/` e são ignoradas pelo git. **Não use documentos, vozes ou dados reais:** a leitura remota de PDF/áudio ainda transmite o original ao Gemini; para dados reais, substitua por OCR/STT local e faça avaliação de privacidade antes do uso.

# Requisitos Funcionais — RF01 a RF13
| RF | Como demonstrar | Evidência |
|---|---|---|
| RF01 Configuração | `verificar` | README, versões, `.env.example`, config |
| RF02 Engenharia de prompts | `experimento` A/B/C em condições controladas | `prompts/experimento/`, matriz |
| RF03 Segurança | injeção de C03 e C05 não deve obedecer ordens | `src/seguranca.py`, testes |
| RF04 API | simular falhas, realizar chamada real | `src/cliente.py`, auditoria |
| RF05 JSON | C01 e C06 (lacunas) | `src/extracao.py`, JSON Schema |
| RF06 STT | áudio C02 gravado com ruído | transcrição bruta/revisada, WER |
| RF07 TTS | somente para minuta aprovada | áudio salvo e roteiro |
| RF08 OCR | imagem C03 digitalizada | OCR bruto/revisado, CER |
| RF09 Minuta | campos com evidência e sem inventar prazo | `src/minuta.py` |
| RF10 Imagem | peça visual, prompt completo e proveniência | nota de geração e imagem |
| RF11 Auditoria | rastrear caso, versão de prompt, modelo, duração | JSONL |
| RF12 LGPD | uso fictício e minimização | `documentacao/lgpd.md` |
| RF13 Avaliação | grade de cinco critérios, caso aprovado e rejeitado | `documentacao/protocolo_avaliacao.md` |

# Estrutura do projeto
```text
config/         parâmetros não sensíveis
dados/originais/  entradas fictícias intocadas pelo processamento
dados/gabaritos/  resultados esperados fixados antes da execução
dados/revisao/    simulações de decisão (rotuladas)
prompts/       extração, minuta, A/B/C, prompt de imagem
src/           código, cliente HTTP, OCR/STT/TTS, regras, auditoria, CLI
testes/        testes automatizados e preparação controlada dos dados
resultados/     saídas de execução (não versionar dados/segredos reais)
documentacao/  arquitetura, LGPD, avaliação, 12 horas, relatório, uso de IA
```

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

Ao usar `--mock`, não há medição de desempenho de modelos generativos. Para uma demonstração multimodal real, configure as credenciais e gere os arquivos fictícios de áudio e imagem conforme o roteiro de preparação.

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
python -m testes.gerar_dados_ficticios
python -m src.main --mock --decisoes dados/revisao/decisoes_demo.yaml
```

Registrar separadamente as **execuções com IA real**, a matriz A/B/C, o WER/CER, as avaliações de Diego, Ayron e Guilherme e as evidências da peça visual antes de declarar o trabalho finalizado.

# Autores

**Diego · Ayron · Guilherme**  
FIC_DEV — SECITECI / Escola Técnica Estadual de Cuiabá — 2026
