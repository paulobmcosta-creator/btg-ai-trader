# Sprint 6 Capability Matrix — Scenario Engine

## 1. Entry-gate capabilities

| ID | Capability | Evidence | Status |
|---|---|---|---|
| **S6-EG-AC-01** | Exact closed Sprint 5 baseline | final S5 head `9956f3a...` | PASS |
| **S6-EG-AC-02** | Sprint 6 Entry Gate canonical | PR #80 merged; gate PASS | PASS |
| **S6-EG-AC-03** | Final canonical Entry Gate head reconciled | `616849f8e77ecf3624b2b9362c1ef42c7fb9bcc1` | PASS |
| **S6-EG-AC-04** | Final canonical gate CI | run `35474371811` | PASS |
| **S6-EG-AC-05** | Final canonical pinned upstream | run `35474371852` | PASS |
| **S6-EG-AC-06** | DD-89 adjudicated | S6 Decision Register | PASS |
| **S6-EG-AC-07** | Functional implementation remains unauthorized | S6 governance docs | PASS |
| **S6-EG-AC-08** | Zero additional recurring cost | no paid service/dependency | PASS |

## 2. Pre-authorization remediation requirements

These requirements must be fully materialized and independently reviewed before a human functional-authorization decision.

| ID | Requirement | Required evidence | Remediation state |
|---|---|---|---|
| **S6-PRE-01** | Mandatory fail-closed `ScenarioInputBoundary` with a role for every analysis | Entry Contract + Decision Register | MATERIALIZED |
| **S6-PRE-02** | Protected-evidence inheritance | `EvaluationRole`, `EvaluationHistory`, protected boundary and scenario research-history rules | MATERIALIZED |
| **S6-PRE-03** | Same-boundary protected reuse rejection | `PROTECTED_INFORMED` rule | MATERIALIZED |
| **S6-PRE-04** | Neutral model evidence boundary | no direct ML-core import/model deserialization | MATERIALIZED |
| **S6-PRE-05** | `ScenarioOutcomeSet != ObservedDistributionSummary` | explicit type/semantic separation | MATERIALIZED |
| **S6-PRE-06** | Explicit `RegimeUseMode` | causal stratification vs strategy-bound vs retrospective | MATERIALIZED |
| **S6-PRE-07** | Predeclared `ScenarioDispositionPolicy` | canonical 0E-F dispositions, separate robustness characterization and non-compensatory invalidity | MATERIALIZED |
| **S6-PRE-08** | Sprint 3 economic-kernel delegation | action/replay identity-preservation rules | MATERIALIZED |
| **S6-PRE-09** | ObservedSeries path/tail semantics | unit/population/order/time/denominator rules | MATERIALIZED |
| **S6-PRE-10** | Predeclared `TailMetricPolicy` | tail/sample sufficiency contract | MATERIALIZED |
| **S6-PRE-11** | No model adaptation in S6 | explicit prohibition | MATERIALIZED |
| **S6-PRE-12** | Functional quality gate | 100% statement/branch coverage + engineering checks | MATERIALIZED |
| **S6-PRE-13** | Security/side-effect gate | no dynamic exec/deserialization/network/subprocess | MATERIALIZED |
| **S6-PRE-14** | Final Entry Gate evidence reconciliation | final head + final runs recorded | MATERIALIZED |
| **S6-PRE-15** | Exact-head remediation CI/upstream | PR #82 head `485b70af...`; runs `35533162875`, `35533162868`, `35533162885` PASS | PASS |
| **S6-PRE-16** | Independent re-audit | review `5261545806` on exact PR head `485b70af...` | PASS |

## 3. Functional positive capabilities required after future explicit authorization

These are requirements, not current implementation claims.

| ID | Required capability | Governing source | Entry status |
|---|---|---|---|
| **S6-AC-01** | Immutable `RegimeDefinition` contract | 0E-C; DD-89 | NOT_IMPLEMENTED |
| **S6-AC-02** | Point-in-time causal regime assignment | C-HQI-16; QPI-02 | NOT_IMPLEMENTED |
| **S6-AC-03** | Development-only learned-threshold fitting | S6-D-04 | NOT_IMPLEMENTED |
| **S6-AC-04** | Retrospective regime analysis exploratory-only | C-HQI-15; QPI-04 | NOT_IMPLEMENTED |
| **S6-AC-05** | Regime-definition digest/provenance | S6-D-15 | NOT_IMPLEMENTED |
| **S6-AC-06** | Explicit UNKNOWN regime state | QPI-11 | NOT_IMPLEMENTED |
| **S6-AC-07** | Explicit `RegimeUseMode` | S6-D-21 | NOT_IMPLEMENTED |
| **S6-AC-08** | Verified immutable `ScenarioInputBoundary` with mandatory evaluation role/role provenance | S6-D-17 | NOT_IMPLEMENTED |
| **S6-AC-09** | Protected-evidence integration with existing `EvaluationHistory` plus scenario research history | S6-D-18; QPI-04 | NOT_IMPLEMENTED |
| **S6-AC-10** | Same-boundary protected reuse rejection | S6-D-18 | NOT_IMPLEMENTED |
| **S6-AC-11** | Neutral `ModelEvidenceSnapshot` | S6-D-19 | NOT_IMPLEMENTED |
| **S6-AC-12** | Deterministic `ScenarioSpec` | 0E-E; S6-D-06 | NOT_IMPLEMENTED |
| **S6-AC-13** | Finite canonical `ScenarioGrid` | DD-108; QPI-04 | NOT_IMPLEMENTED |
| **S6-AC-14** | Scenario predeclaration evidence | E-HQI-38 | NOT_IMPLEMENTED |
| **S6-AC-15** | Internally consistent multi-variable stress | E-HQI-51 | NOT_IMPLEMENTED |
| **S6-AC-16** | Stress separated from probability forecast | E-HQI-39 | NOT_IMPLEMENTED |
| **S6-AC-17** | Sprint 3 delegated fee/slippage/latency/spread stress | S6-D-23 | NOT_IMPLEMENTED |
| **S6-AC-18** | Action/replay identity preservation under stress | S6-D-24 | NOT_IMPLEMENTED |
| **S6-AC-19** | Baseline/stressed manifest lineage | S6-D-23 | NOT_IMPLEMENTED |
| **S6-AC-20** | Regime-conditioned evaluation summaries | PR-0E-C-05 | NOT_IMPLEMENTED |
| **S6-AC-21** | Immutable `ObservedSeries` | S6-D-25 | NOT_IMPLEMENTED |
| **S6-AC-22** | `ScenarioOutcomeSet` distinct from observed distribution | S6-D-20 | NOT_IMPLEMENTED |
| **S6-AC-23** | Governed empirical distribution summary | 0E-E; S6-D-11 | NOT_IMPLEMENTED |
| **S6-AC-24** | Predeclared `TailMetricPolicy` | S6-D-26 | NOT_IMPLEMENTED |
| **S6-AC-25** | Sample/tail sufficiency diagnostics | E-HQI-20 | NOT_IMPLEMENTED |
| **S6-AC-26** | Observed extreme-tail preservation | E-HQI-40 | NOT_IMPLEMENTED |
| **S6-AC-27** | Path metrics guarded by order/time/denominator semantics | S6-D-25 | NOT_IMPLEMENTED |
| **S6-AC-28** | Predeclared `ScenarioDispositionPolicy` using canonical 0E-F dispositions | S6-D-22 | NOT_IMPLEMENTED |
| **S6-AC-29** | Separate governed robustness characterization (`ROBUST_WITHIN_DECLARED_SCOPE`/`FRAGILE`/`MIXED`) | S6-D-22 | NOT_IMPLEMENTED |
| **S6-AC-30** | Non-compensatory `INVALID` disposition | QPI-10; S6-D-22 | NOT_IMPLEMENTED |
| **S6-AC-31** | `INCONCLUSIVE` on insufficient required evidence | QPI-11; E-HQI-53 | NOT_IMPLEMENTED |
| **S6-AC-32** | Complete scenario/regime/policy search history | QPI-04 | NOT_IMPLEMENTED |
| **S6-AC-33** | Experimental parity checks | QPI-01 | NOT_IMPLEMENTED |
| **S6-AC-34** | Deterministic repeated-run equivalence | S6-D-10 | NOT_IMPLEMENTED |
| **S6-AC-35** | Scenario/regime provenance manifest | S6-D-15 | NOT_IMPLEMENTED |
| **S6-AC-36** | Dedicated S6 boundary verifier | program governance | NOT_IMPLEMENTED |
| **S6-AC-37** | Adversarial causal/post-hoc tests | 0E-C | NOT_IMPLEMENTED |
| **S6-AC-38** | Adversarial protected-evidence tests | S6-D-18 | NOT_IMPLEMENTED |
| **S6-AC-39** | Adversarial stress/probability tests | 0E-E | NOT_IMPLEMENTED |
| **S6-AC-40** | Adversarial observed-vs-synthetic distribution tests | S6-D-20 | NOT_IMPLEMENTED |
| **S6-AC-41** | Adversarial path/tail sufficiency tests | S6-D-25/26 | NOT_IMPLEMENTED |
| **S6-AC-42** | S6 package 100% statement coverage | S6-D-28 | NOT_IMPLEMENTED |
| **S6-AC-43** | S6 package 100% branch coverage | S6-D-28 | NOT_IMPLEMENTED |
| **S6-AC-44** | Ruff + strict mypy + compile + dependency audit | S6-D-28 | NOT_IMPLEMENTED |
| **S6-AC-45** | Full S1-S5 regression preservation | program governance | NOT_IMPLEMENTED |
| **S6-AC-46** | Exact-head CI / pinned upstream evidence | program governance | NOT_IMPLEMENTED |
| **S6-AC-47** | Security surface scanner | S6-D-29 | NOT_IMPLEMENTED |
| **S6-AC-48** | Zero additional recurring cost | project constraint | NOT_IMPLEMENTED |

## 4. Negative capabilities that must remain absent

| ID | Prohibited capability | Required state |
|---|---|---|
| **S6-NC-01** | Strategy operational path | ABSENT |
| **S6-NC-02** | Signal operational path | ABSENT |
| **S6-NC-03** | StrategyDecision / TradeIntent generation | ABSENT |
| **S6-NC-04** | RiskDecision / RiskAuthorization | ABSENT |
| **S6-NC-05** | Position sizing / capital allocation authority | ABSENT |
| **S6-NC-06** | Operational risk/daily-loss limits | ABSENT |
| **S6-NC-07** | OrderIntent / OrderPlan / ExecutionOrder | ABSENT |
| **S6-NC-08** | Broker account/order capability | ABSENT |
| **S6-NC-09** | Paper / Live Trading | ABSENT |
| **S6-NC-10** | Real money / economic commitment | ABSENT |
| **S6-NC-11** | FinancialLedger mutation | ABSENT |
| **S6-NC-12** | Automatic Strategy/Paper/Live promotion | ABSENT |
| **S6-NC-13** | Post-hoc regime confirmatory rescue | ABSENT |
| **S6-NC-14** | Future information in causal regime assignment | ABSENT |
| **S6-NC-15** | Claim of strategy regime-use without upstream proof | ABSENT |
| **S6-NC-16** | Adaptive scenario/regime/policy search on protected evidence | ABSENT |
| **S6-NC-17** | Same protected boundary reused after protected-informed adaptation | ABSENT |
| **S6-NC-18** | Synthetic stress probability without governed evidence | ABSENT |
| **S6-NC-19** | Scenario outcomes treated as empirical frequencies | ABSENT |
| **S6-NC-20** | VaR/ES/probability-of-loss over synthetic `ScenarioOutcomeSet` | ABSENT |
| **S6-NC-21** | Monte Carlo / bootstrap / stochastic scenario generation | ABSENT |
| **S6-NC-22** | Adaptive clustering as causal confirmatory evidence | ABSENT |
| **S6-NC-23** | UNKNOWN converted to favorable value | ABSENT |
| **S6-NC-24** | Real observed tail events discarded to improve metrics | ABSENT |
| **S6-NC-25** | Tail metric converted to Risk limit | ABSENT |
| **S6-NC-26** | Time-underwater/recovery duration without timestamps | ABSENT |
| **S6-NC-27** | Drawdown ratio without valid positive denominator | ABSENT |
| **S6-NC-28** | Scenario Engine action creation/deletion/reordering/mutation | ABSENT |
| **S6-NC-29** | Scenario Engine reimplementation of fills/accounting/P&L | ABSENT |
| **S6-NC-30** | Direct S6-core runtime import of `btg_ai_trader.ml_engine` | ABSENT |
| **S6-NC-31** | ML retraining/feature selection/hyperparameter/candidate selection | ABSENT |
| **S6-NC-32** | Model estimator loading/deserialization in S6 core | ABSENT |
| **S6-NC-33** | Unsafe pickle/joblib deserialization | ABSENT |
| **S6-NC-34** | Dynamic eval/exec or untrusted dynamic imports | ABSENT |
| **S6-NC-35** | Network clients in S6 core | ABSENT |
| **S6-NC-36** | Subprocess spawning in S6 core | ABSENT |
| **S6-NC-37** | Paid external scenario/risk service | ABSENT |
| **S6-NC-38** | New mandatory runtime dependency | ABSENT |
| **S6-NC-39** | Functional Scenario Engine implementation before human authorization | ABSENT |
