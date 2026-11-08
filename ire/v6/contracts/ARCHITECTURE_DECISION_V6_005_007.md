# IRE V6-005–007 — Snapshot-bound audit, frozen gold arithmetic and acceptance boundaries

**Status:** implemented and independently tested on synthetic fixtures in an isolated working tree. **Not merged, not V6 production GO.** Baseline: `yhappcom/pensionport` development HEAD `f753ba57a1afabaa849f3eeca88170938c0b51f6` (observed 2026-11-08). No owner-private SRT/ZIP, private reviewer identities, actual official-law document contents, or 116 approved prior items are included in this deliverable.

## V6-5: Atomic TERMINAL_BLOCKED audit (not research completion)

`TransactionStore.issue_terminal_audit_receipt` replays its full event chain **inside BEGIN IMMEDIATE**; reads source SRT, frozen manifest, owner-held inventory and current structural proofs; checks *each current finance-candidate* against real supplied document bytes and pinned baseline bytes **inside that same transaction**; recalculates current blind arithmetic if present. It then commits a canonical `TERMINAL_AUDIT_RECORDED` event and updates the head in the **same SQLite COMMIT**. No author-controlled success flag is accepted. Missing data produces a typed error or an explicit BLOCKED reason. Event issuance is serialized against competing writers.

The receipt contains: base event head, base derived-state SHA, private-input commitment SHA (only hashes, not plaintext), current proof/finance revision digests, missing-model/proof/finance blockers, source-byte replay status, and explicit negative reviewer/issuer/semantic authorization. `read_terminal_audit_receipt` replays the full ledger and reports whether the historical receipt event is still the latest; it does **not** pretend to re-retrieve previously supplied external bytes. The request is idempotent only when the original command ID, base head **and private-input commitments** match; changes are conflicts. Hard-kill and pre-COMMIT failures leave no ghost event. Crucially, `issue_terminal_receipt` (research-complete authority) remains disabled and raises `QualityNotProven`. A terminal **audit attempt** with `TERMINAL_BLOCKED` is not a completed research report.

No automated engine-quality GO / financial fact approval is possible. SHA-256 and SQLite event hashes are integrity controls only; a privileged attacker who can rewrite both the full DB and an untrusted SHA reference requires an external, independently retained checkpoint to detect it.

## V6-6: Predetermined gold evaluation arithmetic (not proven independence)

`freeze_blind_plan` binds the **actual private source, owner's separately supplied immutable inventory SHA, scope windows, rubric version, selected sample, threshold ppm, and `gold_commitment_sha256`** to a durable event **before any MODEL_RECORDED prediction in the scope**. It also stores an intended reviewer protocol digest, which by itself does not authenticate actual reviewers. The store rejects plans submitted after model events, even if the author asserts `gold_sealed_before_predictions=true`.

`record_blind_measurement` derives the current model set from immutable model events and insists that submitted predicted atoms match the recorded propositions, source quotes and modalities. Every current window requires a current, replay-validated **structural proof**, and the input gold must match the precommitted SHA. Duplicate atoms or alignments, wrong cue quotes, impossible EXACT verdict field labels and post-hoc gold substitution fail closed. Results are recorded append-only as `BLIND_MEASUREMENT_RECORDED` and can be independently recomputed against private SRT bytes via `snapshot_with_blind_measurement` in one SQLite read snapshot.

Arithmetic yields strict exact TP/FP/FN, precision and recall with explicit denominators, five category breakdowns (`TAX`, `PENSION`, `LEVERAGE`, `RETURN`, `OTHER`), high-risk recall and deterministic Wilson 95% ppm bounds. `PARTIAL` is not a true positive. Zero denominators yield `null` metrics, never a fabricated 100%. Precommitted numeric thresholds can be *arithmetically* met while `semantic_accuracy_certified` and `actual_reviewer_identity_verified` remain FALSE. No automated test or claimed human independence flag establishes genuine independent reviewer existence, blindness, adjudication quality or comprehensive gold coverage. The sample fixture is synthetic and nonindependent.

The old V5 educational fact acceptance policy excluding external blind approval as a **universal fact-acceptance requirement** is preserved; that policy does not convert synthetic, internally generated evaluation labels into externally verified *engine accuracy*. Independent source-first gold and genuine reviewer provenance still gate V6 engine quality GO.

## V6-7: Integration and strict release gates

The isolated integration test traverses: SRT bytes → manifest/cue census → owner-inventory pin → precommitted gold/rubric → actual MODEL_RECORDED → current STRUCTURAL_PROOF_RECORDED → official and legacy relation candidates → blind arithmetic → recomputed private read → **snapshot-bound blocked audit**. It injects incorrect source/official bytes, post-hoc gold substitution, stale model revisions (including A→B→A protection inherited from V6-1–4), concurrent event writers, request replays and hard-kill after SQLite head update. Tests never claim independent financial truth.

For remote PR/push, `python -m ire.v6.prepush --root . --strict --expected-sha <actual SHA>` must run on a **complete canonical checkout**, Python 3.11, with all tracked files and six mandatory V5 checks plus V6 tests. Current runtime has Python 3.13.5 and only the V6 artifact; `BLOCKED_PREPUSH_VALIDATION`, exit 2. GitHub actions at the preexisting SHA do NOT cover the unsubmitted V6 files. No push/PR/merge should occur from this environment.

V6 release-quality GO additionally requires the genuine owner-held inventory/pointer and external immutable checkpoint, actual private source replay and cross-video/origin checks, authentic primary official financial sources with their operative dates, actual 116-item content relation validation, independently authored and verified gold TP/FP/FN with **pre-registered** pass thresholds, end-to-end successful completeness evidence and exact new-SHA GitHub CI PASS. This implementation deliberately does **not** enable `RESEARCH_REPORT_CLOSED`, P1 automatic knowledge promotion, individual trade authorization or ENGINE QUALITY GO.

## Backward compatibility / migration

Schema is **`IRE_V6_STATE_V4` / `PRAGMA user_version=4`**. Existing v1, v2, v3 V6 DB files are rejected with `V6_STORE_VERSION_MIGRATION_REQUIRED` instead of being silently replayed under the new reducer; an explicit, lossless and separately validated migration has not yet been implemented. Old V5 events and existing approved knowledge are never reinterpreted, rewritten or imported as V6 proofs. Persisted gold and alignment text can contain private subtitle excerpts; the actual SQLite DB/WAL must remain owner-only and must **never** be added to a public patch, ZIP, or Git repository.

## Non-negotiable status

V6-5 **audit attempt feature**: isolated software PASS, research completion NOT ENABLED.

V6-6 **gold arithmetic & preregistration**: isolated software PASS, independent gold accuracy UNMEASURABLE.

V6-7 **local synthetic integration**: isolated software PASS; full checkout, private source, official 116 relations and GitHub exact SHA release verification BLOCKED.

**ENGINE QUALITY NOT PROVEN / P0 NO-GO**.
