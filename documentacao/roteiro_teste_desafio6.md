# Roteiro de teste — Desafio 6

Este roteiro usa os documentos fictícios fornecidos em `dados/originais/` e a API OpenAI. Consultas, indexação, extração de mídia e classificação de avaliações podem consumir créditos. O brasão não faz parte do acervo de perguntas. As respostas são minutas para revisão humana e não são enviadas automaticamente.

## 1. Preparar o ambiente

No PowerShell, abra a pasta do projeto e execute:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Se já houver um ambiente virtual configurado, basta ativá-lo e instalar as dependências. Se ainda não existir `.env`, crie-o com `Copy-Item .env.example .env` e configure `OPENAI_API_KEY` nesse arquivo. Preserve o `.env` existente e não compartilhe a chave.

Verifique a configuração e o índice:

```powershell
python -m src.main verificar
python -m src.main desafio6 estado
```

Confira se a chave está configurada, sem exibir seu valor. Se o índice estiver vazio ou desatualizado, execute `python -m src.main desafio6 indexar`; a indexação inicial pode levar alguns minutos e usar créditos. Se estiver atualizado, aproveite o índice existente.

## 2. Abrir a interface e conferir o acervo

```powershell
python -m streamlit run src/desafio6/app.py --server.address 127.0.0.1
```

Abra <http://localhost:8501> e mantenha o terminal aberto. Na aba **Acervo**, confira os documentos selecionados e expanda **Situação do índice**. Se a interface indicar que o índice precisa ser criado ou atualizado, mantenha os documentos do acervo selecionados e clique em **Indexar seleção**. Aguarde a conclusão.

## 3. Consultar os documentos

1. Abra **Solicitação e consulta** e selecione **Texto**.
2. Para testar apenas a busca, deixe **Solicitação ou texto extraído** vazio. Em **Pergunta ao acervo institucional**, informe: `Qual é a responsabilidade do candidato em relação às informações do edital?`
3. Clique em **Consultar fontes e preparar minuta**. Confira a situação, a minuta e **Fontes e passagens citadas**. Abra também os trechos exibidos e compare a resposta com o documento e suas retificações.
4. Faça outra pergunta cuja resposta não esteja nos documentos. Verifique se a aplicação informa a ausência de evidência em vez de inventar uma resposta. Se apresentar informação sem suporte, registre a falha para revisão.

O resultado pode variar entre chamadas. Uma citação e uma pontuação de similaridade não substituem a conferência do conteúdo, das retificações e da vigência.

## 4. Registrar uma revisão

Na minuta, escolha **revisar**, **rejeitar** ou **aprovar** conforme sua avaliação. Preencha **Responsável pela decisão** e **Justificativa da decisão**, marque **Li esta versão da minuta e conferi suas fontes.** e clique em **Registrar revisão**. Depois, abra **Revisões** e confirme que a decisão aparece com o estado escolhido. Se houver dúvida ou divergência entre documentos, escolha **revisar** e descreva o motivo. Nenhuma resposta é enviada ao registrar a decisão.

## 5. Testar áudio e imagem/PDF (opcional)

Em **Solicitação e consulta**, escolha **Áudio** ou **Imagem/PDF**, envie um arquivo fictício compatível de até 2 MB e clique em **Extrair texto da mídia**. Compare o texto extraído com o arquivo, corrija erros e confira especialmente nomes, protocolos e datas. Marque **Conferi nomes, protocolos e datas no arquivo original.**, escreva uma pergunta e consulte. O áudio original fornecido no acervo é maior que o limite de upload da interface; ele pode ser processado durante a indexação do acervo.

## 6. Testar o painel de avaliações (opcional)

Em **Avaliações e painel**, cole os exemplos fictícios abaixo em **Avaliações em JSON** e clique em **Classificar avaliações fornecidas**:

```json
[
  {"id": "AV01", "texto": "O atendimento foi claro e útil."},
  {"id": "AV02", "texto": "A explicação não resolveu minha dúvida."},
  {"id": "AV03", "texto": "O atendimento ocorreu pela manhã."},
  {"id": "AV04", "texto": "A equipe foi gentil, mas a orientação não resolveu o problema."}
]
```

Confira o total, a tabela e o gráfico; teste o filtro **Polaridades** e avalie se as classificações fazem sentido. Esses textos servem apenas para testar a interface: não são gabaritos nem demonstram o cumprimento das métricas formais do desafio. A avaliação formal do acervo atual requer casos e gabaritos preparados previamente.

## 7. Encerrar e executar os testes automatizados

Para parar a interface, pressione `Ctrl+C` no terminal. Para executar a suíte automatizada, use:

```powershell
python -m unittest discover -s testes -t .
```

Os testes automatizados podem usar simulações; uma simulação não comprova uma chamada real à OpenAI. Resultados locais da aplicação ficam em `resultados/desafio6/`.
