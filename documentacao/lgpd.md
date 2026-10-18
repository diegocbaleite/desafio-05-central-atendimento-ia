# LGPD — dados de teste e salvaguardas (RF12)
Este é um protótipo com **dados fictícios**. Em um órgão real, deve haver avaliação jurídica, de segurança da informação, contratos e governança apropriados antes de qualquer uso operacional.

| Campo | Pode ser pessoal? | Finalidade simulada | Necessário para API? | Risco | Salvaguarda |
|---|---|---|---|---|---|
| Nome | Sim | Identificar destinatário | Evitar se não precisar | Médio | Fictício; pseudonimizar se possível |
| CPF/RG | Sim | Conferir cadastro | **Não** | Alto | Remover antes de provedor |
| E-mail/telefone | Sim | Contato | **Não** | Médio | Remover/pseudonimizar |
| Voz | Sim | Acessibilidade/STT | Depende | Alto | Gravação fictícia, sem usuário real |
| Fotografia/formulário | Sim | Extração/OCR | Não, se local | Alto | Preferir Tesseract local |
| Protocolo | Pode identificar pessoa | Acompanhamento | Às vezes | Médio | Fonte e confirmação |
| Assunto/pedido | Pode conter sensíveis | Classificação | Texto minimizado | Variável | Revisão de conteúdo |

Checklist de entrega:
- [x] Arquivos de teste usam personagens inventados.
- [x] `.env` não é versionado; tokens nunca são exibidos intencionalmente.
- [x] A chamada de estruturação ao OpenRouter minimiza CPF, e-mail e telefone; não envia esses campos como evidência.
- [x] OCR local por Tesseract continua disponível, mas o provedor padrão atual é Gemini e recebe a página inteira renderizada; use `--provider local` ou configure `ocr_provider: local` para não enviar o formulário. O STT padrão é Groq e recebe o áudio original; configure `local` para não enviá-lo.
- [x] OCR local é alternativa de processamento soberano.
- [x] Não existe envio automático de respostas a cidadãos; chamadas a serviços de IA seguem o provedor selecionado ou configurado.
- [x] TTS e imagem usam provedores configuráveis; a configuração atual mantém esses serviços locais.
- [ ] Confirmar por escrito que todo o material de `dados/originais/` (texto, áudio, PDF) é fictício; os arquivos contêm nome, CPF, RG, e-mail e nome da mãe, que seriam dados pessoais em um cenário real.
- [ ] Confirmar tratamento e retenção contratual do provedor selecionado.
- [ ] Definir regra de retenção/descarte se houver implantação futura.
- [ ] Inspecionar logs/prints antes de publicar.
- [ ] Confirmar se nenhuma gravação contém voz real de pessoa sem autorização.

Os artefatos de execução (texto extraído, transcrição, OCR) ficam em diretórios locais para preservar evidências. Groq recebe o áudio original e Gemini recebe páginas renderizadas do documento quando esses provedores estão selecionados; portanto **não devem receber conteúdo real ou confidencial**. Confirme que os dados são fictícios antes de executar fluxos remotos. Para um cenário real, use OCR/STT local, defina retenção e acesso às transcrições e conclua uma avaliação de privacidade e segurança antes de habilitar provedores externos.

Bases para avaliação interna: finalidade, adequação, necessidade, transparência, segurança, prevenção, prestação de contas (art. 6º da LGPD), governança e transparência de decisões; para transferências internacionais reais é necessária análise adicional (art. 33). Não equiparar pseudonimização a anonimização.
