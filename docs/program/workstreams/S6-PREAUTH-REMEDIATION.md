# S6-PREAUTH-REMEDIATION — Functional Contract Hardening

```text
SPRINT = 6
WORK_MODE = PREAUTH_REMEDIATION_ONLY
ISSUE = #81
CANONICAL_BRANCH = sprint/6-scenario-engine
WORK_BRANCH = s6/01-preauth-remediation
BASE_SHA = 616849f8e77ecf3624b2b9362c1ef42c7fb9bcc1

ENTRY_GATE = PASS
FUNCTIONAL_IMPLEMENTATION = FORBIDDEN
SRC_SCENARIO_ENGINE = MUST_NOT_EXIST_IN_THIS_PR
TEST_SCENARIO_ENGINE = MUST_NOT_EXIST_IN_THIS_PR
PYPROJECT_CHANGE = FORBIDDEN
NEW_RUNTIME_DEPENDENCIES = FORBIDDEN
MERGE = FORBIDDEN_WITHOUT_HUMAN_AUTHORIZATION
```

## 1. Purpose

Close the eight pre-authorization findings identified after the canonical Sprint 6 Entry Gate without implementing Scenario Engine functionality.

## 2. Required remediation findings

### R1 — Protected evidence
Materialize inherited S4/S5 evaluation-role semantics, append-only research history and rejection of same-boundary confirmatory reuse after protected-informed adaptation.

### R2 — Input boundary
Materialize an immutable `ScenarioInputBoundary` binding upstream scientific identity, lineage, evaluation/protected role, numeric policy, code revision and digest.

### R3 — Synthetic vs empirical distributions
Materialize `ScenarioOutcomeSet != ObservedDistributionSummary`; synthetic scenario counts/weights are not empirical probabilities or VaR/ES samples.

### R4 — Regime-use semantics
Materialize `CAUSAL_STRATIFICATION`, `STRATEGY_BOUND` and `RETROSPECTIVE_EXPLORATORY`, requiring upstream proof for `STRATEGY_BOUND`.

### R5 — Disposition policy
Materialize a predeclared immutable `ScenarioDispositionPolicy`; prohibit post-result robustness labeling and universal compensatory scores.

### R6 — Sprint 3 delegation
Require execution-economic stresses to reuse Sprint 3. Preserve action sequence and replay boundary; do not reimplement fills/accounting/P&L.

### R7 — Series/tail/path semantics
Materialize `ObservedSeries` and `TailMetricPolicy`; require timestamps for duration metrics and valid denominator/capital convention for ratios.

### R8 — Engineering/security acceptance
Require 100% statement and branch coverage of the future S6 package, full regression, Ruff, strict mypy, compile, dependency audit, boundary/security scanners, exact-head CI and pinned upstream. Prohibit dynamic execution, unsafe model deserialization, network/subprocess and model adaptation.

## 3. Additional reconciliation

The Entry Gate historical merge SHA and final canonical head are distinct and must both remain visible:

```text
ENTRY_GATE_MERGE_SHA = d74e632f47fafab9f441574acbacb3ae7f1a7a72
ENTRY_GATE_FINAL_CANONICAL_HEAD = 616849f8e77ecf3624b2b9362c1ef42c7fb9bcc1
ENTRY_GATE_FINAL_CI_RUN = 35474371811
ENTRY_GATE_FINAL_UPSTREAM_RUN = 35474371852
```

## 4. Authorized file surface

This remediation may modify only:

- S6 governance/program documentation;
- living program/agent/master-plan documentation;
- S6 governance CI/workflow triggers required to validate this remediation.

It may not modify:

- `src/`;
- `tests/`;
- `pyproject.toml`;
- Foundation snapshots/protocols;
- Sprint 1–5 functional code.

## 5. Exact-head validation requirements

The remediation PR must prove:

- required remediation tokens/artifacts are present;
- `src/`, `tests/`, `pyproject.toml` unchanged from `616849f8...`;
- no `src/btg_ai_trader/scenario_engine` exists;
- Foundation verifier PASS;
- `git diff --check` PASS;
- pinned upstream PASS;
- independent review PASS.

## 6. Stop conditions

```text
REMEDIATION_EXACT_HEAD_VALIDATION = REQUIRED
INDEPENDENT_REAUDIT = REQUIRED
MERGE_AUTHORIZED = NO
SPRINT_6_FUNCTIONAL_IMPLEMENTATION = NOT_AUTHORIZED
```

A successful remediation does not authorize functional implementation.
