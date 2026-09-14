# S1 — DD-60 Initial Market Data Provider Decision Packet

## Status

```text
DD_ID = DD-60
DECISION = PENDING_HUMAN_SELECTION
MANDATORY_FOR_ALL = YES
ADR_REQUIRED = YES
DEPENDENT_CAPABILITY = AC-05 Read-Only Market-Data Subscription
NO_PROVIDER_CODE_BEFORE_DECISION = TRUE
```

This packet is advisory evidence for the coordination decision. It does not itself select a provider and
is not an ADR.

## Contract criteria

The selected provider must support the Sprint 1 observer while preserving:

- `READ_ONLY_BY_CONSTRUCTION`;
- `STRUCTURAL_ESCALATION`;
- zero trading credentials consumed by the Observer;
- zero order/execution authority;
- point-in-time instrument discovery/resolution;
- read-only subscription/streaming for B3 market data;
- tick/candle or equivalent observation needed by the laboratory;
- heartbeat/reconnect/liveness evidence;
- explicit provider capabilities and timestamp/fidelity limitations;
- a clean path to technical evidence persistence and provenance;
- all applicable dual-use conditions from 0F-E.

## Candidate A — BTG Solutions Data Services

### Current official evidence reviewed on 2026-09-13

Official BTG Solutions Data Services material states that the service is designed for financial
applications and strategies and exposes Brazilian market data through REST and WebSocket. Its current
Python documentation exposes a `MarketDataFeed` / market-data WebSocket surface with:

- `exchange='b3'`;
- `stream_type='realtime'` or `delayed`;
- market-data types including `trades`, `books`, `candles-1S`, `candles-1M`, `instrument_status` and
  `settlement-price`;
- `data_subtype='derivatives'` as a supported subtype;
- `available_to_subscribe()` for instrument discovery;
- `subscribe()`, `unsubscribe()`, `run()` and `close()` for feed lifecycle;
- reconnect support;
- API-key authentication;
- official Python 3.12 compatibility recorded in the package changelog.

The REST client also documents `get_available_tickers(..., market_type='derivatives')` and reference-data
queries. The product site explicitly positions the service as BTG Pactual Solutions' market-data product
for the Brazilian market.

Primary sources:

- https://dataservices.btgpactualsolutions.com/
- https://dataservices.btgpactualsolutions.com/site/about
- https://python-client-docs.dataservices.btgpactualsolutions.com/btgsolutions_dataservices.websocket.html
- https://python-client-docs.dataservices.btgpactualsolutions.com/btgsolutions_dataservices.rest.html
- https://python-client-docs.dataservices.btgpactualsolutions.com/changelog.html

### Architectural fit

```text
MARKET_DATA_ONLY_SURFACE = STRONG
NATIVE_STREAMING = YES
B3 = YES
DERIVATIVES = YES
INSTRUMENT_DISCOVERY = YES
PYTHON_3_12 = DOCUMENTED
TRADING_API_IN_SAME_DOCUMENTED_CLIENT = NOT_OBSERVED_IN_REVIEWED_MARKET_DATA_SURFACE
TRADING_ACCOUNT_CREDENTIAL_REQUIRED = NOT_INDICATED_FOR_MARKET_DATA_CLIENT
API_KEY_REQUIRED = YES
```

This candidate is therefore the current **preferred architecture fit** for Sprint 1 because the provider
surface is already market-data-oriented and does not require the Observer to import a general trading
terminal SDK merely to receive market data.

### Required qualification before acceptance

Even if selected, the adapter must still prove:

1. API-key handling without leak in logs/manifests;
2. exact availability of the chosen B3 derivative/instrument under DD-68;
3. real connection and subscription in an authorized test account/plan;
4. observed event schema, timestamp semantics and fidelity limits;
5. reconnect and daily/session lifecycle behavior;
6. bounded ingestion/backpressure behavior under the real feed;
7. no hidden execution or financial-authority dependency in the imported package/runtime graph;
8. full NEG-CAP and final Security Diff Scan evidence.

## Candidate B — MetaTrader 5

### Current official evidence reviewed on 2026-09-13

The official MetaTrader 5 Python integration supports market-data functions such as `symbols_get`,
`symbol_info_tick`, market book subscription and tick/bar retrieval. However, the same official Python
surface also exposes active-order, position, margin/profit and `order_send` functions. `initialize()` can
connect to the terminal using trading account login/password/server parameters or discover an existing
terminal instance.

Primary sources:

- https://www.mql5.com/en/docs/python_metatrader5
- https://www.mql5.com/en/docs/python_metatrader5/mt5initialize_py
- https://www.mql5.com/en/docs/python_metatrader5/mt5symbolsget_py
- https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksfrom_py

The repository's existing PR #11 spike additionally proves Python 3.12 installation/import compatibility
for the inspected package but deliberately does **not** prove terminal connection, real market-data
capture, reconnect/liveness or the eleven dual-use admissibility conditions.

### Architectural fit

```text
MARKET_DATA_CAPABLE = YES
NATIVE_STREAMING_OR_BOOK = YES
B3_AVAILABILITY = BROKER_TERMINAL_DEPENDENT
PYTHON_3_12_IMPORT = PROVEN_BY_SPIKE
DUAL_USE_EXECUTION_SURFACE = YES
TRADING_ACCOUNT_CONTEXT = POSSIBLE
DD_61_IF_SELECTED = TRIGGERED
DUAL_USE_PROOF_BURDEN = HIGH
```

MT5 remains technically viable only if the eleven dual-use conditions can be demonstrated. It carries a
materially higher Sprint 1 safety/audit burden because market-data and execution functions coexist in the
same SDK/terminal environment.

## Comparative adjudication

| Criterion | BTG Solutions Data Services | MetaTrader 5 |
|---|---|---|
| Official/current source | BTG Pactual Solutions | MetaQuotes |
| B3 market data | Explicit | Depends on connected broker/server |
| Derivatives support | Explicitly documented | Possible through broker symbol universe |
| Read-only product orientation | **Strong** | Weak — dual-use trading terminal |
| Streaming | WebSocket | Terminal API / market book + retrieval |
| Instrument discovery | Explicit APIs | `symbols_get()` |
| Python 3.12 | Official changelog support | Repository spike proves import; DD-61 still needed end-to-end |
| Credential model | API key | Terminal/account context may involve login/password/server |
| Execution functions in same SDK | Not observed in reviewed market-data client | **Yes (`order_send`, etc.)** |
| Dual-use isolation burden | Lower | **High** |
| Fit to `READ_ONLY_BY_CONSTRUCTION` | **Preferred** | Conditional / higher-risk |

## Coordination recommendation

```text
RECOMMENDED_DD60_SELECTION = BTG_SOLUTIONS_DATA_SERVICES
RECOMMENDATION_CLASS = ARCHITECTURAL_SAFETY_AND_SCOPE_FIT
HUMAN_DECISION_REQUIRED = YES
```

Rationale: Sprint 1 needs market data, not a trading terminal. An official BTG market-data service with
B3 derivatives, WebSocket streaming, instrument discovery and Python 3.12 support minimizes the amount
of dual-use capability that must be excluded by construction. MT5 should remain a fallback candidate,
not the default, unless the BTG Data Services real-feed qualification fails materially.

## Decision consequences if Candidate A is approved

Before provider-dependent code:

1. create a DD-60 ADR selecting BTG Solutions Data Services for Sprint 1 only;
2. classify API-key handling under DD-43 as triggered read-only credential management;
3. resolve DD-68 for the first real laboratory derivative/instrument;
4. implement the smallest adapter around the market-data-only feed surface;
5. prohibit import/use of any unrelated product client in the Observer runtime;
6. execute real read-only subscription, discovery, liveness/reconnect and evidence tests;
7. rerun NEG-CAP and the official Security Diff Scan before Sprint 1 acceptance.

No DD-60 selection authorizes execution, trading credentials, Paper or real-money operation.
