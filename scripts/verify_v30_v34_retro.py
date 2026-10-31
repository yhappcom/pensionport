#!/usr/bin/env python3
"""Historical development-only comparison with frozen V3.2 #66-70 labels.

This reuses exposed labels and claims: NOT a first-use, blind or independent
performance estimate. It does not tune V3.4 or modify existing V3.2 results.
"""
import json
from pathlib import Path
from v30_v34_pipeline import read_historical,historical_index
from v30_v34_retrieval import retrieve
from v30_verified_core import guard

ROOT=Path(__file__).resolve().parents[1]

def compare():
    gold=json.loads((ROOT/"v30/validation/v32_066_070_real_firstuse_result_v1.json").read_text(encoding="utf-8"))
    cases=gold["cases"]
    guard(len(cases)==48 and
          sum(bool(r["precommitted_relevance"]) for r in cases)==24,
          "V34_HISTORICAL_DIAGNOSTIC_GOLD_DENOMINATOR_CHANGED")
    records=read_historical(ROOT)
    corpus=tuple(r for r in historical_index(records) if 66<=r["video_number"]<=70)
    guard(len(corpus)==108,"V34_HISTORICAL_EVALUATION_COHORT_CHANGED")
    byid={r["claim_id"]:r for r in corpus}
    guard(all(c["left"] in byid and c["right"] in byid for c in cases),
          "V34_PRECOMMITTED_HISTORIC_PAIR_NOT_IN_INDEX")
    queries=sorted({x for c in cases for x in (c["left"],c["right"])})
    searched={qid:{x["claim_id"] for x in
                    retrieve(byid[qid],corpus,top_k=10,audit_count=0)["hits"]}
              for qid in queries}
    tp=fn=fp=tn=0
    for c in cases:
        hit=c["right"] in searched[c["left"]] or c["left"] in searched[c["right"]]
        if c["precommitted_relevance"]:
            if hit:tp+=1
            else:fn+=1
        else:
            if hit:fp+=1
            else:tn+=1
    guard(tp+fn==24 and fp+tn==24,"V34_HISTORICAL_DIAG_COUNTS_INVALID")
    return {
        "schema":"V34_EXPOSED_HISTORIC_066_070_RETROSPECTIVE_DIAGNOSTIC_V1",
        "cohort_videos":[66,67,68,69,70],
        "historical_claims":108,
        "previously_published_pair_labels":48,
        "positive_pairs":24,
        "negative_pairs":24,
        "top_k":10,
        "either_direction":True,
        "tp":tp,"fn":fn,"fp":fp,"tn":tn,
        "sample_recall":tp/24,
        "sample_precision":tp/(tp+fp) if tp+fp else None,
        "frozen_v32_previous_diagnostic_top10_recall":5/24,
        "scores_comparable_only_as_development_diagnostic":True,
        "same_search_retrieval_corpus_as_v32_certified":False,
        "labels_seen_in_previous_engine_development":True,
        "independent_blind_review":False,
        "actual_unseen_recall":None,
        "actual_unseen_precision":None,
        "automated_knowledge_approval":False,
        "release":"BLOCKED"
    }
if __name__=="__main__":
    print(json.dumps(compare(),sort_keys=True,ensure_ascii=False))
