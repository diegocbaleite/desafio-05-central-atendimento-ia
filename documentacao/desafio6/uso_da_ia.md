# Registro do uso de IA no desenvolvimento — Desafio 6

A responsabilidade pela solução é da equipe (Diego Assunção Leite, Ayron Brhenno Silva Figueiredo e Guilherme da Silva Lessa). Este registro descreve o uso de agentes de codificação e as evidências de validação. Em **29/10/2026**, Diego Assunção Leite pediu expressamente que o registro fosse preenchido em seu nome. A confirmação ao final foi redigida pelo agente a seu pedido e abrange Diego; não declara conferência individual por Ayron ou Guilherme.

## Ferramentas e modelos

| Ferramenta | Modelo / versão | Uso |
|---|---|---|
| Claude Code (extensão VS Code, Windows 11) | Claude Opus 5.5 (`claude-opus-5-5`) | Leitura do PDF e do repositório, implementação, testes, execução da avaliação e documentação, em 27/10/2026 |
| Codex (OpenAI) | Identificador exato do modelo: não localizado | Revisão de prontidão e correções; depois, execução autorizada de RAG e validações complementares com o LLM real, organização de evidências e documentação; sem decisões humanas produzidas pelo agente |
| Modelo de embedding (dentro do produto, não de desenvolvimento) | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` via fastembed 0.9.1 | Recuperação vetorial local |
| LLM do produto | OpenAI `gpt-6-luna` (principal desde 29/10/2026; antes, Gemini) | Conexão, duas rodadas RAG reais e validação complementar de extração, resumo, sentimentos e ataques; reteste de S02/S06; histórico e limitações preservados |

## Solicitações relevantes feitas ao agente

1. **Implementação do Desafio Prático 02 a partir do Desafio 01** — implementar RF14–RF24 reaproveitando o repositório anterior, preservando autoria e histórico, sem alterar o repositório `desafio-05`, com gabaritos prévios, testes e documentação honesta sobre simulações.
2. **Publicação em repositório novo** — o repositório `desafio-06-central-atendimento-ia` foi criado manualmente pela equipe; o agente clonou o projeto anterior, trocou os remotos (o antigo ficou só para leitura, com push desativado) e publicou no novo.
3. **Validação** — executar os testes existentes antes das mudanças (linha de base: 114 testes OK), os novos testes e a CLI, diferenciando execução local, simulação e modelo real.
4. **Revisão e correções por etapa** — verificar prontidão contra o enunciado e corrigir, uma a uma, as falhas de suporte das afirmações, prioridade de fontes, orçamento e caminhos de upload, preservando originais e gabaritos.

## Sugestões do agente e destino

| Sugestão / decisão do agente | Situação | Observação |
|---|---|---|
| Versionar gabaritos e parâmetros de avaliação em commit próprio **antes** dos avaliadores | Conferência técnica registrada; preenchimento em nome de Diego autorizado em 29/10/2026 | Histórico Git: `e24dd15` contém os gabaritos e precede `2930e6a`, primeiro commit de `src/avaliacao_integrada.py`; ancestralidade conferida pelo agente |
| Usar embeddings locais (fastembed) + Chroma em vez de API | Aceita pelo agente | Sem chave disponível; evita enviar o acervo a terceiros |
| Gerador `extrativo_local` como segunda configuração | Aceita, com ressalva explícita de não ser LLM | Permite demonstrar o fluxo sem credencial, sem alegar qualidade equivalente |
| Status do RAG decidido por código, não pelo gerador | Aceita | Base de T08–T10 |
| Dividir frases também em `;` | **Rejeitada após teste** | Quebrava listas (P01); ajuste nº 1 |
| Usar o texto livre do LLM como resposta quando as citações batem | **Rejeitada após revisão** | Abria caminho para conteúdo não verificado; ajuste nº 4 |
| Quarentena apenas do trecho suspeito | **Modificada** | Passou a marcar o documento inteiro como suspeito ao ser citado; ajuste nº 2 |
| Reutilizar o limiar de recuperação no guardrail de escopo | **Modificada** | Falha em teste; criado `guardrails.limiar_escopo_semantico` |
| Reduzir repetições do cliente de 2 para 1 | Aceita | Exigência do RF16; teste antigo atualizado e comentado |
| Correções autorizadas por Diego durante a revisão | Aceitas para implementação: verificação literal das afirmações, prioridade de fontes, orçamento de consultas, proteção de uploads e reajuste do RAG | Autorizações e acompanhamento na conversa; detalhes, modificações e limitações em `registro_ajustes.md`. As decisões técnicas históricas atribuídas ao agente nas linhas anteriores permanecem identificadas como tais |

## Erros encontrados e como foram validados

| Erro | Como apareceu | Correção | Validação |
|---|---|---|---|
| PDFs tratados como texto pelo Git (CRLF) | Aviso do Git no primeiro commit | `.gitattributes` com `*.pdf binary` e LF fixo no acervo | Hash do blob igual ao do arquivo |
| Resposta P01 incompleta | 1ª execução do RAG | Divisão de frases sem `;` | Reexecução: fatos de P01 presentes |
| Falso “fato sem suporte” na S02 | 1ª avaliação integrada (T03 parcial) | Datas normalizadas do original contam como suportadas | T03 aprovado na execução final |
| Dimensão do índice gravada como `null` | `status-indice` após reindexar sem mudanças | Preservar a dimensão já registrada | Novo teste em `test_d6_indice_rag` |
| Parâmetro depreciado do Streamlit | Aviso na execução headless | `width="stretch"` | Teste da interface sem avisos |

Validação original em 27/10/2026: `python -m unittest discover -s testes -t .` (176 testes), `python -m src.main verificar`, `python -m src.main avaliar --publicar-evidencias`, servidor Streamlit iniciado (`/_stcore/health` = ok) e execução headless da interface com o modelo de embedding real. Nessa rodada, nenhuma chamada a LLM real foi feita; nenhuma decisão humana foi registrada pelo agente (as decisões dos testes têm origem `simulada_teste`).

## Declaração

Atualização técnica inicial em 29/10/2026: 188 testes passaram; a avaliação local `20261029T214410Z_517c20` manteve 14 aprovados e T11 parcial. As sugestões implementadas e suas limitações estão em `registro_ajustes.md`, itens 5–8. A confirmação de Diego foi registrada posteriormente, ao final deste documento; ela não altera a natureza dessa avaliação automática histórica.

Configuração OpenAI em 29/10/2026: suíte ampliada inicialmente para 192 testes aprovados. Uma chamada real, com mensagem técnica fictícia sem documentos do projeto, confirmou OpenAI/GPT-6 Luna e JSON restrito (55 tokens de entrada, 13 de saída). A revisão automática inicialmente exigiu consentimento específico para envio dos trechos do acervo à API externa. Após o usuário autorizar, as oito perguntas RAG foram executadas na rodada `20261029T221237Z_33cce1`: duas respondíveis completas, uma parcial, duas abstenções por formato, duas abstenções corretas sem fonte e conflito encaminhado. Foram medidos 7.894 tokens de entrada e 1.201 de saída. A suíte passou com **193 testes** após acrescentar a regressão do registro de método/modelo/tokens. A chave no `.env` foi preservada. Ver [relatório real](avaliacao_rag_openai_2026-10-29.md).

Após pedido de reajuste, o verificador passou a aceitar sequências contíguas de frases completas de um mesmo trecho, e o prompt 1.2 passou a exigir que `texto` e `citacao_literal` fossem a mesma cópia, preservando listas. A revalidação local das respostas antigas confirmou P04/P05 e continuou recusando a paráfrase de P01. A nova rodada real `20261029T222148Z_5018e2` teve 5/5 respondíveis completas, 12/12 fatos, 2/2 abstenções corretas e conflito encaminhado; T08–T10 aprovados. A suíte passou com **200 testes**. Os ajustes foram feitos conhecendo os casos, sem alterar gabaritos; as duas rodadas foram preservadas. Ver [comparação antes/depois](reajuste_rag_openai_2026-10-29.md).

Atualização da demonstração e do fechamento em 29/10/2026: Diego registrou pela interface o pedido de revisão de UI-001 e a aprovação de UI-002. Os estados, operadores, origem humana e hashes foram conferidos por leitura do banco; os 15 prints e cinco JSONs do [catálogo](evidencias_humanas/README.md) estão presentes e conferidos. O agente organizou as imagens e copiou registros já persistidos, sem produzir essas decisões. Foram acrescentadas a orientação de sessão vazia do painel e a correção do destino de auditoria da CLI, com regressões e **201 testes aprovados**, conforme itens 12–13 de `registro_ajustes.md`. O preenchimento da confirmação abaixo foi solicitado expressamente por Diego; não representa revisão técnica independente de cada linha do código por ele ou pelos outros integrantes.

### Confirmação de Diego Assunção Leite

| Campo | Registro |
|---|---|
| Responsável por esta confirmação | **Diego Assunção Leite** |
| Data | **29/10/2026 — America/Cuiaba** |
| Origem do preenchimento | Autorização expressa de Diego nesta conversa para preencher o registro em seu nome; texto redigido pelo agente a seu pedido |
| Conferência demonstrada por Diego | Operação da interface, conferência da fonte DOC-02, aprovação de UI-002 e pedido de revisão de UI-001 com justificativas; acompanhamento e envio dos prints |
| Conferência técnica executada pelo agente | Histórico dos gabaritos, testes automatizados, JSONs, arquivos de evidência, estados e hashes das decisões; resultados e limitações documentados |

Eu, **Diego Assunção Leite**, autorizo este registro do uso de IA em meu nome. O projeto recebeu auxílio de agentes de codificação para implementação, correções, testes e documentação. Acompanhei a demonstração da interface e registrei as decisões humanas de aprovação e pedido de revisão identificadas neste documento. As correções que solicitei e autorizei permanecem descritas com suas validações e limitações.

O registro distingue a execução real do RAG, os métodos por regras locais e as simulações de testes. As limitações das validações executadas e o fechamento do pacote continuam indicados na [verificação de fechamento](verificacao_fechamento_2026-10-29.md). Esta confirmação não declara que todos os caminhos foram executados com LLM real, nem substitui a responsabilidade da equipe pela entrega.

Conteúdo elaborado com auxílio de IA. **Não há confirmação individual registrada neste documento em nome de Ayron ou Guilherme.**
