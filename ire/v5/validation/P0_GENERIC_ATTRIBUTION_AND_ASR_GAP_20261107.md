# V5 cross-video engine contract — attribution, transcription uncertainty and no-claim windows

**Evidence trigger:** #22 W00013–W00024, real SRT cues 217–432. This is a proposed fail-closed schema change, **not implemented in production**.

## Failure classes

1. **Quoted viewer question becomes presenter-endorsed financial advice.** Viewer age, investment history, personal account balances, and intended withdrawal schedule must be `PERSONAL_CASE` with `speaker_role=QUOTED_VIEWER`, not promoted to a generally applicable RULE.
2. **Automatic transcript errors create nonexistent financial rules.** Cue 260–266 has ambiguous `추납/주합`; cue 384–388 has `세공제/새공지`. Preserve original cue SHA256; attach normalized interpretation only with `transcript_confidence=UNCERTAIN` and an explicit unresolved hearing note. Do not rewrite the private source.
3. **Empty financial windows silently skipped.** Seven of twelve windows in this batch have no independently extractable finance propositions. Require `disposition=NO_FINANCIAL_ATOMIC_CLAIMS`, full cue ownership and second-pass attestation, not an empty list interpreted as incomplete work.
4. **Tax benefit confused with cash benefit.** Separate (a) ISA maturity transfer eligibility and transfer deadline, (b) additional tax-credit contribution limit, (c) actual tax-credit amount given individual liability, (d) pension-account withdrawal ordering/tax, and (e) individual suitability. The presence of one cannot establish another.
5. **Historical market number without index/period.** A percentage decline needs `index_id`, `start_date`, `end_date`, `return_basis`, `currency`, `price_vs_total_return`. If missing, `OPEN_HISTORICAL_INDEX_DATE`.

## Proposed generic evidence fields

```json
{
  "window_disposition": "CLAIMS_EXTRACTED | NO_FINANCIAL_ATOMIC_CLAIMS",
  "source_cue_ids": [1],
  "source_cue_sha256": ["..."],
  "speaker_role": "PRESENTER | COHOST | QUOTED_VIEWER | UNKNOWN",
  "attribution_confidence": "CONFIRMED | INFERRED | UNCERTAIN",
  "transcript_confidence": "CLEAR | UNCERTAIN",
  "atomicity_second_pass": {
    "checked": true,
    "independent_blind": false,
    "added_claim_ids": [],
    "unresolved_boundary_ids": []
  },
  "financial_scope": {
    "effective_date": null,
    "account_type": null,
    "personal_eligibility_open": true,
    "withdrawal_tax_open": true
  }
}
```

## Required regression cases before implementation

- Quoted viewer's 60-year-old retirement plan cannot be reclassified as universal pension advice.
- Uncertain ASR `주합` cannot be treated as confirmed `추납` with numerical 119-month ceiling.
- A no-claim window passes cue ownership checks but cannot certify claim-recall without a second pass.
- A 300만원 additional tax-credit contribution limit cannot be labeled a 300만원 guaranteed tax refund.
- An ISA-to-pension transfer cannot be marked risk-free without withdrawal taxation and individual tax-credit use checks.
- A 2021 `30%` fall cannot be verified without the index and exact return interval.

**Implementation status:** design-only OPEN. Formal `ResearchRun` / `SecondPassRegistry` receipts and gold-recall measurement remain necessary. No P0 or P1 approval.
