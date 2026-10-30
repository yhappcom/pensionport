#!/usr/bin/env python3
"""V2.2 first-use #17/#18 holdout, frozen engine and guarded provenance.

The diagnostic set was COMMITTED BEFORE executing this evaluator. Labels
are analyst-selected, not independent blinded representative ground truth.
Historical 251 development cases are never scored as first-use evidence.
"""
import argparse
import itertools
import json
from pathlib import Path

from evaluate_v5_001_010_synthesis import git_blob_sha,need,read
from evaluate_v5_candidate_v22 import source_contract_v22,evaluate as v22_development
from v5_candidate_engine_v22_guarded import retrieve_claims
from verify_v5_knowledge_integration import load_legacy_claim_index,verified_verdict_reconciliations

ROOT=Path(__file__).resolve().parents[1]
BENCH="v5/integration/benchmark_017_018_v22_holdout_v1.json"
FREEZE="v5/integration/v22_pre_new_video_gate_v1.json"
EXPECTED_BENCH_BLOB="86d12168b229c7b497adfb5bb450f7b066fc467e"
EXPECTED_COUNTS={"NEW17-":41,"NEW18-":42,"CROSS17-18-":10}
EXPECTED_VIDEOS={17:"nCXWFko0TaA",18:"CvM8Os4ltfE"}
EXPECTED_PROVENANCE={
"nCXWFko0TaA":{"v3":"9a73352debf6f787dede0d7049b5f47ef99a2590",
                "srt":"b3182276d3dab45372252712ef9e671dda961278c6eebf3bc2c4e77e2048464f","cue_count":37},
"CvM8Os4ltfE":{"v3":"64476de471224e2895595ac213074200afafc9f0",
                "srt":"fd147eb6b765e2d7de7bc86839a8be0fbb2856fe1975571c1cdaec94477d6589","cue_count":51},
}
EXPECTED_BASELINE_V22={"TP":164,"FN":0,"FP":0,"TN":87}
EXPECTED_FIRST_USE_SCHEMA="V5_CANDIDATE_V22_FIRST_USE_017_018_RESULT_V1"
ALLOWED_VERDICTS={"QUALIFIED","PRIMARY_CONFIRMED","CONTRADICTED",
                  "HYPOTHETICAL","SPEAKER_OPINION"}
REFUTED_NEW={"nCXWFko0TaA-04"}
REFUTED_OLD={
 "sz5N9WJS310-06","sz5N9WJS310-15","aNfGrcO6WPI-03",
 "VKr060rIirM-05","3_9IXnycZ3s-04","3_9IXnycZ3s-05",
 "keu5SvpD7KE-04","keu5SvpD7KE-06",
 "IMJfPgmnFwc-01","IMJfPgmnFwc-07",
}

def validate_benchmark(root,b):
    need(git_blob_sha(root/BENCH)==EXPECTED_BENCH_BLOB,
         "unseen first-use benchmark labels or dates were modified after preregistration")
    gate=read(root/FREEZE)
    need(gate["schema"]=="V5_V22_PRE_NEW_VIDEO_FROZEN_CODE_GATE_V1" and
         gate["next_evaluation_eligible_video_number"]==17 and
         gate["production_release_status"]=="BLOCKED" and
         gate["proceed_to_unseen_video_eval_only"] is True and
         gate["engine_retraining_allowed_on_unseen"] is False and
         gate["automatic_knowledge_approval"] is False,
         "protected V2.2 prerelease/first-use gate changed")
    for path,sha in gate["protected_blobs"].items():
        need(git_blob_sha(root/path)==sha,"frozen engine/guard/audit source changed: "+path)
    need(b["schema"]=="V5_CANDIDATE_V22_FIRST_USE_017_018_PREREGISTERED_BENCHMARK_V1" and
         b["engine_blob_sha"]==gate["protected_blobs"]["scripts/v5_candidate_engine_v22.py"] and
         b["guarded_blob_sha"]==gate["protected_blobs"]["scripts/v5_candidate_engine_v22_guarded.py"] and
         b["not_independently_blind"] is True and
         b["baseline_claims"]==180 and b["new_claims"]==14 and
         b["baseline_videos"]==16 and b["new_videos"]==2 and
         b["all_claims"]==194 and b["all_pairs"]==18721 and
         b["new_involving_pairs"]==2611 and
         b["case_count"]==93 and len(b["tests"])==93 and
         b["case_split"]=={"new_17_vs_older":41,
                           "new_18_vs_older":42,"new_17_vs_new_18":10} and
         b["positive_expected"]==55 and b["negative_expected"]==38 and
         len(b["new_video_sources"])==2,
         "precommit sample size or holdout universe altered")
    src_map={x["roster_number"]:x for x in b["new_video_sources"]}
    need({n:x["video_id"] for n,x in src_map.items()}==EXPECTED_VIDEOS,
         "new-video roster numbers changed")
    old, cases=source_contract_v22(root)
    need(len(old)==180 and len(cases)==251,
         "V2.2 historical development claims or cases changed")
    idx=read(root/"data/subtitles/content_index_001_070.json")["items"]
    for num,id in EXPECTED_VIDEOS.items():
        x=src_map[num];expected=EXPECTED_PROVENANCE[id]
        p=x["original_v3_source"]
        need(p==f"data/analysis_events/{id}.json" and
             git_blob_sha(root/p)==x["original_v3_blob_sha"]==expected["v3"] and
             x["registered_subtitle_sha256"]==idx[id]["subtitle_sha256"]==expected["srt"] and
             x["registered_cues"]==idx[id]["cue_count"]==expected["cue_count"] and
             idx[id]["roster_no"]==num and x["claim_count"]==7 and
             set(x["refuted_claim_ids"])==(REFUTED_NEW if num==17 else set()),
             "new V3 source hash, SRT registration or correction provenance mismatch")
        src=read(root/p)
        need(src["video_id"]==id and src["approval"]=="APPROVED" and
             src["analysis_status"]=="COMPLETE" and
             src["evidence_gate"]["source_checked"] is True and
             src["evidence_gate"]["source_fingerprint"]==expected["srt"] and
             len(src["core_claims"])==7 and
             {c["claim_id"] for c in src["core_claims"] if c["verification"]=="CONTRADICTED"}==set(x["refuted_claim_ids"]),
             "V3 claim proof-of-source or correction status altered")
        for item in src["core_claims"]:
            cid=item["claim_id"]
            need(cid.startswith(id+"-") and cid not in old and
                 item["claim"] and item["timecode"] and
                 item["verification"] in ALLOWED_VERDICTS,
                 "new claim lacks canonical text, status or timestamp")
            old[cid]={"id":cid,"text":item["claim"],
                      "verdict":item["verification"],"video_number":num,
                      "video_id":id}
    need(len(old)==194 and
         {cid for cid,c in old.items() if c["verdict"]=="CONTRADICTED"}==REFUTED_OLD|REFUTED_NEW,
         "new claim count or 11 correction-only claims changed")
    legacy,_,_=load_legacy_claim_index(root)
    verified_verdict_reconciliations(root,legacy)
    need(all(cid in legacy and legacy[cid]["video_id"]==old[cid]["video_id"]
             and legacy[cid]["original_verdict"]==old[cid]["verdict"]
             for cid in old if old[cid]["video_number"]>=17),
         "new V3 claim not crosswalk reconciled with old 4120 historical assertions")
    seen=set()
    for t in b["tests"]:
        k=(t["left"],t["right"])
        need(len(t["reason"])>=12 and k not in seen and
             t["left"] in old and t["right"] in old and
             t["left"]!=t["right"] and t["analyst_label"] in
             {"QUALIFY","CORRECTION_REVIEW","TOPIC_ONLY"} and
             t["approved_merge"] is False and
             t["independent_blind_gold"] is False,
             "invalid label or unverified human approval")
        seen.add(k)
        a=old[t["left"]];c=old[t["right"]]
        if t["id"].startswith("NEW17-"):
            need(a["video_number"]==17 and c["video_number"]<=16,
                 "NEW17 case must be first-use vs historical")
        elif t["id"].startswith("NEW18-"):
            need(a["video_number"]==18 and c["video_number"]<=16,
                 "NEW18 case must be first-use vs historical")
        else:
            need(t["id"].startswith("CROSS17-18-") and a["video_number"]==17 and c["video_number"]==18,
                 "new-new cases must compare 17 with 18")
        if t["analyst_label"]=="CORRECTION_REVIEW":
            need(a["verdict"]=="CONTRADICTED" or c["verdict"]=="CONTRADICTED",
                 "correction label missing source contradiction")
        if a["verdict"]=="CONTRADICTED" or c["verdict"]=="CONTRADICTED":
            need(t["analyst_label"]!="QUALIFY",
                 "contradicted assertion improperly positive-used")
    for prefix,n in EXPECTED_COUNTS.items():
        need(sum(t["id"].startswith(prefix) for t in b["tests"])==n,
             "precommitted diagnostic strata changed")
    return old,b["tests"]

def ratios(x):
    return {"precision":round(x["TP"]/(x["TP"]+x["FP"]),6)
                if x["TP"]+x["FP"] else None,
            "recall":round(x["TP"]/(x["TP"]+x["FN"]),6)
                if x["TP"]+x["FN"] else None,
            "specificity":round(x["TN"]/(x["TN"]+x["FP"]),6)
                if x["TN"]+x["FP"] else None}

def run(root,full=False):
    claims,tests=validate_benchmark(root,read(root/BENCH))
    baseline=v22_development(root)
    need(baseline["total_confusion"]==EXPECTED_BASELINE_V22 and
         baseline["candidate_pairs_all"]==2211,
         "historical 251 developer baselines/16,110 candidate count changed")
    by_group={k:dict.fromkeys(("TP","FN","FP","TN"),0) for k in EXPECTED_COUNTS}
    rows=[]
    for t in tests:
        a,b=claims[t["left"]],claims[t["right"]]
        hit,why=retrieve_claims(a,b)
        expected=t["analyst_label"]!="TOPIC_ONLY"
        outcome=("TP" if hit else "FN") if expected else ("FP" if hit else "TN")
        group=next(k for k in EXPECTED_COUNTS if t["id"].startswith(k))
        by_group[group][outcome]+=1
        rows.append({"id":t["id"],"left":t["left"],"right":t["right"],
          "analyst_label":t["analyst_label"],"predicted_candidate":hit,
          "confusion":outcome,
          "v22_bridges":why["v22_bridges"],
          "inherited_v21_positive":why["v22_base_v21_candidate"],
          "v22_scope_blocks":why["v22_scope_blocks"],
          "inherited_scope_blocks":why["inherited_v21_v2_scope_blocks"],
          "source_risk":why["source_risk"],
          "automatic_merge_permitted":why["automatic_merge_permitted"]})
    need([sum(x.values()) for x in by_group.values()]==list(EXPECTED_COUNTS.values()),
         "incomplete first-use group scoring")
    total={k:sum(v[k] for v in by_group.values())
           for k in ("TP","FN","FP","TN")}
    all_candidates=new_candidates=new_possible=refuted_only=hypothetical_only=0
    for aid,bid in itertools.combinations(sorted(claims),2):
        a,b=claims[aid],claims[bid]
        hit,why=retrieve_claims(a,b)
        all_candidates+=hit
        if a["video_number"]>=17 or b["video_number"]>=17:
            new_possible+=1
            new_candidates+=hit
            if hit and why["source_risk"]=="CORRECTION_ONLY":refuted_only+=1
            if hit and why["source_risk"]=="UNREPLICATED_HYPOTHETICAL_SOURCE":hypothetical_only+=1
    need(new_possible==2611 and
         len(claims)*(len(claims)-1)//2==18721,
         "comparison denominator inconsistent")
    return {
        "schema":EXPECTED_FIRST_USE_SCHEMA,
        "evaluation":"FROZEN_V22_FIRST_USE_017_018_NOT_INDEPENDENTLY_BLINDED_GOLD",
        "source_srt_reopened_during_this_test":False,
        "historical_v3_claims_reverified_from_original_audio":False,
        "new_videos":[17,18],"new_source_claims":14,
        "cumulative_video_count":18,"cumulative_claim_count":194,
        "new_contradicted_claim_ids":sorted(REFUTED_NEW),
        "legacy_refuted_claims_protected":10,
        "universe":{"all_pairs":18721,"new_involving_pairs":2611,
                    "all_candidates":all_candidates,
                    "new_involving_candidates":new_candidates,
                    "new_involving_refuted_candidates_correction_only":refuted_only,
                    "new_involving_hypothetical_candidates_review_only":hypothetical_only},
        "baseline_1_to_16_development":{"case_count":251,"confusion":EXPECTED_BASELINE_V22,
                    "candidate_pairs":2211},
        "diagnostic":{"case_count":93,"by_group":{k:{"confusion":v,**ratios(v)}
                            for k,v in by_group.items()},
                      "confusion":total,**ratios(total),
                      "independently_blinded":False,
                      "population_generalizable":False},
        "case_results":rows if full else None,
        "errors":[x for x in rows if x["confusion"] in ("FN","FP")],
        "automatic_semantic_approvals":0,
        "automatic_knowledge_merges":0,
        "new_research_completion_certificates":0,
        "new_video_source_audio_certificates":0,
        "production_ready":False}

def negative_tests(root):
    claims,tests=validate_benchmark(root,read(root/BENCH))
    reversed_count=0
    for t in tests:
        a,b=claims[t["left"]],claims[t["right"]]
        p,d=retrieve_claims(a,b)
        q,e=retrieve_claims(b,a)
        need(p==q and d["correction_only"]==e["correction_only"],
             "candidate asymmetric for novel source video")
        reversed_count+=1
    a=next(c for c in claims.values() if c["video_number"]==17)
    b=next(c for c in claims.values() if c["video_number"]==18)
    rejected=0
    for mutated in [
        dict(a,verdict=None),dict(a,verdict="VERIFIED"),
        dict(a,text=""),dict(a,video_id="INVALID_VIDEO"),
        dict(a,id=b["id"]),dict(a,video_number=0),
    ]:
        try:retrieve_claims(mutated,b)
        except ValueError:rejected+=1
        else:raise ValueError("invalid source-claim metadata accepted")
    need(rejected==6 and reversed_count==93,
         "new source provenance mutations or symmetry incomplete")
    first=run(root)
    need(first==run(root),"first-use decisions not deterministic")
    return {"invalid_source_metadata_inputs_blocked":rejected,
            "pair_order_symmetry":reversed_count,
            "repeat_full_universe_deterministic":True,
            "human_review_approval_only":True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--show-cases",action="store_true")
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--assert-snapshot",action="store_true")
    args=p.parse_args()
    root=args.root.resolve()
    r=run(root,args.show_cases)
    if args.self_test:r["negative_tests"]=negative_tests(root)
    if args.assert_snapshot:
        saved=read(root/"v5/integration/v22_first_use_017_018_results_v1.json")
        full=r["case_results"] if args.show_cases else run(root,True)["case_results"]
        for k in ("universe","diagnostic","baseline_1_to_16_development",
                  "new_contradicted_claim_ids"):
            need(saved[k]==r[k],"postcommitted output drift: "+k)
        need(saved["case_results"]==full and saved["production_ready"] is False,
             "original first-use 93-case decisions changed")
    print(json.dumps(r,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    try:main()
    except (KeyError,ValueError,TypeError,IndexError,OSError) as ex:
        print(json.dumps({"gate":"FAIL","error":str(ex)},ensure_ascii=False))
        raise SystemExit(1)
