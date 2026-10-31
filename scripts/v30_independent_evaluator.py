#!/usr/bin/env python3
"""Unseen / historical exposure-aware relation retrieval evaluator.

Predictions are consumed only after separate precommitted gold labels. Supports
per-domain confusion, Wilson 95% intervals and candidate/noncandidate review.
Never treats an analyst-selected nonblind sample as population accuracy.
"""
import argparse
import hashlib
import json
import math
from collections import Counter,defaultdict
from pathlib import Path

from v30_verified_core import guard,sha256,canonical

Z=1.959963984540054

def wilson(successes,total,z=Z):
    if total==0:return None
    p=successes/total
    denom=1+z*z/total
    center=(p+z*z/(2*total))/denom
    margin=(z/denom)*math.sqrt(p*(1-p)/total+z*z/(4*total*total))
    return {"lower":round(max(0,center-margin),6),
            "upper":round(min(1,center+margin),6),
            "observed_rate":round(p,6),"n":total}

def stats(conf):
    tp,fn,fp,tn=(conf[k] for k in ("TP","FN","FP","TN"))
    return {
       "counts":dict(conf),
       "precision":wilson(tp,tp+fp),
       "recall":wilson(tp,tp+fn),
       "specificity":wilson(tn,tn+fp),
       "positive_diagnoses":tp+fn,
       "negative_diagnoses":fp+tn,
    }

def evaluate(benchmark,predictions,require_independent=True):
    guard(benchmark.get("schema")=="V30_PREREGISTERED_RELATION_BENCHMARK_V1"
          and predictions.get("schema")=="V30_FROZEN_RELATION_PREDICTIONS_V1",
          "PRE_REGISTERED_BENCHMARK_AND_PREDICTIONS_REQUIRED")
    guard(benchmark.get("engine_blob_sha")==
          predictions.get("engine_blob_sha")
          and benchmark.get("index_sha256")==
          predictions.get("index_sha256"),
          "EVALUATION_ENGINE_OR_INDEX_CHANGED_AFTER_REGISTRATION")
    gold=benchmark.get("cases");pred=predictions.get("cases")
    guard(isinstance(gold,list) and bool(gold) and isinstance(pred,list),
          "EVALUATION_GOLD_PREDICTIONS_MISSING")
    guard(len({a["id"] for a in gold})==len(gold) and
          len({a["id"] for a in pred})==len(pred) and
          {a["id"] for a in gold}=={a["id"] for a in pred},
          "CASE_IDS_MISSING_EXTRA_OR_DUPLICATED")
    blind=benchmark.get("independent_blinded_adjudication") is True
    history=benchmark.get("historical_index_exposure")
    guard(history in ("UNEXPOSED_TO_MODEL_AND_REVIEWER",
                      "PREVIOUSLY_EXPOSED_HISTORICAL_INDEX"),
          "HISTORICAL_METADATA_EXPOSURE_UNDISCLOSED")
    prespecified=benchmark.get("committed_before_predictions") is True
    if require_independent:
        guard(blind and prespecified and
              history=="UNEXPOSED_TO_MODEL_AND_REVIEWER"
              and benchmark.get("sampling_method") in
                  ("STRATIFIED_PROBABILITY","CENSUS"),
              "NEVER_CLAIM_INDEPENDENT_GENERALIZATION_FROM_DEVELOPMENT_CASES")
    pmap={x["id"]:x for x in pred}
    cells=Counter();grouped=defaultdict(Counter)
    missed=[];false=[]
    for g in gold:
        q=pmap[g["id"]]
        guard(type(g.get("related")) is bool and
              type(q.get("candidate")) is bool and
              g.get("stratum") and
              isinstance(g.get("relation_type"),str) and
              g.get("video_number") and
              g.get("independent_reviewer_reference"),
              "INCOMPLETE_INDEPENDENT_CASE_CLASSIFICATION")
        hit=q["candidate"]
        actual=g["related"]
        cell=("TP" if hit else "FN") if actual else ("FP" if hit else "TN")
        cells[cell]+=1
        grouped[str(g["stratum"])][cell]+=1
        if cell=="FN":missed.append(g["id"])
        if cell=="FP":false.append(g["id"])
    total={k:cells[k] for k in ("TP","FN","FP","TN")}
    by={k:stats({key:values[key] for key in ("TP","FN","FP","TN")})
        for k,values in sorted(grouped.items())}
    score=stats(total)
    requirements=benchmark.get("release_thresholds",{})
    precision=score["precision"]
    recall=score["recall"]
    evaluation_pass=bool(
        require_independent and precision and recall and
        recall["lower"]>=requirements.get("recall_lower_bound",0.95) and
        precision["lower"]>=requirements.get("precision_lower_bound",0.85)
    )
    return {
       "schema":"V30_SEPARATED_GENERALIZATION_EVALUATION_V1",
       "cases":len(gold),
       "independent_blinded":blind,
       "original_historical_index_exposure":history,
       "precommitted_gold_attested_by_code":False,
       "gold_was_claimed_precommitted":prespecified,
       "claim_population_representative":(
           benchmark.get("sampling_method") in
           ("STRATIFIED_PROBABILITY","CENSUS") and blind and
           history=="UNEXPOSED_TO_MODEL_AND_REVIEWER"),
       "evaluation_type":("INDEPENDENT_HOLDOUT_CANDIDATE_DIAGNOSTIC"
                         if require_independent else "DEVELOPMENT_DIAGNOSTIC_ONLY"),
       "total":score,
       "by_domain":by,
       "false_negative_case_ids":missed,
       "false_positive_case_ids":false,
       "model_release_threshold_pass":evaluation_pass,
       "real_source_or_human_reviewer_trust_automatically_proven":False,
       "automatic_research_completion":False,
       "automatic_knowledge_merge":False,
    }

def validate_prereg_git_history(repo,benchmark_path,predictions_path):
    """Require distinct commits: benchmark history first, predictions later.

    Git dates alone do not prove the reviewers were truly blind.
    """
    import subprocess
    repo=Path(repo)
    def exec_git(*args):
        p=subprocess.run(["git",*args],cwd=repo,capture_output=True,text=True)
        guard(p.returncode==0,"GIT_HISTORY_PRE_REGISTRATION_NOT_VERIFIABLE")
        return p.stdout.strip()
    g=exec_git("log","--format=%H","--",str(benchmark_path)).splitlines()
    p=exec_git("log","--format=%H","--",str(predictions_path)).splitlines()
    guard(g and p and g[0]!=p[0],
          "GOLD_AND_PREDICTIONS_MUST_BE_DISTINCT_COMMITS")
    ancestor=exec_git("merge-base","--is-ancestor",g[0],p[0]) if False else None
    check=subprocess.run(["git","merge-base","--is-ancestor",g[0],p[0]],
                         cwd=repo)
    guard(check.returncode==0,"BENCHMARK_WAS_NOT_COMMITTED_BEFORE_PREDICTIONS")
    return {"gold_commit":g[0],"prediction_commit":p[0],
            "independent_human_review_proven_by_git":False,
            "chronological_preregistration_commit_order_verified":True}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--benchmark",type=Path,required=True)
    p.add_argument("--predictions",type=Path,required=True)
    p.add_argument("--diagnostic-only",action="store_true")
    args=p.parse_args()
    try:
        b=json.loads(args.benchmark.read_text())
        pr=json.loads(args.predictions.read_text())
        print(json.dumps(evaluate(b,pr,
             require_independent=not args.diagnostic_only),
                         sort_keys=True,ensure_ascii=False))
    except (ValueError,KeyError,TypeError) as e:
        print(json.dumps({"gate":"FAIL","error":str(e)},ensure_ascii=False))
        raise SystemExit(1)
