"""Unify legacy research, new source archives and V5 reviews using YouTube IDs.

This produces task routing ONLY. Event sequences are not video roster numbers.
No model inference, financial fact approval or automatic knowledge merging.
"""
from __future__ import annotations
import argparse
import json
import re
from collections import Counter
from pathlib import Path

VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}\Z")
ROW = re.compile(r"^\|\s*(\d+)\s*\|.*?\|\s*\x60([A-Za-z0-9_-]{11})\x60\s*\|.*?\|\s*(Long-form|Short)\s*\|")
EVENT_FILE = re.compile(r"\d+_([A-Za-z0-9_-]{11})\.json\Z")

class QueueError(ValueError):
    pass

def check(ok: bool, reason: str) -> None:
    if not ok: raise QueueError(reason)

def roster(root: Path) -> list[dict]:
    seen_ids,seen_no,out=set(),set(),[]
    for line in (root/"VIDEO_INVENTORY_2026-10-07.md").read_text("utf-8").splitlines():
        if not re.match(r"^\|\s*\d+\s*\|",line): continue
        m=ROW.search(line)
        check(m is not None,"ROSTER_ROW_PARSE_ERROR")
        n,vid,typ=int(m[1]),m[2],m[3]
        check(n not in seen_no and vid not in seen_ids,"DUPLICATE_ROSTER_ENTRY")
        seen_no.add(n);seen_ids.add(vid)
        out.append({"roster_no":n,"video_id":vid,"type":typ})
    check(bool(out),"EMPTY_ROSTER")
    return sorted(out,key=lambda x:x["roster_no"])

def existing_research(root: Path) -> tuple[set[str],dict[str,set[str]]]:
    ids=set()
    for line in (root/"data/videos.jsonl").read_text("utf-8").splitlines():
        if line.strip():
            vid=json.loads(line).get("video_id")
            check(type(vid) is str and VIDEO_ID.fullmatch(vid) is not None,
                  "INVALID_LEGACY_VIDEO_ID")
            ids.add(vid)
    for file in (root/"data/canonical_events").glob("*.json"):
        m=EVENT_FILE.fullmatch(file.name)
        if m is not None:
            obj=json.loads(file.read_text("utf-8"))
            check(obj.get("video_id")==m[1],"EVENT_FILE_ID_MISMATCH")
            ids.add(m[1])
    # V3 single-file research events are a separate lane from canonical
    # sequence events. Presence means there is a record to audit, NOT
    # that the transcript was completely or independently verified.
    for file in (root/"data/analysis_events").glob("*.json"):
        obj=json.loads(file.read_text("utf-8"))
        vid=obj.get("video_id")
        check(type(vid) is str and VIDEO_ID.fullmatch(vid) is not None,
              "ANALYSIS_EVENT_VIDEO_ID_INVALID")
        if file.stem.startswith("video_"):
            check(file.stem[6:]==vid,"ANALYSIS_EVENT_FILE_ID_MISMATCH")
        else:
            check(file.stem==vid,"ANALYSIS_EVENT_FILE_ID_MISMATCH")
        ids.add(vid)
    backlinks={}
    for line in (root/"data/claims.jsonl").read_text("utf-8").splitlines():
        if line.strip():
            claim=json.loads(line)
            check(type(claim.get("claim_id")) is str,"LEGACY_CLAIM_ID_INVALID")
            for vid in claim.get("supporting_videos",[]):
                backlinks.setdefault(vid,set()).add(claim["claim_id"])
    return ids,backlinks

def indexed_sources(root: Path) -> dict[str,dict]:
    result={}
    for file in sorted((root/"ire/v5/source_catalog").glob("*.json")):
        obj=json.loads(file.read_text("utf-8"))
        check(obj.get("schema")=="IRE_V5_SRT_CORPUS_CENSUS_V1",
              "SOURCE_CATALOG_SCHEMA_INVALID")
        for row in obj["files"]:
            vid=row["video_id"]
            check(VIDEO_ID.fullmatch(vid) is not None and
                  type(row["cue_count"]) is int and row["cue_count"]>0,
                  "BAD_CATALOG_SOURCE_ROW")
            if vid in result:
                check(result[vid]["source_sha256"]==row["source_sha256"],
                      "CONFLICTING_SOURCE_FOR_VIDEO_ID")
            else: result[vid]=row
    return result

def provisional_reviews(root: Path) -> dict[str,dict]:
    result={}
    for file in sorted((root/"ire/v5/reviews").glob("*.json")):
        obj=json.loads(file.read_text("utf-8"))
        vid=obj.get("video_id")
        check(type(vid) is str and VIDEO_ID.fullmatch(vid) is not None,
              "REVIEW_VIDEO_ID_INVALID")
        check(vid not in result,"DUPLICATE_VIDEO_REVIEW")
        check(obj.get("investment_advice_approved") is False and
              obj.get("financial_facts_independently_approved")==0,
              "REVIEW_UNSUPPORTED_PROMOTION")
        result[vid]=obj
    return result

def build(root: Path) -> dict:
    listing=roster(root)
    legacy,backlinks=existing_research(root)
    sources=indexed_sources(root)
    reviews=provisional_reviews(root)
    known={item["video_id"] for item in listing}
    check(set(sources)<=known,"SOURCE_NOT_IN_FIXED_ROSTER")
    check(set(reviews)<=known,"REVIEW_NOT_IN_FIXED_ROSTER")
    work=[]
    for item in listing:
        vid,typ=item["video_id"],item["type"]
        old=vid in legacy
        source=vid in sources
        new_review=vid in reviews
        if typ=="Short": kind="SHORTS_INVENTORY"
        elif new_review: kind="REVIEW_EVIDENCE_AND_KNOWLEDGE_RECONCILIATION"
        elif old and source: kind="RECONCILE_ORIGINAL_WITH_LEGACY"
        elif old: kind="AUDIT_EXISTING_RESEARCH_AND_SOURCE_PROVENANCE"
        elif source: kind="ANALYZE_NEW_SOURCE_THEN_RECONCILE"
        else: kind="SOURCE_NOT_CATALOGED_HERE"
        work.append({**item,"work_class":kind,
                     "legacy_record_present":old,
                     "legacy_claim_backlinks":len(backlinks.get(vid,set())),
                     "srt_in_indexed_catalog":source,
                     "provisional_v5_review_present":new_review,
                     "reanalysis_required_by_default":False if old else source,
                     "finance_facts_independently_approved_here":0,
                     "advisory_eligible":False})
    return {"schema":"IRE_V5_CONTINUOUS_RESEARCH_ROUTER_V1",
            "scope_note":"One row per roster ID. Canonical sequence and event number are distinct.",
            "research_completed_videos_not_inferred":True,
            "independent_financial_approval_not_inferred":True,
            "legacy_video_id_references_total":len(legacy),
            "legacy_video_id_references_in_roster":sum(x["legacy_record_present"] for x in work),
            "indexed_raw_srt_videos":len(sources),
            "provisional_v5_review_videos":len(reviews),
            "work_class_counts":dict(sorted(Counter(x["work_class"] for x in work).items())),
            "items":work}

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    res=build(args.root)
    body=json.dumps(res,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(body,encoding="utf-8")
    print(json.dumps({key:res[key] for key in
        ("schema","legacy_video_id_references_in_roster",
         "indexed_raw_srt_videos","provisional_v5_review_videos",
         "work_class_counts")},ensure_ascii=False,sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())
