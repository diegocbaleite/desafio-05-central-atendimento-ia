# Integração OpenAI — 28/10/2026

Alteração solicitada por Ayron após disponibilizar crédito de API. Escopo: adaptar os módulos existentes do Desafio Prático 1. O arquivo `desafio-06/PROMPT_DESAFIO_06.md` permanece uma especificação futura; esta alteração não implementa RF14–RF24. O PDF integral do enunciado não foi localizado nesta sessão.

## Configuração e escolha dos modelos

`config/config.yaml` passa a selecionar OpenAI em todas as modalidades. O perfil usa `https://api.openai.com/v1` e `OPENAI_API_KEY`, carregada do ambiente ou do `.env` ignorado pelo Git. A chave existente foi detectada sem imprimir seu valor; o `.env` não foi alterado. Não foram adicionadas dependências.

| Função | Modelo configurado | Endpoint | Validação desta alteração |
|---|---|---|---|
| Texto/minutas/experimentos | `gpt-6-luna` | `/chat/completions` | Chamada real concluída em X02; revisão humana pendente |
| OCR/visão | `gpt-6-luna` | `/chat/completions`, imagem PNG em base64 | Contrato testado com resposta simulada; execução OpenAI real pendente |
| Transcrição | `gpt-transcribe` | `/audio/transcriptions` | Contrato multipart testado; execução OpenAI real pendente |
| Voz | `gpt-4o-mini-tts`, voz `coral` | `/audio/speech` | Contrato MP3 e bloqueio de revisão simulada testados; execução real pendente |
| Imagem | `gpt-image-2.5-flare` | `/images/generations` | Contrato base64, proveniência e uso de tokens testados; execução real pendente |

O catálogo da conta foi consultado com sucesso e incluiu todos esses IDs. A consulta não gera conteúdo e não confirma disponibilidade de cada endpoint, cota ou permissão de geração. Texto e visão usam o modelo voltado a tarefas de volume/custo reduzido descrito no [catálogo oficial](https://developers.openai.com/api/docs/models/gpt-6-luna); qualidade ainda depende de avaliação com os casos do desafio.

O cliente mantém Chat Completions para reaproveitar a arquitetura existente. Usa `max_completion_tokens: 2400`, `reasoning_effort: none`, temperatura 0,2 e `store: false`. Com raciocínio ativo, omite temperatura por incompatibilidade documentada no [guia GPT-6](https://developers.openai.com/api/docs/guides/latest-model). Os parâmetros efetivamente enviados são registrados nos metadados. Não usar `none` em um modelo que não o suporte; ao trocar o modelo, conferir suas capacidades e configurar o esforço.

STT envia `languages[]=pt` ao `gpt-transcribe`; modelos anteriores mantêm `language=pt`, conforme o [guia de transcrição de arquivos](https://developers.openai.com/api/docs/guides/speech-to-text). O OCR remoto reaproveita a conversão PNG, preservação do bruto e conferência obrigatória dos campos críticos.

Imagem solicita uma unidade, tamanho `1024x1536` e qualidade `low`, configuráveis no YAML, conforme a [documentação de imagem](https://developers.openai.com/api/docs/guides/image-generation). O retorno `data[0].b64_json` é validado, a arte é identificada como sintética e recebe proveniência e revisão pendente. O brasão é incorporado localmente; isso não comprova edição por IA nem homologação GOV.MT.

TTS reaproveita o contrato Speech e valida o MP3 recebido. A [documentação oficial de voz](https://developers.openai.com/api/docs/guides/text-to-speech) informa encerramento desse modelo/endpoint em **06/01/2027**, exigindo futura migração para Realtime; trocar apenas o ID não basta. Toda gravação deve ser apresentada como voz gerada por IA. `gerar_voz()` continua exigindo aprovação humana real e hash da minuta atual.

## Execução observada

- Ambiente: Windows, Python **3.14.6**. O alias `python` do Windows não executou neste sandbox; foi usado o interpretador instalado em `C:/Users/ayron/AppData/Local/Python/pythoncore-3.14-64/python.exe`.
- Antes da alteração: **114 testes aprovados**.
- Após a alteração: **130 testes aprovados**; `python -m src.main verificar` concluído com chave OpenAI detectada e envio automático desabilitado. `python -m src.main --mock --decisoes dados/revisao/decisoes_demo.yaml` concluiu **5 casos, sem falhas**, execução `262c43f25caf`; suas decisões continuam simuladas e excluídas da taxa humana. eSpeak e ffprobe não estão disponíveis nesta máquina; a duração de áudio pode permanecer não medida.
- Consulta real: `python -m src.main modelos --provider openai`, concluída após liberar rede fora do sandbox. A lista contém os quatro IDs escolhidos para as cinco modalidades (texto e visão compartilham um ID).
- Chamada real: `python -m src.experimento_b_v2_real --versao v4 --caso X02`.
- Evidência local: `resultados/execucoes/prompts_b_v4_real/20261028T172001971412Z/`, com saída textual, CSV, prompt, hashes e `X02_metadados.json`. Diretório ignorado pelo Git; preservar os arquivos locais ao preparar uma entrega higienizada.
- Modelo retornado: `gpt-6-luna`; **1 tentativa**, **5,165 s** no cliente, **1.094 tokens de entrada**, **160 tokens de saída**. Custo monetário não retornado: `não localizado` (não calculado nem estimado).
- Revisão humana e notas RF13 não foram preenchidas. A saída contém variações flexionadas do marcador, como “não localizada” e “não localizados”, em vez de usar sempre o literal obrigatório `não localizado`. O sucesso da chamada comprova integração, não fidelidade total ao formato nem aprovação da minuta. A evidência foi preservada sem corrigir a saída, o prompt ou o gabarito após o teste.

Nenhuma execução OpenAI real de áudio, OCR, TTS ou imagem foi realizada nesta alteração. As métricas antigas de Gemini/Groq/Cloudflare continuam históricas e não foram transferidas para a OpenAI. Entradas originais, gabaritos, decisões humanas e evidências prévias foram preservados.

## Como executar

Na raiz do projeto, com o ambiente Python ativo:

```powershell
python -m src.main verificar
python -m src.main modelos --provider openai
python -m unittest discover -s testes -t .
python -m src.main --mock --decisoes dados/revisao/decisoes_demo.yaml

# API real: uma chamada de texto em fixture fictícia, sem aprovar a minuta
python -m src.experimento_b_v2_real --versao v4 --caso X02

# API real nas modalidades: consome créditos; conferir que as entradas são fictícias
python -m src.main audio dados/originais/entrada_audio.mp3 --provider openai
python -m src.main ocr dados/originais/entrada_pdf-imagem.pdf --provider openai
python -m src.main arte --provider openai

# TTS: substituir pelos arquivos da versão realmente aprovada por pessoa
python -m src.main voz CAMINHO_MINUTA.md --revisao CAMINHO_REVISAO.json --provider openai
```

`audio` sem `--provider` agora respeita o STT configurado, como o fluxo principal. O executor B V2/V3/V4 também respeita `llm.provider` e grava metadados individuais. Gemini, Groq, Cloudflare e alternativas locais permanecem disponíveis; selecione modelo e voz compatíveis ao trocar o provedor. Não existe fallback automático, envio ao cidadão ou aprovação automática.

Os testes de contrato em `testes/test_openai.py` simulam HTTP e cobrem parâmetros, catálogo, autenticação, timeout, limite, transcrição inválida, OCR, MP3, imagem/proveniência e bloqueio de TTS. Dois testes de metadados do fluxo foram atualizados para os novos padrões OpenAI; nenhum gabarito foi alterado. Erros de texto removem o token antes de truncar mensagens do provedor.

Para finalizar a validação multimodal: executar os comandos reais com dados fictícios, preservar bruto e referências independentes, conferir nomes/protocolos/datas e registrar revisão humana. Aprovação de voz exige o documento e seu hash atual; imagens e áudio precisam de conferência visual/auditiva. A avaliação do marcador de ausência e os requisitos posteriores do Desafio 6 permanecem pendentes.
