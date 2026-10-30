#!/usr/bin/env python3
"""Out-of-sample diagnostic of frozen 1-10 candidate finder on videos #11-#12.

Deliberately evaluates unchanged retrieval rules. The new benchmark was committed
before this runner, and any change in the original evaluator SHA causes failure.
Source assertions do not imply independently verified economic truth.
"""
import argparse
import copy
import itertools
import json
from pathlib import Path

from evaluate_v5_001_010_synthesis import (
    documents, curated_claim_groups, is_candidate, measure,
    read, need, git_blob_sha, BENCH, CURATED,
)
from verify_v5_knowledge_integration import (
    load_legacy_claim_index, verified_verdict_reconciliations,
)

ROOT=Path(__file__).resolve().parents[1]
HOLDOUT="v5/integration/benchmark_011_012_holdout_v1.json"
EXPECTED_IDS={11:"HfrBi5mzm8w",12:"3_9IXnycZ3s"}
VERDICTS={"QUALIFIED","HYPOTHETICAL","PRIMARY_CONFIRMED","CONTRADICTED"}
LABELS={"QUALIFY","SUPPORT","CORRECTION_REVIEW","TOPIC_ONLY"}

def contract(h):
    need(h["schema"]=="V5_011_012_OUT_OF_SAMPLE_DIAGNOSTIC_V1" and
         h["intent"]=="FROZEN_ENGINE_HOLDOUT_NOT_FINANCIAL_RESEARCH_CERTIFICATION" and
         h["approval"] is False and
         h["original_38_tests_untouched"] is True,
         "holdout is not allowed to certify real financial research")
    need(h["old_001_010_claim_count"]==122 and h["new_original_claim_count"]==15 and
         h["all_001_012_claim_count"]==137 and
         h["all_pair_universe"]==9316 and
         h["new_involving_pair_universe"]==1935,
         "incorrect heldout claim denominator")
    need(h["frozen_engine_path"]=="scripts/evaluate_v5_001_010_synthesis.py" and
         h["frozen_original_benchmark_path"]==BENCH,
         "holdout cannot swap baseline evaluator")
    need(len(h["source_videos"])==2 and
         {x["video_number"]:x["video_id"] for x in h["source_videos"]}==EXPECTED_IDS and
         [x["claim_count"] for x in h["source_videos"]]==[7,8],
         "holdout #11/#12 source identity changed")
    blocked=set(h["source_blocked_correction_only_ids"])
    need(blocked=={"3_9IXnycZ3s-04","3_9IXnycZ3s-05"},
         "historically refuted short-video claims promoted")
    pairs=h["holdout_tests"]
    need(len(pairs)==60 and len({x["id"] for x in pairs})==60,
         "frozen diagnostic 60-case denominator changed")
    need(sum(x["left"].startswith("HfrBi5mzm8w-") for x in pairs)==28 and
         sum(x["left"].startswith("3_9IXnycZ3s-") for x in pairs)==32,
         "each new video must be represented in heldout set")
    need(all(x["analyst_label"] in LABELS and
             x["adjudication"]=="ANALYST_DIAGNOSTIC_NOT_INDEPENDENT" and
             x["certified_merge"] is False and
             isinstance(x["reason"],str) and len(x["reason"])>8
             for x in pairs),"unreviewed semantic gold promoted")
    need(all(x["analyst_label"]!="SUPPORT" for x in pairs if x["left"] in blocked),
         "contradicted original claim used as positive support")
    need(all(x["left"] in blocked for x in pairs
             if x["analyst_label"]=="CORRECTION_REVIEW"),
         "correction-review case must cite contradicted #12 claim")
    seen=set()
    for x in pairs:
        key=tuple(sorted((x["left"],x["right"])))
        need(x["left"]!=x["right"] and key not in seen and
             x["right"][:11] not in EXPECTED_IDS.values(),
             "holdout must be new-vs-prior, unique unordered pairs")
        seen.add(key)
    return pairs

def sources(h,root,claims,video_no,reviews):
    new_claims={}
    cue_index=read(root/"data/subtitles/content_index_001_070.json")["items"]
    for item in h["source_videos"]:
        vid=item["video_id"];number=item["video_number"];path=item["v3_path"]
        need(path==f"data/analysis_events/{vid}.json" and
             git_blob_sha(root/path)==item["v3_git_blob_sha"],
             "new original claim source was changed")
        data=read(root/path)
        need(data["video_id"]==vid and data["approval"]=="APPROVED"
             and data["analysis_status"]=="COMPLETE"
             and len(data["core_claims"])==item["claim_count"],
             "missing source-scoped educational V3 record")
        need(cue_index[vid]["roster_no"]==number and
             cue_index[vid]["subtitle_sha256"]==item["private_srt_sha256_registered"],
             "historic source SRT fingerprint is unpinned")
        need(data["evidence_gate"]["source_checked"] is True
             and data["evidence_gate"]["audio_checked"] is False
             if "audio_checked" in data["evidence_gate"]
             else data["evidence_gate"]["source_checked"] is True,
             "source metadata cannot claim independent audio proof")
        for item_claim in data["core_claims"]:
            cid=item_claim["claim_id"]
            need(cid not in claims and cid not in new_claims and
                 cid.startswith(vid+"-") and item_claim["verification"] in VERDICTS
                 and item_claim.get("timecode"),"new original claim ID/provenance invalid")
            new_claims[cid]={"id":cid,"text":item_claim["claim"],
                              "verdict":item_claim["verification"],
                              "video_number":number,"video_id":vid,
                              "source_blob":item["v3_git_blob_sha"]}
        video_no[vid]=number
        # No fabricated V5 completed closeout for #11/#12. New-to-V5
        # videos have no preexisting video-level V5 relationship links.
        reviews[vid]={"cross_video":{"related_video_ids":[]}}
    need(len(new_claims)==15 and
         {cid for cid,v in new_claims.items() if v["verdict"]=="CONTRADICTED"}==
         set(h["source_blocked_correction_only_ids"]),
         "two contradicted short source statements must remain quarantined")
    claims.update(new_claims)
    return new_claims

def evaluate(h,root,include_pairs=False):
    tests=contract(h)
    need(git_blob_sha(root/h["frozen_engine_path"])==
         h["frozen_engine_git_blob_sha"] and
         git_blob_sha(root/h["frozen_original_benchmark_path"])==
         h["frozen_original_benchmark_git_blob_sha"],
         "the 38-pair-tuned baseline code or input changed during holdout")
    base=read(root/BENCH)
    legacy_base=measure(base,root)
    need(legacy_base["retrieval"]["sample_true_positive"]==30 and
         legacy_base["retrieval"]["sample_false_positive"]==0 and
         legacy_base["retrieval"]["sample_false_negative"]==0 and
         legacy_base["retrieval"]["sample_true_negative"]==8,
         "38-case original benchmark drift")

    claims,video_no,reviews,_,_=documents(root,base)
    new_claims=sources(h,root,claims,video_no,reviews)
    need(len(claims)==137 and
         len(claims)*(len(claims)-1)//2==9316,"137 claim denominator")
    legacy,_,_=load_legacy_claim_index(root)
    effective=verified_verdict_reconciliations(root,legacy)
    need(len(effective)==1 and len(set(claims)&set(legacy))==137,
         "historical crosswalk not retained for all 137 claims")
    discrepancies=[]
    for cid in sorted(new_claims):
        if legacy[cid]["original_verdict"]!=new_claims[cid]["verdict"]:
            discrepancies.append({"claim_id":cid,
               "original_v3":new_claims[cid]["verdict"],
               "legacy_crosswalk":legacy[cid]["original_verdict"],
               "status":"NEW_OPEN_SOURCE_VERDICT_RECONCILIATION"})
        need(legacy[cid]["video_id"]==new_claims[cid]["video_id"],
             "crosswalk video ancestry mismatch")

    by_family={cid:legacy[cid]["primary_concept_id"] for cid in claims}
    curated=curated_claim_groups(read(root/CURATED))
    all_ids=sorted(claims)
    initial_candidates=0
    new_candidate_count=0
    new_involving=0
    for a,b in itertools.combinations(all_ids,2):
        predicted,_=is_candidate(a,b,by_family,curated,video_no,reviews,claims)
        initial_candidates+=bool(predicted)
        if a in new_claims or b in new_claims:
            new_involving+=1
            new_candidate_count+=bool(predicted)
    need(new_involving==1935,"new-involving pair denominator wrong")

    counts={"TP":0,"FP":0,"FN":0,"TN":0}
    by_video={str(n):{"TP":0,"FP":0,"FN":0,"TN":0} for n in (11,12)}
    rows=[]
    for case in tests:
        a,b=case["left"],case["right"]
        need(a in new_claims and b in claims and b not in new_claims,
             "diagnostic candidate must compare actual heldout and prior source claims")
        positive=case["analyst_label"]!="TOPIC_ONLY"
        predicted,signals=is_candidate(a,b,by_family,curated,video_no,reviews,claims)
        key=("TP" if predicted else "FN") if positive else ("FP" if predicted else "TN")
        counts[key]+=1
        by_video[str(new_claims[a]["video_number"])][key]+=1
        rows.append({"id":case["id"],"left":a,"right":b,"analyst_label":case["analyst_label"],
                     "retrieved_as_candidate":predicted,"confusion_class":key,
                     "signals":signals,"approved_relation":False})
    need(sum(counts.values())==60 and sum(x["TP"]+x["FP"]+x["FN"]+x["TN"]
                                         for x in by_video.values())==60,
         "missing heldout sample cases")
    result={"schema":"V5_011_012_HOLDOUT_RETRIEVAL_RESULT_V1",
      "engine_frozen":True,
      "labels_independently_blinded":False,
      "labels_provided_before_engine_run":True,
      "heldout_videos":[11,12],
      "source_claims":{"old":122,"new":15,"total":137,
                       "new_correction_only_ids":sorted(h["source_blocked_correction_only_ids"]),
                       "new_crosswalk_verdict_discrepancies":discrepancies,
                       "private_source_srt_reopened_this_run":False,
                       "new_v5_research_completed":0},
      "universe":{"all_pairs":9316,"new_involving_pairs":1935,
                  "all_candidates":initial_candidates,
                  "new_involving_candidates":new_candidate_count},
      "retrieval":{"sample_size":len(tests),"counts":counts,
                   "per_new_video":by_video,
                   "precision":counts["TP"]/(counts["TP"]+counts["FP"]) if counts["TP"]+counts["FP"] else None,
                   "recall":counts["TP"]/(counts["TP"]+counts["FN"]) if counts["TP"]+counts["FN"] else None,
                   "specificity":counts["TN"]/(counts["TN"]+counts["FP"]) if counts["TN"]+counts["FP"] else None,
                   "relationship_labels_automatically_classified":0,
                   "approved_semantic_merges":0,
                   "sampling_generalizable":False},
      "original_38_case_retest":{"TP":30,"FP":0,"FN":0,"TN":8},
      "safety":{"original_v3_v5_immutable":True,
                "new_contradicted_claims_positive_reused":False,
                "new_research_completed":0,
                "automatic_knowledge_approved":0},
      "case_results":rows if include_pairs else None}
    return result

def self_test(h,root):
    trials=[]
    x=copy.deepcopy(h);x["approval"]=True;trials.append(x)
    x=copy.deepcopy(h);x["source_videos"][0]["claim_count"]=8;trials.append(x)
    x=copy.deepcopy(h);x["source_blocked_correction_only_ids"]=[];trials.append(x)
    x=copy.deepcopy(h);x["holdout_tests"][0]["certified_merge"]=True;trials.append(x)
    x=copy.deepcopy(h);x["holdout_tests"][0]["adjudication"]="INDEPENDENT_VERIFIED";trials.append(x)
    x=copy.deepcopy(h);x["holdout_tests"].append(copy.deepcopy(x["holdout_tests"][0]));trials.append(x)
    x=copy.deepcopy(h);x["holdout_tests"][0]["right"]=x["holdout_tests"][0]["left"];trials.append(x)
    x=copy.deepcopy(h);x["holdout_tests"][0]["analyst_label"]="UNVERIFIED_SUPPORT";trials.append(x)
    x=copy.deepcopy(h);x["holdout_tests"][10]["analyst_label"]="SUPPORT";trials.append(x) # ordinary label can be changed without sources; NOT a valid corruption, undo
    trials.pop()
    # Find any correction case and force it to positive support, which must be rejected.
    x=copy.deepcopy(h)
    c=next(t for t in x["holdout_tests"] if t["analyst_label"]=="CORRECTION_REVIEW")
    c["analyst_label"]="SUPPORT";trials.append(x)
    rejected=0
    for t in trials:
        try:contract(t)
        except (ValueError,KeyError,TypeError):rejected+=1
        else:raise ValueError("unsafe holdout mutation accepted")
    a=evaluate(h,root);b=evaluate(h,root)
    need(a==b,"frozen heldout engine is not deterministic")
    return {"negative_contract_mutations_rejected":rejected,
            "deterministic_holdout_replay":True,
            "semantic_gold_independently_adjudicated":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--show-pairs",action="store_true")
    args=p.parse_args()
    root=args.root.resolve()
    data=read(root/HOLDOUT)
    result=evaluate(data,root,args.show_pairs)
    if args.self_test:result["regression"]=self_test(data,root)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    try:main()
    except (ValueError,KeyError,TypeError,IndexError,OSError,OverflowError) as e:
        print(json.dumps({"gate":"FAIL","error":str(e)},ensure_ascii=False))
        raise SystemExit(1)
