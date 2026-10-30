# Parecer de entrega após integração — 30/10/2026

## Conclusão

A entrega principal (`src/app.py`, comandos diretos e acervo fictício `dados/acervo/`) contém implementação e evidências para RF14–RF24 e os entregáveis da seção 13 do enunciado. Está apta à entrega acadêmica **com as limitações declaradas**, após gerar e conferir o ZIP do commit integrado. Não é uma declaração de desempenho perfeito ou homologação. A implementação paralela importada da main foi preservada, mas seus documentos e resultados não substituem o conjunto avaliado.

O enunciado foi extraído e lido integralmente (13 páginas). Ele permite reutilizar STT/OCR, não exige nova geração de áudio/imagem, aceita segunda configuração simulada identificada e exige relato de falhas. RF24 aceita uma aprovação e outra rejeição **ou pedido de revisão**; as evidências versionadas registram aprovação de UI-002 e pedido de revisão de UI-001. T11 automático permanece parcial porque suas decisões são simuladas; não foi reclassificado como humano.

## Conferência executada nesta integração

| Verificação | Resultado |
|---|---|
| Suíte das duas implementações | 322 testes aprovados, Python 3.12.14/Linux |
| Sintaxe | `python -m compileall -q src testes`, sem erro |
| Dependências | `python -m pip check`: sem incompatibilidades |
| Configuração | `python -m src.main verificar`, envio automático desativado; chaves ausentes; eSpeak ausente |
| CLI | Ajuda principal e `desafio6 --help` executadas |
| Acervo principal | Sete documentos existentes; três temas; TXT/PDF; seis documentos regulares e um adversarial |
| Gabaritos | Seis solicitações, oito perguntas RAG, doze sentimentos, três ataques e quinze cenários T01–T15 |
| Evidências | 118 JSONs, quatro JSONLs válidos e quinze PNGs íntegros em `documentacao/desafio6/` |
| RAG real histórico | Oito arquivos P01–P08 e resumo da rodada `20261029T222148Z_5018e2` presentes |
| Credenciais/serviços | Nenhuma nova chamada paga; evidências reais anteriores preservadas |

A integridade atual de JSON/PNG não é uma nova decisão humana nem autenticação independente da execução passada. A conferência de conteúdo e as decisões originais continuam atribuídas aos operadores identificados nos registros. Os testes usam transportes simulados e embeddings determinísticos próprios de teste.

## Cobertura da seção 13 do enunciado

| Entregável | Local |
|---|---|
| Código, dependências, configuração e instruções | `src/`, `requirements.txt`, `config/config.yaml`, `README.md` |
| Dados fictícios, acervo e gabaritos prévios | `dados/acervo/`, `dados/solicitacoes/`, `dados/avaliacoes/`, `dados/ataques/`, `dados/gabaritos/desafio6/` |
| JSON sintático/esquema, resumo, categorias e entidades | `evidencias/rf14_comparacao_json.json`, demais evidências RF14/RF15 e `validacao_complementar_llm_2026-10-29.md` |
| Chunking e índice reproduzível | `evidencias/rf18_chunking.json`, configuração A/B e comandos `indexar`/`status-indice` |
| Oito consultas RAG e três ataques | `evidencias_openai/rag_20261029T222148Z_5018e2/`, `validacao_complementar_llm_2026-10-29.md` e suas evidências vinculadas |
| Sentimentos, métricas e painel | `dados/avaliacoes/`, evidências RF22/RF23, capturas 06 e variantes |
| Matriz, regressão, auditoria e exclusão | `evidencias/matriz_T01_T15.*`, arquivos RF23/RF24, auditorias sanitizadas e testes de exclusão |
| Relatório e uso de IA | `relatorio_tecnico.md`, `uso_da_ia.md`, `privacidade_retencao.md` |
| Apresentação de até quinze minutos | `roteiro_apresentacao_15min.md` |

## Limitações residuais

1. ATQ02 mantém critério literal parcial: o trecho malicioso específico não entrou no top-4; houve encaminhamento seguro por outra passagem suspeita. Não houve vazamento de segredo ou envio autorizado pelo ataque.
2. S04 contém um subpedido não recuperado, com abstenção registrada. A comparação A/B discrimina pouco por usar seções curtas.
3. O conjunto é pequeno/conhecido; houve ajuste de prompt e reteste de S02/S06. As métricas consolidadas não equivalem a nova rodada completa nem a avaliação de generalização.
4. A interface usa compreensão por regras por padrão; as evidências LLM são rodadas separadas e identificadas.
5. Não há chave neste ambiente para reproduzir chamadas reais. O primeiro download do embedding depende da rede; a reprodução histórica em cópia limpa está em `fechamento_entrega_2026-10-30.md` e não foi tratada como nova execução.
6. A implementação paralela da main tem outro catálogo. A equipe deve demonstrar a versão indicada no README, sem aplicar as métricas do acervo fictício a documentos diferentes.

O pacote é preparado para a equipe submeter. Este trabalho não registra novas decisões de aprovação em nome de pessoas e não envia arquivos à instituição.
