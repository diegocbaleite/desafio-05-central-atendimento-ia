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
- [x] Cliente de API recebe texto minimizado para minuta.
- [x] OCR local é alternativa de processamento soberano.
- [x] Não existe envio automático.
- [ ] Confirmar tratamento e retenção contratual do provedor selecionado.
- [ ] Definir regra de retenção/descarte se houver implantação futura.
- [ ] Inspecionar logs/prints antes de publicar.
- [ ] Confirmar se nenhuma gravação contém voz real de pessoa sem autorização.

Bases para avaliação interna: finalidade, adequação, necessidade, transparência, segurança, prevenção, prestação de contas (art. 6º da LGPD), governança e transparência de decisões; para transferências internacionais reais é necessária análise adicional (art. 33). Não equiparar pseudonimização a anonimização.
