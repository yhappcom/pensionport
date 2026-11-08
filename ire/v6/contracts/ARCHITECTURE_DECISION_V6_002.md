# V6-002 — Private Source Replay and Version-anchored Structural Proof

**Date:** 2026-11-08 KST. **Status:** isolated implementation complete; canonical integration blocked. Based on `f753ba57a1afabaa849f3eeca88170938c0b51f6`; does not amend V1–V5, master 116 or P4 29.

## Trust boundaries

1. An SRT ZIP/file reference or a correctly shaped 64-hex digest is **not proof** of original bytes. The caller obtains raw private bytes, separately pinned owner inventory source SHA-256, and an independently fixed manifest SHA-256 before calling `verify_source`. The current prototype obtains expected values from the private scope record. If an attacker can rewrite both the scope record and its source files, full-provenance authenticity is still **not proven**. An owner-held immutable inventory and external chain checkpoint remain required.
2. `verify_source` hashes the *exact* raw bytes, parses all cue text/time/order, rejects retrograde starts, validates every primary window text hash, contiguous window identifiers, explicit partial/full coverage, and owner without gaps/overlap. All public fixtures are synthetic.
3. `SOURCE_ATTESTED` is issued only by `TransactionStore.attest_source` after actual bytes are checked. Only SHA/counts/census digest are put into the event; raw SRT remains private. Reading an old event alone cannot assert that the original SRT was re-read during the present call.
4. `STRUCTURAL_PROOF_RECORDED` can be issued only by `submit_structural_proof`, which replays the private original and matches exact cue quotes, the actual window ownership, and the **current** model revision event ID. No arbitrary `submit` endpoint can forge the event. `snapshot_with_source` rechecks all *currently active* proof records inside one SQLite read transaction. Older A→B→A proofs are historical and not current.
5. This structural proof **does not** certify semantic claim completeness, correctness of financial rules, reviewer's external independence, acoustic ASR accuracy, or closed research. `issue_terminal_receipt` remains disabled; all `engine_quality_certified`, `p0_go` are false.
6. V6-1 database `PRAGMA user_version=1` uses a different derived-state digest. V6-2/3 requires version **2** and fail-closes older databases with `V6_STORE_VERSION_MIGRATION_REQUIRED`. The later migration must be a separately tested, explicit, evidence-preserving operation. There is no silent rewrite of old events.
7. Exact same structural proof command is idempotent, even after newer revisions, but returns a *historical nonterminal receipt*, not current approval. Different input under the same command ID fails.

## Source plan schema

- `schema=IRE_V6_SOURCE_PLAN_V1`, `video_id`, `source_sha256`, `cue_count`.
- `scope={mode: FULL_VIDEO|PARTIAL, first_cue, last_cue}`; FULL_VIDEO must cover all original cues.
- `windows=[{window_id,first_cue,last_cue,text_sha256}]`, ordered, gapless, with sequential numeric W-ID. Offsets are allowed for partial scopes.
- Cue census digest includes `index,start_ms,end_ms,text`. Per-window text digest uses the literal cue texts joined by one space.

## Proof contract

- Model must use `IRE_V6_ATOMIC_MODEL_V1` with source-ref-indexed atomic candidates. The earliest cited cue determines the claim's primary window; any additional quoted cues may cross a window boundary.
- Review must use `IRE_V6_STRUCTURAL_REVIEW_V1`, include every claim ID, and unambiguously state `review_scope=SOURCE_ANCHORS_ONLY` and `independent_gold_verified=false`.
- Persisted event binds source attestation event SHA, current model revision event SHA, review payload, and derived audit. The reducer rejects an incompatible live source or model revision.
- Fresh snapshot with the raw source re-derives the original structural audit and checks exact equality. A historical snapshot from `snapshot()` never automatically upgrades a review to proven independent semantic accuracy.

## Adversarial gates run in isolation

- Correct raw bytes and all-text/cue/time/window plan; corrupted original or time-only change; attacker-updated manifest without pinned original; recomputed hash with nonmonotonic starts; W-ID skip/reorder; primary owner gap/overlap; partial offset scope.
- Cross-window multi-cue true anchors, impossible quotes, model ownership theft, incorrect context span, false independent gold, incomplete reviewer claim set.
- Source attestation and structural proof forged by generic submit; exact idempotent replay and conflicting command ID; A→B→A proof invalidation; chain corruption; stale-head concurrent proof attempt; V6-1 database migration refusal.
- Source-attestation and structural-proof event insert/HEAD update followed by injected pre-COMMIT failures: rollback persisted, new Store reopens with unchanged HEAD and a clean retry succeeds.
- No private source text or independent gold data is included in GitHub-ready source artifacts.

## Remaining P0 requirements

- Owner-held source inventory and immutable external ledger checkpoint; real 71 SRT / 70 unique video replay with separately provided byte pointers; independent TP/FP/FN; comprehensive claim extraction, evidence and official temporal applicability; legacy 116 relationships; full source→receipt integration and exact-SHA CI; Python 3.11 same-checkout six mandatory V5/preflight commands.

**Outcome:** V6-2/3 structural source-check proof slice, NOT ENGINE QUALITY GO.
