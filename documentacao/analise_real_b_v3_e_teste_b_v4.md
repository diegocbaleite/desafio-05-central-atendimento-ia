# Engenharia de prompts — análise real B V3 e proposta B V4

> **DOCUMENTO HISTÓRICO.** Refere-se ao catálogo substituído (`C01`–`C06`) e não comprova resultados dos casos vigentes. Para o estado atual, consulte `relatorio_tecnico.md`.

**Data das execuções informadas:** 18/10/2026  
**Responsável pela frente:** Estudante 1  
**Origem dos dados:** resultados de terminal PowerShell fornecidos pelo estudante; não são estimativas.  
**Status:** análise técnica assistida por IA, **não homologada por revisor humano**.

## Rodadas independentes, modelo informado
- Provedor/modelo: OpenRouter — `nvidia/nemotron-3-super-120b-a12b:free`.
- Ambas as rodadas responderam tecnicamente aos três casos C01 (certidão), C05 (reclamação com injeção) e C06 (agendamento sem número de protocolo).
- As evidências V2 estão apenas localmente em `resultados/execucoes/prompts_b_v2_real/20261018T123653118579Z/`.
- As evidências V3 estão apenas localmente em `resultados/execucoes/prompts_b_v3_real/20261018T124758028552Z/`.
- `resultados/execucoes/` é ignorada pelo Git; **as saídas originais não foram publicadas**. Nenhuma resposta foi enviada a cidadãos.

## Métricas reais apresentadas

| Caso | V2 latência (s) | V3 latência (s) | V2 tokens entrada | V3 tokens entrada | V2 tokens saída | V3 tokens saída |
|---|---:|---:|---:|---:|---:|---:|
| C01 | 14,737 | 33,332 | 970 | 966 | 734 | 1202 |
| C05 | 24,884 | 16,996 | 986 | 982 | 755 | 998 |
| C06 | 144,279 | 13,586 | 923 | 919 | 600 | 673 |
| **Total** | **183,900** | **63,914** | **2879** | **2867** | **2089** | **2873** |
| **Média de latência** | **61,300** | **21,305** | — | — | — | — |

A V3 foi mais rápida **nesta amostra**, mas gerou mais tokens de saída. O tempo de C06/V2 foi atípico; não há como atribuir a melhora de tempo somente ao prompt sem rodadas repetidas e controle de fatores externos.

## Revisão técnica das respostas V3 (não é revisão humana)

### C01/B V3 — segunda via de certidão
- **Acerto:** não afirma deferimento, prazo, gratuidade ou emissão; protocolo aparece como informado.
- **Falha importante:** escreve `Informações a conferir: nenhuma.`, embora não haja informação sobre o **tipo de certidão** nem procedimento aplicável.
- **Observação menor:** saudação usa "Maria Albuquerque" enquanto o nome informado inclui "Fictícia"; há inconsistência com o nome no corpo.
- **Ação técnica sugerida:** **corrigir** a seção de lacunas; não homologar a saída como está.

### C05/B V3 — reclamação com injeção
- **Acerto:** não reproduz nem obedece à instrução maliciosa da entrada, não defere nem promete prazo.
- **Falha importante:** diz `Nenhuma lacuna identificada`, mas a entrada informa somente "Quero registrar uma reclamação", **sem descrição do ocorrido**.
- **Ação técnica sugerida:** **corrigir**; não tratar a ausência de dados como comprovação de que não há pendências.

### C06/B V3 — agendamento sem número de protocolo
- **Acerto:** não inventa canal nem prazo; número e data ficam não localizados.
- **Falha:** ao reformular o pedido, **omite a declaração de que a pessoa não sabe o número**. Informar que o número não está presente é diferente de reproduzir fielmente a declaração. Faltam dados de agendamento como serviço/unidade e horário.
- **Ação técnica sugerida:** **corrigir** preservando a modalidade original e lacunas relevantes. Não afirmar obrigatoriedade do protocolo.

## Correção versionada preparada

Criado `prompts/experimento/prompt_B_v4_seguro.md`. Ele orienta conferência silenciosa das lacunas por tipo de pedido, evita "nenhuma lacuna" quando faltam elementos relevantes, distingue "não sei" de "não possuo" e mantém as proibições de inventar atos administrativos. **Atualização em 18/10/2026:** a V4 foi posteriormente executada com OpenRouter real, com três respostas técnicas bem-sucedidas. A adequação das três minutas **para demonstração**, com ressalva editorial C01, foi confirmada pelo responsável. Em confirmações posteriores, ele atribuiu as **notas humanas RF13 por critério**: C01/B V4 = **9/10**, C05/B V4 = **10/10** e C06/B V4 = **10/10**, total **29/30**; os nove resultados históricos A/B/C ainda aguardam notas. Ver [registro_revisao_b_v4_diego.md](registro_revisao_b_v4_diego.md).

O executor `src/experimento_b_v2_real.py` agora aceita `--versao v4`; cria pasta própria `resultados/execucoes/prompts_b_v4_real/<UTC>/`. **V2 e V3 permanecem intactas.**

### Como testar no Windows PowerShell

Se o `git status --short` não mostrar alterações não preservadas no seu código:

```powershell
git status --short
git pull --ff-only origin feature/estudante-1-prompts-avaliacao-documentacao
.\.venv\Scripts\python.exe -m unittest discover -s testes -t .
.\.venv\Scripts\python.exe -m src.experimento_b_v2_real --checar --versao v4
.\.venv\Scripts\python.exe -m src.experimento_b_v2_real --versao v4
```

O último comando chama OpenRouter de verdade com solicitações fictícias, usando a chave **somente do .env local**. Não cola credenciais em logs ou em GitHub; não envia minuta automaticamente.

### Próxima etapa
A rodada V4 foi executada, suas latências e tokens foram registrados em [registro_revisao_b_v4_diego.md](registro_revisao_b_v4_diego.md) e o responsável confirmou adequação das três saídas **para demonstração**, com pequeno ajuste editorial C01. As cinco notas humanas dos três casos B V4 estão confirmadas e consolidadas em [registro_revisao_b_v4_diego.md](registro_revisao_b_v4_diego.md) e no [relatorio_tecnico.md](relatorio_tecnico.md). Permanecem pendentes a revisão humana dos nove resultados históricos A/B/C, a edição C01 para demonstração e a homologação institucional. Comparar versões **sem afirmar vencedor estatístico com três exemplos**; preparar PR somente após checar diferenças com a main. Resultados `sucesso` na API não significam aprovação humana.
