#!/usr/bin/env python3
"""Independent executable tests for #1-#10 V4 overlay; no network, orders or ledger writes."""
import argparse, copy, json, math, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MODEL="data/synthesis/investment_knowledge_v4/models/v4_001_010_supplemental_models_20261030.json"
AUDIT="data/synthesis/investment_knowledge_v4/reviews/v4_001_010_cross_video_final_audit_20261030.json"
LEGACY="data/synthesis/investment_knowledge_v4/models/decision_models_006_010_20261030.json"
PREV="data/synthesis/investment_knowledge_v4/reviews/v4_005_010_incremental_manifest_20261030.json"

class GateFailure(ValueError): pass
def require(v,msg):
 if not v: raise GateFailure(msg)
def close(x,y,msg,tolerance=1.1):
 require(isinstance(y,(int,float)) and math.isfinite(x) and abs(x-y)<=tolerance,msg)
def load(root,path):return json.loads((root/path).read_text(encoding="utf-8"))
def test_models(doc):
 models=doc["models"];require(len(models)==doc["integrity"]["model_count"]==6,"six model definitions required")
 ids=[x["id"] for x in models];require(len(set(ids))==6,"duplicate model ID")
 for m in models:
  require(m["formula"] and m["limits"] and m["videos"],"model assumptions missing")
 m=models[0];i=m["inputs"];o=m["result"];w=i["withdrawal_krw"];excluded=min(w,i["tax_excluded_verified_krw"]);other=w-excluded
 for actual,expected in [
   (sum(i[x] for x in ("tax_excluded_verified_krw","credited_principal_krw","investment_growth_krw","deferred_retirement_income_krw")),o["total_balance_krw"]),
   (excluded,o["withdrawn_tax_excluded_krw"]),
   (min(other,i["deferred_retirement_income_krw"]),o["withdrawn_deferred_retirement_income_krw"]),
   (other-min(other,i["deferred_retirement_income_krw"]),o["withdrawn_other_taxable_source_krw"]),
   (other*.055,o["illustrative_tax_5_5pct_krw"]),(other*.165,o["illustrative_tax_16_5pct_krw"])]:
  close(actual,expected,"pension withdrawal")
 m=models[1];i=m["inputs"];o=m["result"];P=i["initial_principal_krw"];fv=P*(1+i["annual_growth"])**i["years"];gain=fv-P
 close(round(fv),o["reference_pre_tax_balance_krw"],"pension balance")
 close(round(gain),o["reference_growth_krw"],"pension gain")
 require([x["credited_fraction"] for x in o["scenarios"]]==i["credited_fractions"],"tax basis scenario list")
 for x in o["scenarios"]:
  fraction=x["credited_fraction"];base=P*fraction+gain
  for actual,expect in [(P*fraction,x["credited_principal_krw"]),(P*(1-fraction),x["documented_noncredited_principal_krw"]),
   (round(base),x["reference_taxable_bases_krw"]),(round(fv-base*.055),x["annualized_illustrative_net_5_5pct_krw"]),(round(fv-base*.165),x["nonqualified_illustrative_net_16_5pct_krw"])]:
   close(actual,expect,"pension credited basis")
 require(o["scenarios"][0]["annualized_illustrative_net_5_5pct_krw"]-o["scenarios"][-1]["annualized_illustrative_net_5_5pct_krw"]==550000,"credited principal difference")
 m=models[2];i=m["inputs"];o=m["result"];annual=i["monthly_payment_krw"]*12;rate=i["statutory_annual_discount_rate"];months=i["months"];years=months//12
 for actual,expect in [
   (i["monthly_payment_krw"]*months,o["nominal_total_krw"]),
   (sum(annual/(1+rate)**j for j in range(1,years+1)),o["annual_end_krw"]),
   (sum(annual/(1+rate)**j for j in range(years)),o["annual_start_krw"]),
   (sum(i["monthly_payment_krw"]/(1+rate)**(j/12) for j in range(1,months+1)),o["monthly_end_economic_krw"]),
   (sum(i["monthly_payment_krw"]/(1+rate)**(j/12) for j in range(months)),o["monthly_start_economic_krw"])]:
  close(round(actual),expect,"gift timing")
 m=models[3];i=m["inputs"];o=m["result"]
 require([x["cancellation_lump_sum_krw"] for x in o["cancellation_floor_cases"]]==i["cancellation_lump_sum_examples_krw"],"gift cancellation")
 for x in o["cancellation_floor_cases"]:
  close(max(i["annual_end_pv_krw"],x["cancellation_lump_sum_krw"]),x["valuation_floor_example_krw"],"gift floor")
 require([x["prior_deducted_10y_krw"] for x in o["prior_deduction_cases"]]==i["prior_10year_ascendant_deductions_krw"],"gift history coverage")
 for x in o["prior_deduction_cases"]:
  remaining=max(0,i["nominal_10year_minor_allowance_krw"]-x["prior_deducted_10y_krw"])
  close(remaining,x["remaining_example_allowance_krw"],"gift allowance")
  close(max(0,i["annual_end_pv_krw"]-remaining),x["excess_over_remaining_if_value_eq_annuity_krw"],"gift excess")
 m=models[4];i=m["inputs"];o=m["result"]
 require([x["jpykrw_change"] for x in o["scenarios"]]==i["jpykrw_changes"],"fx coverage")
 for x in o["scenarios"]:
  fx=x["jpykrw_change"];cash=i["cash_spread_each_side"];preferred=cash*(1-i["cash_spread_preference"])
  expected=(i["capital_krw"]*(1+fx)*(1-cash)/(1+cash),i["capital_krw"]*(1+fx)*(1-preferred)/(1+preferred),
   i["capital_krw"]*(1+fx)*(1+i["etf_local_jpy_bond_return"])*(1-i["etf_annual_stated_fee"])*(1-i["etf_synthetic_tracking_drag"])*(1-i["etf_trade_friction_each_side"])**2)
  for a,b in zip(expected,(x["direct_without_preference_krw"],x["direct_90pct_preference_krw"],x["synthetic_unhedged_jpy_bond_etf_krw"])):
   close(round(a),b,"FX comparable pretax")
 m=models[5];i=m["inputs"];o=m["result"]
 for a,b in [(i["usd_stock_price"]*i["usdjpy_t0"],o["jpy_asset_value_t0"]),(i["usd_stock_price"]*i["usdjpy_t1"],o["jpy_asset_value_t1"]),
   (i["usd_stock_price"]*i["usdkrw_t0"],o["krw_asset_value_t0"]),(i["usd_stock_price"]*i["usdkrw_t1"],o["krw_asset_value_t1"]),
   ((i["usdkrw_t1"]/i["usdkrw_t0"]-1)*100,o["krw_return_percent"]),
   ((i["usdjpy_t1"]/i["usdjpy_t0"]-1)*100,o["jpy_return_percent"])]:
  close(a,b,"USD asset translation",1e-4)
 return len(models)

def test_register(root,audit):
 rows=audit["videos"];require(len(rows)==10 and [v["video_number"] for v in rows]==list(range(1,11)),"10 studies in order")
 totals={"claims":0,"checked":0,"retained":0,"open":0}
 all_ids=set()
 for row in rows:
  old=load(root,row["prior_research_path"])
  n=row["video_number"];old_claims=old["claim_triage"] if n<=5 else old["claims"]
  keys=[x["claim_id"] if n<=5 else x["id"] for x in old_claims]
  actual=[x["id"] for x in row["claim_audit"]]
  require(keys==actual and len(set(actual))==len(actual),"claim identity coverage #"+str(n))
  require(all(not x["reverified_from_raw_srt_in_this_20261030_cycle"] and
      not x["new_personal_investment_approval"] for x in row["claim_audit"]),"independent verification inflation")
  require(all(x["legacy_verdict"]==old_claims[j]["legacy_verdict"] for j,x in enumerate(row["claim_audit"])),"historical verdict changed")
  require(row["source_sha256"]==(old["source"]["original_SRT_SHA256"] if n<=5 else old["historical_source"]["original_srt_sha256"]),"source hash drift")
  require(row["video_id"]==old["video_id"] and row["private_zip_bytes_downloaded_and_hashed_this_cycle"] is False,"source provenance")
  expected_checked=sum((x["scope"]=="REEXAMINED_FOR_MATERIAL_RULE_OR_MODEL") if n<=5
                       else (x["current_review"]=="RECHECKED_MATERIAL_PRIMARY_OR_MATH") for x in old_claims)
  require(expected_checked==row["prior_V4_material_rechecked_count"],"review scope inflation")
  require(row["V3_retained_not_independently_rechecked_count"]==len(keys)-expected_checked,"retained mismatch")
  require(row["V3_claim_count"]==len(keys),"claim count mismatch")
  expected_open=old["unresolved"] if n<=5 else old["external_open"]
  require(len(expected_open)==len(row["open_evidence"]),"OPEN coverage")
  require(row["L3_approved"] is False and row["L4_approved"] is False,"false action readiness")
  for x in row["claim_audit"]:
   require(x["id"] not in all_ids,"duplicate across videos")
   all_ids.add(x["id"])
  totals["claims"]+=len(keys);totals["checked"]+=expected_checked
  totals["retained"]+=len(keys)-expected_checked;totals["open"]+=len(expected_open)
 require((totals["claims"],totals["checked"],totals["retained"],totals["open"])==
  (audit["inventory"]["original_V3_claims"],audit["inventory"]["prior_v4_material_rechecked_claims"],
   audit["inventory"]["prior_V3_retained_claims"],audit["inventory"]["per_video_open_total"]),"inventory inaccurate")
 require(totals=={"claims":122,"checked":69,"retained":53,"open":26},"10-video expected baseline")
 require(audit["inventory"]["existing_001_005_final_manifest_open_count"]==13 and
         audit["inventory"]["existing_001_005_individual_manifest_open_sum"]==12 and
         audit["inventory"]["unreconciled_open_delta"]==1,"known OPEN count reconciliation hidden")
 closeout=load(root,"data/synthesis/investment_knowledge_v4/reviews/v4_001_005_final_closure_20261030.json")
 require(closeout["unresolved_count"]==13,"legacy 13 open changed")
 require(sum(x["open_count"] for x in load(root,"data/synthesis/investment_knowledge_v4/reviews/v4_001_005_deep_research_manifest_20261030.json")["video_reviews"])==12,"12 individual opens changed")
 require(audit["contradiction_ids"]==["VKr060rIirM-05"] and
         any(x["id"]=="VKr060rIirM-05" and x["legacy_verdict"]=="CONTRADICTED" for x in rows[9]["claim_audit"]),"contradiction lost")
 require(not audit["L3_approved"] and not audit["L4_approved"] and not audit["old_V3_approvals_created_in_this_cycle"],"approval inflation")
 return totals

def test_all(root):
 model=load(root,MODEL);audit=load(root,AUDIT)
 require(model["status"]=="HYPOTHETICAL_DECISION_RESEARCH_L2_ONLY" and
         model["integrity"]["L3_approved"] is False and model["integrity"]["L4_approved"] is False,"model promoted")
 require(set(audit["model_ids"])=={x["id"] for x in model["models"]},"model links")
 require(load(root,PREV)["original_V3_claims_reused"]==60 and len(load(root,LEGACY)["models"])==9,"legacy evidence changed")
 result=test_register(root,audit);test_models(model)
 return result

def main():
 parser=argparse.ArgumentParser();parser.add_argument("--root",type=Path,default=ROOT);parser.add_argument("--self-test",action="store_true")
 args=parser.parse_args()
 try:
  root=args.root.resolve();baseline=test_all(root);rejected=0
  if args.self_test:
   models=load(root,MODEL)
   for mutation in ("pension_tax","gift_floor","yen_fee"):
    bad=copy.deepcopy(models)
    if mutation=="pension_tax":bad["models"][1]["result"]["scenarios"][2]["annualized_illustrative_net_5_5pct_krw"]+=100000
    if mutation=="gift_floor":bad["models"][3]["result"]["cancellation_floor_cases"][2]["valuation_floor_example_krw"]-=1000000
    if mutation=="yen_fee":bad["models"][4]["result"]["scenarios"][0]["synthetic_unhedged_jpy_bond_etf_krw"]+=100000
    try:test_models(bad)
    except GateFailure:rejected+=1
    else:raise GateFailure("mutation undetected: "+mutation)
   bad=copy.deepcopy(load(root,AUDIT));bad["videos"][9]["claim_audit"].pop()
   try:test_register(root,bad)
   except GateFailure:rejected+=1
   else:raise GateFailure("missing video claim undetected")
  print(json.dumps({"status":"PASS","videos":10,**baseline,"added_models":6,"self_test_mutations_rejected":rejected,
                    "scope":"structural/arithmetical audit only, no real private contract/tax validation"},ensure_ascii=False))
  return 0
 except (OSError,ValueError,TypeError,KeyError,IndexError,ZeroDivisionError,OverflowError) as e:
  print(json.dumps({"status":"FAIL","reason":str(e)},ensure_ascii=False));return 1
if __name__=="__main__":sys.exit(main())

