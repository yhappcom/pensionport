#!/usr/bin/env python3
"""V3.2 conservative compatibility bridge for heterogeneous historical verdicts.

This does NOT reinterpret primary evidence. It maps legacy *risk statuses*
for read-only candidate review only; original verdict is retained verbatim.
Without a Git-pinned V3 source record, any caller could forge a status.
"""
from v30_verified_core import guard,VERDICTS,CLAIM_RE
ALIASES={
  "CONFIRMED":"PRIMARY_CONFIRMED",
  "CORRECTED_AFTER_PRIMARY_CONTRADICTION":"CONTRADICTED",
}
def normalize_existing_v3_claim(atom,video_number,expected_video_id):
    guard(type(atom) is dict and
          type(video_number) is int and 1<=video_number<=260 and
          isinstance(expected_video_id,str) and
          len(expected_video_id)==11 and
          isinstance(atom.get("claim_id"),str)
          and CLAIM_RE.fullmatch(atom["claim_id"]) and
          atom["claim_id"].startswith(expected_video_id+"-") and
          isinstance(atom.get("claim"),str) and atom["claim"].strip(),
          "V3_HISTORICAL_ATOMIC_PROVENANCE_REQUIRED")
    original=atom.get("verification")
    verdict=ALIASES.get(original,original)
    guard(verdict in VERDICTS,
          "UNKNOWN_HISTORICAL_VERDICT_MUST_BE_BLOCKED")
    converted=original!=verdict
    return {
        "claim_id":atom["claim_id"],
        "video_number":video_number,
        "video_id":expected_video_id,
        "text":atom["claim"],
        "legacy_verdict":verdict,
        "original_v3_verdict":original,
        "historical_verdict_canonicalized_for_retrieval":converted,
        "verdict_canonicalization_reason":(
           "PRIOR_V3_CONFIRMATION_ALIAS_RETRIEVAL_RISK_ONLY"
             if original=="CONFIRMED" else
           "PRIOR_V3_CORRECTED_CLAIM_ALWAYS_CORRECTION_ONLY"
             if original=="CORRECTED_AFTER_PRIMARY_CONTRADICTION" else
           "UNMODIFIED_HISTORICAL_VERDICT"),
        "financial_evidence_independently_verified_here":False,
        "positive_knowledge_approval":False,
        "automatic_investment_advice":False
    }
