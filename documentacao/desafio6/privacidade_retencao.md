# Privacidade, retenção e exclusão — Desafio 6 (RF24)

Protótipo acadêmico com **dados exclusivamente fictícios**. Uma implantação real exigiria análise jurídica (LGPD), contratual e de segurança.

## Dados tratados e minimização

| Dado | Onde aparece | Tratamento |
|---|---|---|
| Texto da solicitação | memória durante o processamento; minuta | Não é gravado na auditoria (só SHA-256); CPF, e-mail e telefone mascarados antes de ir ao provedor e na minuta |
| Nome, protocolo e data | ficha estruturada e minuta | Necessários ao atendimento; nos logs o protocolo é mascarado (`2026-****42`) |
| Pergunta ao acervo | consulta RAG | Log com versão minimizada (máx. 200 caracteres) + SHA-256 |
| Acervo institucional | `dados/acervo/`, índice | Documentos fictícios; embeddings gerados localmente, sem envio a terceiros |
| Credenciais | `.env` | Nunca em prompt, código, log ou evidência; saídas e logs filtram valores configurados |

## Retenção (padrões do protótipo, em `config.yaml → privacidade`)

| Artefato | Local | Retenção |
|---|---|---|
| Documentos versionados do acervo | `dados/acervo/` | Enquanto o exercício existir |
| Documentos enviados pela interface | `dados/acervo/enviados/` (fora do Git) | Até exclusão explícita |
| Vetores | `indice/` (fora do Git) | Até exclusão do documento ou `indexar --recriar` |
| Respostas RAG salvas e resultados de avaliação | `resultados/rag/`, `resultados/avaliacao_d6/` | 90 dias (`privacidade.aplicar_retencao`) |
| Minutas e decisões | `resultados/revisao/revisoes.sqlite3` | Preservadas como registro da decisão humana; descarte manual ao fim do exercício |
| Logs de auditoria | `resultados/logs/auditoria_d6.jsonl` | 180 dias |

## Exclusão de documento

```bash
python -m src.main excluir-documento --doc DOC-06
python -m src.main status-indice          # DOC-06 aparece em "excluidos"
python -m src.main indexar --doc DOC-06   # reinclusão explícita, se desejada
```

A exclusão: (1) remove os vetores do documento em todas as configurações de chunking e confirma 0 trechos restantes; (2) apaga respostas RAG salvas que citam o documento; (3) remove arquivo e entrada do catálogo de enviados, quando o documento veio da interface; (4) lista minutas afetadas sem alterar decisões humanas; (5) registra o evento `exclusao_documento` na auditoria, sem conteúdo do documento.

**Demonstração (T14):** antes da exclusão a consulta “Por quanto tempo os registros de solicitações são mantidos?” trazia trechos do DOC-06; depois, 3 trechos e 1 derivado foram removidos, o DOC-06 não apareceu mais no top-4 e a reindexação comum não o recriou (`evidencias/rf24_t14_exclusao.json`).

## Revisão humana e participação da IA

- Toda minuta nasce `pendente`, com o aviso “Conteúdo preparado com apoio automatizado (gerador: …; LLM: sim/não)”.
- Decisões aceitas: `aprovar`, `rejeitar`, `revisar`; operador (≥3 caracteres) e justificativa (≥5) obrigatórios; `aprovada` e `rejeitada` são finais para aquela versão.
- Cada decisão guarda o SHA-256 da minuta decidida e a origem: `humana_interface`, `humana_cli` ou `simulada_teste`. Decisões simuladas **nunca** contam como humanas.
- Aprovar **não envia** nada; o sistema não possui função de envio.
