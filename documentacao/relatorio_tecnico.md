# Relatório técnico — casos atuais e evidências

**Equipe:** Diego, Ayron e Guilherme. **Desafio:** FIC_DEV IA Generativa, Prático 1/2026.  
**Atualização:** 18/10/2026, após correções da auditoria técnica.

**Adendo de 28/10/2026:** OpenAI substitui os provedores padrão na configuração, com uma chamada real de texto concluída e contratos multimodais testados por simulação. O estado e as tabelas abaixo são históricos; não transferir suas métricas para os novos modelos. Consulte [integração OpenAI](integracao_openai.md) para configuração, parâmetros, medição real, limites e pendências. A revisão humana da nova saída ainda não ocorreu.

Este relatório prioriza o catálogo vigente em `dados/originais/casos.yaml`. Existe também uma avaliação humana concluída de uma rodada anterior com três casos substituídos. Seus resultados são preservados e apresentados em seção própria, sem serem atribuídos aos casos atuais.

## Catálogo avaliado

| Caso | Modalidade | Entrada | Gabarito | Objetivo |
|---|---|---|---|---|
| `T01` | texto | `dados/originais/entrada_texto.txt` | `dados/gabaritos/T01.json` | Extrair e responder à solicitação fictícia de efetivação de matrícula |
| `A01` | áudio | `dados/originais/entrada_audio.mp3` | `dados/gabaritos/A01.json` | Transcrever a mesma demanda e conferir protocolo, data e solicitante |
| `I01` | imagem/PDF | `dados/originais/entrada_pdf-imagem.pdf` | `dados/gabaritos/I01.json` | Executar OCR e conferir campos críticos no documento original |
| `X01` | texto | `testes/fixtures/injecao.txt` | `dados/gabaritos/X01.json` | Verificar tratamento de conteúdo malicioso como dado não confiável |
| `X02` | texto | `testes/fixtures/lacunas.txt` | `dados/gabaritos/X02.json` | Verificar o marcador `não localizado` para campos ausentes |

Os gabaritos foram preparados antes das execuções e não podem ser ajustados para coincidir com saídas de modelos.

## Estado consolidado

| Área | Evidência disponível | Estado e limite |
|---|---|---|
| Texto e extração | Testes de `T01`, `X01` e `X02`; JSON estruturado, esquema e comparação ampliada com gabaritos | Implementado e coberto por testes locais |
| Prompts A/B/C | Código em `src/experimento.py`; matriz real atual; avaliações histórica e atual | Rodada atual concluída com 9/9 chamadas; Prompt B obteve a maior média atual, 7,33/10 |
| Catálogo | Validação de YAML, IDs únicos, modalidades, arquivos, caminhos seguros, referências e seleção por `--caso` | Implementado; referências conferidas disponíveis e lote multimodal `--mock` completo validado |
| STT | Entrada e gabarito de `A01`; processamento local/remoto, retentativas, transcrição bruta e referência conferida | Execução e conferência concluídas; WER 11,43% e CER 5,06% |
| OCR | Entrada e gabarito de `I01`; Tesseract local, visão Gemini, OCR bruto e referência conferida | Execução concluída; WER 91,89% e CER 85,91%; saída bruta rejeitada e campos críticos corrigidos |
| Minutas | Geração local, separação entre pendente/aprovada e trilha de revisão | Nenhuma decisão YAML ou `--mock` vale como aprovação humana |
| TTS | Implementação local/Gemini, retentativas, validação do áudio e bloqueio por aprovação/hash | Gemini TTS executado; WAV, roteiro, hashes, duração e validação para demonstração registrados |
| Imagem | Composição local e integração Cloudflare com retentativas, validação e proveniência | Imagem real gerada por Cloudflare/FLUX e revisão visual aprovada para demonstração |
| Auditoria | Logs JSONL, hashes, timestamps UTC e diretórios por execução | Campos estruturais são protegidos contra sobrescrita; métricas ausentes permanecem `não localizado` |

## Verificação técnica após a auditoria

Em 18/10/2026, foram executadas verificações locais sem chamadas externas:

- `python -m unittest discover -s testes -t .`: **114 testes aprovados**;
- `python -m src.main verificar`: concluído, com envio automático desabilitado;
- `python -m src.main --mock --caso T01 --decisoes dados/revisao/decisoes_demo.yaml`: concluído com sucesso e decisão identificada como simulada;
- `python -m src.main --mock --decisoes dados/revisao/decisoes_demo.yaml`: lote completo concluído com os cinco casos, referências multimodais e decisões corretamente identificadas como simuladas.

Os testes cobrem, entre outros pontos, propagação de falhas do experimento e do TTS, retentativas transitórias, rejeição de conteúdo TTS que não seja MP3, conversão TIFF para PNG, validação do catálogo, IDs desconhecidos, timestamps UTC e comparação dos elementos presentes nos gabaritos.

A aprovação da suíte comprova o comportamento implementado em ambiente controlado. Ela não substitui execução real dos provedores, inspeção auditiva/visual, validação em máquina limpa ou revisão humana dos casos vigentes.

## Provedores, modelos e custos

| Etapa | Provedor/modelo configurado | Parâmetros principais | Evidência atual | Custo medido | Justificativa/limite |
|---|---|---|---|---|---|
| Minuta e experimento A/B/C | Gemini / `gemini-3.1-flash-lite` | temperatura 0,2; máximo 2.400 tokens; timeout 45 s | Minutas e rodada A/B/C atual executadas no serviço real | `não localizado` | Mesmo modelo e parâmetros mantidos entre A, B e C |
| STT | Groq / `whisper-large-v3-turbo`; alternativa local `faster-whisper` | idioma português; timeout 120 s | Execução real e referência conferida de `A01` disponíveis | `não localizado` | O padrão remoto envia o áudio integral; a alternativa local reduz exposição |
| OCR/visão | Gemini / `gemini-3.8-flash`; alternativa Tesseract | até 3 páginas; Tesseract 300 dpi/PSM 6 | Execução real concluída com divergências críticas; referência conferida disponível | `não localizado` | Campos críticos continuam sujeitos a correção no original |
| TTS | Gemini / `gemini-3.8-flash-lite-tts`; alternativa eSpeak | voz `Kore`; tom institucional; limite 3.500 caracteres | Execução e validação para demonstração concluídas | `não localizado` | Só é acionado depois de aprovação humana válida e hash correspondente |
| Imagem | Cloudflare / `@cf/black-forest-labs/flux-1-schnell`; alternativa Pillow | 4 etapas; prompt versionado | Geração, proveniência e revisão para demonstração concluídas | `não localizado` | Uso oficial permanece desabilitado |

Nenhum valor de custo foi inferido. O pacote final de evidências deve conter apenas cópias higienizadas de prompts, saídas, matrizes, metadados e decisões humanas vinculadas aos casos vigentes; até sua criação, os diretórios locais em `resultados/` não são tratados como evidência entregue.

## Engenharia de prompts (RF02)

O experimento compara A (zero-shot), B (estruturado) e C (produzido por metaprompt). O código atual seleciona apenas entradas de modalidade texto, portanto a matriz vigente deve conter `T01`, `X01` e `X02`, cada um executado com os três prompts sob o mesmo modelo e parâmetros. O executor complementar das versões B V2/V3/V4 também passou a consultar o catálogo vigente, sem manter uma lista própria de casos removidos.

A matriz reserva campos humanos para fidelidade, completude, formato, linguagem, segurança, total, decisão, revisor, data, justificativa, tom e tempo até o texto utilizável. Na rodada histórica, os cinco critérios, totais, decisões, justificativas, revisor e data foram preenchidos por avaliação humana. Tom e tempo de correção não foram medidos.

## Avaliação humana já realizada

A avaliação RF13 das nove saídas históricas A/B/C foi realizada e está registrada em [avaliacao_rf13_nove_casos_pendente.csv](avaliacao_rf13_nove_casos_pendente.csv) e [revisao_humana_parte1_diego.md](revisao_humana_parte1_diego.md). Embora o nome do CSV ainda contenha `pendente`, suas colunas humanas foram posteriormente preenchidas.

| Prompt | Casos avaliados | Pontuação humana | Média | Resultado |
|---|---:|---:|---:|---|
| A | 3 | 12/30 | 4,00/10 | Duas rejeições e uma correção profunda |
| B | 3 | 21/30 | 7,00/10 | Três indicações de correção; melhor média da rodada A/B/C |
| C | 3 | 7/30 | 2,33/10 | Três rejeições |
| **Total** | **9** | **40/90** | **4,44/10** | Nenhuma aprovação direta |

O Prompt B foi selecionado para evolução e demonstração porque obteve a maior média humana entre A, B e C e apresentou menos problemas graves. Isso não significa que as três saídas históricas B tenham sido aprovadas sem ajustes: todas receberam decisão de correção.

Também houve avaliação humana da rodada independente B V4 nos mesmos três casos históricos:

- primeiro caso da rodada B V4: 9/10, adequado para demonstração com ajuste editorial;
- segundo caso da rodada B V4: 10/10, adequado para demonstração;
- terceiro caso da rodada B V4: 10/10, adequado para demonstração;
- total: 29/30, média 9,67/10.

Essas avaliações justificam historicamente a escolha do Prompt B e sua evolução até V4. Elas não devem ser transportadas como notas de `T01`, `A01`, `I01`, `X01` ou `X02`, que constituem o catálogo vigente.

Uma execução `--mock` serve para validar o encadeamento e a gravação dos artefatos, mas não permite afirmar qualidade de modelo, prompt vencedor, custo real ou taxa de aprovação. Por isso, a rodada atual foi executada com o serviço real e avaliada separadamente pela rubrica de [protocolo_avaliacao.md](protocolo_avaliacao.md).

## Avaliação A/B/C do catálogo vigente

A rodada real de `T01`, `X01` e `X02` concluiu 9/9 chamadas com Gemini `gemini-3.1-flash-lite`. A matriz bruta e as saídas estão em `resultados/experimento_prompts/real/20261018T173949951344Z/`; a avaliação consolidada está em [avaliacao_rf13_catalogo_atual.csv](avaliacao_rf13_catalogo_atual.csv).

| Prompt | Pontos | Média | Decisões |
|---|---:|---:|---|
| A | 11/30 | 3,67/10 | 3 rejeições |
| B | 22/30 | 7,33/10 | 2 correções e 1 rejeição |
| C | 16/30 | 5,33/10 | 2 correções e 1 rejeição |
| **Total** | **49/90** | **5,44/10** | Nenhuma aprovação direta |

O Prompt B foi selecionado por obter a maior média relativa e melhor tratamento de lacunas e injeção. A taxa direta de 0% mostra que a seleção de um prompt vencedor não elimina a revisão: as nove saídas apresentaram ao menos uma correção ou erro impeditivo.

## Casos multimodais (RF06–RF08)

- `A01`: o modo `--mock` usa `resultados/multimodal/referencias/referencia_audio_conferida.txt`, separada da saída avaliada. A execução real obteve WER 11,43% e CER 5,06%, com campos críticos conferidos.
- `I01`: o modo `--mock` usa `resultados/multimodal/referencias/referencia_ocr_conferida.txt`. A execução remota obteve WER 91,89% e CER 85,91%; a saída bruta foi rejeitada e os campos críticos foram corrigidos a partir da referência.
- Nos dois casos, protocolo, data e solicitante devem ser confirmados ou corrigidos por pessoa diretamente a partir do original. A extração bruta nunca é sobrescrita.

## Segurança, LGPD e revisão humana

`X01` contém uma tentativa fictícia de injeção de prompt. O detector heurístico e o prompt seguro reduzem risco, mas não garantem imunidade. `X02` verifica campos ausentes e exige o uso literal de `não localizado`, sem criar prazo, autoridade, protocolo ou procedimento.

Os arquivos de texto, áudio e imagem são declarados como fictícios para o protótipo, mas contêm campos que seriam pessoais em um cenário real. Chamadas remotas só podem usar conteúdo fictício e provedores autorizados. Consulte [lgpd.md](lgpd.md).

Toda saída de LLM é uma minuta pendente. Não há envio automático, assinatura, deferimento ou protocolo real. O arquivo `dados/revisao/decisoes_demo.yaml` contém somente decisões simuladas e fica excluído da taxa de aprovação.

O checklist de `documentacao/lgpd.md` foi marcado pela equipe como conferido. Essa marcação documenta a declaração interna, mas não transforma o protótipo em sistema autorizado para dados reais nem elimina a necessidade de revisar o pacote final de evidências antes de publicação.

## Métricas e escopos

- Avaliação humana histórica A/B/C: **9 de 9 saídas avaliadas**.
- Média humana histórica: **4,44/10**; Prompt A = **4,00**, B = **7,00**, C = **2,33**.
- Taxa de aprovação direta histórica: **0/9 = 0%**; as correções não possuem reavaliação de aprovação documentada.
- Avaliação humana B V4 histórica: **3 de 3 saídas avaliadas**, média **9,67/10**, uma condicionada a ajuste editorial.
- Avaliação RF13 A/B/C do catálogo vigente: **9 de 9 saídas avaliadas**, média **5,44/10**.
- Taxa de aprovação direta da rodada atual: **0/9 = 0%**.
- Taxa após correção: **não se aplica à rodada bruta**; as respostas avaliadas não foram sobrescritas por versões corrigidas.
- Custo da comparação A/B/C atual com serviço real: **não localizado**.
- WER de `A01`: **11,43%**; CER: **5,06%**.
- WER de `I01`: **91,89%**; CER: **85,91%**.

## Encerramento das validações

As verificações de A/B/C, RF13, WER/CER, campos críticos do OCR, audição do TTS, revisão visual e checklist acadêmico de privacidade foram consolidadas em [registro_validacoes_catalogo_atual.md](registro_validacoes_catalogo_atual.md). As saídas brutas permanecem preservadas e os resultados `mock` continuam identificados como simulação.

Essa conclusão vale para a demonstração acadêmica. Não autoriza envio ao cidadão, assinatura, deferimento, protocolo real ou uso institucional.
