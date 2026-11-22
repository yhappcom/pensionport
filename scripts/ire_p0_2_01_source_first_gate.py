#!/usr/bin/env python3
"""P0-2-01 source-first ETF250 cue dispositions; SHA-only OFFLINE audit.

Per-cue verbatim source/rationale is PRIVATE in the user's Library (not GitHub).
This verifies the public SHA/index classification contract, earlier original
source SHA and preserved semantic OPEN. CI cannot itself replay private bytes,
certify model interpretations as a blind gold set or approve E3/E4/E5.
"""
from __future__ import annotations

import argparse,hashlib,json,sys
from pathlib import Path
from scripts.ire_checklist_gate import CATALOG, STATE, validate as checklist_validate
from scripts.ire_current_status_gate import LEDGER, validate as status_validate

ROOT=Path(__file__).resolve().parent.parent
RECEIPT=Path("docs/IRE_P0_2_01_ETF250_SOURCE_FIRST_SHA_ONLY_20261123.json")
P102=Path("docs/IRE_P0_1_02_OWNER_ETF250_SOURCE_GRAPH_SHA_ONLY_20261122.json")
P103=Path("docs/IRE_P0_1_03_OWNER_ETF250_TYPED_OVERLAY_SHA_ONLY_20261122.json")
SOURCE="e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b"
GRAPH="4f4ab61ddfdc7c1d9d4d7ef7b07568911ab198629d9299284fbd05fa73db5a8f"
REVIEW="7c87f04af158196c6bff964c0634b029d81e23fc377825bcfc409f91fe354897"
PACKAGE="df54f80d153c4f07a80a261344282681c6fb8ddb7bb9bd6fbc9aa6b99ddce8c8"
VECTOR_SHA="d19a044fe17d5baba75ef7388dc948994c50396dd69c0a9c5adda23e3cca3336"
CUE_ROWS_SHA="5f049a34ede8ca5021060f314210698d0dfdbd2a7259ac23967b3d3b8c037fb7"
LABEL_CODES={"F":"FACT","O":"OPINION","Q":"QUESTION","N":"NO_ATOM","U":"OPEN"}
MAIN="d613fd201f4bb077f1ccc74d28dee937b11bfcb2"

def load(root,p):
    return json.loads((root/p).read_text(encoding="utf-8"))

def verify(root=ROOT,*,receipt=None,state=None,ledger=None,p102=None,p103=None):
    root=Path(root).resolve()
    receipt=receipt if receipt is not None else load(root,RECEIPT)
    state=state if state is not None else load(root,STATE)
    ledger=ledger if ledger is not None else load(root,LEDGER)
    p102=p102 if p102 is not None else load(root,P102)
    p103=p103 if p103 is not None else load(root,P103)
    out=[]
    def need(ok,code):
        if not ok:
            out.append("P201_"+code)
    need(not checklist_validate(load(root,CATALOG),state,root=root),
         "CHECKLIST_PREDECESSORS_AND_REPORT_INVALID")
    need(not status_validate(ledger,root=root),
         "CANONICAL_FINANCE_HOLD_MISMATCH")
    items=state.get("items",[])
    need(len(items)==60 and all(t.get("status")=="PASS" for t in items[:13])
         and items[12].get("id")=="P0-2-01"
         and items[13].get("id")=="P0-2-02"
         and items[13].get("status")=="READY"
         and all(t.get("status")=="BLOCKED" for t in items[14:]),
         "ONLY_P202_NEXT_AND_PREVIOUS_PASS")
    dev=ledger.get("development_gate",{})
    need(dev.get("this_item")=="P0-2-02" and
         dev.get("pending_next_item")=="P0-2-02",
         "LEDGER_NEXT_P202_ONLY")
    need(state.get("protected_main_sha")==MAIN and
         receipt.get("schema")=="IRE_P201_PUBLIC_SHA_ONLY_SOURCE_FIRST_CUE_DISPOSITIONS_V1"
         and receipt.get("id")=="P0-2-01"
         and receipt.get("video_id")=="LVE7XN_esTc",
         "RECEIPT_ID_OR_PROTECTED_MAIN_DRIFT")
    need(receipt.get("original_srt_sha256")==SOURCE and
         receipt.get("original_zip_sha256")=="9f5a281191502bb30cb78ff17d2b08f6887f55b836cee67e00d7309770efa397"
         and receipt.get("original_unapproved_native_sha256")=="c8bec3354702cad0e85d4b111d2627ae2978806f3a4111c94a689d3b9e25baeb"
         and receipt.get("previous_P102_graph_sha256")==GRAPH and
         p102.get("source_srt_sha256")==SOURCE
         and p102.get("source_graph_canonical_sha256")==GRAPH
         and p102.get("cue_count")==250
         and p102.get("source_cue_missing_or_duplicated_count")==0
         and p103.get("source_srt_sha256")==SOURCE
         and p103.get("v244_owner_source_graph_sha256")==GRAPH,
         "ORIGINAL_SOURCE_AND_GRAPH_PINS")
    need(receipt.get("private_source_first_review_canonical_sha256")==REVIEW
         and receipt.get("private_review_package_sha256")==PACKAGE
         and receipt.get("private_source_first_review_file_sha256")=="94491c008bd409d4fef7d036083bb90e8b5bca6baab7141bf13114c0ca4c1525"
         and receipt.get("private_later_native_comparison_file_sha256")=="0d87e591ffee0b8ff00ba495397e07fcaa2460b9528b996701e88098cdc4aeb9"
         and receipt.get("source_quote_rationale_rows_public_sha_only_census_sha256")==CUE_ROWS_SHA
         and receipt.get("private_library_file_id")=="libfile_e1711ec217008191bd183252ee58aab5"
         and receipt.get("private_library_uploaded_successfully") is True
         and receipt.get("full_private_review_contains_cue_quotes_and_250_separate_rationales") is True,
         "PRIVATE_EVIDENCE_SHA_AND_LIBRARY_CUSTODY")
    need(receipt.get("actual_private_original_srt_byte_replay_performed_in_current_P201") is True
         and receipt.get("actual_private_original_srt_replay_not_possible_in_public_CI") is True
         and receipt.get("source_first_manual_evaluation_before_old_candidate_comparison") is True
         and receipt.get("previous_V227_V228_native_categories_not_used_as_gold") is True,
         "SOURCE_FIRST_NOT_OLD_LABEL_REMAP")
    vector=receipt.get("disposition_vector")
    if type(vector) is not str:vector=""
    counts={name:vector.count(code) for code,name in LABEL_CODES.items()}
    need(len(vector)==250 and set(vector)==set(LABEL_CODES)
         and hashlib.sha256(vector.encode("ascii")).hexdigest()==VECTOR_SHA
         and receipt.get("disposition_vector_sha256")==VECTOR_SHA
         and counts=={"FACT":92,"OPINION":61,"QUESTION":3,"NO_ATOM":27,"OPEN":67}
         and receipt.get("cue_label_counts")==counts,
         "LABEL_VECTOR_CENSUS_OR_ORDER")
    need(receipt.get("cue_count")==250
         and receipt.get("unresolved_risk_cue_count")==67
         and all(receipt.get(k)==0 for k in (
             "source_cue_quote_mismatch_count","source_cue_missing_count",
             "source_cue_duplicate_count","source_context_quote_mismatch_count",
             "original_cue_timestamp_mismatch_count")),
         "SOURCE_CUE250_EXACT_REPLAY_COUNTS")
    issues=receipt.get("unresolved_issue_groups",[])
    need(type(issues) is list and len(issues)==12
         and [x.get("id") for x in issues if type(x) is dict]==[
             "P201-R%02d"%i for i in range(1,13)]
         and all(type(x) is dict and
                 x.get("status")=="OPEN_FOR_NEXT_MEANING_ADJUDICATION"
                 and type(x.get("cue_indices")) is list and
                 len(x["cue_indices"])>0 and
                 len(x["cue_indices"])==len(set(x["cue_indices"]))
                 and all(type(i) is int and 1<=i<=250 for i in x["cue_indices"])
                 for x in issues)
         and receipt.get("source_only_risk_groups_count")==12
         and receipt.get("index_etf_only_scope_cues")==[45,46,47]
         and receipt.get("inherited_index_scope_comparative_cue_count")==123,
         "12_RISK_GROUPS_AND_INDEX_CONDITIONS")
    # Every OPEN cue must be linked to at least one typed unresolved issue;
    # a cue-specific rationale with no escalation docket is an incomplete gate.
    issue_cues={i for x in issues if isinstance(x,dict)
                for i in x.get("cue_indices",[]) if type(i) is int}
    need(all(i in issue_cues for i,c in enumerate(vector,1) if c=="U"),
         "OPEN_CUE_WITHOUT_ESCALATION_DOCKET")
    need(receipt.get("previous_unapproved_native_candidate_atoms")==68
         and receipt.get("previous_unapproved_native_primary_anchor_cues")==72
         and receipt.get("previous_native_primary_anchor_cues_now_OPEN_source_first")==32
         and receipt.get("previous_unanchored_non_OPEN_fact_cues_not_certified_atom_omissions")==68
         and receipt.get("previous_unanchored_non_OPEN_opinion_cues_not_certified_atom_omissions")==46
         and receipt.get("cross_scope_native_parent_atoms_preserved_unapproved")==21
         and receipt.get("cross_scope_native_source_edges_preserved_unapproved")==49,
         "OLD_68_ATOMS_AND_21_CROSS_NOT_RESOLVED")
    need(receipt.get("not_an_independent_gold_label_set") is True
         and receipt.get("speaker_fact_assertion_not_finance_truth") is True
         and receipt.get("no_atom_does_not_certify_absence_of_all_hidden_claims") is True
         and receipt.get("audio_source_confirmed") is False
         and receipt.get("video_frame_source_confirmed") is False
         and receipt.get("formal_e2_precision") is None
         and receipt.get("formal_e2_recall") is None
         and receipt.get("high_risk_FN_certified") is None
         and receipt.get("e2_final_approved") is False,
         "FALSE_GOLD_NOATOM_OR_AUDIO_SCREEN")
    need(receipt.get("actual_etf_e3_final_approved_children")==0
         and receipt.get("actual_etf_e4_owner_authorized_children")==0
         and receipt.get("actual_etf_e5_parent_publications")==0
         and receipt.get("personal_investment_advice_approved") is False
         and all(ledger.get("stages",{}).get(k,{}).get("official_stage_release")=="HOLD"
                 for k in ("E1","E2","E3","E4","E5")),
         "ETF_E3_E4_E5_FALSE_GO")
    need(receipt.get("public_artifact_contains_original_caption_text") is False
         and receipt.get("public_artifact_contains_cue_rationales") is False
         and receipt.get("next_allowed_item")=="P0-2-02"
         and receipt.get("following_blocked")==46,
         "PUBLIC_PRIVACY_OR_NEXT_TASK_DRIFT")
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("command",nargs="?",choices=["verify"],default="verify")
    p.add_argument("--root",type=Path,default=ROOT)
    a=p.parse_args()
    try:failures=verify(a.root)
    except (OSError,KeyError,ValueError,TypeError,IndexError) as e:
        print("P201_SOURCE_FIRST_ERROR",type(e).__name__,file=sys.stderr)
        return 1
    for code in failures:print("P201_SOURCE_FIRST_ERROR",code,file=sys.stderr)
    if failures:return 1
    print("P201_SOURCE_FIRST_GATE_PASS 250/250 FACT=92 OPINION=61 QUESTION=3 "
          "NO_ATOM=27 OPEN=67 E3=0/13 E4=0 E5=0 NEXT=P0-2-02")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
