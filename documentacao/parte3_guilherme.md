# Parte 3 — Guilherme · áudio, OCR, imagem e acessibilidade

**Situação:** implementação preparada para aplicação **local**, sem commits, sem push, sem PR e sem modificações no GitHub.

## Escopo da atividade
Base: *Desafio Prático 1 — Central Inteligente de Atendimento e Comunicação Institucional*, FIC_DEV (2026), seção 5 (Estudante 3) e requisitos RF06, RF07, RF08, RF10. Integra a estrutura Python atual por **subcomandos de `python -m src.main`** (`audio`, `ocr`, `voz`, `arte`), implementados em `src/audio.py`, `src/visao.py` e `src/imagem.py`, sem substituir o código dos Estudantes 1 e 2.

| Requisito | Implementação | Evidência / ressalva |
|---|---|---|
| RF06/STT | `audio` usa Whisper local opcional (`faster-whisper`) ou Groq conforme seleção/configuração | Preserva texto bruto, SHA-256, idioma, duração, modelo, relatório WER/CER contra **gabarito da mesma modalidade**; não declara STT real nos testes com mock. |
| RF07/TTS | `voz` usa eSpeak offline ou provedor já implementado pelo projeto | Exige revisão humana documentada, nome/data/referência SHA-256; decisões de mock/YAML são recusadas. Adiciona aviso falado sobre “não localizado”. Não envia mensagem. |
| RF08/OCR | `ocr` lê PNG/JPG/TIFF e PDF digitalizado usando `pdftoppm`; permite Tesseract local ou Gemini configurado | Preserva original, OCR bruto, trechos com baixa confiança, data, SHA-256 e revisão pendente. Calcula CER/WER se existir transcrição de referência **prévia**. A tentativa real com Gemini terminou em HTTP 503, sem resultado válido. |
| RF10/Imagem | `arte` usa `imagem.gerar()` | Pillow local continua disponível; `--provider cloudflare` seleciona `@cf/black-forest-labs/flux-1-schnell` via Workers AI. O brasão configurado é incorporado à peça, com hash na proveniência, sem equivaler a autorização de uso oficial. A API não reporta custo por imagem, portanto a proveniência registra `não localizado`; a revisão visual permanece pendente. |
| Testes | `testes/test_audio_visao_imagem.py` | Testes locais determinísticos, sem APIs e sem credenciais (a contagem atual vem de `python -m unittest discover -s testes -t .`). |

## Pré-requisitos Ubuntu
```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
sudo apt install tesseract-ocr tesseract-ocr-por poppler-utils ffmpeg espeak
python -m src.main verificar
```

Para transcrever **localmente**, opcionalmente `pip install faster-whisper` (o primeiro uso pode exigir download de pesos). Alternativamente, para Groq, adicione somente ao `.env` local `GROQ_API_KEY=...` e configure o provedor — **não publique**. Quando Groq estiver selecionado/configurado, o áudio original é enviado ao serviço; use apenas conteúdo fictício.

## Comandos (não enviam respostas a cidadãos)

O OCR e os provedores locais permanecem na máquina. Com um provedor remoto selecionado/configurado, os arquivos necessários ao processamento são enviados a esse serviço.

### OCR local — PDF digitalizado do caso de matrícula
A execução estritamente local deve informar o provedor explicitamente:
```bash
python -m src.main ocr dados/originais/entrada_pdf-imagem.pdf --provider local --psm 6
```
A saída fica em `resultados/ocr/ocr_<id>/ocr_bruto.txt`, `resultado.json` e `PENDENTE_REVISAO.md`. Caso o OCR misture nomes e números manuscritos, não “corrigir” silenciosamente: conferir a imagem original e fornecer depois um arquivo `--revisado` manual. A configuração padrão atual seleciona Gemini; `python -m src.main ocr ... --provider gemini` envia cada página renderizada ao provedor. A tentativa real de 18/10/2026 terminou em HTTP 503 após três tentativas e não valida a qualidade do modelo.

### STT local (opcional, requer faster-whisper)
```bash
python -m src.main audio dados/originais/entrada_audio.mp3 --provider local
```

### STT Groq — somente com áudio fictício
```bash
python -m src.main audio dados/originais/entrada_audio.mp3 --provider groq
```
Para medir WER/CER, acrescentar `--gabarito dados/gabaritos/referencia_audio_exata.txt`; **não usar automaticamente** `entrada_texto.txt` como transcrição: áudio e texto têm divergências de conteúdo/e-mail e métricas ficariam enganosas. O gabarito deve existir **antes da medição**.

### Voz da minuta aprovada
Revisar uma minuta real (não `mock`) e criar arquivo de revisão com os campos necessários:
```json
{
  "decisao": "aprovar",
  "simulada": false,
  "origem": "revisao_humana",
  "revisor": "NOME DO REVISOR QUE REALMENTE REVISOU",
  "data_revisao": "2026-10-17",
  "sha256_minuta": "SHA256 REAL DO CONTEUDO DA MINUTA APROVADA"
}
```
O registro só pode ser preenchido após uma revisão humana efetiva. Para calcular o hash: `sha256sum caminho/minuta_aprovada.md`. A presença do JSON e do hash ajuda na rastreabilidade, mas **não autentica por si só a identidade do revisor**.
```bash
python -m src.main voz caminho/minuta_aprovada.md --revisao caminho/revisao_real.json
```
O padrão usa a API nativa Gemini com `gemini-3.8-flash-lite-tts`, voz `Kore` e instrução de entonação institucional definidas em `config/config.yaml`. O WAV retornado pela API é salvo diretamente como `voz.wav`, sem conversão ou troca artificial de extensão. eSpeak continua disponível como alternativa local configurável. Se houver “não localizado”, o sistema adiciona um aviso antes da leitura. `roteiro_falado.txt` e seu SHA-256 ficam preservados para a conferência, mas o critério de correspondência só é concluído depois de uma pessoa ouvir o áudio e compará-lo com a minuta aprovada.

No fluxo principal (`python -m src.main`), uma decisão humana real `aprovar` cria os arquivos de aprovação e chama automaticamente o mesmo `gerar_voz()`, salvando o pacote em `resultados/audios/tts_<data>_<id>/`. O resumo do caso informa `pasta_audio`. O TTS não é chamado para mock, YAML de demonstração, rejeição ou correção ainda pendente.

O áudio amplia o acesso para pessoas com baixa visão, dificuldade de leitura ou preferência por conteúdo falado. Limitações restantes: nomes próprios, siglas e números podem ter pronúncia imperfeita; o recurso não substitui leitor de tela, Libras ou adaptação individual; a API exige conexão, chave e cota disponíveis; e a ausência de `ffprobe` impede apenas a medição automática da duração.

### Peça visual
```bash
python -m src.main arte --referencia dados/originais/brasao.png
```
Com o padrão local, isso produz ilustração **programática**, não imagem gerada por IA. Para usar a integração de IA gratuita da Cloudflare, execute explicitamente:
```bash
python -m src.main arte --provider cloudflare --referencia dados/originais/brasao.png
```
O catálogo oficial do Workers AI documenta o FLUX.1 schnell como texto-para-imagem, não como modelo de edição. A chamada requer `CLOUDFLARE_ACCOUNT_ID` e um API Token com permissão para Workers AI, armazenado localmente em `CLOUDFLARE_API_KEY` no `.env`; não use a Global API Key nem publique credenciais. A cota gratuita do Workers AI é de 10.000 neurons por dia; monitore o consumo no painel Cloudflare. No plano Workers Free, operações acima do limite falham; planos pagos podem cobrar o excedente. `--mock` força composição local e não faz chamada remota. A tentativa anterior que retornou HTTP 402 foi feita no OpenRouter e não testou a integração Cloudflare. Nenhuma geração real via Cloudflare foi executada ainda. Revisar texto, símbolos, pertinência institucional, selo sintético e metadados; o brasão fornecido é **referência**, não incorporado automaticamente. Nunca apresentar a arte como peça oficial GOV.MT. Consulte [modelo FLUX.1 schnell](https://developers.cloudflare.com/workers-ai/models/flux-1-schnell/) e [preços do Workers AI](https://developers.cloudflare.com/workers-ai/platform/pricing/).

## Onde ficam resultados e auditoria

STT e TTS criam pastas únicas em `resultados/audios/`, OCR em `resultados/ocr/` e o comando `arte` em `resultados/imagens/`, sempre com data e identificador. Os arquivos originais não são modificados. O relatório não deve sair da máquina com nomes, CPF, RG, áudio de voz ou outro dado pessoal real. As pastas de execução devem permanecer ignoradas pelo Git quando contiverem dados não revisados.

## Testes
```bash
python -m unittest discover -s testes -t .
python -m src.main verificar
```
Na elaboração original, 13 testes novos passaram com *stubs* e foi feita uma execução local real de OCR do PDF fornecido (Tesseract português), que evidenciou reconhecimento imperfeito de campos manuscritos e trechos com baixa confiança. **Atualização:** o código foi reorganizado em `src/audio.py`, `src/visao.py` e `src/imagem.py`; STT/TTS locais históricos estão em `resultados/multimodal/`, enquanto novas execuções usam `resultados/audios/`. As integrações Gemini TTS e Cloudflare imagem têm testes simulados; a geração real e a homologação humana seguem pendentes. A suíte completa tem 91 testes aprovados em 18/10/2026 no Windows; repetir no repositório de entrega Ubuntu e anexar evidências após conferir privacidade.

## Checklist de aceite — validação humana obrigatória
- [ ] Confirmar que os arquivos enviados a serviços externos contêm somente dados fictícios.
- [ ] Audio: STT real e transcrição bruta salvos; gabarito de áudio anterior; WER e trechos críticos revisados.
- [ ] PDF: OCR bruto e correções humanas salvas separadamente; CER calculado contra referência da imagem; nome, protocolo e data confirmados no original.
- [ ] Voz: o WAV foi ouvido e conferido, mas ainda é necessário vincular a validação ao revisor identificado e ao arquivo de aprovação cujo hash corresponda à minuta.
- [ ] Imagem: proveniência registra IA **apenas se de fato houve IA**; manter selo e conferir símbolos e textos.
- [ ] Relatório técnico atualizado pela equipe com modelo/versão/custos/datas e limitações.
- [ ] Nenhuma resposta enviada automaticamente ou publicada em serviços externos.

**Responsável pela frente:** Guilherme. **Status de homologação:** não localizado / pendente. 
