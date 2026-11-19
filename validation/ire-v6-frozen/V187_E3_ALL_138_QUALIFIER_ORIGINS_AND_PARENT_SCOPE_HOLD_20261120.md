# V187 — E3 source provenance 138/138 and cross-cue hypothetical scope repairs

**2026-11-20 KST · OWNER ACTUAL SOURCE REVIEW / E3 QUALITY HOLD / E4 NOT RUN / E5=0**

## Starting evidence and invariants

- Actual owner ETF SRT video `LVE7XN_esTc`, 250 original cues, SHA-256 `e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b`.
- Verified V186 **21/21 private file member hashes** and all **4/4 SQLite integrity checks** before examining the next 106 qualifiers. No original SRT/verdicts/SQLite were copied into GitHub.
- Native owner V176 event-head remained exactly `ccd789a0fc6259e600d434381f8b5064a1e6b137256968d7b061192896a9b138`; 69 provisional atoms, original OPEN 17. E3 source-only second pass 92/250; all 54 *previously detected* disagreements were internally cause-adjudicated, **not externally certified**.

## Real ChatGPT in-chat source review: previous 32 + remaining 106

- Seven sequential **private source-cue** batches of 16+16+16+16+16+16+10 = **106 newly reviewed** V176 condition/exception terms. The ChatGPT-authored evidence statements quote exact original cue text where available and contain a specific rationale; every packet/response pair was pinned to the owner video, first-pass head and immutable qualifier journal. One extra local process re-opened all events and revalidated the same source quotes.
- **138/138 terms provenance reviewed**. Responses by source origin: `SOURCE_EXPLICIT = 12`, `SOURCE_CONTEXT = 41`, `REVIEWER_ADDED = 78`, `UNRESOLVED = 7`; missing reviews 0.
- The 78 `REVIEWER_ADDED` caution/finance caveat terms are **excluded from source-spoken frozen V6 qualifiers**, but preserved in private first review and the new qualifier source ledger. They are *not 78 missing original spoken exceptions*.
- The 41 `SOURCE_CONTEXT` terms have only contextual source support, and must **not** be treated as verbatim speaker conditions without a separate semantic argument. The 7 unresolved terms include 2 original audio/video unresolved qualifiers plus 5 cases where the parent source hypothetical cue 212 is outside the local candidate's source context.
- V186 full qualifier journal after this turn: `48f9d1917fc265d4d226599c2439af7c02a865f1ba4881386f551740694386a0`. Status `fully_covered=true`, **`e3_quality_certified=false`** because the review is in-chat, independent gold missing, and many statements lack verified speaker/stance.

## Actual structural defect and E3-only repair: inherited hypothetical scope

- Owner cue **212** explicitly introduces a **fictional ETF screen**. A subsequent cue **215** refers to the same ETF, and cues **218, 220, 227, 228, 229** state the example's NAV, trading price, net assets, previous-day volume and annual fee. The V176 first-pass local contexts for those five candidate atoms do **not include cue 212**. Without an explicit cross-cue link, a naive E3 transform can incorrectly treat fictional example figures as real market data.
- Added `v187_e3_parent_scope_bridge.py` and `v187_e3_parent_scope_cli.py`: a separate, private, hash-chained ChatGPT E3 source-scope attestation journal. Parent original quote and a later direct coreference quote must both match source bytes. Parent must precede the claim by <=20 captions. The target must be an already `UNRESOLVED` **condition** in the fully reviewed V186 qualifier ledger. This prevents arbitrary reviewer warnings or unrelated non-source claims from being promoted.
- Recorded **five source-scope relations**, all provisional and append-only, source parent cue 212, referent cue 215. New bridge journal head `143796f89163ac5c6246cb5eb6f4aa1bc886b212896e64eb3dafd8340b650fbb`.
- V176 native `compile_native_v6_stage(qualifier_provenance=..., cross_cue_scope_bridge=...)` now expands the candidate's **context** and **condition source indices together** for these five pinned claims. Actual frozen `ire.v6.atomic_exchange.audit_host_atomic_exchange` PASS for 69/69 candidate atoms and 250 cue records, **17 source-anchored provisional conditions total** (V186 direct 12 + V187 source-parent 5). The inherited cue is held as source context, NOT an automatically fact-approved NAV or ETF fee.
- Remaining native E3 projection diagnostic: **52** qualifier condition terms unprojected as speaker-explicit; **69** exception terms unprojected. These counts include items deliberately classified as reviewer-added or contextual; **do not interpret all 121 as lost spoken facts**. Native `stance=UNRESOLVED` and `speaker=UNKNOWN` remain for all 69 proposed atoms.
- The two remaining `UNRESOLVED` conditions are source audio/screen gaps, not resolved by rewriting the transcript. Never infer the missing original audio/video from a general financial explanation.

## Code quality and security regression

- New tests cover bridge source proof, forged parent/co-reference quote, duplicate/stale packet, wrong head, wrong original permissions, data tampering, unauthorized approval injection, context-index projection and no E4/E5 authorization.
- Also closed a SQLite connection leak in the V186 original-qualifier read path so repeated provenance audits do not retain owner DB handles.
- Local 60 available V182–V187 synthetic tests PASS. GitHub CI should run the **complete V176–V187 regression suite**; the software unit tests do not measure financial/semantic precision or recall.
- No external model API, no automatic bank/market/regulation fact approval, no investor portfolio connection, no E4/E5 writes.

## Reproducibility and strict HOLD

- V187 private ZIP includes owner SRT, five source-only SQLite journals, all 106 new original-cue packets and ChatGPT judgments, parent scope evidence, and an SHA-256 manifest. **40 files** in the private checkpoint, re-extracted in a separate directory; **40/40 hashes, 5/5 SQLite integrity checks and independent Python-process original / second / adjudication / qualifier / scope replay PASS**.
- Private V187 ZIP SHA-256: `c5c5eff4459b8ca2e4ecfa4f8c1433bca5a43e2a1d2baab34d9ce680d83b867a`. Private manifest SHA-256: `15e29ceaf5afd19a5fb7db57e05f71ac5ee8a7bc7396f0184ae3484731fcd463`. **Never upload this unencrypted owner package to a public repository or CI**.
- E3 **HOLD**: 158/250 original captions still lack separate second-pass review; 17 effective OPEN, parent assertion boundary disagreement and 69 unresolved speaker/stance flags remain; independent fixed answer-set precision>=95%, recall>=98%, high-risk omissions 0 **not measured**. A full 138/138 provenance census is **not** E3 final acceptance.
- V123/E4 **not invoked**, E5 publication **zero**, `main` unchanged. Continue E3 second-pass, source-attributed parent boundaries and independent gold before any E4 test.