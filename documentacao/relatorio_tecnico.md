# Relatório técnico — casos atuais e evidências

**Equipe:** Diego, Ayron e Guilherme. **Desafio:** FIC_DEV IA Generativa, Prático 1/2026.  
**Atualização:** 18/10/2026.

Este relatório considera somente o catálogo vigente em `dados/originais/casos.yaml`. Resultados de conjuntos substituídos não são atribuídos aos casos atuais e não participam das métricas abaixo.

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
| Texto e extração | Testes de `T01`, `X01` e `X02`; JSON estruturado e esquema | Implementado e coberto por testes locais |
| Prompts A/B/C | Código em `src/experimento.py`; execução `--mock` | Comparação real e avaliação humana dos casos atuais pendentes |
| STT | Entrada e gabarito de `A01`; processamento local implementado | O arquivo de referência configurado para `--mock` não está no repositório; referência independente e validação final pendentes |
| OCR | Entrada e gabarito de `I01`; Tesseract local executado; tentativa Gemini terminou em HTTP 503 | O arquivo de referência configurado para `--mock` não está no repositório; OCR remoto válido, CER independente e conferência final pendentes |
| Minutas | Geração local, separação entre pendente/aprovada e trilha de revisão | Nenhuma decisão YAML ou `--mock` vale como aprovação humana |
| TTS | Implementação local/Gemini e bloqueio por aprovação/hash | Execução real validada e revisão auditiva vinculada ainda pendentes |
| Imagem | Composição local e integração Cloudflare coberta por simulação | A composição local não é imagem gerada por IA; geração real e revisão pendentes |
| Auditoria | Logs JSONL, hashes e diretórios por execução | Métricas ausentes devem permanecer `não localizado` |

## Engenharia de prompts (RF02)

O experimento compara A (zero-shot), B (estruturado) e C (produzido por metaprompt). O código atual seleciona apenas entradas de modalidade texto, portanto a matriz vigente deve conter `T01`, `X01` e `X02`, cada um executado com os três prompts sob o mesmo modelo e parâmetros.

Uma execução `--mock` serve para validar o encadeamento e a gravação dos artefatos, mas não permite afirmar qualidade de modelo, prompt vencedor, custo real ou taxa de aprovação. A comparação real dos casos atuais ainda precisa ser executada e avaliada com a rubrica de [protocolo_avaliacao.md](protocolo_avaliacao.md).

## Casos multimodais (RF06–RF08)

- `A01`: o modo `--mock` aponta para `resultados/multimodal/referencias/referencia_audio_conferida.txt`, atualmente ausente. O caso falha de forma explícita até que a equipe forneça uma transcrição conferida; ela não pode ser derivada da saída avaliada.
- `I01`: o modo `--mock` aponta para `resultados/multimodal/referencias/referencia_ocr_conferida.txt`, atualmente ausente. O Tesseract apresentou limitações no conteúdo manuscrito e a tentativa Gemini terminou em HTTP 503. CER só pode ser calculada com referência independente.
- Nos dois casos, protocolo, data e solicitante devem ser confirmados ou corrigidos por pessoa diretamente a partir do original. A extração bruta nunca é sobrescrita.

## Segurança, LGPD e revisão humana

`X01` contém uma tentativa fictícia de injeção de prompt. O detector heurístico e o prompt seguro reduzem risco, mas não garantem imunidade. `X02` verifica campos ausentes e exige o uso literal de `não localizado`, sem criar prazo, autoridade, protocolo ou procedimento.

Os arquivos de texto, áudio e imagem são declarados como fictícios para o protótipo, mas contêm campos que seriam pessoais em um cenário real. Chamadas remotas só podem usar conteúdo fictício e provedores autorizados. Consulte [lgpd.md](lgpd.md).

Toda saída de LLM é uma minuta pendente. Não há envio automático, assinatura, deferimento ou protocolo real. O arquivo `dados/revisao/decisoes_demo.yaml` contém somente decisões simuladas e fica excluído da taxa de aprovação.

## Métricas atuais

- Avaliação humana RF13 dos cinco casos atuais: **não localizada**.
- Taxa de aprovação direta: **não localizada**.
- Taxa de aprovação após correção: **não localizada**.
- Custo da comparação A/B/C atual com serviço real: **não localizado**.
- WER independente de `A01`: **não localizada**.
- CER independente de `I01`: **não localizada**.

## Pendências para encerramento

1. Executar A/B/C com `T01`, `X01` e `X02` usando o mesmo modelo e parâmetros e preservar a matriz bruta.
2. Registrar notas e decisões humanas dos casos atuais com responsável, data e justificativa.
3. Produzir e versionar referências independentes para `A01` e `I01`, habilitar o lote `--mock`, recalcular WER/CER e conferir campos críticos nos originais.
4. Vincular TTS a uma minuta realmente aprovada e validar o áudio resultante.
5. Gerar e revisar uma peça visual efetivamente produzida pelo provedor de IA, mantendo proveniência distinta da composição local.
6. Concluir o checklist de privacidade, revisar logs e repetir a instalação em máquina limpa.

Nenhuma pendência autoriza envio ao cidadão ou uso institucional. Resultados `mock` continuam identificados como simulação.
