# Conferência da entrega — 30/10/2026

A retomada partiu da [verificação de 29/10/2026](verificacao_fechamento_2026-10-29.md). As validações reais e as decisões humanas anteriores foram preservadas. Não foram feitas novas chamadas pagas nem registradas decisões pelo agente.

## Validação local

- **210 testes aprovados**, em 6,130 s, na árvore de trabalho.
- `python -m src.main verificar`: dependências principais disponíveis, credencial indicada somente por presença e envio automático desativado.
- `python -m pip check`: nenhuma dependência incompatível identificada.
- Originais, gabaritos, evidências humanas, banco de revisão e auditoria da demonstração mantiveram os hashes durante a suíte: 35 arquivos protegidos conferidos.
- Os 15 PNGs de evidência passaram na verificação de integridade; JSONs/JSONLs de evidência válidos. A conferência visual permanece a documentada em 29/10/2026.
- A varredura dos arquivos candidatos à entrega não encontrou nomes proibidos, padrões de credenciais ou valores de segredos configurados no `.env`. Nenhum valor foi exposto no registro.

## Reprodução em cópia limpa

Os arquivos candidatos foram copiados para uma pasta temporária fora do repositório, sem `.git`, `.env`, bancos, resultados ou índices locais. As variáveis de credenciais e de configuração da demonstração foram removidas do ambiente do processo de reprodução.

| Verificação | Resultado |
|---|---|
| `pip install --dry-run --no-index -r requirements.txt` | Requisitos atendidos pelas dependências já instaladas |
| `python -m unittest discover -s testes -t .` | 210 aprovados em 9,405 s |
| `python -m src.main verificar` | Concluído; sem credenciais da demonstração |
| `python -m src.main indexar` | Sete documentos; 25 trechos em A e 26 em B |
| `python -m src.main status-indice` | `ok`, modelo multilingual MiniLM, dimensão 384 |
| `python -m src.main avaliar --gerador extrativo_local` | 14 aprovados, T11 parcial, nenhum erro de etapa |

Esta conferência reutilizou **Python 3.14.7, as dependências instaladas e o cache local do modelo de embeddings**. Não comprova uma instalação nova em ambiente virtual nem um primeiro download do modelo. O gerador da avaliação é extrativo local, não-LLM. T11 permanece parcial na matriz automática porque suas decisões são simuladas; as decisões humanas anteriores estão documentadas separadamente.

O resumo sanitizado da conferência está em [evidência de validação](evidencias_entrega/validacao_2026-10-30.json). Os logs completos ficam em `resultados/logs/retomada_2026-10-30_*`, fora do versionamento.

## Pacote e rastreabilidade

O comando `python scripts/gerar_zip_entrega.py` gera `entrega/desafio-06-central-atendimento-ia.zip` a partir do último commit local. O pacote contém código, testes, dados fictícios, gabaritos prévios, documentação e evidências sanitizadas. `.env`, ambientes virtuais, índices reproduzíveis, bancos de revisão e logs da máquina ficam fora.

O manifesto externo `entrega/manifesto_entrega_2026-10-30.json` identifica o commit, o SHA-256 do ZIP e o resultado da conferência do pacote extraído. O manifesto permanece fora do ZIP para evitar referência circular ao hash do próprio arquivo. O versionamento e a geração do pacote são locais; a conferência não publica ou envia a entrega.

Continuam válidas as limitações registradas no [relatório técnico](relatorio_tecnico.md), incluindo ATQ02 parcial no critério de quarentena no top-k e ausência de avaliação de generalização. As evidências históricas e seus erros não foram substituídos.
