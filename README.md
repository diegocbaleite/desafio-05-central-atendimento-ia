# 🏛️ Desafio 6 — Central Inteligente de Atendimento e Comunicação Institucional

Protótipo local em **Python** que recebe solicitações fictícias (texto, transcrição de áudio ou OCR), **valida e estrutura** os dados, **resume e classifica**, consulta um **acervo institucional fictício** por busca vetorial (RAG) e prepara **minutas com fontes verificáveis** para **revisão humana**. Inclui interface **Streamlit**, guardrails, painel de sentimentos e trilha de auditoria.

> **Nenhuma resposta é enviada automaticamente.** Toda minuta nasce `pendente` e só um servidor responsável pode aprová-la, rejeitá-la ou pedir revisão. Todos os dados são fictícios.

## 👥 Identificação

| | |
|---|---|
| **Equipe** | Diego Assunção Leite · Ayron Brhenno Silva Figueiredo · Guilherme da Silva Lessa |
| **Instituição** | SECITECI / Escola Técnica Estadual de Cuiabá |
| **Curso** | FIC_DEV — Programador de Sistemas com IA |
| **Módulo** | Inteligência Artificial Generativa (Aulas 08 a 14) |
| **Atividade** | Desafio Prático 02, versão 2.0 — 2026 |
| **Repositório** | <https://github.com/diegocbaleite/desafio-06-central-atendimento-ia> |

Divisão inicial de responsabilidades (todos devem compreender e demonstrar a solução inteira):

- **Diego Assunção Leite — Estudante 1:** esquemas, NLP, dados fictícios e gabaritos.
- **Ayron Brhenno Silva Figueiredo — Estudante 2:** embeddings, índice, RAG e abstração de provedor.
- **Guilherme da Silva Lessa — Estudante 3:** guardrails, Streamlit, sentimentos e painel.

### Continuidade e numeração

No GitHub esta evolução se chama **Desafio 6**. No enunciado acadêmico ela corresponde ao **Desafio Prático 02** (“Central Inteligente de Atendimento e Comunicação Institucional”, Aulas 08 a 14), que é a **continuação do Desafio Prático 01**. O Desafio Prático 01 está no repositório [`desafio-05-central-atendimento-ia`](https://github.com/diegocbaleite/desafio-05-central-atendimento-ia), que **não foi alterado**. Este repositório parte dele **com o histórico Git preservado** (commits e autoria dos três estudantes). Os requisitos continuam a numeração: RF01–RF13 no Desafio 01, **RF14–RF24** aqui. Memória conversacional e persona (Aula 15) ficam para uma etapa posterior.

O README original do Desafio 01 foi preservado em [`documentacao/desafio1/README_desafio1.md`](documentacao/desafio1/README_desafio1.md).

---

## 🧭 Arquitetura

```
entrada (texto | transcrição STT | OCR)            acervo (TXT + PDF textual)
        │                                                   │
  guardrails de entrada (tamanho, escopo,          ingestao.py: páginas, seções, chunks
  segredo, injeção, moderação)                     guardrails: trecho suspeito → quarentena
        │                                                   │
  estruturacao.py → contrato.py (JSON Schema v2.0.0  embeddings.py (modelo aberto local)
  + regras de negócio; LLM: ≤1 correção)                    │
        │  inválido → BLOQUEIA a minuta              indice.py (Chroma persistente + manifesto)
  nlp.py: resumo ≤100 palavras, categoria,                   │
  entidades literais × inferências                  rag.py: top-k → geração (geracao.py)
        │                                           → verificação de citações → conflito
        └──────────────► pipeline.py ◄──────────────────────┘
                              │ minuta (fatos do solicitante ≠ orientações com fontes)
                     filtro de saída (segredos, dados pessoais)
                              │
                 revisao.py (SQLite: pendente/aprovada/rejeitada/revisar)
                              │
        app.py (Streamlit) · cli_d6.py · auditoria.py (JSONL sanitizado) · metricas.py
```

**Recuperação e geração são separadas.** A recuperação usa embeddings locais e o índice Chroma; a geração é um adaptador escolhido por perfil em `config/config.yaml` (`geracao.perfis`). Trocar o gerador não toca no índice; trocar o modelo de embedding exige reindexação.

| Módulo | Função | RF |
|---|---|---|
| `src/contrato.py`, `src/schemas/solicitacao.v2.schema.json` | Contrato versionado, erros por tipo e regras de negócio | RF14 |
| `src/estruturacao.py`, `src/llm_json.py` | Ficha por regras locais ou LLM com saída restrita e ≤1 correção | RF14 |
| `src/nlp.py` | Resumo, categoria, entidades, avaliação contra gabarito | RF15 |
| `src/guardrails.py`, `src/orcamento.py`, `src/cliente.py` | Camadas de entrada/acervo/saída, teto de chamadas e tokens, 1 repetição | RF16 |
| `src/ingestao.py`, `src/embeddings.py`, `src/indice.py` | Leitura TXT/PDF, chunking, embeddings, índice persistente | RF17/RF18 |
| `src/geracao.py`, `src/rag.py` | Adaptadores de geração, verificação de citações, abstenção e conflito | RF19/RF21 |
| `src/pipeline.py`, `src/app.py`, `src/revisao.py` | Fluxo integrado, interface e revisão persistida | RF20/RF24 |
| `src/auditoria.py` | Eventos JSONL com mascaramento e sem credenciais | RF21 |
| `src/sentimento.py`, `src/metricas.py` | Polaridade e agregação determinística | RF22/RF23 |
| `src/avaliacao_integrada.py` | Matriz T01–T15 e evidências | RF23 |
| `src/privacidade.py` | Exclusão de documento, vetores e derivados; retenção | RF24 |

Módulos do Desafio 01 reutilizados: `config.py`, `cliente.py` (agora com orçamento e 1 repetição), `seguranca.py` (delimitação, minimização), `extracao.py` (regras de extração), `auditoria.py`, `audio.py`, `visao.py`, `imagem.py`, `minuta.py` e a CLI `main.py`.

---

## ⚙️ Instalação

Requisitos: Python 3.12+ (CI em 3.12; desenvolvido em 3.14.7 no Windows 11) e Git.

```bash
git clone https://github.com/diegocbaleite/desafio-06-central-atendimento-ia.git
cd desafio-06-central-atendimento-ia
python -m venv .venv
# Windows: .venv\Scripts\activate    |   Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.main verificar
```

Na primeira indexação o `fastembed` baixa o modelo aberto `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (~220 MB, dimensão 384) para o cache local. O acervo **não** é enviado a terceiros para gerar embeddings.

### Configuração e credenciais

- Parâmetros não sensíveis: [`config/config.yaml`](config/config.yaml) (provedor, modelo, perfis de geração, chunking, top-k, limiares, limites de guardrail, retenção).
- Credenciais: copie `.env.example` para `.env` (ignorado pelo Git) e preencha apenas o que for usar. O perfil `principal` usa `OPENAI_API_KEY`. O exemplo versionado permanece sem valores. As configurações de STT, OCR e TTS reutilizadas do Desafio 01 têm provedores e credenciais próprios.
- Sem chave, use `--gerador extrativo_local` (gerador local determinístico, **não é LLM**).

| Perfil (`geracao.perfis`) | Tipo | Uso |
|---|---|---|
| `principal` | LLM (OpenAI, `gpt-6-luna`, `reasoning_effort: none`) | Fluxo alvo; requer `OPENAI_API_KEY` |
| `extrativo_local` | Extrativo, não-LLM | Segunda configuração compatível; seleciona frases literais dos trechos. Qualidade **não** é equivalente à de um LLM |
| `simulado` | Mock | Somente testes automatizados |

---

## 📚 Indexação do acervo

```bash
python -m src.main indexar                 # indexa A e B; reexecutar não duplica
python -m src.main indexar --chunking A    # só uma configuração
python -m src.main indexar --recriar       # obrigatório após trocar o modelo de embedding
python -m src.main status-indice           # estado: ok | vazio | desatualizado | reindexacao_exigida
```

Acervo fictício em [`dados/acervo/`](dados/acervo/) com [catálogo](dados/acervo/catalogo.yaml) (ID, título, versão, tema, formato, vigência, prioridade, substituições): 3 TXT + 3 PDF textuais (gerados por `scripts/gerar_acervo_pdf.py`) em dois temas principais, mais o DOC-07, **adversarial**, para o ataque de injeção no acervo. Cada trecho guarda documento, versão, SHA-256 do documento e do trecho, página (PDF), seção e `chunk_id`. O índice fica em `indice/` (fora do Git) e é recriado com os comandos acima.

## 🖥️ Interface Streamlit

```bash
streamlit run src/app.py
```

Abas: **Acervo** (status do índice, indexar/recriar, incluir TXT/PDF, excluir documento), **Solicitação** (texto, arquivo, transcrição de áudio ou OCR reaproveitados do Desafio 01, novo áudio/imagem quando houver credencial), **Consulta** (top-k, trechos com similaridade e distância explicadas), **Revisão** (aprovar/rejeitar/revisar com operador e justificativa), **Sentimentos** (painel com filtros, totais, percentuais e denominadores) e **Auditoria**. O sistema avisa sobre índice vazio, desatualizado ou com reindexação exigida, falhas e ausência de evidência.

## ⌨️ CLI

| Comando | O que faz |
|---|---|
| `python -m src.main verificar` | Versões, ferramentas e presença (não o valor) das chaves |
| `python -m src.main consultar "pergunta" [--gerador extrativo_local] [--top-k 4]` | Consulta RAG com fontes, status e trechos |
| `python -m src.main solicitacao arquivo.txt [--modalidade texto\|audio\|imagem]` | Fluxo integrado até a minuta **pendente** |
| `python -m src.main sentimentos [--gerador principal]` | Classifica as 12 avaliações e agrega contra o gabarito |
| `python -m src.main excluir-documento --doc DOC-06` | Remove vetores e derivados (RF24); `indexar --doc DOC-06` reinclui |
| `python -m src.main avaliar [--publicar-evidencias]` | Executa T01–T15 em pasta isolada e grava evidências |
| `python -m src.main --mock --decisoes dados/revisao/decisoes_demo.yaml` | Fluxo do Desafio 01 (preservado) |

## 🧪 Testes e avaliação

```bash
python -m unittest discover -s testes -t .   # 210 testes
python -m src.main verificar
python -m src.main avaliar --publicar-evidencias
python scripts/gerar_relatorio_resultados.py   # regenera documentacao/desafio6/resultados_avaliacao.md
```

Os testes do Desafio 6 usam um embedding determinístico de teste (sem download) e pastas temporárias; um deles executa a interface Streamlit sem navegador (`streamlit.testing`). A avaliação integrada usa o **embedding real local**.

Fechamento em **30/10/2026**: os 210 testes passaram no projeto e em uma cópia limpa, sem `.env`, banco de revisão ou índice prévio. A cópia recriou os índices A/B e concluiu a avaliação local com 14 aprovados e T11 parcial. A reprodução reutilizou as dependências instaladas e o cache do modelo de embeddings. Ver [conferência da entrega](documentacao/desafio6/fechamento_entrega_2026-10-30.md).

Em 29/10/2026, as quatro falhas do parecer de prontidão foram corrigidas, com 12 regressões adicionais. A resposta RAG agora aceita somente frases completas literais, descarta fontes que perdem prioridade e aplica orçamento também às consultas independentes; uploads têm ID e destino validados. Ver [registro dos ajustes](documentacao/desafio6/registro_ajustes.md) e [finalização passo a passo](documentacao/desafio6/finalizacao_passo_a_passo.md). O RAG com LLM real foi avaliado na rodada separada abaixo; Diego também registrou um pedido de revisão e uma aprovação pela interface, documentados nas [evidências humanas](documentacao/desafio6/evidencias_humanas/README.md).

A OpenAI foi configurada em 29/10/2026, com quatro testes adicionais. Um [teste real de conexão](documentacao/desafio6/evidencias_openai/teste_conexao_2026-10-29.json), usando apenas uma mensagem técnica fictícia, confirmou autenticação, modelo e JSON restrito (55 tokens de entrada, 13 de saída). Esse teste não comprova a avaliação do RAG com o acervo. Os resultados medidos abaixo continuam sendo da execução extrativa identificada.

**Rodada real OpenAI após reajuste em 29/10/2026 (`20261029T222148Z_5018e2`):** 5/5 respondíveis completas com fontes esperadas, 12/12 fatos essenciais, 2/2 abstenções sem resposta no acervo e conflito encaminhado corretamente. T08–T10 aprovados. O verificador aceita sequências contíguas de frases completas de um mesmo trecho; o prompt 1.2 preserva listas e exige cópia literal. [Comparação antes/depois e evidências](documentacao/desafio6/reajuste_rag_openai_2026-10-29.md). A [primeira rodada real com falhas](documentacao/desafio6/avaliacao_rag_openai_2026-10-29.md) foi preservada. A suíte passou com 200 testes; os números abaixo continuam sendo da avaliação extrativa anterior.

### Resultados medidos (execução `20261027T194525Z_43f775`)

**Validação complementar com LLM real em 29/10/2026:** seis extrações e resumos, 12 sentimentos e três ataques avaliados com OpenAI/GPT-6 Luna. A rodada inicial foi preservada; S02/S06 foram retestadas após corrigir o prompt. A consolidação por caso tem 18/18 campos críticos, 20/20 entidades, seis resumos com 17/17 fatos essenciais e sentimentos 12/12. ATQ02 mantém critério de quarentena no top-k parcial, embora tenha encaminhamento seguro. Total: 29 chamadas, 16.917 tokens de entrada, 3.846 de saída, custo indisponível. **210 testes passaram**. [Relatório com limites e evidências](documentacao/desafio6/validacao_complementar_llm_2026-10-29.md). A tabela seguinte continua sendo histórica e local.

| Item | Resultado | Natureza |
|---|---|---|
| Matriz T01–T15 | 14 aprovados, 1 parcial (T11: falta a demonstração humana pela interface) | local + simulações identificadas |
| RF15 categoria / entidades / fatos | 6/6 · 20/20 (0 extras) · 17/17 | regras locais (não-LLM) |
| RF18 acerto de recuperação | A 5/5 · B 5/5 → escolhida A pelo critério prévio de desempate | embedding real local |
| RF19 respondíveis com fonte correta / abstenção / conflito | 5/5 · 2/2 · P08 = `conflito_de_fontes` + revisão | gerador extrativo (não-LLM) |
| RF22 sentimentos | 12/12; 3/3 incertos sinalizados | regras locais (não-LLM) |
| RF16 ataques | ATQ01 revisar · ATQ02 revisar · ATQ03 bloquear com 0 chamadas; canário ausente de saídas e logs | local |

Detalhes: [resultados da avaliação](documentacao/desafio6/resultados_avaliacao.md) · [matriz T01–T15](documentacao/desafio6/evidencias/matriz_T01_T15.md) · [evidências](documentacao/desafio6/evidencias/) · [registro de ajustes pós-execução](documentacao/desafio6/registro_ajustes.md).

> **Leitura honesta das métricas:** as regras locais de extração, conflito e sentimento foram escritas conhecendo o conjunto de teste, e o gerador extrativo copia frases literais, de modo que “100% sustentado” é esperado por construção. Os números mostram que o fluxo e as verificações funcionam; **não** medem generalização nem a qualidade de um LLM.

## 🗑️ Exclusão e retenção (RF24)

- `excluir-documento --doc X` remove os vetores do documento em **todas** as coleções, apaga respostas RAG salvas que o citam, retira o arquivo enviado pela interface e registra o evento na auditoria. O documento fica marcado como excluído e não volta numa reindexação comum.
- Minutas já criadas são preservadas (são registro de decisão humana) e aparecem no relatório de exclusão para reavaliação.
- Retenção recomendada para o protótipo: resultados derivados por 90 dias e logs por 180 dias (`privacidade` em `config.yaml`; `privacidade.aplicar_retencao`). Ver [privacidade e retenção](documentacao/desafio6/privacidade_retencao.md).

## ⚠️ Limitações e pendências

1. **Cobertura limitada ao conjunto conhecido.** RAG, extração, resumo, sentimentos e ataques foram executados com o perfil real. Houve reajuste do prompt após observar S02/S06, com reteste desses dois casos; isso não mede generalização. ATQ02 mantém a limitação de recuperação do trecho malicioso no top-4. A interface continua com extração/resumo locais por padrão; os testes dos métodos LLM estão separados dos prints locais e das simulações.
2. **Evidências humanas concluídas:** Diego registrou `revisar` em UI-001 ([evidência](documentacao/desafio6/evidencias_humanas/revisao_UI001_20261029T232021Z.json)) e aprovou UI-002 após conferência ([evidência](documentacao/desafio6/evidencias_humanas/aprovacao_UI002_20261029T235412Z.json)). Ambas as decisões têm origem `humana_interface`, justificativa e persistência confirmada. Os 15 PNGs do conjunto principal e cinco JSONs estão presentes e conferidos, incluindo os históricos de aprovação e revisão. A captura adicional 02e é opcional, pois a passagem já aparece em 03b e sua citação na minuta em 02d. Ver [catálogo](documentacao/desafio6/evidencias_humanas/README.md) e [verificação de fechamento](documentacao/desafio6/verificacao_fechamento_2026-10-29.md). A matriz automática histórica e as decisões `simulada_teste` permanecem identificadas à parte.
3. A comparação de chunking pouco discrimina: as seções do acervo são curtas (até ~80 palavras) e os trechos não cruzam seções.
4. A recuperação falhou em um sub-pedido da S04 (“como acompanhar a solicitação”): a seção com a resposta não entrou no top-4 e o sistema se absteve. É uma falha real, registrada e não corrigida para o caso.
5. Não houve nova transcrição de áudio nem novo OCR; S02/A01 reutilizam a transcrição preservada do Desafio 01 (o enunciado permite). Tesseract, eSpeak e FFmpeg não estão instalados nesta máquina.
6. Tokens e custo ficam “indisponível” para execuções locais. Nas rodadas OpenAI, tokens e latência foram medidos; o serviço não informou custo monetário, que não foi estimado.

Mais detalhes: [relatório técnico](documentacao/desafio6/relatorio_tecnico.md) · [matriz RF14–RF24](documentacao/desafio6/matriz_requisitos_d6.md) · [registro do uso de IA](documentacao/desafio6/uso_da_ia.md) · [roteiro de apresentação](documentacao/desafio6/roteiro_apresentacao_15min.md) · [entrega em ZIP](documentacao/desafio6/entrega_zip.md).

## 📁 Estrutura

```
config/config.yaml            # perfis de geração, recuperação, guardrails, retenção
dados/
  acervo/                     # 7 documentos fictícios (TXT/PDF) + catalogo.yaml + fontes_pdf/
  solicitacoes/               # S01–S06 (reaproveita T01, A01, fixtures do Desafio 01)
  avaliacoes/                 # 12 avaliações fictícias
  ataques/                    # ATQ01–ATQ03
  gabaritos/desafio6/         # gabaritos e parâmetros prévios (commit anterior aos avaliadores)
  originais/, gabaritos/      # Desafio 01 (preservados)
prompts/d6/                   # prompts versionados (extração, resumo, RAG, sentimento)
src/                          # código (ver tabela de módulos)
testes/                       # unittest (Desafio 01 + test_d6_*)
scripts/                      # PDFs do acervo, relatório de resultados, ZIP de entrega
documentacao/desafio6/        # relatório, evidências, matriz, uso de IA, roteiro, ajustes
documentacao/desafio1/        # README histórico do Desafio 01
indice/, resultados/          # gerados localmente (fora do Git)
```
