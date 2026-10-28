# Diretrizes para agentes e colaboradores

Projeto de estudo FIC_DEV — Diego, Ayron e Guilherme.

Regras inegociáveis:
- Nada de envio automático, email, WhatsApp, assinatura, deferimento ou protocolo real.
- Usar os documentos fornecidos em `dados/originais/` como acervo, exceto o brasão; minimizar dados pessoais e nunca gravar chaves no git ou em logs.
- Ausência de valor = `não localizado`; nunca criar lei, prazo, autoridade ou número.
- Não modificar entradas de `dados/originais/` durante o processamento nem adaptar gabaritos depois do teste.
- Respostas do LLM são minutas pendentes de revisão humana; decisões de YAML são simulações.
- Não apresentar saída `mock` como execução de um modelo real.
- Registre alterações em documentação e acrescente testes quando corrigir erros.

Comandos: `python -m unittest discover -s testes -t .`; `python -m src.main verificar`;
`python -m src.main --mock --decisoes dados/revisao/decisoes_demo.yaml`.

Preferir mudanças pequenas e auditáveis, sem novas dependências desnecessárias.
