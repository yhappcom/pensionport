# GitHub Actions RUN-FAIL repeated incidents — cause and prevention (2026-11-05)

## Verified root causes

- Repeated **cancelled** actions on sequential one-file pushes arose from `concurrency: group ... cancel-in-progress: true` in both the V5 standalone and clean-room PR workflows. This is supersession and **not equivalent to test failure**.
- Actual **failure** was reproduced when an intentionally modified B01 test expected a safety-specific error code, but a generic aggregate summary mismatch failed earlier. Regression tests were repaired by changing validation order.
- Intermediate partial commits caused tests of `preflight.py` and `test_preflight.py` or terminal receipt logic to run against out-of-sync files. Individual commits can be internally inconsistent despite a later final successful commit.

## Preventive execution contract

- Build *one complete change set* offline: JSON ledger + master batch state + gate + tests + preflight/receipt updates + documentation.
- Validate syntax, full deterministic preflight, V5 unit tests, clean-room unit tests, V5 application tests, policy boundaries and protected files **before** moving the branch ref when a local checkout is available.
- Publish via GitHub `create_tree` → `create_commit` → `update_ref(expected_sha=<previous HEAD>,force=false)` once. This emits one coherent CI generation for the batch. `create_tree` / `create_commit` create unreachable objects before branch update and do not trigger push workflows.
- Verify latest exact SHA independently on the two checks. Treat `completed/success` as passed, `completed/failure` as true failed, and `cancelled` as superseded, never success.
- If CI fails, inspect the failing test's first exception and source. Apply a fix **with its regression**, and record the old and fixed run links. Never disable fail-closed checks or mutate historical claims to pass.
- Branch scope `ire/**` only for this clean-room PR. Do not modify `main`, original transcript contents, financial statement data, or claim approvals without evidentiary review.

## Batch B02 change

- Source video references: 30 occurrences / 27 distinct videos.
- Read 27 existing summary documents (one per distinct video; one is only a stub); remaining alternate pending document paths are **indexed but not claimed independently read**.
- 20 old claims receive source/context/time/legal-risk triage; newly certified financial facts = 0.
- Important detected crosswalk problems: `GOMHEE-C33` is foreign-dividend/ISA tax, while an existing V5 direct link is to ISA-to-pension transfer; `GOMHEE-C26` is theme concentration, not directly ETF NAV/tracking accuracy. Mark both `REVIEW_CANDIDATE`, do not silently rewrite historic verified graph.
- Maintain B01 unchanged and B03–B06 as pending (remaining 76 claims).

## Limits

GitHub text rules and atomic writes materially reduce preventable failures but do **not** guarantee zero legitimate test failures, infrastructure outages or permission errors. CI remains a safety signal, not a cosmetic metric.
