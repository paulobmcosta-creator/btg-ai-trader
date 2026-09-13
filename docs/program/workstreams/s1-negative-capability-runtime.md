# S1 — Runtime NEG-CAP evidence

Status: EXECUTED_ON_REMOTE_CI; INTEGRATION_REVALIDATION_REQUIRED.

This evidence complements, but does not replace, the structural boundary checker in `scripts/check_s1_boundary.py` and does not constitute the official Security Diff Scan.

## Executed evidence

- Runtime-test implementation head: `06038b3ab9ad10dd90f735592e859747594d24ae`.
- GitHub Actions Remote Python CI: `34789456375` — SUCCESS.
- Pinned upstream engineering verification: `34789456321` — SUCCESS.
- Test job: 434 tests passed; aggregate branch-inclusive coverage 95%.
- `tests/negative_capabilities/test_runtime.py`: all runtime NEG-CAP cases passed.
- Structural boundary job: PASS on the same reviewed source scope.
- Foundation guard, Ruff, mypy, compileall, pip check and diff checks: PASS on the same head.

This head preceded the final reanchor over the property/mutation merge; all claims must be revalidated after that ancestry update before integration.

## Runtime obligations

| Obligation | Runtime evidence |
|---|---|
| NEG-CAP-01 | A real Tick fixture traverses `FixtureObserver`; result is the closed passive `StepResult` surface with no execution authority. |
| NEG-CAP-02 | Executor-shaped dependency objects and a dual-use provider subclass are rejected by exact-type admission before any callback is invoked. |
| NEG-CAP-03 | A nontrivial observation writes only technical archive/journal evidence; an isolated financial sentinel directory remains untouched. |
| NEG-CAP-04 | Strict `ObserverConfig.from_mapping` rejects execution-like keys such as `order_send`, `live_trading`, `auto_trade` and `executor`. |
| NEG-CAP-05 | Synthetic trading-credential environment markers are not required or persisted in Observer technical evidence. This is bounded runtime evidence, not a universal process-level secret-flow proof. |
| NEG-CAP-06 | The admitted fixture provider exposes only `describe_capabilities` and `read_next`; dual-use subclasses are rejected before invocation. |
| NEG-CAP-07 | Quarantine drives the passive posture to `SAFE_HALT`; a following valid fixture does not automatically unlatch it and no financial callback surface exists. |
| NEG-CAP-08 | Runtime packaging declares zero runtime dependencies and no scripts, GUI scripts or entry points. Structural inventory separately checks packaging drift. |
| NEG-CAP-09 | `TechnicalEvidenceStore` rejects ledger-shaped objects before archive/journal I/O; both technical roots remain empty in the rejection fixture. |
| NEG-CAP-10 | After executing the S1 graph, no future execution/Paper/Risk/strategy/formal-replay module is loaded; the structural checker separately validates the source/import inventory and adversarial mutations. |

## Limits

- The evidence is scoped to the integrated passive S1 fixture graph; it is not proof against arbitrary hostile mutation of the Python interpreter or filesystem.
- No real provider, broker SDK, account, trading credential, financial ledger, Paper path or Live path participates in these tests.
- MT5 remains isolated in its import-only spike; DD-60 remains undecided.
- `SECURITY_DIFF_SCAN = NOT_EXECUTED` because the available official scan interface still requires a Git-local target incompatible with the remote-only mandate.
- Passing NEG-CAP evidence does not itself grant `SPRINT1_ACCEPTANCE`.
