# Foundation integrity — remote regression guard

Status: implementation proposed; remote execution pending.
Base: 3bbdcefee96a9d3662112cac97feeb86d7cc7093 (remote CI workstream).
Scope: read-only verification of the approved snapshot bytes and S1-EC table structure.

The guard pins the five verified blobs for 0F-B, its portable companion, 0F-E, 0F-F and TRACEABILITY to the inspected baseline. Any change, missing file or invalid UTF-8 fails. A legitimate future normative revision must update the pin only through its explicit reviewed decision, never by accepting arbitrary current content.

It separately checks all 118 normalized clause rows (including duplicates), the eight clause-type counts, all 41 RQM rows, exact membership of the 26 DDs, and all 20 NC / 10 NEG-CAP obligation rows. Twenty-eight decision-gate clauses are not mistaken for 26 decisions.

Mutation tests exercise duplicated and removed clauses, changed type, replaced DD identity with unchanged cardinality, changed byte identity, and missing artifacts. Tests never modify canonical files.

This verifies document integrity, not RQM implementation, security, negative capability behavior or acceptance. No official Codex Security result or gate is inferred. CI adds a seventh foundation job and includes the script in typing/compilation. All execution occurs on GitHub-hosted runners.

Validation: NOT_EXECUTED until the exact head has remote run evidence. No runtime dependencies, Observer changes, secrets or financial capability.
