# P0-2-05 private chat revision custody — 2026-11-24

Development change, not semantic certification. Existing source and all failed trials remain untouched. Checklist stays HOLD (16 PASS, 43 BLOCKED).

- Optional host batch chat_revision input contains before, edits, cue_reviews. The engine replays the compiler against current owner-pinned source and rejects any mismatch in exchange, models, or structural reviews before committing.
- Private SQLite seal stores the canonical input/result record and its digest; exact retry pins the record, including review reasons. Existing batches without the optional input retain previous commitment semantics.
- Private read verifies the event chain, source owner, record digest, compiler replay and contiguous model/proof event contents. No external model call or independent gold is asserted; no new financial authority.
- Canonical 1 MiB event ceiling applies; oversized inputs fail atomically, not silently truncated. Future compiler changes may require explicit historical replay versioning.
- Integration test covers native write, mismatch rollback, exact retry, changed-reason rejection, reopen/read and full input/output equality. CI must be verified at this new commit.
- Actual independent source-only evidence and ten risk cases remain open; existing ETF development replay is not a fresh holdout. Do not advance to P0-2-06.
