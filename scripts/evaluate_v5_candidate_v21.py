#!/usr/bin/env python3
"""Development-only 162-diagnostic replay for V2.1.

Do NOT report these scores as independent accuracy: all #1-#14 cases were
available during V2.1 development. Preserve frozen V2, V1 and source records.
"""
import argparse
import copy
import itertools
import json
from pathlib import Path

from evaluate_v5_candidate_v2 import data as old_data,evaluate as v2_1to12
from evaluate_v5_candidate_v2_013_014 import (
    BENCH as HOLDOUT_013_014, FROZEN as FROZEN_V2,
    validate_contract as validate_v2_holdout, load_new,
)
from evaluate_v5_001_010_synthesis import read,need,git_blob_sha
from verify_v5_knowledge_integration import (
    load_legacy_claim_index,verified_verdict_reconciliations,
)
from v5_candidate_engine_v21 import retrieve

ROOT=Path(__file__).resolve().parents[1]
CASES_TOTAL=162
EXPECTED_V2={
  "old_38":{"TP":30,"FP":0,"FN":0,"TN":8},
  "added_60":{"TP":29,"FP":0,"FN":0,"TN":31},
}
EXPECTED_V2_NEW={"TP":19,"FP":2,"FN":25,"TN":18}
VERDICTS_REFUTED={"sz5N9WJS310-06","sz5N9WJS310-15","aNfGrcO6WPI-03",
                  "VKr060rIirM-05","3_9IXnycZ3s-04","3_9IXnycZ3s-05",
                  "keu5SvpD7KE-04","keu5SvpD7KE-06",
                  "IMJfPgmnFwc-01","IMJfPgmnFwc-07"}

def source_contract(root):
    old_b,new_b,claims,old_tests=old_data(root)
    heldout=read(root/HOLDOUT_013_014)
    validate_v2_holdout(heldout,root)
    frozen=read(root/FROZEN_V2)
    need(frozen["overall_diagnostic_confusion"]==
         {"TP":59,"FN":0,"FP":0,"TN":39},
         "frozen V2 98-case baseline drift")
    need(frozen["engine_git_blob_sha"]==
         git_blob_sha(root/"scripts/v5_candidate_engine_v2.py"),
         "do not replace V2 under V2.1")
    newer=load_new(heldout,root,claims)
    need(len(claims)==155 and len(newer)==18 and
         len(old_tests)==98 and len(heldout["new_video_diags"])==64,
         "no source claims/diagnostic labels can be removed")
    historical,_,_=load_legacy_claim_index(root)
    verified_verdict_reconciliations(root,historical)
    need(all(cid in historical and historical[cid]["video_id"]==claims[cid]["video_id"]
             for cid in claims),
         "source ID must remain in 4,120 claim legacy crosswalk")
    need({cid for cid,c in claims.items() if c["verdict"]=="CONTRADICTED"}==
         VERDICTS_REFUTED,
         "refuted claims changed or promoted")
    allcases=old_tests+heldout["new_video_diags"]
    need(len(allcases)==CASES_TOTAL and
         len({t["id"] for t in allcases})==CASES_TOTAL,"duplicate/missing diagnostic")
    return claims,allcases

def ratio(a,b):
    return round(a/b,6) if b else None

def evaluate(root,with_cases=False):
    claims,cases=source_contract(root)
    confusion={
      "legacy_38":dict.fromkeys(("TP","FP","FN","TN"),0),
      "next_60":dict.fromkeys(("TP","FP","FN","TN"),0),
      "new_13_14_64":dict.fromkeys(("TP","FP","FN","TN"),0),
    }
    rows=[]
    for t in cases:
        left,right=claims[t["left"]],claims[t["right"]]
        found,ex=retrieve(left["text"],right["text"],
                 left_verdict=left["verdict"],right_verdict=right["verdict"])
        need(ex["review_only"] and ex["automatic_knowledge_approval"] is False and
             ex["semantic_relation_prediction"] is None,
             "candidate must remain manually reviewed and unapproved")
        need(ex["correction_only"]==
             (left["verdict"]=="CONTRADICTED" or right["verdict"]=="CONTRADICTED"),
             "correction-only status must not be lost")
        expected=t["analyst_label"]!="TOPIC_ONLY"
        state=("TP" if found else "FN") if expected else ("FP" if found else "TN")
        key="legacy_38" if t["id"].startswith("PAIR-") else (
            "next_60" if t["id"].startswith("H") else "new_13_14_64")
        confusion[key][state]+=1
        rows.append({
          "id":t["id"],"left":t["left"],"right":t["right"],
          "analyst_label":t["analyst_label"],"predicted_candidate":found,
          "confusion":state,"v21_bridges":ex["v21_bridges"],
          "v21_scope_blocks":ex["v21_scope_blocks"],
          "v2_raw_candidate":ex["v21_raw_v2_candidate"],
          "correction_only":ex["correction_only"],
        })
    expected_sizes={"legacy_38":38,"next_60":60,"new_13_14_64":64}
    need(all(sum(c.values())==expected_sizes[k] for k,c in confusion.items()),
         "case denominator drift")
    total={k:sum(c[k] for c in confusion.values()) for k in ("TP","FP","FN","TN")}
    stats={k:{"counts":c,"precision":ratio(c["TP"],c["TP"]+c["FP"]),
              "recall":ratio(c["TP"],c["TP"]+c["FN"]),
              "specificity":ratio(c["TN"],c["TN"]+c["FP"])}
           for k,c in confusion.items()}
    all_found=new_found=correction_found=0
    for aid,bid in itertools.combinations(sorted(claims),2):
        a,b=claims[aid],claims[bid]
        found,ex=retrieve(a["text"],b["text"],
                     left_verdict=a["verdict"],right_verdict=b["verdict"])
        all_found+=found
        if a["video_number"]>=13 or b["video_number"]>=13:
            new_found+=found
        if found and ex["correction_only"]:correction_found+=1
    need(len(claims)*(len(claims)-1)//2==11935,
         "claim pair universe changed")
    return {
      "schema":"V5_CANDIDATE_V21_001_014_DEVELOPMENT_REPLAY_V1",
      "assessment":"POST_HOC_DEVELOPMENT_REPLAY_NOT_INDEPENDENT_VALIDATION",
      "engine_version":"2.1.0",
      "videos":14,"claims":155,"possible_pairs":11935,
      "candidate_pairs":all_found,"candidate_pairs_involving_13_14":new_found,
      "candidate_edges_with_refutation_review_only":correction_found,
      "diagnostic_sizes":expected_sizes,
      "test_sets":stats,"total_confusion":total,
      "development_corpus_used_to_design_rules":True,
      "independently_blinded_gold":False,
      "semantic_relation_predictions":0,
      "research_completion_certificates":0,
      "approved_semantic_merges":0,
      "refuted_claims_preserved":len(VERDICTS_REFUTED),
      "cases":rows if with_cases else None,
      "errors":[x for x in rows if x["confusion"] in ("FN","FP")],
    }

def mutation_tests(root):
    claims,cases=source_contract(root)
    for cid in sorted(VERDICTS_REFUTED):
        a=claims[cid]
        _,ex=retrieve(a["text"],a["text"],
                 left_verdict=a["verdict"],right_verdict=a["verdict"])
        need(ex["correction_only"] and not ex["automatic_knowledge_approval"],
             "refuted assertion was granted knowledge approval")
    # Scope mutations test generalized cases, not historical claim IDs:
    negative=[
      ("연금계좌 연 1,800만원 일반납입 한도와 세액공제 납입 한도",
       "사적연금 연 1,500만원 연금소득 과세기준을 확인한다",
       "contribution_limit_vs_pension_income_tax_threshold"),
      ("ETF·펀드 모두 전문가가 임의로 종목을 골라 주는 구조는 아니다. 운용자 재량",
       "채권 금 달러 ETF 등을 자산배분하여 위험수준을 관리한다",
       "etf_manager_discretion_vs_multiasset_allocation"),
    ]
    negative.append((
      "엔화로 표시되는 일본 초단기국채 ETF는 환율위험과 채권 민감도를 가진다",
      "원화를 일본 엔화로 직접 환전할 때 스프레드와 현찰 취급 비용을 검토한다",
      "bond_etf_vs_conversion_spread"
    ))
    guarded=0
    for a,b,code in negative:
        yes,ex=retrieve(a,b)
        need(not yes and
             (code in ex["v21_scope_blocks"] or
              code in ex["inherited_v2_scope_blocks"]),
             "scope anti-conflation corruption failed")
        guarded+=1
    # Symmetry checks hold for all diagnostic comparisons in the absence of
    # directional labels. Candidate recall/precision is independent of order.
    for case in cases:
        a,b=claims[case["left"]],claims[case["right"]]
        left=retrieve(a["text"],b["text"],left_verdict=a["verdict"],right_verdict=b["verdict"])
        right=retrieve(b["text"],a["text"],left_verdict=b["verdict"],right_verdict=a["verdict"])
        need(left[0]==right[0] and
             left[1]["correction_only"]==right[1]["correction_only"],
             "order-dependent pair retrieval")
    first=evaluate(root);second=evaluate(root)
    need(first==second,"V2.1 replay not deterministic")
    return {"refuted_cases_approval_blocked":len(VERDICTS_REFUTED),
            "negative_scope_mutations_blocked":guarded,
            "candidate_order_symmetry_cases":len(cases),
            "full_replay_deterministic":True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--show-cases",action="store_true")
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--require-snapshot",action="store_true")
    args=p.parse_args()
    root=args.root.resolve()
    ans=evaluate(root,args.show_cases)
    if args.self_test:ans["negative_tests"]=mutation_tests(root)
    if args.require_snapshot:
        saved=read(root/"v5/integration/v21_development_001_014_v1.json")
        need(saved["source_engine_git_blob_sha"]==
             git_blob_sha(root/"scripts/v5_candidate_engine_v21.py") and
             saved["release_gate"].startswith("BLOCKED_PENDING_"),
             "V2.1 source was modified after frozen development run")
        for field in ("test_sets","total_confusion","candidate_pairs",
                      "candidate_pairs_involving_13_14"):
            need(saved[field]==ans[field],"V2.1 baseline has changed: "+field)
        archived=read(root/"v5/integration/v21_case_results_001_014_v1.json")
        full=ans["cases"] if args.show_cases else evaluate(root,with_cases=True)["cases"]
        need(archived["engine_git_blob_sha"]==saved["source_engine_git_blob_sha"]
             and archived["case_count"]==162 and archived["cases"]==full,
             "162-case V2.1 exact replay differs from archived predictions")
    print(json.dumps(ans,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    try:main()
    except (ValueError,TypeError,KeyError,OSError,IndexError) as e:
        print(json.dumps({"gate":"FAIL","error":str(e)},ensure_ascii=False))
        raise SystemExit(1)
