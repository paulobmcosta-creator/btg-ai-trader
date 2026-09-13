# S1 — Generated properties and executable mutation campaign

- Date: 2026-09-13.
- State: testing mechanism decision recorded before test implementation.
- Base: integrated assembly `37ff91bc9a86269cd68ddf5537b474f49b7d0510`.
- Authority: explicit coordinator/user request for real PROPERTY and MUTATION evidence on the integrated source.
- Scope: tests and this decision document only; no canonical source, composition, NEG suite, dependency or gate promotion.

## Testing mechanism decision

Select stdlib random.Random with fixed enumerated seeds and explicit bounded case counts, plus independent reference models for queue and dedup state machines. Generated actions vary offer/take frequency, capacities, identities, payload conflicts and receipt metadata. Assertions compare observed transitions against an independently maintained model, including conservation, FIFO identity, canonical preservation, bounded retention, duplicate classification and no silent eviction.

Generate arbitrary raw byte sequences for typed technical codec roundtrips, then malformed/truncated/noncanonical variants and mismatched declared hashes. Generate valid fixture JSON envelopes with duplicate-key and truncated variants, requiring raw-preserving quarantine. Add generated equal/earlier/later temporal comparisons. Seeds are fixture test inputs, not economic simulation, so deferred DD-13/DD-14 remain untouched. No new numbered foundation DD is invented: this is the S1-EC-104 mechanism decision supporting existing DD-02/DD-57/DD-59 contracts.

## Mutation mechanism

Use a disposable temporary directory per variant, copy the checked-out package source and generated property test file, and run a child Python/pytest process against that copy. Enforce imported package location within the copy before running tests. The unmodified copied baseline must pass first. Require each mutation anchor exactly once; ambiguous/missing anchors fail the harness rather than silently skip a mutant.

Mutants target actual invariant behavior: FIFO delivery, observed rejection counters, duplicate payload conflict classification, capacity exhaustion classification, canonical codec representation rejection, raw-hash consistency, duplicate JSON-key rejection and equality at the late frontier. Mutations do not edit canonical source. Only a child test failure in an executed selected property group counts as killed; import/collection errors, timeouts and invalid harness setup are errors, not kills.

Store per-mutant source hashes, return code, selected tests and failure counts in a JSON report under pytest's temporary directory; emit the executed campaign summary into CI logs. Require no surviving mutant within this fixed catalog for the mutation test to pass. Do not claim exhaustive mutation coverage, production robustness or zero defects. Counts are reported only after executable evidence exists.

## Verification and evidence limits

Run the regular remote checks on the final PR HEAD. The baseline generated suite and mutation campaign must execute on the same copied canonical source content; report properties/seed count and mutants/killed/survived/errors from actual logs. No local/user checkout execution is used.

The initial PR is stacked on the integrated assembly branch. If the assembly later changes, re-run these tests after integration and anchor claims to that newer exact SHA; earlier passing evidence is not transplanted automatically. Existing directed unit tests remain useful and are preserved.
