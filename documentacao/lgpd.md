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
- [x] A leitura remota de PDF/áudio está documentada como transferência do arquivo original ao Gemini; a demonstração deve usar apenas arquivos fictícios.
- [x] OCR local é alternativa de processamento soberano.
- [x] Não existe envio automático.
- [x] O comando `python -m src.main arquivos` exige `--autorizar-api`; sem a opção nada é enviado a provedores externos.
- [ ] Confirmar por escrito que todo o material de `dados/originais/` (texto, áudio, PDF) é fictício; os arquivos contêm nome, CPF, RG, e-mail e nome da mãe, que seriam dados pessoais em um cenário real.
- [ ] Confirmar tratamento e retenção contratual do provedor selecionado.
- [ ] Definir regra de retenção/descarte se houver implantação futura.
- [ ] Inspecionar logs/prints antes de publicar.
- [ ] Confirmar se nenhuma gravação contém voz real de pessoa sem autorização.

O comando `python -m src.main arquivos --autorizar-api` mantém o texto extraído no diretório local ignorado pelo Git para preservar evidências. A etapa de leitura de PDF/áudio envia os bytes originais ao Gemini, portanto **não deve receber conteúdo real ou confidencial**. Para um cenário real, use OCR/STT local, defina retenção e acesso às transcrições e conclua uma avaliação de privacidade e segurança antes de habilitar provedores remotos.

Bases para avaliação interna: finalidade, adequação, necessidade, transparência, segurança, prevenção, prestação de contas (art. 6º da LGPD), governança e transparência de decisões; para transferências internacionais reais é necessária análise adicional (art. 33). Não equiparar pseudonimização a anonimização.
