# Execução real do Prompt B V2 — Estudante 1

**Situação:** executor preparado na branch do Estudante 1. **Não afirmar que houve execução real antes de ver a saída do OpenRouter.**

O script `src/experimento_b_v2_real.py` executa **somente o Prompt B V2**, em uma rodada separada da comparação histórica A/B/C e da rodada do metaprompt V2.

## Ambiente Windows / PowerShell no VS Code

1. Estar na pasta do repositório e conferir alterações locais antes de atualizar.
2. Atualizar a branch, sem alterar a `main`:
   ```powershell
   git branch --show-current
   git status --short
   git pull --ff-only origin feature/estudante-1-prompts-avaliacao-documentacao
   ```
3. Ativar o ambiente virtual, se necessário:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```
   Se o PowerShell bloquear a ativação, use diretamente `.\.venv\Scripts\python.exe` no lugar de `python` nos comandos.
4. Configure **somente no computador** um token válido `OPENROUTER_API_KEY` no arquivo `.env` ignorado pelo Git. **Não publique, não cole em conversa, não imprima o valor. Troque qualquer chave já exposta.**
5. Antes da API real, confira se o token, o prompt e os casos existem:
   ```powershell
   python -m src.experimento_b_v2_real --checar
   ```
   Este comando **não faz** requisição a serviço externo.
6. Executar realmente:
   ```powershell
   python -m src.experimento_b_v2_real
   ```
   Isso chama o OpenRouter para **C01, C05 e C06** com modelo `nvidia/nemotron-3-super-120b-a12b:free` definido na configuração da branch, caso ainda disponível. Não envolve cidadãos reais nem envio automático de respostas. A entrada enviada à API contém nomes fictícios e usa minimização de CPF/e-mail/telefone; a API **recebe o texto das solicitações**.
7. Para executar apenas o primeiro caso e conferir o funcionamento:
   ```powershell
   python -m src.experimento_b_v2_real --caso C01
   ```
   Para usar um modelo alternativo disponível no OpenRouter:
   ```powershell
   python -m src.experimento_b_v2_real --modelo "ID_EXATO_DO_MODELO"
   ```
   Se trocar o identificador, documente a mudança. Comparações de qualidade e latência entre modelos diferentes exigem ressalva.

## Saídas geradas

Nova pasta única, a cada execução:

`resultados/execucoes/prompts_b_v2_real/<identificador_UTC>/`

Arquivos:
- `parametros.json`: modelo solicitado, temperatura, timeout, SHA-256 do prompt, status de revisão pendente;
- `prompt_B_v2_utilizado.md`: versão exata do prompt;
- `C01_prompt_B_v2_saida.txt` (e C05/C06, em caso de sucesso);
- `matriz_B_v2.csv`: status por caso, erro, latência, tokens reportados, hashes e coluna de decisão humana **vazia**.

A pasta `resultados/execucoes/` já está no `.gitignore`, protegendo a publicação automática de saídas. **Não execute `git add -f` sem revisar privacidade e autorização de publicação.** Um status HTTP 429/502/503 ou resposta sem texto implica falha, não sucesso. O script preserva falhas na matriz e retorna código de saída diferente de zero se uma ou mais chamadas falharem.

## Revisão RF02/RF13

1. Conferir individualmente os três TXT novos contra as entradas C01/C05/C06.
2. Atribuir por pessoa identificada e data real: fidelidade, completude, formato, linguagem e segurança (0–2 cada).
3. Justificar aprovar, corrigir ou rejeitar. Não preencher taxas ou tempos que não foram efetivamente medidos.
4. A comparação técnica B original × B V2 é apenas **indicativa** até avaliar as duas rodadas sob condições comparáveis. Preservar as saídas e a matriz históricas.

**Nenhuma decisão humana, nota, aprovação ou execução real da API foi criada por este documento.**
