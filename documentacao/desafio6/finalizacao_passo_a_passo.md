# Finalização da entrega, uma etapa por vez

> Retomada em 30/10/2026: testes, dependências, integridade das evidências e reprodução em cópia limpa conferidos. O fechamento do pacote está registrado em [conferência da entrega](fechamento_entrega_2026-10-30.md). As etapas abaixo preservam o roteiro e os resultados de 29/10/2026.

Atualizado em 29/10/2026. As quatro correções técnicas do parecer já estão implementadas. O RAG real, as decisões humanas, os 15 prints e a confirmação de uso de IA em nome de Diego foram registrados. A validação complementar real também foi executada; restam as limitações documentadas e o fechamento do pacote.

## 1. Correções técnicas concluídas

| Problema | Comportamento corrigido | Comprovação |
|---|---|---|
| Afirmação com sentido invertido | Somente frase completa e literal da fonte é aceita; paráfrases e recortes são removidos | Testes de negação, condição, exceção e resposta final |
| Fontes com prioridade | Afirmações das fontes que não prevalecem são descartadas; divergência ainda não resolvida exige revisão | Testes de prioridade, substituição, empate e substituição parcial |
| Limites da consulta | Toda consulta recebe um orçamento, compartilhado quando fornecido pelo fluxo | Limite zero na CLI/interface e correção de JSON consumindo o mesmo teto |
| Caminho do upload | ID e nome são validados antes da escrita; destino resolvido fica dentro da pasta permitida | Caminhos Windows/Linux recusados; original fictício preservado |

Para conferir localmente:

```powershell
python -m unittest discover -s testes -t .
python -m src.main verificar
python -m src.main avaliar
```

Resultado desta rodada: **188 testes aprovados**; avaliação `20261029T214410Z_517c20` com 14 aprovados e T11 parcial. Embeddings reais locais, gerador extrativo não-LLM. Os testes novos estão em `testes/test_d6_correcoes_prontidao.py` e `testes/test_d6_app_streamlit.py`. O registro das mudanças está em `registro_ajustes.md`, itens 5–8.

O alias `python` do Windows falhou no ambiente da revisão. Se ocorrer na sua sessão, substitua `python` por `& 'C:\Users\Diego\AppData\Local\Python\pythoncore-3.14-64\python.exe'`. Para iniciar a interface, use esse executável seguido de `-m streamlit run src/app.py`.

## 2. Validar o LLM real

O perfil `principal` usa OpenAI/GPT-6 Luna em `config/config.yaml`. A conexão e duas rodadas reais do RAG foram executadas após autorização específica. O reajuste do prompt/verificador foi concluído: a rodada `20261029T222148Z_5018e2` obteve **5/5 respondíveis completas, 12/12 fatos, 2/2 abstenções corretas e conflito encaminhado**, com T08–T10 aprovados e **200 testes** passando. Ver [comparação antes/depois](reajuste_rag_openai_2026-10-29.md). As falhas da primeira rodada foram preservadas. A [validação complementar real](validacao_complementar_llm_2026-10-29.md) também foi concluída: seis extrações/resumos, 12 sentimentos e ataques, com reteste declarado de S02/S06 e limitação do ATQ02. As instruções abaixo ficam como referência de reprodução; não é necessário repetir as chamadas para obter estas evidências. A chave fica somente no `.env`.

1. Se `.env` ainda não existir, copie o exemplo. Este comando preserva um `.env` existente:

   ```powershell
   if (-not (Test-Path -LiteralPath .env)) { Copy-Item -LiteralPath .env.example -Destination .env }
   ```

2. Abra `.env` no editor e preencha `OPENAI_API_KEY` com a credencial da conta escolhida, caso ainda não esteja preenchida. Confirme apenas a presença da chave com `python -m src.main verificar`.
3. Indexe o acervo e execute uma consulta simples:

   ```powershell
   python -m src.main indexar
   python -m src.main consultar "Em quanto tempo é emitida a segunda via da declaração de matrícula?" --gerador principal
   ```

4. Confira se não houve erro do serviço ou do esquema. Leia a resposta e abra o DOC-02 para conferir frase, versão e página. A nova política exige que o modelo selecione frases completas literais; respostas removidas ou abstenções devem ser registradas como obtidas, sem modificar o gabarito.
5. Execute a avaliação RAG e os sentimentos com o perfil real:

   ```powershell
   python -m src.main avaliar --gerador principal
   python -m src.main sentimentos --gerador principal
   ```

6. Guarde o ID da execução e os resultados medidos, incluindo erros, abstenções, tokens e latência disponíveis. `avaliar --gerador principal` troca a geração RAG; a etapa de sentimentos desse avaliador continua usando regras locais. O segundo comando acima valida os sentimentos por LLM separadamente. A extração e o resumo do fluxo padrão também continuam locais; selecionar o perfil principal não troca todos os métodos.

Se o serviço falhar, a validação real permanece pendente. Registre a falha e confira a configuração; não apresente a execução extrativa ou simulada como substituição da execução do LLM. Não use `--publicar-evidencias` antes de conferir a rodada: essa opção substitui a pasta de evidências publicada. Preserve as execuções anteriores e identifique seus métodos.

## 3. Realizar a revisão humana pela interface

Atualização: etapa concluída. Diego registrou `revisar` no caso UI-001 ([evidência](evidencias_humanas/revisao_UI001_20261029T232021Z.json)) e aprovou a minuta fundamentada de UI-002 ([evidência](evidencias_humanas/aprovacao_UI002_20261029T235412Z.json)). A persistência, a origem `humana_interface` e os hashes foram confirmados em leitura do banco, sem produzir outra decisão. Os 15 PNGs do conjunto principal e os cinco JSONs do [catálogo](evidencias_humanas/README.md) estão presentes e conferidos. Não é necessário repetir o processamento, as decisões ou as capturas. Os passos abaixo permanecem como referência de reprodução.

```powershell
streamlit run src/app.py
```

1. Em **Acervo**, indexe os documentos se necessário.
2. Informe o operador responsável na barra lateral. Selecione o perfil que foi efetivamente validado na etapa anterior.
3. Em **Solicitação**, escolha **Arquivo .txt**, selecione `dados/solicitacoes/DEMO_RF20_declaracao.txt` e processe. Esse exemplo é adicional; `completa.txt` e os gabaritos foram preservados.
4. Leia o original, a ficha, a minuta e as fontes. Em **Revisão**, selecione a minuta, escolha aprovar somente após conferir o conteúdo, escreva a justificativa real e registre a decisão.
5. Preserve o pedido de revisão de UI-001 já registrado; não é necessário repeti-lo para a evidência. A aprovação do novo caso deve corresponder à conferência efetivamente realizada pela pessoa.
6. Reabra a página e confira se os estados e o histórico persistem. Guarde capturas legíveis da minuta, fontes, decisão e justificativa, sem credenciais, em `documentacao/desafio6/evidencias_humanas/`.

Essas decisões devem ser feitas pela equipe. Uma decisão automatizada não comprova T11. Aprovar apenas registra o estado; não envia resposta ao cidadão.

## 4. Registrar o painel e concluir a documentação

O painel completo, a tabela, o filtro com três casos para revisão e a Auditoria já foram capturados e conferidos. O registro de uso de IA foi preenchido em nome de Diego, com a data de 29/10/2026 e sua autorização expressa, sem declarar confirmação pelos demais integrantes. As validações complementares reais já foram executadas; a limitação de top-k do ATQ02, os ajustes e o fechamento do pacote estão descritos na [verificação de fechamento](verificacao_fechamento_2026-10-29.md).

1. Abra **Sentimentos**, classifique as 12 avaliações e confira rótulos, justificativas, total e denominadores. Guarde evidências do painel completo e de um filtro.
2. O preenchimento em nome de Diego em `uso_da_ia.md` está concluído por sua autorização. O documento preserva a distinção entre as ações humanas demonstradas e as verificações técnicas do agente.
3. Acrescente ao relatório os resultados do LLM e a evidência humana, distinguindo-os da avaliação extrativa e dos testes simulados. Não atribua decisões de uma pessoa às execuções automáticas anteriores, cujo T11 permanece parcial.
4. Se alguma execução real revelar erro, registre-o em `registro_ajustes.md`, corrija o código e acrescente uma regressão. Preserve os gabaritos.

## 5. Preparar o ZIP final

Depois de concluir as etapas anteriores:

```powershell
python -m unittest discover -s testes -t .
git diff --check
git status --short
```

Revise as alterações e versione os arquivos que devem integrar a entrega. O script abaixo empacota **somente o último commit (`HEAD`)**; alterações não commitadas ficam de fora:

```powershell
python scripts/gerar_zip_entrega.py
```

Confira o arquivo `entrega/desafio-06-central-atendimento-ia.zip`. Descompacte em outra pasta e siga o README para verificar instalação, testes e indexação. O ZIP deve conter as evidências sanitizadas e os documentos atualizados, preservando a exclusão de `.env`, credenciais, ambientes virtuais, bancos de revisão e índices locais reproduzíveis.
