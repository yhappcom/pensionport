"""Source-lineage audit for the 20 historical core claims.

Legacy video ID presence is NEVER interpreted as SRT cue-level verification.
"""
from pathlib import Path
import json
import re
from .advisory_knowledge_gate import verify_core20,read_json,require

def audit(root):
    root=Path(root)
    verify_core20(root)
    data=read_json(root/"ire/v5/advisory_knowledge/core20_candidates_20261104.json")
    ids={vid for c in data["claims"] for vid in c["original_supporting_video_ids"]}
    registered={json.loads(s)["video_id"] for s in
                (root/"data/videos.jsonl").read_text("utf-8").splitlines() if s.strip()}
    overlays={match.group(1) for p in (root/"data/canonical_events").glob("*.json")
              if (match:=re.fullmatch(r"\d+_([A-Za-z0-9_-]{11})\.json",p.name))}
    studies={p.stem.removeprefix("video_") for p in
             (root/"data/analysis_events").glob("*.json")}
    source_catalog={row["video_id"] for p in
                    (root/"ire/v5/source_catalog").glob("*.json")
                    for row in read_json(p)["files"]}
    require(ids<=registered|overlays|studies,"CORE20_UNREGISTERED_VIDEO_REFERENCE")
    return {
      "schema":"IRE_V5_20_CLAIM_SOURCE_LINEAGE_AUDIT_V1",
      "legacy_claims":len(data["claims"]),
      "unique_supporting_video_ids":len(ids),
      "legacy_base_video_records":len(ids&registered),
      "canonical_overlay_video_records":len(ids&overlays),
      "v3_analysis_event_video_records":len(ids&studies),
      "indexed_srt_ids_in_current_catalog":len(ids&source_catalog),
      "original_cue_quote_verification_performed":False,
      "independent_original_srt_audits_completed":0,
      "independent_financial_fact_approvals":0,
      "release":"LINEAGE_ONLY_NO_FINANCIAL_ADVICE"}

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path("."))
    a=p.parse_args()
    print(json.dumps(audit(a.root),ensure_ascii=False,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
