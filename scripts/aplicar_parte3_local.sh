#!/usr/bin/env bash
# Execute dentro da raiz do repositório depois de extrair o ZIP (nunca faz push nem commit).
set -euo pipefail
esperada='feature/estudante-3-audio-ocr-imagem-acessibilidade'
atual="$(git branch --show-current)"
if [[ "$atual" != "$esperada" ]]; then
  echo "PARE: mude para a branch $esperada (atual: $atual)" >&2
  exit 2
fi
if [[ ! -f src/guilherme_multimodal.py || ! -f testes/test_guilherme_multimodal.py ]]; then
  echo "Extraia o ZIP na raiz do repositório antes de executar este script." >&2
  exit 2
fi
if ! grep -qFx 'resultados/guilherme/' .gitignore; then
  printf '\n# Resultados privados da Parte 3\nresultados/guilherme/\n' >> .gitignore
fi
python -m unittest discover -s testes -t .
python -m src.guilherme_multimodal verificar
printf '\nArquivos alterados APENAS localmente, nenhum push ou commit realizado.\n'
git status --short
