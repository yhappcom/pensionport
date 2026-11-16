# V143 — V123/V126/V128 explicit quarantine and approved-subset atomic release

**2026-11-16 · Frozen V6 feature branch only · SYNTHETIC test fixtures only**

## Behaviour

The ChatGPT final review continues to review *every* original cue and candidate atom. The optional quarantine profile `IRE_V123_SOURCE_PINNED_QUARANTINE_V1` permits a finite set of uncertain or disproven source cues to receive `EXCLUDED_FROM_RESEARCH` rather than indefinite global `OPEN`. Each excluded atom must receive `EXCLUDE_FROM_RESEARCH` and be attached to the original source SHA, atom digest, reason, private ChatGPT note digest and a context/dependency review. Original audio ambiguity is **not claimed resolved**: excluded audio cue indices must equal the declared unverified-audio count, and none may anchor a retained claim. V6 source `UNRESOLVED` and lexically suspicious `NO_ATOM` cues must be among the explicit source exclusions.

V123 PASS still requires a current, replayed source+host receipt, all original cues and atoms accounted for, reviewed conditional/exception/numeric/counterexample semantics, no unadjudicated OPEN or rejected atom, and original official primary-source bytes for every *accepted* finance-sensitive claim. The old strict non-quarantine profile is unchanged. Quarantine is **not** evidence of accuracy, original audio authenticity, formal financial approval, or personalized advice.

V126 validates full original V6 replay and full relation ledger but inserts **only** `ACCEPT_FOR_RESEARCH` atoms. Any child with 0 accepted atoms stages zero DB events and cannot trigger a partial parent publication. The existing evidence retrieval reads only written/active knowledge IDs.

V128 still requires every child V123 PASS, each cross-segment seam and a separate **ChatGPT-signed full-parent decision**. A parent that includes quarantines must also source-bind the exact SHA-only quarantine manifest and explicitly adjudicate excluded cues and cross-scope dependencies. If its digest or affirmative review is missing, the transaction is refused. Validated child inserts are staged in a temporary private SQLite copy; only all-child/whole-parent PASS triggers the existing single `BEGIN IMMEDIATE` parent transaction with full rollback and replay-proof chain.

## Important limits

- Tests use a **synthetic** four-cue/three-atom owner fixture and two-child parent. CI PASS does not approve any of the actual 1,481 video cues.
- The real original SRT has **88 unresolved speech/transcription cues**. None is automatically excluded or upgraded by this patch. A ChatGPT source-first individual decision is still required.
- Same-chat adjudication is not external gold. Precision/recall, P0 GO, 791-video readiness, real operating DB ownership and personal portfolio advice remain **unproven**.
- No original SRT, individual private review or financial owner evidence added to GitHub. `main` and frozen `ire/v6` engine core untouched.
