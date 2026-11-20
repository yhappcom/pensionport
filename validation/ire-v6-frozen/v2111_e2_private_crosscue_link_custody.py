"""V211.1 private E2 cross-cue meaning context custody.

A source-quoted relation is a reviewer hypothesis, not proof of a correct
financial relation. Verify exact raw-source and prior private V210/V211 byte
chains, before returning a text-free mechanical receipt. The next E2 human
or ChatGPT dispute review MUST resolve these links; never auto-release.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256 as hash_bytes
import json

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import parse_srt
from v211_e2_private_real_source_risk_docket import (
    audit_private_v211_source_risk_docket,
)

SCHEMA="IRE_V211_1_PRIVATE_ETF_CROSS_CUE_CONTEXT_RELATIONS_V1"
KINDS={
    "REBUTTAL_SCOPE","CONDITION","EXCEPTION","COUNTERCONTEXT",
    "DEFINITION_SCOPE","NORMATIVE_SCOPE","HYPOTHETICAL_EXAMPLE",
    "DERIVED_MATH_NOT_SPOKEN","VISUAL_EVIDENCE_OPEN",
    "COMPARABLE_PRODUCT_CONDITION","UNITS_OPEN","FICTIONAL_SCOPE",
    "NUMERIC_PAIR","DISCOUNT_SIGN_CONTEXT","COMPARISON_AT_SAME_TIME",
}
DENIAL={
    "each_relation_has_both_original_quotes":True,
    "chat_review_of_relation_not_external_gold":True,
    "e2_final_pass":False,
    "e3_e4_e5_authorized":False,
    "financial_truth_certified":False,
    "native_v6_claims_issued":False,
}
FIELDS={
    "relation_id","from_cue","to_cue","from_quote","to_quote",
    "from_source_text_sha256","to_source_text_sha256",
    "relation_type","chat_reviewer_interpretation_not_source_speaker",
    "semantic_relation_independently_confirmed","financial_fact_approved",
}


def stop(ok,why):
    if not ok:
        raise InvalidInput("V2111_E2_"+why)


def audit_private_cross_cue_relations(raw_srt,inventory_bytes,
                                      private_risk_docket_bytes,
                                      relation_packet,*,
                                      expected_source_sha256):
    stop(type(private_risk_docket_bytes) is bytes,
         "RISK_DOCKET_BYTES_REQUIRED")
    try:
        private_risks=json.loads(private_risk_docket_bytes)
    except (ValueError,UnicodeError,TypeError) as err:
        raise InvalidInput("V2111_E2_RISK_DOCKET_JSON_INVALID") from err
    checked=audit_private_v211_source_risk_docket(
        raw_srt,inventory_bytes,private_risks,
        expected_source_sha256=expected_source_sha256)
    cues=parse_srt(raw_srt)
    stop(type(relation_packet) is dict and
         relation_packet.get("schema")==SCHEMA and
         relation_packet.get("video_id")==private_risks["video_id"] and
         relation_packet.get("original_source_sha256")==expected_source_sha256 and
         relation_packet.get("v210_inventory_sha256")==
            hash_bytes(inventory_bytes).hexdigest() and
         relation_packet.get("v211_docket_sha256")==
            hash_bytes(private_risk_docket_bytes).hexdigest() and
         relation_packet.get("total_cues")==len(cues) and
         all(relation_packet.get(key) is value
             for key,value in DENIAL.items()),
         "SOURCE_RISK_HEAD_OR_FALSE_APPROVAL")
    rows=relation_packet.get("relations")
    stop(type(rows) is list and
         1<=len(rows)<=len(cues)*8 and
         relation_packet.get("relation_count")==len(rows),
         "RELATION_COUNT_OR_FORMAT")
    observed=set()
    types=Counter()
    for n,edge in enumerate(rows,1):
        stop(type(edge) is dict and set(edge)==FIELDS,
             "RELATION_FIELDS_DRIFT")
        i=edge["from_cue"]
        j=edge["to_cue"]
        key=(i,j,edge["relation_type"]) if (
            type(i) is int and type(j) is int and
            type(edge["relation_type"]) is str) else None
        stop(type(i) is int and type(j) is int and
             1<=i<=len(cues) and 1<=j<=len(cues) and
             i!=j and
             type(edge["relation_type"]) is str and
             edge["relation_type"] in KINDS and
             edge["relation_id"]==f"V211R-{n:03d}" and
             key not in observed and
             edge["from_quote"]==cues[i-1].text and
             edge["to_quote"]==cues[j-1].text and
             edge["from_source_text_sha256"]==
                 sha256(cues[i-1].text.encode("utf-8")) and
             edge["to_source_text_sha256"]==
                 sha256(cues[j-1].text.encode("utf-8")) and
             type(edge["chat_reviewer_interpretation_not_source_speaker"]) is str and
             len(edge["chat_reviewer_interpretation_not_source_speaker"].strip())>=18 and
             edge["semantic_relation_independently_confirmed"] is False and
             edge["financial_fact_approved"] is False,
             "RELATION_NOT_ORIGINAL_OR_FINANCIALLY_PREAPPROVED")
        observed.add(key)
        types[edge["relation_type"]]+=1
    return {
        "schema":"IRE_V211_1_E2_REDACTED_CROSS_CUE_RECEIPT_V1",
        "source_sha256":checked["original_source_sha256"],
        "v210_inventory_sha256":hash_bytes(inventory_bytes).hexdigest(),
        "v211_risk_docket_sha256":
            hash_bytes(private_risk_docket_bytes).hexdigest(),
        "original_cues_source_verified":len(cues),
        "private_source_risk_items_source_verified":
            checked["v211_explicit_total_source_review_cases"],
        "source_quoted_cross_cue_relations":len(observed),
        "relation_type_counts":dict(types),
        "missing_v179_individual_owner_cases":True,
        "independent_semantic_gold_verified":False,
        "cross_cue_meanings_finally_approved":False,
        "e2_final_pass":False,
        "e3_e4_e5_authorized":False,
        "financial_truth_certified":False,
        "knowledge_published":False,
    }
