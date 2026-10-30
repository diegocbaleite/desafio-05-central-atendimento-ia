# Resolução dos conflitos do PR #4 — 30/10/2026

Integração da main `a156eaa` na entrega `d5bffc7`, preservando as duas implementações do Desafio 6. A entrega usa `src/app.py` e comandos diretos; a implementação da main usa `src/desafio6/app.py` e o subcomando `desafio6`. Configurações independentes foram mantidas.

- Cliente compartilhado mantém orçamento, uma repetição transitória e JSON Schema da entrega, juntamente com listagem de modelos, `store=false` e remoção de credenciais dos erros da main. Aceita as duas convenções de chamada de `_payload`.
- Configuração principal preserva temperatura omitida e uma repetição. Testes importados da main foram alinhados a esse contrato; os testes de orçamento e saída estruturada existentes permanecem.
- Dependências combinadas, com pypdf >=6,<7. PDF da main preservado em `documentacao/desafio6/` após a reorganização de diretórios.
- README da entrega preservado, links do repositório corrigidos e README anterior da main arquivado em `documentacao/desafio1/README_main_pre_merge.md`.
- Dois testes Streamlit passam a executar o rerun após preencher a pergunta, antes de clicar no botão que depende desse campo. Nenhuma proteção da interface foi removida.

Validação local: Python 3.12.14, `python -m unittest discover -s testes -t .`: 322 testes, OK. `python -m compileall -q src testes`, `python -m src.main verificar`, `python -m src.main --help` e `python -m src.main desafio6 --help` concluídos. Sem credenciais configuradas; nenhuma validação com API real realizada. eSpeak ausente neste ambiente.
