"""Live, fail-closed P4 retrieval: prior 22 education nodes + 7 source-reviewed
video #1 W41-W67 education nodes. Not personal advice or formal law approval.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from . import p3_original_27_source_gate as p3
from . import p4_active_integration as baseline

MANIFEST=Path("ire/v5/advisory_knowledge/p4_p3_incremental_education29_20261106.json")
EXPECTED_MANIFEST_BLOB="b92573dbefb0f22d3a3a266685415c538b4f7a72"
ALLOWED={"SOURCE_AND_ARITHMETIC_EDUCATION","SOURCE_AND_OFFICIAL_SCOPED_EDUCATION",
         "SOURCE_AND_UNVERIFIED_PRODUCT_GUARDRAIL_EDUCATION",
         "SOURCE_AND_GENERAL_RISK_EDUCATION"}

class P4IncrementalError(ValueError): pass

def require(ok,code):
    if not ok: raise P4IncrementalError(code)

def blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()

def read(root,path):
    return json.loads((Path(root)/path).read_text("utf-8"))

def load(root:Path,*,source_zip:Path|None=None,replacement:dict|None=None):
    root=Path(root)
    original=(root/MANIFEST).read_bytes()
    if replacement is None:
        require(blob(original)==EXPECTED_MANIFEST_BLOB,"P4_UNREVIEWED_MANIFEST")
    d=json.loads(original) if replacement is None else replacement
    rec=p3.verify(root,source_zip=source_zip)
    old=baseline.load(root)
    lineage=d.get("lineage",{})
    require(d.get("schema")=="IRE_V5_P4_P3_27_SOURCE_INCREMENTAL_EDUCATION29_V1"
            and d.get("as_of")=="2026-11-06"
            and d.get("prior_education_nodes")==22
            and d.get("new_education_nodes")==7
            and d.get("combined_education_nodes")==29
            and d.get("new_atomic_source_candidates_reviewed")==89
            and d.get("official_narrow_claims_scoped")==10
            and d.get("overgeneralizations_restricted")==14
            and d.get("materialized_116_master_updated") is False
            and d.get("financial_law_facts_formally_approved")==0
            and d.get("blind_independent_recall_certified") is False
            and d.get("raw_private_original_published") is False
            and d.get("scope")=="CHAT_HOST_SOURCE_BYTES_MATCHED_GENERAL_EDUCATION_ONLY",
            "P4_FALSE_RELEASE")
    require(lineage.get("p3_atomic_ledger_path")==str(p3.LEDGER)
            and lineage.get("prior_p4_22_path")==str(baseline.MANIFEST)
            and lineage.get("p3_atomic_ledger_git_blob_sha1")==blob((root/p3.LEDGER).read_bytes())
            and lineage.get("prior_p4_22_git_blob_sha1")==blob((root/baseline.MANIFEST).read_bytes())
            and lineage.get("original_srt_sha256")==p3.EXPECTED_SRT_SHA
            and lineage.get("original_archive_sha256_seen_in_host")==p3.EXPECTED_100_ZIP_SHA,
            "P4_LINEAGE_SOURCE_CHANGED")
    require(old["active_education_node_count"]==22
            and rec["original_cues_dispositioned"]==486
            and rec["source_anchored_candidates"]==89,
            "P4_P3_ATOMIC_RECEIPT_NOT_ACCEPTABLE")
    parent=read(root,p3.LEDGER)
    known={c["claim_id"]:c for w in parent["windows"] for c in w["claims"]}
    oldids={n["knowledge_id"] for n in old["nodes"]}
    items=d.get("items")
    require(type(items) is list and len(items)==7 and
            len({x.get("knowledge_id") for x in items})==7,
            "P4_WRONG_INTEGRATION_COUNT")
    for n in items:
        refs=n.get("source_claim_ids",[])
        official_refs=n.get("official_context_source_ids",[])
        require(n.get("knowledge_id","").startswith("P3-001-")
            and n.get("namespace")=="P3_VIDEO1_W41_67_SOURCE_VERIFIED"
            and n.get("provenance_video_id")==p3.VIDEO_ID
            and n.get("source_original_video1_srt_sha256")==p3.EXPECTED_SRT_SHA
            and n.get("source_original_replayed_by_chat_host") is True
            and n.get("source_original_replayed_by_github_ci") is False
            and n.get("government_signed_original_copy_verified") is False
            and n.get("independent_human_blind_fact_verified") is False
            and n.get("status")=="ACTIVE_SCOPED_GENERAL_EDUCATION_NOT_PERSONAL_ADVICE"
            and n.get("formal_116_master_claim_merged") is False
            and n.get("personalized_action_approved") is False
            and n.get("knowledge_basis") in ALLOWED
            and len(n.get("safe_general_statement",""))>=70
            and len(n.get("critical_scope_and_exceptions",""))>=65,
            "P4_UNAPPROVED_OR_INVALID_KNOWLEDGE")
        require(type(refs) is list and len(refs)>=2 and len(set(refs))==len(refs)
            and all(cid in known for cid in refs)
            and type(n.get("prior_knowledge_ids")) is list
            and all(k in oldids for k in n["prior_knowledge_ids"])
            and type(official_refs) is list
            and all(k in parent["source_catalog"] for k in official_refs)
            and type(n.get("terms")) is list and len(n["terms"])>=3
            and len(set(n["terms"]))==len(n["terms"]),
            "P4_SOURCE_OR_GRAPH_RELATION_INVALID")
        if n["knowledge_basis"]=="SOURCE_AND_OFFICIAL_SCOPED_EDUCATION":
            require(bool(official_refs) and any(
                known[cid]["meaning_class"] in {
                    "REGULATORY_SUPPORTED_SCOPED","REGULATORY_REJECTED_OVERGENERAL"
                } for cid in refs),"P4_UNSUPPORTED_OFFICIAL_CLAIM")
        if n["knowledge_basis"]=="SOURCE_AND_UNVERIFIED_PRODUCT_GUARDRAIL_EDUCATION":
            require(not official_refs and any(
                known[cid]["meaning_class"]=="PRODUCT_UNVERIFIED" for cid in refs)
                and "보증 여부" in n["safe_general_statement"],
                "P4_INSURANCE_PRODUCT_FALSE_GUARANTEE")
    return {"schema":"IRE_V5_P4_P3_LIVE_EDUCATION29_GRAPH_V1",
            "nodes":old["nodes"]+items,
            "existing_education_nodes":22,"new_education_nodes":7,"total_education_nodes":29,
            "source_atomic_candidates":89,
            "source_replayed_in_current_process":rec["original_private_source_replayed_this_process"],
            "formal_master_merges":0,"personal_trading_approved":False,
            "release":"SCOPED_GENERAL_EDUCATION_ONLY"}

def norm(s):
    return re.sub(r"\s+|[,，]","",s.casefold())

def retrieve(root:Path,question:str,*,intent="general_education",limit=8):
    require(type(question) is str and bool(question.strip()),"P4_EMPTY_QUESTION")
    require(intent in {"general_education","personal_decision_support",
                       "order_execution","guaranteed_return"},"P4_UNKNOWN_INTENT")
    require(type(limit) is int and 1<=limit<=29,"P4_BAD_LIMIT")
    if intent in {"order_execution","guaranteed_return"}:
        return {"schema":"IRE_V5_P4_SOURCE_EDUCATION_RETRIEVAL29_V1",
                "match_count":0,"items":[],"decision":"ACTION_BLOCKED",
                "master_modified":False,"personal_order_approved":False}
    graph=load(root)
    q=norm(question)
    scored=[]
    for n in graph["nodes"]:
        hits=[t for t in n["terms"] if norm(t) in q]
        if hits:
            score=sum(len(norm(t))+1 for t in hits)
            if n["knowledge_id"].startswith("P3-001-"): score+=2
            scored.append((score,n))
    scored.sort(key=lambda x:(-x[0],x[1]["knowledge_id"]))
    catalog=read(root,p3.LEDGER)["source_catalog"]
    selected=[]
    for score,n in scored[:limit]:
        fresh=n.get("namespace")=="P3_VIDEO1_W41_67_SOURCE_VERIFIED"
        selected.append({"knowledge_id":n["knowledge_id"],
            "namespace":n["namespace"],"score":score,
            "statement":n.get("safe_general_statement",n.get("statement")),
            "scope_and_exceptions":n.get(
                "critical_scope_and_exceptions",n.get("scope_and_exceptions")),
            "source_claim_ids":n.get("source_claim_ids",[]),
            "official_context_urls":[catalog[s]["url"] for s in
                 n.get("official_context_source_ids",[])] if fresh else [],
            "status":n["status"],"formal_financial_fact_approved":False,
            "personalized_action_approved":False})
    return {"schema":"IRE_V5_P4_SOURCE_EDUCATION_RETRIEVAL29_V1",
            "match_count":len(selected),"items":selected,
            "decision":"SCOPED_EDUCATION_ONLY" if selected else "NO_MATCH",
            "master_modified":False,"personal_order_approved":False}

PROBES={
    "연금 1500 종합과세 강제인가요":"P3-001-PRIVATE-PENSION-1500-CHOICE",
    "국내주식형 ETF IRP 매매차익 과세":
        "P3-001-IRP-DOMESTIC-STOCK-ETF-TAX-DISTINCTION",
    "옛날 연금저축보험 이전과 최저보증이율 비교":
        "P3-001-OLD-PENSION-INSURANCE-TRANSFER-CHECKLIST",
    "ISA 50년 손실 이월 무기한 비과세":
        "P3-001-ISA-NETTING-SCOPE-NO-50YEAR-GUARANTEE",
    "ISA 3년 재가입과 만기 연장":
        "P3-001-ISA-RENEWAL-VS-REENTRY-LIMITS",
    "배당만 빼면 원금 유지 가능한가요":
        "P3-001-DISTRIBUTION-IS-NOT-PRESERVED-PRINCIPAL",
    "10억 노후자금은 충분한가요":
        "P3-001-RETIREMENT-SUFFICIENCY-IS-NOT-GUARANTEE",
}
def audit(root:Path):
    g=load(root)
    for q,want in PROBES.items():
        rows=retrieve(root,q,limit=29)["items"]
        require(want in {r["knowledge_id"] for r in rows},
                "P4_NEW_SOURCE_NODE_NOT_RETRIEVABLE")
    require(not retrieve(root,"내 계좌에서 지금 모두 매도해줘",
             intent="order_execution")["items"],"P4_PERSONAL_ORDER_BLOCK_FAILURE")
    return {"schema":"IRE_V5_P4_P3_LIVE_INTEGRATION_AUDIT_V1",
            "p3_original_windows":27,"source_claim_candidates":g["source_atomic_candidates"],
            "previous_education_nodes":22,"new_education_nodes":7,
            "active_education_nodes":29,"new_question_probes_passed":len(PROBES),
            "formal_master_merges":0,"personal_trading_authorized":False,
            "blind_independent_answer_accuracy_verified":False,
            "release":"P4_NEW_EDUCATION_LIVE_NOT_PERSONAL_ADVICE"}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--source-zip",type=Path)
    p.add_argument("--question")
    args=p.parse_args()
    out=(retrieve(args.root,args.question) if args.question else
         (load(args.root,source_zip=args.source_zip) if args.source_zip else audit(args.root)))
    if isinstance(out,dict) and "nodes" in out:
        out={k:v for k,v in out.items() if k!="nodes"}
    print(json.dumps(out,ensure_ascii=False,sort_keys=True))

if __name__=="__main__": main()
