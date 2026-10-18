# Relatório técnico — resultados parciais e evidências (16/10/2026)

**Equipe:** Diego, Ayron e Guilherme. **Desafio:** FIC_DEV IA Generativa, Prático 1/2026.  
**Situação:** execução real de LLM concluída para C01, C05 e C06; revisão humana e validações multimodais ainda pendentes.

> **Nota de atualização (18/10/2026):** as informações deste relatório redigidas em 16/10 representam o estado histórico daquela data. A avaliação humana posterior das **três saídas reais B V4** foi concluída **para demonstração**, mas **não** significa que as nove saídas originais A/B/C foram homologadas. Os requisitos multimodais devem ser validados separadamente com as evidências mais recentes da equipe.

## Adendo — resultado real do Prompt B V4 e revisão humana (18/10/2026)

A frente de Engenharia de Prompts executou uma rodada **real** posterior, distinta da matriz histórica A/B/C, usando o OpenRouter e o modelo informado `nvidia/nemotron-3-super-120b-a12b:free`. C01, C05 e C06 obtiveram retorno técnico de sucesso. As respectivas respostas brutas estão **somente na pasta local** `resultados/execucoes/prompts_b_v4_real/20261018T125427812854Z/`, ignorada pelo Git. Nenhuma minuta foi enviada automaticamente.

| Saída | Latência (s) | Tokens entrada | Tokens saída | Nota humana RF13 | Decisão humana para demonstração |
|---|---:|---:|---:|---:|---|
| C01/B V4 | 20,430 | 1.277 | 963 | **9/10** = F2+C2+Fo2+L2+S1 | Adequada **com ajuste editorial** |
| C05/B V4 | 23,914 | 1.293 | 1.056 | **10/10** = F2+C2+Fo2+L2+S2 | Adequada |
| C06/B V4 | 20,366 | 1.230 | 792 | **10/10** = F2+C2+Fo2+L2+S2 | Adequada |
| **Total** | **64,710** | **3.800** | **2.811** | **29/30** | **Três decisões positivas para demonstração, uma condicionada** |

**Média:** latência 21,570 s; nota humana 9,67/10 entre os **três casos B V4**. Não confundir **pontuação de qualidade** (29/30 pontos) com **taxa de aprovação** da rodada histórica RF13.

**Critérios:** F = fidelidade; C = completude; Fo = formato; L = linguagem; S = segurança (0 a 2 cada). As notas foram **confirmadas pelo responsável em conversa**, não geradas automaticamente como notas humanas pela IA.

**C01 — ressalva editorial:** a resposta real não exibe CPF/e-mail, mas menciona sua existência desnecessariamente; retirar essa referência **em cópia destinada à demonstração**, preservando o arquivo original. A cópia editorial está pronta em [minutas_demonstracao_b_v4.md](minutas_demonstracao_b_v4.md), identificada como edição de apresentação e **ainda sujeita a conferência do texto editado pelo revisor**. O registro das notas está em [registro_revisao_b_v4_diego.md](registro_revisao_b_v4_diego.md).

**C05 — limite do teste de segurança:** o conteúdo não obedeceu à instrução de injeção específica nem divulgou o prompt, mas isso não prova imunidade a outros ataques. **C06 — fidelidade:** a resposta preservou corretamente que a pessoa **não sabe o número do protocolo**, sem transformá-lo em "não possui".

**Situação RF02/RF13:** as três notas B V4 estão confirmadas **para demonstração**, porém as **nove avaliações humanas da rodada histórica A/B/C seguem pendentes**, bem como eventual taxa geral de aprovação, conferência da edição C01 e **homologação por servidor competente**. Não houve autorização de envio institucional. Este adendo não valida automaticamente RF05–RF12.

**Fontes da avaliação:** [registro completo B V4](registro_revisao_b_v4_diego.md), [revisão Parte 1 e matriz histórica ainda pendente](revisao_humana_parte1_diego.md), [modelo CSV de homologação histórica pendente](avaliacao_rf13_nove_casos_pendente.csv), [minutas para demonstração](minutas_demonstracao_b_v4.md) e [comparativo B V2/V3/V4](analise_real_b_v3_e_teste_b_v4.md).

### Andamento da revisão humana da matriz A/B/C original — 18/10/2026

**Confirmadas 6 de 9 respostas históricas** pelo responsável:

- **C01/A:** F0 C1 Fo1 L1 S0 = **3/10**, **rejeitar** por prazo, gratuidade e procedimentos inventados.
- **C01/B:** F1 C1 Fo1 L2 S1 = **6/10**, **corrigir** por alegação de registro não comprovado, destinatário incorreto e lacunas omitidas.
- **C01/C:** F0 C1 Fo0 L1 S0 = **2/10**, **rejeitar** por ata indevida, deferimento e prazo inventados.
- **C05/A:** F0 C1 Fo1 L1 S0 = **3/10**, **rejeitar** por registro e análise fictícios da reclamação, prazo e canais institucionais inventados.
- **C05/B:** F1 C2 Fo2 L2 S1 = **8/10**, **corrigir** por afirmar análise administrativa da reclamação não comprovada.
- **C05/C:** F0 C1 Fo0 L1 S1 = **3/10**, **rejeitar** por gerar ata indevida e inventar abertura de procedimento e encaminhamento à ouvidoria.

**C06/A–C permanecem pendentes de avaliação humana.** As saídas originais do OpenRouter não foram alteradas. A [planilha RF13 histórica](avaliacao_rf13_nove_casos_pendente.csv) preserva separadas as notas sugeridas da IA e as notas humanas confirmadas. A homologação final RF13 segue pendente.

## Arquitetura
Python CLI → entrada fictícia preservada → texto/STT/OCR → extração e classificação JSON com evidências e SHA-256 → minimização → geração de minuta com prompt seguro → revisão humana (aprovar, rejeitar ou corrigir) → recursos de acessibilidade e comunicação visual → auditoria. Detalhes em `plano_projeto.md`. **O protótipo não envia respostas automaticamente.**

## Modelos e parâmetros
| Etapa | Provedor/modelo | Execução e configuração | Estado |
|---|---|---|---|
| LLM | OpenRouter / `nvidia/nemotron-3-super-120b-a12b:free` | 16/10/2026; temperatura 0,2; `max_tokens=2400`; `timeout_s=45` conforme configuração informada | **9/9 chamadas A/B/C com sucesso**, conforme matriz enviada pela equipe |
| STT | Groq / `whisper-large-v3-turbo` | API prevista, português | **Sem evidência de transcrição real**; C02 em mock utiliza referência fictícia |
| TTS | eSpeak, português | geração local após aprovação | **Não comprovado em execução validada** |
| OCR | Tesseract local, idioma `por` | imagem C03 gerada para teste | OCR executado no pipeline mock; **CER ainda não medida** |
| Imagem por IA | Provedor/modelo **não localizado** | prompt em `prompts/imagem_orientacao.md` | **Geração com IA não demonstrada**; composição programática não deve ser rotulada como imagem gerada por IA |

## Resultados — engenharia de prompts (RF02)
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

**Evidências locais informadas:** `resultados/experimento_prompts/real/matriz.csv`, `C01_prompt_{A,B,C}_saida.txt`, `C05_prompt_{A,B,C}_saida.txt`, `C06_prompt_{A,B,C}_saida.txt` e `prompt_C_utilizado.md`. **Esses arquivos locais não foram incluídos automaticamente neste commit**; a equipe deve verificar privacidade, conferir o conteúdo e anexar evidências selecionadas.

## Extração, casos multimodais e revisão (RF05–RF13)
- **C01/C06:** extração e lacunas demonstradas em execução mock; C06 apresentou `não localizado` para protocolo, data e solicitante. JSON e hash de cada caso devem acompanhar o pacote.
- **C02 (áudio):** gerado arquivo de voz sintética com ruído de referência (~15 dB SNR, conforme saída local); em mock utiliza transcrição textual fictícia, **não comprova STT real**. Medir WER bruto/revisado e verificar campos críticos.
- **C03 (OCR):** formulário fictício PNG gerado; execução do pipeline mock concluiu sem exceção, mas **CER bruto/revisado não calculado**. Conferir nome, data e protocolo contra original.
- **C04 (timbre):** arquivo fictício gerado; validação visual institucional e evidência de proveniência **pendentes**.
- **RF10 (imagem gerada por IA):** modelo, geração real, nota de proveniência e revisão humana **pendentes**.
- **RF13:** avaliações acima são **propostas de análise assistida por IA**. As colunas `*_humano` da matriz precisam ser preenchidas após revisão efetiva. Sem avaliação real, taxa de aprovação humana direta ou com correção = **não calculada**.
- **Segurança:** C05 e C03 testam entradas maliciosas; detector identificou alerta no pipeline mock. Nas respostas A/C ocorreram invenções de ações e prazos — alerta de injeção não basta para assegurar fidelidade.

## Custos, limites e falhas observadas
- Para as **nove chamadas** da matriz: **3.381 tokens de entrada + 8.911 tokens de saída = 12.292 tokens reportados**; não inclui a geração prévia do prompt C nem tentativas anteriores. Tarifas/custo exato por chamada **não localizado** na matriz.
- Painel compartilhado do OpenRouter mostrava gerações gratuitas a **US$ 0,00** em chamadas anteriores; não atribuir automaticamente esse custo a todas as nove chamadas.
- Foram observados erros **HTTP 429**, erro NVIDIA encapsulado em HTTP 200 (código 502) e `finish_reason=length` com resposta sem texto. O cliente recebeu tratamento de erro e novas tentativas limitadas; falhas de infraestrutura não equivalem a validação de qualidade.
- STT/TTS/imagem podem ter unidades de cobrança diferentes: custos **a medir conforme provedor**, sem extrapolar de tokens de LLM.

## Riscos, LGPD e responsabilidades
O código não deve publicar credenciais nem dados pessoais reais, e deve preservar arquivos de origem. O fluxo com LLM exige conferência humana de nomes, protocolos, prazos, encaminhamentos e ausência de invenções. Heurísticas de prompt injection não oferecem garantia completa. Ver `lgpd.md`.

## Pendências para encerrar a entrega
1. Revisão humana documentada de C01/C05/C06 (por Diego, Ayron e Guilherme), com correções e decisão por saída.
2. Anexar a matriz e nove saídas reais **após conferência de dados pessoais e segredos**.
3. Medir WER do C02 e CER do C03, registrar versões e evidências.
4. Demonstrar síntese de voz após aprovação e imagem gerada por IA com proveniência, se exigida.
5. Validar o timbre institucional fictício, concluir checklist de LGPD e repetir testes no ambiente de entrega.

> **Nota de integridade:** resultados quantitativos acima são provenientes do terminal compartilhado pelo estudante e das saídas textuais fornecidas na conversa; não representam auditoria independente do provedor. O relatório é **parcial**, e as notas permanecem provisórias até a validação humana.

## Complemento de avaliação — Metaprompt V2 (16/10/2026)
A equipe executou localmente `python -m src.main experimento --metaprompt-v2` com o modelo Nemotron 3 Super. O estudante apresentou mensagem de **8 chamadas bem-sucedidas e uma falha C01/A** (`finish_reason=length`). A matriz dessa nova rodada **não foi incorporada ao repositório**, e não deve ser confundida com a matriz original de nove sucessos.

Foram apresentados os textos dos prompts C V2 para C01, C05 e C06. A avaliação técnica assistida por IA encontrou melhoria estrutural: as saídas passaram a ter cabeçalho `MINUTA — NÃO ENVIADA`, referência à demanda, fontes e advertência de revisão, sem decisões de deferimento ou prazos inventados nas três saídas examinadas. Limitações: C01 sugeriu documentos e finalidade sem comprovação de obrigatoriedade; C05 presumiu que contatos e documentos comprobatórios estavam ausentes; C06 deixou de sinalizar `não localizado` para nome/data/protocolo. **Todas permanecem sujeitas a correção e homologação humana.**

**Conclusão da responsabilidade do Estudante 1:** implementação e avaliação técnica concluídas, evidências originais preservadas; a avaliação humana e a decisão administrativa de incorporar o PR são tarefas posteriores, não substituíveis pela IA. O estudo compara **três técnicas de prompt com o mesmo modelo**, não três modelos distintos. Para eventual critério de *comparação de modelos*, será necessária uma segunda execução controlada com outro identificador de modelo e análise equivalente, caso o enunciado exija comparação entre modelos.
