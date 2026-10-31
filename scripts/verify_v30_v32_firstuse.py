#!/usr/bin/env python3
"""Frozen V3.2 on separate actual #66-70 prior-project V3 core claims.

Gold labels were Git-committed after V3.2 and input-adapter freezes and
before model predictions. Historical project metadata exposure and lack of
independent blind adjudicators are explicitly disclosed. No model tuning.
"""
import argparse,json,subprocess
from pathlib import Path
from collections import Counter
from v30_verified_core import policy_gate,blob_sha,guard
from v30_semantic_v32 import pair_review_v32,facets_v32,review_queue_v32
from v30_legacy_verdict_v32 import normalize_existing_v3_claim
from v30_independent_evaluator import stats

ROOT=Path(__file__).resolve().parents[1]
SEMANTIC="36a74e8d31180283a0c68f618acae716ac935ac8"
BRIDGE="9ced4d65d037ac29ae8249759d609bf7adb7d433"
GOLD="76352689cce6118c6076349cc14fdfbc211c762f"
FREEZE="dde1adfbbd5af68c131748133e561d27df61ff5a"
ADAPTER_FREEZE="d2e515e2090c53816d54ee9b58fd2c0ac72ef377"
GOLD_COMMIT="041975e17156f56ca1a0c3d142ab08333c53da86"

def bucket(hit,actual):
    return ("TP" if actual else "FP") if hit else ("FN" if actual else "TN")

def run(root=ROOT):
    root=Path(root)
    policy_gate(root)
    guard(blob_sha(root/"scripts/v30_semantic_v32.py")==SEMANTIC
          and blob_sha(root/"scripts/v30_legacy_verdict_v32.py")==BRIDGE,
          "V32_FIRST_USE_CODE_CHANGED_AFTER_GOLD")
    manifest=root/"v30/validation/v32_066_070_real_firstuse_prereg_v1.json"
    guard(blob_sha(manifest)==GOLD,
          "V32_SOURCE_GOLD_CHANGED_AFTER_FIRST_USE")
    gold=json.loads(manifest.read_text(encoding="utf-8"))
    guard(gold["semantic_engine_sha"]==SEMANTIC
          and gold["verdict_bridge_sha"]==BRIDGE
          and gold["source_audio_and_video_not_independently_audited"] is True
          and gold["historical_001_260_knowledge_index_had_meta_exposure"] is True
          and gold["gold_was_set_before_first_frozen_model_predictions"] is True
          and gold["positive_cases"]==24 and gold["negative_cases"]==24
          and len(gold["cases"])==48,
          "EXTERNAL_BLIND_AND_PRECOMMITMENT_CLAIMS_NOT_BOUNDED")
    if (root/".git").is_dir():
        for a,b in ((FREEZE,ADAPTER_FREEZE),(ADAPTER_FREEZE,GOLD_COMMIT),
                    (GOLD_COMMIT,"HEAD")):
            r=subprocess.run(["git","merge-base","--is-ancestor",a,b],
                            cwd=root,capture_output=True)
            guard(r.returncode==0,"GOLD_NOT_CHRONOLOGICALLY_PREREGISTERED")
    idx=json.loads((root/"data/subtitles/content_index_001_070.json").read_text())["items"]
    claims={};source=[];alias_count=Counter()
    for no,vid in zip(gold["video_numbers"],gold["video_ids"]):
        p=root/"data/analysis_events"/(vid+".json")
        guard(blob_sha(p)==gold["source_events_github_blob_shas"][vid],
              "V32_REAL_HOLDOUT_HISTORICAL_V3_SOURCE_TAMPERED")
        o=json.loads(p.read_text())
        guard(o.get("approval")=="APPROVED" and o["video_id"]==vid
              and idx[vid]["roster_no"]==no
              and idx[vid]["subtitle_sha256"]==
                  gold["original_srt_sha256_by_video"][vid]
              and idx[vid]["cue_count"]==
                  gold["original_srt_cues_by_video"][vid],
              "V32_UNMATCHED_HISTORICAL_SOURCE_AND_RAW_SRT_REGISTRY")
        status=Counter()
        for atom in o["core_claims"]:
            c=normalize_existing_v3_claim(atom,no,vid)
            guard(c["claim_id"] not in claims,"DUPLICATE_SOURCE_CLAIM")
            claims[c["claim_id"]]=c
            status[atom["verification"]]+=1
            alias_count[(atom["verification"],c["legacy_verdict"])]+=1
        source.append({
            "video_number":no,"video_id":vid,
            "original_srt_cues_locally_sha_verified":
                gold["original_srt_cues_by_video"][vid],
            "original_srt_sha_from_private_local_validation":
                gold["original_srt_sha256_by_video"][vid],
            "v3_git_blob_sha":gold["source_events_github_blob_shas"][vid],
            "v3_core_claim_count":len(o["core_claims"]),
            "historical_raw_verdicts":dict(status),
            "private_original_srt_bytes_stored_in_repository":False,
            "independently_confirmed_factual_truth":False,
        })
    guard(len(source)==5 and len(claims)==108,
          "V32_FIRST_USE_CLAIM_UNIVERSE_NOT_108")
    # No previously observed model predictions until this point.
    corpus=list(claims.values())
    rank={}
    for item in corpus:
        out=review_queue_v32(item,corpus,limit=10)
        guard(out["automatic_knowledge_merge"] is False and
              out["all_corpus_claims_accounted_for"]==len(corpus),
              "V32_UNAPPROVED_HOLDOUT_SEMANTIC_RETRIEVAL")
        rank[item["claim_id"]]={
            row["claim_id"]:i+1 for i,row
            in enumerate(out["typed_review_candidates"])}
    direct=Counter();top10=Counter();detail=[]
    for row in gold["cases"]:
        a=claims[row["left"]];b=claims[row["right"]]
        actual=row["review_relevant"]
        out=pair_review_v32(a,b)
        predicted=out["typed_review_candidate"]
        ab=rank[a["claim_id"]].get(b["claim_id"])
        ba=rank[b["claim_id"]].get(a["claim_id"])
        retrieved=ab is not None or ba is not None
        direct[bucket(predicted,actual)]+=1
        top10[bucket(retrieved,actual)]+=1
        if "CONTRADICTED" in (a["legacy_verdict"],b["legacy_verdict"]):
            guard(out["legacy_verdict_source_risk"]=="CORRECTION_ONLY",
                  "HISTORIC_CORRECTION_PROVENANCE_PROMOTED")
        guard(not out["automatic_relation_approval"] and
              not out["automatic_knowledge_merge"] and
              not out["research_completion_certificate_approved"],
              "V32_HOLDOUT_AUTO_APPROVAL_BYPASSED")
        detail.append({
           "id":row["id"],"left":row["left"],"right":row["right"],
           "precommitted_relevance":actual,
           "v32_typed_review":predicted,
           "v32_top10_either_direction":retrieved,
           "rank_left_to_right":ab,"rank_right_to_left":ba,
           "matching_financial_events":out["matching_financial_event_tags"],
           "source_risk":out["legacy_verdict_source_risk"],
           "cannot_claim_fact_from_relevance":True,
        })
    results=[]
    for a in corpus:
        results.append(sum(1 for b in corpus if a is not b and
                           pair_review_v32(a,b)["typed_review_candidate"]))
    return {
      "schema":"V32_066_070_REAL_HISTORICAL_COHORT_FIRST_USE_RESULT_V1",
      "evaluation_class":"REAL_SEPARATE_HISTORICAL_VIDEOS_NOT_FULLY_UNEXPOSED_TO_PROJECT_AND_NOT_EXTERNAL_BLIND",
      "source_semantic_sha":SEMANTIC,"source_legacy_adapter_sha":BRIDGE,
      "gold_git_sha":GOLD,"freeze_commit":FREEZE,
      "adapter_freeze_commit":ADAPTER_FREEZE,
      "gold_preregistration_commit":GOLD_COMMIT,
      "source_videos":source,
      "total_legacy_original_claims":len(corpus),
      "total_actual_private_original_SRT_cues":sum(
           r["original_srt_cues_locally_sha_verified"] for r in source),
      "original_legacy_verdict_alias_count":{
          k[0]+"->"+k[1]:v for k,v in sorted(alias_count.items())},
      "source_claims_missing_any_provisional_financial_event":sum(
           not facets_v32(r["text"]) for r in corpus),
      "candidate_links_from_108_claims":sum(results),
      "source_and_gold_not_annotated_by_external_independent_human":True,
      "direct_typed_review_diagnostic":stats({
           k:direct[k] for k in ("TP","FN","FP","TN")}),
      "typed_top10_either_direction_diagnostic":stats({
           k:top10[k] for k in ("TP","FN","FP","TN")}),
      "first_use_false_negatives":[r["id"] for r in detail
           if r["precommitted_relevance"] and
           not r["v32_top10_either_direction"]],
      "first_use_false_positives":[r["id"] for r in detail
           if not r["precommitted_relevance"] and
           r["v32_top10_either_direction"]],
      "cases":detail,
      "frozen_code_tuned_after_unseen_trial":False,
      "real_official_evidence_independently_reviewed":0,
      "manual_research_complete_certificates_issued":0,
      "automatic_knowledge_merge":False,
      "production_release":False,
    }

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,default=ROOT)
    ap.add_argument("--assert-snapshot",action="store_true")
    a=ap.parse_args()
    try:
        o=run(a.root)
        if a.assert_snapshot:
            p=a.root/"v30/validation/v32_066_070_real_firstuse_result_v1.json"
            guard(p.is_file() and json.loads(p.read_text())==o,
                  "HISTORICAL_FIRST_USE_FAILURE_RESULT_WAS_REWRITTEN")
        print(json.dumps(o,ensure_ascii=False,sort_keys=True))
    except (ValueError,KeyError,TypeError) as e:
        print(json.dumps({"gate":"FAIL","error":str(e)},ensure_ascii=False))
        raise SystemExit(1)
