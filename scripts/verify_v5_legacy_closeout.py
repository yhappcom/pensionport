#!/usr/bin/env python3
"""Audit 001-010 V5 bounded retrofit; no personal assets or raw SRT are loaded by GitHub CI."""
import json, re, math, argparse, copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DIR="v5/retrofit"
REGEX=re.compile(r"v5_(00[1-9]|010)_([A-Za-z0-9_-]{11})_bounded_closeout\.json$")
BLOCK={"sz5N9WJS310-06","sz5N9WJS310-15","aNfGrcO6WPI-03","VKr060rIirM-05"}
PRIVATE=re.compile(r"\b\d{6}[- ]?[1-4]\d{6}\b|-----BEGIN (?:RSA |EC )?PRIVATE KEY-----")
DENY_KEYS={"account_number","portfolio_value","owner_name","owner_income","owner_holdings","private_cashflows","api_key"}
def load(x):return json.loads(x.read_text(encoding="utf-8"))
def req(c,msg):
 if not c:raise ValueError(msg)
def num(v):
 req(type(v) in (int,float) and math.isfinite(v),"nonfinite or bool math")
 return v
def mathcheck(t,a):
 for v in a:num(v)
 if t=="MONTHLY_SAVINGS":
  p,e,n=a;req(p>=0 and e>-1 and 1<=n<=1000,"savings inputs");r=(1+e)**(1/12)-1;return p*n if abs(r)<1e-12 else p*math.expm1(n*math.log1p(r))/r
 if t=="RESERVE_GAP":
  m,y,res=a;req(m>=0 and 0<=y<=240 and res>=0,"reserve");return max(0,m*y-res)
 if t=="DEPLOYMENT_MONTHS":
  s,m=a;req(s>=0 and m>0,"deployment");return math.ceil(s/m)
 if t=="DRAWDOWN_RECOVERY":
  (d,)=a;req(0<=d<1,"drawdown");return d/(1-d)
 if t=="BUDGET_OVERCOMMIT":
  income,expenses,proposed=a;req(min(a)>=0,"budget");return max(0,proposed-max(0,income-expenses))
 if t=="GIFT_PV":
  pay,years,rate,floor=a;req(pay>=0 and type(years)==int and 1<=years<=100 and rate>-1 and floor>=0,"gift");return max(sum(12*pay/(1+rate)**y for y in range(1,years+1)),floor)
 if t=="NET_CONTRIBUTION_PNL":
  start,end,net=a;req(start>=0 and end>=0,"asset endpoint");return end-start-net
 if t=="USD_KRW_LOOKTHROUGH":
  ru,fx=a;req(ru>-1 and fx>-1,"FX lookthrough");return (1+ru)*(1+fx)
 if t=="FX_ROUNDTRIP":
  krw,buy,sell=a;req(krw>=0 and buy>0 and sell>0,"FX spreads");return krw/buy*sell
 if t=="PENSION_PRIORITY":
  excluded,deferred,other,withdraw=a;req(min(a)>=0 and withdraw<=excluded+deferred+other,"pension source amount");x=withdraw;u=min(x,excluded);x-=u;v=min(x,deferred);x-=v;return [u,v,min(x,other)]
 raise ValueError("unknown calculation "+t)
def compare(a,b):
 if isinstance(a,list):
  req(isinstance(b,list) and len(a)==len(b),"list result");
  for v,w in zip(a,b):compare(v,w)
 else:req(math.isclose(num(a),num(b),rel_tol=1e-8,abs_tol=1e-6),"arithmetic mismatch")
def privacy_walk(x):
 if isinstance(x,dict):
  for k,v in x.items():req(k.lower() not in DENY_KEYS,"private key "+k);privacy_walk(v)
 elif isinstance(x,list):
  for v in x:privacy_walk(v)
 elif isinstance(x,str):req(PRIVATE.search(x) is None,"private identity/token pattern")
def validate(rec,old,v4,policy):
 n=rec["video_number"];vid=rec["video_id"]
 req(rec["schema_version"]=="V5_001_010_BOUND_CLOSEOUT_1.0","schema")
 req(n==v4["video_number"] and vid==v4["video_id"]==old["video_id"],"video identity")
 src=rec["source"]
 req(src["private_archive_location"]=="PRIVATE_GOOGLE_DRIVE_ONLY","private archive")
 req(src["raw_srt_reopened_and_sha256_recomputed_this_turn"] is True and src["cues_parsed_this_turn"] is True,"source not reopened")
 req(src["source_sha256"]==v4["source_sha256"] and src["cue_count"]==v4["source_cues"],"source hash/cues")
 req(src["all_cues_manually_understood"] is False,"false complete manual understanding")
 req(src["full_human_semantic_review_completed"] is (n==10),"full source review mismatch")
 req(src["original_audio_verified"] is False and src["original_video_frames_verified"] is False,"false audiovisual")
 claims=rec["claim_coverage"]["claims"];oldclaims=old["core_claims"];v4claims=v4["claim_audit"]
 req(len(claims)==len(oldclaims)==len(v4claims)==rec["claim_coverage"]["expected_legacy_claim_count"],"claim count")
 req(rec["claim_coverage"]["prior_V4_rechecked"]==v4["prior_V4_material_rechecked_count"],"V4 rechecked")
 req(rec["claim_coverage"]["reused_V3_without_new_V4_check"]==v4["V3_retained_not_independently_rechecked_count"],"reused")
 req(rec["claim_coverage"]["source_truth_independently_reverified_claim_count"]==0,"new unsourced claim approval")
 located=0
 for c,oc,vc in zip(claims,oldclaims,v4claims):
  req(c["id"]==oc["claim_id"]==vc["id"] and c["timecode"]==oc["timecode"],"claim IDs/time")
  req(c["verdict"]==oc["verification"]==vc["legacy_verdict"],"legacy verdict changed")
  req(c["new_independent_factual_truth_proven"] is False and c["personal_advice_approved"] is False,"unearned approval")
  req(c["use"]==("CORRECTION_ONLY_NOT_POSITIVE" if c["verdict"]=="CONTRADICTED" else "L1_L2_CONDITIONAL_ONLY"),"false positive claim")
  req(type(c["srt_context_read_this_turn"]) is bool,"cue flag")
  located+=int(c["srt_context_read_this_turn"])
 req(located==src["source_cue_contexts_read"]==3,"targeted source cue coverage")
 sources=rec["primary_checks"]
 req(sources and len(sources)==len({x["ref_id"] for x in sources}),"primary references")
 sourceids={x["ref_id"] for x in sources}
 for x in sources:
  req(x["url"].startswith("https://") and x["checked_on"]=="2026-10-30" and x["actual_page_read_this_turn"] is True,"unread primary URL")
  req(x["condition"] and x["supported_claim_ids"] and all(y in {c["id"] for c in claims} for y in x["supported_claim_ids"]),"source scope")
 for c in claims:req(set(c["primary_scope_refs"])<=sourceids,"wrong primary link")
 model=rec["decision_model"];req(model["synthetic_only"] is True and model["model_limit"],"live model assumption")
 ss=model["scenarios"];req([v["label"] for v in ss]==["BASE","ADVERSE"],"scenario coverage")
 for s in ss:compare(s["expected"],mathcheck(model["type"],s["inputs"]))
 d=rec["decision_context"]
 req(d["NO_CHANGE"]["costs"] and d["ALTERNATIVE"]["downside"] and d["core_risk_or_counterexample"],"alternatives/risks")
 for category in ["costs","taxes","liquidity","downside","eligibility"]:
  req(d["NO_CHANGE"].get(category) and d["ALTERNATIVE"].get(category),"missing decision dimension "+category)
 req(d["private_proof_needed"] and d["blocked_investor_action"] and d["flip_condition"],"missing suitability block")
 opens=rec["external_blockers"]
 req(len(opens)==len(v4["open_evidence"]),"external open omitted")
 for item,prior in zip(opens,v4["open_evidence"]):
  req(item["id"]==prior["id"] and item["personal_decision_blocked"] is True,"open status")
  req(item["status"]==("PRIVATE_34_CUE_SRT_RECOVERED_AUDIO_UNCHECKED" if n==10 and item["id"]=="10-ORIGINAL" else "EXTERNAL_OPEN"),"open resolved without evidence")
 req(rec["cross_video"]["contradicted_positive_reuse"] is False,"contradiction leak")
 req(set(rec["cross_video"]["blocked_legacy_claim_ids"])=={c["id"] for c in claims if c["id"] in BLOCK},"blocked claim missing")
 req(rec["decision_status"]==("EVIDENCE_BLOCKED_FOR_CASE_PERFORMANCE" if n==7 else "DECISION_MODULE_LIMITED_L2"),"false readiness")
 for k in ["L3_personalized_approved","L4_execution_approved","personal_input_read","personal_data_in_github"]:
  req(rec[k] is False,"wrong privacy or approval "+k)
 req(rec["generic_research_turn_closed_with_limitations"] is True and rec["original_V3_V4_files_unchanged"] is True,"false completion")
 privacy_walk(rec)
 return located
def run(root):
 summary=load(root/"v5/retrofit/summary_20261030.json")
 baseline=load(root/"data/synthesis/investment_knowledge_v4/reviews/v4_001_010_cross_video_final_audit_20261030.json")
 policy=load(root/"v5/policy/v5_review_policy_20261030.json")
 req({x["id"] for x in policy["blocked_source_claims"]}==BLOCK,"canonical contradicted count")
 files=sorted((root/DIR).glob("v5_*_bounded_closeout.json"))
 req(len(files)==10,"10 retrofit files required")
 counters={"claims":0,"cues":0,"locate":0,"models":0,"open":0}
 for i,f in enumerate(files):
  m=REGEX.fullmatch(f.name);req(m is not None,"wrong file")
  rec=load(f);v4=baseline["videos"][i];old=load(root/"data/analysis_events"/(v4["video_id"]+".json"))
  req(rec["video_number"]==int(m.group(1)) and rec["video_id"]==m.group(2),"filename mismatch")
  n=validate(rec,old,v4,policy)
  counters["claims"]+=len(rec["claim_coverage"]["claims"]);counters["cues"]+=rec["source"]["cue_count"]
  counters["locate"]+=n;counters["models"]+=1;counters["open"]+=len(rec["external_blockers"])
 req(counters=={"claims":122,"cues":19014,"locate":30,"models":10,"open":26},"research tally")
 req(summary["video_count"]==10 and summary["claim_ids"]==122 and summary["source_srt_verified"]==10 and summary["total_cues"]==19014,"summary tally")
 req(summary["numerical_models"]==10 and summary["synthetic_scenarios"]==20 and summary["external_open_recorded_historically"]==26,"summary full coverage")
 req(summary["positive_personal_advice_approvals"]==0 and summary["ready_L2"]==0 and summary["personal_data_used"] is False,"false personal advisor")
 req(summary["CI_status"]=="PENDING","CI must be verified externally")
 privacy_walk(summary)
 return {"status":"V5_BOUNDED_001_010_PASS","verified_video_raw_hashes":10,**counters,"L3":False,"L4":False}
def tests(root):
 allfiles=sorted((root/DIR).glob("v5_*_bounded_closeout.json"))
 rec=load(allfiles[0]);baseline=load(root/"data/synthesis/investment_knowledge_v4/reviews/v4_001_010_cross_video_final_audit_20261030.json")["videos"][0]
 old=load(root/"data/analysis_events"/(baseline["video_id"]+".json"));policy=load(root/"v5/policy/v5_review_policy_20261030.json")
 count=0
 def reject(r):
  nonlocal count
  try:validate(r,old,baseline,policy)
  except (ValueError,KeyError,TypeError):count+=1
  else:raise ValueError("bad mutation accepted")
 cases=[("L3_personalized_approved",True),("personal_input_read",True)]
 for k,val in cases:
  a=copy.deepcopy(rec);a[k]=val;reject(a)
 a=copy.deepcopy(rec);a["source"]["source_sha256"]="0"*64;reject(a)
 a=copy.deepcopy(rec);a["claim_coverage"]["claims"].pop();reject(a)
 a=copy.deepcopy(rec);a["claim_coverage"]["claims"][5]["use"]="L1_L2_CONDITIONAL_ONLY";reject(a)
 a=copy.deepcopy(rec);a["external_blockers"].pop();reject(a)
 a=copy.deepcopy(rec);a["decision_model"]["scenarios"][0]["expected"]=0;reject(a)
 a=copy.deepcopy(rec);a["decision_context"]["ALTERNATIVE"]["costs"]="";reject(a)
 a=copy.deepcopy(rec);a["decision_status"]="DECISION_MODULE_READY_L2";reject(a)
 req(count==9,"regression cases")
 return count
def main():
 parser=argparse.ArgumentParser();parser.add_argument("--root",type=Path,default=ROOT);parser.add_argument("--self-test",action="store_true")
 opt=parser.parse_args();root=opt.root.resolve()
 out=run(root)
 if opt.self_test:out["negative_mutations_rejected"]=tests(root)
 print(json.dumps(out,ensure_ascii=False,sort_keys=True))
if __name__=="__main__":
 try:main()
 except (ValueError,TypeError,KeyError,ArithmeticError,OSError) as e:
  print(json.dumps({"status":"FAIL","type":type(e).__name__,"message":str(e)}));raise SystemExit(1)
