"""Verify a reproducible, source-linked *provisional* 20+5 knowledge snapshot.

Integration here means research joins. It NEVER changes approved knowledge or
certifies legal correctness. Legacy ledger remains immutable.
"""
from pathlib import Path
import json
from collections import Counter
from .five_study_gate import STUDIES,require,StudyGateError,load

class IntegrationError(ValueError):
    pass

def check(ok,reason):
    if not ok: raise IntegrationError(reason)

def audit(root:Path) -> dict:
    root=Path(root)
    p=root/"ire/v5/advisory_knowledge/provisional_integrated_20_plus_5_20261104.json"
    index=load(p)
    check(index.get("schema")=="IRE_V5_PROVISIONAL_INTEGRATED_KNOWLEDGE_V1",
          "INTEGRATION_SCHEMA_INVALID")
    summary=index["summary"]
    check(index.get("approved_legacy_ledger_mutation") is False and
          index.get("independent_blind_verified") is False and
          index.get("release")=="PROVISIONAL_RESEARCH_INTEGRATED_ADVISORY_NO_GO"
          and summary.get("independent_approved_financial_facts")==0
          and summary.get("personalized_advisory_approved") is False,
          "INTEGRATION_FALSE_FINAL_APPROVAL")
    core=load(root/"ire/v5/advisory_knowledge/core20_candidates_20261104.json")
    baseline={c["claim_id"]:c for c in core["claims"]}
    nodes=index.get("nodes")
    check(type(nodes) is list and len(nodes)==len(baseline)==20,"CORE20_NODES_LOST")
    expected={}
    unrelated={}
    for video_id in STUDIES:
        item=load(root/"ire/v5/studies"/(video_id+".json"))
        for c in item["claims"]:
            key=c["claim_id"]
            record={"source_video_id":video_id,
                    "source_roster_no":item["roster_no"],
                    "source_sha256":item["source_sha256"],
                    "source_claim_id":key,
                    "source_cue_start":c["first_cue"],
                    "source_cue_end":c["last_cue"],
                    "relationship":c["relationship"],
                    "source_proposition":c["proposition"],
                    "qualification":c["scope_or_error"],
                    "verification_state":c["review_status"],
                    "evidence_ids":c["evidence_ids"]}
            if c["relationship"]=="UNRELATED":
                unrelated[key]=record
                continue
            for target in c["prior_claim_ids"]:
                expected.setdefault(target,[]).append(record)
    seen=set()
    attached=0
    contested=[]
    for n in nodes:
        cid=n.get("claim_id")
        check(cid in baseline and cid not in seen,
              "INTEGRATION_DUPLICATE_OR_UNKNOWN_LEGACY_ID")
        seen.add(cid)
        base=baseline[cid]
        check(n.get("original_legacy_claim")==base["legacy_claim"]
              and n.get("existing_supporting_video_ids")==base["original_supporting_video_ids"]
              and n.get("domain")==base["domain"],
              "INTEGRATION_ORIGINAL_KNOWLEDGE_CHANGED")
        check(n.get("reviewed_source_candidate_refs")==base["evidence_source_ids"]
              and n.get("existing_scope_condition")==base["condition"]
              and n.get("existing_scope_exception")==base["exception_or_risk"],
              "INTEGRATION_PREVIOUS_CONDITIONS_CHANGED")
        links=n.get("incoming_research_links")
        check(links==expected.get(cid,[]),"INTEGRATION_NEW_EVIDENCE_LOST_OR_TAMPERED")
        check(n.get("integrated_research_status")=="PROVISIONAL_RECONCILIATION_ONLY"
              and n.get("financial_fact_approved") is False
              and n.get("advisory_approved") is False,
              "INTEGRATION_UNVERIFIED_CLAIM_PROMOTED")
        attached+=len(links)
        if any(x["relationship"]=="CHALLENGES" for x in links):
            contested.append(cid)
    excluded=index.get("excluded_non_investment_items")
    check(excluded==list(unrelated.values()),
          "INTEGRATION_UNRELATED_CONSUMER_FINANCE_NOT_EXCLUDED")
    counts=Counter(
        c["relationship"] for video_id in STUDIES
        for c in load(root/"ire/v5/studies"/(video_id+".json"))["claims"])
    check(summary.get("existing_core_nodes")==20
          and summary.get("newly_studied_videos")==5
          and summary.get("new_provisional_claims")==sum(counts.values())
          and summary.get("relationship_by_type")==dict(counts)
          and summary.get("attached_legacy_relation_edges")==attached
          and summary.get("existing_nodes_with_incoming")==len(expected)
          and summary.get("out_of_scope_claims_excluded")==len(unrelated)
          and summary.get("challenged_legacy_claim_ids")==contested,
          "INTEGRATION_SUMMARY_NOT_REPRODUCIBLE")
    return {"schema":"IRE_V5_PROVISIONAL_INTEGRATION_AUDIT_V1",
            "core_claims_unchanged":20,
            "new_source_study_videos":5,
            "new_research_claims":sum(counts.values()),
            "linked_research_edges":attached,
            "core_nodes_receiving_new_evidence":len(expected),
            "external_personal_finance_excluded":len(unrelated),
            "challenged_core_nodes":len(contested),
            "independent_approval":False,"advisory_go":False}

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path("."))
    a=p.parse_args()
    print(json.dumps(audit(a.root),ensure_ascii=False,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
