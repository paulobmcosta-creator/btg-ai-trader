# Sprint 1 — secure BTG first-lab runner

## Purpose

This increment prepares a controlled GitHub-hosted execution path for the already-integrated read-only BTG Data Services first-lab harness. It does **not** run a real session by itself and does not add any trading/account/order capability.

The repository is public. Raw provider evidence therefore MUST NOT be uploaded as a plaintext Actions artifact. The runner encrypts technical evidence before any artifact upload and publishes only ciphertext plus its SHA-256 checksum.

## Trigger model

The workflow `.github/workflows/btg-first-lab-secure.yml` does not use `pull_request` or `workflow_dispatch`. It can execute only on a push that changes:

```text
config/btg-first-lab-request.json
```

on the dedicated branch:

```text
lab/btg-s1-first-capture
```

The laboratory branch is created from the integrated Sprint 1 branch only when an actual controlled run is authorized. Merely integrating the workflow into `sprint/1-market-observer` does not trigger a provider connection.

## Request contract

The run branch must contain exactly one bounded request object with only these fields:

```json
{
  "schema": 1,
  "instrument": "<EXACT_WIN_CONTRACT>",
  "capture_scope": "first-lab",
  "code_revision": "<CURRENT_40_CHAR_SPRINT1_SHA>",
  "discovery_seconds": 10,
  "capture_seconds": 60
}
```

The example above uses documentation placeholders only. No concrete WIN contract is a repository default.

The workflow validates that:

- the instrument matches the bounded concrete WIN format;
- the request contains no extra fields;
- the capture windows remain within the approved limits;
- `code_revision` is a full lowercase 40-character Git SHA;
- `code_revision` equals the current remote head of `sprint/1-market-observer` at execution time.

If Sprint 1 moves after a request is prepared, the run fails closed instead of silently executing stale code.

After validating the request, the workflow checks out the exact approved Sprint 1 SHA and verifies a clean execution tree. The run-request commit itself is therefore not misrepresented as the application code revision.

## External secrets

Two values must be provisioned outside the repository and outside chat as GitHub Actions secrets:

```text
BTG_DATASERVICES_API_KEY
BTG_EVIDENCE_PASSPHRASE
```

`BTG_DATASERVICES_API_KEY` is the read-only Data Services credential already governed by DD-43.

`BTG_EVIDENCE_PASSPHRASE` is a separate strong single-line secret used only to encrypt the technical evidence package. It must not reuse the API key.

The workflow fails before any provider connection if either secret is unavailable. The API key is injected only into the capture step. The evidence passphrase is injected only into the preflight/encryption steps. Neither value is written to the request file, command-line arguments, run configuration or artifact.

## Evidence handling

The integrated harness first writes canonical EvidenceArchive/AuditJournal records into the ephemeral runner filesystem. The workflow then:

1. packages the evidence directory;
2. encrypts it symmetrically with GnuPG/AES-256 using `BTG_EVIDENCE_PASSPHRASE` from standard input;
3. computes SHA-256 over the encrypted package;
4. deletes the plaintext archive and raw evidence directory from the workspace;
5. uploads only the `.gpg` ciphertext and `.sha256` checksum through a SHA-pinned `actions/upload-artifact` action;
6. retains the encrypted artifact for 14 days.

Capture failures are not converted to success. When a failed provider session produced technical evidence, the workflow still attempts to encrypt and preserve that evidence, and the final job remains failed.

## Safety properties

```text
TRIGGER = EXPLICIT_DEDICATED_BRANCH_REQUEST_ONLY
PROVIDER = BTG_SOLUTIONS_DATA_SERVICES
MARKET_DATA_ONLY = YES
API_KEY_IN_REPOSITORY = NO
API_KEY_IN_CHAT = NO
RAW_PUBLIC_ARTIFACT = NO
ENCRYPTED_ARTIFACT_ONLY = YES
ORDER_API = ABSENT
BROKER_ACCOUNT = ABSENT
TRADING_CREDENTIAL = ABSENT
REAL_MONEY_AUTHORITY = ABSENT
AUTO_ROLLOVER = NO
AUTO_FALLBACK = NO
VENDOR_AUTO_RECONNECT = NO
```

Integrating this runner does not close the real-provider gate. That gate closes only after an actual authorized run is executed, its encrypted evidence is recovered and reviewed, and the resulting evidence is reconciled into the Sprint 1 RQM/XC checkpoint.
