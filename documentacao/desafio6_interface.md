# Interface, sentimentos, painel e revisão — Desafio 6

**Atualização:** o acervo usa os arquivos fornecidos em `dados/originais/`, exceto brasão e configuração. As avaliações são fornecidas pelo operador; o conjunto sintético inicial foi removido. As descrições e métricas antigas abaixo são históricas.

## Execução local

```powershell
python -m streamlit run src/desafio6/app.py
```

A interface usa o mesmo `FluxoDesafio6` da CLI e o adaptador OpenAI. Não possui envio de mensagens, assinatura, deferimento ou protocolo real. O catálogo é descoberto em `dados/originais/`; uploads e derivados ficam em `resultados/desafio6/`, ignorados pelo Git.

As abas oferecem seleção/upload e indexação de TXT/PDF textual até 2 MB; solicitação textual ou texto extraído de áudio/imagem; pergunta independente; ficha, resumo, trechos, fontes e minuta; revisão; avaliações e painel. A inclusão de upload e mídia exige confirmação de que os dados são fictícios. A interface informa falhas e índice desatualizado. O fluxo exige conferência de nomes, datas e protocolos antes de usar mídia na minuta. Refazer extração ou editar o texto invalida a confirmação visível. A origem e o hash da mídia acompanham o texto mesmo ao alternar o seletor para Texto, impedindo contornar a conferência. Iniciar uma solicitação textual independente limpa expressamente o conteúdo e seu vínculo anterior.

Cada ação inicia uma execução com orçamento limitado. A extração chama `fluxo.extrair_midia`, sujeita ao orçamento e no máximo uma repetição transitória do adaptador do Desafio 6; não chama diretamente os serviços antigos com outra política de tentativas. A consulta reusa o índice persistido. O texto bruto da mídia e os metadados da extração são preservados separadamente de edições. Sem serviço disponível, a UI informa falha e mantém a pendência, sem fabricar transcrição ou fontes. Os testes locais dos contratos não comprovam uma operação humana pela interface nem execução real de todas as modalidades.

## Revisão humana e retenção

`RepositorioRevisoes` persiste estados `pendente`, `aprovada`, `rejeitada` e `revisar`, versão, hash SHA-256, responsável, justificativa, data UTC e histórico. Aprovação exige revisão da versão exata exibida. Alterar a minuta cria nova versão pendente e invalida aprovação anterior; uma repetição sem mudança preserva a decisão. Alteração manual do conteúdo armazenado causa falha de integridade. Identificadores não podem determinar caminhos fora da pasta gerenciada.

Nenhum nome, assinatura ou decisão é preenchido pela IA. Decisões de teste são exercícios do mecanismo em pastas temporárias e não comprovam participação humana. Saídas simuladas não podem receber decisão humana real; uma decisão explicitamente simulada mantém o estado pendente e não conta como aprovação. A auditoria geral registra somente ID, estado e hash da decisão; responsável e justificativa ficam no registro local de revisão, sem reproduzi-los no log.

Excluir um documento retira vetores e derivados vinculados pelo controlador. Uploads são removidos apenas da pasta gerenciada; documentos originais do exercício são preservados. `limpar_expirados(dias=30)` remove registros locais antigos de revisão, com log de IDs/data/motivo sem reproduzir seu conteúdo; a aplicação deve aplicar a mesma política aos demais derivados pelo fluxo. A retenção é uma política acadêmica, não fundamento legal. A equipe deve higienizar e excluir os artefatos após a avaliação.

## Sentimentos e métricas

`classificar_avaliacoes` usa esquema fechado com polaridade `positiva`, `negativa`, `neutra` ou `indeterminada`, justificativa curta e `necessita_revisao`. Mistura, ironia e contexto insuficiente exigem indeterminação/revisão; isso é uma regra do prompt que deve ser conferida com os gabaritos. O gerador não lê rótulos esperados. Entradas adversariais ou com possível credencial são encaminhadas à revisão sem chamada ao modelo. Validação local rejeita formato inválido e justificativas com dados indevidos.

Não se estima confiança numérica. Polaridade descreve a mensagem, sem inferir personalidade, diagnóstico, atributos sensíveis ou sentimento da população. A interface recebe avaliações fornecidas pelo operador; não há conjunto pré-preenchido. Gabaritos para uma nova avaliação precisam ser preparados antes das chamadas.

`metricas.py` agrega por código, deduplica pelo ID (último registro prevalece) e aplica filtros depois da deduplicação. Percentuais exibem numerador e denominador; conjunto vazio tem percentual `null`, exibido como indisponível, sem divisão por zero. Comparação de rótulos inclui ausências no denominador. As métricas RAG só contam `todas_afirmacoes_sustentadas: true` quando a verificação do fluxo explicitamente forneceu essa evidência; a mera existência de fonte citada não basta.

## Verificação automatizada

`python -m unittest testes.test_desafio6_interface` verifica persistência de decisão/reinício, invalidação por mudança de versão/hash, decisão simulada, integridade, exclusão, retenção, caminhos e credenciais, métricas com filtro/duplicata/vazio, classificação estruturada e uploads. Um teste com `streamlit.testing.v1.AppTest` inicia as quatro abas, indexa o corpus, consulta e classifica as doze avaliações usando cliente simulado; confere ausência de exceções e persistência. Todas as respostas de modelo nesses testes são simuladas. Demonstrar uma aprovação e outra rejeição/revisão reais continua sendo ação da equipe humana; não preencher essas evidências por conta própria.
