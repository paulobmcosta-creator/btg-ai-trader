# ADR 0013 — Observabilidade, proveniência e rastreabilidade de decisões

- **Status:** Aceita
- **Data:** 2026-08-18
- **Refinada por:** ADR 0021 — Refinamento de provenance, Runs, capture e lineage

## Contexto

Auditoria exige saber o que ocorreu, por qual cadeia causal e qual versão exata do sistema o produziu.

## Problema

Definir proveniência mínima sem confundir versões com uma execução específica.

## Alternativas consideradas

- Apenas logs operacionais: insuficientes para reconstrução.
- Somente versionar modelos: não identifica configuração, código ou execução.
- Telemetria e provenance vinculadas: responde operação, causa e versão.

## Decisão

Artefatos de decisão futuros são vinculáveis, quando aplicável, a `strategy_version`, `model_version`, `feature_set_version`, versão/hash de configuração, `code_revision` e `run_id`, além de `event_id`, correlação e causalidade. Versões respondem “o quê”; `run_id`, “em qual execução”. A regra vale para Backtest, Paper e Live; Replay que produza decisão de domínio também a observa. Telemetria registra receipts e tempos por componente, transições e falhas sem substituir o journal.

## Invariantes

- Proveniência não é opcional onde há decisão de domínio aplicável.
- `run_id` não substitui versionamento.
- Rastreabilidade causal e observabilidade operacional são complementares.

## Consequências positivas

Permite reprodução experimental, comparação Paper/Backtest e investigação forense futura.

## Consequências negativas / trade-offs

Exige disciplina de versionamento e propagação de contexto.

## Condições para reabrir a decisão

Novos tipos de artefato ou fonte de versão, por ADR sem remover os vínculos mínimos.

## Relação com outros ADRs

Baseado em 0003 e 0009; aplicado a 0007, 0008, 0010 e 0014.
