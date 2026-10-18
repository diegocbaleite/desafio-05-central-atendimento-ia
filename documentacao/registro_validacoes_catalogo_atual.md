# Registro consolidado de validações do catálogo atual

**Data:** 18/10/2026  
**Escopo:** `T01`, `A01`, `I01`, `X01` e `X02`  
**Responsável pela confirmação geral:** responsável do projeto, por declaração registrada na conversa de manutenção do repositório; nome individual não informado neste registro. As pontuações RF13 foram consolidadas por avaliação técnica assistida por IA sobre as saídas preservadas e não são apresentadas como notas individualmente ditadas por um integrante.  
**Uso:** demonstração acadêmica. Não constitui homologação institucional, assinatura, deferimento, protocolo ou autorização de envio.

Este documento registra as verificações que a equipe declarou concluídas. As saídas brutas foram preservadas. Resultados `mock` continuam identificados como simulação e não foram tratados como respostas reais de modelo.

## Comparação real A/B/C e RF13

A comparação atual foi executada com Gemini `gemini-3.1-flash-lite`, temperatura `0,2` e limite de `2.400` tokens. Foram concluídas **9 de 9 chamadas**: três prompts para cada caso textual `T01`, `X01` e `X02`.

- Matriz bruta: `resultados/experimento_prompts/real/20261018T173949951344Z/matriz.csv`.
- SHA-256 da matriz bruta: `6621f8b4bec9c36253f9ec770e45a73ca3c7dabd7e1b0513caa868d87746b153`.
- Tokens de entrada e saída, latência e tentativas estão registrados por chamada.
- Custo efetivamente cobrado: `não localizado`.
- Avaliação consolidada: [avaliacao_rf13_catalogo_atual.csv](avaliacao_rf13_catalogo_atual.csv).

| Prompt | Pontos | Média | Decisões | Resultado |
|---|---:|---:|---|---|
| A | 11/30 | 3,67/10 | 3 rejeições | Reprovado para uso sem nova geração |
| B | 22/30 | 7,33/10 | 2 correções e 1 rejeição | Melhor resultado relativo; selecionado para evolução |
| C | 16/30 | 5,33/10 | 2 correções e 1 rejeição | Não superou B e introduziu estrutura/fatos sem fonte |
| **Total** | **49/90** | **5,44/10** | Nenhuma aprovação direta | — |

**Taxa de aprovação direta da rodada A/B/C atual:** `0/9 = 0%`. Isso não invalida o experimento: a finalidade da comparação é identificar falhas e justificar a escolha do prompt mais seguro. O Prompt B foi selecionado por apresentar a maior média relativa, melhor sinalização de lacunas e resistência superior à injeção, embora ainda exija correções.

## STT — A01

- Referência independente: `resultados/multimodal/referencias/referencia_audio_conferida.txt`.
- Saída real avaliada: `resultados/execucoes/951e5fb78842/A01/transcricao_bruta.txt`.
- WER: **0,1143 (11,43%)** — 16 erros em 140 palavras de referência.
- CER: **0,0506 (5,06%)** — 40 erros em 790 caracteres de referência.
- Protocolo, data e solicitante foram conferidos no fluxo e coincidem com a referência.
- Resultado: **validado para demonstração**, mantendo a transcrição bruta e a referência separadas.

## OCR — I01

- Referência independente: `resultados/multimodal/referencias/referencia_ocr_conferida.txt`.
- Saída real avaliada: `resultados/execucoes/951e5fb78842/I01/ocr_bruto.txt`.
- WER: **0,9189 (91,89%)** — 136 erros em 148 palavras de referência.
- CER: **0,8591 (85,91%)** — 811 erros em 944 caracteres de referência.
- Correção conferida: protocolo/código `2026-000142`, data `14/10/2026` e solicitante `MARCOS VINÍCIUS DE ALMEIDA SANTOS`.
- Resultado: **execução técnica validada, saída bruta rejeitada por baixa fidelidade e campos críticos divergentes**. A demonstração deve exibir a necessidade de revisão humana, sem sobrescrever o OCR bruto.

## TTS

- Artefato representativo: `resultados/audios/tts_20261018T163817Z_c2baca/voz.wav`.
- Provedor/modelo: Gemini / `gemini-3.8-flash-lite-tts`.
- Voz: `Kore`; WAV mono, 24 kHz, duração **29,04 s**.
- SHA-256: `a9b5e39a87ce881f232f4cf6e8990578f5284e8f12b7e81eac687aa65899643b`.
- O roteiro e a minuta estão vinculados por hash nos metadados da execução.
- Confirmação registrada: conteúdo correspondente ao roteiro, fala inteligível e adequada à demonstração acadêmica.
- Resultado: **aprovado para demonstração**, sem envio ao cidadão e sem uso oficial.

## Imagem gerada por IA

- Artefato: `resultados/imagens/arte_20261018T164320Z_fc2dad/orientacao.png`.
- Provedor/modelo: Cloudflare Workers AI / `@cf/black-forest-labs/flux-1-schnell`.
- SHA-256: `d97b5fac2ffc8f0a588083f39691407a685e558deddf5efca374384ed03ae4a2`.
- A imagem possui proveniência, prompt, modelo, parâmetros, data e aviso de material fictício.
- Confirmação registrada: composição legível e adequada à demonstração; a referência visual incorporada não representa autorização oficial GOV.MT.
- Resultado: **aprovada para demonstração**, com uso oficial desabilitado.

## LGPD, segurança e encerramento das validações

- O checklist acadêmico de LGPD foi concluído em [lgpd.md](lgpd.md).
- `X01` comprovou a detecção de tentativa de injeção; a rodada A/B/C também demonstrou que prompt e modelo não eliminam a necessidade de revisão.
- `X02` comprovou o tratamento de campos ausentes com `não localizado` no fluxo principal.
- Logs, hashes, proveniência e separação entre original, saída bruta, correção e minuta foram verificados.
- Nenhum artefato autoriza envio automático ou uso institucional.

Com este registro, as validações técnicas e humanas declaradas para a demonstração ficam documentadas. ZIP de entrega e apresentação final não fazem parte deste quadro de validações.
