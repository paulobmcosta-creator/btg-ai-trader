# Sprint 1 — Market Observer

## Estado atual

```text
SPRINT_1_STATUS = FINAL_ACCEPTANCE_RECONCILIATION
FOUNDATION_0A_TO_0F = FORMALLY_CLOSED
PRE_CODE_RECONCILIATION = COMPLETE
S1_IMPLEMENTATION = COMPLETE_CURRENT_SCOPE
REAL_PROVIDER_RUNTIME_EVIDENCE = PASS
CURRENT_PROVIDER = XP_SUPPLIED_MT5
PROVIDER_ID = xp-mt5
PRE_RECONCILIATION_INTEGRATED_HEAD = 6457ae1dfec6e91034741e57c6343397f368cbc2
PRE_RECONCILIATION_EXACT_TREE_CI = PASS
GITHUB_NATIVE_SECURITY_GATE = PASS
OFFICIAL_CODEX_SECURITY_DIFF_SCAN = NOT_EXECUTED
SPRINT1_ACCEPTANCE = PENDING_FINAL_RECONCILIATION_CI
```

O Sprint 1 foi implementado sob o contrato 0F-E integral. O Market Observer real foi exercitado de forma estritamente passiva contra XP/MetaTrader 5 em `s1-xp-capture-a12`, com evidência de discovery, ticks, candle finalizado, provenance, health e latência, sem introdução de capacidade financeira.

## Objetivo e fronteira de segurança

O Sprint 1 implementa um **Market Observer** estritamente:

```text
READ_ONLY_BY_CONSTRUCTION
STRUCTURAL_ESCALATION
```

O escopo positivo e os critérios de aceitação são governados pelo Contrato de Entrada canônico `docs/foundation/0F-E_sprint1_entry_contract.md`. O artefato `docs/foundation/0F-F_foundation_final_gate.md` permanece snapshot histórico da adjudicação final da Fundação.

As capacidades financeiras continuam ausentes:

```text
STRATEGY_OPERATIONAL_PATH = ABSENT
RISK_AUTHORIZATION_ENGINE = ABSENT
ORDER_API = ABSENT
PAPER_PATH = ABSENT
LIVE_PATH = ABSENT
FINANCIAL_LEDGER_MUTATION = ABSENT
REAL_MONEY_AUTHORITY = ABSENT
```

## Autoridade e rastreabilidade

O Sprint 1 permanece cumulativamente governado por:

- 0F-B — registro canônico das decisões deferidas;
- 0F-C — 41 RQMs, 27 HQIs e 7 QPIs aplicáveis ao Sprint 1;
- 0F-D — 20 Negative Capabilities e 10 obrigações NEG-CAP;
- 0F-E — 118 cláusulas `S1-EC-001` a `S1-EC-118`;
- 0F-F — snapshot histórico da Fundação;
- ADR-0026 — decisão vigente do provider XP/MT5 para a qualificação final do Observer.

Nenhum desses artefatos congelados foi reescrito para acomodar a implementação.

## Evidência real do provider

A sessão qualificadora ocorreu em 2026-09-16:

```text
CAPTURE_SCOPE = s1-xp-capture-a12
PROVIDER = xp-mt5
INSTRUMENT = WINV26
TIMEFRAME = PERIOD_M1
CODE_REVISION = e622658922ff38e49e1112a48d91eecb2d43a522
DISCOVERY_RECORDS = 18
TICK_RECORDS = 8005
CANDLE_RECORDS = 2
BRIDGE_FINAL_STATE = IDLE
WORKTREE_AT_CAPTURE = CLEAN
```

A evidência sanitizada está em `docs/program/workstreams/S1-XP-MT5-RUNTIME-EVIDENCE-2026-09-16.md`; payloads brutos permanecem fora do Git.

## Engenharia do HEAD integrado

Após o merge do PR #59, o commit `6457ae1dfec6e91034741e57c6343397f368cbc2` executou o GitHub Actions run `35126543429`. Passaram no HEAD exato:

```text
tests
lint
types
compile
dependencies
foundation
boundary
diff
```

Isso resolveu o antigo blocker de exact-final-tree engineering evidence para a árvore integrada anterior à reconciliação documental final.

## Segurança final — decisão de instrumento

O Official Codex Security Diff Scan não foi executado e não é declarado como executado. Por decisão humana explícita de 2026-09-16, a garantia final de segurança do Sprint 1 usa o pacote GitHub-native documentado em:

`docs/program/S1_GITHUB_SECURITY_ALTERNATIVE_GATE_2026-09-16.md`.

A substituição altera apenas o instrumento de evidência. `READ_ONLY_BY_CONSTRUCTION`, `STRUCTURAL_ESCALATION`, RQMs, HQIs/QPIs e NEG-CAP continuam integrais.

## Estado dos gates de saída

```text
RQMS = 41/41 SATISFIED_OR_CURRENT_SCOPE
NEG_CAP_01_TO_10 = PASS
READ_ONLY_BY_CONSTRUCTION = PASS
STRUCTURAL_ESCALATION = PASS
REAL_PROVIDER_EVIDENCE = PASS
GITHUB_NATIVE_SECURITY_GATE = PASS
FINAL_RECONCILIATION_BRANCH_CI = PENDING
```

Todos os 11 exit criteria estão substantivamente prontos para PASS. A única operação remanescente antes do veredito formal é executar os checks no HEAD desta reconciliação documental, registrar a evidência e então promover formalmente ao Sprint 2.

Consulte:

- `docs/program/PROGRAM_EXECUTION.md`;
- `docs/program/RQM_EXECUTION_STATUS.md`;
- `docs/program/S1_FINAL_ACCEPTANCE_GATE.md`;
- `docs/program/S1_GITHUB_SECURITY_ALTERNATIVE_GATE_2026-09-16.md`.

## Próxima transição permitida

Após o HEAD final desta reconciliação passar integralmente os checks de engenharia/Foundation/boundary, o projeto pode registrar:

```text
SPRINT1_PROVIDER_QUALIFIED = YES
SPRINT1_ACCEPTANCE = YES
PROMOTION_TO_SPRINT_2 = YES
```

A promoção ao Sprint 2 autoriza apenas o escopo próprio de **Data Platform & causal market-data replay**. Ela não autoriza Paper, Risk, Strategy, ML operacional, ordens, execução financeira ou dinheiro real.