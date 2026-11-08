# P0 #24 W00037–W00044 — quality-first original-source audit (2026-11-07)

**P0 NO-GO; no financial truth approval.** Directly reopened private `1-70.zip`, SHA-256 `00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd`; #24 `AeCOMNl11v4` SRT SHA-256 `af4d89d0e69b219947fdf82cdd9f3229c1f7b1e14c05c924ac815d2511f6c531`. Inspected **8 consecutive 18-cue windows W00037–W00044, 144 original cues 648–791**, from 00:21:58.559 through 00:26:47.000. Source cue timestamps and per-cue SHA-256 computed in private working derivative; no private subtitle text committed. **Next W00045 / cue 792.**

## 26 provisional propositions — source cue, type, critical countercheck

|Window|Cue|Provisional proposition (paraphrase)|Classification / unresolved falsification|
|---|---:|---|---|
|W37|659|Business, investing or marriage may yield a financial leap|Guest opinion; not necessary/sufficient law|
|W37|663|Host endorses investing as a wealth fast lane|Host endorsement ≠ independently proven advice|
|W38|673|Guest pursued YouTube to learn business|Personal case; employment rules unknown|
|W38|679|Guest's current channel is third after two failed channels|Self-reported history|
|W39|687|Guest first encountered crypto in early 2018|Self-reported investment timing|
|W39|692|Crypto experienced a sharp decline in early 2018|Asset, exchange and period unspecified|
|W39|695|Bitcoin fell from roughly KRW 20m|Exchange and price timestamp unspecified|
|W39|697|Guest bought Ethereum around KRW 1.25m|Personal trading records unavailable|
|W40|703|Prior crypto price crashes had repeatedly occurred|Cycle frequency and sample unknown|
|W40|707|Guest believed lower prices would lead to substantial future returns|Retrospective belief, not predictive guarantee|
|W40|714|Guest's acquaintances invested without understanding crypto|Small anecdotal sample, not population fact|
|W41|719|Crypto recognition would become more widespread|Forecast, distinct from actual usage and returns|
|W41|724|Ethereum subsequently fell approximately 90%|Peak, trough and dates unverified|
|W41|728|Crypto prices recovered around COVID|Ambiguous assets, times and definition of recovery|
|W42|729|Bitcoin traded around KRW 3m–4m in 2019|Exchange/date needed|
|W42|731|Guest's Bitcoin cost basis was around KRW 8m|Unverified personal account|
|W42|734|Guest's Ethereum cost basis was around KRW 200k|Unverified personal account|
|W42|736|Guest managed about KRW 150m before COVID|Personal capital and liability breakdown unknown|
|W43|747|A financial crisis arrives approximately every ten years|Not an established deterministic cycle|
|W43|755|Guest staged purchases and preserved cash during COVID crash|Personal strategy, not universal suitability|
|W43|761|KOSPI could fall from 2000 to 1000|Hypothetical stress scenario, NOT observed market outcome|
|W44|772|Guest borrowed about KRW 100m credit line and KRW 33m personal loan|Leverage, rates, repayment and liquidation risk|
|W44|774|Guest invested approximately KRW 300m total|Unverified aggregation of own and borrowed capital|
|W44|780|Guest concentrated exposure in Bitcoin/Ethereum|Concentration and leveraged downside risk|
|W44|782|Guest recalls subsequent multi-fold gains|No trade ledger, realized returns or fees/taxes|
|W44|785|Host attributes success to preparedness|Post-hoc narrative and survivorship bias|

**Review status:** 26 distinct provisional candidates, each critically counterchecked in the **same session**, **NOT independent blind second pass**. No gold set; TP/FP/FN and precision/recall **NOT MEASURABLE**. Official evidence reviewed **0** this batch; master-116 item-level relationships reviewed **0**; ResearchRun and SecondPassRegistry receipts **0**. All require OPEN disposition. Historical price figures are not validated merely because a speaker reported them. Claims may still be missing; 26 is not a certified complete extraction.

## Quality gate observations and priority

At the inspection point PR #36 (W25–W36) and PR #37 (new one-turn incremental integrity gate) were open, while their GitHub CI checks had passed. PR #37's manifest registered **only W1–W24** and its one-turn verifier checked **redacted derivative hashes and structural provenance**, not private original bytes, semantic recall, independent review or evidence truth. The existing one-turn receipt also reports `one_request_research_complete: true` and `research_state: ALL_53_NEW_VIDEO_CLAIMS_DISPOSITIONED`; these legacy fields must not be interpreted as P0 corpus completeness or independent certification. This is a **semantic status ambiguity** requiring explicit separate P0 status in consumer-facing interpretation.

Before further knowledge promotion: merge/rebase PR #36/#37 safely, register W25–W36 and this batch with exact source hash and cue ownership, integrate private replay where available, add failure-injection for forged research receipts, obtain blind second extraction, verify official financial sources and master-116 relations. This file is an append-only provisional research note, not a verified formal event or GO evidence. Existing main, 116 master items and P4 29 nodes remain untouched.
