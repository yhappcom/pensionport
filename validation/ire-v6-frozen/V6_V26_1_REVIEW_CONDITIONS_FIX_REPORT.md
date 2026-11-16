# V26.1 — Correct synthetic review-condition canonical ordering

Parent `1eab173a4d8e9efcfe9e5c6fb61979479be731bd` (V26). First exact-sha V6 workflow [run 42777384736](https://github.com/yhappcom/pensionport/actions/runs/42777384736) **failed** its V6 adversarial unit stage: 364 discovered tests, five errors with `CURRENT_CHAT_CONDITIONS_INVALID` from the new V26 ISA fixture's `missing_conditions` array not matching the legacy V22 canonical sorted/set list contract.

**Fix:** Reorder the two synthetic missing-condition strings in V26 test fixture to sorted unique order. The V26 production module, old V25 source, authority scope, financial values and test count (**18 new**, **364 unique**) are unchanged. Keep original V26 manifest and initial failing test/blob in history, pin corrected test in V26.1 manifest and require the final CI at new SHA.

This is a **test fixture contract correction**, not evidence of improved independent financial truth. Private SRT/excerpts are not published. V5/current law/personal tax, 791 expansion, independent gold and P0 quality gate stay NO-GO. Main, V5, master116, P4 29 remain unmodified.
