#!/usr/bin/env python3
"""First-use of frozen V3.1 code on novel synthetic #801/#802 statements.

The GOLD JSON was committed AFTER engine freeze and before first prediction.
This is not externally blind human evaluation or a real-video performance
claim. No tuning after first-use failures; preserve complete result snapshot.
"""
import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path

from v30_verified_core import policy_gate,blob_sha,guard
from v30_semantic_v31 import pair_review,search_v31
from v30_independent_evaluator import stats

ROOT=Path(__file__).resolve().parents[1]
FROZEN_COMMIT="49d28d41c815ec9aa3c9ff0bf634533c70d7fcfd"
PREREG_COMMIT="4c38a1a1de2087c03cfa580ad172f1c6e8673eea"
GOLD_SHA="ad8eadb1f07041f37ddb5b83bb4dfa519934cf6d"
FROZEN_ENGINE_SHA="939e11d169355748b92dd81c855bc0d91070f7ba"
FROZEN_MATH_SHA="d24b28f69e0fa292c736506b038aff1a674b0d24"

def category(result,actual):
    return ("TP" if actual else "FP") if result else ("FN" if actual else "TN")

def evaluate(root=ROOT):
    root=Path(root)
    policy_gate(root)
    guard(blob_sha(root/"scripts/v30_semantic_v31.py")==FROZEN_ENGINE_SHA and
          blob_sha(root/"scripts/v30_finance_math_v31.py")==FROZEN_MATH_SHA,
          "FIRST_USE_ENGINE_CODE_CHANGED_AFTER_GOLD_REGISTRATION")
    freeze=json.loads((root/"v30/contracts/v31_first_use_engine_freeze_20261031_v1.json").read_text())
    guard(freeze["semantic_retriever_git_blob_sha"]==FROZEN_ENGINE_SHA and
          freeze["rate_math_git_blob_sha"]==FROZEN_MATH_SHA and
          freeze["cannot_retrain_on_holdout_for_this_first_use"] is True,
          "FIRST_USE_FREEZE_CONTRACT_CHANGED")
    file=root/"v30/validation/v31_novel_synthetic_gold_prereg_v1.json"
    guard(blob_sha(file)==GOLD_SHA,
          "FIRST_USE_PRECOMMITTED_GOLD_FILE_MODIFIED")
    gold=json.loads(file.read_text(encoding="utf-8"))
    guard(gold["code_freeze_commit"]==FROZEN_COMMIT and
          gold["expected_positive"]==24 and gold["expected_negative"]==24
          and gold["first_use_gold_prior_engine_outputs_seen"] is False
          and gold["independent_external_adjudication"] is False
          and len(gold["cases"])==48,
          "NOVEL_GOLD_OR_EXPOSURE_MANIFEST_FAILED")
    if (root/".git").is_dir():
        for older,newer in ((FROZEN_COMMIT,PREREG_COMMIT),
                            (PREREG_COMMIT,"HEAD")):
            verified=subprocess.run(
              ["git","merge-base","--is-ancestor",older,newer],
              cwd=root,capture_output=True)
            guard(verified.returncode==0,"GIT_FIRST_USE_ORDER_UNVERIFIABLE")
    corpus=[];pairs=[];ids=set();counts=Counter()
    for case in gold["cases"]:
        guard(type(case["label"]) is bool and
              case["id"] not in ids,
              "INCOMPLETE_OR_DUPLICATE_FIRST_USE_GOLD")
        ids.add(case["id"])
        a=case["left"];b=case["right"]
        guard(a["test_fixture"] is True and b["test_fixture"] is True
              and a["video_number"]==801 and b["video_number"]==802
              and a["claim_id"].startswith("HOUTA000001-")
              and b["claim_id"].startswith("HOUTB000001-"),
              "HOLDOUT_MISLABELED_AS_ACTUAL_UNSEEN_YOUTUBE")
        corpus.extend((a,b))
        pairs.append((case,a,b))
        counts[case["label"]]+=1
    guard(counts[True]==24 and counts[False]==24
          and len({c["claim_id"] for c in corpus})==96,
          "HOLDOUT_UNIVERSE_INVALID")
    # Prediction begins here; all human-proposed labels were stored in Git.
    direct=Counter();retrieval=Counter();cases=[]
    positions={}
    all_typed_direct=0
    for a in corpus:
        r=search_v31(a,corpus,top_k=10,noncandidate_audit=10,
                     evaluation_mode="SEALED_NOVEL_SYNTHETIC")
        guard(r["relation_auto_approval"] is False and
              r["evaluation_mode"]=="SEALED_NOVEL_SYNTHETIC"
              and r["real_original_claim_provenance_verified"] is False,
              "UNSEEN_SYNTHETIC_SOURCE_FALSIFIED")
        positions[a["claim_id"]]={
            c["claim_id"]:i+1 for i,c in enumerate(r["typed_review_queue"])}
    for item,a,b in pairs:
        out=pair_review(a,b)
        typed=out["typed_review_candidate"]
        ab=positions[a["claim_id"]].get(b["claim_id"])
        ba=positions[b["claim_id"]].get(a["claim_id"])
        ranked=ab is not None or ba is not None
        direct[category(typed,item["label"])]+=1
        retrieval[category(ranked,item["label"])]+=1
        cases.append({
           "id":item["id"],"topic":item["pair_topic"],"gold_relevant":item["label"],
           "typed_review_candidate":typed,
           "top10_either_way":ranked,
           "rank_left_to_right":ab,"rank_right_to_left":ba,
           "shared_events":out["shared_financial_events"],
           "scope_conflicts":out["conflicting_cross_scope_types"],
           "source_risk":out["source_risk"],
           "independent_external_gold_label":False
        })
    for i,a in enumerate(corpus):
        for b in corpus[i+1:]:
            all_typed_direct+=int(pair_review(a,b)["typed_review_candidate"])
    directscore=stats({k:direct[k] for k in ("TP","FN","FP","TN")})
    rankscore=stats({k:retrieval[k] for k in ("TP","FN","FP","TN")})
    return {
       "schema":"V31_SEPARATE_NOVEL_SYNTHETIC_FIRST_USE_EVALUATION_V1",
       "engine_frozen_before_gold":True,
       "engine_semantic_git_sha":FROZEN_ENGINE_SHA,
       "engine_math_git_sha":FROZEN_MATH_SHA,
       "gold_git_blob_sha":GOLD_SHA,
       "engine_freeze_commit":FROZEN_COMMIT,
       "gold_prereg_commit":PREREG_COMMIT,
       "holdout_type":"NEW_SYNTHETIC_FINANCIAL_CLAIMS_NOT_REUSED_HISTORICAL_1_260",
       "is_real_original_unseen_video":False,
       "independent_blinded_human_gold":False,
       "user_real_financial_source_authentication":False,
       "case_count":len(cases),
       "positive_gold_pairs":counts[True],
       "negative_gold_pairs":counts[False],
       "unique_synthetic_statements":len(corpus),
       "typed_candidate_pairs_total_4560":all_typed_direct,
       "direct_pair_review_diagnostic":directscore,
       "retrieval_top10_either_direction_diagnostic":rankscore,
       "first_use_failure_case_ids":[c["id"] for c in cases
           if c["gold_relevant"]!=c["top10_either_way"]],
       "cases":cases,
       "not_used_for_engine_tuning":True,
       "no_prior_original_v30_v23_artifact_changed":True,
       "model_release_approved":False,
       "knowledge_merge_approved":0,
       "research_completion_issued":0
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--assert-snapshot",action="store_true")
    args=p.parse_args()
    try:
        out=evaluate(args.root)
        if args.assert_snapshot:
            p=args.root/"v30/validation/v31_novel_synthetic_firstuse_result_v1.json"
            guard(p.is_file() and json.loads(p.read_text())==out,
                  "FIRST_USE_FAILURE_SNAPSHOT_MUST_NOT_BE_REWRITTEN")
        print(json.dumps(out,ensure_ascii=False,sort_keys=True))
    except (ValueError,KeyError,TypeError) as err:
        print(json.dumps({"gate":"FAIL","error":str(err)},ensure_ascii=False))
        raise SystemExit(1)
