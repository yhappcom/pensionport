#!/usr/bin/env python3
"""P203 ETF source-meaning six-axis SHA-only gate (not source bytes / gold in public CI)."""
from __future__ import annotations
import json,sys
from pathlib import Path
from scripts.ire_checklist_gate import CATALOG,STATE,validate as checklist_validate
from scripts.ire_current_status_gate import LEDGER,validate as status_validate
ROOT=Path(__file__).resolve().parent.parent
P203=Path("docs/IRE_P0_2_03_ETF250_SIX_AXIS_SHA_ONLY_20261123.json")
P201=Path("docs/IRE_P0_2_01_ETF250_SOURCE_FIRST_SHA_ONLY_20261123.json")
P202=Path("docs/IRE_P0_2_02_ETF250_ATOM_CROSS_ADJUDICATION_SHA_ONLY_20261123.json")
P103=Path("docs/IRE_P0_1_03_OWNER_ETF250_TYPED_OVERLAY_SHA_ONLY_20261122.json")
SOURCE="e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b"
NATIVE="c8bec3354702cad0e85d4b111d2627ae2978806f3a4111c94a689d3b9e25baeb"
PRIVATE="1015721b1f95eb30a666c8fea5b901ec246afdbd188e77ca6fb9c42ff0f331a0"
PACKAGE="a5176f0978f646eb061daa4ecd7645190eec7c56dcded4fc0d01f42097ca3bd7"
ORDER=["P203-F%02d"%i for i in range(1,11)]
def load(root,p):return json.loads((Path(root)/p).read_text(encoding="utf8"))
def verify(root=ROOT,*,receipt=None,state=None,ledger=None,p201=None,p202=None,p103=None):
 root=Path(root)
 r=receipt if receipt is not None else load(root,P203)
 s=state if state is not None else load(root,STATE)
 l=ledger if ledger is not None else load(root,LEDGER)
 p201=p201 if p201 is not None else load(root,P201)
 p202=p202 if p202 is not None else load(root,P202)
 p103=p103 if p103 is not None else load(root,P103)
 bad=[]
 def need(v,name):
  if not v:bad.append("P203_"+name)
 need(not checklist_validate(load(root,CATALOG),s,root=root),"CHECKLIST_INVALID")
 need(not status_validate(l,root=root),"FINANCE_STATUS_LEDGER_INVALID")
 items=s.get("items",[])
 idx=next((i for i,t in enumerate(items) if t.get("status")!="PASS"),len(items))
 current=items[idx]["id"] if idx<len(items) else "ALL_COMPLETE"
 need(len(items)==60 and all(t.get("status")=="PASS" for t in items[:14])
      and items[14].get("id")=="P0-2-03" and items[14].get("status") in
      {"READY","IN_PROGRESS","HOLD","FAIL","PASS"}
      and items[15].get("id")=="P0-2-04",
      "PRIOR_FOURTEEN_PASS_SAME_ITEM_ONLY")
 need(l.get("development_gate",{}).get("this_item")==current and
      l.get("development_gate",{}).get("pending_next_item")==current,"LEDGER_LIVE_CURSOR_DRIFT")
 need(r.get("schema")=="IRE_P0_2_03_PUBLIC_SHA_ONLY_SPEAKER_NEGATION_CONTEXT_DUPLICATE_V1"
      and r.get("item_id")=="P0-2-03" and r.get("original_video_id")=="LVE7XN_esTc"
      and r.get("as_of")=="2026-11-23","SCHEMA_SCOPE")
 for k,h in (("original_source_srt_sha256",SOURCE),
             ("original_native_json_sha256",NATIVE),
             ("p203_private_source_semantic_json_sha256",PRIVATE),
             ("p203_private_package_sha256",PACKAGE),
             ("p201_private_review_zip_sha256","df54f80d153c4f07a80a261344282681c6fb8ddb7bb9bd6fbc9aa6b99ddce8c8"),
             ("p202_private_review_zip_sha256","58106bff2c5fe91c36a676cba2325b09ebf9710058dec1f52824358e1991a040")):
  need(r.get(k)==h,"SOURCE_HASH_"+k)
 need(r.get("owner_private_upload_confirmed") is True and
      r.get("private_library_file_id")=="libfile_ba21347a83b48191be7bc70c2869aeff" and
      r.get("private_real_source_regression_tests_pass")==20,"PRIVATE_OWNER_CUSTODY_OR_TESTS")
 need(r.get("source_cue_total")==250 and
      r.get("source_quote_mismatch_count")==0 and r.get("source_neighbor_context_hash_mismatch_count")==0
      and r.get("existing_unapproved_atom_total")==68
      and r.get("original_primary_source_refs_total")==73
      and r.get("unique_primary_source_cue_count")==72,"250_CUE_68_ATOM_73_REF_CENSUS")
 c=r.get("cue_coverage",{})
 need(c=={"original_primary":72,"original_context":157,
          "educational_discourse_with_explicit_reason":7,
          "unlinked_provisional_no_finance_absence_proof":14}
      and sum(c.values())==250,"CUE_COVERAGE_NOT_COMPLETE")
 need(r.get("original_cue_primary_labels")=={"FACT":92,"OPINION":61,"QUESTION":3,"NO_ATOM":27,"OPEN":67}
      and p201.get("cue_label_counts")==r.get("original_cue_primary_labels")
      and p201.get("original_srt_sha256")==SOURCE,"P201_SOURCE_FIRST_LABEL_DRIFT")
 need(r.get("source_first_fact_opinion_without_primary_refs_total")==114 and
      r.get("linked_to_original_context_from_114")==107 and
      r.get("source_only_didactic_from_114")==7
      and r.get("individually_adjudicated_didactic_cues")==[5,6,9,10,11,13,14],"HIDDEN_OMISSION_UNREVIEWED")
 need(r.get("speaker_voice_audio_authenticated") is False
      and r.get("speaker_attribution")=="NARRATOR_PRESENTED_TEXT_ONLY_AUDIO_UNVERIFIED"
      and r.get("rhetorical_questions")==[16,53,236]
      and r.get("explicit_negation_and_caveat_anchor_cues")==
          [28,40,41,64,65,94,95,118,123,202,239,240,241,242,243]
      and r.get("source_based_rebuttal_relations_reviewed")==6,
      "SPEAKER_NEGATION_REBUTTAL_MISATTRIBUTION")
 need(r.get("high_risk_semantic_pair_reviews")==23
      and r.get("exact_duplicate_merges_authorized")==0
      and r.get("priority_meaning_correction_actions")==10
      and r.get("correction_action_ids")==ORDER,"DEDUP_RISK_MERGE_OR_REMEDIATION_GAP")
 case=r.get("hypothetical_premium_case",{})
 need(case.get("nav_cue")==218 and case.get("market_price_cue")==220
      and case.get("difference_cue")==221 and case.get("nav_krw")==17728
      and case.get("market_krw")==17645 and case.get("market_minus_nav_krw")==-83
      and case.get("nav_based_premium_percent")==-0.468186
      and case.get("screen_actual_data_verified") is False,"FICTIONAL_NAV_KRW_PERCENT_OR_SCREEN_REALISM")
 tr=r.get("hypothetical_tracking_example",{})
 need(tr.get("index_return_percent")==20 and tr.get("etf_return_percent")==18
      and tr.get("period")=="ONE_YEAR_HYPOTHETICAL"
      and tr.get("difference_percentage_points")==2
      and tr.get("statistical_tracking_error_from_two_returns_certified") is False,
      "TRACKING_DIFFERENCE_NOT_ERROR")
 need(r.get("index_etf_global_scope_condition_cues")==[45,46,47]
      and r.get("b0013_c00057_own_condition_cues")==[45,46,47,244,245]
      and p103.get("b0013_c00057",{}).get("all_condition_indices")==[45,46,47,244,245],
      "INHERITED_INDEX_SCOPE_LOST")
 need(r.get("cross_scope_atom_count")==21 and r.get("cross_scope_edge_count")==49
      and r.get("foreign_reference_role_counts")=={"context":49,"condition":29,"numeric":3,"exception":0}
      and p202.get("cross_foreign_source_edges_total")==49,"21_ATOM_49_EDGE_HERITAGE")
 need(r.get("source_first_68_statuses_preserved")=={"KEEP":32,"REATOMIZE":17,"QUARANTINE":4,"OPEN":15}
      and r.get("unresolved_and_repair_blocked_original_atoms")==36
      and r.get("original_atoms_silently_mutated_or_deleted")==0,
      "36_UNREPAIRED_ATOM_FALSE_KEEP")
 need(r.get("no_audio_or_visual_verified") is True
      and r.get("independend_gold_or_recall_certified") is False
      and r.get("independent_precision") is None and r.get("independent_recall") is None
      and r.get("independent_high_risk_false_negatives") is None
      and r.get("e2_overall_semantic_accuracy_approved") is False
      and r.get("e3_v123_approved_children")==0 and r.get("e4_authorized_children")==0
      and r.get("e5_parent_publications")==0
      and r.get("real_personal_investment_advice_approved") is False,
      "FALSE_FINANCE_APPROVAL_OR_GOLD")
 need(r.get("public_original_source_text_included") is False
      and r.get("public_private_reason_text_included") is False
      and r.get("next_task_after_checklist_pass")=="P0-2-04"
      and r.get("blocked_after_next")==44,"PUBLIC_EXPOSURE_OR_WRONG_SUCCESSOR")
 return bad
def main():
 failures=verify()
 for f in failures:print("P203_GATE_FAIL",f,file=sys.stderr)
 if failures:return 1
 print("P203_SIX_AXIS_SHA_GATE_PASS cues=250 primary=72 context=157 didactic=7 unsettled_nonfinancial=14 atoms=68 nonprimary=114 pairs=23 rebuttals=6 unresolved=36 finance=HOLD")
 return 0
if __name__=="__main__":raise SystemExit(main())
