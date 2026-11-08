# IRE V6-1 — Isolated deterministic kernel

This is the first implementation slice of the V6 redesign, **not a replacement for V5** and **not quality GO**.
It introduces an ACID transactional event store, strictly pure state projection, revision identity, conservative progress receipts, fail-closed terminal issue, and adversarial tests without editing V5.

## Minimal use (private local filesystem)

```python
from pathlib import Path
from ire.v6 import TransactionStore
from ire.v6.codec import sha256

store = TransactionStore(Path('/private/ire-v6/v6.db'))
created = store.create_scope(
    scope_id='pilot_scope_001', video_id='ABCDE123456',
    source_sha256=sha256(b'placeholder source bytes'),
    manifest_sha256=sha256(b'placeholder plan bytes'),
    command_id='create_pilot_scope_001',
)
recorded = store.submit(
    scope_id='pilot_scope_001', command_id='model_w00001_v1',
    expected_head=created['event_sha256'], kind='MODEL_RECORDED',
    payload={'window_id':'W00001', 'model': {'draft':'NOT VERIFIED'}},
)
assert store.snapshot('pilot_scope_001')['sequence'] == 2
assert store.progress_receipt('pilot_scope_001')['engine_quality_certified'] is False
```

The placeholder input demonstrates software contracts only; this does not verify original SRT bytes. Do not use this as a validated financial research result.

## Test commands

```bash
python -m compileall -q ire/v6
python -m unittest discover -s ire/v6/tests -p 'test_*.py' -v
python -m ire.v6.prepush --root . --isolated
```

The isolated command returns success only for V6 software tests. Pre-push needs the **full canonical repository** with pinned Python 3.11 and all original tracked fixtures:

```bash
python -m ire.v6.prepush --root . --strict --expected-sha <verified-current-dev-HEAD>
```

If full checkout and all six old mandatory commands are unavailable, it returns `BLOCKED_PREPUSH_VALIDATION` and must prevent any remote first push, PR or merge. CI success never establishes independent financial truth or full corpus coverage.

## Current safety boundaries

- `SOURCE_DECLARED` stores only a **pointer**, not independently verified original bytes.
- `MODEL_RECORDED` and `REVIEW_PROPOSED` are not approved semantic/factual findings.
- A terminal research receipt is **deliberately unavailable** in V6-1; the verifier and independent-goldset gates do not exist yet.
- Store files may contain unverified private review text; use an access-controlled private directory. Never upload DB/WAL or raw SRT files to public GitHub.
- WAL requires a local filesystem. The chain needs a separately held trusted checkpoint to detect complete malicious rewriting of all database records.
- The V5 branches, 116 approved facts and 29 P4 nodes are untouched. No migration is performed.

## V6-2/3 private source and structural proof (isolated prototype)

`ire.v6.source.verify_source` checks exact private SRT bytes, start times, cue census and a SHA-pinned, gapless source plan. `TransactionStore.attest_source` records hashes and counts, not plaintext, and `submit_structural_proof` checks current model revision and genuine original quoted cues. `snapshot_with_source` repeats the private source and proof audit against one consistent SQLite snapshot. The event store is now **version 2** and refuses silent migration from V6-1 databases. Historical proof retries remain historical and never imply current approval. The full contract is `contracts/ARCHITECTURE_DECISION_V6_002.md`.

A valid source-attestation **record** is not equivalent to independently validated original ownership; an owner-held immutable inventory is still needed. Structural source linkage is not semantic precision or recall. None of these operations unlocks `issue_terminal_receipt` or P0 GO. Tests use synthetic subtitles and do not read or distribute the owner-private originals.

## V6-3 owner pin + V6-4 finance candidates (isolated follow-up)

`ire.v6.trust.verify_owner_inventory` checks that a complete canonical owner-inventory blob matches an **independently provisioned** SHA-256 digest and that the current SRT, manifest and cue census match one exact inventory entry. `TransactionStore.attest_owner_inventory` stores a digest-only event after `attest_source`. This is not a signature or identity proof; if the submitted pin itself was attacker-controlled, the result cannot be trusted as true owner provenance.

`ire.v6.finance.audit_official_candidate` checks bytes, literal quote, HTTPS metadata and date applicability of a *claimed* official source. `audit_prior_relation` checks membership in an externally SHA-pinned prior knowledge metadata baseline, not the substance or authenticity of 116 facts. `TransactionStore.submit_finance_candidate` requires the current source pin, current model revision, and current structural proof before atomically recording **unapproved** official/legacy relationship candidate hashes. `snapshot_with_finance_candidate` replays all source, proof, official and baseline bytes in one consistent SQLite read transaction.

The new local state version is **3**; opening an earlier V6-1 or V6-2/3 SQLite DB without a separately validated migration fails closed. All status/receipts remain **nonterminal**; the `finance_fact_approved` value is always false. Synthetic `example.org` documents in tests are not authentic sources and the sample baseline has 3 entries, not 116 real approved knowledge items. See `contracts/ARCHITECTURE_DECISION_V6_004.md` for exact contracts, exclusions and release gates.

## V6-5/6/7 — auditable blocked receipts, frozen blind arithmetic, isolated integration

New methods: `TransactionStore.freeze_blind_plan`, `record_blind_measurement`,
`snapshot_with_blind_measurement`, `issue_terminal_audit_receipt`, and
`read_terminal_audit_receipt`. The finite run can produce a **durable,
version-bound TERMINAL_BLOCKED audit** for a real supplied private source and
source-linked candidate artifacts; this is not a completed research report.

V6-6 permits source-first **gold-set digest precommitment before any model event**
and calculates strict TP/FP/FN, precision/recall (overall and high risk), and
Wilson intervals with explicit denominators. The evaluator verifies arithmetic,
not human identity or whether the labels are accurate. Synthetic 100% labels
will NEVER become an independent semantic quality certificate.

`issue_terminal_receipt` remains fail-closed; the owner identity, genuine source
provenance, authentic issuer law, actual master-116 semantic relation, external
blind gold and full checkout CI proof are all still pending. The private DB
schema is **v4**, with no automatic v1–v3 migration. See
`contracts/ARCHITECTURE_DECISION_V6_005_007.md` for contracts and threat model.
