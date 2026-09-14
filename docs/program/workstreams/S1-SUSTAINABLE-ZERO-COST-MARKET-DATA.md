# Sprint 1 — Sustainable zero-cost realtime market-data direction

## Status

```text
CEDRO_FREE_TRIAL = REJECTED_AS_CANONICAL_LONG_TERM_PROVIDER
CEDRO_HISTORY = PRESERVED_AND_REVERTED
BTG_DATA_SERVICES = HISTORICAL_REFERENCE_IMPLEMENTATION
ZERO_ADDITIONAL_COST = HARD_CONSTRAINT
REALTIME_REQUIREMENT = PRESERVED
CANONICAL_PROVIDER_SELECTION = RICO_SUPPLIED_MT5
PROVIDER_SELECTION_STATUS = ACCEPTED_FOR_QUALIFICATION
REAL_PROVIDER_SESSION = NOT_EXECUTED
SPRINT1_PROVIDER_QUALIFIED = NO
```

Normative decision: ADR-0025.

## Rationale

A time-limited provider trial can prove an integration but cannot serve as the canonical market-data source for a program that must remain usable after development is complete.

B3 D-1/historical sources remain useful for development and replay, but they do not satisfy the frozen Sprint 1 realtime observation/subscription obligations.

The selected qualification path is **Rico-supplied MetaTrader 5 market data**, consumed through a structurally read-only boundary rather than the dual-use MT5 Python trading API.

The selection is based on current public documentation indicating that Rico offers MetaTrader 5 free to clients, with platform contracting exempt from charge. Rico's current platform comparison also records MetaTrader 5 as `GRÁTIS`, with `N/A` for minimum brokerage and `N/A` for exemption by number of contracts/RLP. These commercial statements support provider selection, but they do not count as runtime qualification evidence.

## Selected architecture

```text
Rico / MT5 trade server
    -> MetaTrader 5 terminal
       -> login using INVESTOR / READ-ONLY authorization only
       -> custom MQL5 INDICATOR attached to exact WIN symbol
          -> indicator receives passive tick/price recalculation events
          -> indicator writes bounded append-only market-data records to local transport
             -> BTG AI Trader Python Observer tails/reads transport
                -> RawFrame / admission / evidence / provenance
```

### Why a custom indicator

MetaTrader 5 officially supports Investor mode. In that mode trading is disabled for the connected account and `ACCOUNT_TRADE_ALLOWED` is false.

MQL5 also structurally prohibits trading functions in custom indicators, including `OrderSend`, `OrderCheck`, `OrderCalcMargin` and `OrderCalcProfit`. A custom indicator can emit passive data while the trusted Python runtime never imports `MetaTrader5` and never receives broker-account or order functions.

This is stronger than merely promising not to call `order_send`: the selected bridge program type itself cannot execute those trading functions.

## Rico qualification gate

Selection does **not** mean qualification. Before the provider can satisfy the real-provider obligations of Sprint 1, a controlled runtime session must verify:

1. **Cost** — MetaTrader 5 is activated in the concrete Rico account without additional recurring platform/market-data charge under the account state used for qualification.
2. **WIN discovery** — the current WIN contract is discoverable and resolves to an exact provider symbol.
3. **Realtime ticks** — the terminal receives realtime WIN observations sufficient for AC-05 and AC-07.
4. **Read-only authorization** — Investor/read-only mode is available and the runtime demonstrates that trading is disabled.
5. **Indicator-only bridge** — the bridge runs as a custom MQL5 indicator, not Expert Advisor or script.
6. **No Python trading surface** — the trusted Python process does not import `MetaTrader5`, hold a master password, or expose account/order methods.
7. **Temporal/provenance evidence** — event/source timestamps when available, ingestion time, provider/symbol provenance, heartbeat and latency evidence are persisted according to Sprint 1 contracts.
8. **Sustainability** — no minimum real-money operation is required to retain the specific platform/market-data entitlement used in the qualification.

Until all eight are evidenced:

```text
REAL_PROVIDER_SESSION = NOT_EXECUTED
SPRINT1_PROVIDER_QUALIFIED = NO
SPRINT1_ACCEPTANCE = NO
PROMOTION_TO_SPRINT_2 = NO
```

## Offline implementation boundary

Offline development may proceed before the real Rico session only if it remains provider-safe and does not manufacture qualification evidence.

Allowed offline work:

- define the passive bridge record schema;
- implement parser/admission against fixtures;
- implement bounded append-only transport handling;
- validate malformed/truncated/duplicated/out-of-order fixture handling;
- enforce absence of account/order fields;
- add static tripwires preventing `MetaTrader5` imports in the trusted observer path;
- create the MQL5 custom-indicator skeleton with passive market-data output only.

Not allowed offline:

- mark AC-05/AC-07 realtime as satisfied from fixtures;
- assert Rico WIN availability without real-session evidence;
- use a master/trading password as a convenience path;
- introduce Expert Advisor, script, order API, paper execution or live execution;
- reinterpret delayed or historical data as realtime.

## Free permanent development sources

For development, instrument discovery research and historical/replay work, free D-1/end-of-day sources remain independently useful:

- B3 D-1/end-of-day data where publicly available/licensed;
- brapi futures endpoints where applicable.

These sources MUST NOT be relabeled as realtime Sprint 1 qualification evidence.

## Negative capabilities

The implementation MUST enforce:

```text
TRUSTED_PYTHON_IMPORTS_METATRADER5 = NO
MT5_MASTER_PASSWORD_IN_PROJECT = NO
MT5_MASTER_PASSWORD_IN_CHAT = NO
MT5_MASTER_PASSWORD_IN_SECRET_STORE = NO
MT5_INVESTOR_PASSWORD_ONLY = YES
MQL5_BRIDGE_PROGRAM_TYPE = CUSTOM_INDICATOR
MQL5_ORDER_SEND = STRUCTURALLY_PROHIBITED
PYTHON_ORDER_API = ABSENT
BROKER_ACCOUNT_API = ABSENT
ORDER_SUBMISSION = IMPOSSIBLE
ORDER_MODIFICATION = IMPOSSIBLE
ORDER_CANCELLATION = IMPOSSIBLE
PAPER_PATH = ABSENT
LIVE_TRADING_PATH = ABSENT
REAL_MONEY_AUTHORITY = ABSENT
ECONOMIC_COMMITMENT = IMPOSSIBLE
```

The bridge may emit only passive market-data observations and liveness metadata. It may not expose terminal/account state that is unnecessary for market observation.

## Provider replacement rule

Rico is selected for qualification, but the domain contract remains broker-agnostic. If runtime qualification fails because of cost, entitlement, missing WIN realtime data, missing Investor mode, or another hard requirement, Rico is rejected without weakening Sprint 1 and without changing Observer domain semantics. A replacement broker-backed MT5 feed may then be evaluated under the same boundary.

## Current public evidence

As of 14/09/2026:

- Rico MetaTrader page: https://www.rico.com.vc/plataformas/metatrader/
- Rico platform comparison: https://www.rico.com.vc/documentos/comparativo-plataformas/
- MQL5 trade permission / Investor mode: https://www.mql5.com/en/docs/runtime/tradepermission
- MQL5 program restrictions / indicator prohibition of `OrderSend`: https://www.mql5.com/en/docs/runtime/running

Commercial terms remain external and mutable; runtime qualification must revalidate them.