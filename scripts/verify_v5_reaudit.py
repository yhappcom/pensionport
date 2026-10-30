#!/usr/bin/env python3
"""V5: nonpersonal V3/V4 evidence-led review. No private user files are loaded."""
import argparse
import copy
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OLD="data/synthesis/investment_knowledge_v4/reviews/v4_001_010_cross_video_final_audit_20261030.json"
NEW="v5/reviews/v5_001_010_reaudit_20261030.json"
POL="v5/policy/v5_review_policy_20261030.json"
SENSITIVE_KEYS={"account_number","owner_name","personal_holdings","personal_portfolio","personal_cashflows","user_account","api_key","broker_secret"}
PERSON_ID=re.compile(r"\b\d{6}[- ]?[1-4]\d{6}\b|-----BEGIN (?:RSA |EC )?PRIVATE KEY-----")
def load(p): return json.loads(p.read_text(encoding="utf-8"))
def require(x,msg):
    if not x: raise ValueError(msg)
def sensitive_walk(x):
    if isinstance(x,dict):
        for k,v in x.items():
            require(k.lower() not in SENSITIVE_KEYS,"sensitive field "+k)
            sensitive_walk(v)
    elif isinstance(x,list):
        for v in x: sensitive_walk(v)
    elif isinstance(x,str):
        require(PERSON_ID.search(x) is None,"sensitive identity pattern")
def validate(a,p,b,root):
    require(a["schema_version"]=="V5_REAUDIT_001_010_1.0","schema")
    require(a["base_audit_path"]==OLD and a["policy_path"]==POL,"baseline linkage")
    require(p["schema_version"]=="V5_NONPERSONAL_REVIEW_POLICY_1.0","policy")
    require(p["nonpersonal_only"] and p["public_git_data_policy"]=="NO_PRIVATE_INVESTMENT_DATA","privacy policy")
    for key in ("personal_data_read_for_review","personal_data_committed","existing_V3_V4_rewritten","L3_approved","L4_approved","trade_instructions_generated"):
        require(a[key] is False,"approval or source integrity: "+key)
    for key in ("L3_approved","L4_approved","trade_execution_enabled"):
        require(p[key] is False,"policy enabled "+key)
    require(p["allowed_levels"]==["L1_EXPLANATION","L2_HYPOTHETICAL_SCREEN"],"levels")
    v=a["videos"]; x=b["videos"]; inv=a["inventory"]
    require(len(x)==len(v)==inv["video_count"]==10,"videos")
    require(inv["claim_ids"]==b["inventory"]["original_V3_claims"]==122,"claims")
    require(inv["previous_v4_material_rechecked"]==b["inventory"]["prior_v4_material_rechecked_claims"]==69,"material")
    require(inv["previous_v3_retained"]==b["inventory"]["prior_V3_retained_claims"]==53,"retained")
    require(inv["open_evidence_items"]==b["inventory"]["per_video_open_total"]==26,"open count")
    require(inv["historical_001_005_final_count"]==13 and inv["individual_001_005_open_count"]==12 and inv["unreconciled_count_delta"]==1,"open reconciliation silently cleared")
    require(inv["v5_raw_srt_independent_checks"]==0,"unearned source verification")
    require(inv["L3_approved"]==inv["L4_approved"]==0,"new approval")
    seen=set();bad=set()
    for u,w in zip(x,v):
        require(u["video_number"]==w["number"] and u["video_id"]==w["video_id"],"video IDs")
        require(w["historical_source_sha256"]==u["source_sha256"],"historical source hash")
        require(w["source_cues_historical"]==u["source_cues"],"historical cue count")
        require(not w["original_srt_rehashed_in_v5"] and not w["original_audio_checked_in_v5"] and not w["original_frames_checked_in_v5"],"new source verification falsely claimed")
        require(w["historical_v3_claims"]==u["V3_claim_count"],"claim tally")
        require(w["historical_v4_material_rechecked"]==u["prior_V4_material_rechecked_count"],"V4 review tally")
        require(w["historical_retained_without_v4_recheck"]==u["V3_retained_not_independently_rechecked_count"],"V3 retained tally")
        require(len(w["open_evidence"])==len(u["open_evidence"]),"open coverage")
        for aopen,bopen in zip(u["open_evidence"],w["open_evidence"]):
            require(aopen["id"]==bopen["id"] and bopen["status"]=="UNRESOLVED" and bopen["newly_resolved"] is False,"open false resolution")
        require(len(u["claim_audit"])==len(w["claims"]),"per-video full claim scope")
        require(not w["L3_approved"] and not w["L4_approved"] and w["completion"]=="EVIDENCE_LIMITED_DECISION_REREVIEW","false approval")
        require(w["private_evidence_needed_categories"] and w["positive_recommendation_prohibited"],"unqualified recommendation gate")
        for c,d in zip(u["claim_audit"],w["claims"]):
            require(c["id"]==d["id"] and c["legacy_verdict"]==d["legacy_verdict"],"legacy claim/verdict tamper")
            require(c["reviewed_in_prior_v4"]==d["previous_v4_material_rechecked"],"prior recheck flag")
            require(d["new_independent_primary_verification"] is False and d["personal_recommendation_approved"] is False,"unearned independent source or L3")
            desired="CORRECTION_ONLY_NO_POSITIVE_USE" if c["legacy_verdict"]=="CONTRADICTED" else "L1_L2_CONDITIONAL_RESEARCH"
            require(d["v5_use"]==desired,"contradicted promoted")
            require(d["id"] not in seen,"duplicate claim")
            seen.add(d["id"])
            if desired=="CORRECTION_ONLY_NO_POSITIVE_USE": bad.add(d["id"])
    controlled={e["id"] for e in p["blocked_source_claims"]}
    require(len(p["blocked_source_claims"])==4 and len(controlled)==4,"blocked four")
    require(bad==controlled==set(a["blocked_claim_ids"]),"contradicted leakage")
    require(all(not e["can_be_positive_basis"] and e["verdict"]=="CONTRADICTED" for e in p["blocked_source_claims"]),"blocked statuses")
    require(inv["blocked_contradicted_ids"]==len(bad) and len(seen)==122,"tallies")
    sensitive_walk(a);sensitive_walk(p)
    allowed={"v5/README.md","v5/V5_REVIEW_001_010_20261030.md",NEW,POL,
             "v5/ADVISORY_GRADE_ONE_TURN_PROTOCOL_20261030.md",
             "v5/policy/v5_one_turn_advisory_research_policy_20261030.json",
             "v5/templates/v5_one_turn_synthetic_example.json"}
    tracked={f.relative_to(root).as_posix() for f in (root/"v5").rglob("*") if f.is_file()}
    module_pattern=re.compile(r"v5/videos/v5_\d{3}_[A-Za-z0-9_-]{11}_advisory_review\.json$")
    extras=tracked-allowed
    require(all(module_pattern.fullmatch(x) for x in extras),
            "unexpected V5 file; reject unreviewed private artifacts")
    require(allowed<=tracked,"required protected V5 policy or reports missing")
    for f in (root/"v5").rglob("*"):
        if f.is_file():
            require(f.suffix in (".md",".json"),"no binary/private file formats")
            require(PERSON_ID.search(f.read_text(encoding="utf-8")) is None,"sensitive identifier pattern in V5")
    return {"result":"PASS","videos":10,"claims":122,"prior_v4_material":69,
            "historical_verdicts_retained":53,"OPEN":26,"OPEN_count_discrepancy":1,
            "contradictions_blocked":4,"personal_records_accessed":0,"L3":False,"L4":False}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",type=Path,default=ROOT);ap.add_argument("--self-test",action="store_true")
    args=ap.parse_args();r=args.root.resolve()
    a=load(r/NEW);p=load(r/POL);b=load(r/OLD)
    result=validate(a,p,b,r)
    if args.self_test:
        passed=0
        def fails(da,dp,db):
            nonlocal passed
            try: validate(da,dp,db,r)
            except ValueError: passed+=1
            else: raise ValueError("self-test failed to reject mutation")
        z=copy.deepcopy(a);z["L3_approved"]=True;fails(z,p,b)
        z=copy.deepcopy(a);z["videos"][0]["claims"].pop();fails(z,p,b)
        z=copy.deepcopy(a);z["videos"][0]["original_srt_rehashed_in_v5"]=True;fails(z,p,b)
        z=copy.deepcopy(a);z["inventory"]["open_evidence_items"]=25;fails(z,p,b)
        z=copy.deepcopy(a);z["videos"][3]["claims"][2]["v5_use"]="L1_L2_CONDITIONAL_RESEARCH";fails(z,p,b)
        y=copy.deepcopy(p);y["blocked_source_claims"].pop();fails(a,y,b)
        y=copy.deepcopy(p);y["account_number"]="123456";fails(a,y,b)
        require(passed==7,"selftest coverage")
        result["negative_mutations_rejected"]=passed
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
if __name__=="__main__":
    try:main()
    except (OSError,KeyError,ValueError,TypeError,IndexError) as err:
        print(json.dumps({"result":"FAIL","exception":type(err).__name__,"note":str(err)}))
        raise SystemExit(1)
