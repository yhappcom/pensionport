"""P0: clause-aware multi-domain financial intent and evidence-unit planner.

No neural/API inference: the chat host performs actual semantic judgement. This
local deterministic layer extracts *candidate* concepts, amounts and related
knowledge routes. Never call a ranked candidate an independently verified fact.
"""
from __future__ import annotations
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from .advisory60 import load_policy, score, PERSONAL_TERMS, GUARANTEE_TERMS

COMPLEX_CONCEPTS = {
 "ISA_TRANSFER": (r"isa|개인종합자산관리", r"만기|이체|옮기|전환|해지|종료|연금"),
 "ISA_FOREIGN_DIVIDEND": (r"외국|해외|미국", r"배당|원천세|납부세액|외국세|세금"),
 "PENSION_TAX": (r"연금저축|연금계좌|irp|개인연금", r"세액공제|비공제|납입한도|세금 환급|공제"),
 "RETIREMENT_WITHDRAWAL": (r"은퇴|퇴직|연금|노후", r"생활비|부족분|인출|수령|연금액"),
 "IRP_ACCOUNT": (r"퇴직연금|irp|dc형|db형|개인형", r"위험자산|중도인출|계좌|제한|이전"),
 "RETIREMENT_PLANNING": (r"은퇴|노후|국민연금|공무원연금", r"준비|계획|목표|언제|연기|예상"),
 "ETF_PRODUCT": (r"etf|펀드|배당|분배|nav", r"총수익|괴리|보수|지수|분배|배당락|가격"),
 "GENERAL_TAX": (r"세금|과세|외국납부세액|원천징수", r"신고|세율|공제|분리|종합|국내"),
 "ALLOCATION": (r"주식|채권|비중|포트폴리오|리밸런싱", r"목표|배분|조절|%|퍼센트|비중"),
 "CASH_CMA": (r"cma|rp|발행어음|예금", r"비상|보호|안전|금리|현금|단기|위험"),
 "FOREIGN_CURRENCY": (r"달러|usd|엔화|환율|외화", r"rp|예금|환헤지|위험|환전|엔|달러"),
 "BONDS": (r"채권|회사채|국채", r"이자|금리|만기|매입|신용등급|위험|표면"),
 "MARKET_STRESS": (r"서킷브레이커|급락|폭락|하락|손실|본전", r"매도|매수|조정|비중|손절|보유|대응"),
 "RISKY_STRUCTURES": (r"els|낙인|녹인|선물|리츠|원자재", r"상환|손실|장벽|롤오버|비용|위험"),
 "INVESTOR_BEHAVIOR": (r"초보|처음|월급|저축|가계부", r"투자|기록|방법|얼마|현금흐름"),
}
# A main question can be about a foreign-dividend tax *and* an ISA transfer.
# Evidence plan keeps both facets, rather than forcing one false graph link.
BOOST = {
 "ISA_TRANSFER": 8, "ISA_FOREIGN_DIVIDEND": 12,
 "PENSION_TAX": 7, "RETIREMENT_WITHDRAWAL": 8,
 "IRP_ACCOUNT": 7, "RETIREMENT_PLANNING": 6,
 "ETF_PRODUCT": 6, "GENERAL_TAX": 6,
 "ALLOCATION": 7, "CASH_CMA": 7,
 "FOREIGN_CURRENCY": 10, "BONDS": 6,
 "MARKET_STRESS": 10, "RISKY_STRUCTURES": 7,
 "INVESTOR_BEHAVIOR": 6,
}
ROLE_RE = re.compile(r"(?:\d+(?:\.\d+)?\s*(?:억원|억|천만원|만원|원|%|퍼센트|개월|년|일))")
CLAUSE_RE = re.compile(r"(?:[?？;；]|\s+(?:그리고|그런데|반면|동시에|혹은|또는|vs)\s+)")

def _facets(question: str) -> dict[str, dict]:
    q = question.casefold()
    found = {}
    for domain, (subject, predicate) in COMPLEX_CONCEPTS.items():
        a = re.search(subject, q)
        b = re.search(predicate, q)
        if a and b:
            found[domain] = {"domain":domain, "subject":a.group(0),
                             "predicate":b.group(0), "kind":"semantic_facet"}
    return found

def parse(question: str, policy: dict) -> dict:
    if not isinstance(question, str) or len(question.strip()) < 6:
        raise ValueError("P0_INVALID_FINANCIAL_QUESTION")
    clauses = [x.strip() for x in CLAUSE_RE.split(question.strip()) if x.strip()]
    # Strictly preserve the whole question as well: a single clause may contain
    # interacting topics (e.g. ISA transfer versus foreign-dividend taxation).
    facets = _facets(question)
    scores = {}
    for domain in policy["routes"]:
        rid = domain["route_id"]
        scores[rid] = score(question,domain) + (BOOST[rid] if rid in facets else 0)
    order = sorted(scores, key=lambda x:(-scores[x],x))
    candidates = [x for x in order if scores[x] > 0]
    out = candidates[:3]
    multi = len(candidates)>1 and (scores[candidates[0]]-scores[candidates[1]]<=5)
    if len(facets)>1:
        for rid in facets:
            if rid not in out:
                out.append(rid)
    # Factor retrieval in a stable, ranked order; no assumed exact graph
    # similarity, evidence date, personal allocation, or financial fact approval.
    out = sorted(set(out), key=lambda x:(-scores[x],x))[:5]
    source_claims = []
    for rid in out:
        route = next(x for x in policy["routes"] if x["route_id"]==rid)
        for cid in route["claim_ids"]:
            if cid not in source_claims:
                source_claims.append(cid)
    q = question.casefold()
    personal = any(x.casefold() in q for x in PERSONAL_TERMS)
    guaranteed = any(x.casefold() in q for x in GUARANTEE_TERMS)
    return {
        "schema":"IRE_V5_P0_MEANING_PLAN_V1",
        "question":question, "clauses":clauses,
        "detected_facets":list(facets.values()),
        "numeric_tokens":ROLE_RE.findall(question),
        "primary_domain":out[0] if out else None,
        "related_domains":out,
        "scores":{x:scores[x] for x in out},
        "multi_domain_or_ambiguous":multi or len(facets)>1,
        "candidate_claim_ids":source_claims,
        "facts_verified":False,
        "domain_confidence_calibrated":False,
        "human_semantics_required_for_ambiguous_or_financial_rules":True,
        "personal_action_approved":False,
        "requires_user_suitability_check":personal,
        "guaranteed_return_claim_detected":guaranteed,
    }

def audit(root: Path) -> dict:
    root=Path(root)
    policy=load_policy(root)
    sample=json.loads((root/"ire/v5/advisory_integration/LIVE_VALIDATION_SCENARIOS_20261105.json").read_text("utf-8"))
    outcome=[]
    for row in sample["holdout_set"]:
        p=parse(row["question"],policy)
        outcome.append({"case_id":row["case_id"],
                        "expected":row["expected_route_id"],
                        "actual":p["primary_domain"],
                        "retrieved":row["expected_route_id"] in p["related_domains"]})
    return {"schema":"IRE_V5_P0_AUDIT_V1",
            "known_prior_holdout_cases":len(outcome),
            "primary_correct":sum(x["actual"]==x["expected"] for x in outcome),
            "domain_recall_at_up_to_five":sum(x["retrieved"] for x in outcome),
            "not_fresh_blind_data":True,
            "production_financial_advice_validated":False,
            "cases":outcome}

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--question")
    a=p.parse_args()
    policy=load_policy(a.root)
    result=parse(a.question,policy) if a.question else audit(a.root)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
