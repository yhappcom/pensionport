# V5 P0 — #24 W00037–W00044 dual-ledger adjudication checkpoint (2026-11-07)

**Scope:** Original private SRT #24 `AeCOMNl11v4`, archived SHA256 `00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd`, SRT SHA256 `af4d89d0e69b219947fdf82cdd9f3229c1f7b1e14c05c924ac815d2511f6c531`; direct raw-byte verification performed on 2,321 cues, targeted W37–W44 (cue 648–791 = 144 cues). Source text and full SRT not committed. Window text digests and the 26 claimed anchor text SHA256/time labels were computed from the raw original in this turn and preserved in the adjacent JSON record. **These hashes alone cannot prove independent semantic accuracy in public CI.**

## Reproducible fail-closed defect

PR #38 lists **26 provisional claims** but assigns **eight** anchors outside their stated primary windows. Original ownership from the real 18-cue source plan:

| source cue | prior PR #38 window | verified primary window | disposition |
|---:|---|---|---|
| 719 | W00041 | W00040 | ownership corrected; forecast starts before W41 |
| 729 | W00042 | W00041 | corrected |
| 731 | W00042 | W00041 | corrected |
| 734 | W00042 | W00041 | corrected |
| 736 | W00042 | W00041 | corrected |
| 747 | W00043 | W00042 | corrected |
| 755 | W00043 | W00042 | corrected; explanation continues into W43 |
| 772 | W00044 | W00043 | corrected; borrowing amount continues into W44 |

The amended **effective** owner is immutable in the append-only JSON; the invalid original remains recorded as history. Cue 719 uses open context 719–723 (W40→W41), cue 755 uses 755–760 (W42→W43), cue 772 uses 772–775 (W43→W44). Only one primary owner is permitted per atomic claim; adjacent context cannot be independently counted as a new claim. The generic gate rejects all eight original assignments under test, and the corrected effective owner passes.

## 31 vs 26 reconciliation — semantic equivalence remains OPEN

- The 31-unit [PR #37 quality probe](https://github.com/yhappcom/pensionport/pull/37) and 26-unit [PR #38 report](https://github.com/yhappcom/pensionport/pull/38) are both **same-conversation provisional analyses**, neither blinded independent gold. The arithmetic difference of five is **not** a measured five false negatives.
- Five PR #37 topics lack an *independently enumerated* counterpart in PR #38: W37 cue 652 (housing-cost motivation); W38 cue 668 (choosing to study investing); W42 cue 738 (COVID fall perceived as an opportunity); W42 cue 752 (waiting for a downturn); W43 cue 765 (crypto and bank-share holdings). Whether each belongs in the atomic financial claim census is still OPEN; they may be background or personal examples.
- PR #38 separates a quoted Bitcoin fall around KRW 20m at cue 695 from first personal purchase details, whereas PR #37 grouped purchase with price history. PR #38 also records recovery around cue 728, which was not a separately counted PR #37 proposition. The same cue can support multiple independent propositions; neither flat count proves exhaustive decomposition.
- PR #37 W40 cue 717 and W41 cue 720 both describe the crypto-awareness forecast across a real boundary, potentially **premise/conclusion or overlapping restatement**, not necessarily two independent claims. PR #38 cue 719 is anchored in W40 and requires W41 context. Preserve a single question for an independent adjudicator, not a forced 2→1 merge.
- PR #37 cue 732 couples Ethereum market price and guest's own cost basis; PR #38 cue 734 keeps personal basis but leaves market price as possible uncounted independent proposition. PR #37 W43 cue 772 and W44 cue 774 treat borrowing and total position as linked conversational context; PR #38 cue 772/774 separates the loan and estimated total. These are structural differences, not verified factual contradictions.
- Host agreement with a guest's personal investment success is not an endorsement or correctness of personal leveraged cryptocurrency strategy. A hypothetical KOSPI 2000→1000 plan is **not** an observed price-series fact.

**No TP/FP/FN, Precision or Recall is assigned** without a new independent gold labeling pass using the full raw SRT. Other 31 vs 26 source-meaning equivalences remain `OPEN_REQUIRES_BLIND_ADJUDICATION`, not automatically approved. The 26 reconstructed annotations in the JSON preserve PR #38's source intent and correct only anchor ownership.

## Engine quality scope and next checkpoint

- CI-visible correction verifier validates cue→window membership, contiguous window plan, per-cue hash syntax, context ownership, duplicate claim IDs, legacy correction status, SHA256-pinned registry, and fail-closed P0 status. `one_turn_run.py` **must** invoke the gate before terminal receipt; an injected failure must suppress any terminal research receipt.
- CI does **not** read private SRT/ZIP; independent source replay, historical price checks, official authority applicability, master 116 item-level relations, formal ResearchRun/SecondPassRegistry and blinded atomic-claim recall remain OPEN.
- PR #36 W25–W36 and PR #38 W37–W44 must be reconciled with PR #37's versioned manifest before imported as finalized canonical batches; do not merge PR #38's incorrect owner table as canonical truth.
- Formal unsealed research queue remains **#24 W00037**; first not-yet-read manual source window is **#24 W00045** (cue 792). Recording this quality-check sample does not itself advance ResearchRun.
- **P0 NO-GO**, P1 promotion blocked; no main/master116/P4-29 writes.
