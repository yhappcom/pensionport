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
