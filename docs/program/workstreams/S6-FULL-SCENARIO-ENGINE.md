# S6-FULL-SCENARIO-ENGINE — Full Sprint 6 Functional Execution Packet

```text
SPRINT = 6
WORK_MODE = LARGE_BATCH_AUTONOMOUS
ISSUE = #83
CANONICAL_BRANCH = sprint/6-scenario-engine
WORK_BRANCH = s6/02-full-scenario-engine
CANONICAL_BASE_SHA = 1c55fb1335caef5dec20e54a1fc5c62a33467de0
FUNCTIONAL_IMPLEMENTATION_AUTHORIZED = YES
HUMAN_AUTHORIZATION_DATE = 2026-09-22
INDEPENDENT_AUDIT = AFTER_FULL_SPRINT_CANDIDATE
MERGE = COMPLETED_BY_EXPLICIT_HUMAN_AUTHORIZATION
ADDITIONAL_RECURRING_COST = ZERO
NEW_MANDATORY_RUNTIME_DEPENDENCIES = 0
```

## 1. Governing contract

Implementation is strictly bounded by:

- `docs/program/S6_ENTRY_CONTRACT.md`;
- `docs/program/S6_DECISION_REGISTER.md`;
- `docs/program/S6_CAPABILITY_MATRIX.md`;
- `docs/program/S6_ENTRY_GATE.md`;
- Foundation and quantitative protocols.

The pre-authorization remediation is canonical PASS and all eight findings are binding implementation requirements.

## 2. Execution phases

1. **Domain and immutable evidence boundary**
   - `ScenarioInputBoundary`, neutral `ModelEvidenceSnapshot`, content-addressed digests.
2. **Causal regimes**
   - deterministic threshold classification;
   - development-only threshold fitting;
   - explicit `RegimeUseMode` and UNKNOWN.
3. **Scenario definitions and grids**
   - finite, ordered, predeclared deterministic grids;
   - structural-consistency constraints;
   - no probabilities.
4. **Observed series, tail and path**
   - empirical-only observed distributions;
   - governed tail policy and sample sufficiency;
   - guarded path metrics.
5. **Disposition and robustness**
   - canonical 0E-F dispositions;
   - separate robustness characterization;
   - no compensatory score.
6. **Protected-evidence history**
   - append-only search/adaptation evidence;
   - same-protected-boundary reuse rejection.
7. **Sprint 3 economic stress orchestration**
   - preserve actions/replay/instrument identity;
   - delegate fills/accounting/P&L to Sprint 3 kernel.
8. **Tests, security boundary and CI**
   - 100% statement/branch coverage of S6 package;
   - full regression, Ruff, strict mypy, compile, dependency audit;
   - S6 negative-capability scanner.
9. **Final acceptance and independent audit**
   - materialize closure-candidate evidence;
   - exact-head CI/upstream;
   - stop before merge.

## 3. Absolute negative capabilities

No Strategy/Signal operational path, Risk authority, sizing, OrderIntent/OrderPlan/ExecutionOrder, broker account/order capability, Paper/Live, real money, FinancialLedger mutation, automatic promotion, Monte Carlo, bootstrap, stochastic scenario generation, adaptive causal clustering, synthetic probabilities, unsafe deserialization, dynamic execution, network clients or subprocesses.

## 4. Stop condition

```text
SPRINT_6_FUNCTIONAL_IMPLEMENTATION = COMPLETED
MERGE_AUTHORIZED = YES_COMPLETED
STOP_AFTER_INDEPENDENT_AUDIT = YES
```


## Candidate audit remediation — 2026-09-22

Ten semantic findings were closed in one controlled candidate remediation:

1. causal regime assignment requires explicit `as_of_time`;
2. regime observations and thresholds bind units;
3. `STRATEGY_BOUND` fails closed until verified upstream regime-use evidence exists;
4. experimental parity includes S6 code revision and role provenance;
5. protected S4 evidence must match the canonical protected-evidence record;
6. S5 model snapshots are issued through an optional adapter using real verified S5 training manifests while core remains ML-dependency-free;
7. empirical loss direction is explicit and tail policy binds missing-value policy;
8. research history has a deterministic digest, typed scenario predeclaration registration, and is included in `ScenarioRunManifest`;
9. public economic shock application enforces adverse-only semantics and execution verifies ScenarioSpec code revision;
10. shock units are canonical per target.

```text
S6_FUNCTIONAL_CANDIDATE_AUDIT = PASS
OPEN_CANDIDATE_FINDINGS = 0
MERGE_AUTHORIZED = YES_COMPLETED
```

No Strategy, Risk, Paper, Live, broker/order, ledger or real-money authority is introduced.


## Canonical closure — PR #85

```text
S6_FUNCTIONAL_PR_HEAD = 69b5797306027a91b5366d44c4d22f2ab1caa37f
S6_FUNCTIONAL_PR_REAUDIT = PASS
S6_FUNCTIONAL_MERGE_SHA = 0e9438590338e2a322e96306a4dd8cb43d957535
S6_POST_MERGE_PYTHON_CI_RUN = 35898586034
S6_POST_MERGE_ENTRY_GATE_CI_RUN = 35898586113
S6_POST_MERGE_UPSTREAM_RUN = 35898585983
S6_FINAL_VERDICT = PASS
OPEN_FUNCTIONAL_BLOCKERS = 0

SPRINT_7 = NOT_AUTHORIZED
PAPER_TRADING = NO
LIVE_TRADING = NO
REAL_MONEY = NO
```
