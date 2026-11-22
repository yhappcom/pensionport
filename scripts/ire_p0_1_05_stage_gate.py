#!/usr/bin/env python3
"""P0-1-05 E1 software stage closeout; NEVER certify owner ETF E2-E5.

This checks the existing four immutable E1 receipts against the canonical
status and current strict checklist. It is deliberately OFFLINE. Passing
source counts and real SQLite synthetic tests cannot establish live ETF
semantic accuracy, two-user-turn provenance, legal sources or E5 release.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

from scripts.ire_checklist_gate import CATALOG, STATE, validate as checklist_validate
from scripts.ire_current_status_gate import LEDGER, validate as status_validate

ROOT=pathlib.Path(__file__).resolve().parent.parent
RECEIPT=pathlib.Path("docs/IRE_P0_1_05_FINAL_E1_STRUCTURE_ONLY_CLOSEOUT_20261123.json")
P101=pathlib.Path("docs/IRE_P0_1_01_ROUTE_CLOSEOUT_RECEIPT_20261122.json")
P102=pathlib.Path("docs/IRE_P0_1_02_OWNER_ETF250_SOURCE_GRAPH_SHA_ONLY_20261122.json")
P103=pathlib.Path("docs/IRE_P0_1_03_OWNER_ETF250_TYPED_OVERLAY_SHA_ONLY_20261122.json")
P104=pathlib.Path("docs/IRE_P0_1_04_REAL_SQLITE_END_TO_END_CLOSEOUT_20261123.json")
REVIEW=pathlib.Path("docs/IRE_P0_1_05_E1_STRUCTURE_FINAL_ASSESSMENT_20261123.md")
MAIN="d613fd201f4bb077f1ccc74d28dee937b11bfcb2"
ROUTE="validation/ire-v6-frozen/v243_canonical_e1_e5_route.py::run_canonical_research_route"
SOURCE="e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b"
GRAPH="4f4ab61ddfdc7c1d9d4d7ef7b07568911ab198629d9299284fbd05fa73db5a8f"
TYPED="9d4b32d0850cf6f188b9bd77fd0cfc72d009c540422a9a2ae6b58b4dbdbd1662"
HEX=re.compile(r"[0-9a-f]{40}\Z")


def load(root,path):
    return json.loads((root/path).read_text(encoding="utf-8"))


def verify(root=ROOT,*,receipt=None,state=None,ledger=None,inputs=None):
    root=pathlib.Path(root).resolve()
    receipt=receipt if receipt is not None else load(root,RECEIPT)
    state=state if state is not None else load(root,STATE)
    ledger=ledger if ledger is not None else load(root,LEDGER)
    inputs=inputs if inputs is not None else {
        "p101":load(root,P101),"p102":load(root,P102),
        "p103":load(root,P103),"p104":load(root,P104)}
    p1,p2,p3,p4=(inputs[n] for n in ("p101","p102","p103","p104"))
    errs=[]
    def need(ok,code):
        if not ok:
            errs.append("P105_"+code)
    catalog=load(root,CATALOG)
    need(not checklist_validate(catalog,state,root=root),
         "STRICT_PREDECESSOR_SEQUENCE_OR_REPORT_INVALID")
    need(not status_validate(ledger,root=root),
         "CURRENT_STATUS_LEDGER_FAIL_CLOSED")
    tasks=state.get("items",[])
    # Preserve immutable P105 E1 CLOSEOUT and its original E2 first item,
    # without freezing the *current* 60-item cursor at the historical P201
    # READY position. Every later P201/P202 PASS must remain contiguous.
    first_open=next((i for i,v in enumerate(tasks)
                     if v.get("status")!="PASS"),len(tasks))
    need(len(tasks)==60 and [t.get("id") for t in tasks[7:12]]==
         [f"P0-1-{i:02d}" for i in range(1,6)] and
         all(t.get("status")=="PASS" for t in tasks[:12]) and
         tasks[12].get("id")=="P0-2-01" and first_open>=12 and
         (first_open==len(tasks) or
          (tasks[first_open].get("status") in
           {"READY","IN_PROGRESS","HOLD","FAIL"} and
           all(x.get("status")=="BLOCKED" for x in tasks[first_open+1:]))),
         "E1_FIVE_PASS_E2_ONLY_NEXT")
    current_cursor=tasks[first_open]["id"] if first_open<len(tasks) else None
    need(ledger.get("development_gate",{}).get("this_item")==current_cursor and
         ledger.get("development_gate",{}).get("pending_next_item")==current_cursor,
         "E2_CURSOR_NOT_FIRST_ITEM")
    need(state.get("protected_main_sha")==MAIN and
         catalog.get("protected_main_sha")==MAIN and
         state.get("target_branch")=="audit/full-repository-snapshot-20261122",
         "MAIN_OR_BRANCH_MOVED")
    need(receipt.get("schema")=="IRE_P0_1_05_E1_SOFTWARE_STRUCTURE_NOT_REAL_ETF_APPROVAL_V1"
         and receipt.get("item_id")=="P0-1-05" and
         receipt.get("verdict")=="PASS_E1_SOFTWARE_ONLY_ETF_E1_E5_ACTUAL_HOLD",
         "SCOPE_NOT_EXPLICIT")
    need(receipt.get("evidence_source_sha256")==SOURCE and
         receipt.get("source_graph_sha256")==GRAPH and
         receipt.get("typed_review_overlay_sha256")==TYPED,
         "RECEIPT_SOURCE_GRAPH_TYPED_PIN_CHANGED")
    need(receipt.get("software_route")==ROUTE and
         receipt.get("official_supported_api_count")==1 and
         receipt.get("core_exported_cli_count")==0,
         "ROUTE_COUNT_NOT_SINGLE")
    ci=receipt.get("last_precloseout_ci",{})
    need(ci.get("head_sha")=="bd8694618f04f41802c620aa216a29da603bc145"
         and ci.get("run_id")==45067537678 and
         ci.get("conclusion")=="success" and ci.get("successful_jobs")==6
         and ci.get("total_jobs")==6,
         "UNVERIFIED_BASELINE_CI")
    need(receipt.get("post_commit_ci_necessary") is True and
         receipt.get("post_commit_ci_auto_self_certified") is False,
         "CLOSEOUT_CI_SELF_ATTESTATION")
    need(receipt.get("stage_result")==
         {"E1_structural_software":"PASS",
          "ETF_real_owner_E1_end_to_end":"HOLD",
          "E2_semantic":"HOLD","E3_final_chat":"HOLD",
          "E4_owner_authority":"HOLD","E5_knowledge":"HOLD",
          "personalized_investment_advice":"HOLD"},
         "E1_STRUCTURE_FALSE_FULL_RELEASE")

    need(p1.get("official_api")==ROUTE and
         p1.get("official_supported_routes")==1 and
         p1.get("core_module_cli_surface_paths")==0 and
         p1.get("manual_turns_not_platform_authenticated") is True and
         p1.get("actual_etf_formal_e3_child_approvals")==0 and
         p1.get("actual_etf_e5_parent_publications")==0,
         "P101_SINGLE_API_OR_TURN_PROVENANCE")
    need(p2.get("source_srt_sha256")==SOURCE and
         p2.get("source_graph_canonical_sha256")==GRAPH and
         (p2.get("cue_count"),p2.get("child_count"),p2.get("atom_count_unapproved"),
          p2.get("cross_child_parent_atom_count"),p2.get("cross_child_typed_cue_edges"))==
         (250,13,68,21,49) and
         p2.get("source_cue_missing_or_duplicated_count")==0 and
         p2.get("actual_etf_e3_approved_child_count")==0 and
         p2.get("actual_e5_parent_publications")==0,
         "P102_REAL_SOURCE_ONLY_NOT_SEMANTICS")
    p3b=p3.get("b0013_c00057",{})
    need(p3.get("source_srt_sha256")==SOURCE and
         p3.get("v244_owner_source_graph_sha256")==GRAPH and
         p3.get("v245_full_private_typed_parent_review_overlay_sha256")==TYPED
         and p3.get("actual_source_cue_count")==250 and
         p3.get("actual_child_scope_count")==13 and
         p3.get("actual_complete_unapproved_parent_atom_count")==68 and
         p3.get("actual_cross_child_atom_count")==21 and
         p3.get("actual_external_cue_edge_count")==49 and
         p3b.get("foreign_inherited_condition_source_cues")==[45,46,47] and
         p3b.get("primary_source_cue_index")==246 and
         p3b.get("stance_unapproved")=="UNRESOLVED" and
         p3.get("formal_etf_e3_approved_children")==0 and
         p3.get("formal_etf_e5_parent_publications")==0,
         "P103_CROSS_CONDITIONS_NOT_FULLY_RETAINED")
    t=p4.get("test_evidence",{})
    f=p4.get("failure_zero_partial",{})
    o=p4.get("post_commit_pre_e4_seal_crash",{})
    need(p4.get("verdict")=="PASS_E1_SQLITE_SOFTWARE_ONLY_NOT_FINANCIAL_APPROVAL"
         and t.get("new_v246_total")==19 and t.get("new_v246_passed")==19
         and t.get("full_frozen_v200_v246_cohort")==910
         and t.get("full_frozen_cohort_passed")==910 and
         p4.get("code_ci",{}).get("conclusion")=="success" and
         p4.get("code_ci",{}).get("jobs_passed")==6,
         "P104_SQLITE_POSITIVE_NEGATIVE_FAILURE")
    must_zero=("missing_second_turn","missing_secondary_child_official_evidence",
               "source_byte_tamper","wrong_official_domain","v123_chat_open_or_reject",
               "failure_inside_sqlite_begin_immediate")
    need(all(f.get(k)=={"events":0,"knowledge":0,"parent_publications":0}
             for k in must_zero) and
         p4.get("idempotent_replay_with_prior_externally_retained_owner_pin",{}).get(
             "additional_parent_publications")==0 and
         p4.get("idempotent_replay_with_prior_externally_retained_owner_pin",{}).get(
             "additional_knowledge_rows")==0,
         "P104_PARTIAL_WRITE_OR_REPLAY")
    need(o.get("physical_orphan_full_parent_rows")==1 and
         o.get("orphan_formally_certified") is False and
         o.get("manual_recovery_implemented") is True and
         o.get("automatic_physical_rollback_guaranteed") is False and
         o.get("active_database_after_explicit_recovery")=={
             "knowledge_rows":0,"events":0,"parent_proofs":0} and
         o.get("archived_original_full_parent_preserved") is True and
         p4.get("operational_constraints",{}).get(
             "owner_external_pin_custody_not_self_certified") is True,
         "UNSEALED_CRASH_RISK_LAUNDERED_AS_AUTOMATIC_RECOVERY")

    cohort=ledger.get("reference_cohort",{})
    need(cohort.get("video_id")=="LVE7XN_esTc" and
         cohort.get("original_source_sha256")==SOURCE and
         cohort.get("actual_formal_v123_child_approvals")==0 and
         cohort.get("actual_e4_authorized_child_count")==0 and
         cohort.get("actual_e5_publications")==0 and
         cohort.get("actual_e5_knowledge_rows")==0 and
         cohort.get("actual_user_etf_turn2_final_verdict_proven") is False and
         cohort.get("complete_independent_gold_available") is False,
         "ETF_ACTUAL_APPROVAL_PREMATURE")
    stages=ledger.get("stages",{})
    need(set(stages)=={"E1","E2","E3","E4","E5"} and
         all(stages[k].get("official_stage_release")=="HOLD"
             for k in ("E1","E2","E3","E4","E5")) and
         stages["E1"].get("synthetic_software_route",{}).get("status")=="PASS"
         and stages["E1"].get("end_to_end_real_owner_approval_route",{}).get(
             "status")=="HOLD",
         "STAGE_SOFTWARE_AND_REAL_RELEASE_CONFLATED")
    need(ledger.get("advisory",{}).get("official_release")=="HOLD" and
         ledger.get("advisory",{}).get("personalized_recommendation_authorized") is False
         and receipt.get("actual_etf_approvals")=={
             "E3_v123_children":0,"E4_authorized_children":0,
             "E5_parent_publications":0,"E5_knowledge_rows":0},
         "FALSE_INVESTMENT_ADVICE_OR_E5_PUBLICATION")
    need(receipt.get("next_ready_item")=="P0-2-01" and
         receipt.get("blocked_following")==47 and
         receipt.get("passed_items")==12 and
         receipt.get("main_sha_unchanged")==MAIN and
         receipt.get("remaining_open_cross_atoms_for_semantic_review")==21 and
         receipt.get("remaining_cross_qualifier_edges")==49 and
         receipt.get("actual_etf_semantic_gold_verified") is False,
         "NEXT_E2_ENTRY_OR_HOLD_SCOPE_MISSTATED")
    need((root/REVIEW).is_file(),"FINAL_OWNER_REPORT_MISSING")
    return errs


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",nargs="?",choices=["verify"],default="verify")
    parser.add_argument("--root",type=pathlib.Path,default=ROOT)
    args=parser.parse_args()
    try:
        errors=verify(args.root)
    except (KeyError,TypeError,ValueError,OSError,IndexError) as e:
        print("P105_GATE_FAIL",type(e).__name__,file=sys.stderr)
        return 1
    for e in errors:
        print("P105_GATE_FAIL",e,file=sys.stderr)
    if errors:
        return 1
    state=load(args.root,STATE)
    rows=state["items"]
    current=next((x["id"] for x in rows if x["status"]!="PASS"),"ALL_DONE")
    blocked=sum(x["status"]=="BLOCKED" for x in rows)
    print("P105_STAGE_GATE_PASS E1_SOFTWARE_ONLY=PASS ETF_E1_E5=HOLD "
          f"ETF_E3=0/13 ETF_E4=0 ETF_E5=0 "
          f"E1_STAGE_INITIAL_NEXT=P0-2-01 CURRENT_NEXT={current} "
          f"CURRENT_BLOCKED={blocked}")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
