# Relatório de auditoria técnica: Central Inteligente de Atendimento (Desafio 05)

Data do registro: 2026-10-16.

**Método.** Leitura de todo o código de `src/`, da configuração, da CI, dos `.md`, dos prompts, dos gabaritos, dos dados de entrada, dos testes e do gerador de dados. O PDF do Desafio Prático 1 (RF01-RF13) foi usado como referência. O `roteiro_12h.md` foi tratado como cronograma e seu conteúdo oral foi ignorado.

**Limites da análise.**
- Não foram executados testes nem o pipeline. Nada abaixo afirma que os testes passam ou que houve execução real.
- A varredura de segredos usou apenas os padrões `sk-`, `api_key=`, `gsk_` e `AIza`.
- A existência das branches citadas em `divisao_equipe.md` não foi verificada.
- A correção do regex de `solicitante` (item 11 da seção 4) é hipótese, não verificada por execução.

**Efeito colateral a informar.** Ao checar uma biblioteca Python durante a auditoria, o gerenciador de Python do Windows instalou o Python 3.15 e criou a pasta `Python/` na raiz do repositório. Ela aparece como não rastreada no `git status`, e nenhum arquivo versionado foi alterado. A remoção ou inclusão no `.gitignore` fica a critério da equipe.

---

## 1. Resumo executivo

- O esqueleto funcional existe: CLI, extração com proveniência, validação jsonschema, delimitação e detecção de injeção, auditoria JSONL, revisão humana, OCR, STT e TTS. Há também uma barreira que impede envio automático.
- A parte avaliativa do PDF está **documentada, mas não implementada**: taxa de aprovação, severidade, experimento A/B/C com medição, relatório técnico e registro de IA estão vazios ou sem código correspondente.
- Faltam a imagem institucional GOV.MT na minuta (seção 6 do PDF), a execução real com modelo fixo e a medição de custo (`custo_usd` é sempre `None`).
- Os testes usam `unittest`, não pytest como o PDF pede, e cobrem só 11 casos. Cliente de API, multimodal, avaliação e experimento não têm teste.
- A documentação tem contradições (README × config, `lgpd.md` × código, `uso_da_ia.md` citando outro desafio).

---

## 2. O que falta ser feito

| # | Item | Requisito do PDF | Arquivo / pasta | Prioridade |
|---|---|---|---|---|
| 1 | Relatório técnico real (modelo, data, custo, tempo, resultados). Hoje é um modelo com "A preencher/pendente" | Entrega: relatório técnico | `documentacao/relatorio_tecnico.md` | Alta |
| 2 | Registro de uso de IA preenchido (modelos de API, checkboxes, assinaturas) | Entrega: registro de uso de IA | `documentacao/uso_da_ia.md` | Alta |
| 3 | Execução real com LLM e modelo fixo. Hoje `modelo: openrouter/free` não é versionado e `resultados/` só tem saídas mock | RF02, reprodutibilidade | `config/config.yaml`, `resultados/` | Alta |
| 4 | Metaprompt realmente gerado por modelo. O prompt C é um "modelo de exemplo, NÃO gerado por modelo real" | Experimento com 3 prompts | `prompts/experimento/prompt_C_modelo_exemplo.md`, `metaprompt.md` | Alta |
| 5 | Medição de tempo e custo. `custo_usd` sempre `None`; a matriz CSV tem colunas humanas vazias; no mock as saídas são idênticas | Experimento e API (tempo/custo) | `src/cliente.py`, `src/experimento.py` | Alta |
| 6 | Imagem institucional compatível com GOV.MT na minuta. `minuta.py` não insere imagem. `imagem_local` e `imagem_orientacao.md` dizem "sem brasões ou marcas oficiais" | Seção 6 | `src/minuta.py`, `src/multimodal.py:78-105`, `prompts/imagem_orientacao.md` | Alta |
| 7 | Avaliação com taxa de aprovação, severidade, `ausentes`, `decisao_esperada` e C04. `avaliar_campos` só compara protocolo, categoria e alerta, e `avaliacao.py` nunca é chamado pelo `main` | Avaliação com gabaritos | `src/avaliacao.py`, `dados/gabaritos/` | Alta |
| 8 | Migrar/complementar testes para pytest e cobrir `cliente` (retry, timeout, 401/429/5xx, JSON inválido), `multimodal`, `avaliacao`, `experimento`, `auditoria`, `executar_caso`, schema inválido e injeção em C03 | Qualidade de código | `testes/`, `requirements.txt` | Alta |
| 9 | Adicionar `OPENROUTER_API_KEY` ao `.env.example`. O provedor padrão é OpenRouter e o arquivo só lista OPENAI, GROQ e GEMINI | Configuração executável | `.env.example` | Alta |
| 10 | Incluir o caso C04 (imagem/timbre) em `casos.yaml`. O gabarito e o gerador existem, mas o caso não roda no pipeline | Dados e gabaritos | `dados/originais/casos.yaml`, `dados/gabaritos/C04.json` | Média |
| 11 | Usar ou remover `sistema_extracao.md` e `sistema_minuta.md`. A extração é por regex e o prompt da minuta está inline | Pasta `prompts/` coerente | `prompts/`, `src/minuta.py:18-20` | Média |
| 12 | Ligar a geração de imagem ao fluxo. `imagem` chama só `imagem_local`, `arte_ia.gerar` não é chamada e `imagem_provider` não é lido | Multimodal | `src/main.py:80-81`, `src/arte_ia.py` | Média |
| 13 | Fixar versões em `requirements.txt` e declarar o runner de testes. O arquivo está modificado sem commit | Configuração reproduzível | `requirements.txt` | Média |
| 14 | `verificar` deveria checar `pytesseract`, o binário `tesseract` e o `espeak` | Configuração executável | `src/main.py:72-79` | Média |
| 15 | CI sem tesseract/espeak, lint, tipagem ou cobertura | Qualidade | `.github/workflows/testes.yml` | Baixa |
| 16 | Tipagem e docstrings. As funções quase não têm type hints, e o código é compacto (várias instruções por linha) | Qualidade | `src/*.py` | Baixa |

---

## 3. O que pode sair do escopo

- **`src/arte_ia.py`** (geração de imagem pela API OpenAI). O PDF exige uma imagem institucional compatível, não necessariamente gerada por IA, e a composição local já cobre isso. Ele traz custo, uma dependência de provedor e não é chamado pelo pipeline. Não foi possível confirmar no PDF se a imagem precisa ser generativa. Confirmar antes de remover.
- **Provedores extras no `config.yaml`** (groq/openai/gemini além do usado). Cada perfil sem teste é superfície sem evidência. Manter os que serão realmente usados (OpenRouter e Groq para STT).
- **TTS por API.** Os ramos `espeak` e `mock` bastam para demonstrar acessibilidade. O ramo de API não tem teste nem uso comprovado.
- **`roteiro_12h.md` e as menções a ensaio/apresentação em `plano_projeto.md`.** É material de cronograma e fala, fora do escopo desta auditoria.
- **Resíduos:** o import não usado `minimizar` em `src/main.py:13` e a dependência `python-docx`, que já foi removida.

---

## 4. O que deve mudar (não aplicado)

### Tratamento de erros

1. `src/main.py:48`: uma decisão inválida levanta `ValueError` e aborta o lote inteiro. Deveria registrar a falha, pedir de novo ou pular o caso.
2. `src/main.py:91-93`: não há try/except por caso. Um arquivo de áudio ausente, um erro de schema ou um `ErroAPI` interrompem todos os casos seguintes.
3. `src/main.py:57-59`: o `except Exception` registra só `type(exc).__name__`, sem mensagem nem causa. O TTS só roda fora do mock, então o ramo nunca é exercitado nos testes.
4. `src/main.py:50-52`: "corrigir" só grava `PENDENTE_CORRECAO.txt`, sem fluxo de edição ou reprocessamento. Isso é inconsistente com o resultado `corrigir` do YAML e com a métrica "aprovação com correção" documentada.
5. `src/multimodal.py:60-61`: `subprocess.run(check=True)` sem tratamento levanta `CalledProcessError` bruto.
6. `src/multimodal.py:61,71`: `texto[:3500]` trunca a minuta silenciosamente, sem aviso nem registro.
7. `src/multimodal.py:43,72`: timeouts fixos (120 s) fora da configuração, e o STT não tem retry, ao contrário de `cliente.py`.
8. `src/multimodal.py:21-27`: `ler_imagem` não guarda o texto OCR bruto, não valida a qualidade e não registra erro se o `tesseract` não estiver instalado.
9. `src/cliente.py`: `custo_usd` fixo em `None`. Calcular a partir de tokens × preço configurável ou registrar "não localizado".
10. `src/experimento.py`: `__import__("src.main")` dentro do loop e `ErroAPI` importado sem tratamento. Importar no topo e tratar a falha por célula da matriz.

### Correção de comportamento

11. `src/extracao.py:11` e `:6`: o padrão de `solicitante` usa `re.IGNORECASE`, então as classes `[A-Z…]` casam minúsculas, e `\s+` casa quebra de linha. Um "Nome: Maria Fictícia Albuquerque" seguido de "Protocolo: …" na linha seguinte provavelmente captura "Protocolo" junto com o nome. **Hipótese, não verificada por execução.** Verificar com um teste. A correção seria usar `[ \t]+` e um flag local só para a palavra-chave.
12. `src/extracao.py:4`: o protocolo aceita só `20\d{2}\.\d{6}`. O `divisao_equipe.md` cita o formato `2026-000142` (material da equipe), que resultaria em "não localizado". Definir o formato oficial do caso.
13. `src/extracao.py:30`: `texto_fonte` recebe o nome do arquivo, não o texto. O campo engana quem lê o JSON.
14. `src/extracao.py:34`: `confianca_geral` é binário e deriva só da ausência de campos. A injeção detectada não reduz a confiança.
15. `src/seguranca.py:17`: o regex de telefone exige o dígito 9 (fixos passam). Nome, RG e endereço não são minimizados.
16. `src/seguranca.py:4-8`: os 5 padrões de injeção são só em português. Prompts em inglês ("ignore previous instructions") ou sem acento ("instrucoes") passam.
17. `src/minuta.py:21`: só `assunto` e `pedido` vão ao LLM, o que é bom. Mas `nome` e `protocolo` entram no cabeçalho sem minimização, e isso deve estar descrito em `lgpd.md`.
18. `config/config.yaml`: fixar o modelo (hoje `openrouter/free`, que roteia dinamicamente) e ler `imagem_provider`/`imagem_modelo`, ou removê-los.

### Testes

19. Criar testes unitários com `requests` simulado para `conversar` (3 tentativas, `sleep`, 401/403, 429/5xx, resposta vazia), para `transcrever`/`sintetizar` e para `avaliacao` (WER/CER com valores conhecidos).
20. `testes/gerar_dados_ficticios.py`: usa caminhos de fonte só do Linux e `espeak`. No Windows ele imprime "pendente", e o fallback `load_default` piora o OCR. Isso torna o ambiente de desenvolvimento (Windows) diferente do da CI.
21. O texto do PNG de C03 ("o pedido foi deferido") difere de `C03_ocr_ficticio.txt` ("foi deferido"). Alinhar evita falso diagnóstico no WER.

---

## 5. Riscos de segurança e privacidade

- **Credenciais.** Não foi encontrada chave versionada com os padrões testados. A chave vem do ambiente (`env_chave`) e o `.env` está no `.gitignore`. Risco residual: o `.env.example` incompleto leva a pessoa a criar `.env` fora do padrão, e logs de erro devem continuar sem expor tokens.
- **Dados reais.** Os dados de entrada são fictícios (CPF `000.111.222-33`, e-mail `@exemplo.invalid`). Dois riscos permanecem:
  - o material da equipe (`entrada_audio.mp3`, `entrada_pdf-imagem.pdf`, `brasao.png`) é citado em `divisao_equipe.md`, mas não está no repositório. Não há evidência de que seja fictício;
  - `lgpd.md` deixa em aberto a retenção no provedor, a regra de descarte e a confirmação de que não há voz real.
- **Voz e imagem de pessoas.** O áudio de C02 é sintetizado por `espeak`, o que é seguro. O áudio da equipe (`entrada_audio.mp3`) pode conter voz real e não deve ser enviado a um STT externo sem decisão explícita.
- **Brasão oficial.** O PDF pede compatibilidade com o GOV.MT, mas `AGENTS.md` exige dados fictícios e sem marcas oficiais reais. Há conflito possível entre os dois. Documentar a decisão (identidade fictícia compatível ou uso autorizado).
- **Prompt injection.** Há defesa em camadas: delimitação, 5 regexes, alerta no JSON e instrução de sistema. Lacunas: padrões só em português, nenhum teste de injeção para C03, e a detecção por regex não impede o conteúdo de chegar ao LLM.
- **Invenção de fatos.** O "não localizado" é aplicado na extração, mas a minuta depende do LLM. Não há verificação automática de que o texto gerado não introduz protocolo, prazo ou lei.
- **Ausência de revisão humana.**
  - A barreira existe em `config.py` (bloqueia `envio_automatico` e revisão desativada) e no rodapé da minuta.
  - A decisão "aprovar" via YAML é simulação (declarado em `AGENTS.md`).
  - Em modo não interativo, o `input()` é a única barreira. Em um pipeline sem TTY, ele falharia, não aprovaria.
  - "corrigir" não tem fluxo real, então o caminho de revisão com edição não está implementado.
- **Mock.** O modo mock lê transcrições fictícias rotuladas e está sinalizado como não real. Não há evidência de que a saída mock seja apresentada como modelo real, mas é preciso confirmar que `resultados/` não contém mock com aparência de execução real.

---

## 6. Lacunas de documentação

1. **README × configuração.** O README manda trocar `llm.provider` de `mock` para groq/openai/gemini, mas o `config.yaml` real usa `openrouter` e o README não menciona OpenRouter. O passo de clonagem aponta para `github.com/diegocbaleite/...`. Há seções duplicadas e uma seção "Execução do pipeline" colada depois de `---`.
2. **README, tabela de estado.** Declara "Implementado; executar testes" sem evidência de execução. Substituir por data e saída de uma execução real.
3. **`lgpd.md`.** Marca como feito "cliente de API recebe texto minimizado", mas só CPF, e-mail e telefone são minimizados, e apenas em assunto e pedido. Nome, RG e endereço não são.
4. **`protocolo_avaliacao.md`.** Descreve rubrica 0-2 × 5 critérios, severidade, taxa de aprovação direta e com correção, tom 1-5 e minutos até uso. Nada disso é calculado no código, e a rubrica não tem data de congelamento. O risco é adaptar o critério depois do teste, o que `AGENTS.md` proíbe.
5. **Gabaritos.** Não têm data nem hash de congelamento e não definem solicitante, data ou assunto esperados.
6. **`uso_da_ia.md`.**
   - Declara "GPT-6", o que não é verificável.
   - Cita a estruturação do GitHub como `desafio-03-pipeline-recomendacao`, inconsistente com este repositório (Desafio 05). O README já removeu a referência ao Desafio 03.
   - Tem "Modelos usados no fluxo com API: [preencher]", checkboxes vazios e assinaturas em branco.
7. **`plano_projeto.md`.**
   - O fluxo mermaid mostra TTS e peça visual após a aprovação, mas o código não chama a geração de imagem no fluxo.
   - Lista C04, que não está em `casos.yaml`.
   - Exige Python 3.11+, mas a CI usa 3.12 e o ambiente local tem outras versões.
8. **`divisao_equipe.md` × `roteiro_12h.md`.** Atribuem papéis trocados: Diego fica com prompts/avaliação/documentação em um e com API/segurança no outro, e o inverso vale para Ayron. Definir uma fonte única. Também citam material da equipe (protocolo `2026-000142`, e-mail diferente entre texto e áudio) que não está no repositório.
9. **`prompts/`.** `sistema_extracao.md` e `sistema_minuta.md` descrevem comportamento que o código não usa, e o `prompt_C_modelo_exemplo.md` fica ao lado do `metaprompt.md` sem explicar que C não foi gerado.
10. **`relatorio_tecnico.md`.** Sem seções de limitações reais, custos, comparação A/B/C ou aprovação. O próprio texto admite ser um modelo.
11. **Ausências.** Não há uma seção que mapeie RF01-RF13 para arquivo e teste com evidência, nem documentação de como rodar no Windows (fontes, espeak, tesseract).

---

## Ordem de ataque sugerida

1. `.env.example`, README e contradições de documentação.
2. Tratamento de erros por caso e testes de `cliente`.
3. Avaliação com taxa de aprovação e severidade.
4. Execução real com modelo fixo e preenchimento de `relatorio_tecnico.md` e `uso_da_ia.md`.
5. Imagem institucional.
