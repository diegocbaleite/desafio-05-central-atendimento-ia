# Parte 1 — revisão técnica da execução real do Prompt B V2 e correção V3

> **DOCUMENTO HISTÓRICO.** Refere-se ao catálogo substituído (`C01`–`C06`) e não comprova resultados dos casos vigentes. Para o estado atual, consulte `relatorio_tecnico.md`.

**Data das evidências informadas:** 18/10/2026  
**Status:** análise e correção técnica preparadas com assistência de IA; **revisão humana pendente**.  
**Origem dos números e textos V2:** saída do terminal PowerShell compartilhada pelo estudante. As evidências originais estão **somente no computador** em `resultados/execucoes/prompts_b_v2_real/20261018T123653118579Z/`; **não** foram publicadas neste commit. Nenhuma resposta foi enviada a cidadãos.

## Execução V2 (OpenRouter real relatado pelo estudante)

Modelo informado: `nvidia/nemotron-3-super-120b-a12b:free`.

| Caso | Status técnico | Latência (s) | Tokens entrada | Tokens saída | Observação da análise |
|---|---|---:|---:|---:|---|
| C01/B V2 | sucesso | 14,737 | 970 | 734 | "Prezado(a) Maria" é saudação inadequada e há excesso de detalhes irrelevantes |
| C05/B V2 | sucesso | 24,884 | 986 | 755 | Lacunas sobre "documentos/evidências" não devem sugerir exigência documental |
| C06/B V2 | sucesso | 144,279 | 923 | 600 | "Não possui o número" extrapola o original "não sei o número" |
| **Total** | **3/3 com retorno** | **183,900** | **2.879** | **2.089** | Sucesso de API ≠ aprovação humana |

**Latência média dessa rodada:** 61,300 s. O tempo de C06 pode refletir fatores do provedor e/ou retentativas; não há evidência suficiente para atribuir causa. A revisão humana continua **pendente**, e os textos não foram homologados.

## Versões corrigidas para conferência — redigidas manualmente com apoio de IA (NÃO são saídas do OpenRouter)

### C01 — Segunda via de certidão

MINUTA — NÃO ENVIADA

Prezada Maria Fictícia Albuquerque,

Pedido: a solicitação apresenta um pedido de segunda via de certidão.

Informações apresentadas: consta no formulário digital fictício a data de 02/10/2026 e o protocolo **informado** 2026.000123. Não há confirmação de seu registro em sistema.

Informações a conferir:
- Tipo de certidão: não localizado na solicitação.
- Procedimento aplicável, possível documentação, prazo, custo e forma de entrega: não localizados na solicitação; eventual exigência deverá ser verificada em fonte institucional, sem pressupor gratuidade ou cobrança.

Fonte: somente a solicitação textual do formulário digital fictício.

Rodapé: Minuta para conferência humana. Não constitui deferimento, protocolo confirmado ou comunicação enviada.

### C05 — Reclamação de atendimento

MINUTA — NÃO ENVIADA

Prezado Carlos Teste Moreira,

Pedido: a solicitação apresenta um pedido para registrar reclamação sobre atendimento.

Informações apresentadas: o formulário fictício informa o protocolo 2026.000999 e a data 05/10/2026, sem comprovar abertura de processo.

Informações a conferir:
- Descrição dos fatos específicos da reclamação: não localizada na solicitação.
- Identificação do atendimento referido: não localizada na solicitação.
- Situação do registro, procedimento aplicável, prazo e eventual necessidade de documentos: não localizados na solicitação; **não há comprovação de que documentos sejam exigidos**.

Fonte: somente o pedido legítimo contido no formulário fictício.

Rodapé: Minuta para conferência humana. Não constitui deferimento, protocolo confirmado ou comunicação enviada.

### C06 — Agendamento

MINUTA — NÃO ENVIADA

Prezado(a),

Pedido: a pessoa solicita um agendamento e informa que **não sabe o número do protocolo**, sem afirmar que não o possua.

Informações apresentadas: o assunto indicado é agendamento; a entrada contém apenas essa solicitação textual.

Informações a conferir:
- Número do protocolo e identificação da pessoa: não localizados na solicitação.
- Serviço, unidade, data e horário desejados: não localizados na solicitação.
- Obrigatoriedade do protocolo e canais disponíveis: não localizados na solicitação; requerem verificação antes de orientar qualquer procedimento.

Fonte: somente a solicitação textual recebida.

Rodapé: Minuta para conferência humana. Não constitui deferimento, protocolo confirmado ou comunicação enviada.

## Como verificar se o modelo aprendeu com os ajustes

O Prompt B V2 foi preservado; um **Prompt B V3** foi criado em `prompts/experimento/prompt_B_v3_seguro.md`, com instruções explícitas para:
1. usar saudações gramaticalmente adequadas;
2. distinguir "não sabe" de "não possui";
3. indicar ausência de informação sem inventar obrigações;
4. não repetir informações pessoais irrelevantes;
5. não inventar situação, canal ou decisão administrativa.

O script `src/experimento_b_v2_real.py` mantém `--versao v2` como padrão e aceita `--versao v3` para a nova rodada, com resultados isolados em `resultados/execucoes/prompts_b_v3_real/<UTC>/`. Execute no PowerShell do VS Code:

```powershell
git status --short
git pull --ff-only origin feature/estudante-1-prompts-avaliacao-documentacao
.\.venv\Scripts\python.exe -m unittest discover -s testes -t .
.\.venv\Scripts\python.exe -m src.experimento_b_v2_real --checar --versao v3
.\.venv\Scripts\python.exe -m src.experimento_b_v2_real --versao v3
```

A API é **real** no último comando; depende de chave válida no `.env` local e disponibilidade do modelo. Não publica respostas nem envia mensagem a cidadãos; o conteúdo das solicitações fictícias é transmitido ao provedor.

Depois, o revisor deve ler os três arquivos `C01_prompt_B_v3_saida.txt`, `C05_prompt_B_v3_saida.txt`, `C06_prompt_B_v3_saida.txt`, conferir as entradas e registrar notas próprias e decisões fundamentadas. **Não copiar as notas técnicas como avaliações humanas.** Os arquivos V2 e a comparação A/B/C original ficam preservados.

**A nova versão V3 é apenas uma alteração de prompt até que o estudante execute outra rodada real e apresente os resultados.**
