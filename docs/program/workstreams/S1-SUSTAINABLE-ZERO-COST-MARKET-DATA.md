# Sprint 1 — Sustainable zero-cost realtime market-data direction

## Status

```text
CEDRO_FREE_TRIAL = REJECTED_AS_CANONICAL_LONG_TERM_PROVIDER
CEDRO_HISTORY = PRESERVED_AND_REVERTED
ZERO_ADDITIONAL_COST = HARD_CONSTRAINT
REALTIME_REQUIREMENT = PRESERVED
CANONICAL_PROVIDER_SELECTION = REOPENED
LEADING_CANDIDATE = BROKER_SUPPLIED_MT5_READ_ONLY_INDICATOR_BRIDGE
```

## Rationale

A time-limited provider trial can prove an integration but cannot serve as the canonical market-data source for a program that must remain usable after development is complete.

B3 market-data policy distinguishes realtime/delayed commercial distribution from D-1/end-of-day data. D-1/historical sources remain useful for development and replay, but they do not satisfy the frozen Sprint 1 realtime observation/subscription obligations.

The leading sustainable zero-additional-cost path is therefore broker-supplied MetaTrader 5 market data, provided that the project consumes it through a structurally read-only boundary rather than the dual-use MT5 Python trading API.

## Proposed architecture

```text
Broker MT5 server
    -> MetaTrader 5 terminal
       -> login using INVESTOR / READ-ONLY password only
       -> custom MQL5 INDICATOR attached to exact WIN symbol
          -> indicator receives price/tick recalculation events
          -> indicator writes bounded append-only market-data records to local file sandbox
             -> BTG AI Trader Python Observer tails/reads file
                -> RawFrame / admission / evidence
```

### Why a custom indicator

MetaTrader 5 officially supports investor authorization: it permits account/status/price observation but does not permit trading.

MQL5 also structurally prohibits trading functions in custom indicators, including `OrderSend`, `OrderCheck`, `OrderCalcMargin` and `OrderCalcProfit`. A custom indicator can write data to the platform file sandbox, while the trusted Python runtime never imports `MetaTrader5` and never receives broker-account or order functions.

This is stronger than merely promising not to call `order_send`: the bridge program type itself cannot execute those trading functions.

## Candidate broker access

Current public broker pages indicate that MetaTrader 5 real-account platform access can be R$0/month at some Brazilian brokers, including Clear and Modal. These commercial conditions can change and therefore MUST NOT be hard-coded into the architecture.

The provider abstraction must treat the broker as replaceable. Before qualification, the selected broker must be verified for:

1. ongoing R$0 platform/market-data cost under the intended account state;
2. realtime WIN quotes/ticks available in MT5;
3. investor/read-only login supported by the connected MT5 server;
4. no minimum real-money trading requirement to retain the market-data entitlement;
5. stable exact-symbol access for the current WIN contract.

If any condition fails, that broker is rejected without changing the bridge contract.

## Free permanent development sources

For development, instrument discovery and historical/replay work, free D-1/end-of-day sources remain useful independently of the realtime bridge:

- B3 D-1/end-of-day data where publicly available/licensed;
- brapi futures endpoints for WIN/WDO, which are EOD and explicitly not realtime.

These sources MUST NOT be relabeled as realtime Sprint 1 qualification evidence.

## Negative capabilities

The eventual implementation MUST enforce:

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
PAPER_PATH = ABSENT
LIVE_TRADING_PATH = ABSENT
REAL_MONEY_AUTHORITY = ABSENT
```

The bridge may emit only passive market-data observations and liveness metadata. It may not expose terminal/account state that is unnecessary for market observation.

## Next decision gate

Do not select a broker as canonical until current terms and actual realtime WIN availability are verified. Implement/test the bridge contract offline first, then qualify at least one sustainable broker-backed feed. Provider replacement must not require changes to Observer domain semantics.
