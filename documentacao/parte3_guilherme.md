# Parte 3 — Guilherme · áudio, OCR, imagem e acessibilidade

**Situação:** implementação preparada para aplicação **local**, sem commits, sem push, sem PR e sem modificações no GitHub.

## Escopo da atividade
Base: *Desafio Prático 1 — Central Inteligente de Atendimento e Comunicação Institucional*, FIC_DEV (2026), seção 5 (Estudante 3) e requisitos RF06, RF07, RF08, RF10. Integra a estrutura Python atual por um **novo módulo**, sem substituir o código do Estudante 1 ou do Estudante 2.

| Requisito | Implementação | Evidência / ressalva |
|---|---|---|
| RF06/STT | `audio` usa Whisper local opcional (`faster-whisper`) ou Groq (requer autorização explícita) | Preserva texto bruto, SHA-256, idioma, duração, modelo, relatório WER/CER contra **gabarito da mesma modalidade**; não declara STT real nos testes com mock. |
| RF07/TTS | `voz` usa eSpeak offline ou provedor já implementado pelo projeto | Exige revisão humana documentada, nome/data/referência SHA-256; decisões de mock/YAML são recusadas. Adiciona aviso falado sobre “não localizado”. Não envia mensagem. |
| RF08/OCR | `ocr` lê PNG/JPG/TIFF e PDF digitalizado usando `pdftoppm` + Tesseract local | Preserva original, OCR bruto, trechos com baixa confiança, data, SHA-256 e revisão pendente. Calcula CER/WER se existir transcrição de referência **prévia**. |
| RF10/Imagem | `arte` reutiliza `src.arte_ia.gerar()` atual | `imagem_provider=local` produz **Pillow (não IA)**; com `openai` habilitado e permissão explícita usa API. Exige nota de proveniência, registra revisão visual pendente e nunca trata referência de brasão como autorização de uso oficial. |
| Testes | `testes/test_guilherme_multimodal.py` | 13 testes locais determinísticos executados sem APIs e sem credenciais, além da demonstração real local de OCR em PDF. |

## Pré-requisitos Ubuntu
```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
sudo apt install tesseract-ocr tesseract-ocr-por poppler-utils ffmpeg espeak
python -m src.guilherme_multimodal verificar
```

Para transcrever **localmente**, opcionalmente `pip install faster-whisper` (o primeiro uso pode exigir download de pesos). Alternativamente, para Groq, adicione somente ao `.env` local `GROQ_API_KEY=...` e configure o provedor — **não publique**. A leitura remota de áudio só ocorre com a flag `--autorizar-api`, após confirmar que o arquivo/voz não contém dados pessoais reais.

## Comandos (não publicam nada)

### OCR local — PDF digitalizado do caso de matrícula
```bash
python -m src.guilherme_multimodal ocr dados/originais/entrada_pdf-imagem.pdf --psm 6
```
A saída fica em `resultados/guilherme/ocr_<id>/ocr_bruto.txt`, `resultado.json` e `PENDENTE_REVISAO.md`. Caso o OCR misture nomes e números manuscritos, não “corrigir” silenciosamente: conferir a imagem original e fornecer depois um arquivo `--revisado` manual.

### STT local (opcional, requer faster-whisper)
```bash
python -m src.guilherme_multimodal audio dados/originais/entrada_audio.mp3 --provider local
```

### STT Groq — apenas para áudio fictício autorizado
```bash
python -m src.guilherme_multimodal audio dados/originais/entrada_audio.mp3 --provider groq --autorizar-api
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
python -m src.guilherme_multimodal voz caminho/minuta_aprovada.md --revisao caminho/revisao_real.json
```
A voz local é em português brasileiro via eSpeak (WAV). Se houver “não localizado”, adiciona aviso antes da leitura. Confirmar ouvindo o áudio que a locução corresponde à minuta, sem acréscimos relevantes.

### Peça visual
```bash
python -m src.guilherme_multimodal arte --referencia dados/originais/brasao.png
```
Com `multimodal.imagem_provider: local`, isso produz ilustração **programática**, não imagem gerada por IA. Para cumprir a demonstração de **geração por IA** da RF10, somente se houver API autorizada, alterar **localmente** a configuração de imagem para `openai`, preencher `OPENAI_API_KEY` no `.env` e executar:
```bash
python -m src.guilherme_multimodal arte --referencia dados/originais/brasao.png --autorizar-api
```
Revisar texto, símbolos, pertinência institucional, selo sintético e metadata; o brasão fornecido é **referência**, não incorporado automaticamente. Nunca apresentar a arte como peça oficial GOV.MT.

## Onde ficam resultados e auditoria

Cada execução cria uma pasta única em `resultados/guilherme/` com metadados (`resultado.json` ou `revisao_visual.json`). Os arquivos originais não são modificados. O relatório não deve sair da máquina com nomes, CPF, RG, áudio de voz ou outro dado pessoal real. Inclua `resultados/guilherme/` em `.gitignore` se usar esses comandos no repositório.

## Testes
```bash
python -m unittest discover -s testes -t .
python -m src.guilherme_multimodal verificar
```
No ambiente de elaboração, **13 testes novos passaram** com *stubs* das interfaces atuais. Também foi realizada **uma execução local real de OCR** do PDF enviado (Tesseract português), que evidenciou reconhecimento imperfeito de campos manuscritos e trechos com baixa confiança. **Não foi feita transcrição real de áudio, nem chamada de TTS/API de imagem, nem homologação humana.** Para a entrega, repetir todos os testes no seu repositório Ubuntu e anexar evidências após conferir privacidade.

## Checklist de aceite — validação humana obrigatória
- [ ] Entradas têm dados fictícios e autorização para qualquer API externa.
- [ ] Audio: STT real e transcrição bruta salvos; gabarito de áudio anterior; WER e trechos críticos revisados.
- [ ] PDF: OCR bruto e correções humanas salvas separadamente; CER calculado contra referência da imagem; nome, protocolo e data confirmados no original.
- [ ] Voz: aprovação REAL documentada, hash bate; ouvir o WAV e confirmar o conteúdo.
- [ ] Imagem: proveniência registra IA **apenas se de fato houve IA**; manter selo e conferir símbolos e textos.
- [ ] Relatório técnico atualizado pela equipe com modelo/versão/custos/datas e limitações.
- [ ] Nenhuma resposta enviada automaticamente ou publicada em serviços externos.

**Responsável pela frente:** Guilherme. **Status de homologação:** não localizado / pendente. 
