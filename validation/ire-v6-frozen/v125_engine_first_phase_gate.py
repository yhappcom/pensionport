"""V125 phase-order contract: statuses cannot self-authorize future phases.

This module is a policy evaluator for governance checks only.
Engine completion requires real ChatGPT-and-source evidence reviewed outside
these flags; callers cannot manufacture completion by setting booleans.
"""
from __future__ import annotations

import json
from pathlib import Path

REQUIRED_IDS = tuple("E"+str(i) for i in range(1,11))
KEYS = (
    "whole_video_multi_window_one_request",
    "owner_original_sha_manifest_and_scope_provenance",
    "full_cue_cross_clause_semantic_census_and_quality",
    "chat_final_review_finance_primary_evidence",
    "source_reconciled_append_only_knowledge_accumulation",
    "dedup_equivalence_conflict_supersession_and_versioning",
    "knowledge_question_retrieval_with_provenance",
    "current_law_web_search_chat_review_advisory_end_to_end",
    "failure_resume_idempotency_and_cross_video_consistency",
    "private_real_source_end_to_end_acceptance_and_ci",
)

def audit_engine_first_policy(policy: dict) -> dict:
    if type(policy) is not dict or policy.get("schema") != "IRE_V6_V125_ENGINE_FIRST_PORTFOLIO_DEFERRED_POLICY_V1":
        raise ValueError("ENGINE_FIRST_SCHEMA_INVALID")
    if policy.get("user_approved_order") != [
        "ENGINE_COMPLETE_AND_VERIFIED","OTHER_VIDEO_RESEARCH","PORTFOLIO_DRIVE_INTEGRATION"
    ] or policy.get("active_phase") != "ENGINE_DEVELOPMENT_ONLY":
        raise ValueError("ENGINE_FIRST_ORDER_BROKEN")
    req = policy.get("engine_completion_requirements")
    if type(req) is not dict or tuple(req) != KEYS:
        raise ValueError("ENGINE_FIRST_REQUIREMENTS_CHANGED")
    if any(v not in ("OPEN","NOT_IMPLEMENTED") for v in req.values()):
        raise ValueError("ENGINE_FIRST_FALSE_COMPLETION_FLAG")
    for name in ("completed_engine","further_video_research_authorized",
                 "portfolio_connector_usage_for_engine",
                 "portfolio_integration_implementation_authorized",
                 "current_research_candidate_release_allowed","p0_go"):
        if policy.get(name) is not False:
            raise ValueError("ENGINE_FIRST_UNAUTHORIZED_PHASE_OR_RELEASE:"+name)
    if policy.get("new_video_research_after_engine_gate_only") is not True:
        raise ValueError("ENGINE_FIRST_NEW_VIDEO_ORDER_BREAK")
    if policy.get("portfolio_readonly_integration_after_engine_completion_only") is not True:
        raise ValueError("ENGINE_FIRST_PORTFOLIO_ORDER_BREAK")
    if policy.get("chatgpt_final_reviewer") != "CHATGPT_IN_CHAT" or policy.get("external_model_api_required") is not False:
        raise ValueError("ENGINE_FIRST_CHAT_GOVERNANCE_CHANGED")
    return {
        "schema":"IRE_V6_V125_PHASE_ORDER_AUDIT_V1",
        "engine_requirements_count":len(KEYS),
        "engine_requirements_open":len(KEYS),
        "engine_completed":False,
        "new_video_research_allowed":False,
        "portfolio_integration_allowed":False,
        "current_status":"ENGINE_DEVELOPMENT_ONLY_NO_GO",
    }

if __name__=="__main__":
    path=Path(__file__).with_name("V125_ENGINE_FIRST_PORTFOLIO_DEFERRED_POLICY.json")
    print(json.dumps(audit_engine_first_policy(json.loads(path.read_text(encoding="utf-8"))),
                     ensure_ascii=False,sort_keys=True))
