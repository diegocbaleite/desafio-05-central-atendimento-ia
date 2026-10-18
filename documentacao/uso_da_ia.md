# Registro transparente do uso de IA no desenvolvimento

**Equipe:** Diego, Ayron, Guilherme.

## Ferramentas e modelos
- ChatGPT (OpenAI), assistente de programação/documentação — modelo disponibilizado na conversa: **GPT-6**.
- Assistente de codificação integrado ao VS Code (Copilot SDK), usado em 17/10/2026 para auditoria, ajustes de código, testes e documentação — **versão/modelo não exposta ao assistente; preencher se a equipe souber**.
- Modelo com evidência de chamadas reais no experimento A/B/C: OpenRouter / `nvidia/nemotron-3-super-120b-a12b:free`.
- Multimodal: STT local com faster-whisper registrado; Groq / `whisper-large-v3-turbo` está configurado, sem nova execução real comprovada nesta revisão. Gemini / `gemini-3.8-flash` está configurado para OCR, mas a tentativa de 18/10/2026 falhou com HTTP 503. Gemini / `gemini-3.8-flash-lite-tts` está configurado para TTS nativo em WAV, com integração coberta por simulação e execução real ainda pendente. Cloudflare / `@cf/black-forest-labs/flux-1-schnell` foi testado apenas com simulação.
- Resultados `mock` não são resultados de modelo generativo real.

## Solicitações relevantes feitas à IA
1. Planejar e implementar o protótipo multimodal do Desafio Prático 1, com LGPD, 12h e revisão humana.
2. Estruturar o GitHub como o repositório `desafio-03-pipeline-recomendacao`.
3. Criar repositório atualizado e identificar equipe como Diego, Ayron e Guilherme.
4. Auditar o projeto contra o PDF do desafio (17/10/2026) e executar o sistema para testar; relatório em `auditorias/`.
5. Ler o PDF do desafio e as diretrizes do agente e ajustar o projeto (17/10/2026): revisão humana com responsável/justificativa/hash/versão, conferência de campos críticos, bloqueio de envio remoto sem autorização, gabaritos e casos para o material fornecido, matriz de requisitos.
6. Diagnosticar o OCR manuscrito de I01 e ajudar a implementar visão Gemini configurável (18/10/2026), preservando Tesseract local, texto bruto, rastreabilidade e revisão humana obrigatória; os testes automatizados usam simulação para a API. A tentativa real com `gemini-3.8-flash` terminou em HTTP 503 após três tentativas, portanto sua validação permanece pendente.
7. Integrar a criação da peça institucional ao fim de `python -m src.main`, salvando evidências em `resultados/imagens/`, sem confundir composição local com imagem gerada por IA.
8. Incorporar `dados/originais/brasao.png` à peça institucional, preservando o original e registrando seu hash e uso na proveniência.
9. Separar as saídas do fluxo padrão em `resultados/minutas/`, `resultados/logs/` e `resultados/imagens/`, mantendo o ID da execução para rastreabilidade.
10. Fazer o comando isolado `arte` salvar imagens locais ou Cloudflare em `resultados/imagens/`, em vez de `resultados/multimodal/`.
11. Separar também os comandos isolados: STT/TTS em `resultados/audios/` e OCR em `resultados/ocr/`, preservando as evidências históricas existentes.
12. Completar o RF07 com voz, ritmo e instruções de entonação configuráveis, hash do roteiro falado e documentação de benefícios e limitações de acessibilidade.
13. Integrar `gerar_voz()` ao `python -m src.main`, acionando TTS somente depois de aprovação humana real e salvando evidências em `resultados/audios/`.
14. Configurar o TTS para `gemini-3.8-flash-lite-tts` e preservar como WAV o áudio nativo retornado pela API Gemini.

## Sugestões e decisões
| Sugestão | Registro | Justificativa |
|---|---|---|
| CLI Python em vez de interface web | Proposta; conferir pela equipe | Escopo reproduzível em 12h |
| Cliente HTTP OpenAI-compatible | Proposta; conferir pela equipe | Menor acoplamento de provedor |
| Manter Tesseract local como alternativa ao OCR remoto | Implementado; o padrão atual usa Gemini e deve ser escolhido conscientemente | Privacidade e custo; o modo local evita enviar as páginas do documento ao provedor |
| Decisão humana antes de TTS | Proposta; conferir pela equipe | Evitar disseminar minuta não aprovada |
| Imagem local sem IA como se fosse IA | **Rejeitada** | Origem do material deve ser declarada corretamente |
| Provedores externos multimodais | Decisão atual: chamadas ocorrem conforme provedor configurado ou selecionado; o STT padrão é Groq e envia o áudio original. O comando `arquivos` e `extracao_llm.py` foram removidos por decisão da equipe (17/10/2026). | Reduzir etapas de execução; usar somente conteúdo fictício em serviços externos |
| Fundir `multimodal.py`, `guilherme_multimodal.py` e `arte_ia.py` em `audio.py`, `visao.py` e `imagem.py`; WER/CER só em `avaliacao.py`; CLI único em `src.main` | Aprovada pela equipe (17/10/2026) | Eliminar STT/TTS/OCR/Levenshtein duplicados e seguir a estrutura sugerida no PDF |
| Apagar `scripts/*`, `LEIA_PRIMEIRO.txt` e `prompts/sistema_extracao.md` | Aprovada pela equipe (17/10/2026) | Obsoletos: apontavam para pastas e módulos que não existem mais, ou só eram lidos pela extração por LLM removida |
| Manter só o material fornecido em `dados/` e mover injeção/lacunas para `testes/fixtures/` | Decisão da equipe (resposta registrada na conversa) | Respeita o commit que removeu os casos sintéticos e preserva cobertura de RF03/RF05 |
| Aprovação exige responsável e justificativa digitados no terminal | Aceita; conferir pela equipe | RF11/RF13 e diretriz de não preencher decisão humana por conta própria |

## Erros e inadequações a registrar
- [x] 17/10/2026: após o commit `f6d5b8b` (remoção dos casos C01–C06), 4 testes falhavam e `python -m src.main` não tinha entradas; corrigido com `casos.yaml`, gabaritos prévios e fixtures.
- [x] 17/10/2026: o extrator por regex capturava o rótulo seguinte como parte do nome (`Maria Fictícia Albuquerque\nProtocolo`), podia tomar data de nascimento como data da solicitação e não reconhecia protocolo com hífen; corrigido e coberto por testes.
- [x] 17/10/2026: o lote terminava com código 0 mesmo com falhas e `verificar` emitia aviso de depreciação; corrigidos.
- [ ] Registrar outros defeitos encontrados e correções realizadas em execução real.
- [ ] Conferir que nenhum arquivo de origem/gabarito foi alterado para coincidir artificialmente com saída.
- [ ] Preencher ambiente de validação, métricas e responsáveis.
- [x] 18/10/2026: documentação corrigida para distinguir OCR local, OCR Gemini configurado, referência de mock e tentativa real HTTP 503; contagem atualizada posteriormente para 91 testes.
- [x] 18/10/2026: fluxo padrão passou a criar a peça institucional ao final em `resultados/imagens/`; sucesso e falha cobertos por testes.

## Validação do código e do conteúdo gerado
`python -m unittest discover -s testes -t .` e execução de `python -m src.main --mock` com decisões simuladas (sem APIs). Validação por serviço real e por pessoa: ver `documentacao/matriz_requisitos.md`.

## Responsabilidade
Os alunos devem ler, testar, adaptar, validar e assumir responsabilidade pelo resultado final. A colaboração de IA está declarada, sem atribuir a modelos ações que não realizaram.

**Assinaturas/ciência da equipe:** Diego: ___ · Ayron: ___ · Guilherme: ___.
