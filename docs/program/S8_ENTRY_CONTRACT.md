# Sprint 8 — Paper Trader Entry Contract

## 0. Authority and current state

\`\`\`text
SPRINT_8_ENTRY_GATE_AUTHORIZATION_DATE = 2026-10-02
SPRINT_8_ENTRY_GATE_ISSUE = #93
SPRINT_8_CANONICAL_BRANCH = sprint/8-paper-trader
SPRINT_8_ENTRY_GATE_WORK_BRANCH = s8/00-entry-gate
SPRINT_8_REQUIRED_PREDECESSOR_BRANCH_HEAD = 1226aea13bc8a99303b8c008883fd36068247829
SPRINT_7_FUNCTIONAL_CANONICAL_HEAD = e379e9b34a8b607e86165bd3336d23fcd9406259

S8_ENTRY_GATE = CHANGES_REQUIRED
OPEN_S8_ENTRY_GATE_BLOCKERS = 2
S8_FUNCTIONAL_IMPLEMENTATION = NOT_AUTHORIZED
PAPER_CONFIRMATORY_RUN = NOT_AUTHORIZED

LIVE_TRADING = NO
REAL_MONEY = NO
BROKER_ORDER_SIDE_EFFECT = FORBIDDEN
CANONICAL_FINANCIAL_LEDGER_MUTATION = FORBIDDEN
\`\`\`

This contract materializes the Sprint 8 governance boundary only. It does not authorize functional Paper Trader code.

## 1. Mission

Sprint 8 is the first prospective, non-funded evaluation stage. Under Protocol 0E-G, Paper Trading must operate on contemporaneously received market data and exercise the real system decision chain while remaining structurally incapable of creating real financial exposure.

The normative chain remains:

\`\`\`text
contemporaneous admitted market evidence
        |
        v
Signal / Strategy
        |
        v
StrategyDecision
   /            \
NO_TRADE     PROPOSE_TRADE
                  |
                  v
             TradeIntent
                  |
                  v
             RISK ENGINE
            /           \
         REJECT        PERMIT
                         |
                         v
               RiskAuthorization
                         |
                         v
              AuthorizationAllocation
                         |
                         v
                  OrderIntent
                         |
                         v
                    OrderPlan
                         |
                         v
              PAPER EXECUTION ONLY
                         |
                         v
            FICTIONAL ACCOUNT STATE
\`\`\`

No S8 path may cross a real broker/account/order commitment boundary.

## 2. Hard prerequisites for functional authorization

Functional Sprint 8 authorization is conjunctive. All of the following must be satisfied before implementation may start:

1. Sprint 7 remains formally closed/PASS and its audited Risk Engine baseline is exact.
2. A concrete operational Signal/Strategy path exists and emits explicit \`StrategyDecision\`.
3. A concrete \`TradeIntent\` contract exists, binds one concrete tradable instrument and an explicit economic objective, and is the exact input presented to Risk.
4. A specific candidate is formally adjudicated \`PAPER_ELIGIBLE\` under all ten cumulative 0E-G eligibility classes.
5. Candidate identity and all quantitatively material elements are frozen/versioned before confirmatory Paper evidence begins.
6. Candidate-specific Paper policies for duration/information sufficiency, Backtest↔Paper discrepancy, latency/slippage tolerances and stopping rules are predeclared.
7. Risk cannot be bypassed, disabled or replaced by a Paper-local favorable substitute.
8. The Paper execution surface is structurally non-funded and cannot dispatch to a real broker/account/order API.
9. Paper evidence, decisions and discrepancies are append-only/provenance-bound.
10. Any material candidate change during Paper closes the current evidence partition and starts a new lineage.

## 3. Entry-gate blockers found on the canonical predecessor

### S8-B01 — Operational Strategy/TradeIntent chain absent

The canonical source tree at the predecessor head contains packages for Observer, Replay, Backtesting, Statistical Baselines, ML, Scenario and Risk, but no operational Signal/Strategy package and no materialized runtime classes for \`StrategyDecision\` or \`TradeIntent\`.

This is a hard blocker because Protocol 0E-G requires confirmatory Paper to execute the exact candidate through real prospective system decisions. Paper infrastructure may not invent an embedded strategy merely to make the pipeline runnable.

\`\`\`text
S8-B01 = OPEN
STRATEGY_OPERATIONAL_PATH = ABSENT
STRATEGY_DECISION_RUNTIME_CONTRACT = ABSENT
TRADE_INTENT_RUNTIME_CONTRACT = ABSENT
\`\`\`

### S8-B02 — No formally PAPER_ELIGIBLE frozen candidate

No canonical artifact establishes that one exact candidate satisfies the ten cumulative, non-compensatory eligibility classes of Protocol 0E-G and has been frozen for prospective Paper evaluation.

\`\`\`text
S8-B02 = OPEN
PAPER_ELIGIBLE_CANDIDATE = ABSENT
CANDIDATE_FREEZE = ABSENT
CONFIRMATORY_PAPER_START = FORBIDDEN
\`\`\`

These are root blockers. Candidate-specific thresholds and execution-policy choices cannot be honestly finalized before they are resolved.

## 4. Paper authority boundary

A future authorized S8 implementation may, and only within the non-funded Paper profile:

- consume admitted contemporaneous market data;
- consume an exact frozen Strategy/TradeIntent lineage;
- invoke the canonical S7 Risk Engine without bypass;
- create a bounded \`AuthorizationAllocation\` only from a still-valid \`RiskAuthorization\`;
- create broker-neutral internal \`OrderIntent\` and \`OrderPlan\` artifacts;
- simulate execution using contemporaneous observable market evidence;
- maintain explicitly fictional paper cash/position/P&L projections;
- emit append-only paper evidence and a final \`PaperGateAssessment\`.

It may not:

- connect an execution-capable broker/account/order API;
- transmit, modify or cancel a real order;
- use real cash, margin, buying power, positions or custody as writable state;
- mutate the canonical future \`FinancialLedger\`;
- claim live fill probability, queue priority, exchange impact, broker settlement or production readiness;
- silently substitute a strategy/candidate;
- adapt the candidate from confirmatory Paper evidence without closing the current evidence partition;
- promote to Live automatically.

## 5. AuthorizationAllocation and capacity semantics

Sprint 8 is the first stage where downstream consumption of \`RiskAuthorization\` becomes materially relevant.

Before functional authorization, the design must specify an atomic, fail-closed allocation rule that:

- revalidates authorization time/state/policy validity at allocation time;
- never allocates more than the remaining bounded authorization;
- prevents double-spend of risk capacity across concurrent Paper intents;
- preserves the distinction among available, reserved, committed, realized and released capacity;
- releases only by an explicit governed lifecycle event;
- does not fabricate physical market exposure merely because risk capacity is reserved.

The physical mechanism is not selected by this blocked Entry Gate.

## 6. Paper accounting boundary

Paper capital is fictional. S8 must not silently turn the future canonical \`FinancialLedger\` into a simulator.

The future functional design must therefore maintain an explicitly isolated Paper accounting/projection surface. Where economically appropriate, it may reuse already validated Sprint 3 simulation semantics, but any such reuse must be explicit and provenance-bound. Paper accounting does not validate broker margin, settlement, external cash, custody or real financial recognition.

## 7. Evidence and 0E-G requirements

Confirmatory Paper must preserve:

- prospective causality and no future-data access;
- all generated decisions including \`NO_TRADE\`;
- exact candidate identity;
- contemporaneous observable execution inputs;
- Backtest↔Paper structural/distributional comparison;
- all material discrepancies;
- critical operational errors;
- predeclared stopping rules;
- append-only evidence;
- explicit \`PaperGateAssessment\` at closure.

Positive fictional P&L alone is never sufficient for a PASS Paper Gate.

## 8. Zero-cost and dependency boundary

The Entry Gate introduces no paid service and no new mandatory runtime dependency.

Any future functional design must preserve the project constraint of zero additional recurring cost unless a later explicit human decision changes that constraint.

## 9. Current verdict

\`\`\`text
S8_ENTRY_GATE_CANDIDATE = CHANGES_REQUIRED
OPEN_S8_ENTRY_GATE_BLOCKERS = 2
PROMOTION_TO_S8_FUNCTIONAL_IMPLEMENTATION = NO

S8_FUNCTIONAL_IMPLEMENTATION = NOT_AUTHORIZED
PAPER_CONFIRMATORY_RUN = NOT_AUTHORIZED
LIVE_TRADING = NO
REAL_MONEY = NO
\`\`\`
