"""Run every deterministic V5 gate and issue a terminal one-turn research receipt.

This is the GitHub half of the user's ChatGPT+GitHub research workflow.
ChatGPT must perform any semantic analysis and official-source searches in the
active turn; this program cannot invoke ChatGPT without an external model API,
and cannot run an independent human/blind review. It terminates the work with
a fully classified status rather than requesting repeated '진행' commands.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from .preflight import run as preflight_run
from .one_turn_resolution_gate import verify as verify_33
from .integrated_education_gate import verify as verify_education_graph
from .advisory_education_rehearsal import audit as verify_advisory_access
from .new_video_batch_gate import verify as verify_new_video
from .new_video_merge_gate import verify as verify_new_video_merge
from .new_video_followup_gate import verify as verify_followup_video
from .semantic_evidence_gate import verify as verify_semantic_evidence
from .chat_evidence_acceptance_gate import verify as verify_chat_evidenced_facts
from .legacy_consolidation_gate import verify as verify_legacy_consolidation
from .advisory60 import audit as verify_advisory60
from .advisory60_validation import verify as verify_advisory60_validation
from .advisory_semantic import audit as verify_p0_semantic
from .advisory_evidence import audit as verify_p1_evidence
from .advisory_decision import audit as verify_p2_decision
from .advisory_answer_pipeline import audit as verify_p3_answer
from .advisory_final_answer_review import run as verify_final_answer_quality

def run(root:Path,private_zip:Path|None=None)->int:
    root=root.resolve()
    if private_zip is not None:
        from .review44_gate import verify as verify44
        from .external_authority_recheck import verify as verify10
        a=verify44(root,private_zip=private_zip)
        b=verify10(root,private_zip=private_zip)
        new_private=verify_new_video(root,private_zip=private_zip)
        new_followup_private=verify_followup_video(root,private_zip=private_zip)
        if new_followup_private["private_original_claim_spans_byte_rechecked_now"]!=12:
            raise RuntimeError("SECOND_UNSEEN_VIDEO_CLAIM_SPANS_NOT_RECHECKED")
        if new_private["all_private_original_cue_windows_byte_verified_now"]!=13:
            raise RuntimeError("UNSEEN_VIDEO_SOURCE_WINDOWS_NOT_VERIFIED")
        if a["original_claim_spans_byte_reverified_this_run"]!=44 or not b[
            "private_srt_bytes_reverified_during_this_run"]:
            raise RuntimeError("PRIVATE_SOURCE_BYTES_NOT_INDEPENDENTLY_RECHECKED")
    n=preflight_run(root)
    if n:
        print("ONE_TURN_RESEARCH_RECEIPT_NOT_ISSUED_PREFLIGHT_FAILED",flush=True)
        return n
    decision=verify_33(root)
    education=verify_education_graph(root)
    advisory_access=verify_advisory_access(root)
    new_video=verify_new_video(root)
    new_video_merge=verify_new_video_merge(root)
    followup_video=verify_followup_video(root)
    semantic_evidence=verify_semantic_evidence(root)
    fact_acceptance=verify_chat_evidenced_facts(root)
    legacy_consolidation=verify_legacy_consolidation(root)
    advisory60=verify_advisory60(root)
    validation60=verify_advisory60_validation(root)
    p0_semantic=verify_p0_semantic(root)
    p1_evidence=verify_p1_evidence(root)
    p2_decision=verify_p2_decision(root)
    p3_answer=verify_p3_answer(root)
    final_answer_quality=verify_final_answer_quality(root)
    receipt={
        "schema":"IRE_V5_ONE_TURN_RESEARCH_RECEIPT_V1",
        "research_state":"ALL_53_NEW_VIDEO_CLAIMS_DISPOSITIONED",
        "one_request_research_complete":True,
        "repeat_user_progress_command_required":False,
        "actual_ai_semantics_and_source_checks":"ACTIVE_CHAT_HOST_MUST_SUPPLY",
        "external_model_api_required":False,
        "private_original_archive_verified_in_this_process":private_zip is not None,
        "claims":decision,
        "education_knowledge":education,
        "advisory_access_rehearsal":advisory_access,
        "new_video_vertical_slice":new_video,
        "new_video_incremental_merge":new_video_merge,
        "second_unseen_video_full_research":followup_video,
        "second_unseen_video_semantic_evidence_recheck":semantic_evidence,
        "source_scoped_chat_researched_facts":fact_acceptance,
        "legacy_research_consolidation":legacy_consolidation,
        "sixty_claim_decision_support":advisory60,
        "sixty_claim_new_question_validation":validation60,
        "p0_multidomain_semantic_plan":p0_semantic,
        "p1_atomic_source_scoped_evidence":p1_evidence,
        "p2_conditional_decision_analysis":p2_decision,
        "p3_conditional_answer_quality":p3_answer,
        "p3_real_final_answer_acceptance":final_answer_quality,
        "blind_review_required_for_research_fact_acceptance":False,
        "independent_human_blind_evaluation_completed":False,
        "formal_personal_investment_advice_authorized":False,
        "terminal_outcome":"RESEARCH_CLOSED_NOT_ADVICE_RELEASED",
    }
    print("ONE_TURN_RESEARCH_RECEIPT "+json.dumps(
        receipt,ensure_ascii=False,sort_keys=True),flush=True)
    return 0

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--private-zip",type=Path)
    a=p.parse_args()
    raise SystemExit(run(a.root,a.private_zip))

if __name__=="__main__":
    main()
