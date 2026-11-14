# V27 — Whole 34-cue private-original source comparison and residual source-facet negative controls

**As-of:** 2026-11-10 KST. **Scope:** Draft PR #53, validation branch only. Main and protected V5/116/P4 unchanged. All private caption text stays outside public GitHub.

## 1. Actual owner-original inspection (PRIVATE LOCAL, NOT full V26 imported-path E2E)

Original owner Library `1-70.zip` read-only materialized in the current ChatGPT execution session; ZIP SHA-256 `00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd`. Actual 34-cue SRT `8Zh1q4Ziv4c` raw bytes SHA-256 `cbb57d372bc0fb5965052a776b5b945a5b82df3178d5c40dcdcc8b0d8239`. Original cue numbering, timestamps, UTF-8 decoding, and 34/34 positions checked. Private-only bounded same-chat candidate ledger: **16 candidates**, with at least one candidate span mapped to **33/34** cues and one introduction-only cue marked no independent financial atom. Four financial question groups mapped to separate source spans: IRP withdrawal 4 candidates, ETF/general-vs-pension taxation 3, excluded-basis withdrawal 2, and pension taxation/drawdown 4. Group counts overlap. The previous V26 seven-claim report was *limited anchor review*, not a final exhaustive census; do not characterize the 16 as nine independently proved misses.

Private receipt SHA: `4ef52f8439dab7375386cd93b2912027b6a4db970f006956290c1fe13f885ccb`. Private raw cues, quotations, descriptions, account data, and full original-linked cue digest list were **not** committed. The 34-cue examination used a private standalone Python byte/cue/claim-span audit, **not** a successfully imported and executed end-to-end V26/V5 pipeline. Candidate stance/source attribution remains CHATGPT developmental review, not blind human truth. Some ASR fragments split monetary units and tax rate suffixes across overlapping cues, requiring a human or host semantic check before promotion.

## 2. Verified current-rule *context*, not signed official-body attestation

- [Korea Exchange ETF tax rules](https://regulation.krx.co.kr/contents/RGL/03/03060105/RGL03060105.jsp): domestic-stock ETF price gains and non-domestic-stock ETF price gains are not blanket 15.4%-tax equivalent. Distribution taxation is separate.
- [National Law Information Center, Enforcement Decree of Employee Retirement Benefit Security Act, Article 18](https://law.go.kr/LSW/lsInfoP.do?lsiSeq=241795): individual IRP has specified statutory early withdrawal cases; the video's categorical statement requires correction/exception handling. Effective version for today must be reopened at actual advice time.
- Pension-savings non-deducted basis may be excluded from income tax depending on verified original contributions, withdrawal order, and taxation records; **no automatic personal disbursement approval**.

No original video publication date is substituted for current-law as-of. No firm legal conclusions about any individual's eligibility or actual refund.

## 3. Additional V27 defect and scope

V26 requires a supplied-candidate disposition for every input atom but still accepts a **same-facet relevant atom** marked `REVIEWED_OFF_TOPIC`. It also returns a suspicious-`NO_ATOM` cue count but can proceed with existing selected atoms without blocking that source-level omission. On this source, related IRP early-withdrawal, pension-basis and ETF tax claims occur in several noncontiguous spans; an omission can materially bias the final answer.

New **opt-in** `ire/v6/source_facet_audit_v27.py` intercepts before invoking V26/V25/V5:
1. Denies nonzero `unresolved_cues` and `suspicious_no_atom_cues` from the actual source-bound atomic audit.
2. Denies any unselected already-extracted claim sharing the question's conservative IRP/ETF/ISA/etc. fine-grained facet, despite a self-authored `REVIEWED_OFF_TOPIC` label.
3. Scans local ±1 original cue neighborhoods to catch split lexical financial terms and rejects relevant source areas without any selected citation anchor.
4. Preserves V26 exact-candidate census, numeric grounding, current-law quarantine, source hashes, no-orders, and fail-closed P0 status.

**Limitations:** Lexical facet matching can cause false positives and still cannot prove full atomic recall, contextual entailment, correct question-to-claim selection, personal legal applicability or independent financial advice. Old V24/V25/V26 entrypoints remain importable; production-wide route replacement is NOT claimed.

## 4. Regression/quality

Twelve new synthetic V27 tests cover source-to-question coverage, unselected same-facet candidates, forged `OFF_TOPIC`, suspicious no-atom financial cues, unresolved transcript cue, forged source quote, numeric token mutation, real V26/V24/V5 P3 mocked smoke, etc. Previous V26 364 + V27 12 = expected 376 unique V6 tests. Real V5 full-checkout operation remains in inherited V24 integration tests and GitHub CI. The private original-only manual audit must not be presented as independently validated E2E.

Independent human gold / true semantic precision-recall / original 791 videos / personal credit-refund / order execution: all **NOT CERTIFIED**, P0 NO-GO and PR Draft.

**Next requirement:** Build and run an authorized private-source full V26/V27 E2E replay with a source-complete atomic exchange, official evidence replay and real V5 root; separately obtain independent blind answer labels. Source-only 34-cue review is not sufficient.
