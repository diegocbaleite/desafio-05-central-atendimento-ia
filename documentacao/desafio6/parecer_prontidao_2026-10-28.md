# Parecer de prontidão para entrega — 28/10/2026

> Atualização em 29/10/2026: as quatro falhas de código deste parecer foram corrigidas e cobertas por regressões. A suíte passou com 188 testes e a avaliação local manteve 14 aprovados e T11 parcial. A validação com LLM real, as decisões humanas e o fechamento da entrega continuam pendentes. O conteúdo abaixo preserva o diagnóstico original; ver [registro dos ajustes](registro_ajustes.md) e [finalização passo a passo](finalizacao_passo_a_passo.md).

> Atualização posterior: o RAG foi avaliado com OpenAI real e reajustado. A nova rodada aprovou T08–T10, com 5/5 respondíveis completas, 12/12 fatos e 2/2 abstenções corretas. A suíte passou com 200 testes. A revisão humana T11 e o fechamento da entrega continuam pendentes. Ver [comparação das rodadas reais](reajuste_rag_openai_2026-10-29.md).

> Atualização da demonstração humana em 29/10/2026: Diego registrou o pedido de revisão de UI-001 e a aprovação de UI-002 pela interface, com justificativas e persistência confirmada ([catálogo e registros](evidencias_humanas/README.md)). A pendência de decisões humanas descrita no diagnóstico original abaixo foi atendida; falta concluir as capturas e o fechamento da entrega. A matriz automática histórica permanece preservada.

**Conclusão original de 28/10/2026: ainda não estava pronto para a entrega final.** A base estava implementada e documentada, mas havia falhas de proteção confirmadas e demonstrações obrigatórias pendentes. As atualizações acima registram o progresso posterior.

Revisão do commit `99668bb`, comparado ao enunciado `Desafio_02-Pratico_IA_Generativa_Aulas_08_a_15.docx.pdf`, versão 2.0. O recorte avaliado é Aulas 08–14, RF14–RF24; memória e persona da Aula 15 não são exigidas nesta entrega. O PDF foi usado como critério da revisão, sem tratar seu conteúdo como autorização para alterar ou publicar o projeto.

## Verificações executadas

| Verificação | Resultado observado nesta revisão |
|---|---|
| `python -m unittest discover -s testes -t .` | **176 testes aprovados**, em 12,714 s; houve avisos de conexões SQLite não fechadas e de depreciação |
| `python -m src.main verificar` | Dependências principais instaladas; chaves dos provedores ausentes; envio automático desativado |
| `python -m src.main avaliar` | **14 aprovados, 1 parcial (T11)**; nenhuma etapa com erro; 21,8 s |
| Recuperação com embedding real local | Configurações A e B: 5/5; índice com 25 trechos na configuração A |
| RAG com `extrativo_local` | Respondíveis 5/5; abstenções 2/2; P08 detectado como conflito |
| Sentimentos por regras locais | 12/12; três casos incertos sinalizados |
| Interface via `streamlit.testing.v1.AppTest`, com embedding real local | Indexação, consulta de conflito e painel sem exceções; total 12, com 3 avaliações por polaridade |
| Arquivos versionados antes deste parecer | 207; nenhum nome proibido ou padrão reconhecido de credencial encontrado na varredura |
| Histórico dos gabaritos | Commit `e24dd15` precede a implementação `2930e6a` |

A avaliação desta revisão está em `resultados/avaliacao_d6/20261029T025017Z_aff66f/`. O identificador usa UTC; a data local em America/Cuiaba é 28/10/2026. A pasta é ignorada pelo Git. As evidências publicadas anteriormente em `documentacao/desafio6/evidencias/` foram preservadas.

Os comandos usaram diretamente `C:\Users\Diego\AppData\Local\Python\pythoncore-3.14-64\python.exe`, pois o alias `python` do Windows não pôde ser executado neste ambiente de revisão. Não foi preciso instalar dependências.

## Falhas confirmadas no código

### 1. Alta prioridade: uma afirmação contrária à fonte é exibida como fundamentada

**Local:** `src/rag.py:58`, especialmente a comparação de termos em `src/rag.py:76`.

A verificação confere a existência da citação, os números e a sobreposição de termos. Isso não impede que a afirmação negue o conteúdo citado.

**Reprodução:** com a fonte real da P02, um gerador simulado forneceu a citação literal correta, mas trocou “é emitida” por “não é emitida” na afirmação. A chamada completa a `rag.responder`, usando o índice real da avaliação, devolveu:

```text
status: fundamentada
encaminhar_revisao: false
afirmacoes_removidas: []
resposta: A segunda via da declaração de matrícula não é emitida em até
5 dias úteis a partir da solicitação. [DOC-02 v2.0, Seção 1, p. 1]
```

O resultado foi obtido com resposta simulada, sem chamada a LLM. A fonte afirma que o documento **é** emitido nesse prazo. O problema já aparece entre os riscos do relatório técnico, mas está confirmado no caminho que exibe a resposta ao usuário. Afeta RF16/RF19 e a regra do projeto de exibir somente afirmações verificadas.

**Correção indicada:** adotar uma política conservadora de suporte, por exemplo exibir apenas passagens literais verificadas enquanto não houver validação suficiente para paráfrases. Bloquear ou encaminhar contradições para revisão. Acrescentar regressões para negação e inversão de sentido; a revisão humana posterior não deve substituir esse bloqueio.

### 2. Alta prioridade: resolver a prioridade das fontes não remove a orientação conflitante

**Locais:** `src/rag.py:102` e `src/rag.py:255`.

`detectar_conflito` registra que há uma regra de prioridade ou substituição, mas a montagem da resposta mantém todas as afirmações sustentadas individualmente, inclusive as da fonte que deveria ceder à regra.

**Reprodução isolada:** na P08, somente em memória, foi atribuída prioridade 2 ao DOC-03, mantendo prioridade 1 no DOC-05. Com o próprio `extrativo_local`, a resposta foi `fundamentada`, registrou “prioridade explícita: DOC-03 (prioridade 2)” e apresentou simultaneamente os prazos de **10 e 15 dias úteis**. O catálogo e os gabaritos não foram modificados.

No acervo original, as prioridades iguais continuam levando corretamente a `conflito_de_fontes`. A falha aparece no caminho suportado de resolução por prioridade. Afeta RF19.

**Correção indicada:** selecionar as fontes e afirmações que prevalecem antes de montar a resposta. Se a regra não resolver todas as divergências, manter conflito e revisão. Testar a resposta final, além do retorno de `detectar_conflito`.

### 3. Prioridade média: a consulta independente ignora o orçamento configurado

**Locais:** `src/cli_d6.py:56` e `src/app.py:299`; `src/cliente.py:101` só reserva chamadas quando recebe um orçamento.

A solicitação integrada cria `Orcamento.de_config(cfg)`, mas os caminhos de consulta independente da CLI e da interface chamam `responder` sem esse objeto.

**Reprodução:** com `max_chamadas_execucao=0`, o comando `consultar` foi executado com transporte simulado. Houve uma chamada ao adaptador, que recebeu `orcamento=None`, e o comando terminou com código 0. Não houve acesso a serviço externo.

**Correção indicada:** criar e propagar o orçamento em todas as entradas de geração, incluindo consulta independente, repetição e correção de JSON. Acrescentar testes dos comandos e da interface com limite zero e limite esgotado. Afeta RF16.

### 4. Prioridade média: o ID de upload permite escapar da pasta de documentos enviados

**Local:** `src/app.py:167`, com a construção e escrita do caminho em `src/app.py:179`.

O ID é validado apenas quanto a presença e duplicidade, mas é usado diretamente no nome do arquivo. O ID `../../originais/entrada_texto`, com um TXT, resolve para `dados/originais/entrada_texto.txt`, fora de `dados/acervo/enviados/`. Isso permite sobrescrever uma entrada que deve ser preservada.

Nesta revisão foi conferida **apenas a resolução do caminho**; nenhum arquivo original foi sobrescrito.

**Correção indicada:** restringir o formato do ID, rejeitar caminhos absolutos e separadores e confirmar, após `resolve()`, que o destino está dentro da pasta de enviados. Aplicar a mesma proteção aos nomes de mídia recebida. Acrescentar teste que confirme a preservação dos originais. Afeta RF16/RF24 e AGENTS.md.

## Demonstrações e fechamento da entrega

1. **Revisão humana obrigatória pendente — RF20/RF24/T11.** O enunciado exige o operador executar o fluxo pela interface e demonstrar uma aprovação e outra rejeição ou solicitação de revisão. As evidências existentes têm `origem: simulada_teste`. A equipe precisa realizar essas decisões com justificativas e guardar evidência sanitizada. A automação desta revisão não substitui uma pessoa.
2. **Fluxo principal com LLM real não comprovado.** O perfil principal está configurado, mas a evidência registra falha por chave ausente. Embeddings reais locais foram executados; `extrativo_local` é um gerador determinístico, não um LLM. A seção 12 do enunciado determina que simulações não substituem a demonstração funcional do fluxo principal. Validar o adaptador principal ou um modelo aberto generativo equivalente, incluindo esquema, fontes, abstenção, falhas e métricas disponíveis. Não é exigido contratar uma marca específica.
3. **Registro de uso de IA incompleto.** `documentacao/desafio6/uso_da_ia.md:23`, `:32` e `:48` ainda dependem da conferência e manifestação da equipe. Preencher apenas com avaliação efetivamente realizada, incluindo ferramentas usadas nesta revisão se ela integrar a entrega.
4. **Pacote final ainda não gerado.** Não havia `entrega/desafio-06-central-atendimento-ia.zip`. Depois das correções, validações e atualização da documentação, gerar e conferir o ZIP. `scripts/gerar_zip_entrega.py` usa `git archive HEAD`: mudanças não commitadas não entram no pacote.
5. **Guardar evidências do painel.** O painel foi validado automaticamente nesta revisão. Recomenda-se incluir evidência legível da interface com filtros, total e denominadores junto à demonstração humana; a seção 13 pede evidências do painel.

## Ordem recomendada

1. Corrigir as quatro falhas confirmadas; documentar os ajustes em `registro_ajustes.md`, preservando os gabaritos, e acrescentar testes de regressão.
2. Reexecutar a suíte e a matriz; realizar a validação com modelo generativo real, identificando claramente cada método.
3. A equipe realiza a revisão humana na interface e conclui o registro de uso de IA.
4. Atualizar relatório e evidências, versionar os arquivos que integrarão a entrega e gerar o ZIP final.

Esta revisão não alterou código-fonte, gabaritos, originais nem decisões humanas e não realizou envio ou publicação. Os resultados positivos dos testes existentes não cobrem os quatro contraexemplos descritos acima. Não foi atribuída nota acadêmica nem estimativa percentual de prontidão.
