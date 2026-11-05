# IRE V5 agent workflow: CI RUN-FAIL prevention (mandatory)

Scope: all edits under `ire/v5/**` in `feat/ire-v5-vertical-slice-20261103`. Preserve `main`, the legacy data ledgers, private SRT/ZIP, and PR #13 until explicit authorization.

## Mandatory release rules

1. **No one-file-at-a-time pushes.** Assemble related research JSON, CI gate, regression tests, preflight expected list, one-turn receipt tests, and docs together **offline first**.
2. **Run preflight before publishing:** `python -m ire.v5.preflight --root .`; also run `python -m unittest discover -s ire/v5/tests -p 'test_*.py' -v`, `python -m unittest discover -s ire/tests -v`, and `python -m unittest discover -s ire/v5_app/tests -p 'test_*.py' -v`. When repository checkout is unavailable, perform deterministic source/schema cross-checks and state clearly that CI is the first full test.
3. **Atomic GitHub commit**, not piecemeal `create_file` / `update_file` pushes: stage a single Git tree, create exactly one commit with the current parent, then `update_ref` with `expected_sha` and `force=false`. If the branch changed, re-read and reconcile; never override someone else's updates.
4. **CI is fail-closed.** On any true `failure`, inspect the job logs, fix the cause and regression test, rerun a coherent atomic commit; do not disable tests, catch and suppress errors, or mark tests successful without execution.
5. **Cancelled != failed.** The workflows currently have `concurrency.cancel-in-progress: true`. Superseded runs are classified `cancelled`, not `failure`; prevent noisy cancellations by avoiding rapid consecutive pushes. Never misreport a cancelled run as a green test.
6. **Only report success for the latest exact commit SHA.** Both 'IRE V5 standalone transaction core' and 'Independent Research Engine - clean-room foundation' must show `completed/success` for the same HEAD after the final push. A prior green commit is not sufficient.
7. **Protected source scope:** keep public clean-room PR changes within `ire/**` or explicitly whitelisted workflow paths; never commit raw private transcript/ZIP, never edit historical approved originals or `main`, and never fabricate external verification or authorize personalized investment orders.
8. **Research approval rules stay active:** metadata/old summaries and CI success are not proof of financial facts. Only the active chat's source-matched original/official evidence is eligible for fact acceptance. Blind human review is not required by user policy.
9. **Escalate unresolved failures honestly:** infrastructure/network/permission failures cannot be guaranteed absent; record run IDs, exact failure category, change and final recheck. The objective is zero *avoidable* failures, not hiding real defects.

## Failure patterns already observed

- The early B01 tests expected time-sensitive/unverified source errors, but aggregate counter validation fired first. Fix: validate safety-critical conditions before derived summary count; preserve adversarial tests.
- `test_preflight.py` hard-coded stage order must change **in the same atomic commit** as `preflight.py`.
- `one_turn_run.py` receipt fields and `test_one_turn_run.py` expected fields must move together.
- Sequential GitHub writes triggered multiple `cancelled` runs because of the workflow concurrency setting. Use one atomic commit per verified batch.

**Never promise that all CI failures are impossible. Do not suppress a legitimate run failure to achieve a cosmetic success rate.**

## 60 existing claims as conditional advisory decision support (2026-11-05)

- Use `ire/v5/advisory60.py` + `advisory_integration/decision_routes_20261105.json`: **60/60 source references, 15 decision domains and 20 chat-authored routing scenarios**. This is a deterministic, non-generative router. Do not misreport passing scenario routing as live financial answer accuracy.
- B01~B03 source claims have `chat_evidence_fact_approved_this_batch=false` and `official_rule_current_source_verified_this_batch=false`: **no legacy claim may become a currently verified fact merely by indexing it**.
- Educational rule nodes from the existing 13-node graph are only **previously reviewed with explicit effective-date and source caveats**. Run current official-source verification in the active chat for financial rules used in any personal situation.
- Known semantic-mismatch edges **C26→ETF-NAV**, **C33→ISA-to-pension**, **C42→ISA-to-pension or pension-1500**, and **C52→DCA-arithmetic** must never prove the unrelated historical claim. The route catalog uses separately scoped domain-level educational nodes and the output marks them `not_directly_certified_by_route_claims=true`.
- User inputs requesting concrete orders, allocations or guaranteed returns fail closed, but the knowledge engine may provide conditional decision-checklist questions. Keep `personal_action_approved=false`.
- Mandatory CI gate `sixty_legacy_claim_advisory_decision_support` must appear in preflight and in the receipt test in the **same atomic commit**, followed by checking both workflow results for exactly the resulting HEAD SHA.

## Fresh real-question advisory validity checks (2026-11-05)

- `ire/v5/advisory60_validation.py` is the mandatory gate over **20 discovery/repair questions, 16 separate untuned holdout questions, 15 ChatGPT-authored official-source-matched narrow answers, five arithmetic calculations**. Require consistent code, fixture, preflight stage, regression tests, and one-turn receipt in the same atomic commit.
- Do not state **20/20 repaired cases** as unbiased new-question accuracy. **12/16** untuned holdout is the separate generalization result, with H03/H07/H09/H12 recorded as real misses; do not silently tune holdout or mark those 4 successes.
- Web sources were read by ChatGPT in the active turn, **not independently re-fetched/immutably snapshotted by CI**. Source-content alignment remains a chat-level claim under the user-approved policy, not a GitHub-certified legal fact.
- Personal action and guaranteed-return intents must be detected **before** no-route exits. No portfolio weight, securities order, or certainty of return can be released from an unsupported question.
- Every future change to route terms must run existing 20 + repair 20 + untouched holdout scenarios and track new, genuinely unexposed phrasing separately. A corrected prior test must never be passed off as fresh blind validation.

## MANDATORY Git tree path preservation pre-push (2026-11-05)

**Incident:** GitHub create_tree changes initially dropped 3 pre-existing files:
`ire/v5/advisory_integration/REPORT_60_ADVISORY_20261105.md`,
`ire/v5/advisory_integration/question_scenarios_20261105.json`,
`ire/v5/tests/test_advisory60.py`. This caused actual CI failure for SHA `25c6da5cdfb59d5592e7a55302b0425195bc1b19`. Do not diagnose this as merely superseded or cancelled.

**Required BEFORE each GitHub update_ref:**
1. Fetch recursively the HEAD Git tree of the parent commit, and the recursively expanded proposed Git tree. Ensure `truncated=false` for both.
2. Compute every old blob path missing in the new candidate; **abort publication on any deletion not explicitly approved by the user** (including tests, existing scenario data, reports, original evidence and independent workflow files). Check retained paths, not just SHA of modified blobs.
3. When staging through repeated `create_tree` operations, inspect the full candidate after all updates, because intermediate new directories can replace older sibling files. Restore missing blob entries by their exact previous Git SHA, then run the diff again.
4. Require `ire.v5.repository_tree_gate` in preflight before existing advisory gates. Confirm both `test_advisory60.py` and `test_advisory60_validation.py` were preserved.
5. Push **only after the comparison passes**, with one atomic `update_ref(expected_sha=HEAD,force=false)`. Then verify both workflows on the final HEAD.
6. GitHub CI cannot replace this pre-branch-update diff. A CI failure must be disclosed with exact cause and remediated, never suppressed.


## Actual final-answer semantic review (2026-11-05)
Mandatory gate: ire.v5.advisory_final_answer_review. Previous 12/12 structural checks were insufficient: direct-answer review found Q05/Q07/Q09/Q10 missing the requested judgment, baseline only 8/12. These four are now tuned regression questions, NOT a blind validation set. Do not rewrite historical baseline. Keep eight post-edit exploratory questions and failures visible. New source scopes: SEC general rebalancing (not KRX circuit regulations), issuer-specific foreign-currency RP, and issuer-specific CMA RP. No personal advice approval or live law verification by CI. Preserve all prior files in Git tree, update runner receipt and tests together.


## Final-answer quality rubric V2 — mandatory from 2026-11-05

1. Use `ire/v5/advisory_integration/P3_FINAL_ANSWER_STANDARD_V2_20261105.md` as the single release gate for user-visible answers. Score direct answer (20), official source/scope (25), independently recomputed math (20), comparative decision (15), risk/limits (10), and action safety (10). Minimum 90/100 AND zero hard-fail defects.
2. Never call the 12 exposed repaired cases or eight formerly failed exploratory cases “new blind accuracy”. Record the original 8/12 directness and 5/8 exploratory scores. Report post-fix outcomes separately.
3. After issuing the deterministic answer, actually assess final text for wrong mathematical calculation, option rankings, legal overclaim, fake source, missing conclusion and unauthorized order; no gate can be satisfied only by existence of route IDs.
4. Recheck cited issuer source document **content** in live chat. We found the earlier 한국투자증권 외화RP auto-service page did not contain the claimed direct issuer-specific risk provisions; use the verified 미래에셋증권 official foreign-RP product risk PDF with explicit insurance exclusion, issuer/FX risk and cautions. Do not use a mere service page as proof.
5. Every changed rubric/corpus/code file must land together with preflight, one-turn receipt and adversarial tests in one atomic commit. Compare recursive pre-commit and post-commit Git blob-path inventory to prevent deletion. Inspect both GitHub CI workflows for exact final HEAD.

## Engine-verification vs source-research gating (2026-11-05)

- **Software PASS is not research completion.** At basis HEAD `84b03a38ed6a959a10b036b535e936f29df0e9c1`, two workflows succeeded, 29/29 checks and 415 tests (one skipped). The 2026-11-05 full-source research readiness judgment is `SOFTWARE_VERIFIED_RESEARCH_VALIDATION_PENDING`. Do not report full engine GO.
- Run `python -m ire.v5.first_five_source_readiness_gate --root .` as part of every preflight. Without raw source it must return `full_research_engine_validation_completed=false` and `broad_corpus_research_go=false`.
- The **#1~#5 original batch is not the other five 201-300 source studies**. Inspect `ire/v5_app/batch_states/v5-gomhee-001-005-batch.json`: 5,129 SRT cues, 288 windows, five publicly recorded processed windows and 283 remaining/unconfirmed, `all_five_videos_research_complete=false`.
- Original private `1-100.zip` must be byte-verified without committing the raw SRT, using `python -m ire.v5.first_five_source_readiness_gate --root . --source-zip /private/1-100.zip`. Verify all five exact YouTube IDs, stored SHA-256, contiguous cues and valid timestamps. **Only** successful source verification unlocks *semantic pilot*, not broad video expansion.
- After source verification: process 288/288 windows; extract material finance claims with cue/timestamp provenance; recheck legal efficacy and exceptions; resolve duplicates/conflicts; test final advisory answers at rubric V2 (>=90 with zero hard fails). Mark unresolved evidence OPEN and do not promote it to personal advice.
- User has declined separate external blind evaluation engine and external LLM API; these are **not prerequisites** for a bounded internal pilot. Nevertheless, no independent verification may be claimed, and scope limitations are non-negotiable.
- The source file currently visible to the chat runtime is `201-300.zip`, and it must never be relabeled or treated as `1-100.zip`. Public V5 encrypted snapshots do not prove an accessible plaintext.
- Do not edit `main`, canonical source claim ledger, existing approved education nodes, or any private transcript. Preserve all Git blob paths and run both CI workflows on final exact HEAD.

## 2026-11-05 original #1~#5 SRT found in personal Library

- After initial source-blocked verdict, previous user Library folder `박곰희TV_원본확보` yielded `1-70.zip`. The *exact five source SRTs*, indexed by video ID, matched all saved per-SRT SHA-256 bytes; all **5,129/5,129** numbered and time-ordered cues validated.
- The verified raw archive SHA-256 is `00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd`; receipt `ire/v5/validation/first_five_raw_srt_integrity_receipt_20261105.json`. No original text or archive bytes go into Git.
- `1-70.zip` is acceptable even though the originally anticipated archive name was `1-100.zip`, because the identical raw SRT bytes and SHA-256 of all five video IDs were actually matched.
- This completes **source integrity** only. It unlocks **the first five private-SRT semantic and financial-evidence pilot**, NOT full corpus research approval or future personal trade advice. To re-run byte verification in a new runtime, supply the owner Library source and use `python -m ire.v5.first_five_source_readiness_gate --source-zip /secure/1-70.zip`.
- GitHub CI only verifies the recorded receipt/schema/hash correspondence; it cannot directly reopen the owner Library archive. Do not claim that a CI pass is an independent byte recheck.



## 2026-11-05 first-five real SRT semantic quality audit — **research NO-GO**

- Owner Library `1-70.zip` source SHA and 5,129 numbered cues passed. After inspecting original text, 25 selected high-risk source spans (892 distinct cues) were actually compared with 116-claim ledger, 60-claim advisory route and issuer/regulator primary sources. These cases are **risk-targeted, non-blind, not 288/288 window comprehensive semantic research**.
- Artifacts: `ire/v5/validation/first_five_original_qa_25_20261105.json` (25 source-span hashes, safeguards, six official/issuer references) and `ire/v5/validation/FIVE_ORIGINAL_QUALITY_EVALUATION_20261105.md`. Source text/private archive is **never** committed.
- **Critical decision-safety watchlist:** F03 pension 1500 tax threshold ≠ hard withdrawal prohibition; F08 CMA RP protection/credit risk; F14 ETF parking 3% ≠ guaranteed; F15 insurance surrender vs dividend not income equivalent; F22 employer stock risk; F23 employer industry ETF human-capital concentration. Do not convert the presenter’s hypothetical education into unconditional trade orders.
- Research/knowledge connection gap confirmed: #1/#2 SRT video IDs have no direct entry in 116 canonical claims; #3/#4/#5 correspond to C64/C63/C62, outside first-60 advisory routes because B04 is pending. Do not claim tested P0-P3 path has integrated these five original videos.
- Run `python -m ire.v5.first_five_quality_gate --root .` in every preflight. With an accessible private archive, `--source-zip /secure/1-70.zip` additionally reopens 25 original spans and verifies their text SHA. CI has **no private raw source**, so static ledger crosschecks are distinct from original byte proof.
- Broad expansion, user portfolio advice and five-video entire-semantic research: **NO-GO**. Release only after all 288 original source windows have semantic evidence decisions, critical cases are scoped/verified and the actual query → source span → integrated knowledge → correct final answer path is tested. No independent-human-blind gate required by owner policy, but no false independent quality claims.
