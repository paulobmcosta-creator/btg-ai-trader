# ADR 0005 — Identidade, lifecycle e rollover de instrumentos

- **Status:** Aceita
- **Data:** 2026-08-18

## Contexto

Famílias econômicas, contratos negociáveis e símbolos de provedores têm identidades distintas.

## Problema

Evitar que aliases externos ou rollover mutem a identidade histórica de um contrato.

## Alternativas consideradas

- Usar símbolo do provider como identidade: instável e dependente de fornecedor.
- Um alias mutável por família: apaga qual contrato foi selecionado.
- Identidades separadas e resolução versionada: mantém história verificável.

## Decisão

Manter `InstrumentFamilyId`, `TradableInstrumentId` e `ProviderInstrumentRef` distintos. Instrumento concreto é imutável; seus atributos e lifecycle podem ser versionados. Rollover é mapeamento explícito, com validade e motivo, de família para instrumento negociável; não é mutação de `WINQ26` em outro contrato.

## Invariantes

- Identidade interna não depende exclusivamente de texto de provider.
- Disponibilidade momentânea não muda identidade.
- Registros históricos permitem responder qual instrumento uma política selecionou em dado instante.

## Consequências positivas

Preserva continuidade histórica e permite múltiplos provedores.

## Consequências negativas / trade-offs

Requer registry e resolução explícitos em fase posterior.

## Condições para reabrir a decisão

Nova classe de instrumento que não possa ser modelada com identidades separadas, formalizada em ADR.

## Relação com outros ADRs

O TradeIntent do ADR 0007 deve referenciar instrumento concreto; dados do ADR 0006 usam referências do provider.
