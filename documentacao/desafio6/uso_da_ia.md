# Registro do uso de IA no desenvolvimento — Desafio 6

A responsabilidade pela solução é da equipe (Diego Assunção Leite, Ayron Brhenno Silva Figueiredo e Guilherme da Silva Lessa). Este registro descreve o uso de um agente de codificação. Os campos marcados como **“a preencher pela equipe”** dependem de avaliação humana e não foram preenchidos pelo agente.

## Ferramentas e modelos

| Ferramenta | Modelo / versão | Uso |
|---|---|---|
| Claude Code (extensão VS Code, Windows 11) | Claude Opus 5.5 (`claude-opus-5-5`) | Leitura do PDF e do repositório, implementação, testes, execução da avaliação e documentação, em 27/10/2026 |
| Modelo de embedding (dentro do produto, não de desenvolvimento) | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` via fastembed 0.9.1 | Recuperação vetorial local |
| LLM do produto | Gemini `gemini-3.1-flash-lite` (configurado) | **Não executado** nesta etapa por falta de credencial |

## Solicitações relevantes feitas ao agente

1. **Implementação do Desafio Prático 02 a partir do Desafio 01** — implementar RF14–RF24 reaproveitando o repositório anterior, preservando autoria e histórico, sem alterar o repositório `desafio-05`, com gabaritos prévios, testes e documentação honesta sobre simulações.
2. **Publicação em repositório novo** — o repositório `desafio-06-central-atendimento-ia` foi criado manualmente pela equipe; o agente clonou o projeto anterior, trocou os remotos (o antigo ficou só para leitura, com push desativado) e publicou no novo.
3. **Validação** — executar os testes existentes antes das mudanças (linha de base: 114 testes OK), os novos testes e a CLI, diferenciando execução local, simulação e modelo real.

## Sugestões do agente e destino

| Sugestão / decisão do agente | Situação | Observação |
|---|---|---|
| Versionar gabaritos e parâmetros de avaliação em commit próprio **antes** dos avaliadores | Aceita pelo agente; validação da equipe **a preencher** | Ver `git log -- dados/gabaritos/desafio6` |
| Usar embeddings locais (fastembed) + Chroma em vez de API | Aceita pelo agente | Sem chave disponível; evita enviar o acervo a terceiros |
| Gerador `extrativo_local` como segunda configuração | Aceita, com ressalva explícita de não ser LLM | Permite demonstrar o fluxo sem credencial, sem alegar qualidade equivalente |
| Status do RAG decidido por código, não pelo gerador | Aceita | Base de T08–T10 |
| Dividir frases também em `;` | **Rejeitada após teste** | Quebrava listas (P01); ajuste nº 1 |
| Usar o texto livre do LLM como resposta quando as citações batem | **Rejeitada após revisão** | Abria caminho para conteúdo não verificado; ajuste nº 4 |
| Quarentena apenas do trecho suspeito | **Modificada** | Passou a marcar o documento inteiro como suspeito ao ser citado; ajuste nº 2 |
| Reutilizar o limiar de recuperação no guardrail de escopo | **Modificada** | Falha em teste; criado `guardrails.limiar_escopo_semantico` |
| Reduzir repetições do cliente de 2 para 1 | Aceita | Exigência do RF16; teste antigo atualizado e comentado |
| Sugestões aceitas/rejeitadas pela equipe ao revisar este trabalho | **a preencher pela equipe** | — |

## Erros encontrados e como foram validados

| Erro | Como apareceu | Correção | Validação |
|---|---|---|---|
| PDFs tratados como texto pelo Git (CRLF) | Aviso do Git no primeiro commit | `.gitattributes` com `*.pdf binary` e LF fixo no acervo | Hash do blob igual ao do arquivo |
| Resposta P01 incompleta | 1ª execução do RAG | Divisão de frases sem `;` | Reexecução: fatos de P01 presentes |
| Falso “fato sem suporte” na S02 | 1ª avaliação integrada (T03 parcial) | Datas normalizadas do original contam como suportadas | T03 aprovado na execução final |
| Dimensão do índice gravada como `null` | `status-indice` após reindexar sem mudanças | Preservar a dimensão já registrada | Novo teste em `test_d6_indice_rag` |
| Parâmetro depreciado do Streamlit | Aviso na execução headless | `width="stretch"` | Teste da interface sem avisos |

Validação geral: `python -m unittest discover -s testes -t .` (176 testes), `python -m src.main verificar`, `python -m src.main avaliar --publicar-evidencias`, servidor Streamlit iniciado (`/_stcore/health` = ok) e execução headless da interface com o modelo de embedding real. **Nenhuma** chamada a LLM real foi feita; nenhuma decisão humana foi registrada pelo agente (as decisões dos testes têm origem `simulada_teste`).

## Declaração

Conteúdo gerado com auxílio de IA. A conferência final, a demonstração humana e a responsabilidade pela entrega pertencem à equipe: **a preencher pela equipe** (nome, data e conferência).
