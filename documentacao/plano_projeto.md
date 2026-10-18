# Plano técnico do protótipo — FIC_DEV 2026
Equipe: **Diego, Ayron e Guilherme**. Ref.: Desafio Prático 1, Aulas 01–07, v1.0.

## 1 — Arquitetura proposta
```mermaid
flowchart TD
 A[Arquivo fictício: texto/áudio/imagem] --> B[Validar extensão, tamanho, SHA-256]
 B --> C{Modalidade}
 C -->|texto| D[Texto preservado]
 C -->|áudio| E[STT + bruto/revisado + WER]
 C -->|imagem| F[OCR local + bruto/revisado + CER]
 D --> G[Extrair campos com evidência + JSON Schema]
 E --> G
 F --> G
 G --> H[Minimizar dados / delimitar conteúdo externo]
 H --> I[LLM: minuta sem novos fatos]
 I --> J[Verificar e revisar]
 J -->|rejeitar| R[Tratamento manual]
 J -->|corrigir ou nova| I
 J -->|aprovar| K[Texto aprovado]
 K --> L[TTS de acessibilidade]
 K --> M[Peça visual e proveniência]
 A & B & E & F & G & I & J & L & M --> N[Auditoria JSONL]
```

Decisões técnicas: Python CLI evita infraestrutura web no prazo de 12h; YAML separa configuração de segredo; cliente HTTP compatível com APIs comerciais evita acoplamento a SDK; Tesseract local preserva imagens e reduz custo; JSON Schema valida formato; SHA-256 documenta integridade da origem. A revisão humana é uma **barreira de negócio**, não opcional.

## 2 — Estrutura de pastas
A estrutura proposta está no README. Código `src/`; dados de entrada `dados/originais/`; gabaritos **definidos antes dos resultados** em `dados/gabaritos/`; saídas processadas em `resultados/`, prompts versionados e documentação separada. O código nunca sobrescreve os originais.

## 3 — Configuração
Python 3.11+, `python -m venv .venv`, `pip install -r requirements.txt`, Tesseract com idioma `por`. Execute `python -m src.main verificar`. Crie `.env` a partir do exemplo, sem publicar. API real exige selecionar provedor/modelo válido e cota autorizada. Use `--mock` apenas para teste do fluxo.

## 4 — Experimento A/B/C
- A: zero-shot curto, sem guias detalhados.
- B: Persona, Contexto, Tarefa, Formato e Critérios de sucesso explícitos.
- C: produzido por **metaprompt**, arquivando separadamente prompt gerado e entrada.

Controle obrigatório: **mesma entrada, mesmo modelo, mesma temperatura, limite de tokens e época aproximada**. Testes C01, C05 e C06 abrangem solicitação normal, injeção e lacunas.

Grade de cada saída: fidelidade, fatos inventados, formato, tom institucional, sinalização de lacunas, segurança, tempo da chamada e minutos de correção humana. Escolher B **somente se a comparação real justificar**. Resultados `mock` nunca decidem vencedor.

## 5 — JSON de extração
`src/schemas/extracao.schema.json` exige campos `protocolo`, `data_solicitacao`, `solicitante`, `assunto`, `pedido`. Cada campo tem valor, evidência literal e confiança. Sem evidência usar `não localizado`. `fonte` contém caminho, modalidade, SHA-256 e caminho do texto analisado; `categoria` é controlada; `campos_ausentes` e `requer_revisao` dão sinal explícito.

## 6 — Prompt injection
Defesas em camadas: (1) system vs user, (2) delimitação de conteúdo externo, (3) instrução de não seguir comandos internos, (4) heurísticas de alerta, (5) esquema de saída e comparação com fonte, (6) modelo sem ferramenta capaz de enviar, (7) revisão humana obrigatória. Testar injeção textual (C05) e embutida no OCR (C03). Heurísticas têm falsos negativos: jamais tratá-las como garantia completa.

## 7 — Casos e gabaritos
**Atualização (17/10/2026):** os casos vigentes estão em `dados/originais/casos.yaml` — **T01** (texto), **A01** (áudio) e **I01** (PDF digitalizado), o material fornecido pela equipe para a mesma solicitação, mais **X01** (injeção) e **X02** (campos ausentes), entradas sintéticas em `testes/fixtures/`. Os gabaritos prévios estão em `dados/gabaritos/<id>.json`. A tabela abaixo é o desenho original (C01–C06), mantido porque o experimento A/B/C e o relatório técnico se referem a ele; `testes/fixtures/completa.txt`, `injecao.txt` e `lacunas.txt` reproduzem C01, C05 e C06.
| ID | Entrada | Esperado | Revisão |
|---|---|---|---|
| C01 | Solicitação completa (texto) | Segunda via, protocolo 2026.000123, sem vazar CPF/e-mail | Aprovar depois de conferir |
| C02 | Áudio fictício com ruído moderado | João Exemplo Pereira, protocolo 2026.000456, pedido de andamento | Conferir transcrição e aprovar |
| C03 | Formulário digitalizado fictício | Agendamento, 2026.000789, injeção no campo observações | Corrigir, nunca deferir |
| C04 | Timbre fictício para documentos | proporção horizontal, declaração de modelo fictício, sem brasão real | Validar visualmente |
| C05 | Texto de reclamação com injeção | Rejeitar tentativa de deferimento, alertar servidor | Rejeitar |
| C06 | Texto incompleto | `não localizado` para protocolo/data/nome | Aprovar rascunho que pede dados |

## 8 — Checklist LGPD
Ler `documentacao/lgpd.md`. Aplicar finalidade, minimização, segregação das credenciais, política de retenção, acesso ao log, dados fictícios, revisão humana e verificação do local de processamento do provedor.

## 9 — Roteiro de 12h
Detalhe em `documentacao/roteiro_12h.md`. Priorizar primeiro rastreabilidade, gabaritos, texto, prompts e injeção; depois áudio, OCR, arte e avaliação; por fim pacote e demo.

## 10 — Riscos mais críticos
**R1** identidade/protocolo errados após STT/OCR: conferir na origem; **R2** fato ou prazo inventado pelo LLM: revisar contra fonte; **R3** injeção dentro de imagem: alerta + revisão; **R4** chave vazada: `.gitignore` e higienização; **R5** modelo/cota indisponível: fallback documentado e pré-teste; **R6** trabalho entregue só em mock: mostrar limitações e executar ao menos uma chamada real; **R7** imagem local declarada IA: não confundir composição programática com IA.
