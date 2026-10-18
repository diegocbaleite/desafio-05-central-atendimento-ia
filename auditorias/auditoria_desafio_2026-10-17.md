# Auditoria técnica — Desafio Prático 1

**Data:** 17/10/2026  
**Referências:** [prompt de auditoria](./prompt_auditoria.md) e [Desafio Prático 1](../Desafio_01-Pratico_IA_Generativa_Aulas_01_a_07.docx.pdf).  
**Escopo:** código Python e documentação Markdown; materiais de apresentação oral foram ignorados.

## 1. Resumo executivo

A auditoria inicial registrou 66 testes automatizados aprovados. Após as correções técnicas abaixo, a suíte foi reexecutada em 18/10/2026 e **74 testes passaram**. O comando original `python -m src.main` terminou com código 1 sem entrada interativa: não houve decisão humana e nenhum caso foi contado como aprovado. A integração OpenRouter de imagem foi implementada, mas a única chamada autorizada falhou com HTTP 402, sem produzir imagem. Permanecem pendentes geração concluída de imagem por IA, validação humana documentada e métricas independentes de STT/OCR. A execução original criou evidências locais em [resultados/execucoes/0e1b1706b6a7](../resultados/execucoes/0e1b1706b6a7/).

## 2. O que falta ser feito

| Prioridade | Requisito | Pendência e evidência |
|---|---|---|
| **Alta** | **RF10 — Imagem** | Integração implementada para OpenRouter / `google/gemini-3.1-flash-image` usando `POST /images`; o endpoint correto está documentado [aqui](https://openrouter.ai/google/gemini-3.1-flash-image). O modelo é pago; a única chamada autorizada retornou HTTP 402 por créditos insuficientes, sem arquivo ou custo reportado. Nova geração exige créditos e nova autorização. Composição Pillow continua identificada como não-IA. |
| **Alta** | **RF13 — Avaliação e revisão** | A execução sem terminal interativo não registrou decisões reais: nenhum caso entrou na taxa de aprovação. A revisão de campos de STT/OCR agora permite registrar correções individuais, mas a decisão humana da minuta e a matriz de avaliação continuam dependendo da equipe. A [matriz de requisitos](../documentacao/matriz_requisitos.md) ainda exige ao menos um caso aprovado e outro rejeitado ou corrigido por uma pessoa. Decisões em YAML ou `--mock` não substituem essa evidência. |
| **Alta** | **RF06/RF08 — STT e OCR** | A referência de áudio não é independente do modelo, e a referência/revisão de OCR deriva da mesma transcrição — portanto, WER/CER zerados não provam acurácia ([matriz de requisitos](../documentacao/matriz_requisitos.md)). O pipeline agora preserva texto bruto e metadados de STT/OCR na mesma execução; campos críticos continuam exigindo conferência contra os originais. É necessário criar referências independentes antes de medir. |
| **Alta** | **RF12 — Privacidade** | O fluxo principal usa Groq para STT, que recebe o áudio original. A confirmação de que todo o material é fictício e os itens de retenção ainda aparecem pendentes na [documentação LGPD](../documentacao/lgpd.md). O usuário confirmou nesta conversa que os dados usados no teste são fictícios e autorizou os envios a Groq e OpenRouter; essa confirmação ainda não está registrada no repositório. |
| **Média** | **RF02 — Comparativo A/B/C** | Há evidência de 9/9 respostas reais, mas as avaliações humanas, a justificativa final do prompt escolhido e os custos por chamada continuam pendentes ([README](../README.md), [relatório técnico](../documentacao/relatorio_tecnico.md)). Também falta manter explícita a correspondência entre os casos antigos C01/C05/C06 e os casos/fixtures atuais. |
| **Média** | **RF11 — Rastreabilidade** | Corrigido parcialmente: o pipeline salva STT/OCR brutos e metadados técnicos por caso/execução, e os parâmetros LLM ficam nos eventos. Métricas independentes e validação humana seguem pendentes ([src/main.py](../src/main.py), [src/cliente.py](../src/cliente.py)). |
| **Média** | **RF01/RF07 — Reprodutibilidade e áudio** | README e matriz registram 74 testes aprovados nesta revisão; repetir em uma máquina limpa continua pendente. `verificar` detectou Tesseract e Poppler, mas não `espeak` nem `ffprobe`; assim, não é possível regenerar TTS localmente nem medir a duração do áudio neste ambiente. |
| **Média** | **RF09 — Minuta institucional** | A compatibilidade do timbre com documentos GOV.MT permanece explicitamente não validada ([README](../README.md), [matriz de requisitos](../documentacao/matriz_requisitos.md)). Deve ser validada ou mantida claramente identificada como pendência, sem alegar conformidade oficial. |
| **Média** | **RF04/RF11 — Parâmetros da API** | Corrigido nesta revisão: metadados da minuta agora registram temperatura, `max_tokens` e timeout efetivos. A implementação está em [src/cliente.py](../src/cliente.py), com teste sem chamada externa. |

## 3. O que pode sair do escopo

- A interface web, integração com canais reais e envio de respostas a cidadãos não são exigidos; a CLI atual é suficiente e deve continuar sem envio automático.
- Os comandos `imagem` e `arte` oferecem caminhos parcialmente redundantes; pode-se priorizar `arte`, que registra revisão visual e proveniência. Não se deve adiar a própria peça visual exigida por RF10.
- Metaprompt V2 e suporte a vários provedores além do necessário para demonstrar o desafio podem ficar como extensões. O comparativo obrigatório de três prompts e ao menos uma chamada real a uma API precisam permanecer.

## 4. O que deve mudar

- **Revisão de campos críticos — implementada:** [`_conferir_campos_criticos`](../src/main.py) agora solicita cada valor conferido; Enter mantém valor extraído, texto informado corrige-o e `não localizado` exige confirmação explícita. A minuta usa a versão conferida, preservando extração original e os registros de correção. A participação e decisão humana efetivas continuam pendentes.
- **Integração multimodal — implementada no pipeline:** STT/OCR brutos, provedor/modelo, parâmetros e duração são gravados em `resultados/execucoes/<id>/<caso>/` junto à extração. Métricas independentes ainda dependem de referências prévias válidas.
- **Minimização:** [`minimizar`](../src/seguranca.py) mascara CPF, e-mail e telefone, mas não nomes, protocolos ou identificadores que possam aparecer dentro do assunto/pedido. A minimização deve cobrir os dados efetivamente enviados.
- **Auditoria de parâmetros — implementada:** metadados agora incluem temperatura, `max_tokens` e timeout efetivos; veja [src/cliente.py](../src/cliente.py).
- **Falhas de provedores — limitação documentada:** STT, TTS e imagem não repetem chamadas automaticamente; o README instrui conferir erro/limite antes de repetir manualmente, evitando repetição silenciosa.
- **Sincronizar documentação — em andamento nesta revisão:** README e matriz refletem o pipeline e o estado atual; protocolo usa os casos T01/A01/I01/X01/X02, e o [relatório técnico](../documentacao/relatorio_tecnico.md) mantém C01/C05/C06 como histórico. Decisões humanas, métricas independentes e imagem por IA não foram inventadas.

## 5. Riscos de segurança e privacidade

- A configuração do fluxo principal envia o áudio original a Groq; o LLM recebe assunto e pedido após minimização. Essa transmissão é incompatível com dados reais ou confidenciais e deve ser mantida restrita a entradas fictícias.
- Os resultados de [resultados/multimodal](../resultados/multimodal/) e [resultados/experimento_prompts](../resultados/experimento_prompts/) estão versionados, mas o [.gitignore](../.gitignore) não os exclui. Antes de publicar/entregar, é necessário revisar transcrições, OCR, áudio e saídas dos prompts; adicionar regras de ignore para esses diretórios se não forem evidências aprovadas para entrega.
- Não encontrei credenciais hardcoded no Python inspecionado; o [.env.example](../.env.example) contém valores vazios e `.env` está no `.gitignore`. Porém, o `.env.example` não lista `OPENAI_API_KEY`, embora README e geração de imagem dependam dela ([README](../README.md), [src/imagem.py](../src/imagem.py)).
- O código não envia minutas a cidadãos automaticamente. Ainda assim, `verificar` exibe “envio automático: False”; esse estado pode ser confundido com ausência de chamadas externas, embora o STT remoto padrão envie áudio ao provedor.

## 6. Lacunas de documentação

- README, [matriz de requisitos](../documentacao/matriz_requisitos.md) e [protocolo de avaliação](../documentacao/protocolo_avaliacao.md) foram sincronizados com a implementação e os casos atuais; a instalação em máquina limpa continua pendente.
- O [relatório técnico](../documentacao/relatorio_tecnico.md) agora diferencia as evidências históricas de C01/C05/C06 e acrescenta o estado das correções; avaliações antigas não foram convertidas em evidência dos casos atuais.
- O [registro do uso de IA](../documentacao/uso_da_ia.md) tem campos de modelos, validação e responsabilidade humana a preencher; a [revisão da Parte 1](../documentacao/revisao_parte1.md) mantém assinaturas e itens de homologação pendentes.
- O código e a configuração não dependem mais de OpenAI; a seção 5 foi preservada sem alterações conforme a exceção solicitada e deve ser lida como registro dos riscos observados na auditoria inicial, não como descrição da configuração atual.
- O README e a matriz registram que a chamada à imagem recebeu HTTP 402; nenhum arquivo de geração real foi criado.

## Verificações realizadas

- `python -m src.main` — terminou com código 1 por falta de entrada humana; nenhum caso foi aprovado.
- `python -m unittest discover -s testes -t .` — **74 testes passaram** em 18/10/2026.
- `python -m src.main verificar` — passou; `espeak` e `ffprobe` ausentes; as chaves OpenRouter, Groq e Gemini aparecem configuradas.
- `python -m src.main arte --provider openrouter` — única tentativa autorizada; HTTP 402, nenhum arquivo retornado; nenhuma repetição realizada.
