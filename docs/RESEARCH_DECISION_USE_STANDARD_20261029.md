# Research Completion and Investment Decision-Use Standard

**Status:** Active research operating baseline  
**Adopted:** 2026-10-29  
**Scope:** Educational source review, cross-video knowledge integration, and conditional decision support.  
**Canonical location:** This file on `main`; other branches should **link to it**, not maintain competing copies.

## 1. Goal and source-of-truth hierarchy

The objective is a traceable investment knowledge base that can eventually support **accurate, conditional decisions**. Research throughput and the number of extracted principles are not proxies for decision quality.

This document supplements, but does **not** supersede:
1. [WORKFLOW.md](../WORKFLOW.md) — the V3 per-video record, unique-video counting, readback, and single-write rules.
2. The research branch's [independent-evidence policy](https://github.com/yhappcom/pensionport/blob/feat/subtitles-incremental-registry-20261009/docs/INVESTMENT_RESEARCH_VERIFICATION_POLICY_20261012.md) — source verification, claim status, and unresolved evidence.
3. The [safe batch/CI policy](https://github.com/yhappcom/pensionport/blob/feat/subtitles-incremental-registry-20261009/docs/SUBTITLE_CI_PUSH_POLICY_20261026.md) — preflight, final CI success, and preserving approved records.
4. [Research item 001 maturity review](../research/001_research_maturity.md) — the historical, source-limited evaluation, not a general advisory certification.
5. The [item 001 decision-readiness audit](https://github.com/yhappcom/pensionport/blob/feat/subtitles-incremental-registry-20261009/data/synthesis/investment_knowledge_v4/reviews/v4_001_decision_readiness_audit_20261029.json) — the traceable L1–L4 classifications.

**Precedence:** Source/evidence and CI gates remain binding. This document defines *incremental decision-use evaluation* and avoids reopening closed educational studies without a material trigger. A maturity score does not override an evidence gate.

## 2. Baseline: research item 001 (do not automatically rework)

**Educational study:** conditionally closed, with source-specific limits and unresolved claims retained.  
**Research maturity:** **75/100**, analyst judgment, not an independently certified metric and not advisory accuracy.

| Dimension | Maximum | Recorded score |
|---|---:|---:|
| Source integrity and traceability | 20 | 19 |
| Knowledge extraction and structure | 25 | 23 |
| Independent fact, rule, and calculation checks | 30 | 22 |
| Decision-use readiness | 25 | 11 |
| **Total** | **100** | **75** |

The existing first-item review records 1,195 source-text cues, 42 detailed review claims, and 12 educational principles. Its decision audit demonstrated hypothetical numerical comparison for seven principles (L2); the other five are screening-only (L1). **L3: 0; L4: 0.** These are *capability classifications*, not percentages of forecast accuracy.

Separately estimated, noncertified maturity by purpose: knowledge extraction ~90%; principle validation ~75%; strategy comparison ~60%; personalized advisory use ~25%. Do not describe any of these as a tested investment success rate.

**Closure rule:** Do not reanalyze item 001 merely to raise 75 to 90, and do not copy its 42 existing claims into new records. Reopen *only the affected claim* when a new primary source, source discrepancy, regulatory change, model defect, contradiction, or decision-blocking evidence gap materially changes its validity. Preserve the original assessment and link an evidence-based amendment rather than silently overwriting history.

## 3. Three separate statuses — never conflate them

| Layer | Meaning | Proof / acceptance |
|---|---|---|
| **Video study** | The video was actually reviewed from adequate identified content, with source limits and claim evidence | V3 `COMPLETE` or `PARTIAL` under WORKFLOW.md and the research branch's evidence gate; final saved record, readback, and applicable CI success |
| **Investment knowledge** | A claim/principle was independently assessed and linked to other research | Claim status `PRIMARY_CONFIRMED`, `QUALIFIED`, `HYPOTHETICAL`, `CONTRADICTED`, or `OPEN`; authoritative sources, effective date, scope, and corrections |
| **Decision use** | A specific alternative can be compared, ranked, or acted on for an investor | Evidence-based L1–L4 grading, explicit inputs, assumptions, counterexamples, stop rules, and independent model tests |

A study may be educationally complete while individual assertions are `OPEN`. Educational closure is **not** certification that audio/video has been verified, a modeled return is achievable, or a personal investment action is suitable.

## 4. Decision-use ladder

- **L1 — Screening:** Check rule, contract, risk, tax classification, documentation needs, and disqualifying conditions. No individualized payoff or optimal choice.
- **L2 — Hypothetical comparison:** Reproducible numeric calculations with stated hypothetical inputs, costs, taxes, sensitivities, and failure cases. No personal strategy ranking.
- **L3 — Conditional personalized comparison:** Requires verified investor/account/contract data, current official rules and market inputs, documented suitability, model checks, and explicit limits. Not demonstrated by item 001.
- **L4 — Action readiness:** Independently validated action/implementation conditions, fresh data, authorization, operational risk checks, and applicable professional/regulatory boundaries. Not demonstrated by item 001.

**Never infer L3/L4 from a high study score, fluent narrative, or a successful hypothetical calculation.** If any action-changing input or applicable rule is missing, stop at L1/L2 and state exactly what is missing. A research project does not provide licensed investment advice or authorize orders.

## 5. Standard decision-model record (when a new model is warranted)

Before building a new model, search existing `knowledge/`, `synthesis/`, V4 reviews, and related source records; reuse an existing claim/principle/model ID rather than duplicating it. Maintain a single canonical decision record when implementation begins, linked to its supporting source IDs.

Minimum fields to document in that record:

| Field | Required content |
|---|---|
| `decision_id`, `linked_principles` | Stable ID, source record pointers, existing/new/reinforce/extend/change/conflict classification |
| `decision_question`, `alternatives` | Exact investor decision and comparable options, including a do-nothing baseline |
| `required_inputs`, `missing_inputs` | Eligibility, age/horizon, balances, contribution/tax-basis ledgers, product/contract constraints, liquidity, risk tolerance; **only fields relevant to this decision** |
| `model_assumptions` | Return/discount/inflation scenarios, calendar and tax dates, units, compounding, contribution/withdrawal timing |
| `net_outcomes`, `risk_metrics` | After-tax/after-cost comparisons, downside, sequence risk, uncertainty; avoid return guarantees |
| `sensitivity`, `counterexamples` | Break-even and conditions that reverse the ranking; missing-data stress cases |
| `evidence`, `as_of` | Primary citations, effective dates, source limitations, independent calculation review |
| `stop_rules`, `decision_level`, `test_results` | Disqualifying conditions, L1–L4, test inputs/expected outcomes, pass/fail, audit timestamp |

Do not create a global duplicated ledger simply to document this policy. A machine-readable schema or decision-record directory should be introduced only when the first substantive decision model is actually implemented and independently validated.

## 6. Incremental workflow for the next and subsequent videos

1. **Preflight — reuse first.** Inspect the fixed roster and existing records for the precise source ID. Determine whether the source is already fully analyzed, merely registered, partial, or waiting on evidence. Do not treat historical registry entries or `state/progress.json` as proof of analysis.
2. **Read original evidence once per relevant source scope.** Confirm the correct source ID and source-text integrity; retain timecoded evidence and note unverified audio/frames. Do not publish full source transcripts or private financial records.
3. **Extract and reconcile.** Link each relevant atomic claim to an existing principle or a justified new one; record `NEW / REINFORCE / EXTEND / CHANGE / CONFLICT / TIME_SENSITIVE`. An unchanged, corroborated principle is a legitimate finding; **do not invent a new principle to increase counts**.
4. **Verify what matters.** Check current official rules and effective dates for taxes, pensions, accounts, products, and calculations; distinguish the source's historical assertion, a simulated example, and today's operative rule. Preserve contradictions and `OPEN` items.
5. **Assess two outcomes independently.** (a) Video-study/source quality, with an **aspirational 90/100 maturity target**, not a mandatory CI threshold or a reason to withhold legitimate source-limited closure; (b) practical decision-use L1–L4, requiring evidence and explicit missing inputs.
6. **Save only justified deltas.** Follow the existing V3 single validated analysis record and the research branch's preflight/batch rules. Reference existing source and knowledge artifacts; amend central knowledge only for genuinely changed/verified information, not for every episode or run.
7. **Verify and report.** Read the saved record back, confirm actual final CI outcome, list newly verified records separately from existing/partial/registered items, report new or strengthened principles, changes in L-level, and unresolved blockers. Never count a documentation-only commit as a newly completed video.

## 7. Rework triggers and stop conditions

| Event | Action |
|---|---|
| Existing study and evidence unchanged | Reuse canonical record; no second full analysis |
| New video reinforces an existing principle | Add source cross-reference/evidence delta, without cloning principle text |
| New official rule or effective date | Update only impacted claim/model, retain superseded date and citation |
| New conflicting source or failed calculation | Quarantine impacted conclusion; reopen and document resolution |
| Missing source detail that could reverse a decision | `OPEN`, keep L1/L2 ceiling, no individual ranking/action |
| Failed or pending CI / missing saved-file readback | Do not mark new study complete |
| GitHub security/safety tool block | Stop further writes for that run; do not rephrase/re-route to bypass it |

## 8. Research success measures

Track separately: (1) source-grounded unique video studies, (2) independently verified versus qualified/open claims, (3) nonduplicative cross-video principles, (4) independently reproducible decision comparisons and stress tests, and (5) appropriate stop decisions on incomplete investor data.

**Priority:** Quality of verified decisions and refusal/stop behavior takes precedence over study count. Continue beyond item 001 rather than holding the entire series open to exhaust every possible personalized-use gap in one source.

**Public repository privacy:** Do not insert a creator/channel name, full transcript, long source quotations, account positions, or private money-flow details into this policy or its README links. Existing source-specific evidence remains subject to separate public-exposure review.
