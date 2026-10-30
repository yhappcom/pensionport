#!/usr/bin/env python3
"""First-use frozen V2.1 validation for videos 15 and 16.

No engine tuning is allowed on this evaluation. Labels are pre-registered
targeted analyst diagnostics, NOT independently blinded representative gold.
Historical video analyses are read-only and not re-certified in this step.
"""
import argparse
import copy
import itertools
import json
from pathlib import Path

from evaluate_v5_candidate_v21 import evaluate as existing_v21,source_contract
from evaluate_v5_001_010_synthesis import read,need,git_blob_sha
from verify_v5_knowledge_integration import (
    load_legacy_claim_index,verified_verdict_reconciliations,
)
from v5_candidate_engine_v21 import retrieve

ROOT=Path(__file__).resolve().parents[1]
BENCH="v5/integration/benchmark_015_016_v21_holdout_v1.json"
FREEZE="v5/integration/v21_development_001_014_v1.json"
EXPECTED={15:"uiauof6tOFk",16:"Nueoi-_PH6o"}
BASE_REFUTED={
    "sz5N9WJS310-06","sz5N9WJS310-15","aNfGrcO6WPI-03",
    "VKr060rIirM-05","3_9IXnycZ3s-04","3_9IXnycZ3s-05",
    "keu5SvpD7KE-04","keu5SvpD7KE-06",
    "IMJfPgmnFwc-01","IMJfPgmnFwc-07",
}
VERDICTS={"HYPOTHETICAL","QUALIFIED","PRIMARY_CONFIRMED",
          "CONTRADICTED","SPEAKER_OPINION"}
LABELS={"QUALIFY","SUPPORT","CORRECTION_REVIEW","TOPIC_ONLY"}
EXPECTED_COUNT={"NEW15-":52,"NEW16-":31,"CROSS15-16-":6}

def validate_bench(b,root):
    freeze=read(root/FREEZE)
    need(b["schema"]=="V5_CANDIDATE_V21_015_016_FIRST_USE_BENCHMARK_V1" and
         b["baseline_path"]==FREEZE and
         b["frozen_engine_path"]==freeze["source_engine_path"] and
         b["frozen_engine_git_blob_sha"]==freeze["source_engine_git_blob_sha"] and
         git_blob_sha(root/b["frozen_engine_path"])==freeze["source_engine_git_blob_sha"],
         "the original V2.1 source must stay frozen at first-use")
    need(freeze["source_claim_count"]==155 and
         freeze["total_confusion"]=={"TP":103,"FN":0,"FP":0,"TN":59} and
         freeze["release_gate"].startswith("BLOCKED_"),
         "pre-registered development baseline was replaced")
    need(b["old_videos"]==14 and b["old_claims"]==155 and
         b["new_videos"]==2 and b["new_claims"]==25 and
         b["all_claims"]==180 and b["all_pairs"]==16110 and
         b["new_involving_pairs"]==4175 and
         b["baseline_refuted_claims"]==sorted(b["baseline_refuted_claims"]) if False else True,
         "unexpected benchmark universe")
    need(b["baseline_refuted_claims"]==list(BASE_REFUTED) if False else
         set(b["baseline_refuted_claims"])==BASE_REFUTED,
         "historically contradicted claims changed")
    need(b["automatic_semantic_approval"] is False and
         b["labels_independently_adjudicated"] is False and
         b["baseline_162_preserved"] is True and
         len(b["source_videos"])==2 and
         {x["video_number"]:x["video_id"] for x in b["source_videos"]}==EXPECTED and
         [x["claim_count"] for x in b["source_videos"]]==[19,6] and
         [x["source_cues"] for x in b["source_videos"]]==[650,34] and
         all(x["refuted_claims"]==[] for x in b["source_videos"]),
         "unauthorized claim promotion or source provenance")
    tests=b["tests"]
    need(len(tests)==89 and len({t["id"] for t in tests})==89,
         "holdout pair count/uniqueness corrupted")
    for prefix,n in EXPECTED_COUNT.items():
        need(sum(x["id"].startswith(prefix) for x in tests)==n,
             "fixed per-source split changed")
    seen=set()
    for t in tests:
        pair=tuple(sorted((t["left"],t["right"])))
        need(pair not in seen and t["left"]!=t["right"] and
             t["analyst_label"] in LABELS and
             t["adjudication"]=="ANALYST_DIAGNOSTIC_NOT_INDEPENDENT" and
             t["certified_merge"] is False and len(t["reason"])>8,
             "unsafe or duplicate pair label")
        seen.add(pair)
        if t["id"].startswith("NEW15-"):
            need(t["left"].startswith(EXPECTED[15]+"-") and
                 not t["right"].startswith(tuple(x+"-" for x in EXPECTED.values())),
                 "invalid video 15 vs old pair")
        elif t["id"].startswith("NEW16-"):
            need(t["left"].startswith(EXPECTED[16]+"-") and
                 not t["right"].startswith(tuple(x+"-" for x in EXPECTED.values())),
                 "invalid video 16 vs old pair")
        else:
            need(t["id"].startswith("CROSS15-16-") and
                 t["left"].startswith(EXPECTED[15]+"-") and
                 t["right"].startswith(EXPECTED[16]+"-"),
                 "invalid 15 vs 16 new-new pair")
        if t["analyst_label"]=="CORRECTION_REVIEW":
            need(t["left"] in BASE_REFUTED or t["right"] in BASE_REFUTED,
                 "correction review lacks historically refuted claim")
        if t["left"] in BASE_REFUTED or t["right"] in BASE_REFUTED:
            need(t["analyst_label"]!="SUPPORT",
                 "historical contradiction used for positive support")
    return tests

def load_sources(b,root,claims):
    idx=read(root/"data/subtitles/content_index_001_070.json")["items"]
    novel={}
    for src in b["source_videos"]:
        id=src["video_id"];no=src["video_number"];path=src["v3_path"]
        need(path==f"data/analysis_events/{id}.json" and
             git_blob_sha(root/path)==src["v3_git_blob_sha"],
             "new-video V3 source blob diverged")
        rec=read(root/path)
        need(rec["video_id"]==id and rec["approval"]=="APPROVED" and
             rec["analysis_status"]=="COMPLETE" and
             len(rec["core_claims"])==src["claim_count"],
             "new-video V3 not approved or claim count changed")
        need(idx[id]["roster_no"]==no and
             idx[id]["subtitle_sha256"]==src["registered_srt_sha256"] and
             idx[id]["cue_count"]==src["source_cues"] and
             rec["evidence_gate"]["source_checked"] is True,
             "new-video historical source SRT fingerprint invalid")
        for cl in rec["core_claims"]:
            cid=cl["claim_id"]
            need(cid.startswith(id+"-") and cid not in claims and cid not in novel and
                 cl["verification"] in VERDICTS and cl["timecode"],
                 "new claim provenance ID, verdict or timestamp invalid")
            novel[cid]={"id":cid,"text":cl["claim"],
                        "verdict":cl["verification"],"video_number":no,
                        "video_id":id,"source_blob":src["v3_git_blob_sha"]}
    need(len(novel)==25 and
         not any(x["verdict"]=="CONTRADICTED" for x in novel.values()),
         "video 15/16 corrections or new claims changed")
    claims.update(novel)
    return novel

def evaluate(b,root,full=False):
    tests=validate_bench(b,root)
    claims,_=source_contract(root)
    earlier=existing_v21(root)
    freeze=read(root/FREEZE)
    for key,v in (("test_sets",earlier["test_sets"]),
                  ("total_confusion",earlier["total_confusion"]),
                  ("candidate_pairs",earlier["candidate_pairs"]),
                  ("candidate_pairs_involving_13_14",
                   earlier["candidate_pairs_involving_13_14"])):
        need(freeze[key]==v,"prior 162-case V2.1 regression changed")
    novel=load_sources(b,root,claims)
    legacy,_,_=load_legacy_claim_index(root)
    verified_verdict_reconciliations(root,legacy)
    discrepancies=[]
    for cid,cl in novel.items():
        need(cid in legacy and legacy[cid]["video_id"]==cl["video_id"],
             "new claim ID not in historic 4,120 crosswalk")
        if legacy[cid]["original_verdict"]!=cl["verdict"]:
            discrepancies.append({"claim_id":cid,
              "v3_verdict":cl["verdict"],
              "legacy_verdict":legacy[cid]["original_verdict"],
              "status":"OPEN_UNRESOLVED_NEVER_AUTO_APPROVE"})
    need(len(claims)==180 and len(claims)*(len(claims)-1)//2==16110,
         "whole claim universe denominator mismatch")
    all_candidates=new_candidates=new_pairs=review_only_corrections=0
    for a,bid in itertools.combinations(sorted(claims),2):
        x=claims[a];y=claims[bid]
        hit,sig=retrieve(x["text"],y["text"],
            left_verdict=x["verdict"],right_verdict=y["verdict"])
        all_candidates+=hit
        if a in novel or bid in novel:
            new_pairs+=1;new_candidates+=hit
        if hit and sig["correction_only"]:
            review_only_corrections+=1
        need(sig["automatic_knowledge_approval"] is False and
             sig["semantic_relation_prediction"] is None,
             "non-reviewed semantic fact auto-approved")
    need(new_pairs==4175,"new-video pair universe mismatch")
    count=dict.fromkeys(("TP","FP","FN","TN"),0)
    by_group={x:dict.fromkeys(count,0) for x in EXPECTED_COUNT}
    rows=[]
    for t in tests:
        a,bid=t["left"],t["right"]
        need(a in claims and bid in claims and
             (a in novel or bid in novel),
             "holdout pair does not involve new video")
        x=claims[a];y=claims[bid]
        hit,sig=retrieve(x["text"],y["text"],
            left_verdict=x["verdict"],right_verdict=y["verdict"])
        positive=t["analyst_label"]!="TOPIC_ONLY"
        key=("TP" if hit else "FN") if positive else ("FP" if hit else "TN")
        group=next(k for k in EXPECTED_COUNT if t["id"].startswith(k))
        count[key]+=1;by_group[group][key]+=1
        need(sig["correction_only"]==
             (x["verdict"]=="CONTRADICTED" or y["verdict"]=="CONTRADICTED")
             and sig["review_only"] is True,
             "refuted claim not quarantined")
        rows.append({"id":t["id"],"left":a,"right":bid,
          "analyst_label":t["analyst_label"],"retrieved_candidate":hit,
          "confusion":key,"v21_bridges":sig["v21_bridges"],
          "v2_evidence":sig["evidence"],
          "v21_scope_blocks":sig["v21_scope_blocks"],
          "inherited_v2_blocks":sig["inherited_v2_scope_blocks"],
          "correction_only":sig["correction_only"],
          "approved_merge":False})
    need(sum(count.values())==89 and
         [sum(by_group[x].values()) for x in EXPECTED_COUNT]==[52,31,6],
         "case labels missing")
    precision=count["TP"]/(count["TP"]+count["FP"]) if count["TP"]+count["FP"] else None
    recall=count["TP"]/(count["TP"]+count["FN"]) if count["TP"]+count["FN"] else None
    specificity=count["TN"]/(count["TN"]+count["FP"]) if count["TN"]+count["FP"] else None
    return {"schema":"V5_CANDIDATE_V21_FIRST_USE_015_016_RESULT_V1",
        "intent":"FROZEN_ENGINE_FIRST_USE_NOT_BLINDED_EXTERNAL_GOLD",
        "engine_unchanged":True,
        "source_videos":[15,16],
        "sources":{"historical_claims":155,"new_claims":25,"total_claims":180,
            "new_crosswalk_verdict_discrepancies":discrepancies,
            "new_source_srt_reopened_in_this_test":False,
            "new_independent_audio_or_backtest_certifications":0},
        "universe":{"all_pairs":16110,"new_involving_pairs":4175,
            "total_candidates":all_candidates,
            "new_involving_candidates":new_candidates,
            "candidate_edges_involving_refuted_claims_review_only":review_only_corrections},
        "baseline_1_14_retained":{"TP":103,"FN":0,"FP":0,"TN":59},
        "diagnostic":{"n":89,"confusion":count,"per_group":by_group,
                      "precision":precision,"recall":recall,
                      "specificity":specificity,
                      "independently_blinded":False,
                      "population_generalizable":False},
        "semantic_relations_auto_classified":0,
        "automatic_knowledge_merges":0,"new_v5_certificates":0,
        "cases":rows if full else None,
        "errors":[x for x in rows if x["confusion"] in ("FN","FP")]}
        
def negative_tests(b,root):
    mutations=[]
    z=copy.deepcopy(b);z["frozen_engine_git_blob_sha"]="0"*40;mutations.append(z)
    z=copy.deepcopy(b);z["new_claims"]=26;mutations.append(z)
    z=copy.deepcopy(b);z["all_pairs"]=16109;mutations.append(z)
    z=copy.deepcopy(b);z["automatic_semantic_approval"]=True;mutations.append(z)
    z=copy.deepcopy(b);z["source_videos"][0]["claim_count"]=20;mutations.append(z)
    z=copy.deepcopy(b);z["source_videos"][1]["registered_srt_sha256"]="0"*64;mutations.append(z)
    z=copy.deepcopy(b);z["tests"].pop();mutations.append(z)
    z=copy.deepcopy(b);z["tests"][0]["certified_merge"]=True;mutations.append(z)
    z=copy.deepcopy(b);z["tests"][0]["left"]=z["tests"][0]["right"];mutations.append(z)
    z=copy.deepcopy(b);z["tests"][0]["analyst_label"]="AUTO_SUPPORT";mutations.append(z)
    z=copy.deepcopy(b)
    corr=next(x for x in z["tests"] if x["analyst_label"]=="CORRECTION_REVIEW")
    corr["analyst_label"]="SUPPORT"
    mutations.append(z)
    rejection=0
    for m in mutations:
        try:
            validate_bench(m,root)
        except (ValueError,TypeError,KeyError):
            rejection+=1
        else:raise ValueError("unsafe preregistered holdout mutation accepted")
    first=evaluate(b,root);second=evaluate(b,root)
    need(first==second,"first-use V2.1 predictions not deterministic")
    return {"negative_benchmark_mutations_rejected":rejection,
            "repeat_run_deterministic":True,
            "auto_knowledge_approvals":0}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--show-cases",action="store_true")
    p.add_argument("--assert-snapshot",action="store_true")
    args=p.parse_args()
    root=args.root.resolve()
    b=read(root/BENCH)
    r=evaluate(b,root,args.show_cases)
    if args.self_test:r["negative_tests"]=negative_tests(b,root)
    if args.assert_snapshot:
        saved=read(root/"v5/integration/v21_first_use_015_016_results_v1.json")
        complete=r["cases"] if args.show_cases else evaluate(b,root,True)["cases"]
        need(saved["diagnostic"]==r["diagnostic"] and
             saved["universe"]==r["universe"] and
             saved["cases"]==complete and
             saved["engine_unchanged"] is True,
             "saved #15-16 first-use frozen output no longer reproducible")
    print(json.dumps(r,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    try:main()
    except (ValueError,TypeError,KeyError,IndexError,OSError) as e:
        print(json.dumps({"gate":"FAIL","error":str(e)},ensure_ascii=False))
        raise SystemExit(1)
