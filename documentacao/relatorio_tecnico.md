# Relatório técnico — casos atuais e evidências

**Equipe:** Diego, Ayron e Guilherme. **Desafio:** FIC_DEV IA Generativa, Prático 1/2026.  
**Atualização:** 18/10/2026, após correções da auditoria técnica.

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
| Prompts A/B/C | Código em `src/experimento.py`; matriz RF13; avaliação humana histórica de nove saídas em `avaliacao_rf13_nove_casos_pendente.csv` | Avaliação histórica concluída e favorável ao Prompt B entre A/B/C; repetição com `T01`, `X01` e `X02` ainda pendente |
| Catálogo | Validação de YAML, IDs únicos, modalidades, arquivos, caminhos seguros, referências e seleção por `--caso` | Implementado; referências independentes ausentes bloqueiam explicitamente o lote multimodal `--mock` |
| STT | Entrada e gabarito de `A01`; processamento local/remoto, retentativas e preservação da transcrição bruta | O arquivo de referência configurado para `--mock` não está no repositório; referência independente e validação final pendentes |
| OCR | Entrada e gabarito de `I01`; Tesseract local executado; visão remota converte formatos aceitos para PNG | A tentativa Gemini registrada terminou em HTTP 503; referência independente, CER e conferência final pendentes |
| Minutas | Geração local, separação entre pendente/aprovada e trilha de revisão | Nenhuma decisão YAML ou `--mock` vale como aprovação humana |
| TTS | Implementação local/Gemini, retentativas, validação do MP3 e bloqueio por aprovação/hash | Falha de síntese aparece no resumo e torna a execução incompleta; validação auditiva real ainda está pendente |
| Imagem | Composição local e integração Cloudflare com retentativas, validação e proveniência | A composição local não é imagem gerada por IA; geração real e revisão pendentes |
| Auditoria | Logs JSONL, hashes, timestamps UTC e diretórios por execução | Campos estruturais são protegidos contra sobrescrita; métricas ausentes permanecem `não localizado` |

## Verificação técnica após a auditoria

Em 18/10/2026, foram executadas verificações locais sem chamadas externas:

- `python -m unittest discover -s testes -t .`: **112 testes aprovados**;
- `python -m src.main verificar`: concluído, com envio automático desabilitado;
- `python -m src.main --mock --caso T01 --decisoes dados/revisao/decisoes_demo.yaml`: concluído com sucesso e decisão identificada como simulada;
- lote `--mock` completo: interrompido corretamente porque as referências independentes declaradas para `A01` e `I01` ainda não existem.

Os testes cobrem, entre outros pontos, propagação de falhas do experimento e do TTS, retentativas transitórias, rejeição de conteúdo TTS que não seja MP3, conversão TIFF para PNG, validação do catálogo, IDs desconhecidos, timestamps UTC e comparação dos elementos presentes nos gabaritos.

A aprovação da suíte comprova o comportamento implementado em ambiente controlado. Ela não substitui execução real dos provedores, inspeção auditiva/visual, validação em máquina limpa ou revisão humana dos casos vigentes.

## Provedores, modelos e custos

| Etapa | Provedor/modelo configurado | Parâmetros principais | Evidência atual | Custo medido | Justificativa/limite |
|---|---|---|---|---|---|
| Minuta e experimento A/B/C | Gemini / `gemini-3.1-flash-lite` | temperatura 0,2; máximo 2.400 tokens; timeout 45 s | Implementação e simulação; rodada real atual pendente | `não localizado` | Mesmo modelo e parâmetros devem ser mantidos entre A, B e C |
| STT | Groq / `whisper-large-v3-turbo`; alternativa local `faster-whisper` | idioma português; timeout 120 s | Execução e validação independente de `A01` pendentes | `não localizado` | O padrão remoto envia o áudio integral; a alternativa local reduz exposição |
| OCR/visão | Gemini / `gemini-3.8-flash`; alternativa Tesseract | até 3 páginas; Tesseract 300 dpi/PSM 6 | Tesseract parcial; tentativa Gemini HTTP 503 | `não localizado` | Campos críticos continuam sujeitos a conferência no original |
| TTS | Gemini / `gemini-3.8-flash-lite-tts`; alternativa eSpeak | voz `Kore`; tom institucional; limite 3.500 caracteres | Integração simulada; execução e audição humanas pendentes | `não localizado` | Só é acionado depois de aprovação humana válida e hash correspondente |
| Imagem | Cloudflare / `@cf/black-forest-labs/flux-1-schnell`; alternativa Pillow | 4 etapas; prompt versionado | Integração simulada; geração real pendente | `não localizado` | Pillow é composição programática e não satisfaz sozinho a exigência de IA |

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

Uma execução `--mock` serve para validar o encadeamento e a gravação dos artefatos, mas não permite afirmar qualidade de modelo, prompt vencedor, custo real ou taxa de aprovação. A comparação real dos casos atuais ainda precisa ser executada e avaliada com a rubrica de [protocolo_avaliacao.md](protocolo_avaliacao.md).

## Casos multimodais (RF06–RF08)

- `A01`: o modo `--mock` aponta para `resultados/multimodal/referencias/referencia_audio_conferida.txt`, atualmente ausente. O caso falha de forma explícita até que a equipe forneça uma transcrição conferida; ela não pode ser derivada da saída avaliada.
- `I01`: o modo `--mock` aponta para `resultados/multimodal/referencias/referencia_ocr_conferida.txt`, atualmente ausente. O Tesseract apresentou limitações no conteúdo manuscrito e a tentativa Gemini terminou em HTTP 503. CER só pode ser calculada com referência independente.
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
- Avaliação humana RF13 do catálogo vigente: **não localizada**.
- Taxa de aprovação direta do catálogo vigente: **não localizada**.
- Taxa de aprovação após correção: **não localizada**.
- Custo da comparação A/B/C atual com serviço real: **não localizado**.
- WER independente de `A01`: **não localizada**.
- CER independente de `I01`: **não localizada**.

## Pendências para encerramento

1. Repetir A/B/C com `T01`, `X01` e `X02` usando o mesmo modelo e parâmetros, preservando a matriz bruta sem substituir a avaliação histórica.
2. Registrar notas e decisões humanas dos casos atuais com responsável, data e justificativa; a avaliação histórica já realizada permanece válida somente para seu próprio conjunto.
3. Produzir e versionar referências independentes para `A01` e `I01`, habilitar o lote `--mock`, recalcular WER/CER e conferir campos críticos nos originais.
4. Vincular TTS a uma minuta realmente aprovada e validar o áudio resultante.
5. Gerar e revisar uma peça visual efetivamente produzida pelo provedor de IA, mantendo proveniência distinta da composição local.
6. Preservar a comprovação do checklist de privacidade, revisar o pacote final de logs e repetir a instalação em máquina limpa.

Nenhuma pendência autoriza envio ao cidadão ou uso institucional. Resultados `mock` continuam identificados como simulação.
