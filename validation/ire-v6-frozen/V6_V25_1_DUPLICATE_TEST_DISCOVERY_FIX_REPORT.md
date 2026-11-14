# V25.1 — V25 test discovery duplication correction

Parent: `26f86c17f63d083850b89c460fc089a87deb2d35`. Scope: validation branch only; Draft PR #53.

## Finding from actual V25 CI
The source/manifest gates, six required V6 push jobs, and separate cleanroom all passed on the initial V25 SHA. However its V6 prepush output showed **360 discovered tests**: 328 prior + 18 V25 new cases + 14 duplicates of imported V24 `CurrentDecisionUtilityTests`. No assertions failed, but this inflated the apparent executed-case count.

## Correction
Moved the V24 test-helper class import **inside** the V25 fixture's `setUp()`, so the unittest loader does not discover its methods a second time under the V25 module. The 18 V25 regression methods and the V25 production module are unchanged. The corrected count should be **346**, with the same baseline 328 and exactly 18 V25 tests. The exact discovery cardinality is now checked by CI.

Historical V25 manifest and old test blob remain reachable and SHA-pinned; V25.1 manifest pins the corrected test blob and parent SHA. No source SRT, individual finance data or gold labels published.

The final exact-SHA GitHub Actions and independent cleanroom results must be read separately. P0 NO-GO, no personal-tax certification, PR stays Draft.
