# Sprint 6 — Scenario Engine

```text
SPRINT_6_STATUS = ENTRY_GATE_APPROVED
SPRINT_6_LIFECYCLE = FUNCTIONAL_IMPLEMENTATION_IN_PROGRESS
SPRINT_6_CANONICAL_BRANCH = sprint/6-scenario-engine
PREAUTH_REMEDIATION_BRANCH = s6/01-preauth-remediation
PREAUTH_REMEDIATION_ISSUE = #81

S6_ENTRY_GATE = PASS
S6_ENTRY_GATE_CANONICAL = PASS
S6_ENTRY_GATE_MERGE_SHA = d74e632f47fafab9f441574acbacb3ae7f1a7a72
S6_ENTRY_GATE_FINAL_CANONICAL_HEAD = 616849f8e77ecf3624b2b9362c1ef42c7fb9bcc1
S6_ENTRY_GATE_FINAL_CI_RUN = 35474371811
S6_ENTRY_GATE_FINAL_UPSTREAM_RUN = 35474371852

S6_PREAUTH_REMEDIATION = PASS
S6_FUNCTIONAL_IMPLEMENTATION_ISSUE = #83
S6_FUNCTIONAL_WORK_BRANCH = s6/02-full-scenario-engine
SPRINT_6_FUNCTIONAL_IMPLEMENTATION = AUTHORIZED
PROMOTION_TO_S6_FUNCTIONAL_IMPLEMENTATION = NO

FINANCIAL_AUTHORITY = ABSENT
STRATEGY_OPERATIONAL_PATH = ABSENT
RISK_OPERATIONAL_PATH = ABSENT
PAPER_TRADING = FORBIDDEN
LIVE_TRADING = FORBIDDEN
REAL_MONEY = FORBIDDEN
ADDITIONAL_RECURRING_COST = ZERO
```

## 1. Purpose

Sprint 6 is a research-only Scenario Engine stage. The Entry Gate is already canonical PASS, but functional implementation remains behind a separate authorization boundary.

The current task is a controlled pre-authorization remediation of the functional contract. No Scenario Engine functional code is authorized.

## 2. Canonical architecture after remediation

```text
IMMUTABLE UPSTREAM EVIDENCE
        |
        v
ScenarioInputBoundary
        |
        +--> protected-evidence role/history
        |
        +--> RegimeDefinition + RegimeUseMode
        |
        +--> ScenarioSpec + ScenarioGrid
        |
        +--> Sprint-3-delegated economic stress
        |
        +--> ObservedSeries --------------------+
        |                                      |
        |                                      v
        |                         ObservedDistributionSummary
        |
        +--> ScenarioOutcomeSet  !=  empirical distribution
        |
        +--> ScenarioDispositionPolicy
        |
        v
Scenario research result + provenance manifest

NEVER:
Scenario -> StrategyDecision
Scenario -> RiskDecision / RiskAuthorization
Scenario -> OrderIntent / Broker
ScenarioOutcomeSet -> probability/VaR/ES
Protected-informed artifact -> same protected boundary confirmation
```

## 3. Governing separations

- causal regime != retrospective segmentation;
- causal regime availability != proof of actual strategy regime use;
- `CAUSAL_STRATIFICATION != STRATEGY_BOUND`;
- synthetic scenario outcome set != observed empirical distribution;
- stress scenario != probability forecast;
- tail metric != Risk limit;
- scenario robustness != Strategy quality;
- scenario evidence != Paper/Live eligibility;
- deterministic computation != empirical certainty.

## 4. Initial implementation constraints if later authorized

- deterministic threshold-based regime classification only;
- no indicator engineering owned by S6 in the initial scope;
- finite predeclared scenario grids;
- economic/execution stress delegated to Sprint 3;
- no action/replay mutation;
- empirical tail/path analysis only from governed `ObservedSeries`;
- predeclared `TailMetricPolicy` and `ScenarioDispositionPolicy`;
- neutral model-evidence snapshots rather than direct optional-ML runtime coupling;
- no model retraining/selection;
- no Monte Carlo/bootstrap/stochastic scenarios;
- no external network/subprocess/dynamic execution surfaces;
- no new mandatory runtime dependency;
- zero additional recurring cost.

## 5. Governing artifacts

- `docs/program/S6_ENTRY_CONTRACT.md`
- `docs/program/S6_DECISION_REGISTER.md`
- `docs/program/S6_CAPABILITY_MATRIX.md`
- `docs/program/S6_ENTRY_GATE.md`
- `docs/program/workstreams/S6-ENTRY-GATE.md` — historical entry-gate packet
- `docs/program/workstreams/S6-PREAUTH-REMEDIATION.md` — current remediation packet

## 6. Current stop condition

```text
S6_ENTRY_GATE = PASS
S6_PREAUTH_REMEDIATION = PASS
SPRINT_6_FUNCTIONAL_IMPLEMENTATION = AUTHORIZED
FUNCTIONAL_WORK_BRANCH = s6/02-full-scenario-engine
MERGE_AUTHORIZED = NO
```

The remediation contract passed independent re-audit, PR #82 was merged by explicit human authorization, and the merge SHA passed post-merge Entry Gate CI and pinned upstream. Functional implementation was explicitly authorized on 2026-09-22 under Issue #83 and is now in progress on `s6/02-full-scenario-engine`. Merge remains separately unauthorized.
