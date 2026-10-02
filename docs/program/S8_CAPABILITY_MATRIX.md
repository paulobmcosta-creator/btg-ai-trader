# Sprint 8 Capability Matrix — Paper Trader

## 1. Entry-gate capabilities

| ID | Capability / prerequisite | Evidence | Status |
|---|---|---|---|
| **S8-EG-AC-01** | Sprint 7 formally closed/PASS | S7 final acceptance | PASS |
| **S8-EG-AC-02** | Exact audited S7 Risk baseline retained | \`e379e9b34a8b607e86165bd3336d23fcd9406259\` | PASS |
| **S8-EG-AC-03** | S8 isolated canonical/work branches and issue | Issue #93; \`sprint/8-paper-trader\`; \`s8/00-entry-gate\` | PASS |
| **S8-EG-AC-04** | Protocol 0E-G is binding | Entry Contract | PASS |
| **S8-EG-AC-05** | Paper explicitly prospective/non-funded | 0E-G; S8-D-01 | PASS |
| **S8-EG-AC-06** | Risk bypass structurally forbidden by contract | S8-D-04 | PASS |
| **S8-EG-AC-07** | AuthorizationAllocation boundary recognized | ADR 0016; S8-D-05 | PASS |
| **S8-EG-AC-08** | Canonical FinancialLedger separated from Paper accounting | ADR 0022; S8-D-06 | PASS |
| **S8-EG-AC-09** | Material changes reset confirmatory evidence lineage | 0E-G; S8-D-09 | PASS |
| **S8-EG-AC-10** | Paper discrepancies preserved as evidence | 0E-G; S8-D-10 | PASS |
| **S8-EG-AC-11** | PaperGateAssessment required | PR-0E-G-04; S8-D-12 | PASS |
| **S8-EG-AC-12** | Operational Signal/Strategy runtime path exists | canonical source tree | **FAIL — S8-B01** |
| **S8-EG-AC-13** | Runtime \`StrategyDecision\` and \`TradeIntent\` contracts exist | canonical source tree | **FAIL — S8-B01** |
| **S8-EG-AC-14** | Exact candidate has canonical \`PAPER_ELIGIBLE\` adjudication | canonical evidence | **FAIL — S8-B02** |
| **S8-EG-AC-15** | Exact candidate is frozen before confirmatory Paper | canonical evidence | **FAIL — S8-B02** |
| **S8-EG-AC-16** | Candidate-specific DD-115/116/117/119 policies predeclared | requires candidate freeze | BLOCKED_BY_S8-B02 |
| **S8-EG-AC-17** | No functional S8 source/test delta in Entry Gate | exact diff | PASS |
| **S8-EG-AC-18** | No runtime dependency delta in Entry Gate | exact diff | PASS |
| **S8-EG-AC-19** | Zero additional recurring cost at Entry Gate | repository diff | PASS |
| **S8-EG-AC-20** | Live/real-money/broker-order capability absent | boundary contract | PASS |

## 2. Functional positive capabilities required after future blocker remediation and explicit authorization

| ID | Required future capability | State |
|---|---|---|
| **S8-AC-01** | Consume contemporaneous admitted market evidence only | REQUIRED_NOT_AUTHORIZED |
| **S8-AC-02** | Execute exact frozen Strategy candidate | REQUIRED_NOT_AUTHORIZED |
| **S8-AC-03** | Emit/retain \`NO_TRADE\` and \`PROPOSE_TRADE\` decisions | REQUIRED_NOT_AUTHORIZED |
| **S8-AC-04** | Materialized immutable \`TradeIntent\` lineage | REQUIRED_NOT_AUTHORIZED |
| **S8-AC-05** | Invoke canonical S7 Risk for every proposed economic change | REQUIRED_NOT_AUTHORIZED |
| **S8-AC-06** | Revalidate \`RiskAuthorization\` at allocation time | REQUIRED_NOT_AUTHORIZED |
| **S8-AC-07** | Atomic bounded \`AuthorizationAllocation\` | REQUIRED_NOT_AUTHORIZED |
| **S8-AC-08** | Prevent aggregate risk-capacity double-spend | REQUIRED_NOT_AUTHORIZED |
| **S8-AC-09** | Broker-neutral \`OrderIntent\` | REQUIRED_NOT_AUTHORIZED |
| **S8-AC-10** | Predeclared \`OrderPlan\` compatible with exact candidate | REQUIRED_NOT_AUTHORIZED |
| **S8-AC-11** | Deterministic/non-funded Paper execution model using contemporaneous observable inputs | REQUIRED_NOT_AUTHORIZED |
| **S8-AC-12** | Explicit fictional Paper position/cash/P&L projections | REQUIRED_NOT_AUTHORIZED |
| **S8-AC-13** | Append-only Paper evidence and provenance | REQUIRED_NOT_AUTHORIZED |
| **S8-AC-14** | All decisions including \`NO_TRADE\` captured | REQUIRED_NOT_AUTHORIZED |
| **S8-AC-15** | Backtest↔Paper structural/distributional comparison | REQUIRED_NOT_AUTHORIZED |
| **S8-AC-16** | Material discrepancy preservation | REQUIRED_NOT_AUTHORIZED |
| **S8-AC-17** | Critical-error evidence and safe interruption | REQUIRED_NOT_AUTHORIZED |
| **S8-AC-18** | Candidate-specific stopping rules | REQUIRED_NOT_AUTHORIZED |
| **S8-AC-19** | Candidate-specific information-sufficiency policy | REQUIRED_NOT_AUTHORIZED |
| **S8-AC-20** | Candidate-specific latency/slippage/discrepancy policies | REQUIRED_NOT_AUTHORIZED |
| **S8-AC-21** | Material adaptation closes current evidence partition | REQUIRED_NOT_AUTHORIZED |
| **S8-AC-22** | Final provenance-bound \`PaperGateAssessment\` | REQUIRED_NOT_AUTHORIZED |
| **S8-AC-23** | Full regression and S8-specific adversarial tests | REQUIRED_NOT_AUTHORIZED |
| **S8-AC-24** | Dedicated S8 negative-capability/broker-side-effect boundary verifier | REQUIRED_NOT_AUTHORIZED |
| **S8-AC-25** | Zero additional recurring cost | REQUIRED_NOT_AUTHORIZED |

## 3. Negative capabilities that must remain absent

| ID | Prohibited capability | Required state |
|---|---|---|
| **S8-NC-01** | Real broker/account/order dispatch | ABSENT |
| **S8-NC-02** | \`order_send()\` or equivalent execution call in authorized Paper path | ABSENT |
| **S8-NC-03** | Real-money exposure | ABSENT |
| **S8-NC-04** | Live Trading | ABSENT |
| **S8-NC-05** | Paper bypassing Risk | ABSENT |
| **S8-NC-06** | Paper-local strategy substitute | ABSENT |
| **S8-NC-07** | RiskAuthorization consumed without bounded allocation | ABSENT |
| **S8-NC-08** | Allocation exceeding authorization/capacity | ABSENT |
| **S8-NC-09** | Canonical FinancialLedger mutation | ABSENT |
| **S8-NC-10** | Fictional Paper accounting represented as broker truth | ABSENT |
| **S8-NC-11** | Silent FX conversion | ABSENT |
| **S8-NC-12** | Fabricated broker margin/buying power validation | ABSENT |
| **S8-NC-13** | Material Paper-informed adaptation retained in same confirmatory partition | ABSENT |
| **S8-NC-14** | Discrepancy/history rewriting | ABSENT |
| **S8-NC-15** | Positive P&L as sole Paper PASS criterion | ABSENT |
| **S8-NC-16** | Automatic Live promotion | ABSENT |
| **S8-NC-17** | Paid mandatory external Paper service | ABSENT |
| **S8-NC-18** | Functional S8 implementation before blocker remediation and explicit authorization | ABSENT |

## 4. Entry-gate verdict

\`\`\`text
S8_ENTRY_GATE_CANDIDATE = CHANGES_REQUIRED
OPEN_S8_ENTRY_GATE_BLOCKERS = 2
S8-B01 = OPEN
S8-B02 = OPEN

PROMOTION_TO_S8_FUNCTIONAL_IMPLEMENTATION = NO
S8_FUNCTIONAL_IMPLEMENTATION = NOT_AUTHORIZED
PAPER_CONFIRMATORY_RUN = NOT_AUTHORIZED
LIVE_TRADING = NO
REAL_MONEY = NO
\`\`\`
