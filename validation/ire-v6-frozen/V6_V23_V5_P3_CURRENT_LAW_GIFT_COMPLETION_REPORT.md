# IRE V6 V23 — V5 P3 actual answer pipeline route to V22 CURRENT-law review; ten remaining gift atoms

**Execution date:** 2026-11-10 KST. **Baseline branch SHA:** `22a0a3cd3e4965fd3549aca2d47257c8058660fc` (Draft PR #53). **Status:** new V6-only adapter; `main`/V5/116/P4 historical knowledge preserved, not merged, P0 NO-GO.

## 1. Change contract and actual integration boundary

The user's decision: **when advising today**, compare historical video claims against laws effective **on the answer date**. Assess historical speaker accuracy by rules effective then only when that is the explicit research question. Do not incorrectly retro-apply current law to completed historical transactions.

The protected original V5 P3 implementation (`ire/v5/advisory_answer_pipeline.py`) cannot be changed on this verification branch. The additive **`ire.v6.current_advisory_bridge.answer_with_current_law(...)`** invokes the *real* V5 P3 `answer(root, question, scenario)` and then uses V22 `audit_current_law_reassessment` to generate the **current-law-controlled final answer**. V5's original text is only hashed for audit, **never printed as a current statute**, because its source snapshot was collected 2026-11-05 and may be stale. V5's analyzed domain/fact IDs remain lineage, not proof of currently applicable law.

Runtime sequence:

1. Bind the original SRT bytes, every cue, prior ChatGPT atom proposals, selected IDs and immutable claims, today’s `current_as_of`, official allowlisted HTTPS excerpts and scope notes, and ChatGPT-hosted judgments.
2. Verify all source/data/rule dates and IDs with V22. Future/expired/stale official excerpts, failed cue/claim hash or forged review classifications **block output**; unreviewed and fact-unknown atoms remain OPEN.
3. Invoke the original V5 P3 answer function, verify its schema/question and that no orders/personal financial recommendations were approved.
4. Compose a **new** current-law response from the V22 judgments and current official rule references. The legacy P3 answer body is not reused. The output labels `CURRENT_RULE_CONTRADICTS_SOURCE`, `CURRENT_RULE_SCOPE_MISSING`, `CURRENT_GENERAL_RULE_CONSISTENT_CONDITIONAL`, `CURRENT_FACT_OR_APPLICABILITY_UNKNOWN` and non-regulatory opinions separately, with conditions and current official URLs.
5. Return an audit receipt with original P3 answer SHA, V22 reassessment SHA, current date, active official URLs and pending claim IDs; `p0_go=false`, `individual_advice_approved=false`, `independent_gold=false`.

**Deployment limitation:** Existing callers that directly invoke `ire.v5.advisory_answer_pipeline.answer` still call unchanged V5. This change supplies and tests a **concrete V6 integration entrypoint**; there is no global monkey-patch, no forced rewrite of protected V5 code, and no assertion that all unrelated external V5 interfaces automatically start using V23. V6 chat orchestration must choose this entrypoint for current-law questions and supply private evidence and decisions.

## 2. Real original V22 gift pending ten cases resolved, preserving history

User-owned `1-70.zip` source SHA-256: `00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd`. Exact original gift video `yDt8Ki7d_Yk`, **32 cues**, same previous **16 ChatGPT-proposed atomic claims**, same original source/manifest digests. The prior V22 development receipt SHA is `a172adb4f530f143908dcd8fed17d698f7be988400738ce131e65673916df693`. The other ten previously OPEN claim IDs were checked against **2026-11-10 current law**, without changing the original 6 earlier chat decisions.

| Original V22 pending claim | Today’s conservative interpretation |
|---|---|
| C00001 child gift deduction recommendation | Conditionally consistent; recipient residency, parent relationship, ten-year history and transaction date necessary |
| C00006 age-thirty 5,000만원 gift example | Conditionally consistent; exact ten-year deduction history and gift-date boundary necessary |
| C00009 progressive gift-tax brackets | General rule conditionally consistent; do not conflate gross gift value with taxable base |
| C00010 first 1억원 tax base bracket at 10% | Conditionally consistent after deductions and excluded special categories |
| C00011 “5억원 이하 20%” | **Scope omission:** proper bracket is **over 1억원 through 5억원**, with 1,000만원 progressive offset |
| C00012 “10억원 이하 30%” | **Scope omission:** proper bracket is **over 5억원 through 10억원**, with 6,000만원 progressive offset |
| C00013 inflation purchasing power | Non-regulatory economic generalization, not a statutorily verified outcome |
| C00014 gift-money investment in equities/ETFs | Non-regulatory opinion, no investment-return guarantee |
| C00015 asset-gap assertion “tenfold” | **OPEN FACT:** absent population, years, metric and authority statistics; not approved |
| C00016 begin investing early | Non-regulatory educational opinion, separate risk/suitability checks |

**Full 16 old claims after new append-only host review:** 9 conditional-general-rule, **3 scope-missing**, 3 non-regulatory opinions, **1 fact unknown**; **16/16 received a host review**; zero `CHATGPT_REVIEW_REQUIRED` *does not mean* zero substantive unresolved facts. The “tenfold gap” remains `CURRENT_FACT_OR_APPLICABILITY_UNKNOWN`. Source SHA `187948e6226ddf137a07a12f99cc064e67a3dea9d5f795af832d4f09e4acdbf8`. V23 safe reassessment receipt SHA `fdd46341f5360ff8b24d8670278242ab79c7065c9af4aaf7640bc557df467c62`.

**Official general-rule sources consulted:** [NTS current gift tax rates](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7960&mi=6538), [NTS 10-year deduction and taxable base](https://j.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7728&mi=2340), [NTS codified Articles 53 and 53-2](https://taxlaw.nts.go.kr/st/USESTA002P.do?ntstBscId=100000000000001561&ntstSysClCd=01&ntstTlawClCd=109). Specific personal tax results, existence of an eligibility exception, actual historic transfer date and native full-text signed primary body have not been independently certified. V22/23 use the **source-verified domain + model-created excerpt digest**, *not official source signature*.

## 3. Tests and actual V5 invocation level

- New additive modules: `ire/v6/current_advisory_bridge.py`, `ire/v6/tests/test_current_advisory_bridge.py`.
- In the private 816-file partial source checkout, **12 synthetic V23 guard tests pass**, plus one **canonical complete-checkout true-V5 P3 smoke** intentionally skips if the protected V5 master fixture is absent. The old V22 tests remain separate and pass. (After CI in complete Git checkout, record exact status of the true-V5 smoke.)
- A private 32-cue real-original gift replay selected four progressive-rate claims and passed the V22 source-first -> mock-P3 fixture -> safe V23 answer pipeline, verifying gross gift-tax bracket lower-bound/offset notes and no stale P3 text. **This local private P3 was mocked**, not falsely claimed a real completed V5 P3 invocation. The **actual** V5 call is executed by the new adapter in complete GitHub checkout tests.
- Legacy V5 P3 content is **not copied** into current-law output, even on a valid old baseline; the output carries SHA and domain/fact lineage only. The bridge rejects model-forged independent golden labels, unsupported unqualified law acceptance, bad official URL/hash/date, ordered/duplicate/nonexistent source claim selections, unauthorized order approval and V5 question/schema drift.
- This version's current-law response requires an explicit **ChatGPT-selected, source-pinned claim list**. Natural-language question-to-source relevance remains a ChatGPT responsibility, not deterministic completeness proof. CLI/global V5 default path not rewritten.

## 4. Research and release guardrails

The previous 9-video/6,829-cue pre-registration, historical V9–V22 source/manifest/CI pins, existing V5/116/P4 29, and `main` are immutable. Private source text, candidate propositions, private current-law decisions, actual individual tax data and private SQLite remain **off public GitHub**. No separate model API, no automatic trades/transfers, no personal tax outcome approval. **Independent human semantic gold absent, true precision and recall unmeasured, G6/P0 NO-GO, S6 original private archive inaccessible, S7 791-video expansion BLOCKED**. New adapter routing is developer functionality, not a final externally audited financial advice deployment.

## 5. Next safe step

Use the V6 `answer_with_current_law` path on actual ChatGPT conversations containing supplied original sources and up-to-date official excerpts. Prioritize an unrelated original unseen research video, newly recheck legal text on the day of user answer, validate claim-selection relevance and review the remaining substantive fact-unknown item with official statistics rather than force-filling a gold. Re-test the same exact commit in canonical full repo CI; report software vs semantic quality independently.
