# Encerramento da Parte 1 — revisão humana pendente

**Responsável:** Diego (Estudante 1). **Avaliadores:** equipe Diego, Ayron e Guilherme.  
**PR:** https://github.com/diegocbaleite/desafio-05-central-atendimento-ia/pull/1

## Evidências já disponíveis
- Matriz real: `resultados/experimento_prompts/real/matriz.csv`: nove respostas com status sucesso, mesmo modelo (`nvidia/nemotron-3-super-120b-a12b:free`) e temperatura 0,2.
- Nove saídas textuais e metaprompt executado estão na mesma pasta.
- Notas **preliminares assistidas por IA** e justificativas: `documentacao/relatorio_tecnico.md`.
- Prompt C original preservado; `prompts/experimento/metaprompt_v2_atendimento.md` é uma proposta de correção **ainda não testada**.
- Nenhuma mensagem foi enviada automaticamente.

## Checklist de validação a preencher por uma pessoa
- [ ] Confirmar que as nove respostas e os gabaritos usam apenas dados fictícios.
- [ ] Conferir C01: prazos, deferimento, custos e contatos inventados em A/C; correções necessárias em B.
- [ ] Conferir C05: a injeção não foi seguida literalmente, mas ocorreram invenções administrativas em A/C e afirmações não comprovadas em B.
- [ ] Conferir C06: ausências de nome/data/protocolo e prazos indevidos.
- [ ] Revisar ou substituir as notas técnicas preliminares por notas dos estudantes, registrando data e responsável.
- [ ] Conferir que o metaprompt v2 não foi confundido com o C original ou avaliado como se tivesse sido executado.
- [ ] Rodar `python -m unittest discover -s testes -t .` no HEAD final do PR e conferir o GitHub Actions.
- [ ] Validar a nova execução opcional de `python -m src.main experimento --metaprompt-v2` (somente se houver cota); nunca alterar a matriz original.
- [x] Integrar `origin/main` na feature: merge `c2719ef`, conflitos de configuração/cliente/experimento resolvidos, 13 testes locais aprovados.
- [ ] Revisar após as correções adicionais desta feature e validar os testes no GitHub Actions.

## Registro de revisão humana

| Revisor | Data | Decisão (aprovar/corrigir/rejeitar) | Justificativa ou correções |
|---|---|---|---|
| Diego | não localizado | pendente | não localizado |
| Ayron | não localizado | pendente | não localizado |
| Guilherme | não localizado | pendente | não localizado |

**Não assinar nem marcar itens como concluídos sem revisão efetiva.**

## Correções posteriores à comparação original
- `src/experimento.py` agora salva cada execução em subpasta de identificador UTC, prevenindo sobrescrita das evidências.
- Grava `matriz.csv` após cada chamada; falhas isoladas não são confundidas com sucesso.
- `python -m src.main experimento --metaprompt-v2` gera uma **nova** execução. A versão revisada ainda não possui resultados reais validados.
- Experimento anterior de 9 resultados, já versionado em `real/`, permanece intocado.

**Importante:** aprovação de PR, notas humanas e revisão de privacidade dependem de pessoas, não de código.
