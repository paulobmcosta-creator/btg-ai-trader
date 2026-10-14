# S8-STRATEGY-REMEDIATION — Operational Strategy / TradeIntent

```text
SPRINT = 8
WORK_MODE = PREAUTH_BLOCKER_REMEDIATION_ONLY
ISSUE = #95
UPSTREAM_ENTRY_GATE_PR = #94
UPSTREAM_ENTRY_GATE_HEAD = 7fce78b02d03cc8140bc021217a0230776cc53ff
CANONICAL_BRANCH = sprint/8-paper-trader
UPSTREAM_WORK_BRANCH = s8/00-entry-gate
WORK_BRANCH = s8/01-strategy-remediation

S8-B01_REMEDIATION = AUTHORIZED
S8-B01_REMEDIATION_AUTHORIZATION_DATE = 2026-10-04
S8-B01_REMEDIATION_CANDIDATE = IMPLEMENTED_PENDING_EXACT_HEAD_CI_AND_INDEPENDENT_REVIEW
S8-B02 = OPEN

S8_FUNCTIONAL_IMPLEMENTATION = NOT_AUTHORIZED
PAPER_CONFIRMATORY_RUN = NOT_AUTHORIZED
LIVE_TRADING = NO
REAL_MONEY = NO
BROKER_ORDER_SIDE_EFFECT = FORBIDDEN
CANONICAL_FINANCIAL_LEDGER_MUTATION = FORBIDDEN
MERGE = FORBIDDEN_WITHOUT_HUMAN_AUTHORIZATION
```

## 1. Purpose

Remediate only S8-B01 by materializing the upstream operational Strategy path required by ADR 0016 and Protocol 0E-F. This work is deliberately separate from Paper Trader functionality and from S8-B02 candidate promotion.

The implemented path is:

```text
DecisionOpportunity / admitted upstream evidence
        ↓
CandidateStrategy
        ↓
deterministic ordered StrategyRule policy
        ↓
StrategyDecision
   ├── NO_TRADE
   └── PROPOSE_TRADE
            ↓
       TradeIntent
            ↓
   one-way risk_adapter
            ↓
       RiskProposal
            ↓
 existing S7 Risk Engine
```

## 2. Runtime contracts

### CandidateStrategy

`CandidateStrategy` is an immutable, version-specific policy identity. Its digest binds:

- strategy name and version;
- code revision;
- one concrete `TradableInstrumentId`;
- portfolio identity;
- upstream input-spec digest;
- maximum admitted evidence age;
- the complete ordered rule set and every economic objective.

The infrastructure selects no favorable thresholds and creates no canonical candidate by itself. Thresholds, priorities, sizing and directions are candidate-owned configuration and therefore become part of candidate identity.

### DecisionOpportunity

`DecisionOpportunity` is the causal Strategy input boundary. It binds:

- concrete instrument and portfolio;
- `event_time <= knowledge_time <= decision_time`;
- exact upstream input-spec digest;
- immutable finite Decimal signal mapping;
- explicit evidence quality;
- source provenance digest.

It is not a Signal generator and does not synthesize market evidence.

### StrategyDecision

Every evaluated opportunity produces an explicit engine-issued `StrategyDecision`:

- `NO_TRADE`; or
- `PROPOSE_TRADE`.

`NO_TRADE` remains a first-class auditable result. Instrument, portfolio, input-spec, evidence-quality, staleness and required-signal failures fail closed to `NO_TRADE`.

### EconomicObjective and TradeIntent

A matched rule carries one immutable `EconomicObjective` with:

- one of the four S7-compatible economic directions;
- positive requested quantity and explicit unit;
- positive requested exposure and explicit unit.

Only an engine-issued `PROPOSE_TRADE` decision may produce an engine-issued `TradeIntent`. The intent binds the candidate digest, opportunity digest, decision digest, concrete instrument, portfolio, economic objective, creation time and source digest.

### Risk adapter

`to_risk_proposal()` is the only Strategy-to-Risk adapter in this workstream. It:

- checks the engine-issued marker as defense in depth, not authentication;
- requires separately admitted candidate and causal evidence from a trusted consumer source;
- independently replays the policy and rejects NO_TRADE or any economic/lineage mismatch;
- constructs RiskProposal exclusively from the replayed intent, not the caller's object;
- maps the four economic directions explicitly to the canonical S7 enum;
- preserves quantity, exposure, units, instrument, portfolio and decision time;
- sets `RiskProposal.source_digest = TradeIntent.intent_digest`;
- creates no `RiskDecision`, `RiskAuthorization` or execution authority.

## 3. Determinism and fail-closed semantics

The runtime uses no randomness, wall-clock reads, network, broker API, filesystem I/O or dynamic code loading. Identical immutable candidate/opportunity inputs produce identical decision/intent/result digests.

Rules are canonicalized by unique integer priority. The first matching rule is deterministic. Missing required signals do not fall through to a potentially favorable lower-information path; they produce `NO_TRADE`.

Evidence at exactly the configured maximum age remains admissible; evidence older than the predeclared maximum produces `NO_TRADE`.

## 4. Explicit non-goals

This workstream does not implement or authorize:

- a specific empirically favorable Strategy candidate;
- `PAPER_ELIGIBLE` adjudication or candidate freeze;
- `AuthorizationAllocation`;
- `OrderIntent`, `OrderPlan`, `ExecutionOrder` or any execution command;
- Paper fills, paper account state, P&L or Paper evidence;
- broker/account/order connectivity;
- canonical `FinancialLedger` mutation;
- Live Trading or real money.

Accordingly, successful S8-B01 remediation leaves S8-B02 open and leaves functional Paper prohibited.

## 5. Acceptance evidence required

The remediation candidate must pass, at one exact PR head:

- full repository regression;
- 100% statement and branch coverage for `btg_ai_trader.strategy`;
- Ruff;
- strict mypy;
- compileall;
- dependency check;
- Foundation integrity;
- S1–S7 capability-boundary checks;
- dedicated S8 Strategy boundary scanner;
- exact authorized-file-surface check;
- pinned upstream engineering;
- independent Codex review with no blocking findings.

## 6. Authorized file surface

Only the following may change relative to `7fce78b02d03cc8140bc021217a0230776cc53ff`:

- `src/btg_ai_trader/strategy/**`;
- `tests/strategy/**`;
- `scripts/check_s8_strategy_boundary.py`;
- the minimal S1 verifier compatibility update that adds `strategy` to the already-existing post-S1 root exclusions;
- the NEG-CAP-10 test correction so it verifies modules loaded *by S1 execution*, rather than modules imported earlier by unrelated future-sprint tests;
- `.github/workflows/s8-strategy-remediation-ci.yml`;
- S8 governance/workstream documentation and living checkpoint documents.

No dependency, Foundation, protocol or historical ADR change is authorized.

## 7. Current stop condition

```text
S8-B01_REMEDIATION_CANDIDATE = IMPLEMENTED_PENDING_EXACT_HEAD_CI_AND_INDEPENDENT_REVIEW
S8-B01_CANONICAL_CLOSURE = NO
S8-B02 = OPEN
PROMOTION_TO_S8_FUNCTIONAL_IMPLEMENTATION = NO
S8_FUNCTIONAL_IMPLEMENTATION = NOT_AUTHORIZED
PAPER_CONFIRMATORY_RUN = NOT_AUTHORIZED
MERGE = FORBIDDEN_WITHOUT_HUMAN_AUTHORIZATION
```


## 8. Historical S1 compatibility clarification

The original S1 boundary verifier already excludes post-S1 package roots (Replay through Risk) before comparing the frozen S1 source inventory. Adding the explicitly authorized `src/btg_ai_trader/strategy` root to that same exclusion list preserves, rather than relaxes, the S1 inventory pins.

Likewise, NEG-CAP-10 is clarified to compare `sys.modules` immediately before and after S1 execution. Its invariant is that executing S1 must not load future financial modules; unrelated test-collection/import order must not cause a false positive merely because a later-sprint module legitimately exists.

## 9. 2026-10-13 — Consumer-side provenance revalidation (P1)

The old `is_engine_issued` closure marker can be falsified in the same
Python interpreter by replacing the read-only snapshot's *closure cell*.
SHA content digests and `frozen=True` dataclasses are not authenticity.

The Strategy→Risk adapter now **fails closed** without both
`admitted_candidate` and `admitted_opportunity`. The consumer must source
those inputs independently of the `TradeIntent` supplier, from a trusted
upstream policy/evidence admission boundary. It reconstructs the complete
deterministic Strategy decision and exact economic intent and compares all
fields before emitting a proposal from the independently replayed values.
NO_TRADE, unknown admission or any disagreement forbids forwarding.

**Bounded threat model:** simply passing alternate objects created by an
untrusted caller is NOT independent admission. This Sprint does not provide
a trusted admission service or an isolation sandbox. Arbitrary hostile code
in the same interpreter can introspect/monkeypatch Python functions, and the
AST negative-capability checks are defense-in-depth, not process isolation.
The later authorized composition owner must independently admit/fix source
candidate and causal opportunity; otherwise no `RiskProposal` is authorized.
This P1 remediation cannot be interpreted as Paper or Live readiness.

New adversarial cases forge the verifier closure itself and recompute intent
digests, verify consumer-side rejection, missing-context fail-closed,
provenance mismatches and NO_TRADE. Re-review the exact head before closure.

```text
S8-B01_CANONICAL_CLOSURE = NO
S8-B02 = OPEN
S8_FUNCTIONAL_IMPLEMENTATION = NOT_AUTHORIZED
PAPER_CONFIRMATORY_RUN = NOT_AUTHORIZED
MERGE = FORBIDDEN_WITHOUT_HUMAN_AUTHORIZATION
```

## 10. 2026-10-13 — P2 compound-alias bypass

The Strategy AST boundary now fails closed on opaque module-value transfers
through destructuring, nested container binding, for/async-for loops,
comprehensions, annotated bindings and computed named expressions. The safe
simple alias `codec = json; codec.dumps(...)` remains explicitly supported.
Adversarial regression fixtures cover the previously reported
`(codec,) = (json,)` write path and several related patterns.

The verifier is a static negative-capability check, **not a Python sandbox**.
Untrusted Strategy code must still be isolated at an appropriately approved
runtime boundary. This correction does not promote the candidate, grant Paper
authority, or close S8-B01 without independent exact-head review.

## 11. 2026-10-14 — Market-event freshness and bounded issuance ledger

The newly reviewed P1 is addressed in the deterministic Strategy outcome:
the `max_evidence_age_seconds` threshold now applies to the difference
between `decision_time` and **both** `event_time` and `knowledge_time`,
with UTC-normalized instants and the pre-existing causal order invariant.
An old market event received moments before a decision must return
`NO_TRADE / EVIDENCE_TOO_OLD`, and equality at the bound remains admissible.
Regression tests cover day-old delayed evidence, a microsecond beyond the
limit, exact equality, and cross-timezone event observations.

The P2 quadratic issuance bookkeeping is replaced by one stable read-only
`MappingProxyType` view over a private O(1)-average mutable ledger. Only the
private issuer can register, and the weakref cleanup removes an entry only
when the callback identity matches that entry (safe if IDs are reused).
The verifier still captures a read-only proxy; retained-batch tests assert
its identity does not change with issuance and prevent reintroduction of
a copy-per-decision path. As already documented in §9, Python closure
reflection is **not** a same-process adversarial authenticity boundary.

The P2 scanner now rejects module capabilities returned or yielded by
helpers, including nested return containers and lambdas. Negative fixtures
demonstrate `def codec(): return json; codec().dump(...)` is blocked without
rejecting pure `json.dumps` value returns. The AST scanner remains
defense-in-depth, not a sandbox.

This changes no upstream protocol, Risk authorization, Paper eligibility,
financial ledger or broker surface. S8-B01 remains subject to exact-head
CI and independent re-review. No merge or S8 functional authority is granted.

```text
S8-B01_CANONICAL_CLOSURE = NO
S8-B02 = OPEN
S8_FUNCTIONAL_IMPLEMENTATION = NOT_AUTHORIZED
PAPER_CONFIRMATORY_RUN = NOT_AUTHORIZED
LIVE_TRADING = NO
REAL_MONEY = NO
MERGE = FORBIDDEN_WITHOUT_HUMAN_AUTHORIZATION
```


## 12. 2026-10-14 — P2 transferred modules in function defaults

Independent Codex review of `5700a412` found that a function argument's
default value could capture the module object without an AST boundary finding:
`def encode(value, handle, codec=json): codec.dump(value, handle)`.
The scanner now rejects transfers of allowlisted module capabilities
through positional and keyword-only function defaults in `def`,
`async def`, and `lambda`, including nested containers and simple
aliases. It preserves legitimate pure-value defaults. Dedicated negative
regressions demonstrate the scanner fails closed on each case.

This correction is static negative-capability defense in depth; it does not
prove arbitrary Python code in the same interpreter is isolated. No Paper
execution, candidate promotion, Risk authority, real order capability, or
merge is authorized. Independent review of the exact resulting head
remains mandatory.

## 13. 2026-10-14 — P2 module capability transfer through calls

The latest independent review of `4d8687af` reproduced
`passthrough(json).dump(...)`: module values supplied to arbitrary helper
calls could escape and perform I/O without a finding. The scanner now fails
closed when any call argument carries an allowlisted module capability,
including positional, keyword, unpacked positional/keyword, nested-container,
and module-alias cases. Negative regression tests cover each class; pure
value arguments and `json.dumps` remain allowed.

This fix restricts only the approved S8-B01 scanner/tests and records its
rationale. Static source inspection is defense in depth, not isolation of
arbitrary code; all other runtime trust and financial authorization gates
remain unchanged. Canonical S8-B01 closure requires exact-head CI and a
separate independent review with no blocking findings.


## 14. 2026-10-14 — Codex P2 arbitrary injected callable

Codex review of `9e62c65d` identified a critical static-policy omission:
`client.submit_order(order)` / `client.cancel_order(order)` and injected
`effect()` calls passed despite explicit Strategy non-capabilities.

The dedicated scanner now **fails closed by default on AST calls**, subject
to a small, explicit allowlist of existing, manually reviewed, pure
Strategy call sites and two typed primitive-result chains. A restricted
issuance-ledger weakref retrieval is the only approved indirect callback
call. New helper/receiver methods cannot be added without a deliberate
review of that exact call surface and tests. Adversarial fixtures include
order-submit/cancel, arbitrary effect/callback methods and dynamic
`getattr`; existing hash/JSON call chains remain permitted.

This is not a sandbox and lexical call allowlisting cannot authenticate a
caller-supplied object in a hostile shared Python runtime. Risk consumer
replay requires **independently admitted** Strategy/evidence as described
in §9. This remediation changes no Risk Engine or Paper/Live authority.

### Exact-head test reconciliation — local helpers and aliases

The fail-closed call policy additionally recognizes functions/classes declared
in the scanned source **only if their names are not shadowed** by parameter,
assignment or loop-target bindings. Reviewed aliases of pure module APIs
(e.g. `digest = hashlib.sha256`) retain their original callable identity.
References to broker submission/cancellation attributes are forbidden even
without an immediate invocation. Shadowed local helper callbacks fail closed.
This preserves legitimate pure helpers without granting caller-supplied
callbacks a generic invocation capability.

## 15. 2026-10-14 — Independent Codex P2 findings on exact head a5b7388c

Independent review documented two missing negative capabilities in the Strategy
scanner: **(a)** a parameter named like an approved call or receiver could run
injected code, and **(b)** attribute/subscript writes to caller-owned objects
were not screened. Both are now explicitly denied with AST lexical scope
inspection. A narrowly constrained exception permits only audited read-only
parameter methods in their existing Strategy domain helpers. Local dictionary
writes remain permitted exclusively for `ledger` inside the two private
issuance factories and `frozen` inside `_freeze_signals`. External writes,
augmented assignment, deletion and destructuring into injected objects fail
closed. `object.__setattr__` remains permitted only for direct dataclass
`self` construction in Strategy domain `__post_init__`. Negative tests
reproduce the two Codex P2 examples and expanded mutation/callback variants.

The scanner is static defense in depth, not a Python sandbox. No Paper/Live,
broker API, financial state, candidate promotion, or merge authority changes.
Exact-head CI and a separate independent re-review remain mandatory.
