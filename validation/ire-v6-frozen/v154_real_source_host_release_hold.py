"""V154 SHA-only public release custody for the 2026-11-16 real owner-private replay.

This module audits the *public summary contract only*. Source content, native
SQLite event heads, original ChatGPT judgments and blind-gold scores are
replayed and retained separately in the user's private owner packet.

A public CI PASS must NEVER be read as semantic PASS, V123 approval,
independent 95/98/zero high-risk FN, V128 release or personal advice.
"""
from __future__ import annotations
import re

SCHEMA="V154_REAL_5_STAGE_OWNER_PRIVATE_E2E_SHA_ONLY_V1"
STATUS="REAL_V154_ORIGINAL_SOURCE_SINGLE_TURN_13_V6_HOST_AND_V123_V128_HOLD__NO_RESEARCH_APPROVAL"
OWNER_SHA="638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d"
HEX=re.compile(r"[0-9a-f]{64}\Z")
FIELDS=[
 "108_cue_dispositions", "atom_change_log", "native_host_13_receipts",
 "revised_parent_source", "single_turn_5_stages",
 "v123_13_hold_summary", "v123_final_13_hold_reviews",
 "v128_no_partial_publish",
]


class V154InvalidReleaseEvidence(ValueError):
    pass


def _check(ok, name):
    if not ok:
        raise V154InvalidReleaseEvidence("V154_" + name)


def audit_v154_public_owner_replay_hold(r):
    _check(type(r) is dict and r.get("schema")==SCHEMA, "SCHEMA")
    _check(r.get("original_srt_sha256")==OWNER_SHA and
           r.get("original_video_id")=="5NvtBlmt93Y", "SOURCE_PIN")
    expected={
        "source_cues":1481, "source_scopes_audited":13,
        "provisional_atoms":278,
        "original_108_cue_linked_to_atoms":15,
        "original_108_cue_no_atom":18,
        "original_108_cue_remaining_unresolved":75,
        "source_cues_under_private_quarantine":86,
        "native_v6_host_batches_committed":13,
        "native_v6_host_replays_idempotent":13,
        "native_v6_source_model_events":25,
        "native_v6_source_proof_events":25,
        "native_v6_unquarantined_attempts_rejected":12,
        "v123_real_chat_hold_cases":13,
        "v123_real_chat_final_pass":0,
        "v123_research_export_negative_controls":13,
        "v1271_child_hold_checkpoints":13,
        "v128_approved_knowledge_entries":0,
        "v128_approved_knowledge_publications":0,
        "v128_private_knowledge_events":0,
    }
    for key,value in expected.items():
        _check(type(r.get(key)) is int and r[key]==value,
               "REAL_REPLAY_CENSUS_"+key.upper())
    _check(r["original_108_cue_linked_to_atoms"]+
           r["original_108_cue_no_atom"]+
           r["original_108_cue_remaining_unresolved"]==108,
           "108_PARTITION")
    _check(r["source_cues_under_private_quarantine"] >=
           r["original_108_cue_remaining_unresolved"],
           "FINANCE_RESIDUAL_NOT_ESCROWED")
    _check(r.get("as_of")=="2026-11-16" and r.get("status")==STATUS,
           "STATUS")
    for key in (
        "full_atomic_blind_gold_complete", "precision_95_recall_98_certified",
        "zero_high_risk_false_negatives_certified",
        "whole_parent_semantic_seams_final_approved",
        "real_v128_approved_knowledge_based_advice_tested",
        "individual_income_account_tax_eligibility_evaluated",
        "p0e_go", "p0_go",
    ):
        _check(r.get(key) is False,"FALSE_RESEARCH_APPROVAL_"+key.upper())
    for key in ("all_202_prior_source_context_notes_available",
                "operator_derived_owner_inventory_not_independently_attested"):
        _check(r.get(key) is True,"OWNER_PROVENANCE_"+key.upper())
    private_hashes=r.get("private_file_sha256")
    _check(type(private_hashes) is dict and
           set(private_hashes)==set(FIELDS) and
           all(type(v) is str and HEX.fullmatch(v) for v in private_hashes.values()),
           "PRIVATE_SHA_CENSUS")
    return {
        "real_original_source_scopes_native_host_structural_committed":13,
        "source_cue_coverage":1481,
        "provisional_atomic_claims":278,
        "residual_v6_unresolved_cues":75,
        "v123_real_final_pass_scopes":0,
        "v128_research_publications":0,
        "blind_precision_recall_measured":False,
        "high_risk_FN_zero_certified":False,
        "actual_approved_knowledge_personal_advice":False,
        "p0e_go":False,
        "status":"V154_REAL_SOURCE_HOST_13_COMMITTED_SEMANTIC_GOLD_AND_KNOWLEDGE_HOLD",
    }
