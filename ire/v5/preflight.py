"""One deterministic, fail-closed V5 preflight for local work and GitHub CI.

Use before pushing a research-engine change:
    python -m ire.v5.preflight --root .

Requires the same pinned dependencies as the V5 workflow. No external model
API and no network searches are performed. This is a software contract check,
not independent certification of financial claims or investment advice.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# These commands preserve every verification step in the former V5 standalone
# workflow. Keep the full unit-test discovery last, after the narrower gates.
_CHECKS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("compile_v5", ("-m", "compileall", "-q", "ire/v5")),
    ("video_id_reconciliation",
     ("-m", "ire.v5.continuous_integration", "--root", ".")),
    ("no_unreviewed_pilot_promotion",
     ("-m", "ire.v5.review_gate",
      "--review", "ire/v5/reviews/4TFtEQxSM38_20261104.json",
      "--prior", "data/claims.jsonl")),
    ("advisory_replay_safety",
     ("-m", "ire.v5.advisory_replay", "--root", ".")),
    ("twenty_plus_five_intake",
     ("-m", "ire.v5.knowledge_stage", "--root", ".")),
    ("five_original_source_studies",
     ("-m", "ire.v5.five_study_gate", "--root", ".")),
    ("provisional_knowledge_reconciliation",
     ("-m", "ire.v5.provisional_knowledge_gate", "--root", ".")),
    ("independent_authority_crosscheck",
     ("-m", "ire.v5.external_authority_recheck", "--root", ".")),
    ("deduplicated_education_safety",
     ("-m", "ire.v5.education_release_gate", "--root", ".")),
    ("remaining_44_source_triage",
     ("-m", "ire.v5.review44_gate", "--root", ".")),
    ("single_turn_final_33_research_verdicts",
     ("-m", "ire.v5.one_turn_resolution_gate", "--root", ".")),
    ("integrated_thirteen_education_topics",
     ("-m", "ire.v5.integrated_education_gate", "--root", ".")),
    ("advisory_access_rehearsal_53_claims",
     ("-m", "ire.v5.advisory_education_rehearsal", "--root", ".")),
    ("unseen_original_video_full_research_and_reconcile",
     ("-m", "ire.v5.new_video_batch_gate", "--root", ".")),
    ("unseen_video_incremental_knowledge_reconciliation",
     ("-m", "ire.v5.new_video_merge_gate", "--root", ".")),
    ("second_unseen_video_full_source_temporal_gate",
     ("-m", "ire.v5.new_video_followup_gate", "--root", ".")),
    ("fine_grained_ipo_semantic_and_current_law_recheck",
     ("-m", "ire.v5.semantic_evidence_gate", "--root", ".")),
    ("user_approved_chat_source_scoped_fact_gate",
     ("-m", "ire.v5.chat_evidence_acceptance_gate", "--root", ".")),
    ("first_three_legacy_reconciliation_batches_60_and_master_116",
     ("-m", "ire.v5.legacy_consolidation_gate", "--root", ".")),
    ("research_tree_original_and_new_file_integrity",
     ("-m", "ire.v5.repository_tree_gate", "--root", ".")),
    ("sixty_legacy_claim_advisory_decision_support",
     ("-m", "ire.v5.advisory60", "--root", ".")),
    ("new_chat_unseen_advisory_routing_official_scope_and_arithmetic",
     ("-m", "ire.v5.advisory60_validation", "--root", ".")),
    ("p0_multidomain_semantic_decomposition",
     ("-m", "ire.v5.advisory_semantic", "--root", ".")),
    ("p1_atomic_source_scoped_evidence",
     ("-m", "ire.v5.advisory_evidence", "--root", ".")),
    ("p2_conditional_decision_scenarios",
     ("-m", "ire.v5.advisory_decision", "--root", ".")),
    ("p3_generated_conditional_answer_quality_audit",
     ("-m", "ire.v5.advisory_answer_pipeline", "--root", ".")),
    ("p3_final_answer_directness_and_source_bound_evaluation",
     ("-m", "ire.v5.advisory_final_answer_review", "--root", ".")),
    ("p3_final_answer_independent_math_and_hard_fail_rubric_v2",
     ("-m", "ire.v5.advisory_final_answer_standard", "--root", ".")),
    ("first_five_raw_source_readiness_not_full_research_approval",
     ("-m", "ire.v5.first_five_source_readiness_gate", "--root", ".")),
    ("first_five_original_risk_quality_and_advisory_retrieval_gap",
     ("-m", "ire.v5.first_five_quality_gate", "--root", ".")),
    ("first_five_original_45_span_provenance_retrieval_bridge",
     ("-m", "ire.v5.first_five_advisory_bridge", "--root", ".")),
    ("first_five_all_288_window_source_meaning_provenance",
     ("-m", "ire.v5.first_five_window_review_gate", "--root", ".")),
    ("first_five_68_atomic_claims_original_and_knowledge_safety",
     ("-m", "ire.v5.first_five_atomic_claim_gate", "--root", ".")),
    ("first_five_221_unprocessed_atomic_candidate_integrity",
     ("-m", "ire.v5.first_five_remnant_221_gate", "--root", ".")),
    ("first_five_13_omission_305_equivalence_and_receipt_integrity",
     ("-m", "ire.v5.first_five_adjudication_receipt_gate", "--root", ".")),
    ("first_five_private_288_model_event_pointer_no_fraud",
     ("-m", "ire.v5.first_five_private_event_gate", "--root", ".")),
    ("first_five_video1_10_windows_cue_by_cue_recheck",
     ("-m", "ire.v5.first_five_phase1_cue_gate", "--root", ".")),
    ("first_five_video1_w11_w20_cue_recheck_after_w01_w10",
     ("-m", "ire.v5.first_five_phase1_second_ten_gate", "--root", ".")),
    ("first_five_video1_w21_to_w40_original_cue_tax_and_chain_audit",
     ("-m", "ire.v5.first_five_phase1_third_twenty_gate", "--root", ".")),
    ("first_five_first40_narrow_official_rule_and_readonly_knowledge_overlay",
     ("-m", "ire.v5.first_five_40_scoped_fact_gate", "--root", ".")),
    ("first_five_first40_five_rule_dispositions_and_B04_scoped_relation_gate",
     ("-m", "ire.v5.first_five_40_formal_approval_b04_gate", "--root", ".")),
    ("first_five_40_official_content_pinned_offline_and_external_dual_signature_policy",
     ("-m", "ire.v5.first_five_40_official_replay_approval_gate", "--root", ".")),
    ("first_five_40_official_education_in_live_advisory_pipeline",
     ("-m", "ire.v5.first_five_40_retrieval_bridge", "--root", ".")),
    ("first_five_p1_p3_p4_progress_source_and_knowledge_safety",
     ("-m", "ire.v5.phase1_to_phase4_progress", "--root", ".")),
    ("p4_active_integrated_education22_source_and_pending_quarantine",
     ("-m", "ire.v5.p4_active_integration", "--root", ".")),
    ("video1_w41_w67_original_srt_486cue_89atom_source_provenance",
     ("-m", "ire.v5.p3_original_27_source_gate", "--root", ".")),
    ("p4_p3_29node_live_incremental_education_source_gate",
     ("-m", "ire.v5.p4_p3_source_integration", "--root", ".")),
    ("first_ten_original_source_five_plus_five_and_crossvideo_quarantine",
     ("-m", "ire.v5.six_stage_original_replay", "--root", ".")),
    ("extra_five_14_source_risk_quarantine_live_p3",
     ("-m", "ire.v5.crossvideo_14_quarantine", "--root", ".")),
    ("frozen_12_new_financial_questions_actual_p3_advisory",
     ("-m", "ire.v5.six_stage_frozen_advisory_eval", "--root", ".")),
    ("first_five_original_15_source_spans_68_237_duplication_risk_gate",
     ("-m", "ire.v5.first_five_residual_15_gate", "--root", ".")),
    ("all_v5_regression_tests",
     ("-m", "unittest", "discover", "-s", "ire/v5/tests",
      "-p", "test_*.py", "-v")),
)


def planned_checks() -> tuple[tuple[str, tuple[str, ...]], ...]:
    return _CHECKS


def run(root: Path) -> int:
    root = root.resolve()
    if not (root / "data/claims.jsonl").is_file():
        print("PREFLIGHT_FAIL: repository root is invalid", file=sys.stderr)
        return 2
    for i, (label, argv) in enumerate(_CHECKS, 1):
        print(f"PREFLIGHT_START {i}/{len(_CHECKS)} {label}", flush=True)
        result = subprocess.run((sys.executable, *argv), cwd=root, check=False)
        if result.returncode:
            print(f"PREFLIGHT_FAIL {label} exit={result.returncode}",
                  file=sys.stderr, flush=True)
            return result.returncode
        print(f"PREFLIGHT_PASS {label}", flush=True)
    print(f"PREFLIGHT_ALL_PASS count={len(_CHECKS)}", flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--list", action="store_true",
                        help="Show exact checks without executing them.")
    args = parser.parse_args()
    if args.list:
        print(json.dumps(
            [{"step": name, "argv": list(argv)} for name, argv in _CHECKS],
            ensure_ascii=False, indent=2))
        return 0
    return run(args.root)


if __name__ == "__main__":
    raise SystemExit(main())
