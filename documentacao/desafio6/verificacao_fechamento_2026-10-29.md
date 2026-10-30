# Verificação de fechamento — 29/10/2026

> Registro histórico de 29/10/2026. A retomada e a reprodução em cópia limpa de 30/10/2026 estão na [conferência da entrega](fechamento_entrega_2026-10-30.md).

**O conjunto principal de prints está completo. O pacote final ainda não está pronto.** A conferência inicial foi somente leitura; depois, o usuário autorizou e foram executadas as validações complementares reais documentadas abaixo. Nenhuma decisão foi registrada pelo agente em nome do operador.

## Conferido

- **15/15 PNGs** do conjunto principal presentes; o último, `05_revisao_rejeitada_ou_revisar.png`, foi aberto e conferido visualmente. Os demais foram inspecionados durante a coleta. As capturas adicionais 02e e 06e são opcionais, conforme o [catálogo](evidencias_humanas/README.md).
- **Cinco JSONs** de evidências humanas e auditoria válidos; links locais do catálogo verificados.
- **UI-001:** estado `revisar`, decisão de Diego com origem `humana_interface` e justificativa de complementação/conferência das fontes.
- **UI-002:** estado `aprovada`, decisão de Diego com origem `humana_interface` e justificativa de conferência no DOC-02.
- Os dois registros JSON correspondem aos estados atuais do SQLite, às decisões e aos operadores. O hash do conteúdo de cada minuta confere com o armazenado e com o da decisão. Conferência em modo somente leitura.
- O critério de RF24 na página 8 do enunciado aceita uma minuta aprovada e outra rejeitada **ou enviada para revisão**. As decisões humanas demonstradas atendem essa combinação. A matriz automática histórica continua com T11 parcial: suas decisões simuladas não foram reclassificadas como humanas.
- **Última suíte registrada:** 210 testes aprovados em 12,254 s, após a validação complementar e seus ajustes. Log: `resultados/logs/complementar_llm_final_2026-10-29_unittest.log`. As 201 aprovações anteriores permanecem históricas; a nova suíte inclui nove regressões de instrumentação e detector numérico.
- `python -m src.main verificar` executado nesta conferência: dependências principais disponíveis, chave OpenAI configurada sem expor seu valor e envio automático desativado. `git diff --check` passou.
- **RAG real:** rodada `20261029T222148Z_5018e2` preservada, com 5/5 respostas completas, 12/12 fatos essenciais, 2/2 abstenções corretas e conflito encaminhado. Não mede generalização; [relatório](reajuste_rag_openai_2026-10-29.md).

## O que falta ou permanece limitado

| Frente | Situação e próxima ação |
|---|---|
| Registro de uso de IA | Preenchido em nome de **Diego Assunção Leite**, em 29/10/2026, por autorização expressa nesta conversa. [Registro](uso_da_ia.md) distingue a conferência demonstrada por Diego das verificações técnicas do agente. Não atribui confirmação individual a Ayron ou Guilherme. |
| Cobertura do LLM real | Executada em 29/10/2026: seis extrações/resumos, 12 sentimentos, ataques com perfil real e bloqueio de segredo antes da chamada. Foram 29 chamadas no total, incluindo reteste de S02/S06; [relatório](validacao_complementar_llm_2026-10-29.md). ATQ02 permanece parcial no critério literal de quarentena no top-k. Os prints antigos continuam locais; a interface mantém extração/resumo por regras por padrão. |
| Versionamento e pacote | Há mudanças modificadas/não rastreadas, incluindo evidências. O ZIP final `entrega/desafio-06-central-atendimento-ia.zip` não existe. Revisar e versionar os arquivos de entrega; `scripts/gerar_zip_entrega.py` usa `git archive HEAD` e deixa de fora mudanças não commitadas. |
| Reprodução do pacote | Depois de gerar o ZIP completo, descompactar em pasta limpa e conferir instalação, testes e indexação conforme o README. A coleta de prints e a execução no ambiente atual não substituem essa verificação. |

Nenhum gabarito ou original foi adaptado. Os resultados automáticos e as falhas históricas foram preservados. Recursos novos de STT/OCR continuam limitados pelas ferramentas/chaves locais; o enunciado admite reaproveitar as transcrições e o OCR do Desafio 01, já usados na regressão.
