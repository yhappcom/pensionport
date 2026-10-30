#!/usr/bin/env python3
"""First-use #13/#14 holdout for immutable V2 engine, no semantic approval.

Developer did not look at V2 predictions for new cases before preregistering
the diagnostic pair labels. The labels are still analyst-selected and not an
independent/representative blinded gold set. Do not tune V2 after seeing this.
"""
import argparse
import copy
import itertools
import json
from pathlib import Path

from evaluate_v5_candidate_v2 import (
 data as old_data, evaluate as evaluate_old,
)
from evaluate_v5_001_010_synthesis import read,need,git_blob_sha
from verify_v5_knowledge_integration import (
 load_legacy_claim_index,verified_verdict_reconciliations,
)
from v5_candidate_engine_v2 import retrieve

ROOT=Path(__file__).resolve().parents[1]
BENCH="v5/integration/benchmark_013_014_v2_holdout_v1.json"
FROZEN="v5/integration/v2_development_001_012_v1.json"
IDS={13:"keu5SvpD7KE",14:"IMJfPgmnFwc"}
CORRECTED={"keu5SvpD7KE-04","keu5SvpD7KE-06",
           "IMJfPgmnFwc-01","IMJfPgmnFwc-07"}
KNOWN_VERDICTS={"QUALIFIED","PRIMARY_CONFIRMED","HYPOTHETICAL",
                "CONTRADICTED","SPEAKER_OPINION"}
LABELS={"SUPPORT","QUALIFY","CORRECTION_REVIEW","TOPIC_ONLY"}

def validate_contract(b,root):
    f=read(root/FROZEN)
    need(b["schema"]=="V5_CANDIDATE_V2_013_014_FIRST_USE_HOLDOUT_V1"
         and b["basis"]=="FROZEN_V2_BEFORE_ANY_TEST_ON_13_14"
         and b["engine_path"]==f["engine_path"]
         and b["engine_git_blob_sha"]==f["engine_git_blob_sha"]
         and git_blob_sha(root/b["engine_path"])==b["engine_git_blob_sha"],
         "frozen V2 code must not change after #13/#14 label registration")
    need(b["development_baseline_path"]==FROZEN
         and b["old_claim_count"]==137
         and b["new_claim_count"]==18
         and b["total_claim_count"]==155
         and b["old_pair_universe"]==9316
         and b["new_pair_universe"]==2619
         and b["total_pair_universe"]==11935
         and b["auto_knowledge_approval"] is False
         and b["independent_gold"] is False,
         "incorrect 13-14 universe or false research approval")
    need(len(b["new_video_sources"])==2 and
         {x["video_number"]:x["video_id"] for x in b["new_video_sources"]}==IDS and
         [x["claim_count"] for x in b["new_video_sources"]]==[9,9] and
         set.union(*(set(x["corrected_only_claim_ids"]) for x in b["new_video_sources"]))==CORRECTED,
         "V3 source ids, denominator, refutations changed")
    t=b["new_video_diags"]
    need(len(t)==64 and len({x["id"] for x in t})==64
         and sum(x["left"].startswith(IDS[13]+"-") for x in t)==30
         and sum(x["left"].startswith(IDS[14]+"-") for x in t)==34,
         "holdout cases 13/14 are not frozen")
    pairs=set()
    for x in t:
        key=tuple(sorted((x["left"],x["right"])))
        need(key not in pairs and x["left"]!=x["right"]
             and x["id"].startswith("NEW13-" if x["left"].startswith(IDS[13]+"-") else "NEW14-")
             and x["left"][:11] in IDS.values()
             and x["right"][:11] not in IDS.values()
             and x["analyst_label"] in LABELS
             and x["adjudication"]=="ANALYST_DIAGNOSTIC_NOT_INDEPENDENT"
             and x["certified_merge"] is False
             and len(x["reason"])>8,
             "untrusted, duplicated or missing 13-14 diagnostic evidence")
        pairs.add(key)
        if x["analyst_label"]=="CORRECTION_REVIEW":
            need(x["left"] in CORRECTED or x["right"] in
                 {"3_9IXnycZ3s-04","3_9IXnycZ3s-05",
                  "aNfGrcO6WPI-03","sz5N9WJS310-15","sz5N9WJS310-06",
                  "VKr060rIirM-05"},
                 "correction case must cite a verified refutation")
        if x["left"] in CORRECTED:
            need(x["analyst_label"]!="SUPPORT",
                 "historically refuted source cannot be positive support")
    return t

def load_new(b,root,old):
    idx=read(root/"data/subtitles/content_index_001_070.json")["items"]
    new={}
    for src in b["new_video_sources"]:
        vid=src["video_id"];no=src["video_number"]
        path=src["v3_path"]
        need(path==f"data/analysis_events/{vid}.json"
             and git_blob_sha(root/path)==src["v3_git_blob_sha"]
             and idx[vid]["roster_no"]==no
             and idx[vid]["subtitle_sha256"]==src["registered_srt_sha256"],
             "source hash, video no, SRT fingerprint mismatch")
        rec=read(root/path)
        need(rec["video_id"]==vid and rec["approval"]=="APPROVED"
             and rec["analysis_status"]=="COMPLETE"
             and len(rec["core_claims"])==9,
             "historic educational analysis not approved")
        for claim in rec["core_claims"]:
            cid=claim["claim_id"]
            need(cid.startswith(vid+"-") and cid not in new and cid not in old
                 and claim["verification"] in KNOWN_VERDICTS
                 and claim.get("timecode"),"new claim ID, verifier, timestamp missing")
            new[cid]={"id":cid,"text":claim["claim"],
                      "verdict":claim["verification"],
                      "video_number":no,"video_id":vid,
                      "source_blob":src["v3_git_blob_sha"]}
    need(len(new)==18
         and {cid for cid,x in new.items()
              if x["verdict"]=="CONTRADICTED"}==CORRECTED,
         "source corrections cannot be altered or lost")
    old.update(new)
    return new

def evaluate(b,root,include_cases=False):
    tests=validate_contract(b,root)
    _,_,claims,_=old_data(root)
    old_stats=evaluate_old(root)
    frozen=read(root/FROZEN)
    for field in ("test_sets","overall_diagnostic_confusion",
                  "total_candidates","new_involving_candidates"):
        need(old_stats[field]==frozen[field],
             "V2 #1-12 development baseline changed before first-use")
    new=load_new(b,root,claims)
    known,_,_=load_legacy_claim_index(root)
    verified_verdict_reconciliations(root,known)
    discrepancies=[]
    for cid,c in new.items():
        need(cid in known and known[cid]["video_id"]==c["video_id"],
             "new claim missing from original 4,120 crosswalk")
        if known[cid]["original_verdict"]!=c["verdict"]:
            discrepancies.append({"claim_id":cid,"original_v3":c["verdict"],
               "crosswalk":known[cid]["original_verdict"],
               "status":"OPEN_PROVENANCE_DO_NOT_AUTO_APPROVE"})
    need(len(claims)==155 and len(claims)*(len(claims)-1)//2==11935,
         "wrong source denominator")

    n_candidates=n_new_candidates=n_new_pairs=0
    for aid,bid in itertools.combinations(sorted(claims),2):
        a=claims[aid];c=claims[bid]
        candidate,_=retrieve(a["text"],c["text"],
                 left_verdict=a["verdict"],right_verdict=c["verdict"])
        n_candidates+=candidate
        if aid in new or bid in new:
            n_new_pairs+=1;n_new_candidates+=candidate
    need(n_new_pairs==2619,"new pair scope drift")
    count={"TP":0,"FN":0,"FP":0,"TN":0}
    per={"13":dict.fromkeys(count,0),"14":dict.fromkeys(count,0)}
    rows=[]
    for case in tests:
        aid,bid=case["left"],case["right"]
        need(aid in new and bid in claims and bid not in new,
             "holdout requires exact new-vs-historical claim IDs")
        a,c=claims[aid],claims[bid]
        flag,explain=retrieve(a["text"],c["text"],
                 left_verdict=a["verdict"],right_verdict=c["verdict"])
        relevant=case["analyst_label"]!="TOPIC_ONLY"
        k=("TP" if flag else "FN") if relevant else ("FP" if flag else "TN")
        count[k]+=1
        per[str(a["video_number"])][k]+=1
        need(explain["review_only"] is True
             and (aid not in CORRECTED or explain["correction_only"]),
             "corrected source cannot be certified by retrieval")
        rows.append({"id":case["id"],"left":aid,"right":bid,
                     "analyst_label":case["analyst_label"],
                     "prediction":flag,"confusion":k,
                     "explanation":explain,
                     "semantic_merge_approved":False})
    need(sum(count.values())==64,"missing 13/14 diagnostic row")
    return {"schema":"V5_CANDIDATE_V2_013_014_FIRST_USE_RESULT_V1",
      "engine_frozen":True,
      "labels_independently_blinded":False,
      "independently_generalizable":False,
      "existing_1_12_development_replay":old_stats["test_sets"],
      "videos":14,"claims":155,"new_claims":18,
      "pairs":{"all":11935,"new_involving":2619,
               "candidate_all":n_candidates,
               "candidate_new_involving":n_new_candidates},
      "new_crosswalk_verdict_discrepancies":discrepancies,
      "sample_size":64,"confusion":count,"per_video":per,
      "precision":count["TP"]/(count["TP"]+count["FP"]) if count["TP"]+count["FP"] else None,
      "recall":count["TP"]/(count["TP"]+count["FN"]) if count["TP"]+count["FN"] else None,
      "specificity":count["TN"]/(count["TN"]+count["FP"]) if count["TN"]+count["FP"] else None,
      "new_refuted_ids":sorted(CORRECTED),
      "auto_relation_labels":0,"approved_knowledge_merges":0,
      "new_research_complete_certificates":0,
      "cases":rows if include_cases else None}

def negative_tests(b,root):
    muts=[]
    x=copy.deepcopy(b);x["engine_git_blob_sha"]="0"*40;muts.append(x)
    x=copy.deepcopy(b);x["total_claim_count"]=154;muts.append(x)
    x=copy.deepcopy(b);x["auto_knowledge_approval"]=True;muts.append(x)
    x=copy.deepcopy(b);x["new_video_sources"][0]["claim_count"]=8;muts.append(x)
    x=copy.deepcopy(b);x["new_video_sources"][1]["corrected_only_claim_ids"]=[];muts.append(x)
    x=copy.deepcopy(b);x["new_video_diags"][0]["certified_merge"]=True;muts.append(x)
    x=copy.deepcopy(b);x["new_video_diags"][0]["left"]=x["new_video_diags"][0]["right"];muts.append(x)
    x=copy.deepcopy(b);x["new_video_diags"].pop();muts.append(x)
    c=next(x for x in b["new_video_diags"] if x["left"] in CORRECTED and
           x["analyst_label"]=="CORRECTION_REVIEW")
    x=copy.deepcopy(b)
    next(y for y in x["new_video_diags"] if y["id"]==c["id"])["analyst_label"]="SUPPORT"
    muts.append(x)
    rejected=0
    for x in muts:
        try:validate_contract(x,root)
        except (ValueError,TypeError,KeyError):rejected+=1
        else:raise ValueError("unsafe 13-14 benchmark mutation accepted")
    a=evaluate(b,root);c=evaluate(b,root)
    need(a==c,"13-14 first-use prediction nondeterminism")
    return {"negative_mutations_rejected":rejected,
            "exact_deterministic_replay":True}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,default=ROOT)
    ap.add_argument("--self-test",action="store_true")
    ap.add_argument("--show-cases",action="store_true")
    args=ap.parse_args()
    root=args.root.resolve()
    b=read(root/BENCH)
    result=evaluate(b,root,args.show_cases)
    if args.self_test:result["regression"]=negative_tests(b,root)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
if __name__=="__main__":
    try:main()
    except (ValueError,TypeError,KeyError,IndexError,OSError,OverflowError) as e:
        print(json.dumps({"gate":"FAIL","error":str(e)},ensure_ascii=False))
        raise SystemExit(1)
