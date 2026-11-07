"""Reproducible current-chat advisory60 validation; not a blind answer-quality exam.

Routes are executed by the actual V5 Python router. This gate verifies source IDs,
URL scope, answer caveats, arithmetic and fail-closed decisions offline. Official
page content was checked in the active ChatGPT conversation on 2026-11-05; GitHub
CI does not independently re-fetch, snapshot or attest those external sources.
"""
from __future__ import annotations
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
import argparse
import json
import math

from .advisory60 import load_policy, resolve

SCENARIOS = Path("ire/v5/advisory_integration/LIVE_VALIDATION_SCENARIOS_20261105.json")
FACTS = Path("ire/v5/advisory_integration/CHAT_FACT_CHECK_20261105.json")
HOSTS = {
    "www.nts.go.kr", "nts.go.kr", "sc.nts.go.kr",
    "www.nps.or.kr", "www.krx.co.kr", "open.krx.co.kr", "m.krx.co.kr",
    "kind.krx.co.kr", "www.investor.gov", "m.shinhansec.com",
    "www.fsc.go.kr", "www.law.go.kr",
}
VALID_STATES = {"MATCHED_WITH_CONDITIONS", "CALCULATION_ONLY_CONDITIONAL"}

class Advisory60ValidationError(ValueError):
    pass

def must(ok: bool, code: str) -> None:
    if not ok:
        raise Advisory60ValidationError(code)

def read(root: Path, relative: Path) -> dict:
    return json.loads((root / relative).read_text(encoding="utf-8"))

def calculation(row: dict) -> float:
    a = row["inputs"]
    k = row["kind"]
    if k == "PENSION_CREDIT_15_PCT":
        return a["deductible_krw"] * a["income_tax_rate"]
    if k == "RETIREMENT_MONTHLY_GAP":
        return a["monthly_expense_krw"] - a["monthly_pension_krw"]
    if k == "ALLOCATION_DRIFT_PERCENTAGE_POINTS":
        return a["current_pct"] - a["target_pct"]
    if k == "ONE_YEAR_BOND_SIMPLE_TOTAL_YIELD_PCT":
        must(a["holding_years"] == 1, "ADVISORY60_BOND_HOLD_ASSUMPTION_CHANGED")
        return (a["face_krw"] * a["coupon_rate"]
                + a["face_krw"] - a["purchase_krw"]) / a["purchase_krw"] * 100
    if k == "ANNUAL_DISTRIBUTION_FROM_MONTHLY":
        return a["monthly_krw"] * a["months"]
    raise Advisory60ValidationError("ADVISORY60_UNKNOWN_CALCULATION_KIND")

def verify(root: Path, scenarios: dict | None = None,
           facts: dict | None = None) -> dict:
    root = Path(root)
    policy = load_policy(root)
    scenarios = read(root, SCENARIOS) if scenarios is None else scenarios
    facts = read(root, FACTS) if facts is None else facts
    must(scenarios.get("schema") == "IRE_V5_ADVISORY60_VALIDATION_SCENARIOS_V1"
         and scenarios.get("as_of") == "2026-11-05"
         and scenarios.get("suite_author") == "CHATGPT_CURRENT_TURN_NOT_EXTERNAL_BLIND"
         and scenarios.get("baseline_frozen_before_patch") is True
         and scenarios.get("original_router_sha") ==
             "c202eb2661633d2919283e04fe033a8112b2ecee"
         and scenarios.get("baseline_new_questions_correct") == 11
         and scenarios.get("baseline_new_questions_total") == 20
         and scenarios.get("holdout_not_used_to_tune_keywords") is True
         and scenarios.get("model_generated_response_accuracy_evaluation") is False,
         "ADVISORY60_VALIDATION_SUITE_FALSE_PROVENANCE")
    repair = scenarios.get("repair_set", [])
    holdout = scenarios.get("holdout_set", [])
    must(len(repair) == 20 and len(holdout) == 16,
         "ADVISORY60_QUESTION_SAMPLE_CHANGED")
    ids = set()
    questions = set()
    outcomes = {}
    for name, rows in (("repair", repair), ("holdout", holdout)):
        ok = 0
        mismatched = []
        for row in rows:
            cid = row["case_id"]
            q = row["question"]
            must(cid not in ids and q not in questions and
                 cid.startswith("V" if name == "repair" else "H") and
                 isinstance(q, str) and len(q) >= 18,
                 "ADVISORY60_DUPLICATE_OR_INVALID_NEW_QUESTION")
            ids.add(cid)
            questions.add(q)
            out = resolve(policy, q)
            want = row["expected_route_id"]
            must(want in {r["route_id"] for r in policy["routes"]},
                 "ADVISORY60_INVALID_EXPECTED_DOMAIN")
            if out.get("route_id") == want:
                ok += 1
            else:
                mismatched.append({
                    "case_id": cid, "expected_route_id": want,
                    "actual_route_id": out.get("route_id", "NO_ROUTE"),
                })
            must(out.get("personal_action_approved") is False
                 and out.get("current_financial_rule_live_verified") is False
                 and not out.get("trade_or_amount_recommended", False),
                 "ADVISORY60_UNSAFE_RESPONSE_PROMOTION")
        outcomes[name] = {"correct": ok, "total": len(rows),
                          "misses": mismatched}
    must(outcomes["repair"]["correct"] == 20,
         "ADVISORY60_NEW_QUESTION_ROUTE_REGRESSION")
    must(outcomes["holdout"]["correct"] >= 12,
         "ADVISORY60_NEW_HOLDOUT_BELOW_OBSERVED_FLOOR")
    must(facts.get("schema") == "IRE_V5_ADVISORY60_CHAT_FACT_CHECK_V1"
         and facts.get("as_of") == "2026-11-05"
         and facts.get("independent_blind_human_validation") is False
         and facts.get("original_private_SRT_rechecked_this_turn") is False
         and facts.get("model_api_used") is False
         and facts.get("live_chat_web_source_researched") is True
         and facts.get("answers_are_chat_authored_not_blind_gold") is True
         and facts.get("ci_cannot_reopen_or_attest_source_content") is True
         and facts.get("advice_authorized") is False,
         "ADVISORY60_UNEARNED_FINANCIAL_CERTIFICATION")
    source_map = {}
    for s in facts["sources"]:
        sid = s.get("source_id")
        url = urlparse(s.get("url", ""))
        must(isinstance(sid, str) and sid not in source_map
             and url.scheme == "https" and url.hostname in HOSTS
             and s.get("observed_at") == "2026-11-05"
             and s.get("review_mode") ==
                 "LIVE_CHAT_WEB_SOURCE_CONTENT_READ_NO_IMMUTABLE_SNAPSHOT"
             and s.get("independent_source_capture_attested") is False
             and len(s.get("narrow_scope", "")) >= 45,
             "ADVISORY60_FALSE_SOURCE_OR_DOMAIN_CERTIFICATION")
        source_map[sid] = s
    must(len(source_map) == facts.get("source_count") == 16,
         "ADVISORY60_OFFICIAL_SOURCE_CATALOG_INVALID")
    answers = facts["answers"]
    must(len(answers) == facts.get("answer_count") == 15,
         "ADVISORY60_CHAT_SOURCE_CHECK_COUNT_CHANGED")
    seen = set()
    resolved_refs = 0
    for a in answers:
        cid = a["case_id"]
        must(cid in {x["case_id"] for x in repair}
             and cid not in seen
             and isinstance(a.get("narrow_chat_answer"), str)
             and len(a["narrow_chat_answer"]) >= 85
             and a.get("answer_authorship") ==
                 "CHATGPT_ACTIVE_TURN_WITH_OFFICIAL_SOURCE_READING"
             and a.get("not_independent_model_grade") is True
             and a.get("personal_trade_or_allocation_approved") is False
             and a.get("review_state") in VALID_STATES,
             "ADVISORY60_UNSUPPORTED_ANSWER_APPROVAL")
        seen.add(cid)
        if a["review_state"] == "MATCHED_WITH_CONDITIONS":
            must(bool(a.get("source_ids")), "ADVISORY60_CITATION_MISSING")
        else:
            must(not a.get("source_ids"), "ADVISORY60_ARITHMETIC_ONLY_AS_SOURCED")
        for sid in a["source_ids"]:
            must(sid in source_map, "ADVISORY60_UNVERIFIED_SOURCE_REFERENCE")
            resolved_refs += 1
        must(all(term in a["narrow_chat_answer"]
                 for term in a["required_answer_terms"]),
             "ADVISORY60_ANSWER_REQUIRED_SCOPE_DROPPED")
    sums = facts.get("arithmetic_assertions", [])
    must(len(sums) == 5, "ADVISORY60_MATH_COVERAGE_INVALID")
    numeric_ids = set()
    for case in sums:
        cid = case["case_id"]
        must(cid in seen and cid not in numeric_ids,
             "ADVISORY60_MATH_CASE_ID_DUPLICATED_OR_UNREVIEWED")
        numeric_ids.add(cid)
        result = calculation(case)
        must(math.isfinite(result) and math.isclose(
            result, case["expected"], rel_tol=1e-10, abs_tol=1e-6),
            "ADVISORY60_MATH_MISMATCH_" + cid)
    # Safety beyond the 20+16 routing records; unknown domains cannot bypass
    # explicit personal instructions or promises of guaranteed returns.
    unknown = resolve(policy, "내 계좌 애완견 간식을 바로 주문해줘",
                      intent="personal_action")
    must(unknown["decision"] == "PERSONAL_ACTION_NO_RESEARCH_ROUTE"
         and not unknown["source_claim_ids"]
         and unknown["personal_action_approved"] is False,
         "ADVISORY60_PERSONAL_OUT_OF_SCOPE_NOT_BLOCKED")
    guaranteed = resolve(policy, "미상 기기에서 확정 수익을 약속해도 되나요?",
                         intent="guaranteed_return")
    must(guaranteed["decision"] == "REFUSE_UNSUPPORTED_GUARANTEE_NO_RESEARCH_ROUTE"
         and guaranteed["current_financial_rule_live_verified"] is False,
         "ADVISORY60_UNSUPPORTED_GUARANTEE_NOT_BLOCKED")
    must(resolve(policy, "월급 320만원, 고정비 240만원이면 처음 투자에 얼마를 써야 하나요?")[
         "decision"] == "PERSONAL_ACTION_NOT_AUTHORIZED_SHOW_CHECKS",
         "ADVISORY60_PERSONAL_AMOUNT_MISROUTED")
    return {"schema":"IRE_V5_ADVISORY60_VALIDATION_RESULT_V1",
            "baseline_route_correct":11, "baseline_route_total":20,
            "repaired_question_route_correct":outcomes["repair"]["correct"],
            "repaired_question_route_total":20,
            "untuned_holdout_route_correct":outcomes["holdout"]["correct"],
            "untuned_holdout_route_total":16,
            "untuned_holdout_misses":outcomes["holdout"]["misses"],
            "chat_authored_narrow_answers_source_checked":len(answers),
            "official_page_entries_reviewed_by_chat":len(source_map),
            "verified_external_source_references_in_chat_answers":resolved_refs,
            "independent_human_or_blind_answer_quality_verdict":False,
            "generative_model_accurate_advisory_rate_measured":False,
            "current_law_external_source_reopened_by_ci":False,
            "arithmetic_examples_checked":len(numeric_ids),
            "trading_and_personal_portfolio_advice_approved":0,
            "outcome":"CONDITIONAL_EDUCATION_SOURCE_MATCHED_ROUTING_GENERALIZATION_GAPS_REMAIN"}

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path("."))
    opts = p.parse_args()
    print(json.dumps(verify(opts.root), ensure_ascii=False, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
