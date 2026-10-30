#!/usr/bin/env python3
"""V5 one-turn VIDEO research decision gate; no personal financial records or internet.
Validates new per-video records against immutable V3, modeling and privacy constraints.
Only a human independently reading original and primary sources can establish truth.
"""
import argparse
import copy
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = "v5/policy/v5_one_turn_advisory_research_policy_20261030.json"
TEMPLATE = "v5/templates/v5_one_turn_synthetic_example.json"
REVIEW_DIR = "v5/videos"
VIDEO_FILE = re.compile(r"v5_(\d{3})_([a-zA-Z0-9_-]{11})_advisory_review\.json$")
YOUTUBE_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HASH = re.compile(r"^[a-f0-9]{64}$")
PRIVATE_NAMES = {"actual_holdings","real_portfolio","owner_balance","account_number",
                 "account_id","bank_account","owner_full_name","tax_basis_amount",
                 "transaction_ledger","kis_account","owner_income","owner_expenses",
                 "api_key","api_secret","real_user_data","owner_portfolio"}
CODES = re.compile(r"\b\d{6}[- ]?[1-4]\d{6}\b|-----BEGIN (?:RSA |EC )?PRIVATE KEY-----")
LEVELS = {"DECISION_MODULE_READY_L2","DECISION_MODULE_LIMITED_L2","EVIDENCE_BLOCKED"}
VERDICTS = {"PRIMARY_CONFIRMED","QUALIFIED","HYPOTHETICAL","CONTRADICTED"}
METHODS = {"DRAWDOWN_RECOVERY","COMPOUND_FV","FX_ROUND_TRIP","CASH_RESERVE"}
PROOF_AREAS = {"costs","taxes","liquidity","downside","eligibility"}

def require(value, message):
    if not value:
        raise ValueError(message)

def finite(value, context):
    require(type(value) in (int,float) and math.isfinite(value),
            context + ": expected finite number")
    return value

def source_file(path):
    return json.loads(path.read_text(encoding="utf-8"))

def privacy_scan(obj):
    if isinstance(obj,dict):
        for k,v in obj.items():
            require(k.lower() not in PRIVATE_NAMES,"possible personal field: "+k)
            privacy_scan(v)
    elif isinstance(obj,list):
        for v in obj: privacy_scan(v)
    elif isinstance(obj,str):
        require(CODES.search(obj) is None,"potential personal identifier in record")
    return True

def calc(model):
    t=model["type"]
    require(t in METHODS,"unsupported model formula")
    a=model["inputs"]
    if t=="DRAWDOWN_RECOVERY":
        d=finite(a["loss_fraction"],"loss_fraction")
        require(0 <= d < 1,"drawdown fraction not in [0,1)")
        return d/(1-d)
    if t=="COMPOUND_FV":
        pv=finite(a["principal"],"principal")
        rate=finite(a["period_rate"],"period_rate")
        n=finite(a["periods"],"periods")
        require(pv>=0 and rate>-1 and 0<=n<=2000,"invalid compound inputs")
        return pv*(1+rate)**n
    if t=="FX_ROUND_TRIP":
        principal=finite(a["starting_currency_amount"],"starting_currency_amount")
        buy=finite(a["buy_price"],"buy_price")
        sell=finite(a["sell_price"],"sell_price")
        require(principal>=0 and buy>0 and sell>0,"FX prices/amount invalid")
        return principal/buy*sell
    monthly=finite(a["monthly_expenses_plus_debt"],"monthly_expenses_plus_debt")
    months=finite(a["reserve_months"],"reserve_months")
    liquid=finite(a["outside_portfolio_reserve"],"outside_portfolio_reserve")
    require(monthly>=0 and 0<=months<=120 and liquid>=0,"reserve inputs invalid")
    return max(0,monthly*months-liquid)

def verify_model(model,claim_ids):
    require(re.fullmatch(r"[A-Za-z0-9_-]{4,90}",model["id"]) is not None,"model ID")
    require(model["type"] in METHODS,"unsupported model")
    require(model["synthetic_only"] is True,"private or unexplained model inputs")
    require(model["arithmetic_verified"] is True,"unverified math")
    require(model["semantic_verified"] is True,"unverified economic meaning")
    require(model["limitations"] and model["formula"],"model semantic limitations")
    require(set(model["claim_ids"])<=claim_ids and model["claim_ids"],"model claim IDs")
    scenarios=model["scenarios"]
    require({x["label"] for x in scenarios} >= {"BASE","ADVERSE"},"base and adverse scenarios required")
    require(len(scenarios)==len({x["label"] for x in scenarios}),"duplicate scenario")
    for s in scenarios:
        expected=finite(s["expected_result"],"expected result")
        output=calc({"type":model["type"],"inputs":s["inputs"]})
        require(math.isclose(expected,output,rel_tol=1e-8,abs_tol=1e-7),
                "scenario calculation mismatch: "+s["label"])
        require(s["interpretation"] and s["limitations"],"scenario assumptions missing")

def verify(doc,policy,legacy_ids=None,is_example=False,canonical_blocked=None):
    require(policy["schema_version"]=="V5_ONE_TURN_ADVISORY_RESEARCH_POLICY_1.0","policy schema")
    require(policy["scope"]=="NONPERSONAL_VIDEO_DECISION_MODULES_ONLY","nonpersonal scope")
    require(policy["L3_approved"] is False and policy["L4_approved"] is False
            and policy["auto_trade"] is False and policy["auto_portfolio_read"] is False,
            "trade/private/approval gate disabled")
    require(doc["schema_version"]=="V5_ONE_TURN_VIDEO_REVIEW_1.0","module schema")
    require(doc["synthetic_example"] is is_example,"real review / example classification")
    n=doc["video_number"]
    require(type(n) is int and n>=11 and n<=999,"invalid video number")
    require(YOUTUBE_ID.fullmatch(doc["video_id"]),"video ID")
    source=doc["source"]
    require(source["evidence_note"] and source["kind"],"source description")
    require(source["archive_stored_privately"] is True,"no private raw archive in repo")
    for k in ("raw_srt_read_and_hash_verified_this_turn","full_cue_review_this_turn",
              "audio_checked","frames_checked"):
        require(type(source[k]) is bool,"explicit source verification flag: "+k)
    if source["raw_srt_read_and_hash_verified_this_turn"]:
        require(source["full_cue_review_this_turn"] is True,"read exact raw source fully")
        require(isinstance(source["source_sha256"],str)
                and HASH.fullmatch(source["source_sha256"]),"actual raw SHA missing")
        require(type(source["source_cue_count"]) is int and source["source_cue_count"]>0,
                "raw cue count missing")
    else:
        require(source["full_cue_review_this_turn"] is False,"cannot claim full review without raw bytes")
    claims=doc["claims"]
    require(isinstance(claims,list) and len(claims)>0,"full claim list required")
    ids=[c["id"] for c in claims]
    require(len(ids)==len(set(ids)),"duplicate claim ids")
    if legacy_ids is not None:
        require(set(ids)==set(legacy_ids),"V5 claims differ from immutable V3 coverage")
    positive=[]
    for c in claims:
        require(c["id"].startswith(doc["video_id"]+"-"),"claim wrong video prefix")
        require(re.fullmatch(r"\d\d:\d\d:\d\d",c["timecode"]),"timecode missing")
        require(c["legacy_verdict"] in VERDICTS,"unknown V3 verdict")
        require(c["current_review"] in ("CHECKED","REUSED_LIMITED","BLOCKED"),"claim review category")
        require(type(c["material"]) is bool and type(c["independently_checked_this_turn"]) is bool,"claim flags")
        require(type(c["positive_principle_allowed"]) is bool,"positive use gate")
        require(c["scope_note"],"claim bounds missing")
        require(isinstance(c["primary_source_ids"],list) and isinstance(c["math_model_ids"],list),"claim links")
        if c["legacy_verdict"]=="CONTRADICTED":
            require(c["positive_principle_allowed"] is False,"contradicted claim promoted")
        if c["positive_principle_allowed"]:
            require(c["current_review"]=="CHECKED" and c["independently_checked_this_turn"],
                    "positive principle relies only on verified current claim")
            require(source["raw_srt_read_and_hash_verified_this_turn"],"positively confirmed without raw source")
            positive.append(c["id"])
    sources=doc["primary_sources"]
    require(isinstance(sources,list),"primary sources required")
    ids_primary=set()
    for x in sources:
        require(x["id"] not in ids_primary,"duplicate primary source ID")
        ids_primary.add(x["id"])
        require(x["publisher"] and x["url"].startswith("https://"),"public official source reference")
        require(ISO_DATE.fullmatch(x["checked_on"]) and x["effective_date"],"source check date and effective-date status")
        require(x["scope_and_exceptions"],"applicability must be stated")
        require(x["actual_text_checked"] is True,"source link does not prove read")
        require(set(x["claim_ids"])<=set(ids) and x["claim_ids"],"wrong cited claim IDs")
    for c in claims:
        require(set(c["primary_source_ids"])<=ids_primary,"claim references nonexistent official source")
        if c["legacy_verdict"]=="PRIMARY_CONFIRMED" and c["positive_principle_allowed"]:
            require(c["primary_source_ids"],"primary confirmation without primary source")
        for sid in c["primary_source_ids"]:
            require(c["id"] in next(x["claim_ids"] for x in sources if x["id"]==sid),"reverse primary link missing")
    if not sources:
        require(doc["primary_not_applicable_reason"],"must explain absent independent source")
    models=doc["models"]
    require(isinstance(models,list),"models required")
    mids=[m["id"] for m in models]
    require(len(mids)==len(set(mids)),"duplicate model ID")
    for m in models:
        verify_model(m,set(ids))
    for c in claims:
        require(set(c["math_model_ids"])<=set(mids),"model/claim linkage")
        if c["material"] and c["math_model_ids"]:
            require(c["current_review"]!="BLOCKED","blocked claim cannot support numeric claim")
    if not models:
        require(doc["no_numeric_model_reason"],"must model material number or explain why no numeric model")
    d=doc["decision_logic"]
    for k in ("question","no_action_if","consider_alternative_if","counterexample",
              "decision_flip_conditions"):
        require(d[k],"missing decision logic: "+k)
    require(isinstance(d["owner_facts_needed"],list) and d["owner_facts_needed"],"private screening categories missing")
    require(type(d["baseline_is_same_horizon_and_currency"]) is bool,"comparable baseline flag")
    alternatives=d["alternatives"]
    require(isinstance(alternatives,list) and {a["id"] for a in alternatives}>={"NO_CHANGE","ALTERNATIVE"},
            "must compare with no change")
    require(len({a["id"] for a in alternatives})==len(alternatives),"duplicate alternatives")
    for alt in alternatives:
        require(alt["assumptions"] and alt["risks"],"incomplete baseline assumptions")
        require(all(alt.get(area) for area in PROOF_AREAS),"missing cost, tax, liquidity, downside or eligibility")
    x=doc["cross_video"]
    require(type(x["contradiction_checked"]) is bool and x["contradiction_checked"],
            "cross-video contradiction scan missing")
    require(isinstance(x["related_claim_ids"],list) and isinstance(x["known_blocked_ids"],list),"cross-ref lists")
    if x["new_correction_required"]:
        require(x["correction_path"],"contradiction correction unavailable")
    all_blocked=set(x["known_blocked_ids"])
    canonical_blocked=set(canonical_blocked or [])
    require(canonical_blocked.intersection(x["related_claim_ids"])<=all_blocked,
            "known historical CONTRADICTED claim omitted from the block list")
    require(all(not c["positive_principle_allowed"] for c in claims
                if c["id"] in (all_blocked|canonical_blocked)),
            "blocked historical positive principle")
    empirical=doc["empirical_validation"]
    require(empirical["limitations"],"missing empirical limits")
    require(type(empirical["historical_performance_claimed"]) is bool and
            type(empirical["out_of_sample_tested"]) is bool,"empirical flags")
    if empirical["historical_performance_claimed"]:
        require(empirical["market_data_provenance"] not in ("NONE","UNKNOWN","SYNTHETIC"),
                "cannot promote historic performance without real source")
        require(empirical["selection_bias_assessed"] is True,"unexamined survivor bias")
    blockers=doc["open_blockers"]
    require(isinstance(blockers,list),"open blockers required")
    blocker_ids=set()
    for item in blockers:
        require(item["id"] not in blocker_ids and item["id"],"duplicate blocker")
        blocker_ids.add(item["id"])
        require(set(item["claim_ids"])<=set(ids) and item["claim_ids"],"blocker claim references")
        require(item["needed"] and item["blocks"] and item["reopen_trigger"],"actionable blocker missing")
    close=doc["one_turn_closeout"]
    require(close["all_feasible_work_done_this_turn"] is True,"deferred feasible work")
    require(close["external_blockers_remaining"]==len(blockers),"OPEN count understated")
    require(close["result"] in LEVELS,"not an admissible research closeout")
    require(close["max_use"] in ("L1","L2"),"no individual L3")
    require(close["generic_module_not_personalized"] is True and
            close["L3_approved"] is False and close["L4_approved"] is False and
            close["personal_facts_read"] is False and close["personal_facts_committed"] is False,
            "private data or personal advice elevation")
    require(isinstance(close["unperformed_work_disclosed"],list),"work scope missing")
    require(close["validation_status"]=="PENDING_CI","CI is only validated after GitHub Action finishes")
    if close["result"]=="DECISION_MODULE_READY_L2":
        require(source["raw_srt_read_and_hash_verified_this_turn"],"ready despite historical-only source")
        require(not blockers,"ready while material evidence open")
        require(positive and all(c["current_review"]=="CHECKED" for c in claims if c["material"]
                                 and c["legacy_verdict"]!="CONTRADICTED"),
                "ready without material claim recheck")
        require(bool(sources),"ready without primary source verification")
        require(models or doc["no_numeric_model_reason"].startswith("QUALITATIVE_ONLY:"),
                "ready without math or justified qualitative topic")
        require(d["baseline_is_same_horizon_and_currency"] is True,"comparison not normalized")
        require(empirical["historical_performance_claimed"] is False or
                empirical["out_of_sample_tested"] is True,"historical alpha promoted without validation")
        require(close["max_use"]=="L2","ready category limited to L2")
    if close["result"]=="DECISION_MODULE_LIMITED_L2":
        require(source["raw_srt_read_and_hash_verified_this_turn"] or
                any(c["current_review"]=="REUSED_LIMITED" for c in claims),
                "limited L2 still needs at least a source-backed claim")
        require(close["max_use"]=="L2","L2 closeout mismatch")
    if close["result"]=="EVIDENCE_BLOCKED":
        require(close["max_use"]=="L1","blocked only L1 warning")
        require(not positive,"blocked must not assert actionable positive principle")
    require(doc["source_reference_paths"]["prior_V3_analysis_event"] is None or
            doc["source_reference_paths"]["prior_V3_analysis_event"].startswith("data/analysis_events/"),
            "V3 reference integrity")
    privacy_scan(doc)
    return {"status":"PASS","video":n,"claims":len(claims),
            "source_raw_checked":source["raw_srt_read_and_hash_verified_this_turn"],
            "research_result":close["result"],"L3":False,"L4":False}

def validate_repo(root):
    policy=source_file(root/POLICY)
    historical_policy=source_file(root/"v5/policy/v5_review_policy_20261030.json")
    canonical_blocked={c["id"] for c in historical_policy["blocked_source_claims"]}
    require(len(canonical_blocked)==4,"historical contradiction policy not intact")
    require(policy["scope"]=="NONPERSONAL_VIDEO_DECISION_MODULES_ONLY","scope")
    fixture=source_file(root/TEMPLATE)
    require(fixture["synthetic_example"] is True,"fixture is never real data")
    test=verify(fixture,policy,is_example=True,canonical_blocked=canonical_blocked)
    found=list((root/REVIEW_DIR).glob("*.json")) if (root/REVIEW_DIR).is_dir() else []
    for f in found:
        match=VIDEO_FILE.fullmatch(f.name)
        require(match is not None,"unknown V5 video review filename")
        obj=source_file(f)
        require(obj["video_number"]==int(match.group(1)) and
                obj["video_id"]==match.group(2),"review filename mismatches video")
        legacy=root/"data/analysis_events"/(obj["video_id"]+".json")
        require(legacy.is_file(),"no original V3 review: cannot assert full claim coverage")
        v3=source_file(legacy)
        require(v3["video_id"]==obj["video_id"],"V3 video mismatch")
        ids={c["claim_id"] for c in v3["core_claims"]}
        verify(obj,policy,legacy_ids=ids,canonical_blocked=canonical_blocked)
        for claim in obj["claims"]:
            old=next(c for c in v3["core_claims"] if c["claim_id"]==claim["id"])
            require(old["verification"]==claim["legacy_verdict"],
                    "tampered V3 source verdict")
    # Path-by-path allowlisting; no private binary / source file under the V5 review tree.
    if (root/REVIEW_DIR).exists():
        require(len(found)==len([f for f in (root/REVIEW_DIR).rglob("*") if f.is_file()]),
                "unrecognized source/attachment in review directory")
    return {"status":"PASS","synthetic_template":"BLOCKED_FIXTURE",
            "v5_new_video_records":len(found),"L3_approved":False,"L4_approved":False}

def self_test(root):
    policy=source_file(root/POLICY)
    historical_policy=source_file(root/"v5/policy/v5_review_policy_20261030.json")
    canonical_blocked={c["id"] for c in historical_policy["blocked_source_claims"]}
    sample=source_file(root/TEMPLATE)
    verify(sample,policy,is_example=True,canonical_blocked=canonical_blocked)
    checked=0
    def rejects(doc,pol=policy):
        nonlocal checked
        try:
            verify(doc,pol,is_example=True,canonical_blocked=canonical_blocked)
        except (ValueError, KeyError, TypeError, ZeroDivisionError, OverflowError):
            checked+=1
        else:
            raise ValueError("negative mutation unexpectedly accepted")
    x=copy.deepcopy(sample);x["one_turn_closeout"]["L3_approved"]=True;rejects(x)
    x=copy.deepcopy(sample);x["claims"]=[];rejects(x)
    x=copy.deepcopy(sample);x["one_turn_closeout"]["result"]="DECISION_MODULE_READY_L2";rejects(x)
    x=copy.deepcopy(sample);x["one_turn_closeout"]["external_blockers_remaining"]=0;rejects(x)
    x=copy.deepcopy(sample);x["cross_video"]["contradiction_checked"]=False;rejects(x)
    x=copy.deepcopy(sample);x["decision_logic"]["alternatives"]=[x["decision_logic"]["alternatives"][1]];rejects(x)
    x=copy.deepcopy(sample);x["claims"][0]["legacy_verdict"]="CONTRADICTED";x["claims"][0]["positive_principle_allowed"]=True;rejects(x)
    x=copy.deepcopy(sample);x["owner_income"]=1234567;rejects(x)
    x=copy.deepcopy(sample);x["source"]["raw_srt_read_and_hash_verified_this_turn"]=True;rejects(x)
    x=copy.deepcopy(sample);x["primary_sources"]=[{"id":"E1","url":"https://example.com","publisher":"demo",
         "checked_on":"2026-10-30","effective_date":"2026-10-30","scope_and_exceptions":"example",
         "actual_text_checked":False,"claim_ids":["ZZsynthetic-01"]}];rejects(x)
    x=copy.deepcopy(sample);x["models"]=[{"id":"DEMO-DRAW","type":"DRAWDOWN_RECOVERY",
        "synthetic_only":True,"arithmetic_verified":True,"semantic_verified":True,
        "formula":"d/(1-d)","limitations":"synthetic drawdown",
        "claim_ids":["ZZsynthetic-01"],"scenarios":[
            {"label":"BASE","inputs":{"loss_fraction":0.4},"expected_result":0.5,
             "interpretation":"base","limitations":"hypothetical"},
            {"label":"ADVERSE","inputs":{"loss_fraction":0.5},"expected_result":1.0,
             "interpretation":"stress","limitations":"hypothetical"}
        ]}];rejects(x)
    require(checked==11,"self-test incomplete")
    # These synthetic positive paths validate structure only, not real law/source evidence.
    ready=copy.deepcopy(sample)
    ready["source"].update({
        "kind":"SYNTHETIC_STRUCTURAL_TEST","source_sha256":"a"*64,
        "source_cue_count":1,
        "raw_srt_read_and_hash_verified_this_turn":True,
        "full_cue_review_this_turn":True})
    ready["claims"][0].update({
        "legacy_verdict":"PRIMARY_CONFIRMED","current_review":"CHECKED",
        "independently_checked_this_turn":True,
        "positive_principle_allowed":True,"primary_source_ids":["SYNTH_SOURCE"]})
    ready["primary_sources"]=[{
        "id":"SYNTH_SOURCE","publisher":"SYNTHETIC_TEST_ONLY",
        "url":"https://example.org/nonexistent-test-source",
        "checked_on":"2026-10-30","effective_date":"SYNTHETIC_TEST_DATE",
        "scope_and_exceptions":"Structural test; NOT a real primary source.",
        "actual_text_checked":True,"claim_ids":["ZZsynthetic-01"]}]
    ready["open_blockers"]=[]
    ready["decision_logic"]["baseline_is_same_horizon_and_currency"]=True
    ready["no_numeric_model_reason"]="QUALITATIVE_ONLY: no numeric research in test."
    ready["one_turn_closeout"].update({
        "result":"DECISION_MODULE_READY_L2","max_use":"L2",
        "external_blockers_remaining":0})
    verify(ready,policy,is_example=True,canonical_blocked=canonical_blocked)
    positive_paths=1
    # Deterministic, independently calculated base and adverse drawdown cases.
    numeric=copy.deepcopy(ready)
    numeric["claims"][0]["math_model_ids"]=["TEST_DRAW"]
    numeric["models"]=[{
        "id":"TEST_DRAW","type":"DRAWDOWN_RECOVERY",
        "synthetic_only":True,"arithmetic_verified":True,"semantic_verified":True,
        "formula":"d/(1-d)","limitations":"Illustrative, not a return distribution.",
        "claim_ids":["ZZsynthetic-01"],"scenarios":[
            {"label":"BASE","inputs":{"loss_fraction":0.4},
             "expected_result":0.6666666666666666,"interpretation":"reference",
             "limitations":"hypothetical"},
            {"label":"ADVERSE","inputs":{"loss_fraction":0.5},
             "expected_result":1.0,"interpretation":"stress",
             "limitations":"hypothetical"}]}]
    verify(numeric,policy,is_example=True,canonical_blocked=canonical_blocked)
    positive_paths+=1
    x=copy.deepcopy(numeric);x["models"][0]["scenarios"][0]["expected_result"]=0.5;rejects(x)
    x=copy.deepcopy(numeric);x["models"][0]["semantic_verified"]=False;rejects(x)
    x=copy.deepcopy(numeric);x["models"][0]["scenarios"].pop();rejects(x)
    x=copy.deepcopy(ready);x["primary_sources"][0]["actual_text_checked"]=False;rejects(x)
    x=copy.deepcopy(ready);x["source"]["source_sha256"]=None;rejects(x)
    x=copy.deepcopy(ready);x["decision_logic"]["baseline_is_same_horizon_and_currency"]=False;rejects(x)
    x=copy.deepcopy(ready);x["cross_video"]["related_claim_ids"]=["VKr060rIirM-05"];rejects(x)
    require(checked==18 and positive_paths==2,"self-test coverage")
    return {"negative_mutations_rejected":checked,
            "synthetic_positive_structure_paths":positive_paths}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--self-test",action="store_true")
    opt=p.parse_args()
    root=opt.root.resolve()
    result=validate_repo(root)
    if opt.self_test: result["self_test"]=self_test(root)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
if __name__=="__main__":
    try:
        main()
    except (OSError,ValueError,KeyError,TypeError,IndexError,OverflowError,ZeroDivisionError) as e:
        print(json.dumps({"status":"FAIL","exception":type(e).__name__,"problem":str(e)}))
        raise SystemExit(1)
