"""P2: deterministic scenario comparisons conditional on exact available inputs.

Never optimize a personal portfolio, issue orders or invent market forecasts.
A numerical result is only an illustrative comparison under supplied inputs;
legal/tax inputs are not assumed and incomplete items remain unpriced.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

from .advisory_evidence import plan as evidence_plan
from .advisory_semantic import parse as semantic_plan
from .advisory60 import load_policy

FIXTURES = Path("ire/v5/advisory_integration/P2_CONDITIONAL_COMPARISON_CASES_20261105.json")

class DecisionP2Error(ValueError):
    pass

def need(ok: bool, code: str):
    if not ok:
        raise DecisionP2Error(code)

def number(v, name: str, min_value: float = 0.0) -> float:
    need(type(v) in (int,float) and math.isfinite(v) and v>=min_value,
         "P2_INVALID_FINANCIAL_INPUT_" + name)
    return float(v)

def compare(root: Path, question: str, scenario: dict) -> dict:
    root=Path(root)
    policy=load_policy(root)
    semantic=semantic_plan(question,policy)
    kind=scenario.get("kind")
    need(kind in {"ISA_TRANSFER","RETIREMENT_GAP","ETF_TOTAL_RETURN",
                  "ALLOCATION_DRIFT"},"P2_UNKNOWN_COMPARISON_KIND")
    options=scenario.get("options")
    need(isinstance(options,list) and 1<=len(options)<=5,
         "P2_OPTIONS_REQUIRED")
    need(len({x.get("id") for x in options})==len(options),
         "P2_DUPLICATE_OPTION")
    evidence=evidence_plan(question,root)
    results=[]
    unknown=[]
    if kind=="ISA_TRANSFER":
        fid={x["fact_id"] for x in evidence["direct_scoped_evidence"]}
        need({"P1-ISA-60D","P1-ISA-TRANSFER-10PCT"}<=fid,
             "P2_ISA_LAW_NOT_ACTUALLY_RETRIEVED")
        rate=number(scenario.get("assumed_income_tax_credit_rate"),"rate")
        need(rate in (0.12,0.15),"P2_UNVERIFIED_TAX_RATE")
        tax_remaining=scenario.get("remaining_assessable_income_tax_krw")
        if tax_remaining is not None:
            tax_remaining=number(tax_remaining,"tax_remaining")
        for option in options:
            transfer=number(option.get("transfer_krw"),"transfer")
            days=number(option.get("days_after_isa_expiry"),"days")
            eligible=0.1*transfer if days<=60 else 0
            eligible=min(eligible,3000000)
            potential=eligible*rate
            capped=(min(potential,tax_remaining) if tax_remaining is not None
                    else None)
            results.append({"option_id":option["id"],
                            "isa_transfer_krw":transfer,
                            "days_after_expiry":days,
                            "additional_credit_eligible_contribution_krw":eligible,
                            "hypothetical_income_tax_credit_before_tax_cap_krw":potential,
                            "hypothetical_credit_after_supplied_remaining_tax_cap_krw":capped,
                            "benefit_timing_condition_met":days<=60,
                            "estimated_refund_guaranteed":False})
        unknown=["계좌 해지/만기 실제 처리일·이체일",
                 "현재 다른 공제 및 지방소득세",
                 "연금계좌의 중도인출 제약·현금수요",
                 "세액공제 결정세액과 실제 세제 적용자격"]
    elif kind=="RETIREMENT_GAP":
        pension=number(scenario.get("monthly_pension_krw"),"pension")
        income=number(scenario.get("other_monthly_income_krw"),"other_income")
        for option in options:
            expense=number(option.get("monthly_expense_krw"),"expense")
            gap=max(expense-pension-income,0)
            results.append({"option_id":option["id"],
                            "monthly_unfunded_spending_krw":gap,
                            "annual_unfunded_spending_krw":gap*12,
                            "retirement_capital_required":None})
        unknown=["소득세와 건강보험료","물가상승·인출기간",
                 "투자수익률의 순서 위험","기타 연금·대출·의료지출"]
    elif kind=="ETF_TOTAL_RETURN":
        for option in options:
            entry=number(option.get("initial_value_krw"),"initial",1.0)
            ending=number(option.get("ending_market_value_krw"),"ending")
            dividends=number(option.get("cash_distributions_krw"),"distributions")
            external_fees=number(option.get("separately_paid_fees_krw"),"outside_fees")
            net=ending+dividends-external_fees-entry
            results.append({"option_id":option["id"],
                            "net_total_return_krw_pre_tax":net,
                            "net_total_return_pct_pre_tax":net/entry*100,
                            "cash_distribution_krw":dividends,
                            "cash_distribution_not_guaranteed_profit":True})
        unknown=["실제 양도·분배 과세","시세/NAV 시각 및 유동성",
                 "NAV·시장가격에 이미 포함된 운용보수와 외부 납부 비용의 중복 차감 방지"]
    else:
        target=number(scenario.get("target_equity_pct"),"target")
        need(target<=100,"P2_INVALID_TARGET_WEIGHT")
        for option in options:
            current=number(option.get("current_equity_pct"),"current_weight")
            need(current<=100,"P2_INVALID_CURRENT_WEIGHT")
            results.append({"option_id":option["id"],
                            "equity_weight_drift_percentage_points":current-target,
                            "above_target":current>target,
                            "trade_size_krw":None})
        unknown=["포트폴리오 총액과 비상현금","증권 종류별 비용·세금",
                 "정한 목표비중의 적합성·타 상품 위험과 중복",
                 "새 납입금 반영 가능성"]
    return {"schema":"IRE_V5_P2_CONDITIONAL_COMPARISON_V1",
            "kind":kind,"question":question,
            "domain_candidates":semantic["related_domains"],
            "scoped_atomic_fact_ids":[x["fact_id"] for x in evidence["direct_scoped_evidence"]],
            "results":results,"required_unpriced_factors":unknown,
            "recommendation_status":"TRADEOFF_ONLY_NOT_PERSONAL_ACTION",
            "default_win_or_trade_instruction":None,
            "financial_rule_currently_reopened_by_python":False,
            "personalized_trade_authorized":False,
            "future_returns_guaranteed":False,
            "cash_flow_or_tax_suitability_requires_chat_review":True}

def audit(root: Path) -> dict:
    f=json.loads((Path(root)/FIXTURES).read_text("utf-8"))
    need(f.get("schema")=="IRE_V5_P2_EXAMPLE_COMPARISONS_V1"
         and f.get("not_independent_personal_advice_validation") is True
         and len(f.get("cases",[]))==5,"P2_FIXTURE_NOT_PRESERVED")
    evaluated=[]
    for c in f["cases"]:
        out=compare(root,c["question"],c["scenario"])
        need(len(out["results"])==len(c["expected"])
             and not out["personalized_trade_authorized"]
             and out["recommendation_status"]=="TRADEOFF_ONLY_NOT_PERSONAL_ACTION",
             "P2_UNSAFE_COMPARISON_OUTPUT")
        for row,want in zip(out["results"],c["expected"]):
            need(row["option_id"]==want["id"],"P2_OPTION_ALIGNMENT")
            for k,v in want["metrics"].items():
                got=row[k]
                need(got is not None and math.isclose(got,v,rel_tol=1e-10,abs_tol=1e-6),
                     "P2_BAD_CALCULATION_"+c["case_id"]+"_"+k)
        evaluated.append(c["case_id"])
    return {"schema":"IRE_V5_P2_AUDIT_V1",
            "conditional_scenario_templates":4,
            "synthetic_comparison_cases_passed":len(evaluated),
            "live_market_quotes_used":0,
            "future_return_assumptions_invented":0,
            "personal_trade_recommendations_authorized":0,
            "full_investor_suitability_measured":False,
            "cases":evaluated}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path("."))
    a=p.parse_args()
    print(json.dumps(audit(a.root),ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    main()
