"""Advisory-level decision-support routing from 60 triaged legacy research claims.

No OpenAI API, personalized trade authorization, live law verification, or
independent blind scoring. The 60 records are NOT 60 approved financial facts.
Only the pre-existing 13 educational nodes may appear as previously reviewed
educational context with time, scope and current-source limitations.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
import re

from .legacy_consolidation_gate import verify as verify_legacy

CATALOG = Path("ire/v5/advisory_integration/decision_routes_20261105.json")
CASES = Path("ire/v5/advisory_integration/question_scenarios_20261105.json")
GRAPH = Path("ire/v5/advisory_knowledge/integrated_education13_20261104.json")
BATCHES = (
    Path("ire/v5/legacy_consolidation/batch_B01_C001_C020_20261105.json"),
    Path("ire/v5/legacy_consolidation/batch_B02_C021_C040_20261105.json"),
    Path("ire/v5/legacy_consolidation/batch_B03_C041_C060_20261105.json"),
)
TRIAGE = {
    "STRATEGY_CONTEXT_ONLY",
    "GENERAL_EDUCATION_LINK_CANDIDATE",
    "TIME_SENSITIVE_EVIDENCE_RECHECK",
    "SOURCE_LIMITED_NOT_FACT_APPROVED",
}
INTENTS = {"general_education", "decision_support", "personal_action",
           "guaranteed_return"}
PERSONAL_TERMS = (
    "내 계좌", "제 계좌", "내 포트폴리오", "제 포트폴리오",
    "매수해줘", "매도해줘", "사야 하나", "사야하나", "팔아야 하나",
    "팔까요", "지금 매수", "지금 사", "얼마 넣", "매수 비중",
    "투자 비중 추천", "추천해줘", "종목 추천", "몇 % 매수",
)
GUARANTEE_TERMS = (
    "원금보장", "원금 보장", "확정 수익", "확정수익", "반드시 수익",
    "무조건 수익", "절대 손실없", "손실 없이", "100% 수익 보장",
)
BLOCKED_GRAPH_LINKS = {
    ("GOMHEE-C33", "EDU-KR-ISA-TO-PENSION-2026-01"),
    ("GOMHEE-C42", "EDU-KR-ISA-TO-PENSION-2026-01"),
    ("GOMHEE-C42", "EDU-KR-PRIVATE-PENSION-1500-2026-01"),
    ("GOMHEE-C52", "EDU-GENERAL-DCA-ARITH-01"),
    ("GOMHEE-C26", "EDU-ETF-NAV-TRACKING"),
}

class Advisory60Error(ValueError):
    pass

def demand(ok: bool, code: str):
    if not ok:
        raise Advisory60Error(code)

def read(root: Path, path: Path) -> dict:
    return json.loads((Path(root) / path).read_text(encoding="utf-8"))

def score(question: str, route: dict) -> int:
    q = question.casefold()
    return sum(5 if len(k) >= 5 else 4 if len(k) >= 3 else 3
               for k in route["terms"] if k.casefold() in q)

def load_policy(root: Path, catalog: dict | None = None) -> dict:
    root = Path(root)
    verify_legacy(root)
    c = read(root, CATALOG) if catalog is None else catalog
    suite = read(root, CASES)
    graph = read(root, GRAPH)
    demand(
        c.get("schema") == "IRE_V5_ADVISORY60_DECISION_ROUTES_V1"
        and c.get("as_of") == "2026-11-05"
        and c.get("source_batch_ids") == ["B01", "B02", "B03"]
        and c.get("approved_personal_advice_items") == 0
        and c.get("new_financial_fact_approvals") == 0
        and c.get("research_claims_are_not_verified_current_facts") is True
        and c.get("read_time_live_official_sources_required_for_personal_regulation") is True
        and c.get("independent_blind_test_required") is False,
        "ADVISORY60_NO_UNEARNED_FACT_OR_ADVICE_CERTIFICATION")
    routes = c.get("routes")
    demand(isinstance(routes, list) and len(routes) == c.get("route_count") == 15,
           "ADVISORY60_ROUTE_CATALOG_INVALID")
    claims = {}
    for batch in BATCHES:
        data = read(root, batch)
        for row in data["records"]:
            cid = row["claim_id"]
            demand(cid not in claims
                   and row.get("research_triage") in TRIAGE
                   and row.get("chat_evidence_fact_approved_this_batch") is False
                   and row.get("personal_investment_advice_approved") is False
                   and row.get("official_rule_current_source_verified_this_batch") is False
                   and row.get("original_srt_full_cue_coverage_reverified_this_batch") is False,
                   "ADVISORY60_SOURCE_CLAIM_FALSELY_APPROVED")
            claims[cid] = row
    demand(len(claims) == 60 and
           set(claims) ==
           {f"GOMHEE-C{i:02d}" for i in range(1, 61)},
           "ADVISORY60_NOT_EXACTLY_FIRST_60_SOURCE_CLAIMS")
    nodes = {n["knowledge_id"]: n for n in graph["nodes"]}
    demand(len(nodes) == 13, "ADVISORY60_EXISTING_EDUCATION_GRAPH_CHANGED")
    covered = set()
    route_ids = set()
    for route in routes:
        rid = route.get("route_id")
        terms = route.get("terms", [])
        linked = route.get("claim_ids", [])
        verified_node_ids = route.get("education_node_ids", [])
        demand(isinstance(rid, str) and rid.isupper()
               and rid not in route_ids
               and isinstance(terms, list) and len(terms) >= 4
               and len(set(terms)) == len(terms)
               and all(isinstance(x, str) and len(x) >= 2 for x in terms)
               and isinstance(linked, list) and len(linked) >= 2
               and len(set(linked)) == len(linked)
               and set(linked) <= set(claims)
               and len(set(verified_node_ids)) == len(verified_node_ids)
               and set(verified_node_ids) <= set(nodes)
               and len(route.get("decision_frame", "")) >= 30
               and len(route.get("critical_limit", "")) >= 35
               and len(route.get("questions_to_resolve", [])) == 3,
               "ADVISORY60_ROUTE_OR_LIMIT_MISSING")
        # Catalog cannot assert that an already flagged false direct relation is
        # proof that a legacy source claim supports that educational node.
        for cid in linked:
            for nid in verified_node_ids:
                if (cid, nid) in BLOCKED_GRAPH_LINKS:
                    # The route may use other claims and the approved node as
                    # domain context, but never identify this as direct evidence.
                    demand(c.get("education_node_meaning_requires_direct_compatibility") is True,
                           "ADVISORY60_KNOWN_FALSE_GRAPH_LINK_REENABLED")
        covered.update(linked)
        route_ids.add(rid)
    demand(covered == set(claims), "ADVISORY60_COVERAGE_GAP")
    demand(
        suite.get("schema") == "IRE_V5_ADVISORY60_QUESTION_SCENARIOS_V1"
        and suite.get("authorship") == "CHATGPT_AUTHORED_NOT_INDEPENDENT_BLIND_GOLD"
        and suite.get("claims_about_model_answer_accuracy") is False
        and len(suite.get("cases", [])) == 20,
        "ADVISORY60_FALSE_INDEPENDENT_BENCHMARK")
    return {"routes": routes, "claims": claims, "nodes": nodes,
            "cases": suite["cases"], "covered_claim_ids": covered}

def resolve(policy: dict, question: str, intent: str = "general_education",
            as_of: str = "2026-11-05") -> dict:
    demand(intent in INTENTS, "ADVISORY60_UNKNOWN_INTENT")
    demand(type(question) is str and 6 <= len(question.strip()) <= 2000,
           "ADVISORY60_INVALID_QUESTION")
    # The software is a deterministic offline decision framework, not a
    # substitute for official regulation checks or a personal fiduciary.
    demand(as_of == "2026-11-05", "ADVISORY60_HISTORICAL_BASELINE_RECHECK_REQUIRED")
    ranked = sorted(((score(question, x), x["route_id"], x)
                     for x in policy["routes"]),
                    key=lambda x: (-x[0], x[1]))
    if ranked[0][0] <= 0:
        return {"schema": "IRE_V5_ADVISORY60_DECISION_V1",
                "decision": "NO_SUPPORTED_RESEARCH_ROUTE",
                "question": question, "as_of": as_of,
                "source_claim_ids": [], "education_nodes": [],
                "personal_action_approved": False,
                "current_financial_rule_live_verified": False,
                "reason": "60개 연구 주제와 연결되지 않는 질문. 근거·상품·제도 검색 없이 자문 내용을 생성하지 않음"}
    primary = ranked[0][2]
    matches = primary["claim_ids"]
    # A public-study pointer is never new approval, even if legacy confidence
    # was high or the historic 13-node graph contains a topical link.
    source_rows = [{
        "claim_id": cid,
        "source_video_ids": [v["video_id"] for v in policy["claims"][cid]["source_videos"]],
        "triage": policy["claims"][cid]["research_triage"],
        "new_financial_fact_approved": False,
        "unverified_original_full_transcript_this_batch": True,
    } for cid in matches]
    history = [{
        "knowledge_id": nid,
        "previously_reviewed_educational_statement":
            policy["nodes"][nid]["safe_general_statement"],
        "critical_scope_and_exceptions":
            policy["nodes"][nid]["critical_scope_and_exceptions"],
        "historical_review_as_of": "2026-11-04",
        "updated_law_verified_in_this_request": False,
        "not_directly_certified_by_route_claims": True,
    } for nid in primary["education_node_ids"]]
    unsafe_guarantee = intent == "guaranteed_return" or any(
        t.casefold() in question.casefold() for t in GUARANTEE_TERMS)
    personal = intent == "personal_action" or any(
        t.casefold() in question.casefold() for t in PERSONAL_TERMS)
    if unsafe_guarantee:
        decision = "REFUSE_GUARANTEED_RETURN_AND_SHOW_FRAMEWORK"
    elif personal:
        decision = "PERSONAL_ACTION_NOT_AUTHORIZED_SHOW_CHECKS"
    else:
        decision = "CONDITIONAL_EDUCATIONAL_DECISION_SUPPORT"
    return {
        "schema": "IRE_V5_ADVISORY60_DECISION_V1",
        "question": question,
        "as_of": as_of,
        "intent": intent,
        "decision": decision,
        "route_id": primary["route_id"],
        "topic": primary["title"],
        "decision_frame": primary["decision_frame"],
        "questions_to_resolve": primary["questions_to_resolve"],
        "critical_limit": primary["critical_limit"],
        "source_claim_ids": matches,
        "sources": source_rows,
        "education_nodes": history,
        "source_count_not_independent_confirmation": len(matches),
        "active_chat_original_and_regulation_evidence_required": True,
        "current_financial_rule_live_verified": False,
        "investment_risk_and_tax_inputs_needed": True,
        "personal_action_approved": False,
        "trade_or_amount_recommended": False,
        "live_security_quote_provided": False,
        "model_generated_personal_advice": False,
        "independent_blind_accuracy_confirmed": False,
    }

def audit(root: Path, catalog: dict | None = None) -> dict:
    policy = load_policy(root, catalog)
    results = []
    by_route = Counter()
    for case in policy["cases"]:
        demand(case.get("intent") == "general_education",
               "ADVISORY60_CASE_INTENT_UNSAFE")
        out = resolve(policy, case["question"], case["intent"])
        demand(out.get("route_id") == case.get("expected_route_id"),
               "ADVISORY60_CASE_ROUTE_MISS_" + case["case_id"])
        demand(out["source_claim_ids"]
               and all(not x["new_financial_fact_approved"] for x in out["sources"])
               and not out["personal_action_approved"]
               and not out["current_financial_rule_live_verified"],
               "ADVISORY60_CASE_UNSAFE_PROMOTION_" + case["case_id"])
        by_route[out["route_id"]] += 1
        results.append({"case_id": case["case_id"], "route_id": out["route_id"],
                        "safe_source_trace": True})
    demand(len(by_route) == len(policy["routes"]) == 15,
           "ADVISORY60_NOT_ALL_DECISION_DOMAINS_TESTED")
    stress = (
        ("ISA 만기자금 연금전환 무조건 원금 보장되나요", "REFUSE_GUARANTEED_RETURN_AND_SHOW_FRAMEWORK"),
        ("내 포트폴리오 자산배분 목표비중 추천해줘", "PERSONAL_ACTION_NOT_AUTHORIZED_SHOW_CHECKS"),
        ("지금 달러 매수해줘 환율", "PERSONAL_ACTION_NOT_AUTHORIZED_SHOW_CHECKS"),
        ("커버드콜 8% 인출률은 안전한가요", "CONDITIONAL_EDUCATIONAL_DECISION_SUPPORT"),
    )
    for q, expected in stress:
        demand(resolve(policy, q)["decision"] == expected,
               "ADVISORY60_SAFETY_STRESS_MISCLASSIFICATION")
    demand(resolve(policy, "오늘 영화관 상영 시간표")["decision"]
           == "NO_SUPPORTED_RESEARCH_ROUTE",
           "ADVISORY60_UNKNOWN_QUERY_GUESSED")
    return {"schema":"IRE_V5_ADVISORY60_AUDIT_V1",
            "legacy_claims_traced":len(policy["claims"]),
            "legacy_claims_promoted_to_new_financial_fact":0,
            "previously_verified_education_nodes_available":len(policy["nodes"]),
            "decision_domains":len(policy["routes"]),
            "question_scenarios_routed":len(results),
            "question_scenarios_tested":len(policy["cases"]),
            "safety_stress_questions":len(stress)+1,
            "independent_blind_human_accuracy_test":False,
            "actual_model_advisory_answer_accuracy_test":False,
            "official_law_live_researched_by_ci":False,
            "personalized_financial_trade_authorized":False,
            "stage":"ADVISORY_DECISION_SUPPORT_BETA_NO_PERSONAL_TRADE_GO",
            "scenarios":results}

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--question")
    p.add_argument("--intent", choices=sorted(INTENTS), default="general_education")
    args=p.parse_args()
    result = (resolve(load_policy(args.root), args.question, args.intent)
              if args.question else audit(args.root))
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
