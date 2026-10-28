# Desafio 6 — relatório técnico da primeira evolução

**Atualização posterior:** por solicitação da equipe, o acervo sintético descrito neste relatório foi removido e substituído pelos arquivos de `dados/originais/`, exceto o brasão. O usuário esclareceu que os dados fornecidos nessa pasta são fictícios e usados na avaliação do desafio. As medições abaixo pertencem exclusivamente à execução histórica anterior e não são resultados dos editais atuais. A avaliação do novo acervo requer perguntas e gabaritos prévios próprios. Consulte [dados e contratos](desafio6_dados.md) e o README para o fluxo atual.

**Data:** 28/10/2026. **Equipe:** Diego Assunção Leite, Ayron Brhenno Silva Figueiredo e Guilherme da Silva Lessa. SECITECI / Escola Técnica Estadual de Cuiabá, FIC_DEV — Programador de Sistemas com IA.

Corresponde ao **Desafio Prático 02, versão 2.0 — 2026**, continuação do Prático 01 no mesmo repositório. O PDF `desafio-06/Desafio_02-Pratico_IA_Generativa_Aulas_08_a_15.docx.pdf` foi lido integralmente (13 páginas). O escopo é Aulas 08–14, RF14–RF24; não foi implementada memória conversacional. A especificação textual e o PDF concordam no escopo; os vínculos RF inconsistentes na matriz do PDF estão registrados na [matriz local](desafio6_matriz.md).

## Arquitetura e reaproveitamento

`python -m src.main desafio6` encaminha à CLI nova sem substituir os comandos anteriores. A interface é `src/desafio6/app.py`, executada por Streamlit local. `fluxo.py` coordena ficha/NLP, busca e minuta; usa o marcador de apresentação, minimização, validação de arquivos e renderização de PDF do projeto anterior. Nenhuma chamada dispara envio ao cidadão, assinatura, deferimento ou protocolo real.

`contratos.py` e o JSON Schema versão 2.0 proíbem propriedades adicionais e verificam tipos, calendário, campos ausentes e suporte na entrada. Ausências persistem como `null` e são exibidas como `não localizado`. O resumo é extrativo, até 100 palavras, preservando frases completas/negações; inferências ficam vazias. Dados STT/OCR não alcançam minuta sem conferência explícita do operador.

`servicos.py` isola geração e embeddings OpenAI. Geração usa `gpt-6-luna`, esquema restrito, `store: false`, temperatura 0,2 e teto 2400 tokens de saída; embeddings usam `text-embedding-3-small`, 256 dimensões. `config/config.yaml` contém as opções e uma segunda configuração de geração, `gpt-6.1-terra`. Trocar apenas geração preserva o índice; a demonstração automatizada da troca usa adaptador simulado identificado, sem alegar qualidade equivalente.

`indice.py` guarda vetores/metadados em SQLite e calcula cosseno exato em Python. É um equivalente persistente adequado ao acervo pequeno; não é índice ANN para grande escala. Metadados incluem documento, versão, hash, arquivo, seção/página e chunk. A configuração e o modo real/simulado integram o fingerprint. Indexação é transacional, idempotente e envia os chunks novos em lote. Mudança de embedding, dimensão ou chunking requer recriação explícita; alteração da fonte bloqueia a consulta até reindexar.

`rag.py` separa fatos da solicitação do contexto institucional delimitado. O modelo seleciona passagens; o código confere chunk, hash, literalidade, frase completa na seção original e correspondência temática mínima. Perguntas quantitativas exigem o dado temporal/monetário correspondente. A resposta final é extrativa: nenhuma paráfrase institucional livre é liberada. Ainda é necessária revisão de relevância e completude. Conflitos sem prioridade/vigência suficientes retornam `conflito de fontes`.

`revisao.py` mantém pendente/aprovada/rejeitada/revisar com versão, hash, responsável, justificativa e data. Alteração invalida aprovação. A saída simulada não recebe aprovação real. `sentimentos.py` classifica a mensagem, sem inferir personalidade, diagnóstico ou atributos sensíveis. `metricas.py` faz contagens, deduplicação, filtros e proporções com denominadores visíveis.

## Dados e validação observada

O conjunto anterior `dados/desafio6` foi escrito antes das chamadas: seis documentos fictícios (quatro TXT e dois PDFs textuais), seis solicitações, oito perguntas, 12 avaliações e três ataques. Os gabaritos eram separados e o gerador não os consultava. R03/R04 são recortes identificados das referências antigas STT/OCR, não novo reconhecimento nem substituição do bruto I01 rejeitado. Os documentos fornecidos em `dados/originais/` não foram incorporados àquela rodada histórica; integram o acervo atual.

Situação inicial: **130 testes aprovados**. Situação integrada: **218 testes aprovados**, incluindo AppTest do Streamlit, orçamento/retries, persistência, citações, exclusão, revisão, regressão e pacote. Os testes de HTTP são simulados; sua aprovação não comprova API real. O ambiente observado usa Windows e Python **3.14.6**, pypdf 6.16.2 e Streamlit 1.62.0. As dependências novas já estavam instaladas. O alias `python` do sandbox estava indisponível; usou-se o interpretador instalado em `C:/Users/ayron/AppData/Local/Python/pythoncore-3.14-64/python.exe`.

**Rodada histórica real:** `avaliacao_3ac210a30801`, preservada localmente em `resultados/desafio6/real/avaliacoes/avaliacao_3ac210a30801/resultado.json`. Uma cópia local com caminhos minimizados existe em `docs/evidencias/desafio6/real/`; não integra o pacote atualizado. O manifesto anterior às chamadas confirmou referências preservadas.

| Medida automática | Numerador/denominador | Resultado |
|---|---|---|
| Categorias das solicitações | 6/6 | 100% |
| Recuperação de ao menos uma referência no top-3 | 5/5 | 100% |
| Respostas respondíveis liberadas com todas as passagens verificadas | 4/5 | 80% |
| Abstenção nas perguntas sem resposta | 2/2 | 100% |
| Conflito de fontes | 1/1 cenário | Identificado; revisão pendente |
| Polaridades das avaliações | 11/12 | 91,67% |
| Ataques barrados/encaminhados pelos guardrails locais | 3/3 | Sem geração nem revelação de segredo |
| Recuperação: 90 palavras, overlap 20 | 5/5 | 100% |
| Recuperação: 45 palavras, overlap 10 | 5/5 | 100% |

Não houve vencedor no chunking: a medição empatou. Mantém-se a configuração inicial 90/20 como padrão provisório por contexto mais longo, sem alegar superioridade medida; as passagens comparadas ficam na evidência. O top-k foi 3 e o mesmo embedding foi utilizado em ambos os índices.

A rodada principal registrou **45 requisições**, **15.564 tokens de entrada** e **2.108 de saída** disponibilizados nos metadados; soma das latências das requisições: **69,240 s** (não é o tempo total de trabalho nem o tempo humano até resultado utilizável). A indexação inicial real foi executada separadamente, em um lote, com seis documentos e 13 chunks. Custo monetário não foi retornado e não foi estimado: `não localizado`.

Também foi executado o fluxo integrado histórico real R01: análise, resumo, recuperação e minuta fundamentada, ID `cacf89f54d8746f7`. Sua evidência minimizada local contém ficha, fontes, saídas estruturadas e estado pendente. Nenhuma revisão foi atribuída à equipe automaticamente.

## Falhas preservadas e correções

- Na primeira avaliação simulada, Q04 foi encaminhada indevidamente por falta dos termos `consultar/andamento` na regra de escopo; a regra geral foi corrigida com teste. A rodada falha foi preservada, assim como as referências.
- A revisão técnica identificou que recortar palavras de uma frase poderia apagar uma negação. Foram adicionadas validações de unidades completas no resumo e nas citações, incluindo limites de chunk e seção original.
- **R04 real:** o modelo extraiu `14/10/2026` como entidade, mas retornou `data: null` para `DATA MATRÍCULA`, divergindo do gabarito. A lacuna exige revisão e foi mantida; 6/6 categorias não significa 6 fichas totalmente corretas.
- **Q03 real:** D03 foi recuperado em primeiro lugar (cosseno 0,69945508), porém uma passagem selecionada falhou na correspondência lexical. A política bloqueia a resposta inteira quando qualquer afirmação falha. Como aquela rodada não preservou o JSON bruto selecionado antes dessa barreira, não é possível distinguir explicação complementar válida de passagem irrelevante. Mantém-se **4/5**, sem ajustar gabarito nem relaxar a barreira após o resultado.
- **S11 real:** a frase irônica recebeu `negativa` e `necessita_revisao: false`, divergindo do esperado `indeterminada` com revisão. Sua correção de conteúdo depende de conferência; o painel não deve interpretar isso como sentimento da população.
- Para futuras execuções, o adaptador passou a preservar as saídas estruturadas em artefatos locais separados dos logs, após filtro de dados indevidos; credenciais detectadas bloqueiam a saída. A rodada original permanece intacta.

## Recursos, privacidade e limites

Cada cenário/ação tem teto de **12 requisições**, incluindo repetição transitória e correção semântica, timeout configurado de 30 s (máximo 60) e no máximo **uma repetição transitória**. Texto/embeddings reservam até 60.000 tokens de forma conservadora por bytes mais margem e limite de saída; a reserva não é medição nem preço. Uma comparação de chunking usa 12 chamadas sem falha; se houver retry e faltar orçamento, ela interrompe e registra o resultado parcial. A avaliação em lote compreende cenários independentes com seus IDs, não uma chamada ilimitada.

Uploads: TXT/PDF textual, até 2 MiB; PDFs têm limites de páginas/stream descomprimido. Mídia reutiliza validadores e renderização anteriores, passando pelo adaptador D6 com limite de chamadas e no máximo uma repetição. OCR reduz a imagem a 1024px e reserva uma quota explicitamente distinguida do uso medido. STT aplica limite de chamadas/bytes; tokens de áudio de entrada não são conhecidos antes da transcrição e esse teto não equivale a garantia monetária. A nova política de mídia foi testada com HTTP simulado; não foram refeitos áudio, imagem ou TTS pagos sem necessidade.

Logs guardam IDs, consulta minimizada, hashes, versões, resultado, falha técnica, métricas e vínculo à revisão; não contêm credenciais nem corpos de erro do provedor. Textos/objetos ficam em artefatos locais do exercício. Ausência de custo ou tokens permanece indisponível. O nome e a justificativa de revisão são preservados no registro próprio, não copiados ao log técnico.

Retenção operacional: **30 dias** para índice/derivados, uploads e revisões; executar explicitamente `python -m src.main desafio6 limpar-expirados --dias 30`. A auditoria técnica permanece para a entrega acadêmica e deve ser removida pela equipe no encerramento do estudo. Não há agendamento automático. `excluir --documento-id` remove vetores e derivados vinculados, limpa revisões dependentes e registra tombstone para não reintroduzir o documento. Fontes canônicas do exercício são preservadas; uploads gerenciados podem ser removidos pela interface. Cópias exportadas/versionadas de evidências têm descarte separado pela equipe.

O `.gitignore` protege `secrets.toml` do Streamlit, ambientes virtuais, caches, cobertura, temporários e bancos SQLite em pastas personalizadas. Todas as saídas sob `resultados/` e cópias derivadas sob `docs/evidencias/` são ignoradas, inclusive experimentos, relatórios JSON, mídias e peças visuais. A exceção é `resultados/multimodal/referencias/`: são referências humanas prévias utilizadas como entradas dos testes. `.env.example`, `.streamlit/config.toml`, o acervo fictício, gabaritos e prompts continuam disponíveis para versionamento. As regras foram verificadas com `git check-ignore`. Evidências históricas já rastreadas continuam no Git; nenhum arquivo foi removido do índice ou do disco.

## Pendências humanas

A interface está disponível para uma pessoa registrar **ao menos uma aprovação e uma rejeição/revisão reais**, com responsável e justificativa. Isso não foi fabricado pelo agente. Também permanecem conferência visual de layout, avaliação semântica dos resumos/citações, correção ou rejeição de R04/Q03/S11 e revisão da escolha final do chunking. A suíte e a rodada de API não equivalem a validação humana completa de RF14–RF24.

Referências técnicas consultadas: [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=chat), [embeddings](https://developers.openai.com/api/reference/resources/embeddings/methods/create), [AppTest Streamlit](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest) e [extração de PDF pypdf](https://pypdf.readthedocs.io/en/stable/user/extract-text.html). Não foi adicionado serviço externo além da API OpenAI autorizada.
