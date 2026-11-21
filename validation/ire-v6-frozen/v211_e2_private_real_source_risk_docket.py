"""V211 E2 private 250-cue risk docket, source-bound but NOT semantic gold.

The source and individual reviewer findings are only supplied privately.
Public CI uses synthetic fixtures. Return receipts contain hashes/counts
only: no raw transcript, claim propositions or personal data.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256 as digest

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import parse_srt
from v210_e2_private_original_source_inventory import (
    audit_private_e2_source_first_inventory,
)

SCHEMA="IRE_V211_REAL_ETF_E2_SOURCE_250CUE_INDIVIDUAL_REVIEW_DOCKET_V1"
SEVERITY={"HIGH","MEDIUM","LOW"}
DENIALS={
    "direct_chat_review_not_independent_gold":True,
    "source_warning_does_not_equal_proven_factual_error":True,
    "v179_24_and_68_individually_resolved":False,
    "independent_gold_certified":False,
    "e2_pass":False,"e3_e4_e5_authorized":False,
    "finance_approved":False,"knowledge_published":False,
}


def require(ok,code):
    if not ok:
        raise InvalidInput("V211_E2_"+code)


def audit_private_v211_source_risk_docket(raw_srt,inventory_bytes,docket,*,
                                          expected_source_sha256):
    require(type(inventory_bytes) is bytes,
            "PRIVATE_V210_BYTES_REQUIRED")
    import json
    try:
        inventory=json.loads(inventory_bytes)
    except (ValueError,UnicodeDecodeError,TypeError) as e:
        raise InvalidInput("V211_E2_PRIVATE_V210_JSON_INVALID") from e
    # The 57 unapproved candidates must each already have passed EXACT
    # source quote, cue, condition/exception and type-count checks.
    prior=audit_private_e2_source_first_inventory(
        raw_srt,inventory,
        expected_source_sha256=expected_source_sha256)
    cues=parse_srt(raw_srt)
    require(type(docket) is dict and docket.get("schema")==SCHEMA and
            docket.get("source_sha256")==expected_source_sha256 and
            docket.get("video_id")==inventory.get("video_id") and
            docket.get("v210_private_inventory_sha256")==
                 digest(inventory_bytes).hexdigest() and
            docket.get("original_cues")==len(cues) and
            docket.get("all_250_cues_source_hash_accounted") is True and
            docket.get("prior_v179_exact_open_cue_ids_unavailable") is True and
            docket.get("prior_v179_exact_noatom_cue_ids_unavailable") is True and
            type(docket.get("prior_v179_unresolved_total_reported")) is int and
            type(docket.get("prior_v179_suspicious_noatom_total_reported")) is int and
            all(docket.get(k) is v for k,v in DENIALS.items()),
            "SOURCE_PRIOR_V210_OR_APPROVAL_GUARD")
    issues=docket.get("issues")
    census=docket.get("cue_census")
    require(type(issues) is list and
            len(issues)>=1 and len(issues)<=len(cues) and
            type(census) is list and len(census)==len(cues) and
            docket.get("current_explicit_source_risk_cues")==len(issues),
            "ORIGINAL_CUE_OR_RISK_COUNT")
    claim_spans={i:[
        c["provisional_id"] for c in inventory["claims"]
        if c["start_cue"]<=i<=c["end_cue"]]
        for i in range(1,len(cues)+1)}
    bycue={}
    severity=Counter()
    for n,issue in enumerate(issues,1):
        require(type(issue) is dict and set(issue)=={
            "issue_id","source_cue_index","source_quote",
            "source_text_sha256","risk_code","risk_priority",
            "speaker_source_interpretation_unverified",
            "chat_reviewer_warning_not_original_speaker",
            "risk_reason","connected_v210_draft_ids",
            "source_audio_or_visual_confirmed",
            "financial_truth_certified","e2_cleared",
        },"PRIVATE_RISK_FIELDS")
        i=issue["source_cue_index"]
        require(type(i) is int and 1<=i<=len(cues) and i not in bycue and
                issue["issue_id"]==f"V211-SOURCE-{n:03d}" and
                issue["source_quote"]==cues[i-1].text and
                issue["source_text_sha256"]==
                    sha256(cues[i-1].text.encode("utf-8")) and
                type(issue["risk_code"]) is str and
                len(issue["risk_code"])>=5 and
                type(issue["risk_priority"]) is str and
                issue["risk_priority"] in SEVERITY and
                type(issue["speaker_source_interpretation_unverified"]) is str and
                len(issue["speaker_source_interpretation_unverified"].strip())>=4 and
                type(issue["chat_reviewer_warning_not_original_speaker"]) is str and
                len(issue["chat_reviewer_warning_not_original_speaker"].strip())>=18 and
                type(issue["risk_reason"]) is str and len(issue["risk_reason"])>=5 and
                issue["connected_v210_draft_ids"]==claim_spans[i] and
                issue["source_audio_or_visual_confirmed"] is False and
                issue["financial_truth_certified"] is False and
                issue["e2_cleared"] is False,
                "PRIVATE_RISK_SOURCE_QUOTE_OR_ROLE_DRIFT")
        bycue[i]=issue
        severity[issue["risk_priority"]]+=1
    require(docket.get("current_explicit_high_priority")==severity["HIGH"] and
            docket.get("current_explicit_medium_priority")==severity["MEDIUM"] and
            docket.get("current_explicit_low_priority")==severity["LOW"],
            "RISK_PRIORITY_COUNTS_WRONG")
    for n,record in enumerate(census,1):
        require(type(record) is dict and set(record)=={
            "cue_index","source_text_sha256",
            "provisional_v210_context_draft_ids",
            "explicit_v211_risk_issue_ids",
            "independent_atom_level_semantic_verification_passed",
            "v179_prior_exact_disposition_available",
        } and
            record["cue_index"]==n and
            record["source_text_sha256"]==
                sha256(cues[n-1].text.encode("utf-8")) and
            record["provisional_v210_context_draft_ids"]==claim_spans[n] and
            record["explicit_v211_risk_issue_ids"]==
                ([bycue[n]["issue_id"]] if n in bycue else []) and
            record["independent_atom_level_semantic_verification_passed"] is False and
            record["v179_prior_exact_disposition_available"] is False,
            "WHOLE_ORIGINAL_CUE_CENSUS_OR_RISK_DRIFT")
    return {
        "schema":"IRE_V211_E2_REDACTED_SOURCE_RISK_RECEIPT_V1",
        "original_source_sha256":sha256(raw_srt),
        "v210_private_inventory_sha256":digest(inventory_bytes).hexdigest(),
        "original_cues_sha_verified":len(cues),
        "v210_provisional_claims_source_verified":
            prior["source_anchored_provisional_claims"],
        "v211_explicit_high_source_review_cases":severity["HIGH"],
        "v211_explicit_medium_source_review_cases":severity["MEDIUM"],
        "v211_explicit_low_source_review_cases":severity["LOW"],
        "v211_explicit_total_source_review_cases":len(issues),
        "previous_v179_open_total_reported":
            docket["prior_v179_unresolved_total_reported"],
        "previous_v179_suspicious_noatom_reported":
            docket["prior_v179_suspicious_noatom_total_reported"],
        "prior_v179_individual_cue_id_mapping_available":False,
        "new_risk_issues_equal_historical_v179_reported_atoms":False,
        "all_250_source_cue_hashes_verified":True,
        "source_warning_not_proven_factual_error":True,
        "independent_semantic_gold_verified":False,
        "e2_final_pass":False,
        "e3_e4_e5_authorized":False,
        "actual_v176_owner_repair_committed":False,
        "knowledge_published":False,
    }
