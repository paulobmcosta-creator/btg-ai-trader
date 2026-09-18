# Program Execution — BTG AI Trader

## Current remote checkpoint

```text
AUTHORITATIVE_STATE = GITHUB_REMOTE
REPOSITORY = paulobmcosta-creator/btg-ai-trader
FOUNDATION_0A_TO_0F = FORMALLY_CLOSED

SPRINT_1_BRANCH = sprint/1-market-observer
SPRINT_1_ACCEPTED_HEAD = 57d820e256dd386624c1842c6f60b6797ba792aa
SPRINT_1_POST_MERGE_CI_RUN = 35129410553
SPRINT_1_POST_MERGE_CI = PASS
SPRINT_1_LIFECYCLE = FORMALLY_CLOSED
SPRINT_1_FINAL_VERDICT = PASS
SPRINT1_PROVIDER_QUALIFIED = YES
SPRINT1_ACCEPTANCE = YES

SPRINT_2_BRANCH = sprint/2-data-platform-replay
SPRINT_2_LIFECYCLE = FORMALLY_CLOSED
SPRINT_2_FINAL_VERDICT = PASS
SPRINT_2_CANONICAL_HEAD = ba6c0c41988fc9fefbdff13b0daedf96301dd74c
SPRINT_2_SCOPE = DATA_PLATFORM_AND_CAUSAL_MARKET_REPLAY
SPRINT_2_ENTRY_GATE = PASS
S2_A = ACCEPTED (PR #65, 9faa43c3bc112c1d2e558aa3e1518371880cc518)
S2_B = ACCEPTED (PR #67, 071e004f2be8e5925b0de63db97af61cbbf37b30)
S2_C = ACCEPTED (PR #70, ba6c0c41988fc9fefbdff13b0daedf96301dd74c)
PROMOTION_TO_SPRINT_3_GATE = YES

SPRINT_3_BRANCH = sprint/3-deterministic-economic-backtesting
SPRINT_3_LIFECYCLE = FORMALLY_CLOSED
SPRINT_3_FINAL_VERDICT = PASS
SPRINT_3_SCOPE = DETERMINISTIC_ECONOMIC_BACKTESTING
SPRINT_3_CANONICAL_HEAD = 6333b8f431d43be9c40f3222fbbe17cf06509033
SPRINT_3_PR = #72
SPRINT_3_ISSUE = #71 (CLOSED_COMPLETED)
SPRINT_3_INDEPENDENT_REAUDIT = PASS
SPRINT_3_POST_MERGE_CI_RUN = 35256018204
SPRINT_3_POST_MERGE_CI = PASS
SPRINT_3_POST_MERGE_UPSTREAM_RUN = 35256018048
SPRINT_3_POST_MERGE_UPSTREAM = PASS
SPRINT_3_ENTRY_CONTRACT = docs/program/S3_ENTRY_CONTRACT.md
SPRINT_3_DECISION_REGISTER = docs/program/S3_DECISION_REGISTER.md
SPRINT_3_CAPABILITY_MATRIX = docs/program/S3_CAPABILITY_MATRIX.md
SPRINT_3_FINAL_ACCEPTANCE = docs/program/S3_FINAL_ACCEPTANCE.md
S3_ENTRY_GATE = PASS

PROMOTION_TO_SPRINT_4_GATE = YES
SPRINT_4_BRANCH = sprint/4-statistical-baselines
SPRINT_4_LIFECYCLE = FORMALLY_CLOSED
SPRINT_4_FINAL_VERDICT = PASS
SPRINT_4_SCOPE = STATISTICAL_BASELINES
SPRINT_4_CANONICAL_BASE = 922adee625029c0cbd6c665f8906e7fd99cf71cb
SPRINT_4_FUNCTIONAL_MERGE = 0786ace3e6a83ecb23a508af860f43a2fd5d64e8
SPRINT_4_PR = #74
SPRINT_4_ISSUE = #73
SPRINT_4_INDEPENDENT_REAUDIT = PASS
SPRINT_4_POST_MERGE_CI_RUN = 35304136357
SPRINT_4_POST_MERGE_CI = PASS
SPRINT_4_POST_MERGE_UPSTREAM_RUN = 35304136369
SPRINT_4_POST_MERGE_UPSTREAM = PASS
SPRINT_4_ENTRY_CONTRACT = docs/program/S4_ENTRY_CONTRACT.md
SPRINT_4_DECISION_REGISTER = docs/program/S4_DECISION_REGISTER.md
SPRINT_4_CAPABILITY_MATRIX = docs/program/S4_CAPABILITY_MATRIX.md
SPRINT_4_FINAL_ACCEPTANCE = docs/program/S4_FINAL_ACCEPTANCE.md
S4_ENTRY_GATE = PASS
S4_TASK_PACKET = docs/program/workstreams/S4-ANTIGRAVITY-FULL-SPRINT.md
S4_WORK_BRANCH = s4/00-full-statistical-baselines
PROMOTION_TO_SPRINT_5_GATE = YES
SPRINT_5_ENTRY_GATE = AUTHORIZED
SPRINT_5_FUNCTIONAL_IMPLEMENTATION = NOT_AUTHORIZED

OFFICIAL_CODEX_SECURITY_DIFF_SCAN = NOT_EXECUTED
SPRINT1_GITHUB_NATIVE_SECURITY_GATE = PASS

REAL_MONEY = NO
LIVE_TRADING = NO
PAPER_TRADING = NO
STRATEGY_OPERATIONAL_PATH = ABSENT
RISK_OPERATIONAL_PATH = ABSENT
BROKER_ORDER_API = ABSENT
FINANCIAL_LEDGER_MUTATION = ABSENT
ECONOMIC_COMMITMENT = IMPOSSIBLE
```

## Sprint 1 accepted baseline

Sprint 1 — Market Observer — permanece formalmente fechado e aprovado. O provider qualificado é XP-supplied MetaTrader 5 em arquitetura passiva/read-only. A captura qualificadora é `s1-xp-capture-a12` contra `WINV26` / M1.

O Official Codex Security Diff Scan não foi executado. O instrumento final de segurança aceito para o Sprint 1 é o pacote GitHub-native documentado em `docs/program/S1_GITHUB_SECURITY_ALTERNATIVE_GATE_2026-09-16.md`.

## Sprint 2 accepted baseline

Sprint 2 — Data Platform & Causal Market Replay — está formalmente fechado em `ba6c0c41988fc9fefbdff13b0daedf96301dd74c`.

Escopo aceito:

- normalização lossless e qualidade de dados;
- causal replay por `knowledge_time`;
- uma lane `(provider_id, capture_scope)`;
- ordem fornecida preservada, regressões rejeitadas e ausência de sorting reparador;
- cutoffs monotônicos inclusivos;
- velocidade virtual racional exata;
- replay determinístico;
- source evidence imutável;
- missingness preservada;
- zero Strategy/Risk/Paper/Live/broker-order/real-money/FinancialLedger mutation.

## Sprint 3 — Deterministic Economic Backtesting — FORMALLY CLOSED / PASS

O Sprint 3 foi implementado no PR #72 e auditado independentemente sobre o HEAD de trabalho `b0c71b2910509c7b0be5b5e59bb5c7a54351b6fc`.

O PR #72 foi integrado em `sprint/3-deterministic-economic-backtesting` no commit canônico:

```text
6333b8f431d43be9c40f3222fbbe17cf06509033
```

A validação pós-merge no commit exato concluiu:

```text
Sprint 3 Python CI
RUN = 35256018204
JOBS = 10/10 PASS

Pinned upstream engineering verification
RUN = 35256018048
JOBS = 2/2 PASS

ISSUE #71 = CLOSED / COMPLETED
OPEN_S3_BLOCKERS = 0
```

O kernel aceito permanece estritamente classificado como **Deterministic Execution Economics Kernel**. Ele implementa backtesting econômico determinístico, spread side-aware, slippage adverso, taxas explícitas, latência virtual, contabilidade de posição/P&L simulada, métricas econômicas descritivas, proteção contra future-data leakage, sensitivity sweeps e provenance criptográfica.

O Sprint 3 não cria nem autoriza:

```text
Strategy operacional
Signal operacional
Risk operacional
Paper operacional
Live operacional
broker account/order API
order submission / modification / cancellation
real money
canonical FinancialLedger mutation
predictive ML operacional
external economic commitment
```

## Sprint 4 — Statistical Baselines — Formal Closure

Sprint 4 has been fully implemented and verified under single-batch autonomous execution mode:

- **Work Branch:** `s4/00-full-statistical-baselines`
- **Canonical Target:** `sprint/4-statistical-baselines`
- **Issue:** #73
- **Artifact:** `docs/program/S4_FINAL_ACCEPTANCE.md`
- **Scope:** Complete Prospective Temporal Evaluation & Deterministic Catalog (`btg_ai_trader.statistical_baselines`):
  - Domain, samples, and deterministic identities (`domain.py`)
  - Evaluation boundaries, temporal folds, and walk-forward plans (`boundaries.py`)
  - Walk-forward splitting, rolling/expanding modes, purging, and embargo (`splits.py`)
  - Deterministic catalog of seven simple baselines (`baselines.py`)
  - Standardized continuous and classification metrics (`metrics.py`)
  - Probability calibration diagnostics and binning (`calibration.py`)
  - Temporal fold evaluation and distribution-preserving aggregation (`evaluation.py`)
  - Candidate comparison with strict protected-test rejection invariant (`comparison.py`)
  - Cryptographic input boundaries, manifests, and evaluation provenance (`provenance.py`)
- **Verification:** 100% statement (1,377/1,377) and branch (468/468) coverage across all modules and boundary scanner, 200 passed tests, 100-repetition byte-identical determinism, adversarial leakage detection, zero lint errors, zero type errors.
- **Verdict:** `SPRINT_4_FINAL_VERDICT = PASS`, `SPRINT_4_LIFECYCLE = FORMALLY_CLOSED`.
- **Independent re-audit:** PASS on PR #74 exact head `6473bd844ff69ded83f6a536397ff3e4fafffbb1`.
- **Functional merge:** `0786ace3e6a83ecb23a508af860f43a2fd5d64e8`.
- **Post-merge validation:** Sprint 4 CI `35304136357` PASS 11/11; pinned upstream `35304136369` PASS 2/2; 957/957 repository tests; S4 package 1,377/1,377 statements and 468/468 branches.

## Promotion boundary — Sprint 5

Sprint 4 is formally closed. The next authorized step is exclusively the materialization, review, and approval process for the Sprint 5 Entry Gate.

```text
PROMOTION_TO_SPRINT_5_GATE = YES
SPRINT_5_ENTRY_GATE = AUTHORIZED
SPRINT_5_FUNCTIONAL_IMPLEMENTATION = NOT_AUTHORIZED
```

Nenhum código funcional de Sprint 5 (ML Engine, scikit-learn, XGBoost, LightGBM, PyTorch), busca de hiperparâmetros, Strategy, Risk, Paper ou Live está autorizado nesta fase.

## Repository hardening

Issue #61 permanece aberta para Administrative Branch Protection & Ruleset Hardening. A proteção administrativa continua ausente/pending; CI, boundary scanners e revisão manual não substituem enforcement administrativo. Issue #61 permanece defense-in-depth e não bloqueou o fechamento funcional do Sprint 3 ou 4.

Issue #6 permanece aberta para a errata histórica 0F-F/QPI. `docs/protocols/quantitative/TRACEABILITY.md` continua sendo a autoridade canônica das QPIs; o snapshot histórico 0F-F permanece congelado.

## Canonical next action

O próximo trabalho autorizado é exclusivamente a **materialização e revisão do Sprint 5 Entry Gate**. Implementação funcional do Sprint 5 permanece proibida até aprovação formal desse gate.