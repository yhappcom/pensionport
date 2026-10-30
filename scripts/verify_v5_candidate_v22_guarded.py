#!/usr/bin/env python3
"""Prove V2.2 fail-closed provenance adapter preserves every frozen retrieval.

No new video access or source research. The source contract loads only 1-16.
"""
import argparse
import itertools
import json
from pathlib import Path

from evaluate_v5_candidate_v22 import source_contract_v22
from v5_candidate_engine_v22 import retrieve as frozen_v22_retrieve
from v5_candidate_engine_v22_guarded import retrieve_claims

ROOT=Path(__file__).resolve().parents[1]

def must_fail(a,b):
    try:
        retrieve_claims(a,b)
    except (ValueError,TypeError):
        return True
    raise ValueError("UNSAFE_METADATA_INPUT_ACCEPTED")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    args=p.parse_args()
    claims,_=source_contract_v22(args.root.resolve())
    rows=list(claims.values())
    if len(rows)!=180:raise ValueError("SOURCE_COUNT_UNEXPECTED")
    total=candidates=quarantined=hypothetical=0
    for a,b in itertools.combinations(rows,2):
        old,why_old=frozen_v22_retrieve(a["text"],b["text"],
                             left_verdict=a["verdict"],right_verdict=b["verdict"])
        new,why=retrieve_claims(a,b)
        if old!=new:raise ValueError("GUARDED_ADAPTER_ALTERED_ENGINE_PREDICTION")
        if why["source_claim_ids"]!=[a["id"],b["id"]]:
            raise ValueError("ORIGINAL_SOURCE_CLAIM_LINK_LOST")
        if why["source_risk"]=="CORRECTION_ONLY":
            quarantined+=int(new)
        if why["source_risk"]=="UNREPLICATED_HYPOTHETICAL_SOURCE":
            hypothetical+=int(new)
        if why["source_risk"]=="HUMAN_REVIEW_ONLY" and (
             a["verdict"] in ("CONTRADICTED","HYPOTHETICAL") or
             b["verdict"] in ("CONTRADICTED","HYPOTHETICAL")):
            raise ValueError("LIMITED_SOURCE_PROMOTED")
        if why["automatic_merge_permitted"] or
           why["investment_trade_instruction_permitted"] or
           why["research_completion_certificate_permitted"]:
            raise ValueError("UNSAFE_AUTO_APPROVAL")
        total+=1;candidates+=int(new)
    if total!=16110 or candidates!=2211 or quarantined!=313 or hypothetical>596:
        raise ValueError("FROZEN_CANDIDATE_UNIVERSE_DRIFT")
    a,b=rows[0],rows[1]
    def mutated(**kwargs):
        return dict(a,**kwargs)
    failcases=[
       ({},b),
       (mutated(verdict=None),b),
       (mutated(verdict="CORRECT"),b),
       (mutated(verdict="contradicted"),b),
       (mutated(id="bad"),b),
       (mutated(video_id="not_a_video"),b),
       (mutated(text=""),b),
       (mutated(text=" " ),b),
       (mutated(video_number=0),b),
       (mutated(video_number=True),b),
       (mutated(text=None),b),
       (a,a),
    ]
    for x,y in failcases:must_fail(x,y)
    # A repeated claim id is the same claim, not another valid comparison.
    return {"schema":"V5_V22_PROVENANCE_ADAPTER_CONTRACT_V1",
            "scope":"SOURCE_VERIFIED_001_016_NO_17_PLUS",
            "same_retrieval_predictions":True,"pair_count":total,
            "candidate_count":candidates,
            "blocked_contradicted_source_candidates":quarantined,
            "hypothetical_only_review_candidates":hypothetical,
            "invalid_metadata_mutations_rejected":len(failcases),
            "automatic_knowledge_merges":0,
            "research_completion_certificates":0}
if __name__=="__main__":
    try:print(json.dumps(main(),sort_keys=True))
    except (ValueError,TypeError,KeyError,OSError) as e:
        print(json.dumps({"gate":"FAIL","error":str(e)},ensure_ascii=False))
        raise SystemExit(1)
