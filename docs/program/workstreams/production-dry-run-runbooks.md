# S12-A — Architecture and dry-run runbooks

- Status: SPECULATIVE; documentation ready for review, not an approved deployment design.
- Authority: autonomous mandate of 2026-09-13; remote-only engineering.
- Baseline: 183203307169f41ce40e035fe19f1d0a570e3e16.
- Checkpoint authority: PROGRAM_EXECUTION.md on s1/00-post-merge-authorization.
- Dependencies for this proposal: Foundation ADRs 0010, 0018, 0019, 0020 and 0021. Functional deployment depends on implemented and reviewed runtime, persistence, recovery, telemetry and capability checks.
- Decisions: no cloud vendor, region, machine shape, OS image, orchestrator, database, secret manager, service identity, timeout, SLO, RPO or RTO is selected. Material physical decisions remain subject to their deferred-decision triggers and ADRs before implementation.

## Logical boundary

The proposed deployment units preserve the modular monolith: a passive capture/runtime process, technical evidence storage and a telemetry reader. Research and future model training use separate resources; neither may command capture or acquire financial authority through telemetry. These are logical responsibilities, not a selection of separate network services or new infrastructure.

An eventual fixture dry-run binds only deterministic fixtures, an isolated technical archive, explicit clocks and an evidence sink. It contains no broker client, account, external financial transport or credential source. Data described as live in a fixture remains synthetic evidence. The MT5 import spike is separate and supplies no runtime provider admission.

Readiness is assessed per capability. A process reporting RUNNING or emitting heartbeats proves neither usable data nor recovery continuity. SAFE_HALT blocks new commitment conceptually and never instructs flatten/cancel or any other economic action in this runbook. No authority to unlatch is granted here.

## Promotion evidence contract

Each proposed deployment record must identify an immutable code revision, exact dependency lock/artifact digest, configuration artifact and its content digest, fixture/input boundary, new RunId, parent relation when restarting, schemas and required capabilities. A hash-shaped string is not proof: the future executable verifier must recompute bytes and validate referenced artifacts.

Evidence records must separate:
- intended configuration, observed effective configuration and unsupported/unknown values;
- test plan, executed steps, raw observations and assessed outcome;
- procedural completion, recovery quality, reconciliation quality and readiness;
- engineering dry-run, formal Paper evidence and authorization for any future financial activity.

A missing capability, artifact, continuity proof or trustworthy timestamp is a failed prerequisite for the capability it gates. A dry-run success does not promote another sprint or satisfy Gate G.

## Dry-run scenarios to implement after upstream contracts stabilize

All scenarios are fixtures in a disposable internal CI environment. They are specifications, not executed evidence.

| ID | Injected condition | Required observable result | Upstream evidence needed |
|---|---|---|---|
| DR-01 | Start with complete fixture config | New RunId and immutable manifest; independent readiness assessment | S1-C config/manifest implementation |
| DR-02 | Missing/unknown required config or capability | Startup prerequisite rejected; diagnostic references missing field, no default grants | Config schema and capability guard |
| DR-03 | Heartbeat fresh but market data stale | Liveness and data freshness reported separately; passive data capability blocked | S1 health and ingestion integration |
| DR-04 | Finite ingress queue full | Explicit backpressure result and count; no silent drop or overwrite | S1-D transport and overflow contract |
| DR-05 | Corrupt event | Raw bytes retained, quarantine reason and reference recorded; unrelated valid input isolated | Admission/quarantine and archive |
| DR-06 | Archive/journal write failure | Failure observable; dependent progress not falsely acknowledged | S1-E failure and durability contract |
| DR-07 | Restart after interrupted write | New RunId and relation; incomplete artifacts identified; no optimistic continuity | Persistence and recovery contracts |
| DR-08 | Missing/corrupt journal segment | Scope-specific recovery assessment insufficient; no automatic READY | S9 recovery and S1-E journal |
| DR-09 | Metrics normalize after latched fault | Posture remains restricted until explicit applicable authority and prerequisites | S9 unlatch policy, still deferred |
| DR-10 | Unknown external outcome fixture | Unknown retained, no blind retry or inferred no-effect; simulated obligations not erased by restart | Future recovery/commitment contracts |
| DR-11 | Telemetry unavailable or stale | Dashboard distinguishes unknown/stale from healthy; no control authority introduced | S10 telemetry contract |
| DR-12 | Rollback to earlier code artifact | Verify schema compatibility and immutable input boundary before a new run; preserve journal/evidence | Versioning and recovery compatibility policy |

DR-10 is a future isolated runtime fixture specification; it adds no execution model or financial capability to S1. No scenario may be implemented by connecting to a real account or user terminal.

## Startup runbook specification

1. Select the immutable candidate and record the exact evidence scope. Reject an unreviewed or changed HEAD for promotion.
2. Verify artifact/config/input bytes against recorded digests. Missing evidence remains unknown.
3. Inspect the runtime capability set. For this mandate it must have no financial route and no trading credential source.
4. Allocate a new RunId and record context before dependent operations. A previous RunId is never reused.
5. Reconstruct only scopes with demonstrated journal/snapshot continuity. Preserve unresolved scope assessments.
6. Perform any reconciliation only within an explicit observation boundary. Consistency outside it is not claimed.
7. Assess readiness independently. Successful startup, recovery or reconciliation alone cannot grant it.
8. Persist test observations and limitations. A procedure ending does not mean PASS.

## Incident and rollback runbook specification

Record the triggering sample, evaluated policy, affected capability and last known evidence boundary. Preserve raw evidence; do not rewrite history to make dashboards appear healthy. Stop dependent progress when its prerequisite fails. Escalation to a more restrictive posture is permitted by the applicable policy; metric recovery alone cannot remove a latch.

Rollback selects an earlier reviewed code artifact, checks schema/input compatibility, creates a new Run and records its relation. It does not delete evidence, restore an old identity or roll back externally committed obligations. A fixture of an unknown external outcome remains unresolved until sufficient scoped evidence exists. This mandate supplies no authority to query, cancel, adjust or otherwise control a real financial obligation.

## Exit and handoff

This document is complete as a proposal when independently reviewed for consistency with the cited ADRs. Executable dry-run acceptance requires implemented upstreams, exact SHA CI results for DR-01..12, artifact readback, failure-injection results and explicit unresolved-scope reporting. Formal production architecture approval, deployment approval and financial activation are separate gates.

CURRENT_EXECUTED_SCENARIOS = NONE
DRY_RUN_EXECUTION = NOT_EXECUTED
PROVISIONING = NOT_EXECUTED
DEPLOYMENT = NOT_EXECUTED
FINANCIAL_ACTIVATION = FORBIDDEN_IN_THIS_MANDATE
