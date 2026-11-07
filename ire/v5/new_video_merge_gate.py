"""Fail-closed reconciliation of an unseen original video into accumulated V5 knowledge.

The source video can challenge prior policy context without approving its old
tax proposal. Three fresh 2026 rules are kept as *separate pending topics*;
the existing 13 educational knowledge IDs and all legacy claims are unchanged.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

STUDY=Path("ire/v5/new_video_studies/C7KctGzg-K0_20261105.json")
OVERLAY=Path("ire/v5/advisory_knowledge/new_video_C7KctGzg-K0_incremental_20261105.json")
GRAPH=Path("ire/v5/advisory_knowledge/integrated_education13_20261104.json")
LEGACY=Path("ire/v5/advisory_knowledge/provisional_integrated_20_plus_5_20261104.json")

class IncrementalMergeError(ValueError):
    pass

def check(condition,code):
    if not condition:raise IncrementalMergeError(code)

def load(p):
    return json.loads(Path(p).read_text("utf-8"))

def verify(root:Path, overlay:dict|None=None):
    root=Path(root)
    src=load(root/STUDY)
    g=load(root/GRAPH)
    prior=load(root/LEGACY)
    o=overlay if overlay is not None else load(root/OVERLAY)
    check(o.get("schema")=="IRE_V5_NEW_VIDEO_INCREMENTAL_KNOWLEDGE_OVERLAY_V1"
          and o.get("created")=="2026-11-05"
          and o.get("video_id")==src["video"]["video_id"]
          and o.get("new_video_claims")==13
          and o.get("previous_13_education_nodes")==g["total_education_topics"]==13,
          "MERGE_OVERLAY_SCHEMA_OR_PREVIOUS_GRAPH_CHANGED")
    check(o.get("existing_education_graph_unchanged") is True
          and o.get("existing_core_20_claims_unchanged") is True
          and o.get("new_approved_education_topics")==0
          and o.get("current_access_to_personal_financial_advice") is False
          and o.get("independent_human_reviewer_completed") is False
          and o.get("proposed_new_topics_status")=="NO_AUTOMATIC_PROMOTION_UNTIL_INDEPENDENT_REVIEW",
          "MERGE_FALSE_ADVICE_OR_APPROVAL")
    indexed={x["claim_id"]:x for x in src["research_claims"]}
    rows=o.get("normalized_existing_context_links",[])
    check(len(rows)==13 and len({x["claim_id"] for x in rows})==13,
          "MERGE_UNSEEN_CLAIM_MISSING")
    g_ids={n["knowledge_id"] for n in g["nodes"]}
    core_ids={n["claim_id"] for n in prior["nodes"]}
    authors={x["id"] for x in src["authoritative_sources"]}
    combined=0
    for row in rows:
        cid=row["claim_id"]
        check(cid in indexed,"MERGE_INVENTED_CLAIM_ID")
        claim=indexed[cid]
        check(row["disposition"]==claim["disposition"]
              and row["video_id"]==claim["video_id"]
              and row["original_cue_range"]==[claim["cue_start"],claim["cue_end"]]
              and row["source_cue_span_sha256"]==claim["source_cue_span_sha256"]
              and row["existing_context"]==claim["existing_core_claim_ids"]
              and row["existing_knowledge_relation"]==claim["reconciliation_link"]
              and row["candidate_concept_id"]==claim["new_provisional_concept_id"]
              and row["source_refs"]==claim["authority_ids"],
              "MERGE_SOURCE_CUE_OR_TEMPORAL_QUALIFICATION_CHANGED")
        check(set(row["existing_context"])<=core_ids
              and set(row["source_refs"])<=authors
              and row.get("permissible_investment_advice") is False
              and row.get("current_2026_law_replacement_requires_official_sources") is True,
              "MERGE_FAKE_SOURCE_OR_PERSONAL_ADVICE")
        if row["existing_knowledge_relation"] is not None:
            x=row["existing_knowledge_relation"]
            check(x["target_id"] in g_ids|core_ids,
                  "MERGE_UNKNOWN_CORE_OR_EDUCATION_ID")
            combined+=1
    check(combined==src["reconciled_against_prior"]["existing_relation_count"]==5,
          "MERGE_LEGACY_EDGES_NOT_REPRODUCED")
    pending=o.get("new_provisional_topics",[])
    pending_ids={x["knowledge_id"] for x in pending}
    base_ids=set(src["reconciled_against_prior"]["new_provisional_concept_ids"])
    check(len(pending)==o.get("proposed_new_topics")==3
          and len(pending_ids)==3 and pending_ids==base_ids
          and not pending_ids&g_ids,
          "MERGE_NEW_CONCEPTS_NOT_DEDUPLICATED")
    for item in pending:
        original=indexed[item["source_claim_id"]]
        check(original["new_provisional_concept_id"]==item["knowledge_id"]
              and item.get("status","").startswith("PROVISIONAL_UNAPPROVED_")
              and item.get("approved_education") is False
              and item.get("financial_fact_independently_certified") is False
              and item.get("personal_advice_approved") is False
              and len(item.get("current_scope",""))>=80
              and len(item.get("risk",""))>=35
              and len(set(item.get("source_current",[])))>=2
              and set(item["source_current"])<=authors
              and item.get("video_role") in {
                "COUNTEREXAMPLE_2025_DRAFT_NOT_CURRENT",
                "HISTORICAL_POLICY_PROPOSAL_CONFIRMED_WITH_MARKET_EXCEPTIONS",
                "ABORTED_DRAFT_VIDEO_BEFORE_REVERSAL",
              },"MERGE_UNSUPPORTED_NEW_TAX_FACT_ESCALATED")
        # A 2025 proposal alone cannot serve as current 2026 law.
        check("M25" not in item["source_current"],
              "MERGE_2025_DRAFT_FALSELY_CURRENT")
    require_rules=o.get("reconciliation_rules",{})
    check("Never replace" in require_rules.get("knowledge_id_stability","")
          and "DRAFT_REVERSED" in require_rules.get("historical_date_protection","")
          and "counterexample" in require_rules.get("source_provenance",""),
          "MERGE_HISTORICAL_WARNING_REMOVED")
    return {
        "schema":"IRE_V5_NEW_VIDEO_INCREMENTAL_MERGE_GATE_V1",
        "video_id":src["video"]["video_id"],
        "prior_education_topics_unchanged":13,
        "original_video_claims_reconciled":len(rows),
        "existing_core_or_education_links":combined,
        "new_scoped_tax_topics_held_as_provisional":len(pending),
        "new_approved_tax_topics":0,
        "personal_investment_advice_enabled":False,
        "formal_independent_blind_approval":False,
        "merge_status":"PROVENANCE_LINKED_PREVIOUS_KNOWLEDGE_PROTECTED",
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,default=Path("."))
    a=parser.parse_args()
    print(json.dumps(verify(a.root),ensure_ascii=False,sort_keys=True))
    return 0

if __name__=="__main__":
    main()
