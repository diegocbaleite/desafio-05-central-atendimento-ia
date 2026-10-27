# Relatório técnico — Desafio 6 (Desafio Prático 02)

**Central Inteligente de Atendimento e Comunicação Institucional** · Equipe: Diego Assunção Leite, Ayron Brhenno Silva Figueiredo e Guilherme da Silva Lessa · SECITECI / Escola Técnica Estadual de Cuiabá · FIC_DEV — Inteligência Artificial Generativa · 27/10/2026.

## 1. Escopo e continuidade

Evolução do protótipo do Desafio Prático 01 (repositório `desafio-05-central-atendimento-ia`, preservado sem alterações) para as Aulas 08–14, requisitos **RF14–RF24**. O histórico Git foi mantido. Entradas de texto, a transcrição STT e o OCR conferido do Desafio 01 alimentam o mesmo fluxo. O experimento de prompts A/B/C, a geração de imagem e a síntese de voz **não** foram refeitos. A Aula 15 (memória e persona) está fora do escopo.

## 2. Arquitetura

Camadas separadas (ver diagrama no README):

1. **Entrada e proteção** — `guardrails.avaliar_entrada`: tamanho, vazio, pedido de segredo, injeção, moderação (ameaça/insulto) e escopo léxico + semântico (similaridade com o acervo). Decisão `permitir | revisar | bloquear`.
2. **Compreensão** — `estruturacao` produz a ficha no contrato `solicitacao.v2.0.0` (regras locais reaproveitando `extracao.py`, ou LLM); `contrato.validar` aplica sintaxe → esquema → regras de negócio; `nlp` gera resumo ≤100 palavras, categoria e entidades literais com evidência, separando inferências.
3. **Indexação** — `ingestao` lê TXT e PDF textual por página, divide por seção em janelas de palavras e marca trechos suspeitos; `embeddings` (fastembed, modelo aberto local) e `indice` (Chroma persistente + manifesto JSON com modelo, dimensão, versão, SHA-256 por documento e exclusões).
4. **Recuperação e geração** — `rag.responder`: guardrail → top-k → filtro por limiar e quarentena → gerador (`geracao`) → verificação de cada afirmação → detecção de conflito → filtro de saída → status decidido por código.
5. **Revisão** — `revisao` (SQLite) persiste minutas e decisões com operador, justificativa, origem e SHA-256 da versão decidida.
6. **Sentimentos e painel** — `sentimento` (regras locais ou LLM) e `metricas` (proporções com numerador/denominador, deduplicação por ID, filtros e conjunto vazio).
7. **Auditoria** — `auditoria.registrar_d6` grava JSONL sanitizado.

## 3. Provedor configurável (RF21)

- `config/config.yaml → geracao.perfis`: `principal` (LLM Gemini `gemini-3.1-flash-lite` via endpoint OpenAI-compatible, temperatura 0,1, 1.200 tokens, saída estruturada), `extrativo_local` (determinístico, **não-LLM**) e `simulado` (testes).
- A chamada ao provedor fica isolada em `cliente.conversar` (timeout de 45 s, **no máximo 1 repetição** para 429/5xx/timeout, orçamento consultado antes de **cada** requisição, inclusive repetições e correções de esquema).
- A recuperação é configurada à parte (`recuperacao.*`). O T12 mostrou o mesmo índice (hash do manifesto e contagem inalterados) atendendo o gerador extrativo, o perfil LLM (falhou por falta de chave, com erro tratado e auditado) e uma falha 503 simulada.
- **Segunda configuração demonstrada:** `extrativo_local`. Ela não é um LLM e não tem qualidade equivalente; só prova que a interface do adaptador é trocável sem reindexar.

## 4. Decisões técnicas principais

| Decisão | Motivo |
|---|---|
| JSON Schema 2020-12 (jsonschema já era dependência) | Distingue `chave_extra`, `tipo_incorreto` e `campo_obrigatorio_ausente`; o esquema é enviado como `response_format` e **sempre** revalidado localmente |
| Regras de negócio separadas do esquema | Conformidade ao esquema não garante veracidade: datas reais, valores presentes no original, coerência entre nulos e `campos_ausentes`, revisão obrigatória quando há lacuna |
| Embeddings locais (fastembed/ONNX, 384 dimensões) | Sem envio do acervo a terceiros e sem custo por token; roda em CPU |
| Chroma persistente + manifesto próprio | IDs determinísticos e SHA-256 por documento impedem duplicatas; o manifesto detecta troca de modelo/dimensão/versão (`reindexacao_exigida`) e documentos alterados ou órfãos |
| Status do RAG decidido por código | O gerador sugere; o código verifica citação literal, números e cobertura de termos, remove afirmações sem suporte, detecta conflito (mesma unidade, valores diferentes, documentos distintos) e só então decide |
| Resposta exibida montada só com afirmações verificadas | Fecha o caminho em que texto livre do gerador traria conteúdo não verificado (ajuste nº 4) |
| Abstenção por cobertura ponderada por IDF | Similaridade de cosseno alta não garante resposta: nas perguntas sem resposta, trechos com similaridade de 0,42–0,51 foram recuperados, e a cobertura dos termos raros (taxa, carteira, transporte) é que levou à abstenção |
| Documento com trecho suspeito vira “documento suspeito” | Defesa em profundidade: o trecho malicioso nunca entra no contexto, e uma resposta que cite outra parte do mesmo documento vai para revisão (ajuste nº 2) |

## 5. Métricas (execução `20261027T194525Z_43f775`, gerador extrativo, embedding real local)

| Métrica | Numerador/denominador |
|---|---|
| Acurácia de categorias (6 solicitações) | 6/6 |
| Campos críticos corretos | 18/18 |
| Entidades esperadas encontradas / extras | 20/20 / 0 |
| Fatos essenciais no resumo | 17/17 |
| Acerto de recuperação — config A (120/30 palavras) | 5/5 |
| Acerto de recuperação — config B (50/10 palavras) | 5/5 |
| Respondíveis fundamentadas com fonte esperada | 5/5 |
| Respostas com todas as afirmações sustentadas | 5/5 (por construção do gerador extrativo) |
| Abstenção correta | 2/2 |
| Caso contraditório (P08) | `conflito_de_fontes`, DOC-03 × DOC-05, encaminhado à revisão |
| Sentimentos (12) | 12/12; incertos sinalizados 3/3 |
| Matriz T01–T15 | 14 aprovados, 1 parcial |

Os números completos, por pergunta e por solicitação, estão em [`resultados_avaliacao.md`](resultados_avaliacao.md), gerado das evidências JSON.

**Interpretação.** Os 100% vêm de regras escritas conhecendo os dados e de um gerador que copia frases; servem para provar que o fluxo, as verificações e as métricas por código funcionam, **não** para estimar desempenho em dados novos. Falhas observadas e ajustes estão em [`registro_ajustes.md`](registro_ajustes.md). Uma falha real permanece: na S04, o sub-pedido “como acompanhar a solicitação” não recuperou a seção correta no top-4 e o sistema se absteve.

## 6. Custos e recursos

- **Nenhuma chamada paga foi feita nesta etapa.** Os embeddings são locais (custo monetário zero por token; a primeira indexação dos 7 documentos levou cerca de 2 s em CPU, após o download do modelo). A avaliação completa levou 15,0 s.
- Tokens e custo ficam como `"indisponível"` na auditoria das execuções locais; com LLM, o sistema registra os tokens informados pelo provedor e **não** estima os ausentes (`Orcamento.tokens_indisponiveis`).
- Preços de referência do Gemini constam no README do Desafio 01 (consulta de 18/10/2026) e **não foram reconsultados**; confirme nas páginas oficiais antes de executar o perfil `principal`.
- Orçamento padrão por execução: 30 chamadas e 60.000 tokens (`guardrails.max_chamadas_execucao`, `max_tokens_execucao`).

## 7. Privacidade e segurança

- Somente dados fictícios. Os textos reaproveitados do Desafio 01 já eram fictícios e preservados.
- Minimização: CPF, e-mail e telefone são mascarados antes de ir ao provedor (`seguranca.minimizar`) e nos logs; protocolos aparecem parcialmente mascarados (`2026-****42`); a auditoria guarda hash e consulta minimizada, nunca o texto bruto da solicitação.
- Credenciais: lidas do `.env` (ignorado); `filtrar_saida` e `mascarar` removem valores de chaves configuradas e padrões de credencial. No ATQ03 um canário aleatório criado em memória não apareceu nas saídas nem nos logs.
- Retenção, exclusão e direitos: ver [`privacidade_retencao.md`](privacidade_retencao.md).
- Revisão humana: estados `pendente/aprovada/rejeitada/revisar`; operador e justificativa obrigatórios; decisões simuladas têm origem `simulada_teste` e ficam fora das contagens humanas; a minuta identifica a participação de IA/automação; não existe função de envio.

## 8. Riscos residuais

1. **LLM real não validado:** comportamento com o Gemini (aderência ao esquema, citações, recusa) é desconhecido até a execução com credencial.
2. **Regras locais frágeis:** extração, categorias, entidades e sentimentos por regras acertam o conjunto de teste, mas falham com formulações novas (sinônimos, erros de STT, ironia sutil).
3. **Verificação de suporte é léxica:** confere citação literal, números e sobreposição de termos; uma paráfrase correta pode ser removida, e uma afirmação que reutiliza as palavras do trecho com sentido invertido (ex.: negação) pode passar.
4. **Detecção de conflito limitada a quantidades com unidade** (dias, horas, R$); divergências qualitativas não são detectadas.
5. **Guardrails heurísticos:** padrões de injeção e de segredo podem ser contornados. A mitigação estrutural (segredo nunca no prompt, quarentena, saída montada só com afirmações verificadas, revisão humana) reduz o impacto, mas não o elimina.
6. **Índice local sem controle de acesso;** em uso real exigiria autenticação, criptografia e trilha de auditoria imutável.
7. **Revisão humana real ainda não demonstrada** pela equipe na interface.

## 9. Validações pendentes (ações concretas)

| Pendência | Ação |
|---|---|
| Execução com LLM real | Criar `.env` com `GEMINI_API_KEY`; rodar `python -m src.main consultar "..." --gerador principal`, `python -m src.main sentimentos --gerador principal` e `python -m src.main avaliar --gerador principal`; registrar tokens, latência e resultados ao lado dos atuais |
| Extração por LLM | Definir `estruturacao.modo: "llm"` e processar S01–S06; comparar com a extração por regras |
| Demonstração humana (T11/RF24) | Na interface, um integrante aprova uma minuta e outro rejeita ou pede revisão, com justificativas; exportar a aba Auditoria |
| Nova transcrição/OCR | Opcional: com `GROQ_API_KEY`/Tesseract, processar `entrada_audio.mp3`/`entrada_pdf-imagem.pdf` pela aba Solicitação |
