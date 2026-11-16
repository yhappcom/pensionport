"""V152 source lineage and personal-law eligibility fail-closed quality gate.

This verifies a SHA-only receipt's internal consistency, NOT the existence or
meaning accuracy of private 1,481 owner cues. The actual original source was
replayed with the frozen V6 verify_source in the user's private chat runtime.
Do not mark 13 source scopes as 13 ChatGPT-reviewed approved scopes.

A personal financial result also requires actual approved V123/V128 knowledge,
current original official-law body bytes, an evaluated tax period and personal
eligibility; no self-submitted success boolean creates that evidence.
"""
from __future__ import annotations

import re

HEX = re.compile(r"[0-9a-f]{64}\Z")
RSCHEMA = "V152_REAL_SOURCE_NATIVE_SCOPE_REPARTITION_HOLD_V1"
ESCHEMA = "V152_AS_OF_2026_11_16_ELIGIBILITY_GATE_REQUIRED_V1"
HOLD_STATUS = "NATIVE_SOURCE_AND_RESEGMENTATION_VALIDATED__CHAT_MEANING_HOST_AND_GOLD_STILL_HOLD"


class V152QualityHold(ValueError):
    pass


def _must(condition, label):
    if not condition:
        raise V152QualityHold("V152_" + label)


def audit_sha_only_source_repartition(receipt: dict):
    """Validate source-plan candidate status, reject post-hoc false promotion."""
    _must(type(receipt) is dict and receipt.get("schema") == RSCHEMA, "SCHEMA")
    _must(receipt.get("source_sha256") == "638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d",
          "WRONG_OWNER_SOURCE")
    m = receipt.get("source_manifest_digests_sha256")
    _must(type(m) is str and HEX.fullmatch(m) is not None, "MANIFEST_SHA")
    counts = {
        "parent_cue_count": 1481,
        "parent_cue_coverage_verified": 1481,
        "replayed_child_source_scopes": 13,
        "total_provisional_atoms": 276,
        "baseline_atoms_274": 274,
        "new_native_v6_host_event_count": 0,
        "v123_approved_13": 0,
        "v128_actual_parent_published": 0,
    }
    for key, value in counts.items():
        _must(type(receipt.get(key)) is int and receipt[key] == value,
              "COUNT_" + key.upper())
    _must(receipt.get("scope_12") == {
        "first_cue": 1321, "last_cue": 1438, "mode": "PARTIAL"
    } and receipt.get("scope_13") == {
        "first_cue": 1439, "last_cue": 1481, "mode": "PARTIAL"
    }, "SEAM_BOUNDARY")
    _must(receipt.get("V151_new_atom_ids") == ["C00275", "C00276"], "SPLIT_IDS")
    _must(receipt.get("replayed_srt_source_verification_all_13") is True,
          "SOURCE_PRECHECK")
    for field in (
        "meaning_gold_full_video_certified", "high_risk_fn_zero_certified",
        "real_approved_video_knowledge_advice_evaluated",
        "personal_eligibility_approved", "individual_advice_authorized",
        "p0_e_go", "p0_go",
    ):
        _must(receipt.get(field) is False, "FALSE_COMPLETION_" + field.upper())
    _must(receipt.get("status") == HOLD_STATUS, "STATUS_DRIFT")
    return {
        "sha_only_source_precheck_count": 13,
        "source_cue_coverage": 1481,
        "candidate_atom_count": 276,
        "host_events_issued": 0,
        "research_gold_precision_recall_measured": False,
        "V123_chat_scopes_final_passed": 0,
        "V128_parent_published": 0,
        "status": "V152_SOURCE_REPARTITION_RECORDED_SEMANTIC_GOLD_HOLD",
        "P0_E_GO": False,
    }


def assess_personal_eligibility_gate(spec: dict, case: dict, account_kind: str,
                                     *, approved_parent_verified=False,
                                     official_original_bytes_verified=False):
    """Read-only eligibility preflight. Always requires further ChatGPT decision."""
    _must(type(spec) is dict and spec.get("schema") == ESCHEMA, "ELIGIBILITY_SCHEMA")
    _must(spec.get("as_of") == "2026-11-16", "ELIGIBILITY_EFFECTIVE_DATE")
    _must(spec.get("personal_recommendation_authorized") is False and
          spec.get("user_transaction_or_tax_approval") is False and
          spec.get("portfolio_or_approved_knowledge_db_accessed") is False,
          "FALSE_PERSONAL_APPROVAL")
    _must(account_kind in ("ISA", "PENSION"), "ACCOUNT_TYPE")
    _must(type(case) is dict, "CASE_INPUT")
    keys = spec["isa_questions_required"] if account_kind=="ISA" else spec["pension_questions_required"]
    _must(type(keys) is list and len(set(keys))==len(keys) and len(keys)>=5,
          "ELIGIBILITY_REQUIREMENTS")
    missing = [k for k in keys if case.get(k) is None or case.get(k)==""]
    if not approved_parent_verified:
        status = "HOLD_NO_REAL_V123_V128_APPROVED_VIDEO_KNOWLEDGE"
    elif not official_original_bytes_verified:
        status = "HOLD_CURRENT_OFFICIAL_ORIGINAL_NOT_REVALIDATED"
    elif missing:
        status = "HOLD_USER_TAX_AND_ACCOUNT_CONDITIONS_MISSING"
    else:
        status = "REQUIRES_CHATGPT_FINAL_ELIGIBILITY_AND_SUITABILITY_REVIEW"
    return {
        "account_kind": account_kind,
        "missing_required_fields": missing,
        "original_issuer_bytes_verified_in_this_invocation": bool(official_original_bytes_verified),
        "real_approved_video_knowledge_verified_in_this_invocation": bool(approved_parent_verified),
        "automatic_individual_approval": False,
        "trades_or_tax_returns_authorized": False,
        "status": status,
    }


def gate_approved_knowledge_based_answer(*, v128_parent_publication_count: int,
                                          v123_chat_approved_scopes: int,
                                          live_official_original_evidence_count: int,
                                          personal_case_complete: bool):
    """Never synthesize a parent publication or complete a trade from flags."""
    _must(type(v128_parent_publication_count) is int and
          type(v123_chat_approved_scopes) is int and
          type(live_official_original_evidence_count) is int and
          type(personal_case_complete) is bool, "INPUT_TYPES")
    if v128_parent_publication_count == 0 or v123_chat_approved_scopes != 13:
        return {"status":"HOLD_APPROVED_RESEARCH_KNOWLEDGE_UNAVAILABLE",
                "real_advisory_quality_measurable":False,
                "approved_knowledge_answer_issued":False}
    return {"status":"HOLD_REQUIRE_ACTUAL_PRIVATE_V128_SQLITE_PUBLICATION_REPLAY",
            "real_advisory_quality_measurable":False,
            "approved_knowledge_answer_issued":False}
