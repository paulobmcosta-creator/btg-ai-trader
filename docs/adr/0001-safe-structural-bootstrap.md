# ADR 0001 — Bootstrap estrutural seguro

- **Estado:** Aceita
- **Data:** 2026-08-17

## Contexto

O projeto pretende evoluir para um sistema quantitativo intradiário, domínio em que falhas podem produzir perdas financeiras. A primeira entrega deve criar memória técnica e disciplina de engenharia sem capacidade operacional.

## Decisão

Adotar projeto Python com layout `src/`, testes e documentação versionada. Manter dependências de runtime vazias e proibir nesta fase estratégias, ML operacional, integrações BTG/MT5, transmissão de ordens, credenciais, dinheiro real, produção e deploy.

O futuro Risk Engine terá precedência sobre sinais. Evoluções críticas dependerão de ADR, protocolos verificáveis e gates explícitos, incluindo validação fora da amostra e paper trading.

## Consequências

- O repositório começa seguro por construção e sem efeito financeiro.
- Escolhas de stack permanecem abertas até haver requisitos e evidências.
- Funcionalidade aparente é deliberadamente menor; auditabilidade e controles vêm primeiro.
