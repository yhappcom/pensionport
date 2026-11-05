"""P1: scoped financial evidence matcher on top of P0 concept decomposition.

An original video-claim or educational graph edge alone is NEVER legal proof.
Only question-to-atomic-fact scope matches are returned, along with required
inputs and time/version caveats. External official pages were read by ChatGPT;
this deterministic code cannot itself verify today's external legal text.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse
from .advisory60 import load_policy
from .advisory_semantic import parse

FACTS = Path("ire/v5/advisory_integration/P1_ATOMIC_SOURCE_FACTS_20261105.json")
ALLOWED_HOSTS = ("nts.go.kr", "g.nts.go.kr", "sc.nts.go.kr", "m.krx.co.kr",
                 "www.investor.gov", "securities.koreainvestment.com", "m.shinhansec.com")
NO_DIRECT_LINKS = (
    ("GOMHEE-C33", "EDU-KR-ISA-TO-PENSION-2026-01"),
    ("GOMHEE-C42", "EDU-KR-ISA-TO-PENSION-2026-01"),
    ("GOMHEE-C42", "EDU-KR-PRIVATE-PENSION-1500-2026-01"),
    ("GOMHEE-C52", "EDU-GENERAL-DCA-ARITH-01"),
    ("GOMHEE-C26", "EDU-ETF-NAV-TRACKING"),
)

class EvidenceP1Error(ValueError):
    pass

def require(ok: bool, code: str):
    if not ok:
        raise EvidenceP1Error(code)

def load(root: Path) -> dict:
    data = json.loads((Path(root)/FACTS).read_text(encoding="utf-8"))
    require(data.get("schema") == "IRE_V5_P1_SOURCE_SCOPED_ATOMIC_FACTS_V1"
            and data.get("as_of") == "2026-11-05"
            and data.get("sources_reviewed_this_chat") is True
            and data.get("immutable_page_snapshots_captured") is False
            and data.get("independent_human_blind_verified") is False
            and data.get("financial_claims_accepted_only_with_scope") is True
            and data.get("original_legacy_claims_promoted_directly") == 0
            and data.get("personal_financial_advice_authorized") is False,
            "P1_UNEARNED_EVIDENCE_CERTIFICATION")
    rows=data.get("rows", [])
    require(len(rows)==9 and len({x["fact_id"] for x in rows})==9,
            "P1_ATOMIC_FACT_SET_CHANGED")
    for row in rows:
        url=urlparse(row.get("url", ""))
        require(url.scheme=="https" and url.hostname in ALLOWED_HOSTS
                and row.get("agency") in {"국세청","한국거래소","미국증권거래위원회 투자자교육","한국투자증권","신한투자증권"}
                and row.get("as_of")=="2026-11-05"
                and len(row.get("statement", ""))>=40
                and len(row.get("scope_domains", []))>=1
                and len(row.get("require_terms", []))>=1
                and len(row.get("any_terms", []))>=2
                and len(row.get("application_conditions", []))>=2
                and len(row.get("exceptions", []))>=2
                and row.get("legacy_research_claims_are_direct_evidence") is False,
                "P1_FACT_HAS_NO_NARROW_AUTHORITY_SCOPE")
    return data

def matched(question: str, row: dict) -> bool:
    q=question.casefold()
    return (all(re.search(token, q, flags=re.IGNORECASE)
                for token in row["require_terms"]) and
            any(re.search(token, q, flags=re.IGNORECASE)
                for token in row["any_terms"]))

def plan(question: str, root: Path, as_of: str="2026-11-05") -> dict:
    if as_of!="2026-11-05":
        raise EvidenceP1Error("P1_NEW_EFFECTIVE_DATE_REQUIRES_CHAT_SOURCE_RECHECK")
    root=Path(root)
    policy=load_policy(root)
    meaning=parse(question,policy)
    catalog=load(root)
    scopes=[]
    for row in catalog["rows"]:
        if (set(row["scope_domains"]) & set(meaning["related_domains"])
            and matched(question,row)):
            scopes.append({
                "fact_id":row["fact_id"],
                "claim":row["statement"],
                "issuer":row["agency"],
                "authority_url":row["url"],
                "reviewed_at":row["as_of"],
                "application_conditions":row["application_conditions"],
                "exceptions":row["exceptions"],
                "scope_match":"TOPICAL_ATOMIC_EVIDENCE_WITH_STATED_CONDITIONS",
                "currently_reopened_by_python":False,
                "not_evidence_of_unrelated_legacy_claims":True,
            })
    warnings=[]
    candidate=set(meaning["candidate_claim_ids"])
    for cid,kid in NO_DIRECT_LINKS:
        if cid in candidate:
            warnings.append({
                "claim_id":cid,"mislinked_education_id":kid,
                "action":"DO_NOT_USE_LEGACY_GRAPH_EDGE_AS_PROOF",
            })
    return {
        "schema":"IRE_V5_P1_SCOPE_PLAN_V1",
        "question":question,
        "as_of":as_of,
        "meaning":meaning,
        "direct_scoped_evidence":scopes,
        "blocked_false_core_links":warnings,
        "unknown_or_unverified_rules_must_be_researched":True,
        "all_relevant_rules_verified":False,
        "latest_law_live_checked_by_this_code":False,
        "personal_trade_authorized":False,
        "video_context_not_the_same_as_legal_fact":True,
    }

def audit(root: Path) -> dict:
    root=Path(root)
    cases=(
        ("연금계좌 세액공제 900만원 환급인가요", "P1-PENSION-CREDIT-LIMIT"),
        ("ISA 만기 후 70일에 연금계좌로 이체해도 되나요", "P1-ISA-60D"),
        ("ISA 만기 연금 전환 10% 세액공제는?", "P1-ISA-TRANSFER-10PCT"),
        ("ISA 미국 배당 ETF의 외국원천세 신고는?", "P1-FUND-FOREIGN-TAX-2025"),
        ("ETF NAV 괴리율 추적오차의 의미는?", "P1-ETF-NAV-TRACK"),
        ("서킷브레이커가 발동하면 목표비중 복원을 위해 모두 팔아야 하나요?",
         "P1-SEC-REBALANCE-NOT-FORCED-SELL"),
        ("USD 달러예금과 달러 RP를 같은 안전자산으로 보아도 되나요?",
         "P1-FOREIGN-RP-NOT-BANK-DEPOSIT"),
        ("CMA 금리가 높으니 손실 없이 수익을 보장받나요?",
         "P1-CMA-RP-NOT-PROTECTED"),
    )
    for q,want in cases:
        p=plan(q,root)
        require(want in [x["fact_id"] for x in p["direct_scoped_evidence"]],
                "P1_EVIDENCE_RETRIEVAL_MISSED_"+want)
        require(not p["all_relevant_rules_verified"]
                and not p["personal_trade_authorized"],
                "P1_EVIDENCE_MISREPORTED_AS_COMPLETE")
    negative=(
        ("오늘 반도체를 매도하면 수익이 보장되나요", set()),
        ("CMA 발행어음은 은행 예금자보호가 되나요", set()),
        ("ISA 해외배당의 외국원천세 처리는 어떻게 되나요",
         {"P1-FUND-FOREIGN-TAX-2025"}),
    )
    for q,allowed in negative:
        seen={x["fact_id"] for x in plan(q,root)["direct_scoped_evidence"]}
        require(seen <= allowed,"P1_FALSE_FACT_SCOPE_MATCH")
    return {
        "schema":"IRE_V5_P1_EVIDENCE_AUDIT_V1",
        "atomic_source_scoped_facts":len(load(root)["rows"]),
        "question_fact_scope_tests":len(cases)+len(negative),
        "false_legacy_graph_edges_explicitly_blocked":len(NO_DIRECT_LINKS),
        "live_web_checked_by_chat_not_python":True,
        "whole_video_transcripts_reverified":False,
        "new_personalized_actions_approved":0,
        "not_all_60_legacy_claims_reverified":True,
        "outcome":"P1_SCOPED_EVIDENCE_MECHANISM_IMPLEMENTED",
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--question")
    a=p.parse_args()
    out=plan(a.question,a.root) if a.question else audit(a.root)
    print(json.dumps(out,sort_keys=True,ensure_ascii=False))

if __name__=="__main__":
    main()
