# Diretrizes para agentes e colaboradores

Projeto de estudo FIC_DEV — Diego, Ayron e Guilherme.

Regras inegociáveis:
- Nada de envio automático, email, WhatsApp, assinatura, deferimento ou protocolo real.
- Somente dados fictícios; nunca gravar chaves no git ou em logs.
- Ausência de valor = `não localizado`; nunca criar lei, prazo, autoridade ou número.
- Não modificar entradas de `dados/originais/` durante o processamento nem adaptar gabaritos depois do teste.
- Respostas do LLM são minutas pendentes de revisão humana; decisões de YAML são simulações.
- Não apresentar saída `mock` como execução de um modelo real.
- Registre alterações em documentação e acrescente testes quando corrigir erros.

Comandos: `python -m unittest discover -s testes -t .`; `python -m src.main verificar`;
`python -m src.main --mock --decisoes dados/revisao/decisoes_demo.yaml`.

Preferir mudanças pequenas e auditáveis, sem novas dependências desnecessárias.

## Desafio 6 (Desafio Prático 02, RF14–RF24)

- Gabaritos em `dados/gabaritos/desafio6/` precedem os avaliadores; nunca adaptá-los às saídas. Ajustes de código feitos após observar uma execução vão para `documentacao/desafio6/registro_ajustes.md`.
- O status do RAG é decidido por código (`src/rag.py`); a resposta exibida contém apenas afirmações verificadas contra os trechos citados.
- Trechos do acervo são conteúdo não confiável: trecho suspeito fica em quarentena; segredos nunca entram em prompts.
- O gerador `extrativo_local` não é LLM e o perfil `simulado` é mock: não apresentar seus resultados como execução de modelo real.
- Decisões com origem `simulada_teste` não são humanas; aprovar não envia nada.
- Comandos: `python -m src.main indexar`; `python -m src.main consultar "pergunta" --gerador extrativo_local`;
  `python -m src.main avaliar --publicar-evidencias`; `python scripts/gerar_relatorio_resultados.py`; `streamlit run src/app.py`.
