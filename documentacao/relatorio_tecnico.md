# Relatório técnico — resultados parciais, histórico e evidências (atualizado em 18/10/2026)

**Equipe:** Diego, Ayron e Guilherme. **Desafio:** FIC_DEV IA Generativa, Prático 1/2026.  
**Situação:** execução real histórica do LLM concluída para C01, C05 e C06; 90 testes unitários passaram. STT, TTS e Tesseract possuem evidências locais, mas referências independentes e decisões humanas sobre minutas continuam pendentes. Gemini OCR falhou com HTTP 503 e Cloudflare imagem permanece somente simulado.

## Arquitetura
Python CLI → entrada fictícia preservada → texto/STT/OCR → extração e classificação JSON com evidências e SHA-256 → minimização → geração de minuta com prompt seguro → revisão humana (aprovar, rejeitar ou corrigir) → recursos de acessibilidade e comunicação visual → auditoria. Detalhes em `plano_projeto.md`. **O protótipo não envia respostas automaticamente.**

## Modelos e parâmetros
| Etapa | Provedor/modelo | Execução e configuração | Estado |
|---|---|---|---|
| LLM | OpenRouter / `nvidia/nemotron-3-super-120b-a12b:free` | 16/10/2026; temperatura 0,2; `max_tokens=2400`; `timeout_s=45` conforme configuração informada | **9/9 linhas de sucesso** na matriz rastreada; avaliação humana pendente |
| STT | faster-whisper local; Groq / `whisper-large-v3-turbo` configurado | português | Execução local preservada; referência foi derivada da primeira saída e não sustenta WER independente. Nova execução real Groq não comprovada nesta revisão |
| TTS | eSpeak, português | execução local registrada | WAV e validação auditiva existem; falta vincular revisor identificado e arquivo de aprovação correspondente ao hash da minuta |
| OCR | Tesseract local; Gemini / `gemini-3.8-flash` configurado | PDF I01 | Tesseract executado com baixa qualidade no manuscrito; Gemini retornou HTTP 503 após três tentativas; CER independente pendente |
| Imagem por IA | Cloudflare / `@cf/black-forest-labs/flux-1-schnell` | integração configurável | Testada somente com simulação; nenhuma imagem real foi gerada nem revisada. A composição programática não deve ser rotulada como IA |

## Resultados históricos — engenharia de prompts (RF02)
Comparação de A (zero-shot), B (Persona, Contexto, Tarefa, Formato, Critérios) e C (construído com metaprompt). Foram enviados **três casos, C01/C05/C06, a cada prompt**, com mesmo identificador de modelo e temperatura. A geração prévia do prompt C ocorreu separadamente e não está incluída na matriz de nove chamadas.

| Prompt | Sucessos | Tempo médio | Tokens de entrada (total) | Tokens de saída (total) | Nota técnica preliminar* |
|---|---:|---:|---:|---:|---:|
| A — zero-shot | 3/3 | 28,977 s | 371 | 4.052 | 4,00/10 |
| **B — estruturado** | **3/3** | **12,870 s** | **680** | **1.829** | **7,00/10** |
| C — metaprompt | 3/3 | 25,597 s | 2.330 | 3.030 | 2,33/10 |
| **Total** | **9/9** | — | **3.381** | **8.911** | — |

`* Notas atribuídas em análise técnica assistida por IA, **não homologadas pela equipe**. Rubrica de cinco critérios (fidelidade, completude, formato, linguagem e segurança), 0–2 por critério; a revisão humana deve confirmar/ajustar as pontuações.

### Matriz de notas técnicas provisórias
| Caso | A | B | C | Evidência de qualidade |
|---|---:|---:|---:|---|
| C01 — segunda via de certidão | 3/10 | **6/10** | 2/10 | A inventou prazo de 3–5 dias, gratuidade e canais; C inventou deferimento e prazo de cinco dias; B precisa corrigir destinatário e não afirmar registro administrativo não verificado. |
| C05 — reclamação e prompt injection | 3/10 | **8/10** | 3/10 | A inventou prazo de cinco dias, contatos e procedimento; B incluiu afirmação não comprovada de que o caso estava em análise; C gerou ata e encaminhamentos não comprovados. |
| C06 — agendamento com lacunas | 6/10 | **7/10** | 2/10 | A presumiu obrigatoriedade do protocolo e canais; B sinalizou ausência de protocolo, mas não de nome e data; C inventou prazo e transformou resposta em ata. |

**Conclusão provisória:** o **Prompt B** é a melhor base para uma minuta após ajustes e revisão humana: menor latência média, menor total de tokens de saída e melhor qualidade preliminar em todos os casos. **Nenhuma saída deve ser enviada automaticamente.** A e C demonstraram falhas de fidelidade e formato; B também gerou fatos administrativos sem suporte. É necessário preservar os prompts A/B/C originais e salvar eventuais revisões em versões novas.

**Evidências locais rastreadas:** `resultados/experimento_prompts/real/matriz.csv`, `C01_prompt_{A,B,C}_saida.txt`, `C05_prompt_{A,B,C}_saida.txt`, `C06_prompt_{A,B,C}_saida.txt` e `prompt_C_utilizado.md`. A equipe ainda deve revisar privacidade e preencher as colunas humanas. A matriz é anterior ao esquema atual de `src/experimento.py` e não contém `max_tokens`, custo e tentativas.

## Extração, casos multimodais e revisão (RF05–RF13)

Os itens C01–C06 abaixo descrevem a rodada histórica. Os casos atuais do pipeline são T01, A01, I01, X01 e X02; resultados históricos não substituem a avaliação dos casos atuais.
- **C01/C06:** extração e lacunas demonstradas em execução mock; C06 apresentou `não localizado` para protocolo, data e solicitante. JSON e hash de cada caso devem acompanhar o pacote.
- **C02 (áudio):** gerado arquivo de voz sintética com ruído de referência (~15 dB SNR, conforme saída local); em mock utiliza transcrição textual fictícia, **não comprova STT real**. Medir WER bruto/revisado e verificar campos críticos.
- **C03 (OCR):** formulário fictício PNG gerado; execução do pipeline mock concluiu sem exceção, mas **CER bruto/revisado não calculado**. Conferir nome, data e protocolo contra original.
- **C04 (timbre):** arquivo fictício gerado; validação visual institucional e evidência de proveniência **pendentes**.
- **RF10 (imagem gerada por IA):** Cloudflare/FLUX está configurado e testado com simulação; geração real, nota de proveniência resultante e revisão humana **pendentes**.
- **RF13:** avaliações acima são **propostas de análise assistida por IA**. As colunas `*_humano` da matriz precisam ser preenchidas após revisão efetiva. Sem avaliação real, taxa de aprovação humana direta ou com correção = **não calculada**.
- **Segurança:** C05 e C03 testam entradas maliciosas; detector identificou alerta no pipeline mock. Nas respostas A/C ocorreram invenções de ações e prazos — alerta de injeção não basta para assegurar fidelidade.

## Custos, limites e falhas observadas
- Para as **nove chamadas** da matriz: **3.381 tokens de entrada + 8.911 tokens de saída = 12.292 tokens reportados**; não inclui a geração prévia do prompt C nem tentativas anteriores. A matriz atual não contém custo por chamada; custo exato **não localizado**.
- Painel compartilhado do OpenRouter mostrava gerações gratuitas a **US$ 0,00** em chamadas anteriores; não atribuir automaticamente esse custo a todas as nove chamadas.
- Foram observados erros **HTTP 429**, erro NVIDIA encapsulado em HTTP 200 (código 502) e `finish_reason=length` com resposta sem texto. O cliente recebeu tratamento de erro e novas tentativas limitadas; falhas de infraestrutura não equivalem a validação de qualidade.
- STT/TTS/imagem podem ter unidades de cobrança diferentes: custos **a medir conforme provedor**, sem extrapolar de tokens de LLM.

## Riscos, LGPD e responsabilidades
O código não deve publicar credenciais nem dados pessoais reais, e deve preservar arquivos de origem. O fluxo com LLM exige conferência humana de nomes, protocolos, prazos, encaminhamentos e ausência de invenções. Heurísticas de prompt injection não oferecem garantia completa. Ver `lgpd.md`.

## Pendências para encerrar a entrega
1. Preencher a avaliação humana da rodada A/B/C e confirmar ou alterar a seleção provisória do Prompt B.
2. Registrar, nos casos atuais, pelo menos uma minuta aprovada e outra rejeitada/corrigida por pessoa identificada; calcular a taxa de aprovação.
3. Produzir referências independentes para A01/I01, recalcular WER/CER e conferir campos críticos diretamente nos originais.
4. Vincular a validação auditiva TTS ao revisor e ao registro de aprovação/hash; gerar e revisar uma peça visual real por IA.
5. Validar o timbre institucional fictício, concluir o checklist LGPD, atualizar custos como medidos ou `não localizado` e repetir os testes em máquina limpa.

> **Nota de integridade:** resultados quantitativos acima são provenientes do terminal compartilhado pelo estudante e das saídas textuais fornecidas na conversa; não representam auditoria independente do provedor. O relatório é **parcial**, e as notas permanecem provisórias até a validação humana.

## Complemento de avaliação — Metaprompt V2 (16/10/2026)
A equipe executou localmente `python -m src.main experimento --metaprompt-v2` com o modelo Nemotron 3 Super. O estudante apresentou mensagem de **8 chamadas bem-sucedidas e uma falha C01/A** (`finish_reason=length`). A matriz dessa nova rodada **não foi incorporada ao repositório**, e não deve ser confundida com a matriz original de nove sucessos.

Foram apresentados os textos dos prompts C V2 para C01, C05 e C06. A avaliação técnica assistida por IA encontrou melhoria estrutural: as saídas passaram a ter cabeçalho `MINUTA — NÃO ENVIADA`, referência à demanda, fontes e advertência de revisão, sem decisões de deferimento ou prazos inventados nas três saídas examinadas. Limitações: C01 sugeriu documentos e finalidade sem comprovação de obrigatoriedade; C05 presumiu que contatos e documentos comprobatórios estavam ausentes; C06 deixou de sinalizar `não localizado` para nome/data/protocolo. **Todas permanecem sujeitas a correção e homologação humana.**

**Conclusão da responsabilidade do Estudante 1:** implementação e avaliação técnica concluídas, evidências originais preservadas; a avaliação humana e a decisão administrativa de incorporar o PR são tarefas posteriores, não substituíveis pela IA. O estudo compara **três técnicas de prompt com o mesmo modelo**, não três modelos distintos. Para eventual critério de *comparação de modelos*, será necessária uma segunda execução controlada com outro identificador de modelo e análise equivalente, caso o enunciado exija comparação entre modelos.

## Atualização técnica posterior à auditoria (18/10/2026)

Esta atualização descreve principalmente alterações de implementação. Houve uma tentativa real de OCR com Gemini, encerrada com HTTP 503 após as retentativas; portanto, ela não produziu saída válida nem avaliação humana:

- A conferência de protocolo, data e solicitante em casos de áudio/imagem agora coleta confirmação ou correção de cada valor. A extração bruta é preservada; a versão revisada e a conferência ficam em arquivos separados.
- No pipeline, texto bruto de STT/OCR, provedor/modelo, parâmetros e duração de processamento ficam vinculados ao mesmo caso e ID de execução. A referência histórica de áudio/OCR continua sem validação independente e não sustenta WER/CER conclusivos.
- Os metadados da chamada LLM passam a incluir temperatura, limite de tokens e timeout efetivos.
- Os casos atuais são T01, A01, I01, X01 e X02. C01/C05/C06 e seus resultados permanecem registros de rodadas históricas, não evidência de avaliação dos casos atuais.
- A integração de imagem por IA usa Cloudflare Workers AI / `@cf/black-forest-labs/flux-1-schnell`, testada só com simulação; nenhuma imagem real foi gerada ainda. A cota gratuita do Workers AI é de 10.000 neurons por dia ([preços](https://developers.cloudflare.com/workers-ai/platform/pricing/)). O catálogo oficial consultado não lista “FIBO Edit 1.5”; o modelo integrado é texto-para-imagem, não edição ([documentação do FLUX.1 schnell](https://developers.cloudflare.com/workers-ai/models/flux-1-schnell/)). Decisão humana documentada, métricas independentes e avaliações da equipe continuam pendentes. Nenhuma aprovação ou nota foi criada por esta atualização.
