#!/usr/bin/env python3
"""V2.2 RETROSPECTIVE development replay: 162 old + 89 V2.1 first-use cases.

The #15-16 cases have become DEVELOPMENT DATA after inspection by V2.2
developers; a perfect score is NOT fresh out-of-sample evidence. #17 onward
must stay untouched for first-use testing after V2.2 source freeze.
"""
import argparse
import itertools
import json
from pathlib import Path

from evaluate_v5_candidate_v21 import source_contract, evaluate as v21_development
from evaluate_v5_candidate_v21_015_016 import (
    BENCH as PREVIOUS_HOLDOUT, FREEZE as V21_FREEZE,
    validate_bench,load_sources,
)
from evaluate_v5_001_010_synthesis import read,need,git_blob_sha
from verify_v5_knowledge_integration import (
    load_legacy_claim_index,verified_verdict_reconciliations,
)
from v5_candidate_engine_v22 import retrieve

ROOT=Path(__file__).resolve().parents[1]
SNAPSHOT="v5/integration/v22_development_001_016_v1.json"
ARCHIVE="v5/integration/v22_case_results_001_016_v1.json"
EXPECTED_V21_162={"TP":103,"FN":0,"FP":0,"TN":59}
EXPECTED_V21_89={"TP":28,"FN":33,"FP":3,"TN":25}
VERDICTS_REFUTED={
    "sz5N9WJS310-06","sz5N9WJS310-15","aNfGrcO6WPI-03",
    "VKr060rIirM-05","3_9IXnycZ3s-04","3_9IXnycZ3s-05",
    "keu5SvpD7KE-04","keu5SvpD7KE-06",
    "IMJfPgmnFwc-01","IMJfPgmnFwc-07",
}

def source_contract_v22(root):
    freeze=read(root/V21_FREEZE)
    need(freeze["source_engine_git_blob_sha"]==
         git_blob_sha(root/"scripts/v5_candidate_engine_v21.py") and
         freeze["total_confusion"]==EXPECTED_V21_162,
         "original V2.1 immutable code or baseline is not valid")
    source_holdout=read(root/PREVIOUS_HOLDOUT)
    validate_bench(source_holdout,root)
    prior=read(root/"v5/integration/v21_first_use_015_016_results_v1.json")
    need(prior["diagnostic"]["confusion"]==EXPECTED_V21_89 and
         prior["diagnostic"]["n"]==89 and
         prior["frozen_engine_git_blob_sha"]==freeze["source_engine_git_blob_sha"],
         "original #15-16 first-use failure data changed")
    old_claims,old_cases=source_contract(root)
    newer=load_sources(source_holdout,root,old_claims)
    need(len(old_claims)==180 and len(newer)==25,
         "v22 must include every one of 180 source claims")
    legacy,_,_=load_legacy_claim_index(root)
    verified_verdict_reconciliations(root,legacy)
    need(all(cid in legacy and
             legacy[cid]["video_id"]==cl["video_id"] for cid,cl in old_claims.items()),
         "unrecognized original crosswalk claim ID")
    need({cid for cid,cl in old_claims.items()
          if cl["verdict"]=="CONTRADICTED"}==VERDICTS_REFUTED,
         "10 historically refuted claims changed")
    cases=old_cases+source_holdout["tests"]
    need(len(cases)==251 and len({t["id"] for t in cases})==251,
         "development label set missing or duplicated")
    return old_claims,cases

def safe_div(n,d):return round(n/d,6) if d else None

def evaluate(root,show_cases=False):
    claims,cases=source_contract_v22(root)
    labels={
       "legacy_38":dict.fromkeys(("TP","FP","FN","TN"),0),
       "next_60":dict.fromkeys(("TP","FP","FN","TN"),0),
       "new_13_14_64":dict.fromkeys(("TP","FP","FN","TN"),0),
       "dev_15_16_89":dict.fromkeys(("TP","FP","FN","TN"),0),
    }
    rows=[]
    for t in cases:
        a,b=claims[t["left"]],claims[t["right"]]
        found,detail=retrieve(a["text"],b["text"],
                        left_verdict=a["verdict"],right_verdict=b["verdict"])
        need(detail["review_only"] is True and
             detail["semantic_relation_prediction"] is None and
             detail["automatic_knowledge_approval"] is False and
             detail["candidate_is_evidence_of_claim_truth"] is False and
             detail["correction_only"]==(
             a["verdict"]=="CONTRADICTED" or b["verdict"]=="CONTRADICTED"),
             "V2.2 unreviewed merge/approval or refutation status")
        positive=t["analyst_label"]!="TOPIC_ONLY"
        quadrant=("TP" if found else "FN") if positive else ("FP" if found else "TN")
        grp=("legacy_38" if t["id"].startswith("PAIR-") else
             "next_60" if t["id"].startswith("H") else
             "new_13_14_64" if t["id"].startswith(("NEW13-","NEW14-")) else
             "dev_15_16_89")
        labels[grp][quadrant]+=1
        rows.append({
          "id":t["id"],"left":t["left"],"right":t["right"],
          "expected_label":t["analyst_label"],"predicted_candidate":found,
          "confusion":quadrant,"v22_bridges":detail["v22_bridges"],
          "v22_scope_blocks":detail["v22_scope_blocks"],
          "inherited_v21_v2_scope_blocks":detail["inherited_v21_v2_scope_blocks"],
          "baseline_v21_candidate":detail["v22_base_v21_candidate"],
          "correction_only":detail["correction_only"],
          "automatic_semantic_approval":False,
        })
    need([sum(labels[k].values()) for k in labels]==[38,60,64,89],
         "development test count changed")
    total={k:sum(v[k] for v in labels.values()) for k in ("TP","FP","FN","TN")}
    n_total=n_new=n_covered=n_refuted=0
    for aid,bid in itertools.combinations(sorted(claims),2):
        a,b=claims[aid],claims[bid]
        found,detail=retrieve(a["text"],b["text"],
                    left_verdict=a["verdict"],right_verdict=b["verdict"])
        n_total+=int(found)
        if a["video_number"]>=15 or b["video_number"]>=15:
            n_covered+=1;n_new+=int(found)
        if found and detail["correction_only"]:n_refuted+=1
    need(n_covered==4175 and len(claims)*(len(claims)-1)//2==16110,
         "source comparison denominator drift")
    measured={k:{"confusion":v,"precision":safe_div(v["TP"],v["TP"]+v["FP"]),
                 "recall":safe_div(v["TP"],v["TP"]+v["FN"]),
                 "specificity":safe_div(v["TN"],v["TN"]+v["FP"])}
              for k,v in labels.items()}
    return {
      "schema":"V5_CANDIDATE_V22_DEVELOPMENT_REPLAY_001_016_V1",
      "engine_version":"2.2.0",
      "benchmark_kind":"POST_HOC_251_CASE_DEVELOPMENT_NOT_UNSEEN_HOLDOUT",
      "videos":16,"claims":180,"all_possible_pairs":16110,
      "new_video_involving_pairs":4175,
      "candidate_pairs_all":n_total,
      "candidate_pairs_involving_15_16":n_new,
      "refuted_claim_candidate_edges_review_only":n_refuted,
      "case_count":251,"group_results":measured,"total_confusion":total,
      "automatic_semantic_classification_count":0,
      "automatic_knowledge_merge_count":0,
      "new_research_completion_certificates":0,
      "approved_trade_instructions":0,
      "independently_blinded":False,
      "out_of_sample_v22_validation_completed":False,
      "case_results":rows if show_cases else None,
      "errors":[z for z in rows if z["confusion"] in ("FN","FP")],
    }

def adversarial(root):
    claims,cases=source_contract_v22(root)
    guarded=0
    snippets=[
        ("배당금 정기매수와 현금배당 재투자로 복리효과를 추구한다",
         "퇴직금 목돈을 세 번 나눠 분할투자하는 방식", 
         "dividend_recycling_vs_retirement_lump_sum_scheduling"),
        ("미국배당다우존스 지수는 재무지표로 선별된 미국 기업 100개 지수다",
         "엔화로 미국 ETF 사거나 원화로 엔화 ETF를 사는 투자경로",
         "index_constituent_selection_vs_fx_execution_routes"),
        ("미국 SCHD 분기분배 국내 미국배당다우존스 월분배",
         "일본 상장 미국지수 ETF의 배당과 현지/국내 과세", 
         "distribution_cadence_vs_foreign_tax_jurisdiction"),
    ]
    for a,b,expected in snippets:
        hit,why=retrieve(a,b)
        need(not hit and expected in why["v22_scope_blocks"],
             "V2.2 must block incompatible financial action dimensions")
        guarded+=1
    # Engine must never convert an original refutation into positive support.
    for cid in VERDICTS_REFUTED:
        row=claims[cid]
        _,why=retrieve(row["text"],row["text"],
                       left_verdict=row["verdict"],right_verdict=row["verdict"])
        need(why["correction_only"] and why["review_only"] and
             why["automatic_knowledge_approval"] is False,
             "refutation was promoted")
    # Every case must be invariant under left/right reversal.
    for row in cases:
        a,b=claims[row["left"]],claims[row["right"]]
        yes,ex=retrieve(a["text"],b["text"],left_verdict=a["verdict"],right_verdict=b["verdict"])
        rev,exr=retrieve(b["text"],a["text"],left_verdict=b["verdict"],right_verdict=a["verdict"])
        need(yes==rev and ex["correction_only"]==exr["correction_only"],
             "V2.2 claim pair retrieval not symmetric")
    first=evaluate(root)
    need(first==evaluate(root),"V2.2 full universe replay not deterministic")
    return {"scope_confusion_mutations_rejected":guarded,
            "refuted_claims_quarantined":len(VERDICTS_REFUTED),
            "pair_order_symmetry_tests":len(cases),
            "full_universe_replay_deterministic":True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--show-cases",action="store_true")
    p.add_argument("--assert-snapshot",action="store_true")
    args=p.parse_args()
    root=args.root.resolve()
    result=evaluate(root,args.show_cases)
    if args.self_test:result["negative_tests"]=adversarial(root)
    if args.assert_snapshot:
        freeze=read(root/SNAPSHOT)
        need(freeze["engine_git_blob_sha"]==git_blob_sha(root/"scripts/v5_candidate_engine_v22.py"),
             "frozen V2.2 source hash drift")
        for a,b in (("group_results","group_results"),
                    ("total_confusion","total_confusion"),
                    ("candidate_pairs_all","candidate_pairs_all"),
                    ("candidate_pairs_involving_15_16","candidate_pairs_involving_15_16")):
            need(result[a]==freeze[b],"frozen V2.2 development measure drift: "+a)
        archive=read(root/ARCHIVE)
        actual=result["case_results"] if args.show_cases else evaluate(root,True)["case_results"]
        need(archive["case_results"]==actual and
             archive["engine_git_blob_sha"]==freeze["engine_git_blob_sha"],
             "frozen 251-case V2.2 predictions changed")
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    try:main()
    except (ValueError,TypeError,KeyError,IndexError,OSError) as e:
        print(json.dumps({"gate":"FAIL","error":str(e)},ensure_ascii=False))
        raise SystemExit(1)
