# Sprint 6 Capability Matrix — Scenario Engine

## 1. Entry-gate capabilities

| ID | Capability | Evidence | Status |
|---|---|---|---|
| **S6-EG-AC-01** | Exact closed Sprint 5 baseline | final head `9956f3a...` | PASS |
| **S6-EG-AC-02** | Tracking issue | Issue #79 | PASS |
| **S6-EG-AC-03** | Entry Contract | `S6_ENTRY_CONTRACT.md` | PASS |
| **S6-EG-AC-04** | Decision Register | `S6_DECISION_REGISTER.md` | PASS |
| **S6-EG-AC-05** | Capability Matrix | this document | PASS |
| **S6-EG-AC-06** | DD-89 adjudicated | S6 Decision Register | PASS |
| **S6-EG-AC-07** | Functional implementation remains unauthorized | S6 gate documents | PASS |
| **S6-EG-AC-08** | Zero additional recurring cost | no dependency change | PASS |

## 2. Functional positive capabilities required after a future explicit authorization

These are requirements, not current implementation claims.

| ID | Required capability | Governing source | Entry status |
|---|---|---|---|
| **S6-AC-01** | Immutable regime-definition contract | 0E-C; DD-89 | NOT_IMPLEMENTED |
| **S6-AC-02** | Point-in-time causal regime assignment | C-HQI-16; QPI-02 | NOT_IMPLEMENTED |
| **S6-AC-03** | Development-only learned-threshold fitting | 0E-C; S6-D-04 | NOT_IMPLEMENTED |
| **S6-AC-04** | Retrospective analysis explicitly exploratory | C-HQI-15; QPI-04 | NOT_IMPLEMENTED |
| **S6-AC-05** | Regime-definition digest/provenance | S6-D-15 | NOT_IMPLEMENTED |
| **S6-AC-06** | Explicit UNKNOWN regime state | QPI-11 | NOT_IMPLEMENTED |
| **S6-AC-07** | Deterministic scenario specification | 0E-E | NOT_IMPLEMENTED |
| **S6-AC-08** | Finite canonical scenario grid | DD-108; QPI-04 | NOT_IMPLEMENTED |
| **S6-AC-09** | Scenario predeclaration evidence | E-HQI-38 | NOT_IMPLEMENTED |
| **S6-AC-10** | Internally consistent multi-variable stress | E-HQI-51 | NOT_IMPLEMENTED |
| **S6-AC-11** | Stress separated from probability forecast | E-HQI-39 | NOT_IMPLEMENTED |
| **S6-AC-12** | Cost/friction stress when upstream evidence supports it | 0E-D; 0E-E | NOT_IMPLEMENTED |
| **S6-AC-13** | Execution-assumption stress when supported | 0E-D; 0E-E | NOT_IMPLEMENTED |
| **S6-AC-14** | Regime-conditioned summaries | PR-0E-C-05; 0E-F | NOT_IMPLEMENTED |
| **S6-AC-15** | Empirical distribution summary | PR-0E-E-02 | NOT_IMPLEMENTED |
| **S6-AC-16** | Downside/tail diagnostics | 0E-E | NOT_IMPLEMENTED |
| **S6-AC-17** | Path/drawdown diagnostics | 0E-E | NOT_IMPLEMENTED |
| **S6-AC-18** | Tail false-precision safeguard | E-HQI-20 | NOT_IMPLEMENTED |
| **S6-AC-19** | Preserve observed extreme-tail events | E-HQI-40 | NOT_IMPLEMENTED |
| **S6-AC-20** | Complete scenario/regime search history | QPI-04 | NOT_IMPLEMENTED |
| **S6-AC-21** | Experimental parity for comparisons | QPI-01; 0E-C | NOT_IMPLEMENTED |
| **S6-AC-22** | Deterministic repeated-run equivalence | S6-D-10 | NOT_IMPLEMENTED |
| **S6-AC-23** | Scenario/regime provenance manifest | S6-D-15 | NOT_IMPLEMENTED |
| **S6-AC-24** | Research-only evaluation disposition | 0E-F | NOT_IMPLEMENTED |
| **S6-AC-25** | Dedicated S6 boundary verifier | program governance | NOT_IMPLEMENTED |
| **S6-AC-26** | Adversarial causal/post-hoc tests | 0E-C | NOT_IMPLEMENTED |
| **S6-AC-27** | Adversarial stress/probability tests | 0E-E | NOT_IMPLEMENTED |
| **S6-AC-28** | Full S1-S5 regression | program governance | NOT_IMPLEMENTED |
| **S6-AC-29** | Exact-head CI / upstream evidence | program governance | NOT_IMPLEMENTED |
| **S6-AC-30** | Zero additional recurring cost | project constraint | NOT_IMPLEMENTED |

## 3. Negative capabilities that must remain absent

| ID | Prohibited capability | Entry state |
|---|---|---|
| **S6-NC-01** | Strategy operational path | ABSENT |
| **S6-NC-02** | Signal operational path | ABSENT |
| **S6-NC-03** | StrategyDecision generation | ABSENT |
| **S6-NC-04** | TradeIntent generation | ABSENT |
| **S6-NC-05** | Risk operational path | ABSENT |
| **S6-NC-06** | RiskDecision / RiskAuthorization | ABSENT |
| **S6-NC-07** | Position sizing / capital allocation authority | ABSENT |
| **S6-NC-08** | Operational risk / daily-loss limits | ABSENT |
| **S6-NC-09** | OrderIntent / OrderPlan / ExecutionOrder | ABSENT |
| **S6-NC-10** | Broker account/order capability | ABSENT |
| **S6-NC-11** | Paper Trading | ABSENT |
| **S6-NC-12** | Live Trading | ABSENT |
| **S6-NC-13** | Real money | ABSENT |
| **S6-NC-14** | FinancialLedger mutation | ABSENT |
| **S6-NC-15** | External economic commitment | ABSENT |
| **S6-NC-16** | Automatic Strategy/Paper/Live promotion | ABSENT |
| **S6-NC-17** | Post-hoc regime used as confirmatory rescue | ABSENT |
| **S6-NC-18** | Future information in causal regime assignment | ABSENT |
| **S6-NC-19** | Adaptive scenario search on protected evidence | ABSENT |
| **S6-NC-20** | Synthetic stress probability without governed evidence | ABSENT |
| **S6-NC-21** | Monte Carlo engine in initial S6 | ABSENT |
| **S6-NC-22** | Bootstrap inference in initial S6 | ABSENT |
| **S6-NC-23** | Random/entropy-driven scenario generation | ABSENT |
| **S6-NC-24** | Favorable random-path selection | ABSENT |
| **S6-NC-25** | Adaptive clustering promoted as causal without independent evidence | ABSENT |
| **S6-NC-26** | UNKNOWN converted to favorable value | ABSENT |
| **S6-NC-27** | Real tail events discarded to improve metrics | ABSENT |
| **S6-NC-28** | VaR/ES descriptive metric converted to Risk limit | ABSENT |
| **S6-NC-29** | Single-metric scenario merit | ABSENT |
| **S6-NC-30** | Paid external scenario/risk service | ABSENT |
| **S6-NC-31** | New mandatory runtime dependency at entry gate | ABSENT |
| **S6-NC-32** | Functional `src/btg_ai_trader/scenario_engine` code in gate PR | ABSENT |
| **S6-NC-33** | Functional S6 implementation before human authorization | ABSENT |
