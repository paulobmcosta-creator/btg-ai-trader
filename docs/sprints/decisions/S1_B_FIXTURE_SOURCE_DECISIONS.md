# S1-B fixture source increment

- State: decisions recorded before code under the autonomous mandate of 2026-09-13.
- Base: PR12 a594a85cc41efab773e5d56d68560f3d281eda19.
- Scope: finite deterministic fake/test source of raw frames; no real provider, market-data replay engine or scheduler.
- Norms: ADR0006/0012, 0F-E deliverable DELIV-S1-03 and replay boundary section18, existing S1-B DD33 decisions.

DD33 extension: RawMarketDataSource specializes ProviderMetadata with synchronous read_next returning one RawFrame or None for fixture exhaustion. It has no universal authentication, network, reconnect or execution methods.

A RawFrame preserves exact bytes, ProviderInstrumentRef and declared channel kind TICK/CANDLE. Bytes may be malformed domain data and remain untouched for future admission/quarantine. A channel label is not a claim that its payload is valid. It supplies no fabricated EventId, timestamp, RunId, sequence or trading authority.

FixtureMarketDataSource receives an explicit ProviderCapabilities descriptor and finite iterable of frames, copied to a tuple. Every frame must match provider/capture scope, and its channel requires declared SUPPORTED capability. UNKNOWN does not grant support. Different symbols within the same scope are legal. Supplied order and repeated frames are preserved; no deduplication or historical ordering is inferred.

read_next consumes one frame, returns the original immutable frame and eventually None repeatedly. Consumer clock/context, admission, quarantine, finite ingress queue/backpressure, subscriptions and reconnect remain separate contracts. Callers integrating a queue must retain a frame when its offer is rejected; another read is not an acknowledgement of admission. Fixture exhaustion does not imply healthy feed or missing-volume zero.

DD60 remains undecided: this is a test source, not provider admission. DD02 is not selected because the raw bytes have no serializer/parser here. DD22/54/57/59/62 are not implemented by this fixture. No callable injection, environment reader, SDK, side effect, timing control or production feed is introduced.

Required tests: scope/capability rejection including UNKNOWN; channel/type/byte strictness; raw corrupt data unchanged; finite input copied; repeated frames and symbols preserved; exact sequential exhaustion; no timestamp or identity normalization. This partially implements RQM021/024/028 and DELIV-S1-03. It does not satisfy real provider/reconnect or complete NEG-CAP obligations.
