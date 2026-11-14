# V30 — actual private-original semantic warning repair, missing age atom and complete structural numeric accounting

**Date:** 2026-11-10 KST. **Target:** Draft PR #53 / validation branch. **Original SRT:** private owner Library `1-70.zip`, `1-70/youtube-transcript-8Zh1q4Ziv4c.srt`, SRT SHA-256 `cbb57d372bc0fb5965052a776b5b945a5b82df3178d5c40dcd30cdcc8b0d8239`; original 34 cues. No source lines, private exchange or full answers published.

## 1. The exact two reported semantic-risk alerts, source correction, and adjudication

Original `ire.v6.semantic_risk.audit_semantic_risks` on the actual 16-claim exchange returned **two** alerts, both attached to exact source cue hash and candidate ID:

- **C00002, cue #5 `UNMAPPED_EXCEPTION_IN_MODEL_CONTEXT`**: an original question's concessive/contrast marker connects a zero-or-near-zero tax-credit situation to asking whether the contributions should continue. The model did not encode the concessive marker. The revised **QUOTED/QUESTION** frame explicitly includes the premise and question and binds cue #5 in `exception_cue_indices`. This is a **discourse concession**, not a statutory financial exception; do not interpret the cue as a new tax exemption. Adjudication `REMODELED_EXCEPTION` linked to the original SHA-pinned cue.
- **C00015, cue #29 `UNMAPPED_CONDITION_IN_MODEL_CONTEXT`**: the original restricted the withdrawal convenience assertion to a case of urgent liquidity need, with words divided across adjacent original subtitle cues. The corrected claim is **CONDITIONAL**, source context [26–30], condition indices [28,29]. `만약의` in the source is contingency language, not authorization for unconditional anytime withdrawal. Adjudication `REMODELED_CONDITION` linked to the exact source cue.

The original before/after source and manifest are byte-identical. The unchanged historic V14 semantic-risk function and V17 chat review are called **as-is**; neither was weakened. **Actual post-repair risk inventory: 0/2 remaining**, with zero newly introduced cases. Source-bound case SHA + cue SHA + reviewed atom hash pins prevent a fresh unexplained rewrite. This is **same-chat semantic triage**, not independent human adjudication.

## 2. Additional original-source omission found

The earlier 16 candidates included 33/34 original cue positions and omitted a context-bearing age decade in original cue #1. Introduced **C00017**, an explicitly source-anchored factual scenario condition (person in their 40s). Revised source set: **17 candidates / 34 of 34 cues**; this matters to eligibility and future pension planning. The new context candidate makes the previously uncovered first original cue auditable.

Original numeric census from real `ire.v6.atomic_exchange.NUMBER`: **11 occurrences** (including age, contributions, decision tax, quoted rates, first eligible age, and years). Previously `numeric_references` on the original 16 candidates were empty despite the cue-level `numeric_tokens` list; the original code did not require numeric-to-claim linkage. Added exact quote-bound `numeric_references` and checked **11/11 source numeric occurrences** against the revised claims. This is a **literal token-level accounting measure**, NOT independently verified numerical unit semantics, cash flows, tax amounts, legal ages or full atomic claim recall. Some ASR tokens have omitted units; do not infer 600/300 as absolute KRW amounts or 3.3 alone as a certified rate without contextual review.

## 3. Executed real E2E after corrections

The same 3 real private-original pathways were re-executed using the **real V28→V29→V27→V26→V25→V24→V23→V22→V5 P3 route** (no mocked V5 P3). New optional V30 preflight checks exact source, two explicit source-bound review decisions, every original cue and numeric token, all changed/new atom IDs, and a cryptographic commitment of the **complete approved revised atom frames**. The V29 code-blob pin includes the new V30 module (Git blob SHA pinned in manifest), and V30 extends the prior hash-only final-answer chain.

All three:
- IRP early withdrawal, final receipt `2479dfb8215806e36174dbbe26789e52bb7eb80917a18e77590456be1309ddbb`.
- ETF gain taxation, final receipt `ebacf110bfe95c401dff4409f0916f855bb16844dcf41fa844f0f819b6e8c137`.
- Pension savings non-deducted principal, final receipt `bde7fd526a58e73cecea6be11d86972f8babb8272e7311541b4cf5945f93996a`.

The final textual answer SHA-256 values remained equal to prior V29, meaning the new source-quality preflight did not silently rewrite the answer. The raw transcript/answer/exchange remains in private local storage only. The public receipt `validation/ire-v6-frozen/V6_V30_REPAIRED_REAL_PRIVATE_REPLAY_HASH_ONLY_RECEIPTS.json` exposes only hashes, counts, and conservative flags.

New V30 **13 synthetic negative/positive tests** include: exact source cue/number closure; unreviewed numerical omissions; added context claim; unpinned reviewed-claim rewrite; duplicated/forged semantic adjudication; conditions not actually mapped; fake citations; and ensuring no P0/independent-gold claim. Local full V6 discovery and execution: **417/417 PASS**, previous V29 404 +13. The exact new GitHub commit CI must independently pass before software PASS is asserted.

## 4. Independent gold: blocked by real provenance, not hidden by self-scoring

The project already has a pre-registered **nine-video 6,829-cue prospective blind cohort** in `validation/ire-v6-frozen/BLIND_PREREGISTRATION_V1.json`, with precommit SHA `77280d7f917a7f8a25437157b78081147d17088f0b269a90275bac8bc1cbe296`. This is a **different protected prospective cohort** and must not be replaced with the heavily examined 34-cue source. It requires two source-first reviewers who have not seen model predictions and a separate dispute adjudicator, plus at least **50 independent gold atoms / 30 high-risk** (protocol targets: precision >= 95%, recall >= 90%, high-risk recall >= 95%). In the existing registration `gold_commitment_sha256` is **null** and no authenticated reviewer submissions or adjudicated gold are present. `ire.v6.blind_custody` and `ire.v6.evaluation` already enforce signed-custody arithmetic, but **signatures alone do not verify real-world identity or prior blindness**.

It would be incorrect to compute 'independent semantic precision/recall' from today's own 17 source labels or pretend additional model labels are independent humans. The decisive bottleneck is **authentically independent, blinded source-first reference labels**, not more software fixtures. The appropriate next action after this V30 structural repair is to satisfy that already frozen blind protocol, not to open the 791-video rollout.

## 5. Quality release decision

- **Actual current ChatGPT source-bound semantic warning triage: PASS (2→0)**.
- **Actual original source cue and numeric token accounting: PASS (34/34; 11/11)**.
- **Actual revised three-case private E2E replay: PASS**.
- **Original atomic meaning independently adjudicated: NOT PROVEN**.
- **Independent blinded semantic precision / recall: NOT MEASURED**, must retain NULL.
- **Personal account statutory applicability, tax refund or trade authorization: NOT APPROVED**.
- **Software CI: must be verified at final commit; GitHub synthetic tests never imply private source was in CI**.

**P0 RESEARCH-QUALITY NO-GO.** PR #53 stays Draft, no change to `main`/original V5/V6/116 master/P4 29 or past frozen manifests. Claim-accounting structural completion for this ONE SOURCE and three tested questions is not full source semantic or 791-video correctness.

Current public background sources: [KRX ETF product-category tax rules](https://regulation.krx.co.kr/contents/RGL/03/03060105/RGL03060105.jsp) and [2026 National Assembly Budget Office tax reference](https://www.nabo.go.kr/board/file/down.do?fid=33319156). These aid rule-scope comparison but do not replace independent source-first gold annotations. 
