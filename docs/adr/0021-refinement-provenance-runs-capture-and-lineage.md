# ADR 0021 — Refinamento de provenance, Runs, capture e lineage

- **Status:** Aceita
- **Data:** 2026-08-19
- **Refina:** ADR 0013 — Observabilidade, proveniência e rastreabilidade de decisões

## Contexto

O ADR 0013 estabeleceu versionamento e `run_id` para rastreabilidade de decisões. O Sprint 0D definiu a identidade de Run, distinguiu capture/processamento/derivação e impediu que fatos externos sejam apropriados por um Run posterior.

## Decisão / refinamento

- `RunId` identifica uma execução computacional concreta e delimitada. Restart sempre cria novo `RunId`.
- Continuidade entre Runs é registrada por `RunRelation` tipada, como `RESUMES_FROM`; Run não é `OperationalSession` nem `Experiment`.
- `RunManifest` é descriptor imutável do contexto resolvido no início do Run; terminalidade é registrada por `RunCompletionRecord` separado.
- Fatos externos/históricos não exigem `run_id` intrínseco. Um fato pode referenciar `CaptureContext`, que registra o Run de captura, sem alterar a identidade do fato.
- `ProcessingReceipt` relaciona artifact × run × component/stage e permite que o mesmo artifact seja processado em múltiplos Runs sem mutação.
- `ArtifactLineageRecord` é separado de ProcessingReceipt e representa transformação/derivação N→M, com input/output roles quando necessários.
- Permanecem semanticamente distintos: evidence refs, derivation lineage, causation, correlation e processing provenance.
- Reprocessing por novo conhecimento, dados corrigidos ou nova policy cria novo Run e novos artifacts run-generated. Outputs históricos não são reescritos; supersession analítica é relação explícita.
- Mutable aliases (`current`, `latest`, `production`) não constituem provenance de versão suficiente; ao uso, devem resolver para referências imutáveis ou permanecer explicitamente unresolved.

## Invariantes

- Restart não reutiliza `RunId` anterior.
- Run boundary não encerra economic obligations.
- Artifact não deriva de si mesmo e lineage derivacional deve ser acíclica quando semanticamente causal.
- External artifact pode ter múltiplos ProcessingReceipts sem adquirir nova identidade.
- Provenance nunca materializa secret values; somente safe references quando necessárias.

## Consequências

Auditability, replayability, determinism e reproducibility podem ser avaliados separadamente sem prometer reprodução perfeita de fenômenos externos LIVE.

## Decisões deliberadamente adiadas

Permanecem adiados: formato físico de manifest, Git/hash/SemVer como representação universal, artifact registry, MLflow, storage, serialization, environment packaging e mecanismo de secret references.

## Relação com outros ADRs

Refina ADR 0013 e complementa ADRs 0015, 0017, 0018, 0019 e 0022.
