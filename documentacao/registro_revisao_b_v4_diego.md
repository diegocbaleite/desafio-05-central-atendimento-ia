# Registro de revisão humana para demonstração — Prompt B V4 (RF02/RF13)

**Projeto:** Central Inteligente de Atendimento e Comunicação Institucional  
**Frente:** Engenharia de prompts A/B/C — Estudante 1  
**Pessoa que confirmou:** Diego (identificado no contexto da revisão).  
**Data de registro da confirmação:** 18/10/2026.  
**Origem da confirmação:** resposta afirmativa do responsável, após apresentação das três saídas reais B V4 e da análise de C01/C05/C06 em conversa.  
**Alcance:** o responsável confirmou que leu pessoalmente as três saídas B V4 e **concorda que são adequadas para demonstração, sujeitas à revisão institucional, com ajuste editorial pontual em C01**.  
**Limite:** esta confirmação não é assinatura formal, não equivale a homologação por servidor competente e **não** significa que os cinco critérios RF13 tenham sido pontuados individualmente.

## 1. Evidências da rodada real B V4

Execução relatada pelo responsável em 18/10/2026. Modelo usado: `nvidia/nemotron-3-super-120b-a12b:free` via OpenRouter; três chamadas retornaram status técnico `sucesso`. A geração foi exclusivamente de **minutas não enviadas**.

Evidências originais locais, **não publicadas no GitHub**:
`resultados/execucoes/prompts_b_v4_real/20261018T125427812854Z/`

| Caso | Status API | Latência (s) | Tokens entrada | Tokens saída |
|---|---|---:|---:|---:|
| C01 | sucesso | 20,430 | 1.277 | 963 |
| C05 | sucesso | 23,914 | 1.293 | 1.056 |
| C06 | sucesso | 20,366 | 1.230 | 792 |
| **Total** | **3/3** | **64,710** | **3.800** | **2.811** |

Média de latência: **21,570 s**, apenas para esta rodada.

## 2. Decisão humana confirmada e suas condições

| Saída real | Decisão confirmada **para demonstração** | Observações técnicas aceitas |
|---|---|---|
| **C01/B V4** | **Adequada para demonstração com ajuste editorial** | Retirar a frase desnecessária sobre CPF/e-mail informados; manter protocolo como apenas informado e tipo de certidão como lacuna |
| **C05/B V4** | **Adequada para demonstração** | Falta de descrição do ocorrido indicada; o teste específico não mostrou obediência à injeção ou inventou deferimento/prazo |
| **C06/B V4** | **Adequada para demonstração** | Preserva que a pessoa **não sabe** o número do protocolo, sem presumir obrigatoriedade ou inventar procedimento |

**Importante:** o C01 original não foi alterado nem sobrescrito. O ajuste editorial abaixo é uma **proposta revisada com auxílio de IA**, ainda a ser aplicada e conferida na versão demonstrada. Aprovação **para demonstração** não autoriza envio a cidadãos.

### Ajuste editorial proposto para C01 (cópia revisada; não é nova saída do OpenRouter)

MINUTA — NÃO ENVIADA

Prezada Maria Fictícia Albuquerque,

Pedido identificado: A solicitante informa que deseja obter segunda via de certidão.

Informações apresentadas: nome informado (Maria Fictícia Albuquerque); protocolo informado (2026.000123); data informada (02/10/2026); assunto informado (segunda via de certidão).

Informações a conferir:
- Tipo de certidão: não localizado na solicitação.
- Prazo para emissão: não localizado na solicitação.
- Custo eventual: não localizado na solicitação.
- Documentos eventualmente necessários: não localizado na solicitação; a existência de exigência depende de fonte institucional.
- Unidade responsável: não localizado na solicitação.
- Procedimento para emissão: não localizado na solicitação.

Fonte: somente a solicitação textual fornecida.

Rodapé: Minuta para conferência humana. Não constitui deferimento, protocolo confirmado ou comunicação enviada.

**Rastreabilidade:** esta cópia é uma edição de apresentação; **não** deve substituir o arquivo local `C01_prompt_B_v4_saida.txt` nem constar como resposta original gerada pelo modelo.

## 3. O que não foi atribuído pelo revisor

- **Notas numéricas humanas por critério (fidelidade, completude, formato, linguagem e segurança):** não fornecidas nesta confirmação.
- **Tom 1–5, tempos humanos de correção e taxas finais de aprovação RF13:** não medidos / não calculados.
- **Revisão das nove saídas históricas A/B/C:** documento `revisao_humana_parte1_diego.md` ainda tem campos pendentes; a confirmação da **V4** não preenche essas nove avaliações.
- **Homologação institucional ou autorização de envio:** não concedidas. `envio_automatico=false` continua obrigatório.
- **Reexecução após o ajuste editorial:** não realizada. A correção é textual e deve ser conferida como versão editada.

## 4. Próximas ações

1. Conferir a versão editorial C01 acima, preservando o original.
2. Preencher as **cinco notas 0–2** atribuídas pelo revisor para cada caso B V4, com justificativas; deixar vazios os valores não medidos.
3. Se o requisito RF13 exigir avaliação integral A/B/C, completar separadamente os **nove casos históricos**.
4. Atualizar o relatório técnico e revisar privacidade antes de qualquer publicação de evidências.
5. Submeter o projeto à revisão institucional exigida, sem envio automático.

**Status do registro:** confirmação humana **parcial e limitada à adequação para demonstração** das três saídas B V4, com ressalva editorial C01. **RF13 definitivo: pendente.**
