#!/usr/bin/env python3
"""Non-destructive V4 annual interest convention and bond-risk regression audit."""
from __future__ import annotations
import argparse, copy, json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = "data/synthesis/investment_knowledge_v4/reviews/v4_001_005_cross_layer_rereview_20261030.json"
MODELS = "data/synthesis/investment_knowledge_v4/models/decision_models_001_005_20261030.json"
V3_001 = "data/analysis_events/sz5N9WJS310.json"
V3_003 = "data/analysis_events/OiDTNstaSpM.json"
MANIFEST = "data/synthesis/investment_knowledge_v4/reviews/v4_001_005_final_closure_20261030.json"

class AuditFailure(ValueError):
    pass
def require(x,msg):
    if not x: raise AuditFailure(msg)
def read(root,filename):
    return json.loads((root/filename).read_text(encoding="utf-8"),
       parse_constant=lambda x: (_ for _ in ()).throw(AuditFailure("Invalid constant "+str(x))))
def fv(payment,monthly,months):
    return payment*((1+monthly)**months-1)/monthly if monthly else payment*months
def verify(root,audit):
    src=read(root,V3_001)
    bondsrc=read(root,V3_003)
    models=read(root,MODELS)
    manifest=read(root,MANIFEST)
    require(src["video_id"]=="sz5N9WJS310" and bondsrc["video_id"]=="OiDTNstaSpM","Source ID mismatched")
    require(manifest["historical_evidence"]["original_v3_claims"]==62, "Old claims changed")
    require(manifest["new_video_approvals"]==0, "Approval count changed")
    require(manifest["personalized_L3_approvals"]==manifest["implementation_L4_approvals"]==0,"Personal approval inflated")
    require(audit["checks"]["prior_claims"]==62 and audit["checks"]["prior_model_count"]==9 and audit["checks"]["extra_model_count"]==5,"Audit inventory")
    require(audit["checks"]["personal_action_approvals"]==0,"Audit action inflated")
    v3claim=next(c for c in src["core_claims"] if c["claim_id"]=="sz5N9WJS310-06")
    require("실효 연7%" in v3claim["claim"],"V3 effective-rate source text changed")
    model=next(c for c in models["models"] if c["id"]=="M01_ACCUMULATION")
    i=model["inputs"]
    require(i["nominal_annual_rate"]==0.07 and i["monthly_krw"]==300000 and set(i["months"])=={84,120},"V4 nominal basis changed")
    finding=next(c for c in audit["findings"] if c["finding_id"]=="CROSS-001-RATE-BASIS")
    output=finding["independent_recalculation"]["output_krw"]
    for months in (84,120):
        rate=i["nominal_annual_rate"]
        eff=(1+rate)**(1/12)-1
        nominal=round(fv(i["monthly_krw"],rate/12,months))
        effective=round(fv(i["monthly_krw"],eff,months))
        row=output[str(months)]
        require(row["nominal_annual_monthly_compounded"]==nominal, "Nominal convention "+str(months))
        require(row["effective_annual"]==effective, "Effective convention "+str(months))
        require(row["difference_nominal_minus_effective"]==nominal-effective, "Rate gap "+str(months))
        require(model["result_krw"][str(months)]==nominal, "Existing model regression "+str(months))
        require(effective<nominal, "Expected interest ordering")
    bond=next(c for c in bondsrc["core_claims"] if c["claim_id"]=="OiDTNstaSpM-05")
    finding=next(c for c in audit["findings"] if c["finding_id"]=="CROSS-003-BOND-RETURN")
    require(bond["verification"]=="QUALIFIED","Existing bond verdict unexpectedly upgraded")
    require("만기" in bond["claim"] and "원금" in bond["claim"],"Underlying bond claim changed")
    require(finding["classification"]=="EXPLICIT_RISK_QUALIFICATION_OF_EXISTING_V3","Bond risk unscoped")
    words=finding["disposition"].lower()
    require(all(w in words for w in ["default","etf","face value","inflation"]),"Bond caveats missing")
    require(len(finding["independent_primary_sources"])>=2,"Official bond sources missing")
    require(audit["overall_status"]=="CROSS_LAYER_REVIEW_COMPLETED_WITH_EXISTING_EXTERNAL_OPEN","Closure overstatement")
    require(audit["v4_study_status_after_review"]=="V4_DEEP_RESEARCH_COMPLETE_WITH_EXTERNAL_OPEN","Unexpected closure promotion")
    return 25

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,default=ROOT)
    ap.add_argument("--self-test",action="store_true")
    opts=ap.parse_args()
    try:
        root=opts.root.resolve()
        audit=read(root,AUDIT)
        n=verify(root,audit)
        if opts.self_test:
            bad=copy.deepcopy(audit)
            bad["findings"][0]["independent_recalculation"]["output_krw"]["84"]["effective_annual"]+=1000
            try:verify(root,bad)
            except AuditFailure:pass
            else:raise AuditFailure("Mutation failed to reject wrong effective FV")
            bad=copy.deepcopy(audit)
            next(c for c in bad["findings"] if c["finding_id"]=="CROSS-003-BOND-RETURN")["disposition"]="No issue"
            try:verify(root,bad)
            except AuditFailure:pass
            else:raise AuditFailure("Mutation failed to reject missing bond caveat")
        print(json.dumps({"status":"PASS","scope":"cross-layer assumption integrity only",
         "assertions":n,"self_test_mutations":2 if opts.self_test else 0}))
        return 0
    except (AuditFailure,OSError,ValueError,KeyError,IndexError,TypeError,OverflowError) as exc:
        print(json.dumps({"status":"FAIL","error":str(exc),"type":type(exc).__name__}))
        return 1
if __name__=="__main__":
    sys.exit(main())
