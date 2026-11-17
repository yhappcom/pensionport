"""V159 private-original B0001-B0003 ChatGPT V123 source-first status guard.

Public GitHub CI is SHA-only. The actual 1,481 cue original, 286 atom
exchanges, 13 native V6 host ledgers and 13 V123 reviews are in the
owner-private packet. Successful public tests DO NOT confer semantic truth,
finance-issuer original bytes, V123 scope PASS, V128 publication or P0 GO.

The owner-private verify_v159_private_replay.py must also run to demonstrate
the integrity of actual original bytes, events and V123 decisions.
"""
from __future__ import annotations
import re

SHA64=re.compile(r"[0-9a-f]{64}\Z")
SOURCE="638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d"
SCHEMA="V159_P0E_REAL_SOURCE_286_V123_PARTIAL_RESEARCH_ACCEPT_SHA_ONLY_HOLD_V1"
STATUS="V159_PRIVATE_SOURCE_3_SCOPES_18_RESEARCH_ONLY_ATOMS__V123_13_HOLD_V128_ZERO"


class V159EvidenceNotReady(ValueError):
    pass


def _require(ok, label):
    if not ok:
        raise V159EvidenceNotReady("V159_"+label)


def audit_v159_public_source_first(meta):
    """Verify literal SHA-only pinned V159 no-GO status and source census."""
    _require(type(meta) is dict and meta.get("schema")==SCHEMA, "SCHEMA")
    _require(meta.get("video_id")=="5NvtBlmt93Y" and
             meta.get("original_source_sha256")==SOURCE, "OWNER_SOURCE")
    counts={
        "original_srt_cues":1481,
        "full_source_first_chat_scopes":3,
        "full_source_first_chat_cues":360,
        "source_cues_currently_reviewed_not_quarantined":356,
        "source_cues_not_yet_source_first_checked":1121,
        "full_source_first_adjudicated_claims":81,
        "original_v158_candidate_atoms":284,
        "new_source_first_recovered_atoms":2,
        "new_candidate_atoms":286,
        "V123_partial_research_only_row_acceptances":18,
        "V123_atom_rows_open":268,
        "V123_13_scope_final_approved":0,
        "V123_13_scope_held":13,
        "original_audio_or_primary_source_unverified_cues":13,
        "V123_explicit_quarantined_cues":24,
        "V6_native_owner_host_receipts_committed":13,
        "V6_native_owner_host_idempotent":13,
        "V128_live_child_checkpoints_held":13,
        "V128_live_knowledge_events":0,
        "V128_live_knowledge_entries":0,
        "V128_parent_publications":0,
    }
    for key,v in counts.items():
        _require(type(meta.get(key)) is int and meta[key]==v,
                 "FALSE_CENSUS_OR_APPROVAL_"+key.upper())
    _require(meta["new_source_first_recovered_atoms"]+
             meta["original_v158_candidate_atoms"]==
             meta["new_candidate_atoms"],"ATOMIC_RECOVERY_MUST_NOT_GET_LOST")
    _require(meta["V123_partial_research_only_row_acceptances"]+
             meta["V123_atom_rows_open"]==meta["new_candidate_atoms"],
             "OPEN_AND_PARTIAL_ACCEPT_ACCOUNTING")
    _require(meta["full_source_first_chat_cues"]+
             meta["source_cues_not_yet_source_first_checked"]==
             meta["original_srt_cues"],"SOURCE_FIRST_IS_NOT_FULL_CENSUS")
    _require(meta["full_source_first_chat_scopes"]<13 and
             meta["V123_13_scope_final_approved"]==0 and
             meta["V128_parent_publications"]==0, "FALSE_SCOPE_RELEASE")
    _require(meta["original_audio_or_primary_source_unverified_cues"]<=
             meta["V123_explicit_quarantined_cues"], "AUDIO_UNQUARANTINED")
    for k in ("same_chat_review_not_independent_gold",):
        _require(meta.get(k) is True, "NOT_INDEPENDENT_GOLD")
    for k in ("precision_95_certified","recall_98_certified",
              "high_risk_false_negatives_zero_certified",
              "current_primary_law_and_personal_suitability_certified",
              "personal_advice_approved","p0e_go"):
        _require(meta.get(k) is False, "FALSE_P0E_APPROVAL_"+k.upper())
    for k in ("owner_private_packet_sha256",
              "owner_private_v123_summary_sha256",
              "owner_private_v128_summary_sha256",
              "owner_private_readonly_replay_sha256",
              "owner_private_b0001_corrected_exchange_sha256",
              "owner_private_b0002_corrected_exchange_sha256",
              "owner_private_b0003_corrected_exchange_sha256"):
        value=meta.get(k)
        _require(type(value) is str and SHA64.fullmatch(value) is not None,
                 "PRIVATE_SHA_REQUIRED_"+k.upper())
    heads=meta.get("host_event_sha256_by_scope")
    _require(type(heads) is dict and
             set(heads)=={f"B{i:04d}" for i in range(1,14)} and
             len(set(heads.values()))==13 and
             all(type(h) is str and SHA64.fullmatch(h) is not None
                 for h in heads.values()),"REAL_HOST_EVENT_HEADS_13_REQUIRED")
    _require(meta.get("status")==STATUS,"HOLD_STATUS")
    return {
        "original_srt_cues":1481,
        "native_v6_13_scope_head_hashes_pinned":13,
        "provisional_atom_count":286,
        "ChatGPT_source_first_full_scopes":3,
        "ChatGPT_source_first_atoms_individually_adjudicated":81,
        "candidate_row_accepted_educational_not_finally_released":18,
        "candidate_rows_still_open":268,
        "V123_final_scope_PASSES":0,
        "V128_approved_parent_knowledge_publications":0,
        "true_precision_recall_certified":False,
        "P0E_GO":False,
        "status":"V159_PRIVATE_SOURCE_FIRST_PARTIAL_RESEARCH_CANDIDATE_ONLY_V123_V128_HOLD"
    }


def research_release_or_personal_advice_allowed(meta):
    status=audit_v159_public_source_first(meta)
    return {
        "v6_native_host_structurally_ready":status["native_v6_13_scope_head_hashes_pinned"]==13,
        "full_video_V123_research_release_approved":False,
        "V128_atomic_knowledge_publish_allowed":False,
        "personalized_advice_approved":False,
        "reason":"ONLY_3_OF_13_SOURCE_FIRST_SCOPES_REVIEWED_AND_FINANCE_GOLD_OPEN",
    }
