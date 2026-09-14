# Security Policy

## Scope

BTG AI Trader is an experimental research and engineering repository. No production trading service, real-money execution path, broker order submission, trading credential, or production deployment is authorized by the current project state.

Security reports are nevertheless welcome for repository code, workflows, dependency handling, credential exposure, supply-chain behavior, unsafe capability escalation, or any defect that could invalidate the documented safety boundaries.

## Reporting a vulnerability

Do **not** publish real credentials, tokens, account identifiers, private keys, exploit payloads containing secrets, or other sensitive material in a public issue, pull request, discussion, commit, or Actions log.

Preferred reporting path after public visibility:

1. If GitHub Private Vulnerability Reporting is enabled, use the repository's **Security → Report a vulnerability** flow.
2. If that private channel is unavailable, open a public issue containing only a non-sensitive summary and request a private follow-up. Do not include exploit details or secret values in the public issue.

## Repository secrets

Real secrets must never be committed. Local credentials and environment-specific configuration must remain outside version control. The repository's `.gitignore`, CI boundary checks, and project governance are defense-in-depth controls and are not substitutes for secret rotation if a credential is ever exposed.

If a real credential is suspected to have been committed or logged, treat it as compromised immediately: revoke or rotate it first, then remediate repository history and evidence as appropriate.

## Financial capability boundary

A security finding must not be "fixed" by introducing or enabling trading authority. In particular, no remediation may silently add broker order submission, modification, cancellation, real-money execution, trading credentials, strategy-to-broker shortcuts, Risk bypass, or other financial capability outside the formally authorized project gates.

## Disclosure status

Public repository visibility is not a production-readiness signal, financial authorization, or assurance that every future branch is safe for deployment. Branches and pull requests may contain explicitly speculative work and must be interpreted according to their documented sprint/gate status.
