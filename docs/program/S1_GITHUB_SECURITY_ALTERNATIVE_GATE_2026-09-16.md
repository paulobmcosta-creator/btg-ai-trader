# Sprint 1 — GitHub-Native Security Alternative Gate

**Date:** 2026-09-16  
**Scope:** Sprint 1 — Market Observer  
**Authority:** explicit human coordination decision  
**Frozen Foundation artifacts changed:** NO

## 1. Purpose

This record formalizes the human decision to use the repository's GitHub-native security assurance package as the final Sprint 1 security gate in place of the unavailable Official Codex Security Diff Scan.

This decision does **not** state or imply that the Official Codex Security Diff Scan executed. Its status remains permanently recorded as `NOT_EXECUTED` for this Sprint 1 closure.

The substitution is an acceptance-evidence decision, not a rewrite of `docs/foundation/0F-E_sprint1_entry_contract.md`. The immutable 0F-E contract requires physical proof of negative capabilities, static inspection, configuration/credential auditing, repository inspection and a formal gate record; it does not require one exclusive branded scanner as the only admissible instrument.

## 2. Human adjudication

```text
OFFICIAL_CODEX_SECURITY_DIFF_SCAN = NOT_EXECUTED
OFFICIAL_CODEX_SECURITY_DIFF_SCAN_REQUIRED_FOR_S1 = WAIVED_BY_EXPLICIT_HUMAN_DECISION
SECURITY_ASSURANCE_REPLACEMENT = GITHUB_NATIVE_SECURITY_PACKAGE
SECURITY_ASSURANCE_REPLACEMENT_STATUS = ACCEPTED
NO_WEAKENING_OF_0F_E = REQUIRED
NO_NEGATIVE_CAPABILITY_WAIVER = TRUE
```

The security substitution applies only to the evidence instrument. It does not waive any 0F-E negative capability, RQM, HQI/QPI, `READ_ONLY_BY_CONSTRUCTION`, `STRUCTURAL_ESCALATION`, or exit criterion.

## 3. Evidence package

### 3.1. Exact integrated Sprint 1 baseline before this final documentary reconciliation

```text
SPRINT_BRANCH = sprint/1-market-observer
INTEGRATED_HEAD = 6457ae1dfec6e91034741e57c6343397f368cbc2
MERGE_SOURCE = PR #59
```

The merge contains the successful XP/MT5 runtime-evidence reconciliation and no additional functional capability beyond the reviewed Sprint 1 tree.

### 3.2. Exact-head GitHub Actions evidence

GitHub Actions run `35126543429`, triggered by push of exact integrated head `6457ae1dfec6e91034741e57c6343397f368cbc2`, completed successfully.

Required jobs on that exact head:

```text
tests          = PASS
lint           = PASS
types          = PASS
compile        = PASS
dependencies   = PASS
foundation     = PASS
boundary       = PASS
diff           = PASS
```

The `boundary` job executed the scoped Sprint 1 boundary, configuration and possible-secret heuristics. The test suite includes the negative-capability tests and the integrated Observer/runtime tests.

### 3.3. PR #59 GitHub security review

PR #59 received an explicit GitHub review anchored to the exact reconciliation diff. The recorded result was:

```text
MANUAL_GITHUB_SECURITY_REVIEW = PASS
BLOCKING_FINDINGS = 0
NON_BLOCKING_FINDINGS = 0
```

That review correctly stated that it was **not** the Official Codex Security Diff Scan. This gate preserves that distinction.

### 3.4. Structural negative-capability evidence

The accepted Sprint 1 tree preserves all of the following:

```text
TRUSTED_PYTHON_IMPORTS_METATRADER5 = NO
PYTHON_ACCOUNT_API = ABSENT
PYTHON_ORDER_API = ABSENT
ORDER_SUBMISSION = IMPOSSIBLE
ORDER_MODIFICATION = IMPOSSIBLE
ORDER_CANCELLATION = IMPOSSIBLE
PAPER_PATH = ABSENT
LIVE_TRADING_PATH = ABSENT
REAL_MONEY_AUTHORITY = ABSENT
ECONOMIC_COMMITMENT = IMPOSSIBLE
FINANCIAL_LEDGER_MUTATION = ABSENT
```

The real XP/MT5 path is one-way: Investor/read-only terminal -> custom MQL5 indicator -> append-only `FILE_COMMON` transport -> trusted Python readers/harness.

## 4. Mapping to 0F-E evidence taxonomy

The GitHub-native package is accepted as the combined evidence instrument for the following 0F-E evidence classes:

| 0F-E evidence class | GitHub-native evidence |
|---|---|
| `EVID-TEST-NEG` | NEG-CAP/runtime tests in GitHub Actions |
| `EVID-STAT-AST` | Sprint 1 boundary/static inspection job |
| `EVID-STAT-TYPE` | mypy/types job |
| `EVID-CONF-SCAN` | boundary/config inspection |
| `EVID-CRED-AUD` | possible-secret heuristics plus repository security review and public-history secret-scanner controls |
| `EVID-REPO-INSP` | exact SHA checkout, Foundation integrity and diff jobs |
| `EVID-GATE-REC` | this formal gate record plus explicit human decision |

No evidence class is removed. The instrument set changes because the previously planned Official Codex scanner is unavailable.

## 5. Security gate verdict

```text
GITHUB_NATIVE_SECURITY_GATE = PASS
OFFICIAL_CODEX_SECURITY_DIFF_SCAN = NOT_EXECUTED
SECURITY_FINDINGS_REQUIRING_REMEDIATION = 0
READ_ONLY_BY_CONSTRUCTION = PASS
STRUCTURAL_ESCALATION = PASS
NEG_CAP_01_TO_10 = PASS
RQM_018_SECURITY_EVIDENCE = SATISFIED_BY_ACCEPTED_ALTERNATIVE
RQM_036_SECURITY_EVIDENCE = SATISFIED_BY_ACCEPTED_ALTERNATIVE
```

This verdict is valid only if the final documentary acceptance tree continues to pass the same exact-tree CI/Foundation/boundary/NEG-CAP checks. Any later functional change reopens the applicable security evidence requirement.

## 6. Explicit non-authorizations

This gate does not authorize:

- strategy operation;
- ML production wiring;
- Risk authorization;
- Paper execution;
- broker order APIs;
- master/trading credentials;
- financial-ledger mutation;
- live trading;
- real-money operation.

Those capabilities remain governed by later sprints and their own gates.