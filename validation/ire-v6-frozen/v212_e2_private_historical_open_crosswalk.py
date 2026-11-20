"""V212 E2 — exact V182 owner-OPEN/source risk crosswalk, private-only.

Historical V182 owner had 17 effective OPEN cue indices. These are NOT
V179's original 24 OPEN or 68 suspicious NO_ATOM, nor do they certify that
an original V176 owner journal was restored. Compare verified V182 cue IDs to
current V210/V211/V211.1 private source records, explicitly retaining all
audio/video/scope unresolved evidence. No financial truth is approved.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256 as raw_digest
import json

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import parse_srt
from v2111_e2_private_crosscue_link_custody import audit_private_cross_cue_relations

SCHEMA="IRE_V212_PRIVATE_ETF_E2_V182_17OPEN_SOURCE_CROSSWALK_V1"
VIDEO_ID="LVE7XN_esTc"
ORIGINAL_SHA="e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b"
HISTORICAL_REFERENCE="V182_OWNER_EFFECTIVE_OPEN_17_DIFFERENT_FROM_V179_24_OPEN_AND_68_NOATOM"
V182_SOURCE_OPEN_TYPES={
    8:"HISTORICAL_STAT_TIME",
    19:"ASR_AUDIO",23:"ASR_AUDIO",52:"ASR_AUDIO",
    123:"FACT_SCOPE_OVERGENERALIZATION",
    126:"FACT_SCOPE_OVERGENERALIZATION",
    133:"ASR_AUDIO",149:"ASR_AUDIO",150:"ASR_AUDIO",
    153:"ASR_AUDIO",160:"ASR_AUDIO",
    163:"VIDEO_SCREEN",166:"VIDEO_SCREEN",
    171:"ASR_AUDIO",
    230:"VIDEO_SCREEN",232:"VIDEO_SCREEN",233:"VIDEO_SCREEN",
}
EVIDENCE_REQUIRED={
    "HISTORICAL_STAT_TIME":"HISTORICAL_AS_OF_AND_SOURCE",
    "ASR_AUDIO":"ORIGINAL_AUDIO",
    "VIDEO_SCREEN":"ORIGINAL_VIDEO_FRAME",
    "FACT_SCOPE_OVERGENERALIZATION":"CLAIM_SCOPE_SEMANTIC_REVIEW_AND_PRIMARY_SOURCE",
}
PRIVATE_BASENAMES=(
    "V210_PRIVATE_ETF_250_REAL_SOURCE_FIRST_DRAFT_20261120.json",
    "V211_PRIVATE_ETF_250_CUE_SOURCE_RISK_ADJUDICATION_DOCKET_20261120.json",
    "V211_1_PRIVATE_ETF_CROSS_CUE_CONDITION_EXCEPTION_REBUTTAL_LINKS_20261120.json",
)
ROWS_FIELDS={
    "cue_index","historical_v182_open_type",
    "historical_v182_effective_open","source_quote",
    "source_text_sha256","original_neighborhood",
    "linked_v210_unapproved_candidate_ids",
    "v211_prior_risk_issue_id","v211_newly_identified_gap",
    "v2111_related_original_source_edge_ids",
    "chat_source_interpretation_not_speaker","must_resolve_via",
    "can_be_marked_resolved_from_current_srt_only",
    "external_gold_certified","financial_fact_approved",
    "original_owner_v176_event_changed",
}
NO_RELEASE={
    "chat_review_is_not_external_gold":True,
    "all_historical_v182_open_still_needs_resolution":True,
    "independent_gold_certified":False,
    "e2_pass":False,"e3_e4_e5_authorized":False,
    "financial_facts_approved":False,"knowledge_published":False,
}


def ensure(ok,reason):
    if not ok:
        raise InvalidInput("V212_E2_"+reason)


def _read_json(b,what):
    ensure(type(b) is bytes,"PRIVATE_"+what+"_BYTES_REQUIRED")
    try:
        value=json.loads(b)
    except (TypeError,ValueError,UnicodeError) as err:
        raise InvalidInput("V212_E2_PRIVATE_"+what+"_JSON_INVALID") from err
    ensure(type(value) is dict,"PRIVATE_"+what+"_JSON_OBJECT_REQUIRED")
    return value


def audit_private_open_crosswalk(raw_srt,inventory_bytes,
                                 risk_docket_bytes,relation_bytes,packet,*,
                                 expected_source_sha256,expected_open_map,
                                 expected_video_id):
    # The precise private source lineage must be checked before any review
    # text is interpreted. All three earlier source-specific validators are
    # replayed for each check; a forged prior hash alone is not sufficient.
    ensure(type(expected_open_map) is dict and bool(expected_open_map) and
           type(expected_video_id) is str and
           type(raw_srt) is bytes and sha256(raw_srt)==expected_source_sha256,
           "SOURCE_OR_HISTORICAL_MAP_INVALID")
    prior_inventory=_read_json(inventory_bytes,"V210")
    prior_risks=_read_json(risk_docket_bytes,"V211")
    prior_relations=_read_json(relation_bytes,"V2111")
    receipt=audit_private_cross_cue_relations(
        raw_srt,inventory_bytes,risk_docket_bytes,prior_relations,
        expected_source_sha256=expected_source_sha256)
    cues=parse_srt(raw_srt)
    expected_keys=set(expected_open_map)
    ensure(all(type(i) is int and 1<=i<=len(cues) and
               typ in EVIDENCE_REQUIRED
               for i,typ in expected_open_map.items()),
           "HISTORICAL_OPEN_INDEX_OR_KIND_INVALID")
    ensure(type(packet) is dict and
           packet.get("schema")==SCHEMA and
           packet.get("video_id")==expected_video_id==
                prior_inventory.get("video_id")==prior_risks.get("video_id") and
           packet.get("original_source_sha256")==expected_source_sha256 and
           packet.get("total_original_cues")==len(cues) and
           packet.get("historical_reference")==HISTORICAL_REFERENCE and
           packet.get("historical_v182_owner_sqlite_recovered") is False and
           packet.get("v179_24_open_individual_cases_available") is False and
           packet.get("v179_68_noatom_individual_cases_available") is False and
           packet.get("historical_v182_open_count")==len(expected_keys) and
           type(packet.get("private_input_hashes")) is dict and
           packet["private_input_hashes"]==dict(zip(PRIVATE_BASENAMES,(
               raw_digest(inventory_bytes).hexdigest(),
               raw_digest(risk_docket_bytes).hexdigest(),
               raw_digest(relation_bytes).hexdigest(),
           ))) and
           all(packet.get(k) is v for k,v in NO_RELEASE.items()),
           "PRIVATE_INPUT_SHA_OR_HISTORICAL_CUSTODY_MISMATCH")
    open_types=Counter(expected_open_map.values())
    expected_issues={x["source_cue_index"]:x for x in prior_risks["issues"]}
    expected_relations={
        i:[edge["relation_id"] for edge in prior_relations["relations"]
           if i in (edge["from_cue"],edge["to_cue"])]
        for i in expected_keys
    }
    expected_claims={
        i:[c["provisional_id"] for c in prior_inventory["claims"]
           if c["start_cue"]<=i<=c["end_cue"]]
        for i in expected_keys
    }
    rows=packet.get("rows")
    ensure(type(rows) is list and len(rows)==len(expected_keys),
           "OPEN_CUE_17_CENSUS_MISMATCH")
    seen=set()
    gaps=[]
    covered=0
    for i,row in zip(sorted(expected_keys),rows):
        ensure(type(row) is dict and set(row)==ROWS_FIELDS,
               "OPEN_CUE_REVIEW_FIELDS")
        text=cues[i-1].text
        issue=expected_issues.get(i)
        has_issue=issue is not None
        need_neighborhood=list(range(max(1,i-2),min(len(cues),i+2)+1))
        expected_neighborhood=[{
            "cue_index":n,"source_quote":cues[n-1].text,
            "source_text_sha256":sha256(cues[n-1].text.encode("utf-8"))
        } for n in need_neighborhood]
        ensure(type(row["cue_index"]) is int and row["cue_index"]==i and
               i not in seen and
               row["historical_v182_open_type"]==expected_open_map[i] and
               row["historical_v182_effective_open"] is True and
               row["source_quote"]==text and
               row["source_text_sha256"]==sha256(text.encode("utf-8")) and
               row["original_neighborhood"]==expected_neighborhood and
               row["linked_v210_unapproved_candidate_ids"]==
                   expected_claims[i] and
               row["v211_prior_risk_issue_id"]==
                   (issue["issue_id"] if has_issue else None) and
               row["v211_newly_identified_gap"] is (not has_issue) and
               row["v2111_related_original_source_edge_ids"]==
                   expected_relations[i] and
               type(row["chat_source_interpretation_not_speaker"]) is str and
               len(row["chat_source_interpretation_not_speaker"].strip())>=30 and
               row["must_resolve_via"]==
                   EVIDENCE_REQUIRED[expected_open_map[i]] and
               row["can_be_marked_resolved_from_current_srt_only"] is False and
               row["external_gold_certified"] is False and
               row["financial_fact_approved"] is False and
               row["original_owner_v176_event_changed"] is False,
               "SOURCE_OPEN_REVIEW_OR_REFERENCED_EVIDENCE_DRIFT")
        seen.add(i)
        if not has_issue:
            gaps.append(i)
        else:
            covered+=1
    ensure(seen==expected_keys and
           packet.get("v211_existing_risk_covered_count")==covered and
           packet.get("v211_missing_cue_risk_count")==len(gaps) and
           packet.get("v211_missing_original_cue_ids")==gaps and
           packet.get("historical_open_types")==dict(open_types),
           "HISTORICAL_OPEN_CASES_OR_RISK_GAP_COUNTS_WRONG")
    return {
        "schema":"IRE_V212_E2_PRIVATE_REDACTED_HISTORICAL_OPEN_CROSSWALK_V1",
        "source_sha256":sha256(raw_srt),
        "v210_inventory_sha256":raw_digest(inventory_bytes).hexdigest(),
        "v211_risk_sha256":raw_digest(risk_docket_bytes).hexdigest(),
        "v2111_relations_sha256":raw_digest(relation_bytes).hexdigest(),
        "original_source_cues_verified":len(cues),
        "historical_v182_explicit_open_cases_source_checked":len(seen),
        "v211_previous_risk_items_covering_open":covered,
        "new_e2_gap_cue_indices":gaps,
        "new_e2_gap_count":len(gaps),
        "source_evidence_types":dict(open_types),
        "previous_v179_open_24_resolved":False,
        "previous_v179_noatom_68_resolved":False,
        "audio_video_unavailable_still_open":True,
        "external_gold_certified":False,
        "e2_final_pass":False,
        "e3_e4_e5_authorized":False,
        "financial_facts_approved":False,
        "knowledge_published":False,
    }


def audit_real_v182_etf_source_open(raw_srt,inventory_bytes,
                                    risk_docket_bytes,relation_bytes,packet):
    """Production entrypoint for the exact 250-cue user-owned ETF source."""
    return audit_private_open_crosswalk(
        raw_srt,inventory_bytes,risk_docket_bytes,relation_bytes,packet,
        expected_source_sha256=ORIGINAL_SHA,
        expected_open_map=V182_SOURCE_OPEN_TYPES,
        expected_video_id=VIDEO_ID)
