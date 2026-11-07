# IRE V5 host feasibility — actual no-API ChatGPT run (2026-11-04)

**Scope:** Current ChatGPT conversation, NOT ChatGPT Work; no external LLM API. Original #1–#5 source-authenticated 5,129 SRT cues, V5 288 frozen windows. Existing baseline 5/288, new 10 source windows authored and accepted, ending **15/288 processed and 273 still unprocessed**.

## Actual model / web / engine integration
- ChatGPT directly inspected 180 actual original subtitle cues in W00002–W00003 of each of five videos, authored **9 provisional atomic claims**, cue statuses and provisional evidence/prior-knowledge review. This is not blanket whole-video certification.
- Official primary source research performed for NPS pension-topup eligibility and Ministry of Employment and Labor retirement pension portability. A historical corporate-ownership news source was contextual only, not an official statistical baseline. Individual pension increase, employer bank-loan causality, and historic market rank remained OPEN.
- Five new per-video immutable multi-action receipts, one for each pair of windows, were accepted, yielding **10 total receipts across 5 videos**, no approved financial facts, no advice clearance.
- Deliberately fabricated source quote rejected with `MODEL_HALO_OR_FABRICATED_QUOTE`, before any persisted write. Exact duplicate re-submission was idempotent.
- Verified local encrypted 5-video backup and independently re-opened V5 store. Also uploaded archive to private Google Drive folder, downloaded exact blob and verified SHA256 plus decrypted full five-ledger replay. Archive SHA: `8c3045f89abac5236ee96655c30b3e6fba845d7f16f1bf8bfb9c7148c2b53adf`. Drive file id `1MVSTwIt-bx7lv4EjpdnhQs18qD5TRQMY`; private recovery key was not uploaded or committed.
- Regression 53 core cases: 50 pass, 3 skip (private fixtures missing); 24 app tests pass.

## Newly discovered high-impact defect / quality risk
The V5 sentence-aware planner flags `continuation_boundary_review_required` for **215/288 = 74.7%** of windows:
#1 48/67; #2 55/76; #3 37/44; #4 33/43; #5 42/58. These are **risk flags**, not demonstrated semantic mistakes. Current `ResearchRun.packet()` supplies only primary cues, not the adjacent halo. An excerpt such as #1 W00002→W00003 crosses a client's pension question, so source boundary semantics must be stitched/reviewed before advancing source coverage with assurance. Consider source-preserving cross-window halo and cue-specific citation ownership, independently checked on withheld multi-cue claims.

The existing five-video run's manifest **does not enable STRICT_P0C_V1**. Evidence candidate links/OPEN notes therefore **do not prove raw official-byte verification or claim-specific effective-law applicability**. Use strict P0C on future locked runs; never silently mutate a signed old plan.

25-window **source-only** packet = 39,359 bytes; it is not 25 analyzed windows.

## Decision
- ChatGPT → actual SRT semantic sample → official web search → V5 receipts → cold storage/replay: **PASS (limited sample)**.
- Current host full 4–5-video, one-user-turn comprehensive research: **NO-GO / NOT DEMONSTRATED**.
- Work-mode cloud executor continuity: **NOT TESTED**.
- GitHub Actions alone cannot summon more ChatGPT inference without separate model API. Public GitHub counters remain non-attesting metadata, not a substitute for actual private source verification.

**No changes to main, historical approvals or source originals.** The result motivates: (1) prove long-running host runtime, (2) fix forced continuation validation, (3) enforce official scope and prior-diff audits, (4) test full one-video closure before the five-video user-turn GO gate.
