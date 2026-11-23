#!/usr/bin/env python3
"""Issue 48/50 adversarial RED/GREEN release-negative policy receipt checker.

Only validates public immutable regression contracts. V6 strict full-tree CI
separately executes the actual source code/synthetic SQLite tests.
"""
from __future__ import annotations
import json
from pathlib import Path
from scripts.ire_checklist_gate import CATALOG,STATE,validate as checklist_validate
from scripts.ire_current_status_gate import LEDGER,validate as status_validate

ROOT=Path(__file__).resolve().parent.parent
P204=Path("docs/IRE_P0_2_04_ISSUES_48_50_RED_GREEN_SHA_ONLY_20261123.json")
P203=Path("docs/IRE_P0_2_03_ETF250_SIX_AXIS_SHA_ONLY_20261123.json")
SRC_SHA="e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b"
PRE_SHA="bd85fec39f0ff25ea3d2a7944a1d983f72b9d25e"
RED_SHA="a3abecb03b06430126b0da14170d7c13ca581be7"
GREEN_SHA="d08dd33010c73ffe830d23dfa692146a709f4f27"

def load(root,path):
    return json.loads((Path(root)/path).read_text(encoding="utf8"))

def verify(root=ROOT,*,receipt=None,state=None,ledger=None,p203=None):
    root=Path(root)
    r=receipt if receipt is not None else load(root,P204)
    s=state if state is not None else load(root,STATE)
    l=ledger if ledger is not None else load(root,LEDGER)
    prior=p203 if p203 is not None else load(root,P203)
    errors=[]
    def need(condition, label):
        if not condition:
            errors.append("P204_"+label)
    need(not checklist_validate(load(root,CATALOG),s,root=root),
         "FULL_60_TASK_CHECKLIST_INVALID")
    need(not status_validate(l,root=root),
         "CANONICAL_FINANCE_HOLD_INVALID")
    items=s.get("items",[])
    next_i=next((i for i,x in enumerate(items) if x.get("status")!="PASS"),len(items))
    actual=items[next_i]["id"] if next_i<len(items) else "ALL_COMPLETE"
    need(len(items)==60 and all(x.get("status")=="PASS" for x in items[:15])
         and items[15].get("id")=="P0-2-04"
         and items[15].get("status") in {"READY","IN_PROGRESS","HOLD","FAIL","PASS"}
         and items[16].get("id")=="P0-2-05",
         "P204_ORDER_AND_PRIOR_15_PASS")
    need(l.get("development_gate",{}).get("this_item")==actual and
         l.get("development_gate",{}).get("pending_next_item")==actual,
         "ACTIVE_STAGE_CURSOR_MISMATCH")
    need(r.get("schema")=="IRE_P0_2_04_ISSUES_48_50_ADVERSARIAL_RED_GREEN_RECEIPT_V1"
         and r.get("item_id")=="P0-2-04" and r.get("as_of")=="2026-11-23"
         and r.get("issue_numbers")==[48,50],
         "ISSUE_ID_AND_SCHEMA")
    need(r.get("baseline_sha")==PRE_SHA and r.get("baseline_run_id")==45117726788
         and r.get("baseline_six_jobs_succeeded")==6
         and r.get("explicit_red_sha")==RED_SHA
         and r.get("explicit_red_run_id")==45118510783
         and r.get("red_negative_tests_failed_as_expected")==3
         and r.get("candidate_green_sha")==GREEN_SHA
         and r.get("candidate_green_run_id")==45118804379,
         "RED_GREEN_CI_CHAIN_AND_3_DEFECTS")
    need(r.get("cross_cue_rebuttal_synthetic_tests")==5
         and r.get("legacy_v2_synthetic_tests")==5,
         "TEN_NEW_ATTACK_AND_POSITIVE_CASES")
    need(r.get("issue48_unmodelled_high_risk_tax_assertion_can_close_research") is False
         and r.get("issue48_nonfact_self_label_independent_role_certified") is False
         and r.get("issue48_source_first_residual_all_cues_censused") is True
         and r.get("issue48_source_first_atomic_exhaustiveness_certified") is False,
         "ISSUE48_SOURCE_FIRST_NONFACT_NO_FALSE_COMPLETE")
    need(all(r.get(k) is True for k in (
         "issue50_negated_quote_same_cue_rejected",
         "issue50_cross_cue_rebuttal_and_disclaimer_rejected",
         "issue50_cross_window_stance_risk_rejected",
         "issue50_interleaved_duplicate_rule_rejected",
         "issue50_model_revision_invalidates_rule",
         "issue50_revision_bound_rule_status_stable_after_unrelated_review")),
         "ISSUE50_NEGATION_DUPLICATE_REVISION_NO_BYPASS")
    need(r.get("issue50_rebuttal_locality_radius_cues")==3
         and r.get("issue50_scope_stance_semantics_fully_certified") is False,
         "NO_FALSE_SEMANTIC_GENERALIZATION")
    need(r.get("issue50_legacy_v2_readonly_historical_reducer_replay_available") is True
         and r.get("issue50_legacy_v2_historic_research_complete_declassified_no_go") is True
         and r.get("issue50_legacy_v2_synthetic_fixture_only") is True
         and r.get("issue50_real_owner_v2_database_import_or_migration_approved") is False
         and r.get("issue50_original_legacy_database_mutated") is False,
         "V2_HISTORIC_REPLAY_NO_UNCONTROLLED_MIGRATION")
    need(r.get("issue50_current_official_source_snapshot_date_bounded") is True
         and r.get("issue50_as_of_future_version_unsilenced") is False
         and r.get("issue50_arithmetic_math_from_statutory_verification_approved") is False,
         "OFFICIAL_TEMPORAL_OR_MATH_FALSE_GO")
    need(r.get("original_owner_etf_250_srt_sha256")==SRC_SHA
         and r.get("p203_private_source_review_sha256")==
             prior.get("p203_private_source_semantic_json_sha256")
         and prior.get("source_cue_total")==250
         and prior.get("existing_unapproved_atom_total")==68
         and r.get("original_owner_68_atoms")==68,
         "P203_OWNER_SOURCE_AND_68_ATOM_PROVENANCE")
    need(r.get("real_owner_etf_source_replay_this_stage") is False
         and r.get("synthetic_adversarial_tests_only_for_issues_48_50") is True,
         "FALSE_NEW_PRIVATE_SOURCE_VALIDATION")
    need(r.get("independent_semantic_precision") is None
         and r.get("independent_semantic_recall") is None
         and r.get("independent_high_risk_false_negative_count") is None
         and r.get("factual_meaning_independent_gold") is False
         and r.get("source_speaker_meaning_approved") is False
         and r.get("issue48_whole_scope_research_complete") is False
         and r.get("issue50_current_p0_go") is False
         and r.get("real_etf_e3_v123_approvals")==0
         and r.get("real_etf_e4_owner_authorizations")==0
         and r.get("real_etf_e5_publications")==0,
         "FALSE_FINANCIAL_E2_E3_E4_E5_OR_ADVISORY_APPROVAL")
    need(r.get("public_private_subtitle_or_financial_statement_exposed") is False
         and r.get("no_main_or_protected_frozen_branch_modification") is True
         and r.get("signoff_scope")==
             "RED_GREEN_SOFTWARE_ADVERSARIAL_GATES_ONLY_RESEARCH_E2_ACCURACY_HOLD"
         and r.get("subsequent_after_closeout")=="P0-2-05"
         and r.get("remaining_blocked_after_closeout")==43,
         "NEXT_STEP_OR_PROTECTED_BASELINE_VIOLATED")
    return errors

def main():
    errors=verify()
    if errors:
        for err in errors:print("P204_GATE_FAIL",err)
        return 1
    print("P204_ISSUES_48_50_RED_GREEN_SHA_GATE_PASS red=3/3 reproduced "
          "crosscue=5 v2readonly=5 fullsource=NOT_THIS_STAGE "
          "independent_gold=UNMEASURABLE finance=HOLD")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
