# V189 — E3 source-pinned omission reassessment and parent-claim false-link guard

**Date:** 2026-11-20 KST. **Disposition:** E3 HOLD, V123/E4 NOT RUN, E5=0. Not an independent financial or scientific correctness certification.

## Original-source baseline and immutable journals

- User-owned ETF original `LVE7XN_esTc`: 250 SRT cues, raw SHA-256 `e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b`.
- Independently restored V188 private checkpoint SHA-256 `7f1b74095e03ef072584c0322d6f8eaa09a20c0953b528277926a9aa0187a3d7`. Original 79 private files, all member hashes checked; five SQLite databases `integrity_check=ok`.
- The two source-only E3 judgments are 250/250 complete, original first 69 and second 71 provisional atoms, with 149 original cause labels. These are **not** approved assertions. Original first/second/adjudication heads are held unchanged:
  - first `ccd789a0fc6259e600d434381f8b5064a1e6b137256968d7b061192896a9b138`
  - second `142c2d43921ca7e09ac2b00d4a526e9dffb64cac579a3c92b9f1750f0b29fa5c`
  - cause adjudication `4bb83cb6b6fddc2c5a072c510bbbc7a2c922c02f0ddc1358fc41a06633f41d21`.

## Critical source review: 12 labels incorrectly treated as independently confirmed omissions

The V188 cause set used `CONFIRMED_FIRST_PASS_OMISSION` or `CONFIRMED_SECOND_PASS_OMISSION`. These labels were **ChatGPT internal source-informed judgments** and not externally validated gold. Reviewing the full first/second atomic ledgers around each cue revealed real counterexamples:

| V189 interpretation | Count | Original cue indices | Consequence |
|---|---:|---|---|
| Provisional new claim **candidate** | **6** | 6, 10, 18, 26, 85, 91 | Other-pass claim SHA pinned as an unapproved repair suggestion; no original record change |
| Already covered at a different cue anchor | **5** | 56, 78, 181, 239, 247 | Existing source-context-bearing first/second claim reference pinned; prevent duplicate atom |
| Claim boundary / explanatory scope unresolved | **1** | 38 | No claim projected or silently omitted |

Examples of the duplicate risk: cue 78's ETF exchange-trading assertion was already anchored in the **first-pass cue 77** claim with cue 78 in its context. Cue 247's product-comparison recommendation was already anchored in first-pass cue 244 and includes cue 247. Cue 239's relative-index explanation was already present in the **second-pass cue 244** with cue 239 in context. Simply appending all twelve alleged omissions would create duplicated or mismatched atoms.

`v189_e3_omission_repair_overlay.py` records the reevaluation in a **separate append-only SQLite journal**, pinned to the source SHA and three prior immutable journal heads. `prepare/submit` regenerates the full original challenge, checks literal source quotation and exact existing first/second claim SHA, refuses wrong-pass references, duplicate/stale/self-forged challenges, secretless approval forgery, and nonprivate database files. **No V6 claim, speaker attribution, or E4 approval is changed.** The six new claim references must still undergo fully source-anchored atomicity and reviewer-provenance re-evaluation before any revised stage can be constructed.

## 65 parent boundary labels: heuristic source pairing is not semantic equivalence

A further ChatGPT source-informed screen of the previous 65 `CLAIM_BOUNDARY_DISAGREEMENT` entries found:

| Conservative screen | Cues | Certification |
|---|---:|---|
| Provisional same-parent candidate (1 structural pair) | 23 | **NOT proven equivalent** |
| One possible pair, **overlapping but materially distinct facts** | 13 | Distinctness flagged; must not auto-merge |
| Multiple candidate pairs | 25 | Unresolved |
| No grounded heuristic pair | 4 | Unresolved |

Previous V185 candidate matching required only close cue indices, similar numeric tokens and category/context compatibility. Real source comparison exposed false matches including **NAV versus intraday market price** (cue 138), **small tracking differences versus their long-term accumulation** (cue 110), and **small fee comparisons versus investor switching behavior** (cue 197). The match could be unique yet still false; never equate confidence with uniqueness. The 13 materially distinct relationships are ChatGPT review findings, not independent gold. The 23 same-parent statuses remain *provisional*.

`v189_e3_parent_alignment_screen.py` issues source-grounded E3 candidate packets and validates a model-authored answer against exact original cue quotations and candidate claim hashes; `validate_live()` regenerates the packet from the frozen source and earlier SQLite journals. Multiple or absent candidate pairs must stay unresolved, and no response can claim equivalence certification, independent gold, E3 or E4 approval.

## Correct metric/next evaluation procedure

1. No precision/recall estimate may be published from V188 69-vs-71 candidate counts or 149 structural differences. **Precision ≥95%, recall ≥98%, zero high-risk omission remain UNMEASURED.**
2. The 6 additional provisional candidates must be adjudicated against all other claims, not inserted automatically. For the 65 parent labels, inspect the 25 multiple and 4 no-candidate cases, then resolve the 13 materially distinct cases with explicit atom boundaries and scope.
3. Build and preregister a separate *unseen* video source and scoring ontology **before** the model sees its validation labels; retain every original cue with risk tags, source quote, speaker, time, conditions, exceptions and cross-cue parent links. The same ChatGPT operating in different turns is procedural blind separation, **not independent external gold**.
4. Only score when every denominator and high-risk adjudication is backed by a fixed judged answer set; E3 must fail closed otherwise. E4/V123 final approval and E5 are not attempted here.

## Public-safe execution boundary

All owner SRT bytes, provisional claim texts, reviewer decisions and SQLite files reside **only** in a user-private, unencrypted checkpoint; GitHub and Actions receive code, synthetic fixtures and this redacted document only. The repo `main` remains untouched, PR #71 remains Draft. Synthetic regression checks validate software safety and reproducibility; they do **not** certify financial truth or review independence.