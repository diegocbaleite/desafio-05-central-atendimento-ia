# Roteiro de pitch — Central Inteligente de Atendimento

**Duração total:** 12 minutos.

O roteiro está dividido em seis blocos. As falas podem ser distribuídas livremente entre as pessoas responsáveis pela apresentação.

## 1. Problema, arquitetura, ferramentas e modelos — 0:00 a 2:00

### Fala

> Órgãos públicos recebem solicitações por texto, áudio e documentos digitalizados. O trabalho não consiste apenas em responder: é necessário identificar corretamente o pedido, preservar os dados recebidos, evitar informações inventadas e garantir revisão humana antes de qualquer comunicação.
>
> Para apoiar esse processo, desenvolvemos a Central Inteligente de Atendimento e Comunicação Institucional, um protótipo educacional em Python. A aplicação recebe conteúdo fictício, realiza transcrição ou OCR quando necessário, extrai campos estruturados, classifica a demanda, gera uma minuta e registra toda a execução.
>
> A arquitetura segue este fluxo: entrada, STT ou OCR, extração estruturada, classificação, geração da minuta, revisão humana e, somente depois de aprovação válida, síntese de voz.
>
> Para texto e geração de minutas, a configuração utiliza Gemini. Para áudio, há Groq com Whisper e uma alternativa local com `faster-whisper`. Para OCR, usamos Tesseract local ou visão Gemini. Para síntese de voz, há Gemini TTS ou eSpeak. Para a peça visual, usamos Cloudflare com FLUX ou uma composição local com Pillow.
>
> As escolhas priorizam baixo acoplamento, alternativas locais, rastreabilidade e separação clara entre execução real e simulação.

```text
Texto ────────────────┐
Áudio → STT ──────────┼→ Extração → Classificação → Minuta → Revisão humana
Imagem/PDF → OCR ─────┘                                      ↓
                                                        TTS e evidências
```

## 2. Experimento dos três prompts — 2:00 a 4:00

### Slide sugerido

| Prompt | Estratégia | Característica |
|---|---|---|
| A | Zero-shot | Instrução curta e direta |
| B | Estruturado | Regras explícitas de formato, segurança e lacunas |
| C | Metaprompt | Prompt produzido a partir de critérios definidos |

### Fala

> Para comparar estratégias de engenharia de prompts, criamos um experimento controlado com três versões.
>
> O Prompt A representa uma abordagem zero-shot, com instruções mínimas. O Prompt B é estruturado e explicita o formato da minuta, o tratamento de campos ausentes e as proibições contra invenção de fatos. O Prompt C é produzido por um metaprompt, que transforma requisitos em instruções operacionais.
>
> Os três prompts devem usar as mesmas entradas textuais — `T01`, `X01` e `X02` —, o mesmo modelo e os mesmos parâmetros. A matriz registra latência, tokens, custo quando informado e os cinco critérios humanos: fidelidade, completude, formato, linguagem e segurança.
>
> A avaliação humana da rodada histórica analisou nove saídas: três casos com cada um dos prompts. O Prompt A obteve média 4,00; o Prompt B, 7,00; e o Prompt C, 2,33. Nenhuma das nove saídas teve aprovação direta, mas o Prompt B apresentou a maior média e menos problemas graves, por isso foi selecionado para evolução.
>
> Depois dos ajustes, a rodada B V4 também recebeu avaliação humana: 9 de 10 no primeiro caso e 10 de 10 nos outros dois, com média 9,67. O primeiro caso ficou condicionado a um ajuste editorial.
>
> Assim, a escolha do Prompt B é sustentada pela avaliação humana histórica e também por sua estrutura explícita, separação entre instrução e conteúdo externo, uso de `não localizado` e proibição de inventar protocolo, prazo ou decisão administrativa.
>
> O limite é que essas notas pertencem ao catálogo histórico. A repetição com os casos atuais `T01`, `X01` e `X02` continua necessária; resultados `mock` não medem qualidade de modelo.

## 3. Demonstração de texto, áudio e visão/OCR — 4:00 a 7:00

### Preparação

Deixar o terminal, o catálogo de casos e exemplos de artefatos previamente abertos. Não depender de chamadas externas durante a apresentação.

### Texto — aproximadamente 1 minuto

Executar:

```powershell
python -m src.main --mock --caso T01 --decisoes dados/revisao/decisoes_demo.yaml
```
> Explicar no começo que o comando padrão é ```python -m src.main``` que executa com as apis, os comanos executados são apenas para testes.

> No fluxo textual, usamos o caso fictício `T01`. O sistema lê a entrada sem modificar o original, extrai protocolo, data, solicitante, assunto e pedido, classifica a demanda e compara o resultado com o gabarito preparado anteriormente.
>
> Como esta é uma execução `mock`, a decisão do YAML aparece como simulada, não representa aprovação humana e não entra na taxa de aprovação.

Destacar na saída:

- categoria extraída;
- avaliação contra o gabarito;
- `execucao_mock: true`;
- `decisao_simulada: true`;
- `taxa_aprovacao_direta: null`.

### Áudio — aproximadamente 1 minuto

Mostrar `dados/originais/entrada_audio.mp3` e o comando:

```powershell
python -m src.main audio dados/originais/entrada_audio.mp3 --provider local
```

> No caso `A01`, o áudio passa pelo reconhecimento de fala. A transcrição bruta é preservada em arquivo separado, junto com provedor, modelo, duração e hash do original.
>
> O sistema não corrige automaticamente a transcrição. Protocolo, data e solicitante precisam ser conferidos por uma pessoa diretamente no áudio original.
>
> A referência independente necessária para calcular WER conclusivo ainda está pendente. Portanto, não apresentamos uma métrica inventada.

### Visão/OCR — aproximadamente 1 minuto

Mostrar `dados/originais/entrada_pdf-imagem.pdf` e o comando:

```powershell
python -m src.main ocr dados/originais/entrada_pdf-imagem.pdf --provider local
```

> No caso `I01`, o PDF é renderizado e processado por OCR. O texto bruto e os trechos de baixa confiança são preservados, sem alteração do documento original.
>
> Tesseract está disponível como alternativa local. A visão Gemini também está implementada, mas a tentativa registrada terminou em erro HTTP 503. A referência independente para calcular CER e a conferência humana final permanecem pendentes.

## 4. Minuta, síntese de voz e imagem — 7:00 a 9:00

### Slide sugerido

```text
Extração → MINUTA — NÃO ENVIADA → decisão humana
                                      ├→ rejeitar/corrigir
                                      └→ aprovar → TTS
```

### Fala

> Depois da extração, o sistema gera uma minuta marcada como “NÃO ENVIADA”. Ela utiliza apenas os dados disponíveis e apresenta `não localizado` quando uma informação não consta na fonte.
>
> A pessoa revisora pode aprovar, rejeitar, corrigir ou solicitar uma nova versão. Uma aprovação real exige responsável, justificativa, data e hash da minuta. Decisões de YAML e execuções `mock` nunca são tratadas como aprovação humana.
>
> Somente depois dessa aprovação o sistema permite gerar uma versão falada. O TTS registra voz, instruções de entonação, hash do roteiro e arquivo produzido. Se a síntese falhar, a falha aparece no resumo e a execução termina como incompleta.
>
> A aplicação também produz uma peça visual. Com Pillow, o resultado é rotulado como composição programática sem IA. Com Cloudflare e FLUX, a proveniência registra o modelo, o prompt, a data e o uso de IA. A geração real e a revisão visual ainda precisam ser concluídas.

Comandos de referência:

```powershell
python -m src.main voz <minuta_aprovada.md> --revisao <revisao.json>
python -m src.main arte --provider local --referencia dados/originais/brasao.png
```

Não executar o comando `voz` sem uma aprovação humana válida.

## 5. Testes, segurança, falhas, LGPD e revisão humana — 9:00 a 11:00

### Slide sugerido

- 112 testes automatizados aprovados;
- dados fictícios e credenciais fora do Git;
- prompt injection tratada como dado;
- revisão humana obrigatória;
- nenhum envio automático.

### Fala

> A suíte possui 112 testes automatizados aprovados. Ela cobre extração, catálogo, decisões simuladas, auditoria, retentativas, validação de áudio, conversão de imagens e propagação de falhas.
>
> O caso `X01` contém uma tentativa fictícia de prompt injection. A entrada externa é isolada das instruções do sistema e tratada como dado não confiável. O detector é apenas uma camada adicional e não substitui revisão humana.
>
> O caso `X02` verifica campos ausentes. Nessas situações, a aplicação utiliza `não localizado` e não cria leis, prazos, números ou autoridades.
>
> As APIs possuem timeout e até três tentativas para falhas transitórias. Erros de experimento, TTS, imagem, catálogo e referências são propagados para o código de saída, evitando apresentar uma execução incompleta como sucesso.
>
> Para LGPD, usamos somente dados declarados como fictícios, mantemos credenciais fora do Git e não registramos tokens. Áudio e imagem podem ser enviados integralmente aos provedores remotos, por isso qualquer uso externo exige confirmação prévia do conteúdo e do provedor.
>
> Não existe envio por e-mail, WhatsApp, assinatura, protocolo ou deferimento automático. Toda saída de modelo é uma minuta pendente de revisão humana.

## 6. Limitações, custos, uso de IA e melhorias — 11:00 a 12:00

### Fala

> As principais limitações são a ausência das referências independentes de áudio e OCR, a revalidação dos prompts com o catálogo atual, a validação auditiva do TTS e a revisão de uma imagem efetivamente gerada por IA.
>
> Em 18 de outubro de 2026, o Gemini 3.1 Flash-Lite custava US$ 0,25 por milhão de tokens de entrada e US$ 1,50 de saída. O Gemini 3.8 Flash custava US$ 0,75 de entrada e US$ 3,75 de saída. No TTS, eram US$ 0,50 para texto e US$ 6 para áudio, também por milhão de tokens.
>
> O Whisper da Groq cobra US$ 0,04 por hora de áudio; o FLUX da Cloudflare cobra por bloco e etapa; e o Nemotron histórico usa um endpoint gratuito com limites. São tarifas públicas, não custos medidos: valores ausentes continuam como `não localizado`.
>
> O uso de IA está documentado. Como melhorias, propomos revalidar os casos atuais, medir WER e CER e preparar evidências higienizadas.
>
> Para executar o fluxo principal com as APIs configuradas, o comando é `python -m src.main`. Ele deve ser usado somente com dados fictícios, credenciais autorizadas e revisão humana. Obrigado.

### Tabela de apoio para o slide de custos

| Modelo/serviço | Preço público em 18/10/2026 |
|---|---|
| Gemini 3.1 Flash-Lite | US$ 0,25 entrada / US$ 1,50 saída por 1 milhão de tokens |
| Gemini 3.8 Flash | US$ 0,75 entrada / US$ 3,75 saída por 1 milhão de tokens até 31/12/2026 |
| Gemini 3.8 Flash-Lite TTS | US$ 0,50 texto / US$ 6,00 áudio por 1 milhão de tokens até 31/12/2026 |
| Groq Whisper Large V3 Turbo | US$ 0,04 por hora de áudio |
| Cloudflare FLUX.1 schnell | US$ 0,0000528 por bloco 512×512 + US$ 0,0001056 por etapa |
| OpenRouter Nemotron `:free` | US$ 0,00 por 1 milhão de tokens; sujeito a limites |
| Ferramentas locais | Sem tarifa de API; infraestrutura não medida |

Fontes: [Gemini](https://ai.google.dev/gemini-api/docs/pricing), [Gemini 3.8 Flash](https://ai.google.dev/gemini-api/docs/latest-model), [Groq](https://console.groq.com/docs/model/whisper-large-v3-turbo), [Cloudflare](https://developers.cloudflare.com/workers-ai/platform/pricing/) e [OpenRouter](https://openrouter.ai/nvidia/nemotron-3-super-120b-a12b%3Afree/pricing).

## Plano de contingência

Se uma demonstração local demorar ou falhar, usar capturas previamente revisadas de:

1. verificação do ambiente;
2. execução textual `T01` em modo `mock`;
3. JSON de extração;
4. transcrição bruta de áudio;
5. OCR bruto e trechos incertos;
6. minuta marcada como “NÃO ENVIADA”;
7. registro de auditoria e proveniência da imagem.

Não executar APIs remotas durante o pitch. Isso evita dependência de rede, consumo de cota e exposição acidental de conteúdo.
