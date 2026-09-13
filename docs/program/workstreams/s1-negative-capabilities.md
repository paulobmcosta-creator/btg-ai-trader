# S1 — Negative-capability verification plan

- Status: DRAFT_TEST_PLAN; ASSEMBLY_CONTRACT_PENDING; EXECUTION_NOT_STARTED.
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
