# V26 — Known-candidate completeness census, ISA action suppression and prior-tranche abstention

**As-of:** 2026-11-10 (Asia/Seoul). **Scope:** Draft PR #53 validation branch, no main merge. **Status:** SOFTWARE-ONLY candidate; not release, P0 NO-GO.

## Actual owner-original limited re-examination (private; no source published)

- Access-controlled Library `1-70.zip`: SHA256 `00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd`, verified in current ChatGPT working environment.
- Video `8Zh1q4Ziv4c`: one 34-cue SRT original, bounded source-first manual examination. Seven selected *candidate* source spans/anchors were separately checked, covering the video's IRP early-withdrawal, ETF tax, pension tax deferral and excluded contribution-basis discussion. Four real-user-style questions were mapped to source cue hashes in a **private-only** receipt.
- Private bounded chat receipt hash: `bafa33115827879023a3f2fbdf55082ae15e6bde32e1b0f8201217823a3bf512`.
- **This was NOT a complete seven-claim-only atom census of 34 cues, independent gold, or an exact V26 Python integration replay.** The selected set deliberately does not claim all statements/exceptions were extracted. No private cue words, client accounts or exact source quotations were committed to GitHub.

## Defects in prior V25 route

1. `_audit_relevance` scanned **selected IDs only**. If extraction had found another candidate relevant to the question but that candidate was omitted from `selected_claim_ids`, the V25 validation could still pass. New `audit_candidate_census` demands a per-question, exact-hash, same-chat disposition for **every supplied atom** and blocks PENDING/UNCERTAIN/undisposed candidates before V5 P3/P2 execution.
2. An ISA transfer/order request could follow V25's `isa_law_review` branch and append numerical terms **after** V24 had rejected user order execution, e.g. the Korean imperative "ISA 만기자금 3천만원을 연금계좌로 옮겨줘". V26 recognizes execution intent before invoking the V25/V5 route and refuses the numeric path.
3. V25 assumed caller-supplied `previously_used_extra_base_krw` adequately reconciles earlier partial ISA transfers. There is no independent transfer/basis custody. V26 now withholds ISA example arithmetic entirely whenever either an earlier transfer or used extra base is reported, or a transfer straddles tax years. It does NOT treat zero self-reported used base as sufficient evidence of no previous partial transfer.

## V26 contract

- New **opt-in** `ire.v6.source_census_tax_guard_v26.evaluate_current_question_v26` preserves V25 and all historical modules without modification.
- Exact candidate census is a completeness gate **relative to the atoms already supplied**, not proof that ChatGPT extracted every atom from the original video.
- One-to-one source claim SHA / question SHA / current reviewer/date / checked context; every candidate is `SELECTED_RELEVANT` or `REVIEWED_OFF_TOPIC`. Relevant-unselected and unreviewable claims fail closed.
- ISA preflight validates intent, exact scenario fields, bounded integer KRW, dates and expiry balance *before V5 P3*. Safe first-time, same-tax-year illustration is labeled a **nominal additional deductible contribution base**, **never** actual tax-credit or refund. All prior-transaction, cross-year and unresolved-law cases stay OPEN.
- The V26 route calls V25 **without passing any ISA scenario**, so neither historical V5 ISA tax math nor V25's unsafe extra figure can leak. V26 owns the only narrow optional illustration. For ordinary non-ISA calculations it retains the V25/V24/V5 P2 guarded route.

## Current public-law context (general only)

- NTS income-tax credit guidance: https://j.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7875&mi=6439
- NTS pension contributions / ISA 60-day maturity condition and cross-tax-year balance rule: https://nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7885&mi=6605
- NTS written ruling on unused contribution-credit-base treatment in later tax periods: https://taxlaw.nts.go.kr/qt/USEQTA002P.do?ntstDcmId=200000000000006505

Official contexts were checked in chat on 2026-11-10, **not** signed and archived as independently authenticated publisher full documents. The cross-year statute is nuanced; V26 deliberately abstains rather than assigning a possibly inaccurate personal amount.

## Quantitative and governance restrictions

- 18 new synthetic regression methods: candidate-census omissions/contradictions/forged question hash; ISA user-order imperatives; first-transfer example separation; prior-used versus prior-deposit; year crossover; stale and unsupported input blocks.
- Exact-SHA CI, legacy IRE/V5 compatibility, cleanroom success and test discovery cardinality require independent confirmation on the final commit. Do not cite anticipated CI as passing.
- Never publish private original captions, promote personal tax eligibility or refund, place orders, certify independent semantic precision/recall, or authorize 791-video rollout.
- V26 is an **opt-in** adapter. The existing V24/V25 entrypoints remain reachable by direct Python import. Global production routing to V26 is not claimed.

**Required quality status:** `p0_go=False`, `independent_semantic_recall=False`, `personal_tax_or_order_approved=False`.
