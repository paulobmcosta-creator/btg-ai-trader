# Arquitetura

## Baseline lógica do Sprint 0C, não implementada

O contexto do projeto aponta para um sistema quantitativo intradiário em camadas:

```text
Market Data Provider -> Normalized Market Events -> Signal -> TradeIntent
                                                       |
                                                       v
                                               RiskDecision/Authorization
                                                       |
                                                       v
                                                Order Planning -> OrderIntent
                                                       |
                                                       v
                                                   Execution (futura)
```

Esta é uma baseline lógica, não uma implementação nem autorização operacional. Nenhum componente financeiro está implementado. O Risk Engine futuro será independente, fail-safe e terá precedência absoluta sobre sinais e decisões; somente Execution poderá solicitar efeito externo após autorização válida.

Pesquisa/treinamento deverão ser isolados do eventual nó de execução. Backtest, replay, validação temporal fora da amostra e paper trading precederão qualquer proposta de uso real.

## Limites atuais

- Não há adaptador BTG ou MetaTrader 5.
- Não há coleta de mercado, estratégia, features, modelo, simulador ou executor.
- Não há infraestrutura cloud ou produção.
- Não há autorização para ordens ou dinheiro real.

## Decisões materializadas no Sprint 0C

- arquitetura modular orientada a eventos e envelope causal versionado;
- semântica temporal, ordenação contextual e fidelidade histórica declarada;
- identidade, lifecycle e rollover explícitos de instrumentos;
- fronteiras de dados, intents, Risk e Execution;
- perfis Replay/Backtest/Paper/Live e requisito de determinismo;
- persistência lógica, recovery, reconciliação, fail-safe e eventos inválidos;
- ownership de Ledger, Position/Portfolio e exposição;
- observabilidade, provenance e identidade de execução.

Os schemas, interfaces, tolerâncias, calendário, tecnologia física e protocolos quantitativos permanecem para 0D e sprints posteriores.
