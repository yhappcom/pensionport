# Cross-layer research rereview — studies 001-005

**Date:** 2026-10-30  
**Basis:** existing 62 V3 educational claims, 9 V4 numeric models, 5 follow-up scenarios, current primary regulatory references. This is an **incremental audit**, not a new claim census or independent re-verification of every claim from audiovisual sources.

## Confirmed cross-layer issue: study 001 annual interest convention

The historical V3 claim `sz5N9WJS310-06` uses Korean **`실효 연7%`** (effective 7% annual rate) and approximately 32.14m KRW after seven years or 51.32m KRW after ten years. The later numeric model `M01_ACCUMULATION` instead explicitly computes **nominal annual 7% with monthly compounding**.

| Horizon, month-end KRW300k deposits | Effective 7% annually | Nominal 7% / 12 per month | Difference |
|---|---:|---:|---:|
| 7 years | 32,141,806 | 32,399,694 | 257,888 |
| 10 years | 51,315,519 | 51,925,442 | 609,923 |

The two model values are **not contradictory outcomes**: they are two different rate conventions. A seven-year, ~51m balance is inconsistent with **both** conventions. The source video's original audio and slides are still unavailable for exact attribution. The old source claim and existing V4 model must **both be preserved**, and future comparisons must name the convention.

## Confirmed risk qualification: study 003 bond maturity

Existing claim `OiDTNstaSpM-05` is correctly `QUALIFIED`, but the earlier V4 review did not provide a sufficiently explicit bond-versus-bond-fund distinction. For a particular individual bond, contractual face-value repayment presupposes **no issuer default** and may differ from the original acquisition price. Mark-to-market and liquidity risks remain before maturity; call and inflation risks can also matter. A diversified bond ETF or standard rolling bond fund **does not normally guarantee original capital on a fixed maturity date**.

Primary investor education: [SEC individual bond risks](https://www.investor.gov/introduction-investing/investing-basics/investment-products/bonds-or-fixed-income-products/bonds) and [SEC bond fund risk](https://www.investor.gov/introduction-investing/investing-basics/glossary/bond-funds-and-income-funds).

## Other material checks

- **003 IRP:** National Tax Service 2026 actual receipt-year fractions for eligible deferred retirement income reconfirmed ([NTS](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6605)). Nominal KRW10k pension application does not prove tax qualification or statutory receipt-year start.
- **004 losing stock:** The historic transcript's current-account/GDP ~20% statistic remains source-unreproduced. It is not used to forecast a particular equity recovery, and an assumed universal three-year recovery cycle remains disallowed.
- **002 and 005:** Existing CMA/income-tax/account-product and employee-budget/TDF suitability restrictions are retained. A mathematical example must not be promoted into a personal allocation decision.

## Outcome and reuse rules

The source-limited V4 educational research stays **conditionally closed with external OPEN items**; nothing new authorizes L3 personalized ranking or L4 implementation. Existing V3 approvals, 62 claim IDs, earlier 14 model outputs and the historic first-study 75/100 estimate were not revised or inflated. All five do **not** gain a new independent 100-point maturity score.

Machine-readable supporting audit and executable source-to-model check are linked from [the companion JSON](../data/synthesis/investment_knowledge_v4/reviews/v4_001_005_cross_layer_rereview_20261030.json). The new CI guard checks both annual-rate interpretations against the unchanged V3 claim and stored V4 model, and preserves the explicit bond risk caveat. Neither test proves the primary transcript’s audio or legally suitable future returns.
