"""V158 public SHA-only proof for owner-private ChatGPT reviewed V6 atomic events.

This audits the aggregate ledger commitment; only a replay of the private
original SRT and 13 SQLite ledger heads can independently confirm actual host
events. Source-first speech-act AFFIRMED is not financial factual truth.
"""
from __future__ import annotations
import re

SHA64=re.compile(r"[0-9a-f]{64}\Z")
SOURCE="638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d"
SCHEMA="V158_REAL_SOURCE_FIRST_129_FIELD_PATCHED_NATIVE_HOST_SHA_ONLY_HOLD_V1"
STATUS="V158_REAL_13_NATIVE_SOURCE_HOST_PASSED__129_STANCE_KIND_EDITS__V123_V128_GOLD_HOLD"

class V158ReleaseEvidenceError(ValueError):pass

def _need(cond,name):
    if not cond:raise V158ReleaseEvidenceError("V158_"+name)

def audit_v158_public_receipt(record:dict):
    _need(type(record) is dict and record.get("schema")==SCHEMA,"SCHEMA")
    _need(record.get("original_video_id")=="5NvtBlmt93Y" and
          record.get("original_source_sha256")==SOURCE,"SOURCE_IDENTITY")
    expected={
        "original_cues":1481,"child_scopes":13,"candidate_atoms":284,
        "source_first_chat_kind_changes":28,
        "source_first_chat_stance_and_condition_changes":101,
        "source_first_chat_field_patches":129,
        "prior_unresolved_stances":178,"unresolved_stances_after_patch":77,
        "source_speaker_unknown":282,"unresolved_original_audio_cues":13,
        "quarantined_source_cues":27,"native_v6_host_committed_scopes":13,
        "native_v6_host_idempotent_replay_scopes":13,
        "actual_v123_chat_hold_scopes":13,"actual_v123_chat_pass_scopes":0,
        "actual_v128_parent_publication_count":0,
    }
    for key,v in expected.items():
        _need(type(record.get(key)) is int and record[key]==v,
              "FALSE_COUNT_"+key.upper())
    _need(record["source_first_chat_kind_changes"]+
          record["source_first_chat_stance_and_condition_changes"]==
          record["source_first_chat_field_patches"],
          "FIELD_PATCH_COUNT")
    _need(record["prior_unresolved_stances"]-
          record["source_first_chat_stance_and_condition_changes"]==
          record["unresolved_stances_after_patch"],"STANCE_REDUCTION_COUNT")
    _need(record.get("affirms_are_utterance_not_verified_truth") is True,
          "AFFIRMED_TRUTH_CONFUSION")
    for field in ("current_precision_95_certified","current_recall_98_certified",
                  "zero_high_risk_FN_certified","personal_financial_suitability_verified",
                  "p0e_go"):
        _need(record.get(field) is False,"UNSUPPORTED_APPROVAL_"+field.upper())
    for k in ("private_review_129_row_digest_sha256",
              "private_unresolved_13_docket_sha256","private_owner_package_sha256"):
        v=record.get(k)
        _need(type(v) is str and SHA64.fullmatch(v) is not None,
              "PRIVATE_OWNER_DIGEST_"+k.upper())
    event=record.get("host_event_sha256_by_scope")
    _need(type(event) is dict and
          set(event)=={f"B{i:04d}" for i in range(1,14)} and
          len(set(event.values()))==13 and
          all(type(v) is str and SHA64.fullmatch(v) is not None for v in event.values()),
          "13_NATIVE_SCOPE_DIGESTS_REQUIRED")
    _need(record.get("status")==STATUS,"FALSE_STATE_PROMOTION")
    return {"owner_original_cues":1481,"candidate_atoms":284,
            "real_native_v6_event_heads":13,
            "explicit_chat_source_first_changes":129,
            "remaining_unresolved_stances":77,"unknown_speaker_roles":282,
            "original_audio_or_official_open":13,"V123_final_pass_scopes":0,
            "V128_parent_published":0,"gold_accuracy_certified":False,
            "individual_advice_approved":False,"p0e_go":False}

def research_release_allowed(record:dict):
    result=audit_v158_public_receipt(record)
    return {"native_v6_structural_ledger_ready":result["real_native_v6_event_heads"]==13,
            "V123_release_approved":False,"V128_knowledge_publish_allowed":False,
            "personalized_advice_authorized":False}
