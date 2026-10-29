# V4 Quantitative Regression and Provenance Gate

**Effective:** 2026-10-30  
**Active research branch:** `feat/subtitles-incremental-registry-20261009`  
**Guarded source:** `data/synthesis/investment_knowledge_v4/models/decision_models_001_005_20261030.json`  
**Executable gate:** `scripts/verify_v4_quant_models.py`

## What changed

The existing subtitle-evidence gate did not include `data/synthesis/investment_knowledge_v4/**` in its trigger list. Therefore edits of V4 numerical model JSON alone could miss GitHub Actions entirely. Both **push** and **pull_request** path filters now include the V4 data tree, this test script and this protocol. Every relevant run executes:

```bash
python -B scripts/verify_v4_quant_models.py --self-test
python -B scripts/verify_v4_quant_models.py --root .
```

This executable gate re-evaluates **all nine current hypothetical numeric models** from their declared inputs and compares with their stored outputs, including NPS discounted cash flows, pension accumulation and withdrawal, ISA taxable-gain examples, market-path DCA returns, staged retirement investment, loss-recovery ratios and TDF fee sensitivity. It also checks the 001–005 research manifest and per-video claim, model and source-fingerprint links against existing V3/pilot records. Missing/duplicate models, mismatched results, absent reviews, approval inflation and unrecognized model IDs cause failure.

The `--self-test` mode performs two **negative mutation checks**: changing a stored return value and deleting a model must both be rejected. Ordinary mode verifies the actual repository; neither mode writes source data or generated output into Git.

```bash
# Run before staging/pushing a V4 batch:
python -B scripts/verify_v4_quant_models.py --root .
# Confirm failure detection:
python -B scripts/verify_v4_quant_models.py --self-test
# After staging the complete review batch:
python -B scripts/preflight_subtitle_batch.py
```

The V3 local preflight now invokes the model gate when staged changes include V4 synthesis or the model verifier. The existing V3 evidence audit, SRT/ZIP publication prohibition, branch scope, final CI rule and approved records are **not weakened or removed**.

## Validation boundaries and future models

- This is a **deterministic numerical regression test**, not a historical return backtest, probability estimate, official legal interpretation, product quote, or validation of an investor's personal after-tax outcome. Synthetic market paths must remain labelled hypothetical.
- It validates that the model's current input assumptions reproduce the stored outputs. It **cannot** establish that assumed rates or retirement outcomes are true, or detect a coordinated malicious edit of both assumptions and outputs. Primary-source and suitability checks remain separate.
- When adding a new decision model, extend the verifier with a matching independent calculation, scenario bounds, and failure tests **in the same review batch**. Unknown IDs fail rather than silently passing.
- Keep the 2026-10-30 model JSON's original `CI_numeric_assertions_automated: false` historical flag untouched. This newer dated CI policy records subsequent automation without backdating or rewriting research evidence.
- If a numerical result is wrong, correct through a traceable amended model and source-linked review; do not silently rewrite the historical source claims or relax thresholds. CI success proves only that the declared checks passed.
- For a saved V4 deep-research completion, require new model test PASS, preflight if locally available, GitHub Actions final SUCCESS on the exact commit, and GitHub file readback. `in_progress`, `failure`, or `cancelled` do not qualify.

## Non-duplication

This change introduces **zero new videos, zero new historical claim IDs and zero newly approved investor actions**. The prior 5-video, 62-claim, 9-model data remains immutable. Report model-gate improvements separately from research-completeness scoring.
