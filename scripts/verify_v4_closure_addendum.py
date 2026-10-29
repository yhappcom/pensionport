#!/usr/bin/env python3
"""Recalculate all five source-limited V4 closure addenda; read-only.
Neither financial forecast nor legal or personal advice validation.
"""
import argparse
import copy
import json
import math
import sys
from pathlib import Path

ADDENDUM = "data/synthesis/investment_knowledge_v4/models/decision_models_001_005_closure_addendum_20261030.json"
MANIFEST = "data/synthesis/investment_knowledge_v4/reviews/v4_001_005_final_closure_20261030.json"
ORIGINAL_MANIFEST = "data/synthesis/investment_knowledge_v4/reviews/v4_001_005_deep_research_manifest_20261030.json"
IDS = ["F001_SEQUENCE_RISK","F002_DEBT_VS_INVEST","F003_IRP_DEFERRED_TAX_YEAR","F004_HOLD_VS_REPLACE","F005_EMERGENCY_RESERVE"]

class CheckFailure(ValueError):
    pass

def need(label, cond):
    if not cond:
        raise CheckFailure(label)

def approx(label,a,b,tol=1.01):
    need(label, isinstance(b,(int,float)) and not isinstance(b,bool)
         and math.isfinite(a) and math.isfinite(b) and abs(a-b)<=tol)

def calc(cases):
    need("case coverage exactly five and unique", [c["id"] for c in cases]==IDS)
    need("case-video fixed roster", [c["roster_no"] for c in cases]==[1,2,3,4,5])
    for c in cases:
        need("scenario labels", c.get("kind") and c.get("decision_cap","").startswith("L2"))
        need("source and limitation", c.get("external_primary_sources") and c.get("limits"))
    count=0
    x=cases[0]
    i=x["inputs"]
    need("yearly return multiset equal",sorted(x["hypothetical_paths"]["early_loss"])==sorted(x["hypothetical_paths"]["late_loss"]))
    for path,sequence in x["hypothetical_paths"].items():
        capital=i["initial_portfolio_krw"]
        depleted=None
        need("sequence length",len(sequence)==i["years"])
        need("one negative year",sum(z<0 for z in sequence)==i["negative_year_counts"])
        for yr,annual in enumerate(sequence,1):
            if capital < i["annual_fixed_draw_start_of_year_krw"] and depleted is None:
                depleted=yr
            capital=max(0,capital-i["annual_fixed_draw_start_of_year_krw"])*(1+annual)
            approx("yearly balance "+path+" year "+str(yr),round(capital),
                   x["outputs"][path]["balances_krw"][yr-1])
            count+=1
        need("exhaustion year "+path,depleted==x["outputs"][path]["year_exhausted"])
        approx("final balance "+path,round(capital),x["outputs"][path]["ending_balance_krw"])
        count+=2
    x=cases[1];i=x["inputs"];o=x["outputs"]
    avoided=i["allocation_krw"]*i["debt_simple_annual_rate"]
    invested=i["allocation_krw"]*i["investment_gross_return_assumption"]*(1-i["positive_investment_gain_tax_proxy"])
    approx("debt interest avoided",round(avoided),o["debt_interest_avoided_krw"])
    approx("invested net gain",round(invested),o["investment_after_tax_gain_krw"])
    approx("debt minus invest",round(avoided-invested),o["debt_minus_investment_net_benefit_krw"])
    approx("debt breakeven return",
           i["debt_simple_annual_rate"]/(1-i["positive_investment_gain_tax_proxy"]),
           o["breakeven_gross_investment_return"],1e-10)
    count+=4
    x=cases[2];i=x["inputs"]
    need("yearly case coverage",set(x["outputs"])==set(map(str,i["actual_pension_receipt_years"])))
    need("effective date","2026-01-01"==i["effective_from"])
    for year in i["actual_pension_receipt_years"]:
        taxrate=.7 if year<=10 else .6 if year<=20 else .5
        row=x["outputs"][str(year)]
        approx("IRP tax fraction "+str(year),taxrate,row["tax_fraction"],1e-10)
        approx("IRP numeric illustration "+str(year),i["hypothetical_outside_pension_tax_on_same_payment_krw"]*taxrate,row["illustrative_tax_krw"])
        count+=2
    x=cases[3];i=x["inputs"];o=x["outputs"]
    cash=i["current_liquidation_value_krw"]
    alternative=i["alternative_future_return"]
    fee=i["switch_one_way_cost_fraction"]
    approx("switch break even",(1-fee)*(1+alternative)-1,o["breakeven_old_equity_future_return"],1e-10)
    approx("replacement proceeds",round(cash*(1-fee)*(1+alternative)),o["replacement_terminal_krw"])
    need("hold scenario coverage",set(o["hold_terminals_krw"])==set(map(str,i["old_equity_future_returns"])))
    for r in i["old_equity_future_returns"]:
        approx("hold proceeds "+str(r),round(cash*(1+r)),o["hold_terminals_krw"][str(r)])
        count+=1
    count+=2
    x=cases[4];i=x["inputs"];o=x["outputs"]
    free=i["monthly_take_home_krw"]-i["monthly_essential_expenses_krw"]-i["monthly_debt_payment_krw"]
    need("cashflow supports reserve savings",0<i["monthly_emergency_fund_savings_krw"]<=free)
    approx("monthly free",free,o["monthly_available_cash_krw"])
    approx("residual cash",free-i["monthly_emergency_fund_savings_krw"],o["monthly_uncommitted_after_reserve_savings_krw"])
    need("reserve coverage",set(o["targets"])==set(map(str,i["expense_months"])))
    for months in i["expense_months"]:
        target=months*(i["monthly_essential_expenses_krw"]+i["monthly_debt_payment_krw"])
        years=math.ceil((target-i["initial_reserve_krw"])/i["monthly_emergency_fund_savings_krw"])
        approx("reserve target "+str(months),target,o["targets"][str(months)]["target_krw"])
        need("reserve duration "+str(months),years==o["targets"][str(months)]["months_to_build"])
        count+=2
    count+=2
    return count

def read(path):
    return json.loads(path.read_text(encoding="utf-8"),
                      parse_constant=lambda value: (_ for _ in ()).throw(CheckFailure("non-finite JSON")))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--self-test",action="store_true")
    opts=parser.parse_args()
    try:
        root=opts.root.resolve()
        add=read(root/ADDENDUM)
        need("schema",add["schema_version"]=="V4_001_005_BOUNDED_CLOSURE_ADDENDUM_1.0")
        count=calc(add["new_closure_cases"])
        if opts.self_test:
            bad=copy.deepcopy(add["new_closure_cases"])
            bad[0]["outputs"]["early_loss"]["ending_balance_krw"]+=10000
            try:calc(bad)
            except CheckFailure:pass
            else:raise CheckFailure("negative corruption test not rejected")
            try:calc(add["new_closure_cases"][:-1])
            except CheckFailure:pass
            else:raise CheckFailure("missing case not rejected")
            print(json.dumps({"status":"PASS","mode":"self_test","recomputed_checks":count,"negative_tests":2}))
            return 0
        manifest=read(root/MANIFEST)
        old=read(root/ORIGINAL_MANIFEST)
        need("five review count",len(old["video_reviews"])==len(manifest["scope_results"])==5)
        need("prior 9 preserved",old["count"]["simulated_models"]==add["historical_model_count"]==9)
        need("prior 62 preserved",old["count"]["existing_v3_claims"]==manifest["historical_evidence"]["original_v3_claims"]==62)
        need("addendum file path",manifest["addendum_model_file"]==ADDENDUM)
        need("five models",manifest["addendum_model_count"]==len(IDS))
        need("no additional claims",manifest["new_claims_added_to_original_ledger"]==0)
        need("no new approved videos",manifest["new_video_approvals"]==0)
        need("no real-life approvals",manifest["personalized_L3_approvals"]==manifest["implementation_L4_approvals"]==0)
        for item in manifest["scope_results"]:
            need("external OPEN listed",bool(item["items"]))
            need("action blocked",item["missing_proof_impact"]=="INVESTOR_ACTION_BLOCKED")
        print(json.dumps({"status":"PASS","mode":"repository","models_recalculated":len(IDS),
                          "scenario_checks":count,"source_manifest_checks":"PASS",
                          "limit":"synthetic arithmetic and cross-file consistency only"}))
        return 0
    except (ValueError,KeyError,TypeError,OSError,OverflowError,ZeroDivisionError,IndexError) as exc:
        print(json.dumps({"status":"FAIL","error":str(exc),"type":type(exc).__name__}))
        return 1

if __name__=="__main__":
    sys.exit(main())
