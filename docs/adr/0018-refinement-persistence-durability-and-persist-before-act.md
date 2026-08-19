# ADR 0018 — Refinamento de persistência, durabilidade e persist-before-act

- **Status:** Aceita
- **Data:** 2026-08-19
- **Refina e substitui parcialmente:** ADR 0009 — Persistência, journal de auditoria e snapshots

## Contexto

O ADR 0009 separou archive, operational/audit journal e snapshots e rejeitou event sourcing indiscriminado. O Sprint 0D fechou as guarantees semânticas necessárias para recovery e para side effects econômicos.

## Decisão / refinamento

- `EvidenceArchive`, `AuditJournal` e `SnapshotMaterialization` permanecem persistence planes distintos. Persistir um artifact não transfere ao storage ownership sobre o domínio.
- EvidenceArchive preserva evidência/raw/artifacts/lineage; archived não significa admitted, canonical ou current.
- AuditJournal preserva história operacional/auditável crítica. `AuditJournal` é distinto do `Ledger`, que permanece financeiro.
- Snapshot é projeção derivada e acelerador de recovery; nunca substitui nem corrige journal/fatos.
- Identidade lógica de persistência é distinta de row ID, file offset, object key, stream offset ou location física. Copy/migration/replication do mesmo logical record não cria novo domain artifact.
- Para qualquer side effect capaz de criar ou ampliar commitment econômico, todos os logical records safety-critical exigidos pela policy devem satisfazer seus `DurabilityRequirement`s antes do início do dispatch externo. Persistência crítica indisponível ou incerta bloqueia novo side effect econômico.
- Esse persist-before-act é um hard durability gate interno e não cria transação ACID distribuída com broker/venue; outcome externo desconhecido continua possível e exige idempotência/reconciliation.
- Missing persistence receipt não prova ausência do logical record. Outcome de write desconhecido deve ser resolvido por logical persistence identity antes de repetir write crítico quando duplicação for material.
- Grupos semanticamente atômicos, como `LedgerTransaction → 1..N LedgerPostings`, não podem ser recuperados parcialmente e tratados silenciosamente como completos.

## Invariantes

- Durability, integrity, availability e continuity são dimensões distintas.
- `JournalPosition` possui scope explícito e não substitui event time, source sequence ou causation.
- Snapshot válido não autoriza automaticamente apagar journal anterior.
- Replay/recovery de journal não redispara side effects externos.

## Consequências

A expressão histórica “persistir antes de agir sempre que possível” é substituída, para novos commitments econômicos, pelo gate obrigatório acima. A inexistência de ACID distribuído com infraestrutura externa permanece preservada.

## Decisões deliberadamente adiadas

Permanecem adiados: banco, SQL/NoSQL, filesystem/object storage, Kafka, WAL, fsync, replication/quorum, transaction mechanism, serialization, snapshot format, TTL/retention e cloud provider.

## Relação com outros ADRs

Refina ADR 0009 e suporta ADRs 0010/0019, 0014/0022 e 0021.
