# ADR 0002 — Monólito modular orientado a eventos

- **Status:** Aceita
- **Data:** 2026-08-18

## Contexto

O núcleo precisa ser reproduzível e auditável sem introduzir a complexidade operacional de serviços distribuídos nesta fase.

## Problema

Definir a forma de composição inicial e a semântica entre módulos de domínio.

## Alternativas consideradas

- Pipeline síncrono acoplado: simples, mas dificulta replay e isolamento.
- Microserviços com broker: isolamento físico, porém complexidade e não determinismo prematuros.
- Event sourcing integral: reconstrução ampla, mas custo desproporcional.
- Monólito modular orientado a eventos: fronteiras explícitas e determinismo inicial.

## Decisão

Adotar monólito modular orientado a eventos. `Event` descreve fato ocorrido; `Intent`, proposta; `Decision`, avaliação autoritativa; e `Command`, solicitação de efeito externo. Replay e Backtest admitem despacho sequencial determinístico; concorrência é detalhe futuro das bordas de I/O.

## Invariantes

- O domínio não pressupõe threads, `asyncio`, broker externo ou paralelismo.
- Fronteiras de módulo são contratuais mesmo no mesmo processo.
- Separação física futura não pode alterar a semântica de domínio.

## Consequências positivas

Preserva simplicidade operacional, testes determinísticos e evolução gradual.

## Consequências negativas / trade-offs

Exige disciplina para impedir acoplamento interno e não oferece isolamento de falhas de processos separados.

## Condições para reabrir a decisão

Evidência de requisitos de escala, isolamento ou disponibilidade que não possam ser atendidos sem distribuição, registrada em ADR novo.

## Relação com outros ADRs

Base para ADRs 0003 a 0014; o limite financeiro é definido especialmente em ADR 0007.
