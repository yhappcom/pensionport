#!/usr/bin/env python3
"""V2.3 retrospective development replay #1-18, never unseen generalization.

Includes 251 earlier DEVELOPMENT pairs plus 93 USED #17-18 FIRST-USE pairs.
The latter are now development examples because V2.3 was improved from them.
No #19+ video may be accessed or added to this evaluator.
"""
import argparse
import itertools
import json
from collections import Counter
from pathlib import Path

from evaluate_v5_001_010_synthesis import read,need,git_blob_sha
from evaluate_v5_candidate_v22 import source_contract_v22
from evaluate_v5_candidate_v22_017_018 import (
    validate_benchmark, BENCH as PREVIOUS_17_18_BENCH,
    EXPECTED_BENCH_BLOB as PREVIOUS_17_18_BLOB,
)
from v5_candidate_engine_v23 import retrieve_claims

ROOT=Path(__file__).resolve().parents[1]
SNAP="v5/integration/v23_development_001_018_v1.json"
ARCHIVE="v5/integration/v23_case_results_001_018_v1.json"
ORIGINAL_17_18_RESULT="v5/integration/v22_first_use_017_018_results_v1.json"
PREVIOUS_V22_RESULT_BLOB="95da7fc873734a91f6c9f18340925f18e2a53de3"
EXPECTED_V22_FIRST_USE={"FN":19,"FP":2,"TN":36,"TP":36}
EXPECTED_OLD_DEV={"TP":164,"FN":0,"FP":0,"TN":87}
GROUP_COUNTS={
 "legacy_38":38,"next_60":60,"new_13_14_64":64,
 "dev_15_16_89":89,"dev_17_18_93":93,
}
REFUTED_N=11

def safe_div(num,den):
    return round(num/den,6) if den else None

def source_contract_v23(root):
    old,old_cases=source_contract_v22(root)
    full,new_cases=validate_benchmark(root,read(root/PREVIOUS_17_18_BENCH))
    need(git_blob_sha(root/PREVIOUS_17_18_BENCH)==PREVIOUS_17_18_BLOB,
         "preexisting diagnostic preregistration changed")
    need(git_blob_sha(root/ORIGINAL_17_18_RESULT)==PREVIOUS_V22_RESULT_BLOB,
         "V2.2 new-video first-use failure evidence mutated")
    prior=read(root/ORIGINAL_17_18_RESULT)
    need(prior["diagnostic"]["confusion"]==EXPECTED_V22_FIRST_USE
         and prior["diagnostic"]["case_count"]==93
         and prior["universe"]["all_pairs"]==18721
         and prior["universe"]["all_candidates"]==2574
         and prior["universe"]["new_involving_candidates"]==363,
         "V2.2 original first-use confusion/candidate totals not preserved")
    need(len(old)==180 and len(full)==194 and
         len(old_cases)==251 and len(new_cases)==93 and
         all(cid in full and old[cid]==full[cid] for cid in old),
         "original 180 claim values or 194 inventory changed")
    need({c["id"] for c in full.values() if c["verdict"]=="CONTRADICTED"}
         ==set(prior["new_contradicted_claim_ids"]) |
           set(__import__("evaluate_v5_candidate_v22").VERDICTS_REFUTED),
         "11 original refuted claim IDs changed")
    ids={t["id"] for t in old_cases+new_cases}
    need(len(ids)==344,"duplicate or lost 344 development diagnosis IDs")
    return full,old_cases+new_cases

def group_of(caseid):
    if caseid.startswith("PAIR-"):return "legacy_38"
    if caseid.startswith("H"):return "next_60"
    if caseid.startswith(("NEW13-","NEW14-")):return "new_13_14_64"
    if caseid.startswith(("NEW15-","NEW16-","CROSS15-16-")):
        return "dev_15_16_89"
    if caseid.startswith(("NEW17-","NEW18-","CROSS17-18-")):
        return "dev_17_18_93"
    raise ValueError("UNKNOWN_REGRESSION_TEST_GROUP: "+caseid)

def evaluate(root,include_cases=False):
    claims,cases=source_contract_v23(root)
    groups={name:dict.fromkeys(("TP","FP","FN","TN"),0)
            for name in GROUP_COUNTS}
    labels=Counter()
    rows=[]
    for t in cases:
        a,b=claims[t["left"]],claims[t["right"]]
        hit,detail=retrieve_claims(a,b)
        need(detail["review_only"] is True and
             detail["source_provenance_required"] is True and
             detail["automatic_knowledge_approval"] is False and
             detail["automatic_merge_permitted"] is False and
             detail["semantic_relation_prediction"] is None and
             detail["research_completion_certificate_permitted"] is False and
             detail["investment_trade_instruction_permitted"] is False and
             detail["correction_only"]==(
                 a["verdict"]=="CONTRADICTED" or
                 b["verdict"]=="CONTRADICTED"),
             "review-only source/provenance/contradiction constraint breached")
        expected=t["analyst_label"]!="TOPIC_ONLY"
        quadrant=("TP" if hit else "FN") if expected else ("FP" if hit else "TN")
        grp=group_of(t["id"])
        groups[grp][quadrant]+=1
        labels[t["analyst_label"]+"_"+quadrant]+=1
        rows.append({
          "id":t["id"],"left":t["left"],"right":t["right"],
          "expected_label":t["analyst_label"],"confusion":quadrant,
          "predicted_candidate":hit,
          "inherited_v22_candidate":detail["v23_inherited_v22_candidate"],
          "v23_bridges":detail["v23_bridges"],
          "v23_scope_blocks":detail["v23_scope_blocks"],
          "inherited_v22_scope_blocks":detail["v23_inherited_scope_blocks"],
          "source_risk":detail["source_risk"],
          "correction_only":detail["correction_only"],
          "automatic_merge_permitted":False,
        })
    need({k:sum(v.values()) for k,v in groups.items()}==GROUP_COUNTS,
         "V2.3 diagnostic grouping/coverage drift")
    total={k:sum(x[k] for x in groups.values())
           for k in ("TP","FP","FN","TN")}
    count=new_count=new_pairs=added=vetoed=refuted=hypothetical=0
    new_video_degrees=Counter()
    reasons=Counter()
    for aid,bid in itertools.combinations(sorted(claims),2):
        a,b=claims[aid],claims[bid]
        hit,detail=retrieve_claims(a,b)
        prior=detail["v23_inherited_v22_candidate"]
        if hit and not prior:added+=1
        if not hit and prior:vetoed+=1
        count+=int(hit)
        if a["video_number"]>=17 or b["video_number"]>=17:
            new_pairs+=1
            if hit:
                new_count+=1
                if a["video_number"]>=17:new_video_degrees[aid]+=1
                if b["video_number"]>=17:new_video_degrees[bid]+=1
        if hit:
            reasons.update(detail["v23_bridges"])
            refuted+=int(detail["source_risk"]=="CORRECTION_ONLY")
            hypothetical+=int(detail["source_risk"]=="UNREPLICATED_HYPOTHETICAL_SOURCE")
            need(not detail["automatic_merge_permitted"] and
                 detail["semantic_relation_prediction"] is None,
                 "unguarded candidate in full universe")
    need(new_pairs==2611 and count>=0 and new_count>=0 and
         len(claims)*(len(claims)-1)//2==18721,
         "194-claim comparison universe changed")
    bygrp={k:{"confusion":v,
              "precision":safe_div(v["TP"],v["TP"]+v["FP"]),
              "recall":safe_div(v["TP"],v["TP"]+v["FN"]),
              "specificity":safe_div(v["TN"],v["TN"]+v["FP"])}
           for k,v in groups.items()}
    dev={"case_count":344,"total_confusion":total,
         "precision":safe_div(total["TP"],total["TP"]+total["FP"]),
         "recall":safe_div(total["TP"],total["TP"]+total["FN"]),
         "specificity":safe_div(total["TN"],total["TN"]+total["FP"]),
         "by_group":bygrp,"by_label_confusion":dict(labels)}
    return {
      "schema":"V5_CANDIDATE_V23_RETROSPECTIVE_DEVELOPMENT_REPLAY_001_018_V1",
      "kind":"POST_HOC_TUNING_ON_ALL_344_CASES_NOT_INDEPENDENT_HOLDOUT",
      "engine_version":"2.3.0",
      "videos":18,"claims":194,"case_count":344,
      "development":dev,
      "v22_frozen_first_use_baseline":EXPECTED_V22_FIRST_USE,
      "universe":{
        "all_possible_pairs":18721,"new_videos_involving_possible_pairs":2611,
        "v22_baseline_candidate_pairs":2574,
        "v23_candidate_pairs":count,
        "v23_candidates_involving_17_18":new_count,
        "added_candidates_vs_v22":added,
        "suppressed_candidates_vs_v22":vetoed,
        "candidates_involving_refuted_claims_correction_only":refuted,
        "candidates_involving_hypothetical_claims_review_only":hypothetical,
        "new_video_candidate_degree":dict(sorted(new_video_degrees.items())),
        "v23_bridge_frequency":dict(reasons.most_common()),
      },
      "case_results":rows if include_cases else None,
      "remaining_errors":[r for r in rows if r["confusion"] in ("FP","FN")],
      "independent_blinded":False,
      "newly_unseen_video_validation_performed":False,
      "new_research_completion_certificates":0,
      "automatic_knowledge_approvals":0,
      "automatic_trade_instructions":0,
      "production_release":"BLOCKED_PENDING_19_PLUS_UNSEEN_INDEPENDENT_EVALUATION",
    }

def adversarial(root):
    claims,cases=source_contract_v23(root)
    count=0
    for t in cases:
        a,b=claims[t["left"]],claims[t["right"]]
        hit,detail=retrieve_claims(a,b)
        rev,revdetail=retrieve_claims(b,a)
        need(hit==rev and
             detail["correction_only"]==revdetail["correction_only"] and
             detail["source_risk"]==revdetail["source_risk"],
             "V2.3 pair order dependent or changed source risk")
        count+=1
    a=next(c for c in claims.values() if c["video_number"]==17)
    b=next(c for c in claims.values() if c["video_number"]==18)
    mutations=[dict(a,verdict=None),dict(a,verdict="TRUE"),
               dict(a,video_id="x"*11),dict(a,id="invalid"),
               dict(a,video_number=False),dict(a,text=""),
               dict(a,text=None),dict(a,video_number=0)]
    for v in mutations:
        try:retrieve_claims(v,b)
        except (ValueError,TypeError):pass
        else:raise ValueError("invalid V2.3 provenance mutation accepted")
    first=evaluate(root,False)
    need(first==evaluate(root,False),"V2.3 18721 pair deterministic replay failed")
    return {"source_mutations_rejected":len(mutations),
            "pair_order_symmetry_cases":count,
            "full_18721_pair_double_replay_deterministic":True,
            "contradicted_claims_total":REFUTED_N,
            "automatic_merges":0}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--show-cases",action="store_true")
    p.add_argument("--assert-snapshot",action="store_true")
    args=p.parse_args()
    root=args.root.resolve()
    out=evaluate(root,args.show_cases)
    if args.self_test:out["negative_tests"]=adversarial(root)
    if args.assert_snapshot:
        snapshot=read(root/SNAP)
        need(snapshot["engine_git_blob_sha"]==
             git_blob_sha(root/"scripts/v5_candidate_engine_v23.py"),
             "V2.3 frozen development engine code SHA changed")
        need(snapshot["evaluator_git_blob_sha"]==
             git_blob_sha(root/"scripts/evaluate_v5_candidate_v23.py"),
             "V2.3 evaluation harness SHA changed")
        for key in ("development","universe","production_release"):
            need(snapshot[key]==out[key],"V2.3 frozen diagnostic drift: "+key)
        a=read(root/ARCHIVE)
        rows=out["case_results"] if args.show_cases else evaluate(root,True)["case_results"]
        need(a["engine_git_blob_sha"]==snapshot["engine_git_blob_sha"] and
             a["case_results"]==rows,
             "V2.3 344-case original predictions were modified")
    print(json.dumps(out,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    try:main()
    except (OSError,ValueError,TypeError,KeyError,IndexError) as exc:
        print(json.dumps({"gate":"FAIL","error":str(exc)},ensure_ascii=False))
        raise SystemExit(1)
