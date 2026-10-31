#!/usr/bin/env python3
"""V3.4 integrated read-only development runner: SRT -> atoms -> frames -> search.

Does NOT run on protected #261+ material, write to frozen research ledgers,
create gold labels, approve knowledge, or claim independent retrieval recall.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
from v30_verified_core import guard, sha256, canonical, VID_RE
from v30_v34_atomic_semantics import make_draft, attach_frames
from v30_v34_retrieval import indexed_historical_claim, make_record, retrieve

FILES=(
    "data/synthesis/investment_knowledge_001_260/claims_crosswalk_001_130.json",
    "data/synthesis/investment_knowledge_001_260/claims_crosswalk_131_260.json",
)
ENGINE_SCHEMA="V34_INTEGRATED_DEV_ATOMIC_SEMANTIC_RETRIEVAL_V1"

def read_historical(root):
    """Original 4,120-claim frozen crosswalk, no silent omissions."""
    collected=[]
    for relative in FILES:
        filename=Path(root)/relative
        source=json.loads(filename.read_text(encoding="utf-8"))
        guard(type(source) is dict and type(source.get("records")) is list,
              "V34_HISTORICAL_CROSSWALK_MISSING_OR_INVALID")
        collected.extend(source["records"])
    guard(len(collected)==4120 and
          len({x["claim_id"] for x in collected})==4120 and
          len({x["roster_no"] for x in collected})==253,
          "V34_FROZEN_4120_HISTORY_DENOMINATOR_CHANGED")
    return collected

def historical_index(rows):
    """Every history row is searchable, even with missing source SHA."""
    guard(type(rows) is list,"V34_HISTORICAL_DATASET_REQUIRED")
    index=tuple(sorted((indexed_historical_claim(x) for x in rows),
                       key=lambda x:x["claim_id"]))
    guard(len(index)==len(rows) and len({x["claim_id"] for x in index})==len(rows),
          "V34_INDEX_DROPPED_HISTORY_CLAIMS")
    return index

def run_development(raw_srt,original_sha256,video_id,video_number,
                    historical,query_limit=None,synthetic_fixture=False):
    guard(type(video_number) is int and 1<=video_number<=260
          and type(video_id) is str and VID_RE.fullmatch(video_id)
          and type(query_limit) is int and query_limit>=1
              if query_limit is not None else
              type(video_number) is int and 1<=video_number<=260
              and type(video_id) is str and VID_RE.fullmatch(video_id),
          "V34_HOLDOUT_AND_INVALID_DEVELOPMENT_SOURCE_BLOCKED")
    draft=make_draft(raw_srt,original_sha256,video_id)
    semantics=attach_frames(draft)
    catalog=historical_index(historical)
    queries=[]
    count=len(draft["claims"]) if query_limit is None else min(
          query_limit,len(draft["claims"]))
    for atom,frame in zip(draft["claims"][:count],semantics["frames"][:count]):
        query=make_record(atom["claim_id"],atom["source_quote"],video_number,
                          original_sha256,frame=frame)
        queries.append(retrieve(query,catalog,top_k=10,audit_count=20))
    complete=len(queries)==len(draft["claims"])
    return {
        "schema":ENGINE_SCHEMA,
        "cohort":"SYNTHETIC_UNIT_TEST_ONLY" if synthetic_fixture else
                 "EXPOSED_HISTORICAL_DEVELOPMENT_ONLY",
        "source": {"video_id":video_id,"video_number":video_number,
                   "srt_sha256":original_sha256,
                   "source_audio_validated":False,
                   "human_cue_audit_completed":False},
        "atomic":draft,
        "semantics":semantics,
        "relations":queries,
        "index": {
            "historical_claims":len(catalog),
            "historical_original_sha_missing":sum(
                r["provenance_state"]=="HISTORIC_ORIGINAL_SHA_MISSING"
                for r in catalog),
            "candidate_queries_evaluated":len(queries),
            "all_atomic_queries_processed":complete,
            "historical_records_silently_dropped":False
        },
        "metrics": {
            "development_top10_recall":None,
            "independent_blind_recall":None,
            "independent_blind_precision":None,
            "human_gold_label_count":0
        },
        "automatic_knowledge_approval":False,
        "automatic_research_complete":False,
        "release":"BLOCKED_PENDING_REAL_SEMANTIC_REVIEW_AND_BLIND_GOLD"
    }

def private_export(path,root,data):
    """No private source or derived quotes enter GitHub or console output."""
    dest=Path(path).expanduser().resolve()
    base=Path(root).expanduser().resolve()
    guard(not dest.is_relative_to(base) and not dest.exists(),
          "V34_PRIVATE_OUTPUT_MUST_BE_NEW_AND_OUTSIDE_REPOSITORY")
    dest.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(str(dest),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as handle:
            json.dump(data,handle,ensure_ascii=False,indent=2,allow_nan=False)
    except Exception:
        dest.unlink(missing_ok=True)
        raise
    return {"private_output_created":True,
            "source_sha256":data["source"]["srt_sha256"],
            "proposed_claims":data["atomic"]["proposed_claim_count"],
            "unreviewed_frames":data["semantics"]["unreviewed_frames"],
            "historical_index_count":data["index"]["historical_claims"],
            "missing_historical_srt_sha":data["index"]["historical_original_sha_missing"],
            "relation_queries":data["index"]["candidate_queries_evaluated"],
            "all_queries_processed":data["index"]["all_atomic_queries_processed"],
            "independent_blind_recall":None, "release":data["release"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",default=".")
    p.add_argument("--historical-index-check",action="store_true")
    p.add_argument("--original-srt")
    p.add_argument("--original-sha256")
    p.add_argument("--video-id")
    p.add_argument("--video-number",type=int)
    p.add_argument("--private-output")
    p.add_argument("--query-limit",type=int,default=None)
    args=p.parse_args()
    rows=read_historical(args.root)
    if args.historical_index_check:
        index=historical_index(rows)
        print(json.dumps({"schema":"V34_HISTORICAL_INDEX_CENSUS_V1",
                          "indexed":len(index),
                          "original_sha_missing":sum(
                              r["source_srt_sha256"] is None for r in index),
                          "review_only":True,"release":"BLOCKED"},sort_keys=True))
        return
    guard(all((args.original_srt,args.original_sha256,args.video_id,
               args.video_number,args.private_output)),
          "V34_PRIVATE_ORIGINAL_AND_DEVELOPMENT_VIDEO_ARGUMENTS_REQUIRED")
    result=run_development(Path(args.original_srt).read_bytes(),
                           args.original_sha256,args.video_id,
                           args.video_number,rows,query_limit=args.query_limit)
    print(json.dumps(private_export(args.private_output,args.root,result),
                     sort_keys=True,ensure_ascii=False))

if __name__=="__main__":
    try:main()
    except (ValueError,TypeError,KeyError,OSError) as e:
        print(json.dumps({"gate":"FAIL","error":str(e)},ensure_ascii=False))
        raise SystemExit(1)
