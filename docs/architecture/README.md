# Arquitetura

## Visão inicial, não implementada

O contexto do projeto aponta para um sistema quantitativo intradiário em camadas:

```text
Market Data -> Features -> Regime/Signals/Scenarios -> Risk Engine -> Execution
                                      |                    |
                                      +---- observabilidade+
```

Nesta etapa, o diagrama é apenas uma direção arquitetural. Nenhum componente financeiro está implementado. O Risk Engine futuro será independente, fail-safe e terá precedência absoluta sobre sinais e decisões.

Pesquisa/treinamento deverão ser isolados do eventual nó de execução. Backtest, replay, validação temporal fora da amostra e paper trading precederão qualquer proposta de uso real.

## Limites atuais

- Não há adaptador BTG ou MetaTrader 5.
- Não há coleta de mercado, estratégia, features, modelo, simulador ou executor.
- Não há infraestrutura cloud ou produção.
- Não há autorização para ordens ou dinheiro real.

## Decisões em aberto para o Sprint 0

- escopo preciso do primeiro observador de mercado;
- contratos entre camadas e modelo de eventos;
- política de tempo, calendários, timezone e precisão numérica;
- proveniência, qualidade, retenção e versionamento de dados;
- armazenamento e formato de configuração;
- observabilidade, trilha de auditoria e tratamento de falhas;
- estratégia de testes e ameaças específicas por componente;
- critérios mensuráveis de cada gate.
