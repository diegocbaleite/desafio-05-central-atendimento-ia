# Matriz de requisitos RF01–RF13

## Migração de provedor em 28/10/2026

O padrão agora é OpenAI. A tabela consolidada abaixo preserva as evidências anteriores e não comprova validação dos novos modelos. Detalhes e execução: [integração OpenAI](integracao_openai.md).

| Requisito | Arquivos/teste adicional | Estado OpenAI | Pendência |
|---|---|---|---|
| RF01/RF04/RF11 | `config/config.yaml`, `.env.example`, `src/cliente.py`, `src/main.py`, `testes/test_openai.py` | Implementado, simulado e catálogo real consultado | Concluir validação dos endpoints multimodais |
| RF02/RF09 | `src/experimento_b_v2_real.py`, metadados X02 da rodada `20261028T172001971412Z` | Uma chamada real com B V4 concluída; revisão humana pendente | Avaliar fidelidade e uso literal de `não localizado`; não refizemos A/B/C |
| RF06/RF08 | `src/audio.py`, `src/visao.py`, `testes/test_openai.py` | Implementado e simulado | STT/OCR reais, referências e conferência humana |
| RF07/RF10 | `src/audio.py`, `src/imagem.py`, `testes/test_openai.py` | Implementado e simulado | Aprovação real da minuta antes do TTS; geração e audição/inspeção visual |

## Evidências consolidadas anteriores à migração

Estados usados (um não implica os demais): **P** planejado · **I** implementado · **S** testado com simulação (testes unitários/`--mock`) · **R** validado com serviço real · **H** validado por pessoa.
As colunas R e H só citam evidência dos casos atuais `T01`, `A01`, `I01`, `X01` e `X02`. O fluxo real e o mecanismo de decisão humana foram exercitados; validações marcadas como parciais ainda exigem registros humanos específicos, e a validação em máquina limpa não foi realizada.

| RF | Arquivos responsáveis | Testes | I | S | R | H | Resultado / limite |
|---|---|---|:-:|:-:|:-:|:-:|---|
| RF01 Configuração | `src/main.py` (`verificar`), `config/config.yaml`, `.env.example`, `requirements.txt`, README | `test_fluxo_revisao.TestCli` | sim | sim | n/a | não | Um integrante seguir apenas o README em máquina limpa e registrar o resultado |
| RF02 Prompts A/B/C | `src/experimento.py`, `prompts/experimento/` | `test_experimento_evidencias`, `test_fluxo_revisao.TestCli` | sim | sim | sim | sim | Rodada atual concluída com 9/9 chamadas e avaliação RF13; Prompt B obteve a maior média relativa (7,33/10) |
| RF03 Prompt seguro | `src/seguranca.py`, `prompts/sistema_minuta.md` | `test_basico`, `test_multimodal` | sim | sim | não | não | `X01` cobre a tentativa de injeção; detector por regex não é garantia e revisão humana continua obrigatória |
| RF04 API | `src/cliente.py`, `src/audio.py`, `src/imagem.py` | `test_cliente_retry`, `test_audio_visao_imagem`, `test_fluxo_revisao` | sim | sim | sim | parcial | Fluxo atual executado com APIs de texto, STT, OCR, TTS e imagem; manter métricas indisponíveis como `não localizado` e concluir as inspeções humanas específicas |
| RF05 Extração JSON | `src/extracao.py`, `src/schemas/extracao.schema.json` | `test_multimodal`, `test_basico` | sim | sim | n/a (regex local) | não | A extração por LLM foi removida por não ser exigida e por transmitir conteúdo a terceiros; a extração atual é local |
| RF06 STT | `src/audio.py`, `src/main.py`, `src/avaliacao.py` | `test_audio_visao_imagem`, `test_fluxo_revisao` | sim | sim | sim | parcial | `A01` possui execução real, transcrição bruta, referência conferida e conferência de campos críticos; consolidar WER/CER |
| RF07 TTS | `src/audio.py` (`sintetizar`, `gerar_voz`), `src/main.py`, `config/config.yaml` | `test_audio_visao_imagem`, `test_fluxo_revisao`, `test_decisoes_simuladas` | sim | sim | sim | sim | Gemini TTS gerou WAV vinculado ao hash da minuta; audição registrada como adequada à demonstração |
| RF08 OCR/visão | `src/visao.py`, `src/main.py`, `src/avaliacao.py` | `test_audio_visao_imagem`, `test_fluxo_revisao` | sim | sim | sim | sim | `I01` avaliado com WER 91,89% e CER 85,91%; saída bruta rejeitada e campos críticos corrigidos pela referência |
| RF09 Minuta | `src/minuta.py` | `test_basico`, `test_fluxo_revisao.TestMinutaEPrompt` | sim | sim | sim | sim | Minutas e avaliação RF13 atual registradas; compatibilidade GOV.MT não foi validada oficialmente |
| RF10 Imagem | `src/imagem.py`, `src/main.py` | `test_decisoes_simuladas`, `test_audio_visao_imagem`, `test_fluxo_revisao.TestCli` | sim | sim | sim | sim | Cloudflare/FLUX gerou peça com proveniência e revisão visual aprovada para demonstração; uso oficial permanece desabilitado |
| RF11 Auditoria | `src/auditoria.py`, `src/main.py`, `src/cliente.py` | `test_basico`, `test_fluxo_revisao`, `test_cliente_retry` | sim | sim | n/a | sim | Logs, hashes, timestamps, métricas e registros consolidados verificados; campos indisponíveis permanecem `não localizado` |
| RF12 LGPD | `src/seguranca.py`, `documentacao/lgpd.md`, configuração de provedores | `test_basico`, `test_audio_visao_imagem`, `test_fluxo_revisao` | sim | sim | n/a | sim (protótipo) | Checklist acadêmico concluído; repetir inspeção do pacote final e realizar avaliação jurídica/contratual antes de qualquer implantação real |
| RF13 Avaliação | `src/avaliacao.py`, `src/main.py`, `dados/gabaritos/`, `documentacao/protocolo_avaliacao.md` | `test_fluxo_revisao.TestAvaliacao`, `test_multimodal`, `test_fluxo_revisao.TestConferenciaDeCamposCriticos` | sim | sim | n/a | sim | 9/9 saídas atuais avaliadas; média 5,44/10 e aprovação direta 0%, com justificativas preservadas |

## Limitações conhecidas do fluxo local

- Em `--mock`, `A01` e `I01` usam os arquivos de referência conferidos indicados em `casos.yaml`; o lote completo foi validado com os cinco casos. As referências permanecem separadas das saídas e dos gabaritos.
- No PDF `I01`, o Tesseract não reconheceu todos os campos críticos. Após uma tentativa Gemini com HTTP 503, houve execução remota concluída, mas com divergências críticas; a correção humana continua obrigatória.
- Decisões de `dados/revisao/decisoes_demo.yaml` e `--mock` são simulações e ficam fora da taxa de aprovação.
