"""Verify V5's materialized 13-topic *provisional education* knowledge graph.

The graph is made for retrieval and duplication-safe accumulation across SRT
videos. Passing does not certify financial truth or authorize personalized
advice. The 20-node legacy graph and approved 116-claim source ledger are
read-only inputs. This gate fails closed on unknown claims, weak links, lost
exceptions, or false independent approval.
"""
from __future__ import annotations
import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

GRAPH = "ire/v5/advisory_knowledge/integrated_education13_20261104.json"
DIR = Path("ire/v5/advisory_knowledge")

class GraphGateError(ValueError):
    pass

def require(ok, message):
    if not ok:
        raise GraphGateError(message)

def read(root: Path, name: str):
    return json.loads((root / name).read_text(encoding="utf-8"))

def verify(root: Path, graph: dict | None = None):
    root = Path(root)
    g = graph if graph is not None else read(root, GRAPH)
    old = read(root, str(DIR/"deduplicated_educational_knowledge_20261104.json"))
    cases = read(root, str(DIR/"one_turn33_20261104/decisions.json"))
    triage = read(root, str(DIR/"review44_20261104/triage.json"))
    aud = read(root, str(DIR/"verification_20261104/adjudications.json"))
    spans = read(root, str(DIR/"verification_20261104/source_spans.json"))
    legacy = read(root, str(DIR/"provisional_integrated_20_plus_5_20261104.json"))
    old_author = read(root, str(DIR/"verification_20261104/external_authorities.json"))
    require(g.get("schema")=="IRE_V5_INTEGRATED_EDUCATION_KNOWLEDGE_13_V1"
            and g.get("as_of")=="2026-11-04"
            and g.get("total_education_topics")==13
            and len(g.get("nodes",[]))==13,
            "GRAPH_MISSING_OR_EXTRA_EDUCATION_TOPICS")
    require(g.get("status")=="PROVISIONAL_GENERAL_EDUCATION_RESEARCH_NOT_PERSONAL_ADVICE"
            and g.get("original_legacy_ledger_mutated") is False
            and g.get("remaining_other_53_statuses_protected") is True
            and g.get("independent_blind_review_completed") is False
            and g.get("formal_financial_advice_approved") is False,
            "GRAPH_FALSE_APPROVAL_OR_LEGACY_MUTATION")
    original={x["knowledge_id"]:x for x in old["entries"]}
    cases_by_id={x["claim_id"]:x for x in cases["cases"]}
    tri_by_id={x["claim_id"]:x for x in triage["records"]}
    prior_aud={x["audit_id"]:x for x in aud["rows"]}
    source_spans={x["id"]:x for x in spans["rows"]}
    historical={x["claim_id"]:x for x in triage["records"]
                if x["disposition"] in
                {"HISTORICAL_ONLY","UNSAFE_GENERALIZATION_BLOCKED","OUT_OF_SCOPE"}}
    core_ids={x["claim_id"] for x in legacy["nodes"]}
    require(len(original)==4 and len(cases_by_id)==33
            and len(prior_aud)==10 and len(source_spans)==10
            and len(historical)==11 and len(core_ids)==20,
            "GRAPH_PREDECESSOR_UNEXPECTED")
    expected_new=defaultdict(list)
    for case in cases["cases"]:
        if case["old_status"]=="EDUCATION_CANDIDATE":
            expected_new[case["knowledge_target"]].append(case)
    require(len(expected_new)==11
            and sum(map(len,expected_new.values()))==12,
            "GRAPH_NEW_EDUCATION_SOURCE_COUNT_CHANGED")
    node_ids={n["knowledge_id"] for n in g["nodes"]}
    expected_ids=set(original)|set(expected_new)
    require(len(node_ids)==13 and node_ids==expected_ids,
            "GRAPH_LOST_OR_INVENTED_KNOWLEDGE_CONCEPT")
    byid={n["knowledge_id"]:n for n in g["nodes"]}
    require(len(byid)==len(g["nodes"]),
            "GRAPH_DUPLICATED_NODE_ID")
    official_sources={}
    for x in [*old_author["sources"],*cases["reference_catalog"]]:
        rid=x["id"]
        u=urlparse(x["url"])
        require(u.scheme=="https" and bool(u.hostname),
                "GRAPH_INVALID_OFFICIAL_SOURCE_URL")
        if rid in official_sources:
            require(official_sources[rid]["url"]==x["url"],
                    "GRAPH_AUTHORITY_ID_CHANGED_URL")
        official_sources[rid]=x
    stored={x["id"]:x for x in g.get("source_reference_catalog",[])}
    require(len(stored)==len(g.get("source_reference_catalog",[]))
            and set(stored)<=set(official_sources),
            "GRAPH_UNKNOWN_OR_DUPLICATED_REFERENCE")
    expected_edgelist={}
    for kid,base in original.items():
        for aid in base["source_audit_ids"]:
            require(aid in source_spans and aid in prior_aud
                    and prior_aud[aid]["disposition"]=="EVIDENCE_SUPPORTED_EDUCATIONAL_SCOPE",
                    "GRAPH_MISSING_OR_UNAPPROVED_PRIOR_EVIDENCE")
            original_span=source_spans[aid]
            expected_edgelist[aid]={
                "evidence_role":"SOURCE_CONTEXT_SCOPED_FINANCIAL_EDUCATION",
                "research_review_id":aid,
                "source_claim_id":original_span["source_study_claim_id"],
                "source_video_id":original_span["video_id"],
                "original_cue_start":original_span["first_cue"],
                "original_cue_end":original_span["last_cue"],
                "original_cue_span_sha256":original_span["cue_span_sha256"],
                "external_reference_ids":prior_aud[aid]["authority_ids"],
            }
    actual_referenced=set()
    attached_new=set()
    all_edges=[]
    linked_core=set()
    for kid,n in byid.items():
        require(n.get("safe_use")=="GENERAL_EDUCATION_ONLY"
                and n.get("research_quality_status")==
                "MULTI_SOURCE_PUBLIC_DOCUMENT_CROSSCHECK_NOT_BLIND_HUMAN_APPROVAL"
                and n.get("independent_human_blind_verified") is False
                and n.get("personalized_advice_approved") is False
                and n.get("financial_fact_independently_certified") is False,
                "GRAPH_CONCEPT_UNAUTHORIZED_APPROVAL")
        require(isinstance(n.get("safe_general_statement"),str)
                and len(n["safe_general_statement"])>=20
                and isinstance(n.get("critical_scope_and_exceptions"),str)
                and len(n["critical_scope_and_exceptions"])>=25,
                "GRAPH_OMITTED_KNOWLEDGE_SCOPE_OR_EXCEPTIONS")
        if kid in original:
            base=original[kid]
            require(n.get("previous_education_record") is True
                    and n.get("prior_education_claim_unchanged") is True
                    and n["safe_general_statement"]==base["educational_fact"]
                    and n["critical_scope_and_exceptions"]==base["critical_qualification"],
                    "GRAPH_SILENT_CHANGE_TO_PREVIOUS_EDUCATION_FACT")
        else:
            require(n.get("previous_education_record") is False
                    and n.get("prior_education_claim_unchanged") is None,
                    "GRAPH_FABRICATED_ORIGINAL_KNOWLEDGE")
        edges=n.get("source_links")
        require(isinstance(edges,list) and edges,
                "GRAPH_KNOWLEDGE_WITHOUT_SOURCE_LINKS")
        expected_edge_ids=[
            *(original[kid]["source_audit_ids"] if kid in original else []),
            *["one_turn33:"+c["claim_id"] for c in expected_new.get(kid,[])],
        ]
        require([x.get("research_review_id") for x in edges]==expected_edge_ids,
                "GRAPH_EVIDENCE_LINKS_LOST_OR_MISORDERED")
        core=set(original[kid]["legacy_claim_ids"]) if kid in original else set()
        for e in edges:
            rid=e["research_review_id"]
            if rid in expected_edgelist:
                require(e==expected_edgelist[rid],
                        "GRAPH_EXISTING_ORIGINAL_CUE_PROVENANCE_CHANGED")
            else:
                require(rid.startswith("one_turn33:"),
                        "GRAPH_UNKNOWN_EVIDENCE_LINK")
                cid=rid.split(":",1)[1]
                require(cid not in attached_new and cid in cases_by_id
                        and cid not in historical,
                        "GRAPH_DUPLICATE_OR_UNVERIFIED_NEW_SOURCE")
                attached_new.add(cid)
                source=cases_by_id[cid]
                tri=tri_by_id[cid]
                require(source["knowledge_target"]==kid
                        and source["old_status"]=="EDUCATION_CANDIDATE"
                        and e["source_claim_id"]==cid
                        and e["source_video_id"]==source["video_id"]
                        and e["original_cue_start"]==tri["first_cue"]
                        and e["original_cue_end"]==tri["last_cue"]
                        and e["original_cue_span_sha256"]==tri["original_cue_span_sha256"]
                        and e["external_reference_ids"]==source["official_reference_ids"],
                        "GRAPH_NEW_CUE_OR_AUTHORITY_MISMATCH")
                core.update(tri["prior_claim_ids"])
            for sid in e["external_reference_ids"]:
                require(sid in official_sources
                        and sid in stored
                        and stored[sid]["url"]==official_sources[sid]["url"]
                        and stored[sid]["source_verified_by_external_human"] is False
                        and stored[sid]["immutable_original_copy_archived"] is False,
                        "GRAPH_FABRICATED_INDEPENDENT_SOURCE")
                actual_referenced.add(sid)
            all_edges.append(e)
        require(n.get("existing_core_claim_ids")==list(dict.fromkeys(
                    x for x in (
                        [*original[kid]["legacy_claim_ids"]]
                        if kid in original else [])+
                    [p for c in expected_new.get(kid,[])
                     for p in tri_by_id[c["claim_id"]]["prior_claim_ids"]]))
                and core<=core_ids,
                "GRAPH_EXISTING_CORE_CLAIM_LINEAGE_CHANGED")
        require(n.get("original_source_claims")==list(dict.fromkeys(
                    e["source_claim_id"] for e in edges)),
                "GRAPH_SOURCE_CLAIM_IDS_MISSING")
        require(n.get("authority_ids")==list(dict.fromkeys(
                    r for e in edges for r in e["external_reference_ids"])),
                "GRAPH_AUTHORITY_IDS_MISSING")
        require(n.get("requires_fresh_effectivity_check") is True
                if n["knowledge_kind"]=="REGULATED_TAX_RULE" else True,
                "GRAPH_MISSING_REGULATED_TAX_FRESHNESS_GATE")
        linked_core.update(core)
    require(set(attached_new)=={
        c["claim_id"] for c in cases["cases"]
        if c["old_status"]=="EDUCATION_CANDIDATE"},
        "GRAPH_NOT_ALL_12_EDUCATION_SOURCES_CONNECTED")
    require(set(stored)==actual_referenced,"GRAPH_REFERENCE_CATALOG_NOT_REPRODUCIBLE")
    metrics=g.get("metrics",{})
    require(metrics.get("initial_existing_education_concepts")==4
            and metrics.get("new_education_concepts")==9
            and metrics.get("education_source_assessment_links")==17
            and len(all_edges)==17
            and metrics.get("distinct_original_video_ids")==
                len({e["source_video_id"] for e in all_edges})==5
            and metrics.get("approved_personal_advice")==0
            and metrics.get("external_human_blind_approvals")==0,
            "GRAPH_SUMMARY_OR_COVERAGE_MISMATCH")
    return {
      "schema":"IRE_V5_INTEGRATED_EDUCATION_GRAPH_GATE_V1",
      "knowledge_concepts":len(byid),
      "source_evidence_links":len(all_edges),
      "previous_education_concepts_preserved":len(original),
      "new_concepts_deduplicated":len(byid)-len(original),
      "corroborating_new_source_claims":len(attached_new),
      "videos_with_original_cue_lineage":5,
      "legacy_20_nodes":len(core_ids),
      "legacy_core_nodes_referenced":len(linked_core),
      "source_authorities_referenced":len(stored),
      "unassessed_or_blocked_claims_auto_promoted":0,
      "independent_blind_human_verdicts":0,
      "personal_financial_advice_go":False,
      "release":"SCOPED_EDUCATION_GRAPH_ONLY",
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,default=Path("."))
    args=parser.parse_args()
    print(json.dumps(verify(args.root),ensure_ascii=False,sort_keys=True))
    return 0

if __name__=="__main__":
    main()
