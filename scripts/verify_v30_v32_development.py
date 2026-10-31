#!/usr/bin/env python3
"""V3.2 development-only regression on SEEN #1-5 and exposed #61-65 gold.

These gold pairs were accessed in earlier V3.1 work, and are NOT unseen.
"""
import argparse,json
from collections import Counter
from pathlib import Path
from v30_verified_core import policy_gate,guard
from v30_semantic_v32 import pair_review_v32,facets_v32,review_queue_v32
from v30_independent_evaluator import stats

ROOT=Path(__file__).resolve().parents[1]
IDS={1:"sz5N9WJS310",2:"6VEfKF7BzZU",3:"OiDTNstaSpM",
     4:"aNfGrcO6WPI",5:"qtluAViPpsQ",
     61:"7RRWNL0V6As",62:"w1ZgJwm-_KU",63:"LVE7XN_esTc",
     64:"aUW6waebLl8",65:"NOl9u50dgao"}
GROUPS={
 "001_005":"v30/validation/retro_001_005_diagnostic_cases_v1.json",
 "061_065":"v30/validation/v31_061_065_historical_cohort_prereg_v1.json"
}
def run(root):
    policy_gate(root)
    by={}
    for n,vid in IDS.items():
        source=json.loads((root/f"data/analysis_events/{vid}.json").read_text())
        guard(source["approval"]=="APPROVED","UNREVIEWED_V3_HISTORICAL_SOURCE")
        for atom in source["core_claims"]:
            by[atom["claim_id"]]={
             "claim_id":atom["claim_id"],"text":atom["claim"],
             "legacy_verdict":atom["verification"],"video_number":n,
            }
    groups={}
    for kind,path in GROUPS.items():
        gold=json.loads((root/path).read_text())
        counts=Counter();cases=[]
        for c in gold["cases"]:
            pair=pair_review_v32(by[c["left"]],by[c["right"]])
            correct=c.get("review_relevant")
            got=pair["typed_review_candidate"]
            counts[("TP" if correct else "FP") if got else
                   ("FN" if correct else "TN")]+=1
            guard(not pair["automatic_relation_approval"] and
                  not pair["automatic_knowledge_merge"] and
                  not pair["research_completion_certificate_approved"],
                  "UNSAFE_V32_DEV_ADVICE_OR_KNOWLEDGE_APPROVAL")
            if "CONTRADICTED" in (
                by[c["left"]]["legacy_verdict"],
                by[c["right"]]["legacy_verdict"]):
                guard(pair["legacy_verdict_source_risk"]=="CORRECTION_ONLY",
                      "REFUTED_V32_CLAIM_POSITIVELY_PROMOTED")
            cases.append({
                "id":c["id"],"original_gold":correct,
                "v32_typed_pair_review":got,
                "matching_tags":pair["matching_financial_event_tags"],
                "blocked_cross_scope":pair["cross_scope_conflicts"],
            })
        groups[kind]={
            "n":len(cases),
            "diagnostic":stats({s:counts[s] for s in ("TP","FN","FP","TN")}),
            "cases":cases,
            "full_population_or_independently_blinded":False
        }
    unused=sum(not facets_v32(v["text"]) for k,v in by.items()
               if v["video_number"] in range(61,66))
    # Queue is review-only even when a short predicate is relevant.
    hold=[v for v in by.values() if v["video_number"]==63]
    preview=review_queue_v32(hold[0],hold,limit=5)
    guard(preview["automatic_knowledge_merge"] is False
          and preview["all_corpus_claims_accounted_for"]==len(hold),
          "UNREVIEWED_V32_QUEUE_WAS_AUTOMATICALLY_APPROVED")
    return {
        "schema":"V32_PRIOR_SEEN_DEVELOPMENT_EVALUATION_V1",
        "training_or_diagnostic_exposure":"001_005_AND_061_065_EXPOSED_AFTER_V31_FIRST_USE",
        "groups":groups,
        "original_061_065_claims_with_no_event_tags":unused,
        "development_only_not_unseen":True,
        "frozen_V31_firstuse_preserved":True,
        "new_model_RELEASE_APPROVED":False,
        "automatic_knowledge_approvals":0,
        "original_V3_V4_V5_v30_v31_unchanged":True,
    }
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--assert-snapshot",action="store_true")
    args=p.parse_args()
    try:
        result=run(args.root)
        if args.assert_snapshot:
            sp=args.root/"v30/validation/v32_seen_dev_result_v1.json"
            guard(sp.is_file() and json.loads(sp.read_text())==result,
                  "V32_DEVELOPMENT_BASELINE_DRIFT")
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
    except (ValueError,KeyError,TypeError) as e:
        print(json.dumps({"gate":"FAIL","error":str(e)},ensure_ascii=False))
        raise SystemExit(1)
