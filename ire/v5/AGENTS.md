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
