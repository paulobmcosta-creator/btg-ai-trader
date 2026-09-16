# Sprint 2 Capability Matrix

## Positive capabilities

| ID | Capability | Verification |
|---|---|---|
| S2-AC-01 | Dataset/capture boundary validation | unit/property tests reject incomplete or incompatible input identity |
| S2-AC-02 | Lossless market-data normalization | tests preserve temporal fields, missingness and source facts |
| S2-AC-03 | Causal lane partitioning | mixed provider/capture scopes fail closed |
| S2-AC-04 | Immutable replay schedule | mutation attempts fail; input order retained |
| S2-AC-05 | Inclusive knowledge cutoff | before/at/after boundary tests |
| S2-AC-06 | Monotonic virtual clock | backward movement rejected without state advance |
| S2-AC-07 | Exact logical replay speed | rational 1x/2x/0.5x and arbitrary positive ratios |
| S2-AC-08 | Replay input provenance | manifest binds source identities, hashes when available, code/config identity |
| S2-AC-09 | Replay lineage | every output identity traceable to accepted input evidence |
| S2-AC-10 | Data-quality evidence | anomalies reported without silent repair |
| S2-AC-11 | Schema upcast | conditional; required only after multiple schema versions are consumed |
| S2-AC-12 | Deterministic replay | repeated accepted input yields identical ordered logical outputs |
| S2-AC-13 | Persisted research dataset | conditional; blocked pending DD-82/83 completion |
| S2-AC-14 | External historical-data ingestion | conditional; blocked pending DD-77 |

## Negative capabilities

| ID | Prohibition | Enforcement evidence |
|---|---|---|
| S2-NC-01 | Strategy operational path | S2 boundary AST/name scan + review |
| S2-NC-02 | Signal/trade intent path | boundary scan |
| S2-NC-03 | Risk authorization path | boundary scan |
| S2-NC-04 | Paper execution | boundary scan |
| S2-NC-05 | Live execution | boundary scan |
| S2-NC-06 | Broker order/account API | import/name scan; no credentials |
| S2-NC-07 | Financial Ledger mutation | boundary scan |
| S2-NC-08 | P&L/economic backtest | prohibited capability names/namespace review |
| S2-NC-09 | Spread/fees/slippage/fill economics | prohibited capability scan |
| S2-NC-10 | Predictive ML operational wiring | prohibited imports/names in S2 runtime |
| S2-NC-11 | Real-money authority | no execution/account path |
| S2-NC-12 | Source-evidence mutation | immutable inputs + tests |
| S2-NC-13 | Fabricated temporal evidence | tests reject unknown/naive required knowledge time |
| S2-NC-14 | Synthetic cross-lane ordering | mixed-lane tests fail closed |
| S2-NC-15 | Silent missing-data imputation | normalization tests preserve missingness |
| S2-NC-16 | Wall-clock causal semantics | S2 boundary rejects `sleep`, `datetime.now`, `time.time` in S2 replay/data modules |

## Gate interpretation

A positive capability marked `REQUIRED_IF_TRIGGERED` may remain absent if its trigger is not activated. A negative capability is conjunctive: one violation blocks the affected Sprint 2 increment.

The capability matrix does not authorize any Sprint 3 economic simulation or later financial capability.