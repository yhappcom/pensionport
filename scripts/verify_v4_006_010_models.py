#!/usr/bin/env python3
"""Deterministic bounded V4 006-010 research models gate. No trading or network."""
import argparse, copy, json, math, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MODEL="data/synthesis/investment_knowledge_v4/models/decision_models_006_010_20261030.json"
MANIFEST="data/synthesis/investment_knowledge_v4/reviews/v4_005_010_incremental_manifest_20261030.json"
IDS=["3MyhYE2jmuE","4CQ4FjGT2gA","OfkY343OaNs","YNOSY15ppf8","VKr060rIirM"]
NAMES=["V4_006_GIFT_ANNUITY_PV","V4_006_GIFT_SCHEDULE_SUM","V4_007_WEALTH_ATTRIBUTION","V4_007_LEVERAGE_RISK","V4_008_JPY_ETF_FX_FEE","V4_008_CROSS_FX_US_EQUITY","V4_009_SPOT_FX_SPREAD","V4_010_PENSION_SOURCE","V4_010_ORDINARY_PENSION_TAX"]
class Bad(ValueError):pass
def check(x,msg):
 if not x:raise Bad(msg)
def close(x,y,msg,t=1.01):
 check(type(y) in (int,float) and math.isfinite(x) and math.isfinite(y) and abs(x-y)<=t,msg)
def read(root,path):return json.loads((root/path).read_text(encoding="utf-8"))
def test(v):
 check([m["id"] for m in v]==NAMES,"ID count/order");check([m["video"] for m in v]==[6,6,7,7,8,8,9,10,10],"source-video number")
 for m in v:check(bool(m.get("limits")) and bool(m.get("formula")),"missing model assumptions")
 n=0;x=v[0];i=x["inputs"];o=x["result"];a=i["monthly_krw"]*12;t=i["months"]//12;r=i["statutory_annual_rate"]
 for va,vb in [(i["monthly_krw"]*i["months"],o["nominal_paid_krw"]),(a,o["annual_entitlement_krw"]),(round(sum(a/(1+r)**yr for yr in range(1,t+1))),o["year_end_pv_krw"]),(round(sum(a/(1+r)**yr for yr in range(t))),o["year_start_pv_krw"]),(a*20,o["twenty_times_annual_krw"])]:close(va,vb,"gift annuity");n+=5
 x=v[1];s=x["inputs"]["gift_events_krw"];close(sum(s),x["result"]["all_events_krw"],"gift schedule total");close(sum(s[:4]),x["result"]["first_four_krw"],"gift pre-special");n+=2
 x=v[2];i=x["inputs"];o=x["result"];dif=i["ending_krw"]-i["beginning_krw"];close(dif,o["gross_change_krw"],"wealth change");n+=1
 check(set(o["net_gain_by_contribution_krw"])==set(map(str,i["net_contributions_krw"])),"wealth scenario count")
 for z in i["net_contributions_krw"]:close(dif-z,o["net_gain_by_contribution_krw"][str(z)],"wealth contributed");n+=1
 x=v[3];i=x["inputs"];o=x["result"];eq=i["gross_assets_krw"]-i["debt_krw"];post=i["gross_assets_krw"]*(1-i["asset_drawdown"])-i["debt_krw"]
 close(eq,o["initial_equity_krw"],"leverage equity");close(post,o["after_drawdown_equity_krw"],"leverage after");close((eq-post)/eq,o["equity_drawdown_fraction"],"leverage ratio",1e-8);n+=3
 x=v[4];i=x["inputs"];o=x["result"]
 check(set(o)==set(map(str,i["jpy_to_krw_change"])),"yen scenario keys")
 for fx in i["jpy_to_krw_change"]:
  factor=(1+i["assumed_local_bond_return"])*(1+fx)*(1-i["issuer_stated_fee"])
  close(round(i["initial_krw"]*factor),o[str(fx)]["terminal_krw"],"yen value")
  close(round((factor-1)*100,6),o[str(fx)]["return_percent"],"yen return",1e-5);n+=2
 x=v[5];i=x["inputs"];o=x["result"]
 for a,b in [(i["usdkrw_t0"]*100/i["usdjpy_t0"],o["krw_per_100jpy_t0"]),(i["usdkrw_t1"]*100/i["usdjpy_t1"],o["krw_per_100jpy_t1"]),(i["unchanged_usd_stock"]*i["usdjpy_t0"],o["jpy_value_t0"]),(i["unchanged_usd_stock"]*i["usdjpy_t1"],o["jpy_value_t1"]),((i["usdkrw_t1"]/i["usdkrw_t0"]-1)*100,o["krw_return_pct"])]:close(a,b,"cross yen",1e-5);n+=5
 x=v[6];i=x["inputs"];o=x["result"];check(set(o)==set(map(str,i["preferential_discounts"])),"spread scenarios")
 for pref in i["preferential_discounts"]:
  s=i["dealer_spread_each_leg"]*(1-pref)
  close(s,o[str(pref)]["effective_spread"],"discounted spread",1e-6)
  close((1+s)/(1-s)-1,o[str(pref)]["minimum_mid_appreciation_fraction"],"spread breakeven",1.01e-9);n+=2
 x=v[7];i=x["inputs"];o=x["result"];base=min(i["properly_evidenced_noncredited_principal_krw"],i["hypothetical_withdrawal_krw"]);tax=i["hypothetical_withdrawal_krw"]-base
 for a,b in [(i["properly_evidenced_noncredited_principal_krw"]+i["credited_principal_krw"]+i["investment_gain_krw"],o["account_value_krw"]),(base,o["tax_excluded_withdrawal_krw"]),(tax,o["taxable_withdrawal_krw"]),(tax*i["eligible_taxable_pension_withholding_example"],o["tax_illustration_krw"])]:close(a,b,"pension source");n+=4
 x=v[8];i=x["inputs"];o=x["result"];fv=i["principal_krw"]*(1+i["gross_annual_return"])**i["years"];gain=fv-i["principal_krw"]
 close(round(fv),o["terminal_pretax_krw"],"tax FV");close(round(gain),o["gain_krw"],"tax gain");n+=2
 for field,rs in [("ordinary_net_krw",i["ordinary_gain_tax_scenarios"]),("pension_net_krw",i["pension_gain_tax_scenarios"])]:
  check(set(o[field])==set(map(str,rs)),"tax case coverage")
  for rate in rs:close(round(i["principal_krw"]+gain*(1-rate)),o[field][str(rate)],"tax net");n+=1
 return n
def provenance(root,data):
 man=read(root,MANIFEST);check(man["original_V3_claims_reused"]==60,"claims reused");check(man["new_V3_approvals"]==man["new_V3_claims"]==0,"approval inflation")
 check(man["model_count"]==len(data["models"])==9,"model count");check(len(man["review_files"])==5,"review count")
 count=0
 for j,entry in enumerate(man["review_files"]):
  id=IDS[j];check(entry["id"]==id and entry["roster_no"]==6+j,"roster")
  row=read(root,entry["path"]);check(row["video_id"]==id and row["status"]=="V4_DEEP_RESEARCH_COMPLETE_WITH_EXTERNAL_OPEN","status")
  hist=row["historical_source"];pilot=read(root,hist["pilot_path"]);a=read(root,hist["v3_path"])
  check(a["approval"]=="APPROVED" and a["video_id"]==id and pilot["approval"]=="NOT_APPROVED","historical approvals")
  check(hist["original_srt_sha256"]==pilot["source_audit"]["original_srt_sha256"],"source hash")
  if j==4:check(hist["original_srt_sha256"] is None,"shorts SRT absence")
  else:check(bool(hist["original_srt_sha256"]),"missing prior source")
  check({x["id"] for x in row["claims"]}=={x["claim_id"] for x in a["core_claims"]},"claim ID mapping")
  check(row["decision_readiness"]["L3_approved"] is False and row["decision_readiness"]["L4_approved"] is False,"personal investment claim")
  check(set(row["models"])=={x["id"] for x in data["models"] if x["video"]==6+j},"model links")
  check(len(row["external_open"])==entry["open_count"] and bool(row["external_open"]),"source blockers")
  count+=len(row["claims"])
 check(count==60,"total 60")
 return count
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=ROOT);p.add_argument("--self-test",action="store_true");opts=p.parse_args()
 try:
  root=opts.root.resolve();doc=read(root,MODEL);check(doc["schema_version"]=="V4_006_010_MODELS_1.0","schema")
  n=test(doc["models"])
  if opts.self_test:
   bad=copy.deepcopy(doc["models"]);bad[0]["result"]["year_end_pv_krw"]+=10000
   try:test(bad)
   except Bad:pass
   else:raise Bad("mutation undetected")
   try:test(doc["models"][:-1])
   except Bad:pass
   else:raise Bad("missing model undetected")
   print(json.dumps({"status":"PASS","models":9,"arithmetics":n,"mutations":2}));return 0
  c=provenance(root,doc)
  print(json.dumps({"status":"PASS","models":9,"arithmetics":n,"original_V3_claims_linked":c,"scope":"synthetic math and source registry only"}));return 0
 except (Bad,ValueError,KeyError,TypeError,OSError,ZeroDivisionError,OverflowError,IndexError) as e:
  print(json.dumps({"status":"FAIL","error":str(e),"type":type(e).__name__}));return 1
if __name__=="__main__":sys.exit(main())
