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
from .p0_incremental_source_gate import verify as verify_p0_incremental_source
from .p0_claim_ownership_gate import verify as verify_p0_claim_ownership
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
from .advisory_final_answer_standard import run as verify_final_answer_rubric_v2
from .first_five_source_readiness_gate import verify as verify_first_five_readiness
from .first_five_quality_gate import verify as verify_first_five_quality
from .first_five_adjudication_receipt_gate import verify as verify_five_source_adjudication
from .first_five_private_event_gate import verify as verify_private_source_event_pointer
from .first_five_phase1_cue_gate import verify as verify_five_phase1_cue_review
from .first_five_phase1_second_ten_gate import verify as verify_second_ten_cue_review
from .first_five_phase1_third_twenty_gate import verify as verify_third_twenty_cue_review
from .first_five_40_scoped_fact_gate import verify as verify_scoped_finance_first40
from .first_five_40_formal_approval_b04_gate import verify as verify_first40_B04_safe_links
from .first_five_40_official_replay_approval_gate import verify as verify_first40_external_approval_policy
from .first_five_40_retrieval_bridge import audit as audit_first40_live_retrieval
from .p4_active_integration import audit as audit_p4_active_integration
from .p3_original_27_source_gate import verify as verify_p3_original_27
from .p4_p3_source_integration import audit as audit_p4_p3_live
from .six_stage_original_replay import audit as audit_ten_original
from .crossvideo_14_quarantine import audit as audit_crossvideo_guard
from .first_five_residual_15_gate import audit as audit_first_five_residual15
from .first_five_all5129_risk_gate import audit as audit_all5129_risk
from .video10_all34_cue_gate import audit as audit_video10_all34
from .video7_compilation_dedup_gate import audit as audit_video7_compilation
from .extra_video6_8_9_source_gate import audit as audit_extra369
from .extra369_unanchored_window_gate import audit as audit_extra369_gap
from .extra369_low65_source_gate import audit as audit_extra369_low65
from .extra369_linked97_cue_gap_gate import audit as audit_partial97
from .six_stage_frozen_advisory_eval import run as evaluate_frozen_questions
from .phase1_to_phase4_progress import audit as audit_p1_p3_p4_progress

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
    # Mandatory real-path gate: registry/bundle/source-anchor drift aborts the
    # transaction before any terminal receipt can be printed.
    p0_incremental_integrity=verify_p0_incremental_source(root)
    p0_claim_ownership=verify_p0_claim_ownership(root)
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
    final_answer_rubric_v2=verify_final_answer_rubric_v2(root)
    first_five_readiness=verify_first_five_readiness(root)
    first_five_quality=verify_first_five_quality(root)  # private 1-70 ZIP uses its separate CLI
    first_five_adjudication=verify_five_source_adjudication(root)
    first_five_private_source_pointer=verify_private_source_event_pointer(root)
    first_five_current_phase1=verify_five_phase1_cue_review(root)
    first_five_current_phase1_w20=verify_second_ten_cue_review(root)
    first_five_current_phase1_w40=verify_third_twenty_cue_review(root)
    first_five_first40_scoped_finance=verify_scoped_finance_first40(root)
    first_five_first40_B04_education_review=verify_first40_B04_safe_links(root)
    first_five_first40_official_repro_policy=verify_first40_external_approval_policy(root)
    first40_live_advisory_connection=audit_first40_live_retrieval(root)
    p1_p3_p4_progress=audit_p1_p3_p4_progress(root)
    p4_active=audit_p4_active_integration(root)
    p3_source_review=verify_p3_original_27(root)
    p4_p3_knowledge=audit_p4_p3_live(root)
    original_ten=audit_ten_original(root)
    crossvideo_hazards=audit_crossvideo_guard(root)
    first_five_residual15=audit_first_five_residual15(root)
    all5129_risk=audit_all5129_risk(root)
    video10_all34=audit_video10_all34(root)
    video7_dup=audit_video7_compilation(root)
    extra369=audit_extra369(root)
    extra369_gap=audit_extra369_gap(root)
    extra369_low65=audit_extra369_low65(root)
    partial97=audit_partial97(root)
    frozen_advice=evaluate_frozen_questions(root)
    receipt={
        "schema":"IRE_V5_ONE_TURN_RESEARCH_RECEIPT_V1",
        "research_state":"ALL_53_NEW_VIDEO_CLAIMS_DISPOSITIONED",
        "one_request_research_complete":True,
        "repeat_user_progress_command_required":False,
        "actual_ai_semantics_and_source_checks":"ACTIVE_CHAT_HOST_MUST_SUPPLY",
        "external_model_api_required":False,
        "private_original_archive_verified_in_this_process":private_zip is not None,
        "p0_incremental_source_derivative_integrity":p0_incremental_integrity,
        "p0_provisional_claim_window_ownership":p0_claim_ownership,
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
        "p3_final_answer_rubric_v2":final_answer_rubric_v2,
        "first_five_raw_source_reanalysis_readiness":first_five_readiness,
        "first_five_original_quality_audit":first_five_quality,
        "first_five_13_omission_equivalence_and_receipt_audit":first_five_adjudication,
        "first_five_private_provisional_event_pointer_no_source_replay_claim":first_five_private_source_pointer,
        "first_five_video1_first_ten_original_cue_review_private_v4":first_five_current_phase1,
        "first_five_video1_first_twenty_original_cue_review_private_v5":first_five_current_phase1_w20,
        "first_five_video1_first_forty_original_cue_review_private_v7":first_five_current_phase1_w40,
        "first_five_40_scoped_official_education_retrieval_v1":first_five_first40_scoped_finance,
        "first_five_40_five_terminal_rule_dispositions_and_B04_scoped_edges":first_five_first40_B04_education_review,
        "first_five_40_reproducible_official_extractions_and_signed_knowledge_policy":first_five_first40_official_repro_policy,
        "first_five_40_official_education_live_advisory_retrieval":first40_live_advisory_connection,
        "first_five_P1_P3_P4_scoped_progress":p1_p3_p4_progress,
        "p4_active_integrated_education22":p4_active,
        "first_five_video1_w41_w67_original_source_atomic_review":p3_source_review,
        "p4_p3_incremental_29_live_education_nodes":p4_p3_knowledge,
        "first_ten_raw_srt_metadata_and_source_replay_readiness":original_ten,
        "new_five_source_anchored_negative_risk_quarantine":crossvideo_hazards,
        "first_five_original_15_residual_and_duplicate_conflict_adjudication":first_five_residual15,
        "first_five_5129_cue_risk_22_source_group_audit":all5129_risk,
        "extra_video10_all34_cue_scoped_financial_review":video10_all34,
        "extra_video7_compilation_dedup_no_independent_holdout":video7_dup,
        "extra_video6_8_9_3123cue_source_scoped_candidate_36":extra369,
        "extra_three_175_window_78_unanchored_13_scoped_risks":extra369_gap,
        "extra_three_65_low_keyword_windows_semantic_audit":extra369_low65,
        "extra_three_97_claim_linked_windows_506_residual_cue_audit":partial97,
        "new_twelve_frozen_questions_structural_advisory_evaluation":frozen_advice,
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
