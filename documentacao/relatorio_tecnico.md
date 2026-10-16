# Relatório técnico — modelo a preencher com execuções reais

**Equipe:** Diego, Ayron e Guilherme. **Desafio:** FIC_DEV IA Generativa, Prático 1/2026.

## Arquitetura
Python CLI -> entrada validada -> STT/OCR/texto -> extração JSON e evidências -> minimização -> minuta segura -> revisão humana -> acessibilidade e imagem -> auditoria. Leia `plano_projeto.md`.

## Modelos e parâmetros
| Etapa | Provedor / modelo usado na execução | Versão/data | Parâmetros reais |
|---|---|---|---|
| LLM | **A preencher após execução** | — | config.yaml |
| STT | **A preencher** | — | idioma pt |
| TTS | **A preencher** | — | voz/instruções |
| OCR | Tesseract local, conferir versão | — | idioma por |
| Imagem gerada por IA | **A preencher** | — | prompt salvo |

## Resultados
- Experimento A/B/C: **pendente**; anexe matriz real, entradas, saídas, escolha baseada em evidência.
- Extração C01/C06: anexar JSON, casos de ausência e decisão humana.
- C02 STT: WER bruto/revisado **a medir**; revisar nome, data, protocolo.
- C03 OCR: CER bruto/revisado **a medir**; anotar trechos ilegíveis, corrigir só após conferir original.
- C04 timbre: validar proporção e declaração de material fictício.
- RF10 peça visual: modelo gerador, prompt, data, custos e nota de proveniência **a registrar**.
- Avaliação RF13 (0–10): preencher por caso com cinco critérios e assinatura do revisor.
- Taxa de aprovação direta e com correção: **não calculada** sem revisão verdadeira.

## Custos e execução
- LLM: extrair uso de tokens do log. Se preço não foi conferido em tabela oficial, registrar **indisponível**, não inventar.
- STT/TTS/imagem: cobrança pode ser por áudio ou imagem, não inferir a partir dos tokens do LLM.
- Indicar limites de cota, erros 429 e indisponibilidade se ocorrerem.

## Riscos e limitações
Prompt injection fora dos padrões da heurística; nomes de autoridades inventados e não detectados por regra; OCR de imagens com ruído; erros em nome/protocolo mesmo com WER baixo; indisponibilidade da API; separação entre mock e modelo real; dados pessoais em logs. A atuação humana é indispensável.

## Responsabilidade e LGPD
Somente cenários fictícios. Proibido envio automático. Equipe deve conferir critérios do enunciado, modelo/provedor, retenção e transparência; consulte `lgpd.md`.

> **Nota de integridade:** este documento é um modelo, não um relatório de validação concluída. Preencher resultados exclusivamente após medição e revisão.
