#!/usr/bin/env python3
"""Retrospective #1-5 development diagnostic for unchanged V3.0/V2.3.

Runs both frozen engine implementations on the SAME actual Git-checked
62 historical core claims. The 44 pair labels were committed *before*
first retrieval. This does not read/private-store original SRT text in CI
and does not establish independent blind generalization or factual truth.
"""
import argparse
from collections import Counter
import json
from pathlib import Path

from v30_verified_core import policy_gate,blob_sha
from v30_hybrid_search import build_development_history,search
from v5_candidate_engine_v23 import retrieve_claims
from v30_independent_evaluator import stats

ROOT=Path(__file__).resolve().parents[1]
ROSTER={
  1:("sz5N9WJS310","5bd8c20cff81446fb5fe058f92953f6ce4457962",23,1195),
  2:("6VEfKF7BzZU","cb9827570e78684f678030ca220b56190a2cef1a",9,1347),
  3:("OiDTNstaSpM","53281c9bc9ce85692267d6ff7e00ebaf5b4ecc27",15,785),
  4:("aNfGrcO6WPI","b551925f3e823b4f46e3e1aebaa6cd2e5ae802af",6,758),
  5:("qtluAViPpsQ","a845a8e3d8a463035900c376187250adc76a5e12",9,1044),
}
BASE_LABELS="v30/validation/retro_001_005_diagnostic_cases_v1.json"
STATUS={"PRIMARY_CONFIRMED","QUALIFIED","HYPOTHETICAL","CONTRADICTED","SPEAKER_OPINION"}
def need(v,err):
    if not v:raise ValueError(err)
def source_reconciliation(root):
    """Historic V3/V5 immutable source claim statuses cannot drift."""
    index=json.loads((root/"data/subtitles/content_index_001_070.json").read_text())["items"]
    history=json.loads((root/"v5/research_completion_001_010.json").read_text())
    need(history["certified_count"]==0,"HISTORIC_COMPLETENESS_FALSIFIED")
    src=[]
    total=Counter()
    for n,(vid,sha,claims,cues) in ROSTER.items():
        path=root/"data/analysis_events"/(vid+".json")
        need(blob_sha(path)==sha,"HISTORICAL_V3_STUDY_GIT_BLOB_CHANGED")
        record=json.loads(path.read_text(encoding="utf-8"))
        v5path=root/f"v5/retrofit/v5_{n:03d}_{vid}_bounded_closeout.json"
        v5=json.loads(v5path.read_text(encoding="utf-8"))
        v3={r["claim_id"]:r["verification"] for r in record["core_claims"]}
        v5map={r["id"]:r["verdict"] for r in v5["claim_coverage"]["claims"]}
        need(len(v3)==claims and v3==v5map
             and record["video_id"]==vid
             and record["approval"]=="APPROVED"
             and index[vid]["roster_no"]==n
             and index[vid]["cue_count"]==cues
             and v5["source"]["source_sha256"]==index[vid]["subtitle_sha256"]
             and v5["source"]["cue_count"]==cues
             and v5["source"]["full_human_semantic_review_completed"] is False
             and v5["source"]["original_audio_verified"] is False
             and v5["source"]["original_video_frames_verified"] is False,
             "V3_V5_FINGERPRINT_VERDICT_OR_REVIEW_STATE_DIVERGED")
        counts=Counter(v3.values())
        need(set(counts)<=STATUS,"UNKNOWN_HISTORICAL_STUDY_VERDICT")
        total.update(counts)
        src.append({
            "video_number":n,"video_id":vid,
            "original_srt_sha256_registered":index[vid]["subtitle_sha256"],
            "original_srt_cue_count":cues,
            "v3_git_blob_sha":sha,
            "v3_core_claims":claims,
            "v5_core_claims":len(v5map),
            "verdicts":dict(sorted(counts.items())),
            "historical_external_blockers":len(v5["external_blockers"]),
            "v5_research_complete":False,
            "full_private_srt_reopened_on_GitHub_actions":False,
            "real_financial_truth_reverified_by_this_script":False,
        })
    return src,dict(sorted(total.items()))
def evaluate(root):
    policy_gate(root)
    labels=json.loads((root/BASE_LABELS).read_text(encoding="utf-8"))
    need(labels["schema"]=="V30_001_005_RETROSPECTIVE_DIAGNOSTIC_CASES_V1"
         and labels["evaluation_class"]==
         "NONBLIND_DEVELOPMENT_REGRESSION_NOT_INDEPENDENT_HOLDOUT"
         and len(labels["cases"])==44
         and labels["positive_cases"]==24
         and labels["negative_cases"]==20,
         "PREREGISTERED_RETROSPECTIVE_CASES_CHANGED")
    need(blob_sha(root/"scripts/v30_hybrid_search.py")==
         labels["freeze"]["v30_hybrid_search_git_blob_sha"]
         and blob_sha(root/"scripts/v5_candidate_engine_v23.py")==
         labels["freeze"]["v23_engine_git_blob_sha"],
         "FROZEN_V30_OR_V23_DEVELOPMENT_CODE_CHANGED")
    vids={n:meta[0] for n,meta in ROSTER.items()}
    historical,verdicts=source_reconciliation(root)
    rows=build_development_history(root,vids)
    need(len(rows)==62 and len({r["claim_id"] for r in rows})==62
         and sum(1 for r in rows if r["legacy_verdict"]=="CONTRADICTED")==3,
         "FROZEN_HISTORY_RETRIEVAL_UNIVERSE_WRONG")
    by_id={r["claim_id"]:r for r in rows}
    ranks={}
    # Evaluate ALL 62 query directions, not just analyst-selected pairs.
    risk=Counter()
    for r in rows:
        output=search({"claim_id":r["claim_id"],"text":r["text"],
                       "financial_role":None,"topic_families":[]},
                      rows,limit=10,audit_non_candidates=5)
        positions={x["claim_id"]:i for i,x in
                   enumerate(output["review_candidates"],1)}
        ranks[r["claim_id"]]=positions
        for item in output["review_candidates"]:
            risk[item["source_risk"]]+=1
        need(output["candidate_precision_claimed"] is None
             and output["candidate_recall_claimed"] is None
             and output["eligible_corpus_claims"]==62
             and output["development_embargo_up_to_video"]==20
             and output["embedding_backend"]=="NOT_SUPPLIED"
             and len(output["noncandidate_audit_sample"])==5,
             "V30_SEARCH_DID_NOT_ISSUE_CORRECT_DEV_REVIEW_ONLY_OUTPUT")
    cases=[];conf_v30=Counter();conf_v23=Counter()
    pair_seen=set()
    for c in labels["cases"]:
        left,right=c["left"],c["right"]
        need(left in by_id and right in by_id and left!=right and
             frozenset((left,right)) not in pair_seen and
             type(c["review_relevant"]) is bool and
             c["review_reason"],
             "BAD_DUPLICATED_OR_SPOOFED_DEVELOPMENT_PAIR")
        pair_seen.add(frozenset((left,right)))
        a=by_id[left];b=by_id[right]
        rank_ab=ranks[left].get(right)
        rank_ba=ranks[right].get(left)
        v30hit=bool(rank_ab is not None or rank_ba is not None)
        f1={"id":left,"text":a["text"],"verdict":a["legacy_verdict"],
            "video_id":left[:11],"video_number":a["video_number"]}
        f2={"id":right,"text":b["text"],"verdict":b["legacy_verdict"],
            "video_id":right[:11],"video_number":b["video_number"]}
        v23hit,v23why=retrieve_claims(f1,f2)
        need(v23why["automatic_knowledge_approval"] is False
             and v23why["automatic_merge_permitted"] is False
             and v23why["research_completion_certificate_permitted"] is False
             and (v23why["source_risk"]=="CORRECTION_ONLY")==
                 ("CONTRADICTED" in
                   {a["legacy_verdict"],b["legacy_verdict"]}),
             "ORIGINAL_V23_SOURCE_SAFETY_INCONSISTENCY")
        v23reverse,_=retrieve_claims(f2,f1)
        need(v23hit==v23reverse,"V23_PAIR_RESULT_NOT_SYMMETRIC")
        def cm(hit,truth):
            return ("TP" if truth else "FP") if hit else ("FN" if truth else "TN")
        conf_v30[cm(v30hit,c["review_relevant"])]+=1
        conf_v23[cm(v23hit,c["review_relevant"])]+=1
        cases.append({
            "id":c["id"],"left":left,"right":right,
            "expected_review_relevance":c["review_relevant"],
            "v30_top10_either_way":v30hit,
            "v30_rank_left_to_right":rank_ab,
            "v30_rank_right_to_left":rank_ba,
            "v23_candidate":bool(v23hit),
            "source_risk":v23why["source_risk"],
            "requires_human_independent_evidence":True,
        })
    allpairs=0;v23selected=0
    for i,a in enumerate(rows):
        for b in rows[i+1:]:
            allpairs+=1
            v23,_=retrieve_claims(
                {"id":a["claim_id"],"text":a["text"],
                 "verdict":a["legacy_verdict"],"video_id":a["claim_id"][:11],
                 "video_number":a["video_number"]},
                {"id":b["claim_id"],"text":b["text"],
                 "verdict":b["legacy_verdict"],"video_id":b["claim_id"][:11],
                 "video_number":b["video_number"]})
            v23selected+=int(v23)
    return {
      "schema":"V30_001_005_REPLAY_RESULT_V1",
      "test_date":"2026-10-31",
      "classification":"ALREADY_EXPOSED_DEVELOPMENT_DIAGNOSTIC_NOT_UNSEEN_OR_BLIND",
      "original_source_source_sha_verified_in_private_local_replay":False,
      "source_sha_verified_against_registered_historical_metadata":True,
      "original_source_audio_independently_verified":False,
      "source_and_legacy_comparison":historical,
      "cumulative_legacy_verdicts":verdicts,
      "total_historical_core_claims":len(rows),
      "total_historical_srt_cues":sum(r["original_srt_cue_count"] for r in historical),
      "all_source_claims_original_legacy_status_preserved":True,
      "five_videos_research_complete_certificates":0,
      "v30_retrieval":{
          "top_k":10,"total_directions":len(rows),
          "candidate_places":len(rows)*10,
          "risk_counts_in_candidate_slots":dict(sorted(risk.items())),
          "financial_roles_populated_in_historical_development_loader":0,
          "financial_topic_families_populated_in_loader":0,
          "semantic_vector_search_enabled":False,
      },
      "v23_retrieval":{"candidate_pairs_in_1891":v23selected,
                       "total_unordered_claim_pairs":allpairs},
      "precommitted_diagnostic_pair_count":len(cases),
      "v30_diagnostic":stats({k:conf_v30[k] for k in ("TP","FN","FP","TN")}),
      "v23_diagnostic":stats({k:conf_v23[k] for k in ("TP","FN","FP","TN")}),
      "cases":cases,
      "automatic_knowledge_merges":0,
      "automatic_research_completion_certificates":0,
      "engine_tuned_after_examination":False,
      "independently_adjudicated_first_use_performance_proven":False,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--assert-snapshot",action="store_true")
    args=p.parse_args()
    result=evaluate(args.root)
    if args.assert_snapshot:
        path=args.root/"v30/validation/retro_001_005_replay_result_v1.json"
        need(path.is_file() and json.loads(path.read_text(encoding="utf-8"))==result,
             "FROZEN_001_005_REPLAY_OR_DEVELOPMENT_LABEL_RESULTS_DRIFTED")
    print(json.dumps(result,sort_keys=True,ensure_ascii=False,separators=(",",":")))

if __name__=="__main__":
    try:main()
    except (ValueError,TypeError,KeyError,IndexError,OSError) as err:
        print(json.dumps({"gate":"FAIL","error":str(err)},ensure_ascii=False))
        raise SystemExit(1)
