"""Structured, source-cited advisory access rehearsal over 53 original claims.

This is a deterministic safety policy, NOT a generative answer-quality test.
ChatGPT must identify claim IDs and perform fresh source checks in the active
turn; only limited general-education text may pass through this policy.
Unverified, historical, overconfident, personalized, or unknown requests fail
closed. No customer profile can authorize personalized investment advice here.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from pathlib import Path
import argparse
import json

from .integrated_education_gate import GRAPH, read, verify as verify_graph

STUDIES=("7p3p7TKcdqY","l0Q-2Ah-ba8","2bLy034D5LA",
         "z1oZOJ3_uIk","tDD5GzvDYq8")
STUDY_DIR="ire/v5/studies"
ROOT_DIR="ire/v5/advisory_knowledge"

class AdvisoryAccessError(ValueError):
    pass

def source_claims(root):
    content={}
    for vid in STUDIES:
        s=read(root,f"{STUDY_DIR}/{vid}.json")
        if s["video_id"]!=vid:
            raise AdvisoryAccessError("SOURCE_VIDEO_ID_CHANGED")
        for c in s["claims"]:
            if c["claim_id"] in content:
                raise AdvisoryAccessError("SOURCE_CLAIM_ID_DUPLICATED")
            content[c["claim_id"]]={"video_id":vid,**c}
    if len(content)!=53:
        raise AdvisoryAccessError("SOURCE_UNIVERSE_NOT_53")
    return content

def create_policy(root:Path):
    root=Path(root)
    verify_graph(root)
    g=read(root,GRAPH)
    originals=source_claims(root)
    triage=read(root,f"{ROOT_DIR}/review44_20261104/triage.json")
    initial=read(root,f"{ROOT_DIR}/verification_20261104/adjudications.json")
    node_lookup=defaultdict(list)
    for node in g["nodes"]:
        for claim_id in node["original_source_claims"]:
            node_lookup[claim_id].append(node)
    if len(node_lookup)!=17:
        raise AdvisoryAccessError("INCORRECT_EDUCATION_SOURCE_COVERAGE")
    for cid in node_lookup:
        if cid not in originals:
            raise AdvisoryAccessError("EDUCATION_CLAIM_NOT_FROM_SRT")
    raw_states=defaultdict(set)
    for r in initial["rows"]:
        raw_states[r["source_study_claim_id"]].add(r["disposition"])
    for r in triage["records"]:
        raw_states[r["claim_id"]].add(r["disposition"])
    for cid in originals:
        if not raw_states[cid]:
            raise AdvisoryAccessError("SOURCE_WITHOUT_ANY_REVIEW_STATUS")
    refs={x["id"]:x for x in g["source_reference_catalog"]}
    return {
        "original_claims":originals,
        "education_nodes":dict(node_lookup),
        "review_statuses":dict(raw_states),
        "official_refs":refs,
        "knowledge_node_count":len(g["nodes"]),
    }

def apply(policy,claim_id:str,intent:str):
    if intent not in {"general_education","personal_action","guaranteed_return"}:
        raise AdvisoryAccessError("UNKNOWN_QUERY_INTENT_FAIL_CLOSED")
    if claim_id not in policy["original_claims"]:
        return {"claim_id":claim_id,"intent":intent,
                "decision":"REFUSE_UNKNOWN_CLAIM",
                "reason":"원문 자막과 연결되지 않은 주장으로 지식·자문 결과를 생성하지 않음",
                "personal_advice_approved":False}
    statuses=sorted(policy["review_statuses"][claim_id])
    nodes=policy["education_nodes"].get(claim_id,[])
    if intent=="personal_action":
        return {"claim_id":claim_id,"intent":intent,
                "decision":"REFUSE_PERSONALIZED_ADVICE",
                "reason":"개인 계좌·소득·상품·위험감내 및 독립 적합성 심사 미완료",
                "verified_public_education_available":bool(nodes),
                "missing_checks":["투자자 목적·기간·위험감내","계좌·과세원천·결정세액",
                                  "상품 코드·최신 공시·비용","독립 적합성·법적 운영 승인"],
                "personal_advice_approved":False}
    if intent=="guaranteed_return":
        return {"claim_id":claim_id,"intent":intent,
                "decision":"REFUSE_PROFIT_OR_LOSS_GUARANTEE",
                "reason":"금융 원금·배당·정액적립·리밸런싱에 무조건 보장 없음",
                "personal_advice_approved":False}
    if not nodes:
        return {"claim_id":claim_id,"intent":intent,
                "decision":"NOT_RELEASED_AS_EDUCATION",
                "review_statuses":statuses,
                "reason":"추가 조건·과거 자료·수치 ASR·위험 일반화 등으로 교육 지식 승격 보류",
                "personal_advice_approved":False}
    references=list(dict.fromkeys(
        source for node in nodes for source in node["authority_ids"]))
    return {
        "claim_id":claim_id,
        "intent":intent,
        "decision":"GENERAL_EDUCATION_WITH_SCOPE_ONLY",
        "knowledge_ids":[n["knowledge_id"] for n in nodes],
        "safe_general_statements":[n["safe_general_statement"] for n in nodes],
        "required_qualifications":[n["critical_scope_and_exceptions"] for n in nodes],
        "official_reference_urls":[policy["official_refs"][k]["url"] for k in references],
        "review_statuses":statuses,
        "context_specific_warnings":[s for s in statuses
                                     if s!="EVIDENCE_SUPPORTED_EDUCATIONAL_SCOPE"
                                     and s!="EDUCATION_CANDIDATE"],
        "personal_advice_approved":False,
        "source_audio_independently_verified":False,
        "human_blind_independent_accuracy_verified":False,
    }

def audit(root:Path):
    p=create_policy(root)
    results=Counter()
    for cid in p["original_claims"]:
        res=apply(p,cid,"general_education")
        results[res["decision"]]+=1
        if res["personal_advice_approved"]:
            raise AdvisoryAccessError("UNSAFE_GENERAL_EDUCATION_PROMOTED")
        personal=apply(p,cid,"personal_action")
        if personal["decision"]!="REFUSE_PERSONALIZED_ADVICE" or personal[
            "personal_advice_approved"]:
            raise AdvisoryAccessError("PERSONAL_ACTION_ACCIDENTALLY_APPROVED")
    if results!={"GENERAL_EDUCATION_WITH_SCOPE_ONLY":17,
                 "NOT_RELEASED_AS_EDUCATION":36}:
        raise AdvisoryAccessError("INVALID_RESEARCH_RELEASE_COUNTS")
    return {
        "schema":"IRE_V5_DETERMINISTIC_ADVISORY_ACCESS_REHEARSAL_V1",
        "source_claims_checked":len(p["original_claims"]),
        "structured_education_claims_available":results[
            "GENERAL_EDUCATION_WITH_SCOPE_ONLY"],
        "other_claims_rejected_for_education":results[
            "NOT_RELEASED_AS_EDUCATION"],
        "personalized_action_requests_refused":53,
        "new_and_existing_education_concepts":p["knowledge_node_count"],
        "independent_model_answer_quality_measurement":False,
        "independent_blind_human_accuracy_verdicts":0,
        "real_personalized_investment_advice_approved":False,
        "release":"GENERAL_EDUCATION_RETRIEVAL_WITH_GUARDRAILS_ONLY",
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--claim-id")
    p.add_argument("--intent",choices=("general_education","personal_action","guaranteed_return"),
                   default="general_education")
    args=p.parse_args()
    if args.claim_id:
        result=apply(create_policy(args.root),args.claim_id,args.intent)
    else:
        result=audit(args.root)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
