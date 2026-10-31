#!/usr/bin/env python3
"""V3.1 *separate historical real-video cohort* first-use relation audit.

Do not misrepresent #61-65 as truly never seen: prior project V3 and
1-260 synthesis already contained their claim metadata. The V3.1 engine
itself was frozen before this cohort's 48 gold labels and predictions.

This runs typed pair classification ONLY. The original search_v31
explicitly forbids post-20 corpora as development data; bypassing that
embargo by relabeling video numbers is prohibited.
"""
import argparse,json,subprocess
from collections import Counter
from pathlib import Path
from v30_verified_core import policy_gate,blob_sha,guard
from v30_semantic_v31 import pair_review,derive_facets
from v30_independent_evaluator import stats

ROOT=Path(__file__).resolve().parents[1]
SRT_IDS={
 61:("7RRWNL0V6As","8702b58d6072ac3376ea42ffcc980cace5058fc0"),
 62:("w1ZgJwm-_KU","963d58c40bce3ffa6b4313232812d977682c0fdf"),
 63:("LVE7XN_esTc","87e21a64870a59ee550792e40ec66d3f6966f194"),
 64:("aUW6waebLl8","f46aeb1944b978a24f427b11b96d037b4881b5b8"),
 65:("NOl9u50dgao","05ad68107f91d39bda3d80a25d4c8c09db5bd5f2"),
}
ENGINE="939e11d169355748b92dd81c855bc0d91070f7ba"
MATH="d24b28f69e0fa292c736506b038aff1a674b0d24"
GOLD="4a69f1ee55573ac1e2a81ad3845c6b67bcb5ba5b"
FREEZE_COMMIT="49d28d41c815ec9aa3c9ff0bf634533c70d7fcfd"
GOLD_COMMIT="b77ac381e593a21fe7180ecd462d8fe9ad8bdd12"
def category(pred,actual):
    return ("TP" if actual else "FP") if pred else ("FN" if actual else "TN")

def run(root=ROOT):
    root=Path(root)
    policy_gate(root)
    guard(blob_sha(root/"scripts/v30_semantic_v31.py")==ENGINE and
          blob_sha(root/"scripts/v30_finance_math_v31.py")==MATH,
          "V31_ACTUAL_VIDEO_EVAL_MUST_REUSE_FROZEN_CODE")
    path=root/"v30/validation/v31_061_065_historical_cohort_prereg_v1.json"
    guard(blob_sha(path)==GOLD,"ALTERED_PRESPECIFIED_061_065_GOLD")
    gold=json.loads(path.read_text())
    guard(gold["engine_sha"]==ENGINE and
          gold["freeze_commit"]==FREEZE_COMMIT and
          gold["gold_before_first_model_predictions_on_this_cohort"] is True
          and gold["historical_index_exposure"]==
               "PREVIOUSLY_INCLUDED_IN_PROJECT_001_260_METADATA"
          and gold["external_blind_human_gold"] is False
          and gold["positive_count"]==24 and gold["negative_count"]==24
          and len(gold["cases"])==48,
          "REAL_COHORT_SOURCE_PROVENANCE_EXPOSURE_NOT_DISCLOSED")
    if (root/".git").is_dir():
        for older,newer in ((FREEZE_COMMIT,GOLD_COMMIT),
                            (GOLD_COMMIT,"HEAD")):
            p=subprocess.run(["git","merge-base","--is-ancestor",older,newer],
                            cwd=root,capture_output=True)
            guard(p.returncode==0,"REAL_COHORT_GOLD_CHRONOLOGY_INVALID")
    index=json.loads((root/"data/subtitles/content_index_001_070.json").read_text())["items"]
    by={};source=[];facets=Counter()
    for n,(vid,sha) in SRT_IDS.items():
        p=root/"data/analysis_events"/(vid+".json")
        guard(blob_sha(p)==sha,"REAL_COHORT_OLD_V3_EVENT_TAMPERED")
        obj=json.loads(p.read_text())
        entry=index[vid]
        guard(obj.get("approval")=="APPROVED" and
              obj["video_id"]==vid and entry["roster_no"]==n and
              entry["subtitle_sha256"]==
                  gold["source_origins"]["registered_srt_sha256"][n-61],
              "REAL_COHORT_SRT_OR_VIDEO_ID_DRIFT")
        status=Counter()
        for r in obj["core_claims"]:
            cid=r["claim_id"]
            guard(cid not in by,"DUPLICATED_CLAIM_ID_IN_REAL_COHORT")
            by[cid]={
              "claim_id":cid,"text":r["claim"],
              "legacy_verdict":r["verification"],
              "video_number":n,"video_id":vid}
            status[r["verification"]]+=1
            facets.update(derive_facets(r["claim"]))
        source.append({
           "video_number":n,"video_id":vid,
           "original_srt_registry_sha256":entry["subtitle_sha256"],
           "original_srt_registered_cues":entry["cue_count"],
           "original_v3_event_git_blob":sha,
           "historical_claim_count":len(obj["core_claims"]),
           "historical_verdicts":dict(status),
           "private_original_srt_read_in_GitHub_CI":False,
           "independently_verified_real_world_financial_facts":False,
        })
    truth=Counter();cells=Counter();cases=[];read_pairs=set()
    for row in gold["cases"]:
        left,right=row["left"],row["right"]
        guard(left in by and right in by and left!=right and
              type(row["review_relevant"]) is bool and
              frozenset((left,right)) not in read_pairs,
              "GOLD_CASE_REFERENCES_UNKNOWN_OR_DUPLICATE_REAL_CLAIM")
        read_pairs.add(frozenset((left,right)))
        a=by[left];b=by[right]
        prediction=pair_review(a,b)
        pred=prediction["typed_review_candidate"]
        actual=row["review_relevant"]
        truth[actual]+=1;cells[category(pred,actual)]+=1
        guard(prediction["approved_semantic_relation"] is False and
              prediction["research_completion_certificate_permitted"] is False
              and prediction["automatic_knowledge_merge"] is False,
              "REAL_HISTORICAL_CLAIM_WAS_AUTOMATICALLY_APPROVED")
        if "CONTRADICTED" in (a["legacy_verdict"],b["legacy_verdict"]):
            guard(prediction["source_risk"]=="CORRECTION_ONLY",
                  "REAL_HISTORICAL_REFUTED_CLAIM_IMPROPERLY_REHABILITATED")
        cases.append({
           "id":row["id"],
           "left":left,"right":right,
           "precommitted_review_relevance":actual,
           "frozen_V31_typed_candidate":pred,
           "overlap_events":prediction["shared_financial_events"],
           "scope_conflicts":prediction["conflicting_cross_scope_types"],
           "source_risk":prediction["source_risk"],
           "human_blind_gold":False,
        })
    guard(truth[True]==24 and truth[False]==24,"GOLD_CLASS_BALANCE_UNVERIFIED")
    return {
      "schema":"V31_061_065_ACTUAL_HISTORICAL_COHORT_FIRST_USE_V1",
      "classification":"SEPARATE_REAL_HISTORICAL_VIDEOS_NOT_TRAINED_IN_V31_BUT_PREVIOUSLY_EXPOSED_PROJECT_METADATA",
      "frozen_engine_semantic_sha":ENGINE,
      "frozen_math_sha":MATH,
      "precommitted_gold_blob_sha":GOLD,
      "git_freeze_commit":FREEZE_COMMIT,
      "git_gold_commit":GOLD_COMMIT,
      "original_source_file_hashes_locally_checked_separately":True,
      "actual_private_SRT_bytes_available_in_CI":False,
      "source_videos":source,
      "total_historical_legacy_claims":len(by),
      "historical_source_cues":sum(x["original_srt_registered_cues"] for x in source),
      "distinct_provisional_event_tags":len(facets),
      "claims_with_no_recognized_provisional_event":sum(
          not derive_facets(r["text"]) for r in by.values()),
      "provisional_tag_count":sum(facets.values()),
      "labeled_pairs":len(cases),
      "direct_typed_relation_diagnostic":stats({k:cells[k]
                  for k in ("TP","FN","FP","TN")}),
      "false_negative_case_ids":[c["id"] for c in cases if
          c["precommitted_review_relevance"] and
          not c["frozen_V31_typed_candidate"]],
      "false_positive_case_ids":[c["id"] for c in cases if
          not c["precommitted_review_relevance"] and
          c["frozen_V31_typed_candidate"]],
      "source_and_evidence_auditor":None,
      "independent_blinded_human_labeling":False,
      "population_sampling_random":False,
      "separate_actual_historical_unseen_to_code_only":True,
      "post20_retrieval_embargo_respected":True,
      "ranking_search_on_this_cohort_tested":False,
      "financial_facts_independently_verified":0,
      "first_use_failure_cases_not_used_for_this_frozen_code_tuning":True,
      "cases":cases,
      "release_approved":False,"research_complete":False,
      "automatic_knowledge_merge":False
    }

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,default=ROOT)
    ap.add_argument("--assert-snapshot",action="store_true")
    a=ap.parse_args()
    try:
        result=run(a.root)
        if a.assert_snapshot:
            p=a.root/"v30/validation/v31_061_065_realcohort_result_v1.json"
            guard(p.is_file() and
                  json.loads(p.read_text(encoding="utf-8"))==result,
                  "ACTUAL_HISTORICAL_FIRST_USE_RESULTS_MUTATED")
        print(json.dumps(result,sort_keys=True,ensure_ascii=False))
    except (ValueError,KeyError,TypeError) as err:
        print(json.dumps({"gate":"FAIL","error":str(err)},ensure_ascii=False))
        raise SystemExit(1)
