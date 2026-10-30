# Desafio 6 — Central Inteligente de Atendimento e Comunicação Institucional

Evolução do Desafio Prático 01 para o **Desafio Prático 02, versão 2.0 (2026), Aulas 08 a 14**. Protótipo Python/Streamlit com extração estruturada, resumo, classificação, entidades, guardrails, busca vetorial, RAG com fontes, sentimentos e revisão humana.

**Equipe:** Diego Assunção Leite · Ayron Brhenno Silva Figueiredo · Guilherme da Silva Lessa.

**Curso:** FIC_DEV — Programador de Sistemas com IA.

**Instituição:** SECITECI / Escola Técnica Estadual de Cuiabá.

**Repositório:** [desafio-05-central-atendimento-ia](https://github.com/diegocbaleite/desafio-05-central-atendimento-ia).

**Branch da entrega:** `entrega-desafio6-2026-10-30`, [PR #4](https://github.com/diegocbaleite/desafio-05-central-atendimento-ia/pull/4).

Toda minuta começa pendente. Aprovar, rejeitar e pedir revisão são decisões do operador, com justificativa persistida. Nenhuma resposta é enviada automaticamente. O acervo de avaliação descrito abaixo é fictício; similaridade e confiança não garantem verdade. Memória conversacional e persona da Aula 15 não fazem parte do escopo obrigatório.

## Qual versão executar

A entrega avaliada usa **`src/app.py`**, os comandos diretos `indexar`, `consultar`, `avaliar` e as configurações `geracao`/`recuperacao`. Seu acervo é `dados/acervo/`, com gabaritos em `dados/gabaritos/desafio6/` e evidências em `documentacao/desafio6/`.

A integração preserva também a implementação paralela da main em `src/desafio6/`, acessível por `python -m src.main desafio6 --help` e `python -m streamlit run src/desafio6/app.py`. Ela usa a seção `desafio6` do YAML, embeddings OpenAI e outro catálogo. **Os resultados medidos da entrega não avaliam esse catálogo paralelo.** Seu [README anterior](documentacao/desafio1/README_main_pre_merge.md) foi preservado como referência. Para a entrega e apresentação, siga os comandos abaixo, sem alternar os dois fluxos.

## Instalação

Pré-requisitos: Git e Python 3.12+. Testado nesta integração com Python 3.12.14 em Linux. Execute a partir da raiz do projeto.

```bash
git clone --branch entrega-desafio6-2026-10-30 https://github.com/diegocbaleite/desafio-05-central-atendimento-ia.git
cd desafio-05-central-atendimento-ia
python -m venv .venv
```

Ative o ambiente no Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Ou no Linux/macOS:

```bash
source .venv/bin/activate
```

Depois:

```bash
python -m pip install -r requirements.txt
python -m src.main verificar
```

Somente em configuração nova, copie `.env.example` para `.env` (`Copy-Item` no PowerShell ou `cp` no Linux). Se já existir, preserve-o. Preencha `OPENAI_API_KEY` para o perfil de geração principal e mantenha a chave fora do Git. Parâmetros ficam em [config/config.yaml](config/config.yaml).

A primeira indexação baixa o modelo aberto `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` pelo fastembed; precisa de rede e espaço para cache. Os embeddings são locais, com dimensão 384. A geração principal envia os trechos recuperados à API configurada e pode consumir créditos. Sem chave, o gerador `extrativo_local` permite executar o fluxo por seleção literal: **não é LLM**. O perfil `simulado` é mock e serve para testes.

Áudio/OCR podem reaproveitar as transcrições do Desafio 01, como permite o enunciado. Novos processamentos dependem do provedor ou das ferramentas opcionais: Tesseract/Poppler para OCR local, FFmpeg/faster-whisper para áudio local e eSpeak para síntese local. O fluxo textual não depende dessas ferramentas.

## Indexar e abrir a interface

```bash
python -m src.main indexar
python -m src.main status-indice
python -m streamlit run src/app.py --server.address 127.0.0.1
```

O índice Chroma fica em `indice/`, fora do versionamento. Reindexar o mesmo acervo não cria duplicatas; trocar o modelo de embedding exige `python -m src.main indexar --recriar`. Trocar apenas o perfil de geração preserva o índice.

Na interface, percorra Acervo → Solicitação → Consulta → Revisão → Sentimentos → Auditoria. Confira ficha, fatos do solicitante, trechos e fontes antes de decidir. Os estados são `pendente`, `aprovada`, `rejeitada` e `revisar`. Cada consulta é independente.

## Comandos de demonstração

```bash
# Consulta local sem chamada ao LLM; requer índice e modelo de embedding
python -m src.main consultar "Qual o prazo para a segunda via da declaração de matrícula?" --gerador extrativo_local

# Consulta com o perfil principal configurado; requer chave e pode consumir créditos
python -m src.main consultar "Qual o prazo para a segunda via da declaração de matrícula?"

# Regressão do Desafio 01, identificada como simulação
python -m src.main --mock --decisoes dados/revisao/decisoes_demo.yaml

# Testes sem credenciais e sem chamadas pagas
python -m unittest discover -s testes -t .

# Avaliação local em diretório próprio; não substitui as decisões humanas
python -m src.main avaliar --gerador extrativo_local

# Ajuda e catálogo de modelos da conta (a consulta ao catálogo requer chave)
python -m src.main --help
python -m src.main modelos --provider openai
```

`excluir-documento --doc DOC-06` demonstra remoção dos vetores e derivados; `indexar --doc DOC-06` permite reincluir explicitamente. Faça a demonstração em cópia de trabalho. Dados originais e gabaritos não devem ser adaptados às saídas.

## Cobertura e evidências

| Frente | Evidência disponível |
|---|---|
| RF14–RF15: esquema, regras de negócio e NLP | Seis solicitações e gabaritos; comparação de JSON sintático/esquema; [validação complementar com LLM](documentacao/desafio6/validacao_complementar_llm_2026-10-29.md) |
| RF16: proteção em camadas e limites | Três ataques, bloqueio de segredo antes da chamada e encaminhamento para revisão; ATQ02 mantém limitação de recuperação declarada |
| RF17–RF18: persistência e chunking | Sete documentos (seis regulares e um adversarial), três temas, TXT/PDF; comparação A/B nas mesmas cinco perguntas com embedding real local |
| RF19: RAG e citações | [Oito consultas reais](documentacao/desafio6/reajuste_rag_openai_2026-10-29.md): 5/5 respondíveis completas, 12/12 fatos essenciais, 2/2 abstenções corretas e conflito encaminhado |
| RF20/RF24: interface e revisão | [15 capturas e registros humanos](documentacao/desafio6/evidencias_humanas/README.md), com uma minuta aprovada e outra enviada para revisão |
| RF21: geração e auditoria | Adaptadores configuráveis, perfil extrativo identificado, tokens/latência quando disponíveis, logs sanitizados; custo monetário indisponível |
| RF22–RF23: sentimentos e regressão | Doze avaliações, métricas com denominadores, filtros/duplicatas/conjunto vazio, regressão textual e áudio/OCR reaproveitados |

**Integração de 30/10/2026: 322 testes aprovados.** As 210 aprovações e as avaliações anteriores permanecem registros históricos. A matriz automática histórica tem 14 aprovados e T11 parcial porque usa decisões simuladas; os registros humanos posteriores complementam RF20/RF24 sem reclassificar simulações.

As métricas de LLM acima são das evidências versionadas de 29/10/2026. Nesta integração não foram feitas novas chamadas pagas. Os números pertencem a um conjunto pequeno e conhecido, com reajustes e retestes declarados; não medem generalização. As métricas locais/extrativas permanecem separadas das chamadas reais.

## Documentação da entrega

- [Conferência atual e parecer de entrega](documentacao/desafio6/parecer_entrega_integrada_2026-10-30.md).
- [Matriz RF14–RF24](documentacao/desafio6/matriz_requisitos_d6.md) e [matriz T01–T15](documentacao/desafio6/evidencias/matriz_T01_T15.md).
- [Relatório técnico](documentacao/desafio6/relatorio_tecnico.md), [arquitetura/integração](documentacao/desafio6/integracao_main_2026-10-30.md) e [uso de IA](documentacao/desafio6/uso_da_ia.md).
- [Privacidade e retenção](documentacao/desafio6/privacidade_retencao.md), [resultados locais](documentacao/desafio6/resultados_avaliacao.md) e [ajustes/falhas preservados](documentacao/desafio6/registro_ajustes.md).
- [Roteiro da apresentação de até 15 minutos](documentacao/desafio6/roteiro_apresentacao_15min.md).
- [Histórico do Desafio 01](documentacao/desafio1/README_desafio1.md).

## Limitações que acompanham a entrega

- ATQ02 foi encaminhado com segurança, mas o trecho malicioso específico não entrou no top-4: critério literal de quarentena parcial.
- A recuperação omitiu um subpedido da S04, com abstenção registrada. A comparação de chunking discrimina pouco por usar seções curtas.
- A interface usa extração/resumo por regras por padrão. As rodadas LLM estão documentadas separadamente; a consolidação de S02/S06 inclui retestes após correção do prompt.
- Não houve nova geração de áudio/imagem nesta etapa; o enunciado permite reaproveitar STT/OCR. Custos não retornados pelo provedor permanecem indisponíveis.
- Retenção configurada: resultados por 90 dias e logs por 180 dias, com aplicação por código. O protótipo exige revisão humana e não representa homologação institucional.

## Gerar o pacote

Após versionar as alterações:

```bash
python scripts/gerar_zip_entrega.py
```

O ZIP `entrega/desafio-06-central-atendimento-ia.zip` exporta o último commit, com código, dados fictícios, gabaritos, prompts, relatórios e evidências versionadas. Exclui `.env`, ambiente virtual, índices, bancos e logs locais. O script verifica nomes proibidos e padrões de credenciais. Descompacte em outra pasta e execute os testes antes da submissão. Índices são recriados pelos comandos de instalação/indexação; não entram no pacote.
