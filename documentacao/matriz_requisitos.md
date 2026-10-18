# Matriz de requisitos RF01–RF13

Estados usados (um não implica os demais): **P** planejado · **I** implementado · **S** testado com simulação (testes unitários/`--mock`) · **R** validado com serviço real · **H** validado por pessoa.
As colunas R e H só citam evidência dos casos atuais `T01`, `A01`, `I01`, `X01` e `X02`. Decisões humanas sobre as minutas e validação em máquina limpa ainda não foram realizadas.

| RF | Arquivos responsáveis | Testes | I | S | R | H | Pendência / ação concreta |
|---|---|---|:-:|:-:|:-:|:-:|---|
| RF01 Configuração | `src/main.py` (`verificar`), `config/config.yaml`, `.env.example`, `requirements.txt`, README | `test_fluxo_revisao.TestCli` | sim | sim | n/a | não | Um integrante seguir apenas o README em máquina limpa e registrar o resultado |
| RF02 Prompts A/B/C | `src/experimento.py`, `prompts/experimento/` | `test_experimento_evidencias`, `test_fluxo_revisao.TestCli` | sim | sim | não | não | Executor e código de saída cobrem falhas parciais; executar A/B/C com `T01`, `X01` e `X02` e preencher as colunas humanas sem reutilizar notas de outros conjuntos |
| RF03 Prompt seguro | `src/seguranca.py`, `prompts/sistema_minuta.md` | `test_basico`, `test_multimodal` | sim | sim | não | não | `X01` cobre a tentativa de injeção; detector por regex não é garantia e revisão humana continua obrigatória |
| RF04 API | `src/cliente.py`, `src/audio.py`, `src/imagem.py` | `test_cliente_retry`, `test_audio_visao_imagem`, `test_fluxo_revisao` | sim | sim | parcial | não | Texto e APIs multimodais têm até três tentativas para falhas transitórias; registrar uma execução atual completa e manter métricas indisponíveis como `não localizado` |
| RF05 Extração JSON | `src/extracao.py`, `src/schemas/extracao.schema.json` | `test_multimodal`, `test_basico` | sim | sim | n/a (regex local) | não | A extração por LLM foi removida por não ser exigida e por transmitir conteúdo a terceiros; a extração atual é local |
| RF06 STT | `src/audio.py`, `src/main.py`, `src/avaliacao.py` | `test_audio_visao_imagem`, `test_fluxo_revisao` | sim | sim | sim (faster-whisper local) | parcial | `A01` preserva transcrição bruta e parâmetros; produzir referência independente antes de calcular WER conclusivo |
| RF07 TTS | `src/audio.py` (`sintetizar`, `gerar_voz`), `src/main.py`, `config/config.yaml` | `test_audio_visao_imagem`, `test_fluxo_revisao`, `test_decisoes_simuladas` | sim | sim | não | parcial | TTS só pode ocorrer após aprovação humana/hash válidos; executar o provedor configurado e vincular revisor à validação auditiva |
| RF08 OCR/visão | `src/visao.py`, `src/main.py`, `src/avaliacao.py` | `test_audio_visao_imagem`, `test_fluxo_revisao` | sim | sim | parcial (Tesseract executado; Gemini retornou HTTP 503) | parcial | `I01` preserva OCR bruto e parâmetros; produzir referência independente, calcular CER e concluir a conferência dos campos críticos |
| RF09 Minuta | `src/minuta.py` | `test_basico`, `test_fluxo_revisao.TestMinutaEPrompt` | sim | sim | não | não | Registrar revisão humana das minutas atuais; compatibilidade GOV.MT não foi validada oficialmente |
| RF10 Imagem | `src/imagem.py`, `src/main.py` | `test_decisoes_simuladas`, `test_audio_visao_imagem`, `test_fluxo_revisao.TestCli` | sim | sim | não | não | A composição local possui proveniência própria; geração real pelo provedor de IA e revisão visual permanecem pendentes |
| RF11 Auditoria | `src/auditoria.py`, `src/main.py`, `src/cliente.py` | `test_basico`, `test_fluxo_revisao`, `test_cliente_retry` | sim | sim | n/a | não | `auditoria.jsonl` usa timestamp UTC e protege campos estruturais; métricas independentes e decisões humanas continuam pendentes |
| RF12 LGPD | `src/seguranca.py`, `documentacao/lgpd.md`, configuração de provedores | `test_basico`, `test_audio_visao_imagem`, `test_fluxo_revisao` | sim | sim | n/a | não | Confirmar que os originais são fictícios e concluir retenção, autorização de voz e revisão dos logs antes de chamadas remotas |
| RF13 Avaliação | `src/avaliacao.py`, `src/main.py`, `dados/gabaritos/`, `documentacao/protocolo_avaliacao.md` | `test_fluxo_revisao.TestAvaliacao`, `test_multimodal`, `test_fluxo_revisao.TestConferenciaDeCamposCriticos` | sim | sim | n/a | não | Comparação automática cobre todos os campos presentes, ausências, categoria e injeção; notas da minuta e decisões humanas reais continuam pendentes |

## Limitações conhecidas do fluxo local

- Em `--mock`, `A01` e `I01` exigem os arquivos de referência indicados em `casos.yaml`, que não estão disponíveis no repositório atual. O lote completo falha explicitamente nesses dois casos; nenhuma referência deve ser fabricada a partir da saída ou do gabarito.
- No PDF `I01`, o Tesseract não reconheceu todos os campos críticos; a tentativa Gemini terminou em HTTP 503. A conferência humana continua obrigatória.
- Decisões de `dados/revisao/decisoes_demo.yaml` e `--mock` são simulações e ficam fora da taxa de aprovação.
