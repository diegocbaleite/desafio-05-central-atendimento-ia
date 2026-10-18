# Matriz de requisitos RF01–RF13

Estados usados (um não implica os demais): **P** planejado · **I** implementado · **S** testado com simulação (testes unitários/`--mock`) · **R** validado com serviço real · **H** validado por pessoa.
As colunas R e H só citam evidência existente no repositório; o que consta apenas como relato da equipe está identificado. Última verificação automática desta matriz: 64 testes unitários aprovados e fluxo `--mock` executado em 17/10/2026 (Windows, Python 3.14.6).

| RF | Arquivos responsáveis | Testes | I | S | R | H | Pendência / ação concreta |
|---|---|---|:-:|:-:|:-:|:-:|---|
| RF01 Configuração | `src/main.py` (`verificar`), `config/config.yaml`, `.env.example`, `requirements.txt`, README | `test_fluxo_revisao.TestCli` | sim | sim | n/a | não | Um integrante seguir apenas o README em máquina limpa e registrar o resultado |
| RF02 Prompts A/B/C | `src/experimento.py`, `prompts/experimento/` | `test_experimento_evidencias` | sim | sim | sim (9/9 chamadas, `resultados/experimento_prompts/real/`) | não | Notas são de análise assistida por IA; preencher colunas `*_humano` da matriz. As entradas C01/C05/C06 dessa rodada eram sintéticas e hoje estão em `testes/fixtures/` (`completa.txt`, `injecao.txt`, `lacunas.txt`, cópias do commit anterior) |
| RF03 Prompt seguro | `src/seguranca.py`, `prompts/sistema_minuta.md` | `test_basico`, `test_multimodal` | sim | sim | relatado (C05 no relatório técnico) | não | Detector por regex não é garantia; revisão humana é a barreira |
| RF04 API | `src/cliente.py` | `test_cliente_retry`, `test_fluxo_revisao` | sim | sim | relatado (OpenRouter; 429/502 observados) | não | Custo por chamada é **não localizado** (modelo gratuito sem custo reportado) |
| RF05 Extração JSON | `src/extracao.py`, `src/schemas/extracao.schema.json` | `test_multimodal`, `test_basico` | sim | sim | n/a (regex local) | não | A extração por LLM (módulo `extracao_llm` e comando `arquivos`) foi removida por não ser exigida pelo desafio e por enviar originais a terceiros |
| RF06 STT | `src/audio.py`, `src/avaliacao.py` | `test_audio_visao_imagem` | sim | sim | sim (faster-whisper local, `resultados/multimodal/stt_*`) | parcial | WER 0% usa referência derivada da saída do modelo (`REGISTRO_DE_CONFERENCIA_AUDIO.md`); produzir referência independente |
| RF07 TTS | `src/audio.py` (`sintetizar`, `gerar_voz`) | `test_audio_visao_imagem`, `test_fluxo_revisao` | sim | sim | sim (eSpeak local, `resultados/multimodal/tts_*`) | sim (`VALIDACAO_AUDITIVA.txt`) | Limitação registrada: voz robótica |
| RF08 OCR/visão | `src/visao.py`, `src/avaliacao.py` | `test_audio_visao_imagem`, `test_fluxo_revisao` | sim | sim | sim (Tesseract local) | parcial (14 valores conferidos) | O OCR não lê os campos manuscritos de I01; referência e revisão vêm da mesma transcrição (CER 0 não é independente) |
| RF09 Minuta | `src/minuta.py` | `test_basico`, `test_fluxo_revisao.TestMinutaEPrompt` | sim | sim | relatado | não | Timbre citado, compatibilidade GOV.MT **não validada** oficialmente |
| RF10 Imagem | `src/imagem.py` | `test_decisoes_simuladas`, `test_audio_visao_imagem` | sim | sim | **não** | não | Gerar imagem por IA (OpenAI) com chave autorizada e registrar proveniência; composição Pillow não é IA |
| RF11 Auditoria | `src/auditoria.py`, `src/main.py` | `test_fluxo_revisao` | sim | sim | n/a | não | Auditoria registra revisor, justificativa, versão, SHA-256 da minuta e hash do prompt |
| RF12 LGPD | `src/seguranca.py` (`minimizar`, `validar_arquivo`), `documentacao/lgpd.md`, trava `--autorizar-api` em áudio/voz/arte | `test_basico`, `test_audio_visao_imagem`, `test_fluxo_revisao` | sim | sim | n/a | não | Confirmar por escrito que todo o material de `dados/originais/` é fictício; concluir itens abertos do checklist |
| RF13 Avaliação | `src/avaliacao.py`, `dados/gabaritos/`, `documentacao/protocolo_avaliacao.md` | `test_fluxo_revisao.TestAvaliacao`, `test_multimodal` | sim | sim | n/a | **não** | Sem decisão humana real a taxa de aprovação é **não calculada**; registrar ao menos um caso aprovado e um rejeitado/corrigido por pessoa |

## Limitações conhecidas do fluxo local (verificadas em 17/10/2026)
- Em `--mock`, A01 usa a transcrição de referência (texto conferido por pessoa) e I01 usa OCR real; a data falada por extenso em A01 não é normalizada e a extração marca `data_solicitacao` como `não localizado` (divergência corretamente apontada contra o gabarito).
- No PDF I01 o OCR local não reconheceu protocolo, solicitante, data, assunto nem pedido; a conferência humana de campos críticos é obrigatória antes da minuta.
- Decisões de `dados/revisao/decisoes_demo.yaml` e `--mock` são simulações e ficam fora da taxa de aprovação.
