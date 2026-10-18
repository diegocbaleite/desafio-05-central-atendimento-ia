# Parte 3 — Guilherme · áudio, OCR, imagem e acessibilidade

**Situação:** implementação preparada para aplicação **local**, sem commits, sem push, sem PR e sem modificações no GitHub.

## Escopo da atividade
Base: *Desafio Prático 1 — Central Inteligente de Atendimento e Comunicação Institucional*, FIC_DEV (2026), seção 5 (Estudante 3) e requisitos RF06, RF07, RF08, RF10. Integra a estrutura Python atual por **subcomandos de `python -m src.main`** (`audio`, `ocr`, `voz`, `arte`), implementados em `src/audio.py`, `src/visao.py` e `src/imagem.py`, sem substituir o código dos Estudantes 1 e 2.

| Requisito | Implementação | Evidência / ressalva |
|---|---|---|
| RF06/STT | `audio` usa Whisper local opcional (`faster-whisper`) ou Groq conforme seleção/configuração | Preserva texto bruto, SHA-256, idioma, duração, modelo, relatório WER/CER contra **gabarito da mesma modalidade**; não declara STT real nos testes com mock. |
| RF07/TTS | `voz` usa eSpeak offline ou provedor já implementado pelo projeto | Exige revisão humana documentada, nome/data/referência SHA-256; decisões de mock/YAML são recusadas. Adiciona aviso falado sobre “não localizado”. Não envia mensagem. |
| RF08/OCR | `ocr` lê PNG/JPG/TIFF e PDF digitalizado usando `pdftoppm` + Tesseract local | Preserva original, OCR bruto, trechos com baixa confiança, data, SHA-256 e revisão pendente. Calcula CER/WER se existir transcrição de referência **prévia**. |
| RF10/Imagem | `arte` usa `imagem.gerar()` | `imagem_provider=local` produz **Pillow (não IA)**; com `openai` configurado usa API. Exige nota de proveniência, registra revisão visual pendente e nunca trata referência de brasão como autorização de uso oficial. |
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
```bash
python -m src.main ocr dados/originais/entrada_pdf-imagem.pdf --psm 6
```
A saída fica em `resultados/multimodal/ocr_<id>/ocr_bruto.txt`, `resultado.json` e `PENDENTE_REVISAO.md`. Caso o OCR misture nomes e números manuscritos, não “corrigir” silenciosamente: conferir a imagem original e fornecer depois um arquivo `--revisado` manual.

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
A voz local é em português brasileiro via eSpeak (WAV). Se houver “não localizado”, adiciona aviso antes da leitura. Confirmar ouvindo o áudio que a locução corresponde à minuta, sem acréscimos relevantes.

### Peça visual
```bash
python -m src.main arte --referencia dados/originais/brasao.png
```
Com `multimodal.imagem_provider: local`, isso produz ilustração **programática**, não imagem gerada por IA. Para cumprir a demonstração de **geração por IA** da RF10, altere **localmente** a configuração de imagem para `openai`, preencha `OPENAI_API_KEY` no `.env` e execute:
```bash
python -m src.main arte --referencia dados/originais/brasao.png
```
Revisar texto, símbolos, pertinência institucional, selo sintético e metadata; o brasão fornecido é **referência**, não incorporado automaticamente. Nunca apresentar a arte como peça oficial GOV.MT.

## Onde ficam resultados e auditoria

Cada execução cria uma pasta única em `resultados/multimodal/` com metadados (`resultado.json` ou `revisao_visual.json`). Os arquivos originais não são modificados. O relatório não deve sair da máquina com nomes, CPF, RG, áudio de voz ou outro dado pessoal real. Inclua `resultados/multimodal/` em `.gitignore` se usar esses comandos no repositório.

## Testes
```bash
python -m unittest discover -s testes -t .
python -m src.main verificar
```
Na elaboração original, 13 testes novos passaram com *stubs* e foi feita uma execução local real de OCR do PDF fornecido (Tesseract português), que evidenciou reconhecimento imperfeito de campos manuscritos e trechos com baixa confiança. **Atualização:** o código foi reorganizado em `src/audio.py`, `src/visao.py` e `src/imagem.py`; STT/TTS locais executados depois pela equipe estão em `resultados/multimodal/` (ver `documentacao/matriz_requisitos.md`). Continuam pendentes: geração de imagem por IA e homologação humana. Para a entrega, repetir todos os testes no seu repositório Ubuntu e anexar evidências após conferir privacidade.

## Checklist de aceite — validação humana obrigatória
- [ ] Confirmar que os arquivos enviados a serviços externos contêm somente dados fictícios.
- [ ] Audio: STT real e transcrição bruta salvos; gabarito de áudio anterior; WER e trechos críticos revisados.
- [ ] PDF: OCR bruto e correções humanas salvas separadamente; CER calculado contra referência da imagem; nome, protocolo e data confirmados no original.
- [ ] Voz: aprovação REAL documentada, hash bate; ouvir o WAV e confirmar o conteúdo.
- [ ] Imagem: proveniência registra IA **apenas se de fato houve IA**; manter selo e conferir símbolos e textos.
- [ ] Relatório técnico atualizado pela equipe com modelo/versão/custos/datas e limitações.
- [ ] Nenhuma resposta enviada automaticamente ou publicada em serviços externos.

**Responsável pela frente:** Guilherme. **Status de homologação:** não localizado / pendente. 
