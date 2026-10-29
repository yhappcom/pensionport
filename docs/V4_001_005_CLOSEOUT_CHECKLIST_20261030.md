# V4 studies 001-005 final scoped closure gate

**Date:** 2026-10-30

The five older V3-approved source studies and their 62 claims were already preserved. This final closeout **adds five synthetic decision scenarios** and an explicit evidence scope; it does not create five new research-video approvals.

New [closeout manifest](../data/synthesis/investment_knowledge_v4/reviews/v4_001_005_final_closure_20261030.json) and [model addendum](../data/synthesis/investment_knowledge_v4/models/decision_models_001_005_closure_addendum_20261030.json) define source limitations, still-required external evidence and blocked investor-specific decisions.

`scripts/verify_v4_closure_addendum.py` independently recalculates all five new scenarios and tests that corrupted/missing outcomes fail. Existing `scripts/verify_v4_quant_models.py` must continue to verify nine original models. Both run on V4 model changes (push and PR), with nonzero exit status stopping CI. No one may treat simulated return paths or example tax fractions as individualized advice or certified future portfolio outcomes.

**Final acceptance:** checked files saved, readback matches, prior original claims unchanged, closeout CI passes on exact commit. A pending, failed or cancelled CI is not completion.
