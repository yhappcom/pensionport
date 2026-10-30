#!/usr/bin/env python3
"""V2 retrospective development regression on previously reviewed #1-#12.

#1-#10 38 diagnostic cases and #11-#12 60 failures are NOT an independent
evaluation after V2 development. The #13-#14 first-use set must remain sealed
until this candidate engine and operating contract are frozen.
"""
import argparse
import copy
import itertools
import json
from pathlib import Path

from evaluate_v5_001_010_synthesis import (
  BENCH,CURATED,documents,read,need,git_blob_sha,
)
from evaluate_v5_011_012_holdout import (
  HOLDOUT,contract as holdout_contract,sources as load_new_sources,
)
from verify_v5_knowledge_integration import (
  load_legacy_claim_index,verified_verdict_reconciliations,
)
from v5_candidate_engine_v2 import retrieve

ROOT=Path(__file__).resolve().parents[1]
SNAPSHOT="v5/integration/v2_development_001_012_v1.json"
BLOCKED_010={"sz5N9WJS310-06","sz5N9WJS310-15",
             "aNfGrcO6WPI-03","VKr060rIirM-05"}
BLOCKED_012={"3_9IXnycZ3s-04","3_9IXnycZ3s-05"}

def data(root):
    a=read(root/BENCH)
    b=read(root/HOLDOUT)
    holdout_contract(b)
    need(a["claim_count"]==122 and len(a["tests"])==38
         and b["new_original_claim_count"]==15
         and len(b["holdout_tests"])==60
         and set(b["source_blocked_correction_only_ids"])==BLOCKED_012,
         "original 1-12 diagnostic test denominators changed")
    need(git_blob_sha(root/b["frozen_engine_path"])==
         b["frozen_engine_git_blob_sha"],
         "frozen V1 must not be retrained during V2 development")
    claims,n,reviews,_,_=documents(root,a)
    new=load_new_sources(b,root,claims,n,reviews)
    need(len(claims)==137 and len(new)==15,"missing V3 #11-12 sources")
    old,_,_=load_legacy_claim_index(root)
    verified_verdict_reconciliations(root,old)
    need(all(cid in old and cid in claims and
             old[cid]["video_id"]==claims[cid]["video_id"] for cid in claims),
         "all historical claim IDs must match 4,120 crosswalk")
    tests=a["tests"]+b["holdout_tests"]
    need(len({x["id"] for x in tests})==98,"duplicate diagnostic ids")
    return a,b,claims,tests

def evaluate(root,details=False):
    a,b,claims,tests=data(root)
    counts={"old_38":{"TP":0,"FP":0,"FN":0,"TN":0},
            "added_60":{"TP":0,"FP":0,"FN":0,"TN":0}}
    failures=[]
    pairs=[]
    for t in tests:
        left=claims[t["left"]];right=claims[t["right"]]
        retrieved,explain=retrieve(
            left["text"],right["text"],left_verdict=left["verdict"],
            right_verdict=right["verdict"])
        relevant=t["analyst_label"]!="TOPIC_ONLY"
        quadrant=(("TP" if retrieved else "FN") if relevant
                  else ("FP" if retrieved else "TN"))
        category="old_38" if t["id"].startswith("PAIR-") else "added_60"
        counts[category][quadrant]+=1
        row={"pair_id":t["id"],"label":t["analyst_label"],
             "retrieved":retrieved,"confusion":quadrant,
             "left":t["left"],"right":t["right"],
             "evidence":explain["evidence"],"scope_blocks":explain["scope_blocks"],
             "correction_only":explain["correction_only"]}
        pairs.append(row)
        if quadrant in ("FP","FN"):failures.append(row)
    groupstats={}
    for k,c in counts.items():
        groupstats[k]={"confusion":c,
          "precision":c["TP"]/(c["TP"]+c["FP"]) if c["TP"]+c["FP"] else None,
          "recall":c["TP"]/(c["TP"]+c["FN"]) if c["TP"]+c["FN"] else None,
          "specificity":c["TN"]/(c["TN"]+c["FP"]) if c["TN"]+c["FP"] else None}
    grand={k:sum(z[k] for z in counts.values()) for k in ("TP","FP","FN","TN")}
    candidates=0;new_pairs=0;new_candidates=0; correction_candidates=0
    ids=sorted(claims)
    for a,b in itertools.combinations(ids,2):
        x,y=claims[a],claims[b]
        found,_=retrieve(x["text"],y["text"],left_verdict=x["verdict"],
                         right_verdict=y["verdict"])
        candidates+=found
        newflag=x["video_number"]>10 or y["video_number"]>10
        if newflag:
            new_pairs+=1;new_candidates+=found
        if found and (x["verdict"]=="CONTRADICTED" or y["verdict"]=="CONTRADICTED"):
            correction_candidates+=1
    need(new_pairs==1935 and len(ids)*(len(ids)-1)//2==9316,"pair universe")
    need(sum(grand.values())==98 and
         len(pairs)==98 and len(failures)==grand["FP"]+grand["FN"],
         "V2 measurement must keep all original diagnostic cases")
    need({cid for cid,c in claims.items() if c["verdict"]=="CONTRADICTED"}==
         BLOCKED_010|BLOCKED_012,
         "one or more historically contradicted claims were lost")
    need(all(x["correction_only"] for x in pairs
             if x["left"] in BLOCKED_010|BLOCKED_012 or
                x["right"] in BLOCKED_010|BLOCKED_012),
         "V2 must not allow contradicted claims to act as positive evidence")
    return {"schema":"V5_CANDIDATE_V2_DEVELOPMENT_REPLAY_V1",
       "assessment_kind":"RETROSPECTIVE_DEVELOPMENT_SET_NOT_INDEPENDENT_HOLDOUT",
       "engine_version":"2.0.0","videos":12,"claims":137,
       "total_possible_pairs":9316,"new_involving_pairs":1935,
       "total_candidates":candidates,"new_involving_candidates":new_candidates,
       "candidate_edges_involving_refuted_claims_review_only":correction_candidates,
       "test_sets":groupstats,"overall_diagnostic_confusion":grand,
       "independently_adjudicated_gold":False,
       "automatic_semantic_relation_labels":0,
       "auto_approved_knowledge_merges":0,
       "historic_source_files_changed":False,
       "failures":failures if details else None,
       "case_results":pairs if details else None}

def adversarial(root):
    # These are contract and negative source tests; meaningful financial
    # completeness still requires human/independent evidence review.
    a,b,claims,tests=data(root)
    invalid=[
      ({"left":"FAKE","right":tests[0]["right"]},"unknown claim"),
      ({"left":tests[0]["left"],"right":tests[0]["left"]},"identical claim"),
    ]
    rejected=0
    for x,_ in invalid:
        try:
            need(x["left"] in claims and x["right"] in claims
                 and x["left"]!=x["right"],"invalid pair")
        except ValueError:rejected+=1
        else:raise ValueError("invalid claim source accepted")
    for cid in sorted(BLOCKED_010|BLOCKED_012):
        src=claims[cid]
        yes,flags=retrieve(src["text"],src["text"],
                           left_verdict=src["verdict"],right_verdict=src["verdict"])
        need(flags["correction_only"] and flags["review_only"],
             "contradicted claim promoted into positive verified knowledge")
    x=evaluate(root)
    y=evaluate(root)
    need(x==y,"non-deterministic V2 replay")
    return {"corrupted_claim_input_rejected":rejected,
            "blocked_source_claims_review_only":len(BLOCKED_010|BLOCKED_012),
            "exact_replay":True,
            "independent_adjudication_completed":False}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,default=ROOT)
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--show-pairs",action="store_true")
    ap.add_argument("--assert-snapshot",action="store_true")
    args=ap.parse_args()
    root=args.root.resolve()
    result=evaluate(root,args.show_pairs)
    if args.self_test: result["regression"]=adversarial(root)
    if args.assert_snapshot:
        a=read(root/SNAPSHOT)
        for field in ("test_sets","overall_diagnostic_confusion",
                      "total_candidates","new_involving_candidates"):
            need(a[field]==result[field],"V2 replay snapshot drift: "+field)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    try:main()
    except (ValueError,TypeError,KeyError,IndexError,OSError) as e:
        print(json.dumps({"gate":"FAIL","error":str(e)},ensure_ascii=False))
        raise SystemExit(1)
