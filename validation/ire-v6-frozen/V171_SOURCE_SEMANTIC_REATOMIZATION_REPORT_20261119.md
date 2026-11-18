# V171 — Source-pinned semantic re-atomization (research correction, not approval)

2026-11-19 (KST). Parent: V170 draft PR #59; protected `main`, frozen V123/V126/V128 and all owner source files unchanged.

## Confirmed defect

The V162 real owner B0002 atom `C00018` was marked `kind=FACT` even though its source cues 141–143 combine **a factual generalization about people in major technology firms** with **the speaker's subjective impression of population size**. As a result, a factual acceptance of the original fused atom could incorrectly certify the speaker's impression. This is a source-meaning decomposition error, not primarily an evidence-download or SHA problem.

## Actual private-source pilot (read-only)

- Exact original 1,481-cue SRT SHA-256 `638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d`.
- Original B0002 exchange and native V123 review hashes checked; original native `C00018=OPEN`.
- **New draft only:** `C00018` becomes a source-attributed `OPINION` with cues 142–143. New `C00294` is a separately `OPEN` factual verification target with cues 141–142. Both keep the original 141–143 context, unknown speaker and unchanged condition/exception/numeric frame.
- Original reference cues 141–143 all retained; the entire B0002 cue↔claim census and all unchanged atom refs checked against the real private raw SRT. New B0002 draft has 32 atoms instead of 31.
- `C00294` is free in the *V162* 292-atom namespace; it has NOT been checked against the unavailable latest V166 293-atom namespace. Do **not** apply this draft to V166 without global ID reconciliation.
- The private draft, full source quotes and revised atom rows are stored outside public GitHub at `/mnt/data/v171/V171_PRIVATE_V162_B0002_C00018_REATOMIZATION_DRAFT.json`; only metadata appears here.
- The private source was NOT executed through the full frozen V6 auditor locally, because this runtime lacks the complete repository checkout. Local private source-quote and complete B0002 cue/claim structural checks passed. This is not a native V123 re-review and is not eligible for E4/E5.

## Public reusable code & frozen V6 synthetic regression

`v171_source_bound_reatomization.compile_split` verifies the pinned original source/exchange/review, requires actual ChatGPT-authored semantic analysis and original `OPEN` status, splits one mixed atom into distinct `FACT` and `OPINION` atoms, retains all prior source references and context/conditions/numbers, and calls **the untouched original `ire.v6.atomic_exchange.audit_host_atomic_exchange` before and after** to verify all cue dispositions. It requires a complete video-wide existing claim ID namespace. Existing exchange/review are never mutated.

The new V123 row set is only a **non-final draft**: the old host receipt is stale, all new rows stay OPEN, the revised source-first/counterexample/adjudication flags are false, and a new host structural batch plus full ChatGPT final review must occur before any native V123 result can be considered. No E4 issuer authentication, E5 parent publication or personal advice is possible via this helper.

CI tests are synthetic and prove structural software behavior, not model semantic recall or independent accuracy.

## Next blocking steps

1. Load latest private V166 193-OPEN exact revision, reconcile whether `C00018` still exists in the same form and allocate a globally unique new child ID without overwriting the owner review or SHA.
2. Execute a **genuine private native V6 restaging** of the revised B0002 exchange and re-check all 13 segments and inter-atom qualification links; then author complete new ChatGPT V123 review rows rather than converting one OPEN to ACCEPT by rule.
3. Authenticate first-party evidence and effective law where relevant. Require all 13 actual native V123/E4 approvals before ACID E5 parent publication. Until then: **E4 FAIL; E5/E6/E7 NOT_RUN; zero new knowledge**.