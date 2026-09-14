# S1 — Point-in-time instrument discovery

- Status: implementation detail under DD-58 for RQM-040 / AC-01.
- Scope: passive discovery within an immutable InstrumentRegistry snapshot.
- Authority: 0F-E RQM-020/RQM-040, AC-01/AC-02 and 0E-B B-HQI-16/QPI-02.

## Decision

Sprint 1 discovery is a causal query over already evidenced registry mappings. It does **not** select a live market-data provider and does not implement rollover policy.

A discovery query must explicitly provide:

- `InstrumentFamilyId`;
- provider label;
- capture/reference scope;
- `valid_at` point in time;
- `knowledge_cutoff`.

A mapping is discoverable only when it matches family/provider/scope, is valid at `valid_at`, and was already known by `knowledge_cutoff`. All admissible mappings are returned in immutable registry order. Overlapping contracts remain multiple results; discovery never ranks, promotes or silently chooses one contract.

Resolution of an exact `ProviderInstrumentRef` remains the separate `InstrumentRegistry.resolve` operation. Discovery therefore answers “which evidenced contracts were admissible in this family/scope at this point in time?”, while resolution answers “what canonical identity does this exact provider reference resolve to?”.

## DD-60 boundary

This decision does not select a concrete real provider, vendor, SDK or connection. Fixture/provider labels are test evidence only. DD-60 remains a separate governance decision whose trigger is a concrete provider/real-adapter path; no such selection is made here.

## Limits

- No liquidity ranking, front-contract choice or rollover algorithm.
- No network discovery, subscription or authentication.
- No executable-price claim, order path or economic authority.
- No B3 calendar policy is introduced.
