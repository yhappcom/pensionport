#!/usr/bin/env python3
"""Public video evidence + private suitability input CONTRACT. No owner data.
GitHub CI must never inspect, log, or store actual portfolio or suitability data.
"""
import argparse, copy, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
E="v5/evidence/V5_PUBLIC_EVIDENCE_20261030.json"
P="v5/policy/v5_private_suitability_contract_20261030.json"
DENY={"owner_holdings","account_number","investment_balance","real_cashflow","tax_ledger",
      "personal_profile","age_of_owner","actual_portfolio","private_owner_values",
      "user_email","user_phone","owner_income","owner_debts","risk_score"}
REGEX=re.compile(r"\b\d{6}[- ]?[1-4]\d{6}\b|-----BEGIN (?:RSA |EC )?PRIVATE KEY-----")
def check(v,msg):
    if not v: raise ValueError(msg)
def scan(v):
    if isinstance(v,dict):
        for k,x in v.items():
            check(k.lower() not in DENY,"private field in public gate: "+k)
            scan(x)
    elif isinstance(v,list):
        for x in v:scan(x)
    elif isinstance(v,str):
        check(REGEX.search(v) is None,"potential private identity")
def check_document(e,p):
    check(e["schema_version"]=="V5_PUBLIC_EVIDENCE_AND_SUITABILITY_GATE_20261030","schema")
    check(e["data_classification"]=="PUBLIC_VIDEO_RESEARCH_ONLY","classification")
    check(e["no_personal_profile_or_positions"] is True,"owner positions in public")
    check(e["client_suitability_approved"] is False and
          e["trade_execution_approved"] is False,"unearned permissions")
    check(e["all_26_legacy_open_resolved"] is False,"false OPEN resolution")
    ids=set()
    for x in e["public_evidence"]:
        check(x["id"] not in ids,"source duplicate")
        ids.add(x["id"])
        check(x["url"].startswith("https://"),"source URL")
        check(x["publisher"] and x["rule"] and x["source_as_of"] and
              x["status"] and x["private_dependency"],"missing applicability")
        check(x["videos"] and all(type(n)==int and 1<=n<=10 for n in x["videos"]),
              "wrong videos")
    check(len(ids)>=6,"core official sources omitted")
    check(p["schema_version"]=="V5_PRIVATE_SUITABILITY_CONTRACT_1.0","policy")
    check(p["L3_approved"] is False and p["L4_approved"] is False,"approved")
    check(p["current_owner_fields_collected"] is False,"private profile must not be public")
    check(p["decision_policy"]["not_all_checks_complete"]=="PERSONAL_ADVICE_BLOCKED",
          "incomplete profile wrongly approved")
    check(p["decision_policy"]["all_checks_complete"]==
          "REQUIRE_MANUAL_PRIVATE_REVIEW_NOT_AUTOMATIC_L3","auto approval")
    check(p["decision_policy"]["trade_execution"]=="ALWAYS_DISABLED","trade")
    categories=p["required_private_checks"]
    check(len(categories)==10 and len(set(categories))==10,"required evidence categories")
    scan(e);scan(p)
    return {"status":"PASS","public_source_records":len(ids),
            "personal_data_read_by_gate":0,"personal_approval":False}
def synthetic_assess(checklist,p):
    # CLIENT DATA MAY NEVER BE SENT HERE IN GITHUB CI. Pure boolean test only.
    keys=p["required_private_checks"]
    check(set(checklist)==set(keys),"wrong private category set")
    check(all(type(checklist[k]) is bool for k in keys),"no values beyond boolean completeness flags")
    complete=all(checklist.values())
    return "REQUIRE_MANUAL_PRIVATE_REVIEW_NOT_AUTOMATIC_L3" if complete else "PERSONAL_ADVICE_BLOCKED"
def self_test(e,p):
    checked=0
    def rejected(a,b):
        nonlocal checked
        try:check_document(a,b)
        except (ValueError,KeyError):checked+=1
        else:raise ValueError("bad evidence state accepted")
    x=copy.deepcopy(e);x["client_suitability_approved"]=True;rejected(x,p)
    x=copy.deepcopy(e);x["all_26_legacy_open_resolved"]=True;rejected(x,p)
    x=copy.deepcopy(e);x["public_evidence"][0]["url"]="http://example.org";rejected(x,p)
    x=copy.deepcopy(e);x["owner_holdings"]=[123];rejected(x,p)
    y=copy.deepcopy(p);y["L3_approved"]=True;rejected(e,y)
    y=copy.deepcopy(p);y["required_private_checks"].pop();rejected(e,y)
    y=copy.deepcopy(p);y["decision_policy"]["all_checks_complete"]="PERSONAL_ADVICE_APPROVED";rejected(e,y)
    check(checked==7,"negative tests")
    flags={k:False for k in p["required_private_checks"]}
    check(synthetic_assess(flags,p)=="PERSONAL_ADVICE_BLOCKED","empty record approved")
    flags={k:True for k in p["required_private_checks"]}
    check(synthetic_assess(flags,p)=="REQUIRE_MANUAL_PRIVATE_REVIEW_NOT_AUTOMATIC_L3",
          "all synthetic flags incorrectly auto-approved L3")
    flags[p["required_private_checks"][0]]=False
    check(synthetic_assess(flags,p)=="PERSONAL_ADVICE_BLOCKED","partly incomplete record approved")
    return {"negative_mutations_rejected":checked,"synthetic_boolean_suitability_tests":3}
def main():
    q=argparse.ArgumentParser()
    q.add_argument("--root",type=Path,default=ROOT)
    q.add_argument("--self-test",action="store_true")
    opts=q.parse_args();root=opts.root.resolve()
    e=json.loads((root/E).read_text(encoding="utf-8"))
    p=json.loads((root/P).read_text(encoding="utf-8"))
    result=check_document(e,p)
    if opts.self_test:result["tests"]=self_test(e,p)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
if __name__=="__main__":
    try:main()
    except (ValueError,KeyError,TypeError,OSError) as err:
        print(json.dumps({"status":"FAIL","reason":str(err)}))
        raise SystemExit(1)
