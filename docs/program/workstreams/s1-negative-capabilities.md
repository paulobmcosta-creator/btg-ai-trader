# S1 — Negative-capability verification plan

- Status: STRUCTURAL_IMPLEMENTATION_AUTHORIZED; COMPOSITION_API_PENDING; NEG_RUNTIME_NOT_EXECUTED.
- Authority: bounded CONSOLIDATE_S1 task under the remote execution mandate.
- Planning base: `d22e73f10d1e0ca21cbd7a0af90b94719debad44`.
- Normative sources: [0F-E](../../foundation/0F-E_sprint1_entry_contract.md) §§7, 9, 14, 15, 20; NC-01..20, NEG-CAP-01..10, XC-01..11.
- This document precedes implementation. It is neither a passing test suite nor a Security Diff Scan.

## Objective and limits

Verify the concrete assembled Observer's negative capabilities through a combination of source inventory, AST/import closure, strict configuration, actual runtime fixtures and typed technical persistence rejection. Mere absence of text such as an order method name is insufficient. Tests must exercise real assembly entrypoints and reject unsupported dependency/configuration paths before executing them.

A passing Foundation guard or a passing component test does not prove the assembled graph safe. Until the coordinator supplies the exact assembly contract and source snapshot, runtime NEG-CAP evidence remains NOT_EXECUTED; tests must not manufacture green results through skips, empty parameter sets or absent modules.

All test execution is on GitHub-hosted runners using temporary fixture directories. No physical user checkout, broker account, real trading credential, production service, financial effect or main promotion is involved.

## Scope manifest and independent static checks

The implementation will inventory the exact runtime modules, supported entrypoints, declared dependencies, config schema and reviewed blob/content identities of the assembled S1 graph. The manifest covers all production Python files and relevant packaging/entrypoint/config declarations, not just selected favorable files. CI records the actual reviewed HEAD separately; the manifest does not attempt a self-referential commit hash.

Unexpected files, unlisted dependencies, unapproved imports, unresolved import targets or entrypoints fail closed. Observer imports must not reach research/replay, strategy, risk, execution, Paper or financial accounting. Standard-library/provider boundaries require explicit reviewed allowances; an import of a broad SDK is not treated as safe merely because its name is allowed.

An AST pass resolves import aliases, rejects wildcard/dynamic imports, eval/exec and unbounded plugin/callback wiring. Reflection is assessed against concrete source constructs: existing finite field-validation loops are not blanket banned, and arbitrary getattr-based capability routing is not accepted. This is a scoped engineering check, not a universal Python interpreter or formal security proof.

Adversarial AST/import fixtures must test the semantic checker independently of file pins: mutation fixtures re-pin their own synthetic bytes so a failure cannot be attributed only to a stale hash. Separate tests verify that production inventory/blob drift fails before a purported unchanged-snapshot result can be issued. Fixtures never modify canonical repository snapshots.

## Required runtime test cases

| Test ID | Concrete behavior and evidence | Assembly prerequisite |
|---|---|---|
| NEG-CAP-01 | Execute Tick/Candle fixtures through assembly; validate the closed observation/report output types and absence of operational execution authority. Attempt unsupported executor/conversion injection at real boundaries and verify rejection before invocation. Do not invent a functioning OrderIntent implementation just to claim it was tested. | Assembly entrypoint, result schema, dependency admission contract. |
| NEG-CAP-02 | Supply inert executor-shaped objects, misleading duck types and unsupported subclasses to every dependency slot; verify rejection before any callback/method can run. No generic object/plugin executor slot may bypass the check. | Exact accepted provider/storage/health types and DI slots. |
| NEG-CAP-03 | Run a nontrivial observation fixture through provider/ingestion/admission and technical persistence. Record allowed calls and verify financial sentinels remain untouched, including failure paths. Combine with closed import/call boundary evidence. | Full technical graph, deterministic provider fixture mechanism. |
| NEG-CAP-04 | Reject unknown config keys, execution-like flags and alternate wiring requests through the real strict parser/constructor; demonstrate env/config changes cannot add execution authority. Valid read-only config still runs. | Config schema and entrypoint parsing contract. |
| NEG-CAP-05 | Complete the assembled fixture without trading environment variables. Use inert environment-read tripwires to detect consumption of prohibited credential keys; synthetic values are non-secret test markers. Credential swap does not change code capability. | Concrete environment/config read boundary; authentication contract if triggered. |
| NEG-CAP-06 | Inspect the provider/service surface and actual import closure; unsupported execution methods/SDK escapes are unavailable through the assembled API. Inert executor-shaped objects are rejected. Any dual-use SDK needs all eleven 0F-E §9 conditions, not just this test's name. | Concrete selected provider and exposed service object. |
| NEG-CAP-07 | Trigger stale/timeout/SAFE_HALT paths using explicit fixture time. Verify no financial callback or auto-flatten, no automatic unlatch, and the documented passive readiness result. | Health/admission composition and deterministic time injection. |
| NEG-CAP-08 | Inspect packaging/CLI/UI/admin entrypoints structurally. Exercise declared parsers with unsupported trading commands/parameters and require rejection. If a surface is absent, inventory proves absence; nonexistent CLI tests do not count as runtime execution. | Complete declared entrypoint inventory. |
| NEG-CAP-09 | Pass an inert ledger-shaped request to both real technical append APIs and require typed rejection before I/O; verify a separate financial sentinel directory is unchanged during the full fixture and failure paths. No real ledger implementation is introduced. | EvidenceArchive/AuditJournal types, controlled separate temporary roots. |
| NEG-CAP-10 | Verify the complete S1 source/dependency/import inventory excludes Paper execution, formal replay and future financial wiring. Mutated inventories/import graphs introducing those paths must fail, including alias/dynamic routing attempts. | Exact assembled S1 production source inventory. |

## Cross-cutting evidence

Each result must map its NEG-CAP ID to concrete tests, runtime paths, source identities, CI HEAD and outcomes. Keep source inventory evidence, AST evidence, fixture execution, reviewed limitations and official security-scanning status separate.

The matrix addresses all 20 negative capabilities through combined evidence; no one method or ten passing test names establish them alone. In particular, financial commitment/account mutation and hidden routing require the closed composed graph plus runtime boundary tests. Arbitrary hostile mutation of the Python process or filesystem is not claimed to be impossible.

XC-05/06/07/08/11 receive only the evidence actually produced by the assembled suite. XC-01..04, XC-09/10, the 41 RQMs, provider qualification, capture provenance and independent reviews remain separate acceptance obligations. This plan does not set Sprint 1 acceptance to PASS.

## Required coordinator inputs before implementation

1. Immutable assembly base/head and target PR branch.
2. Composition entrypoint and exact constructor/function signatures.
3. Strict configuration parser/types, supported keys and declared CLI/entrypoints.
4. Accepted provider/storage/health inputs and fixture substitution mechanism, with no financial callback slot.
5. Output/report schemas and safe-readiness/failure behavior.
6. Complete production module/dependency/config inventory and provider scope constraints.

Once supplied, reconcile the plan against the actual graph, record any material decision before dependent code, implement tests and the bounded static checker, run CI on the exact HEAD, investigate failures, and request independent review. No merge is authorized by this document.

## Structural implementation decision before code

The coordinator authorized the structural subset on assembly `37ff91bc9a86269cd68ddf5537b474f49b7d0510`. PR25 is reanchored on that assembly with ancestry retained. The reviewed production inventory initially comprises the supplied source tree, config files, pyproject.toml and .python-version. Runtime composition is not yet present and its tests remain explicitly pending.

The checker will combine exact Git blob pins, AST import closure and reviewed stdlib member allowances, rejection of dynamic import/evaluation and capability-routing reflection, packaging/runtime-dependency restrictions, and independently re-pinned adversarial fixture trees. Existing getattr field validation is allowed only for explicit finite literal field sets, never as an invoked callback. None of these checks is a general interpreter or proof against arbitrary hostile in-process mutation.

An additional possible-secret heuristic scans runtime/config/workflow text and AST literal assignments for credential-shaped values and private-key markers. Its findings contain only file/line/rule, never the suspected value. Planted synthetic test strings verify detection and non-disclosure. This heuristic is separate from the principal NEG-CAP checks and from an official Security scan; false negatives and false positives remain possible.

An explicit CI boundary job will report structural inventory/AST, packaging/config and possible-secret results on the exact checked-out HEAD. It must also report NEG_RUNTIME_NOT_EXECUTED until real composition tests exist. Passing this structural subset does not set the ten runtime obligations, twenty NCs or Sprint 1 gate to PASS.

## Review correction decision before code

Independent ordinary implementation review of 53563fe3 identified imported-module copying/container escape and invocation through aliases of a finite-field reflection result. The bounded checker will reject external module objects escaping their directly reviewed member access, and reflected values escaping reviewed scalar validation contexts. Direct approved reflection assignments require a single local name; subsequent uses are limited to scalar comparisons and direct type/validation checks, preventing copied aliases, container storage and returned callbacks. Re-pinned fixtures must exercise both paths independently of source identity pins. This remains a restricted syntax policy, not general Python data-flow interpretation.

The first CI also found an overly broad compile attribute rejection: re.compile is an already-declared regular-expression operation and will be distinguished from dynamic builtin compile by resolved import identity. Lint/type defects will be corrected without changing runtime production bytes or weakening inventory checks. Runtime composition tests remain pending.

## Composition integration decision before dependent tests

Composition candidate `ad7835c94dd5203bab485cc71533f4636beec8e6` has been read and its Remote Python CI `34788398634` completed successfully. This increment incorporates that exact upstream through explicit ancestry. The production inventory is re-established from the incorporated tree, including composition.py and the technical OBSERVATION_RECORDED enum extension; no source pin is silently relaxed.

The coordinator approved a narrow trusted-reviewed-serializer exception for the complete ASTs of module-level `composition._wire` and `ObserverConfig.canonical_bytes`. Their entire reviewed syntax, exact lexical owner, local explicit model tuple, guards, recursive calls and body are matched to stored reviewed templates (position-free AST fingerprints). This is an explicitly trusted reviewed serializer, not an inference that arbitrary reflection is safe. Aliasing, rebinding, shadowing or duplicate definitions of these protected bindings are rejected. A changed model tuple, guard, body, owner, or new getattr outside those two complete functions must fail even when a synthetic manifest is re-pinned. Ordinary config validation retains a separate finite literal field allowlist. No future arbitrary dataclass/plugin serializer is authorized.

Runtime tests exercise the real exact-type FixtureObserver, ObserverConfig, FixtureMarketDataSource, InstrumentRegistry and TechnicalEvidenceStore. Test-only fabricated subclasses/duck types, synthetic environment tripwires, technical filesystem fault injection and a separate inert financial sentinel provide negative evidence; no financial implementation is added. Each accepted dependency slot is tested separately. Tick/Candle, quarantine, failed publication, stale/timeout/UNKNOWN health, strict config, unsupported constructor/retry parameters and both typed technical append APIs receive executed tests. The inventory/AST check remains necessary alongside those fixtures.

The manifest status SCOPED_TESTS_IMPLEMENTED only declares that actual tests have been added. CI must execute them on its exact HEAD before evidence can be reported. CLI absence is shown by package/source inventory, not by claiming a nonexistent command ran. Runtime fixture code pins are caller-declared synthetic identities; the CI checkout SHA is the actual source identity. No complete 20-NC, 11-XC, RQM, official Security or Sprint 1 acceptance claim is introduced.
