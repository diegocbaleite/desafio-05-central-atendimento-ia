# Roteiro de execução — 12 horas

> **ROTEIRO HISTÓRICO.** As referências a `C01`–`C06` pertencem ao catálogo substituído. Para a execução vigente, use `T01`, `A01`, `I01`, `X01` e `X02` conforme `dados/originais/casos.yaml`.

| Horas | Diego (API/segurança) | Ayron (prompts/avaliação) | Guilherme (multimodal) | Marco |
|---|---|---|---|---|
| 0–1 | Clonar, configurar `.env` e verificar Python | Conferir regras e congelar gabaritos | Instalar Tesseract e espeak | Setup |
| 1–2 | Rodar C01/C05/C06 em mock | Revisar prompts A/B/C | Preparar imagem e áudio fictícios | Primeira demo |
| 2–4 | Validar integração com modelo real e falhas | Executar A/B/C com mesmas condições | Processar áudio com ruído e OCR | Saídas reais |
| 4–5 | Verificar logs, chaves e tokens | Comparar matriz e selecionar prompt | Validar WER e CER | Escolha justificada |
| 5–7 | Testar segurança/injeção | Revisar minutas, registrar decisões | Gerar áudio de aprovadas | Aprovação/rejeição |
| 7–9 | Conferir JSON e proveniência | Preencher rubrica e métricas | Produzir arte com IA e revisar legenda | Evidências |
| 9–10 | Testes completos | Redigir relatório e LGPD | Inspecionar arte/timbre GOV.MT fictício | Documentação |
| 10–11 | Instalação limpa | Documentar uso real de IA | Ensaiar demonstração | Reprodutibilidade |
| 11–12 | Gerar ZIP seguro e conferir | Preparar explicação | Apresentar multimodalidade | Entrega |

Cortes possíveis se necessário: visão remota (mantém OCR local), visual sofisticado (mantém arte simples produzida por IA), interface web (mantém CLI). **Não cortar:** gabaritos prévios, chamada de API real, A/B/C, teste de injection, revisão humana, JSON, logs, transparência da proveniência.
