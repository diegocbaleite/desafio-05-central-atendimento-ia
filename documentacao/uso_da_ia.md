# Registro transparente do uso de IA no desenvolvimento

**Equipe:** Diego, Ayron, Guilherme.

## Ferramentas e modelos
- ChatGPT (OpenAI), assistente de programação/documentação — modelo disponibilizado na conversa: **GPT-6**.
- Assistente de codificação integrado ao VS Code (Copilot SDK), usado em 17/10/2026 para auditoria, ajustes de código, testes e documentação — **versão/modelo não exposta ao assistente; preencher se a equipe souber**.
- Modelos usados no fluxo com API: **[preencher após execuções reais]**.
- Resultados `mock` não são resultados de modelo generativo real.

## Solicitações relevantes feitas à IA
1. Planejar e implementar o protótipo multimodal do Desafio Prático 1, com LGPD, 12h e revisão humana.
2. Estruturar o GitHub como o repositório `desafio-03-pipeline-recomendacao`.
3. Criar repositório atualizado e identificar equipe como Diego, Ayron e Guilherme.
4. Auditar o projeto contra o PDF do desafio (17/10/2026) e executar o sistema para testar; relatório em `auditorias/`.
5. Ler o PDF do desafio e as diretrizes do agente e ajustar o projeto (17/10/2026): revisão humana com responsável/justificativa/hash/versão, conferência de campos críticos, bloqueio de envio remoto sem autorização, gabaritos e casos para o material fornecido, matriz de requisitos.

## Sugestões e decisões
| Sugestão | Registro | Justificativa |
|---|---|---|
| CLI Python em vez de interface web | Proposta; conferir pela equipe | Escopo reproduzível em 12h |
| Cliente HTTP OpenAI-compatible | Proposta; conferir pela equipe | Menor acoplamento de provedor |
| OCR local em vez de subir imagem | Proposta; conferir pela equipe | Privacidade e custo |
| Decisão humana antes de TTS | Proposta; conferir pela equipe | Evitar disseminar minuta não aprovada |
| Imagem local sem IA como se fosse IA | **Rejeitada** | Origem do material deve ser declarada corretamente |
| `arquivos` exigir `--autorizar-api` | Aceita nesta rodada; conferir pela equipe | Evitar envio acidental de PDF/áudio a provedores externos |
| Manter só o material fornecido em `dados/` e mover injeção/lacunas para `testes/fixtures/` | Decisão da equipe (resposta registrada na conversa) | Respeita o commit que removeu os casos sintéticos e preserva cobertura de RF03/RF05 |
| Aprovação exige responsável e justificativa digitados no terminal | Aceita; conferir pela equipe | RF11/RF13 e diretriz de não preencher decisão humana por conta própria |

## Erros e inadequações a registrar
- [x] 17/10/2026: após o commit `f6d5b8b` (remoção dos casos C01–C06), 4 testes falhavam e `python -m src.main` não tinha entradas; corrigido com `casos.yaml`, gabaritos prévios e fixtures.
- [x] 17/10/2026: o extrator por regex capturava o rótulo seguinte como parte do nome (`Maria Fictícia Albuquerque\nProtocolo`), podia tomar data de nascimento como data da solicitação e não reconhecia protocolo com hífen; corrigido e coberto por testes.
- [x] 17/10/2026: o lote terminava com código 0 mesmo com falhas e `verificar` emitia aviso de depreciação; corrigidos.
- [ ] Registrar outros defeitos encontrados e correções realizadas em execução real.
- [ ] Conferir que nenhum arquivo de origem/gabarito foi alterado para coincidir artificialmente com saída.
- [ ] Preencher ambiente de validação, métricas e responsáveis.

## Validação do código e do conteúdo gerado
`python -m unittest discover -s testes -t .` e execução de `python -m src.main --mock` com decisões simuladas (sem APIs). Validação por serviço real e por pessoa: ver `documentacao/matriz_requisitos.md`.

## Responsabilidade
Os alunos devem ler, testar, adaptar, validar e assumir responsabilidade pelo resultado final. A colaboração de IA está declarada, sem atribuir a modelos ações que não realizaram.

**Assinaturas/ciência da equipe:** Diego: ___ · Ayron: ___ · Guilherme: ___.
