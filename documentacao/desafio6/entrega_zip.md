# Como gerar o ZIP da entrega

```bash
git status                      # confirme que tudo está commitado
python scripts/gerar_zip_entrega.py
```

O arquivo `entrega/desafio-06-central-atendimento-ia.zip` é montado com `git archive` a partir do último commit. Por isso **não** entram:

- `.env` e qualquer credencial (somente `.env.example`, sem valores);
- ambientes virtuais (`.venv/`), `__pycache__/`;
- o índice vetorial (`indice/`), que é reproduzível com `python -m src.main indexar`;
- bancos de revisão (`*.sqlite3`), logs locais, resultados de execução e documentos enviados pela interface;
- dados reais (o repositório contém apenas dados fictícios).

O script confere o ZIP contra nomes proibidos e padrões de chave (Gemini, OpenAI, Groq e o canário dos testes) e apaga o arquivo se encontrar algum problema.

Conteúdo esperado: código (`src/`), testes, `requirements.txt`, `config/config.yaml`, `.env.example`, `.gitignore`, dados fictícios, gabaritos, esquemas, prompts versionados, `README.md` e `documentacao/desafio6/` (relatório técnico, resultados, evidências sanitizadas, matriz T01–T15, uso de IA e roteiro).

Para conferir depois de descompactar:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s testes -t .
python -m src.main indexar
python -m src.main avaliar
```
