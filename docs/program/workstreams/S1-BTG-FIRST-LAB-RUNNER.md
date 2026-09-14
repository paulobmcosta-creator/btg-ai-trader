# Sprint 1 — secure BTG first-lab runner

## Purpose

This increment prepares a controlled GitHub-hosted execution path for the already-integrated read-only BTG Data Services first-lab harness. It does **not** run a real session by itself and does not add any trading/account/order capability.

The repository is public. Raw provider evidence therefore MUST NOT be uploaded as a plaintext Actions artifact. The runner encrypts technical evidence before artifact upload and exposes only ciphertext, checksum and a deliberately sanitized technical summary that contains no raw trade payload or price.

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

## Protected GitHub Environment

The capture job is bound to the GitHub Environment:

```text
btg-readonly-lab
```

Before any real run, that Environment must be configured in GitHub with deployment protection for the laboratory branch and, where the repository plan/UI permits it, a required reviewer. The two laboratory secrets described below must be stored as **Environment secrets**, not repository-level or organization-level secrets.

Do not create repository/org Actions secrets under the laboratory secret names. The purpose of the dedicated Environment is to keep real provider credentials behind an explicit deployment boundary in this public repository.

Environment configuration is an external administrative control; it is not encoded by a repository commit and is not treated as present merely because the workflow declares `environment: btg-readonly-lab`.

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

## External Environment secrets

Exactly two values are required in the protected `btg-readonly-lab` Environment and must be provisioned outside the repository and outside chat:

```text
BTG_LAB_DATASERVICES_API_KEY
BTG_LAB_EVIDENCE_PASSPHRASE
```

`BTG_LAB_DATASERVICES_API_KEY` is mapped only at runtime to the process variable `BTG_DATASERVICES_API_KEY` required by the integrated read-only harness. It remains governed by DD-43.

`BTG_LAB_EVIDENCE_PASSPHRASE` is a separate strong single-line secret used only to encrypt the technical evidence package. It must not reuse the API key and must have at least 24 characters.

The workflow fails before any provider connection if either secret is unavailable. The API key is injected only into the preflight/capture context needed for validation and provider authentication; the evidence passphrase is used only by preflight/encryption. Neither value is written to the request file, command-line arguments, run configuration, sanitized summary or artifact contents.

## Evidence handling

The integrated harness first writes canonical EvidenceArchive/AuditJournal records into the ephemeral runner filesystem. After a successful capture, the workflow derives a sanitized summary containing only:

- provider identifier;
- explicit instrument candidate;
- exact code revision;
- RunId;
- confirmed trade-frame count;
- non-trade post-subscription message count;
- evidence/journal record counts;
- `trading_capability=false`.

It does not publish prices, quantities, provider raw payloads or the API key.

The workflow then:

1. packages the raw evidence directory;
2. encrypts it symmetrically with GnuPG/AES-256 using `BTG_LAB_EVIDENCE_PASSPHRASE` from standard input;
3. computes SHA-256 over the encrypted package;
4. deletes the plaintext archive and raw evidence directory from the workspace;
5. uploads the `.gpg` ciphertext, `.sha256` checksum and sanitized JSON summary through a SHA-pinned `actions/upload-artifact` action;
6. also writes the sanitized summary to the Actions step summary for remote adjudication;
7. retains the protected artifact for 14 days.

Capture failures are not converted to success. When a failed provider session produced technical evidence, the workflow still attempts to encrypt and preserve that raw evidence. The final job remains failed. A successful final job additionally requires the sanitized summary, encrypted evidence and artifact upload all to succeed.

## Safety properties

```text
TRIGGER = EXPLICIT_DEDICATED_BRANCH_REQUEST_ONLY
ENVIRONMENT = btg-readonly-lab
ENVIRONMENT_SECRETS_ONLY_BY_GOVERNANCE = YES
PROVIDER = BTG_SOLUTIONS_DATA_SERVICES
MARKET_DATA_ONLY = YES
API_KEY_IN_REPOSITORY = NO
API_KEY_IN_CHAT = NO
RAW_PUBLIC_ARTIFACT = NO
ENCRYPTED_RAW_ARTIFACT = YES
SANITIZED_NON_MARKET_PAYLOAD_SUMMARY = YES
ORDER_API = ABSENT
BROKER_ACCOUNT = ABSENT
TRADING_CREDENTIAL = ABSENT
REAL_MONEY_AUTHORITY = ABSENT
AUTO_ROLLOVER = NO
AUTO_FALLBACK = NO
VENDOR_AUTO_RECONNECT = NO
```

Integrating this runner does not close the real-provider gate. That gate closes only after the protected Environment is actually configured, an authorized run is executed, its evidence is reviewed, and the resulting evidence is reconciled into the Sprint 1 RQM/XC checkpoint.
