# Evidências multimodais — FICDEV-IA

**Conjunto selecionado para revisão da equipe — 18/10/2026.**

Este pacote é uma seleção dos resultados executados localmente. Não é o histórico completo nem o ZIP final do projeto. Mantém a pasta `resultados/guilherme/` ausente e **não contém credenciais, transcrições brutas, ficha de matrícula nem áudio narrado com dados do atendimento**. Os originais permanecem no arquivo local `evidencias_multimodais_revisao.zip` e devem ser guardados sob controle da equipe.

## Requisitos e resultados

- **RF06 / STT:** Whisper local `small`, áudio de 89,16 s, execução de 27,109 s; WER/CER registrados em 0,00. **Limitação essencial:** a referência conferida é idêntica à transcrição bruta do modelo; portanto, os valores zero não demonstram acurácia independente. O JSON ainda indica revisão humana pendente nessa execução.
- **RF07 / TTS:** síntese local eSpeak, arquivo WAV de 181,14 s, aprovada por escuta humana, com ressalva de voz robótica. Arquivo WAV completo foi mantido no conjunto local por precaução quanto a dados pessoais.
- **RF08 / OCR:** Tesseract local, PDF de 1 página, PSM 6. Métricas do OCR bruto: WER 0,6892 (68,92%) e CER 0,4661 (46,61%). O texto revisado por humano apresenta WER/CER 0,00 perante uma referência idêntica; isso não representa acurácia do OCR bruto. A execução indica que a autoria/conferência da revisão precisa ser identificada na documentação.
- **RF10 / imagem:** geração real via Cloudflare Workers AI `@cf/black-forest-labs/flux-1-schnell`, `steps=4`, com registro de proveniência e imagem. Validação humana separada pelo revisor Guilherme: **aprovada para demonstração com ressalvas**. A imagem é uma cena de escritório com brasão legível; papéis e quadros na parede apresentam estranhezas. **Uso oficial: não autorizado.** Os JSONs originais retêm `revisao_humana: pendente`, pois foram produzidos antes da avaliação humana separada.

## Conteúdo do pacote

- `rf06_stt/resultado.json`: metadados originais da última execução; sem transcrição.
- `rf07_tts/resultado.json`, `rf07_tts/VALIDACAO_AUDITIVA.txt`: metadados e avaliação humana; sem WAV.
- `rf08_ocr/resumo_metricas_sem_dados_pessoais.json`: resumo derivado das métricas originais, sem trechos do formulário.
- `rf10_imagem/orientacao.png`, `rf10_imagem/orientacao.proveniencia.json`, `rf10_imagem/revisao_visual.json`, `rf10_imagem/VALIDACAO_VISUAL_HUMANA.txt`: arquivos originais da execução com API real e validação posterior.

## Atenções para integração

1. Antes de integrar PR #32, validar se as duas referências `resultados/multimodal/referencias/referencia_audio_conferida.txt` e `referencia_ocr_conferida.txt` contêm **apenas dados fictícios e autorizados para publicação**. Elas trazem nome, CPF, data de nascimento, contato e informações de matrícula. Se não forem dados comprovadamente sintéticos, não devem permanecer em branch compartilhada; pedir à equipe para tratar o histórico de Git, e não apenas remover na próxima versão.
2. Não anexar `.env`, tokens da Cloudflare, `.wav` ou ficha de matrícula real a commits públicos.
3. Integrar na `main` por Pull Request após revisão da equipe; não executar `git add resultados/` indiscriminadamente.
4. O resumo OCR é **derivado e sanitizado**, não substitui o `resultado.json` bruto nem seu histórico de auditoria.
5. A validade de qualquer demonstração com dados fornecidos pelo curso depende de confirmação de que o conjunto é fictício/anônimo ou de autorização para uso.

Gerado a partir dos arquivos do ZIP recebido, sem novas chamadas de modelos ou alteração dos registros originais.
