# V25 — Source-specific semantic relevance and conditional ISA basis guard

- Date: 2026-11-10 (Asia/Seoul)
- Branch: `verify/ire-v6-p1-atomic-host-batch-20261109`
- Parent: `96fa870de76e7ac4420dc15c9784ac6f762ccdba`
- Status: **DEVELOPMENT ONLY / P0 NO-GO / DRAFT PR #53 / NO MAIN MERGE**
- No owner-private SRT, transcript excerpts, individual account details, sealed gold labels, or external model APIs in public source.

## Root defects identified

1. V24 compared a question's financial **topic name** to the concatenation of selected source claims. It could accept an IRP withdrawal claim for an IRP retirement-income question and fail to require each independent facet of a mixed IRP+ETF question.
2. V24 intentionally quarantined ISA personal tax calculations. It did not offer the distinction between the nominal additional **deductible contribution base** and the actual tax credit/refund.

## Additive V25 implementation

- `ire/v6/semantic_finance_decision_v25.py`: a new opt-in caller, leaving V24 and all earlier sources byte-identical.
- Each selected atom requires an exact question SHA-256 and proposition SHA-256, same-chat reviewer and date, one-to-one ID census, individual subtopic/facet coverage, a substantive rationale, and affirmative review of source attribution, stance, numeric scope, conditions and exceptions. Unrelated, uncertain, missing or wrong-facet selections fail closed **before the legacy V5 pipeline runs**. These are machine-checked **host assertions**, not independently measured semantic entailment.
- The V25 wrapper calls the real V24 path, retaining V5 P3, current-rule review, guarded V5 P2 arithmetic and all safety flags. V24 remains available for compatibility; callers requiring V25 protections must explicitly use `evaluate_current_question_v25`.
- ISA nominal additional eligible **contribution base** computation takes fixed current general-law parameters (60 days, 10%, KRW 3 million ceiling), two separate same-day official excerpts, SHA-pinned host term review and bounded nonnegative integer inputs. No output for actual tax credit/refund. It rejects mismatched input balances, future or reversed dates, stale evidence, unreviewed terms, and treats tax-year-spanning transfers as **OPEN** rather than resetting a cap.
- This is **illustrative, not a factual personal eligibility decision**. The source URL allowlist/host text checks do not authenticate entire original government document bytes. The official-law conditions need re-verification on each actual answer date.
- Source-to-question relation is still a lexical facet prefilter **plus same-chat review**, not full text entailment. Human-independent gold remains unavailable.

## Primary official context checked in chat on 2026-11-10

- NTS pension income/ISA contribution timing: https://ems.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7885&mi=6449
- NTS employment income, pension credit, extra 10% up to KRW 3m: https://j.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7875&mi=6439
- NTS ruling on carry-over unused ISA contribution credit base (complex cross-tax-year treatment): https://taxlaw.nts.go.kr/qt/USEQTA002P.do?ntstDcmId=200000000000006505

Links establish public rule *context only*; V25 accepts no unauthenticated URL alone as a personal tax computation license.

## Tests / limitations

- New **18 synthetic regression tests** include mixed-subject relevance, same-IRP wrong subtopic, omitted claim coverage, forged hashes, absent exception review, 60-day boundary, 10%/KRW 3m nominal base, prior-year block, stale evidence, prior-used cap, excessive transfers, forged legal terms.
- The existing full V6, IRE, V5, and cleanroom suites are the authoritative execution checks; CI results must be inspected on the **final exact SHA** before reporting PASS.
- No independent human-blind precision/recall score; no actual V25 private SRT full replay, personal suitability assessment, tax refund calculation, or order execution.
- Main, V5, protected 116, P4 29, prior V9–V24 code/manifests, and independent nine-video pre-registration remain untouched.
