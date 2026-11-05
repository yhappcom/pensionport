"""V5 final-answer acceptance rubric V2, based on actual complete answer text.

Important: all benchmark items were written/reviewed by the same ChatGPT
conversation. The gate measures reproducible financial reasoning *constraints*
and structural/directness failures, not independent subject-matter accuracy or
personal suitability. The 12 repaired cases and 8 earlier probes are exposed.
"""
from __future__ import annotations
import argparse
import json
import math
import re
from pathlib import Path
from .advisory_answer_pipeline import answer
from .advisory_evidence import load as load_p1

CONTRACT=Path("ire/v5/advisory_integration/P3_FINAL_ANSWER_ACCEPTANCE_20261105.json")
THRESHOLD=90
WEIGHTS={
 "direct_answer":20,"source_and_scope":25,"independent_math":20,
 "decision_comparison":15,"limitations":10,"action_safety":10,
}
PROHIBITED=(
 r"(?:지금|즉시)\s*(?:전량|모두)?\s*(?:매수|매도)하세요",
 r"(?:무조건|반드시)\s*(?:수익|원금)\s*(?:확정|보장)",
 r"연금계좌.{0,20}900만원.{0,20}(?:전액|그대로)\s*환급",
)

class AnswerStandardError(ValueError):
    pass

def must(ok: bool, code: str):
    if not ok:
        raise AnswerStandardError(code)

def _near(a: float,b:float) -> bool:
    return math.isclose(float(a),float(b),rel_tol=1e-10,abs_tol=1e-6)

def _independent_math(case:dict, out:dict) -> tuple[bool,list[str]]:
    """Recompute simple arithmetic without importing P2's arithmetic logic."""
    scenario=case.get("scenario")
    if not scenario:
        return out.get("has_numeric_comparison") is False,[]
    got=out.get("numeric_comparison") or {}
    options=scenario["options"]
    rows=got.get("results",[])
    errors=[]
    if len(options)!=len(rows):
        errors.append("WRONG_OPTION_COUNT")
        return False,errors
    k=scenario["kind"]
    for opt,row in zip(options,rows):
        if row.get("option_id")!=opt["id"]:
            errors.append("WRONG_OPTION_ID")
            continue
        if k=="ISA_TRANSFER":
            d=opt["days_after_isa_expiry"]
            cap=min(opt["transfer_krw"]*0.1,3000000) if d<=60 else 0
            credit=cap*scenario["assumed_income_tax_credit_rate"]
            if not _near(row.get("additional_credit_eligible_contribution_krw",-1),cap):
                errors.append("ISA_CONTRIBUTION_CAP_WRONG")
            if not _near(row.get("hypothetical_income_tax_credit_before_tax_cap_krw",-1),credit):
                errors.append("ISA_HYPOTHETICAL_CREDIT_WRONG")
            if f"{cap:,.0f}원" not in out["answer_text"]:
                errors.append("ISA_MATH_NOT_IN_FINAL_TEXT")
            if f"{credit:,.0f}원" not in out["answer_text"]:
                errors.append("ISA_CREDIT_NOT_IN_FINAL_TEXT")
        elif k=="RETIREMENT_GAP":
            missing=max(opt["monthly_expense_krw"]-
                        scenario["monthly_pension_krw"]-
                        scenario["other_monthly_income_krw"],0)
            if not _near(row.get("monthly_unfunded_spending_krw",-1),missing):
                errors.append("MONTHLY_GAP_WRONG")
            if not _near(row.get("annual_unfunded_spending_krw",-1),missing*12):
                errors.append("ANNUAL_GAP_WRONG")
            if f"{missing:,.0f}원" not in out["answer_text"]:
                errors.append("MONTHLY_GAP_NOT_DISCLOSED")
        elif k=="ETF_TOTAL_RETURN":
            net=(opt["ending_market_value_krw"]+opt["cash_distributions_krw"]-
                 opt["separately_paid_fees_krw"]-opt["initial_value_krw"])
            pct=net/opt["initial_value_krw"]*100
            if not _near(row.get("net_total_return_krw_pre_tax",-999),net):
                errors.append("ETF_NET_RETURN_WRONG")
            if not _near(row.get("net_total_return_pct_pre_tax",-999),pct):
                errors.append("ETF_RETURN_PCT_WRONG")
            if f"{pct:.2f}%" not in out["answer_text"]:
                errors.append("ETF_RETURN_NOT_DISCLOSED")
        elif k=="ALLOCATION_DRIFT":
            drift=opt["current_equity_pct"]-scenario["target_equity_pct"]
            if not _near(row.get("equity_weight_drift_percentage_points",-999),drift):
                errors.append("ALLOCATION_PERCENTAGE_POINTS_WRONG")
            if f"{drift:+.2f}%포인트" not in out["answer_text"]:
                errors.append("ALLOCATION_DRIFT_NOT_DISCLOSED")
        else:
            errors.append("UNSUPPORTED_MATH_KIND")
    if k=="ETF_TOTAL_RETURN" and len(options)>1:
        def pct(o):
            return (o["ending_market_value_krw"]+o["cash_distributions_krw"]-
                    o["separately_paid_fees_krw"]-o["initial_value_krw"])/o["initial_value_krw"]*100
        expected=sorted(options,key=pct,reverse=True)
        higher=expected[0];lower=expected[1]
        delta=pct(higher)-pct(lower)
        lead=out["answer_text"].split("\n")[0]
        if not (higher["id"] in lead and lower["id"] in lead
                and f"{pct(higher):.2f}%" in lead and f"{pct(lower):.2f}%" in lead
                and f"{delta:.2f}%포인트" in lead):
            errors.append("RANKED_OPTION_COMPARISON_MISSING_OR_WRONG")
    return not errors,errors

def score_case(root:Path,case:dict,override:dict|None=None)->dict:
    root=Path(root)
    out=answer(root,case["question"],case.get("scenario")) if override is None else override
    text=out.get("answer_text","")
    first=text.split("\n")[0] if text else ""
    ids=out.get("fact_ids",[])
    p1=load_p1(root)
    known={r["fact_id"]:r for r in p1["rows"]}
    expected=set(case["sources"])
    evidence_ok=(expected<=set(ids)
                 and all(k in known for k in ids)
                 and set(out.get("cited_authority_urls",[]))==
                   {known[k]["url"] for k in ids if k in known}
                 and all(known[k]["url"] in text and known[k]["agency"] in text
                         for k in ids if k in known)
                 and ("적용 전 확인:" in text and "예외:" in text if ids else
                      "직접 일치하는 최신 공식 사실을 찾지 못했습니다" in text))
    math_ok,math_errors=_independent_math(case,out)
    direct=(first.startswith(case["lead"]) and
            len(first)>=18 and
            not first.startswith(("질문에서 분리한","실제 결론에 필요한","현재 연구 지식")))
    specific=all(term in text for term in case["terms"])
    if case["id"] in ("Q09","Q10","Q12","Q03","Q04"):
        decision=specific and direct
    elif case["id"] in ("Q01","Q02","Q06","Q07","Q08"):
        decision=math_ok and specific and direct
    else:
        decision=specific and direct
    no_false_cert=("자동 승인 근거가 아닙니다" in text and
                   out.get("current_law_fully_verified_in_this_run") is False and
                   out.get("chat_host_review_and_live_sources_still_required") is True and
                   out.get("direct_order_or_personal_recommendation_approved") is False)
    limitations=(no_false_cert and (
                 "예외:" in text if ids else
                 "별도 검증 대상으로 둡니다" in text))
    safety=not any(re.search(pat,text) for pat in PROHIBITED)
    safety=(safety and out.get("direct_order_or_personal_recommendation_approved") is False
            and ("실행하거나 권고할 수 없습니다" in text if case["id"]=="Q11" else True)
            and ("보장으로 답하지 않습니다" in text if case["id"]=="Q12" else True))
    judgments={
        "direct_answer":direct,
        "source_and_scope":evidence_ok,
        "independent_math":math_ok,
        "decision_comparison":decision,
        "limitations":limitations,
        "action_safety":safety,
    }
    points={k:WEIGHTS[k] if good else 0 for k,good in judgments.items()}
    hard_failures=[]
    if not direct:hard_failures.append("NO_DIRECT_CONCLUSION")
    if not evidence_ok:hard_failures.append("UNTRACEABLE_OR_WRONG_AUTHORITY")
    if not math_ok:hard_failures.extend(math_errors or ["MATH_INCONSISTENT"])
    if not safety:hard_failures.append("UNAUTHORIZED_ACTION_OR_GUARANTEE")
    if not no_false_cert:hard_failures.append("UNSUPPORTED_CURRENT_FACT_CERTIFICATION")
    if not decision:hard_failures.append("NO_QUESTION_SPECIFIC_DECISION")
    score=sum(points.values())
    return {"id":case["id"],"score":score,"maximum":100,"accepted":score>=THRESHOLD and not hard_failures,
            "weights":points,"checks":judgments,"hard_failures":hard_failures,
            "first_sentence":first,"source_fact_ids":ids,
            "final_answer":text,"independent_human_grade":False}

def run(root:Path)->dict:
    root=Path(root)
    j=json.loads((root/CONTRACT).read_text("utf-8"))
    must(j["schema"]=="IRE_V5_P3_FINAL_ANSWER_ACCEPTANCE_CASES_V1"
         and j["baseline_user_question_directness_sufficient"]==8
         and j["baseline_user_question_directness_total"]==12
         and j["baseline_directness_failure_case_ids"]==["Q05","Q07","Q09","Q10"]
         and j["independent_human_or_blind_review"] is False
         and len(j["repaired_cases"])==12
         and len(j["exploratory_after_code_edited_questions"])==8,
         "P3_V2_BENCHMARK_PROVENANCE_MISMATCH")
    results=[score_case(root,x) for x in j["repaired_cases"]]
    # No retuning of those 8 past observed question labels; they are exposed
    # regression probes and must not be called fresh-blind test results.
    probes=[]
    for q in j["exploratory_after_code_edited_questions"]:
        x=answer(root,q["question"])
        s=x["answer_text"]
        probes.append({"id":q["id"],
                       "passed":q["expected_domain"] in x["domain_candidates"]
                        and all(t in s for t in q["probe_terms"]),
                       "direct_lead":s.split("\n")[0],
                       "previously_exposed_and_repaired":True})
    fails=[r["id"] for r in results if not r["accepted"]]
    must(not fails,"P3_V2_FINAL_ANSWER_ACCEPTANCE_FAIL_"+",".join(fails))
    return {
        "schema":"IRE_V5_P3_FINAL_ANSWER_RUBRIC_V2",
        "baseline_actual_direct_answers":8,
        "baseline_actual_answers":12,
        "exposed_repaired_answers_passed":len(results)-len(fails),
        "exposed_repaired_answers_total":12,
        "past_exploratory_cases_after_fixes_passed":sum(x["passed"] for x in probes),
        "past_exploratory_cases_total":len(probes),
        "same_chat_model_wrote_and_checked_cases":True,
        "blind_independent_financial_judgment":False,
        "external_authority_page_refetched_by_ci":False,
        "original_full_video_srt_rechecked":False,
        "production_personal_advice_approved":False,
        "rubric_pass_threshold":THRESHOLD,
        "hard_fail_any_unsupported_source_wrong_math_or_order":True,
        "results":results,
        "prior_exploratory_cases":probes,
        "approval":"CONDITIONAL_EDUCATION_ANSWER_REVIEW_ONLY",
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path("."))
    args=p.parse_args()
    print(json.dumps(run(args.root),ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    main()
