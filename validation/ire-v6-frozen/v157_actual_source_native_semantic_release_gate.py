"""V157 real owner-source native V6 event proof public SHA-only release guard.

The original SRT, 284 private candidate texts, 13 SQLite files, host runtime
and ChatGPT risk notes live ONLY in the owner's private ZIP, never public CI.
No status under this module can create a V123 PASS or V128 knowledge release.
"""
from __future__ import annotations
import re

SCHEMA="V157_REAL_PRIVATE_OWNER_V6_NATIVE_FIELD_INTEGRATION_SHA_ONLY_V1"
SOURCE="638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d"
STATUS="NATIVE_HOST_13_CONFIRMED__CHAT_MEANING_FINANCE_GOLD_AND_V128_HOLD"
HEX=re.compile("[0-9a-f]{64}\\Z")


class V157EvidenceInvalid(ValueError):
    pass


def _require(predicate, message):
    if not predicate:
        raise V157EvidenceInvalid("V157_" + message)


def audit_v157_sha_only(receipt: dict):
    _require(type(receipt) is dict and receipt.get("schema")==SCHEMA,"SCHEMA")
    _require(receipt.get("source_sha256")==SOURCE,"OWNER_SOURCE_SHA")
    expected={
        "source_cues":1481,
        "source_scopes":13,
        "candidate_atoms":284,
        "source_first_kind_edits_committed":21,
        "question_source_and_speaker_role_edits":1,
        "condition_and_stance_edits":2,
        "field_patch_log_entries":24,
        "native_v6_13_scopes_committed":13,
        "native_v6_idempotent_replay_count":13,
        "native_no_quarantine_fail_closed_cases":11,
        "source_cue_unresolved_after_review":13,
        "source_cues_quarantined_for_v123":27,
        "speaker_unknown_atoms_after_edit":282,
        "stance_unresolved_atoms_after_edit":178,
        "latest_real_v123_held_scopes":13,
        "latest_real_v123_final_pass":0,
        "latest_real_v128_knowledge_published":0,
    }
    for name,value in expected.items():
        _require(type(receipt.get(name)) is int and receipt[name]==value,
                 "FALSE_COMPLETION_"+name.upper())
    _require(receipt["source_first_kind_edits_committed"]+
             receipt["question_source_and_speaker_role_edits"]+
             receipt["condition_and_stance_edits"] ==
             receipt["field_patch_log_entries"],"FIELD_CHANGE_COUNT")
    for flag in ("finance_ground_truth_certified",
                 "precision_95_recall_98_certified",
                 "high_risk_FN_zero_certified",
                 "personal_investment_advice_approved","p0e_go"):
        _require(receipt.get(flag) is False,"FALSE_FINANCE_APPROVAL_"+flag.upper())
    _require(type(receipt.get("private_owner_packet_sha256")) is str
             and HEX.fullmatch(receipt["private_owner_packet_sha256"]) is not None,
             "PRIVATE_ORIGINAL_CUSTODY")
    events=receipt.get("host_event_sha256_by_scope")
    _require(type(events) is dict and
             set(events)=={f"B{i:04d}" for i in range(1,14)},
             "SOURCE_SCOPE_CENSUS")
    _require(len(set(events.values()))==13 and
             all(type(h) is str and HEX.fullmatch(h) is not None for h in events.values()),
             "NATIVE_EVENT_DIGEST_CENSUS")
    _require(receipt.get("status")==STATUS,"STATUS")
    return {"source_original_cues":1481,"native_host_events":13,
            "candidate_atoms":284,"chat_revised_field_changes":24,
            "quarantined_source_cues":27,"unresolved_cues":13,
            "unknown_speakers":282,"unresolved_stances":178,
            "v123_approved_scopes":0,"v128_published":0,
            "precision_recall_certified":False,"personal_advice_approved":False,
            "p0e_go":False,
            "status":"ACTUAL_NATIVE_HOST_CONFIRMED_RELEASE_STILL_ON_HOLD"}


def can_publish_research_or_personal_advice(receipt: dict):
    result=audit_v157_sha_only(receipt)
    # SHA-only host proof does not establish ChatGPT final semantic approval.
    return {"research_candidate_export_allowed":False,
            "v128_atomic_parent_knowledge_publish_allowed":False,
            "personal_advice_approved":False,"reason":"V123_13_SCOPE_FINAL_CHAT_AND_GOLD_OPEN",
            "native_host_commit_confirmed":result["native_host_events"]==13}
