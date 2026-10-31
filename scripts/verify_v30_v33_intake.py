#!/usr/bin/env python3
"""V3.3 real unexposed #261-264 intake guard, no synthetic substitution.

This is a source/reviewer availability check, NOT a model performance
evaluation. It refuses to invent TP/FP/FN/recall if private original SRT
and truly separate human gold are missing.
"""
import argparse
import json
from pathlib import Path
from v30_verified_core import policy_gate,guard
from v30_blind_recall_v33 import pending_real_unseen_gate

ROOT=Path(__file__).resolve().parents[1]

def check(root=ROOT):
    root=Path(root)
    policy_gate(root)
    manifest=json.loads((root/"v30/holdout/v33_261_264_unseen_intake_v1.json").read_text())
    guard(manifest["schema"]=="V33_261_264_REAL_UNSEEN_SOURCE_INTAKE_V1"
          and manifest["historic_training_boundary"].startswith("#1-260")
          and manifest["independence_verified_by_external_human"] is False,
          "V33_INTAKE_CANNOT_PREDECLARE_REAL_HUMAN_BLINDNESS")
    roster=(root/"data/subtitles/roster_20261007.csv").read_text(encoding="utf-8")
    items={}
    for line in roster.splitlines():
        parts=line.split(",",1)
        if len(parts)==2 and parts[0].isdigit():
            items[int(parts[0])]=parts[1].strip()
    plans=manifest["video_candidates"]
    guard(len(plans)==4 and
          [x["video_number"] for x in plans]==[261,262,263,264]
          and all(items.get(x["video_number"])==x["video_id"] for x in plans),
          "INCONSISTENT_NEXT_UNSEEN_VIDEO_ROSTER")
    historical=[(x["video_number"],
       (root/"data/analysis_events"/(x["video_id"]+".json")).exists())
       for x in plans]
    guard(not any(found for _,found in historical),
          "EXISTING_HISTORIC_ANALYSIS_WOULD_CONTAMINATE_UNSEEN_TEST")
    # Public CI never tries to obtain or enumerate private SRT from the
    # user's account; actual bytes must be safely supplied externally.
    source_count=sum(x["source_raw_bytes_present"] is True and
                     x["source_srt_sha256"] is not None
                     for x in plans)
    gold_count=manifest["external_blind_gold_commit_count"]
    reviewed=sum(x["semantic_review_independent_attestation"] is not None
                 for x in plans)
    pending=pending_real_unseen_gate({
        "target_video_numbers":[261,262,263,264],
        "original_srt_sha_verified":source_count,
        "independent_semantic_reviews":reviewed,
        "independent_blind_gold_committed":gold_count,
        "frozen_engine_predictions":manifest["engine_predictions_on_261_264"],
    })
    guard(pending["release_status"]==
          "BLOCKED_NO_AUTHENTICATED_REAL_UNSEEN_GOLD"
          and pending["measured_recall"] is None
          and source_count==0 and gold_count==0 and reviewed==0,
          "NO_MEASUREMENT_CAN_BE_CLAIMED_WITHOUT_NEW_ORIGINAL_GOLD")
    return {
        "schema":"V33_UNSEEN_SOURCE_AND_EXTERNAL_BLIND_READINESS_V1",
        "verified_public_roster_ids":{str(x["video_number"]):x["video_id"]
                                     for x in plans},
        "original_srt_bytes_verified_in_this_public_run":source_count,
        "prior_v3_261_264_analysis_files_found":sum(f for _,f in historical),
        "independent_semantic_reviewed_originals":reviewed,
        "external_blind_gold_signed":gold_count,
        "actual_recall":None,"actual_precision":None,
        "actual_source_truth_independently_verified":False,
        "preconditions":pending,
        "production_release":False,
        "main_or_historic_research_modified":False
    }
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--assert-snapshot",action="store_true")
    args=p.parse_args()
    try:
        out=check(args.root)
        if args.assert_snapshot:
            saved=args.root/"v30/holdout/v33_pre_eval_snapshot_v1.json"
            guard(saved.is_file() and
                  json.loads(saved.read_text(encoding="utf-8"))==out,
                  "BLIND_EVAL_INTAKE_BASELINE_MUST_NOT_BE_RETROACTIVELY_EDITED")
        print(json.dumps(out,ensure_ascii=False,sort_keys=True))
    except (ValueError,TypeError,KeyError,OSError) as e:
        print(json.dumps({"gate":"FAIL","error":str(e)},ensure_ascii=False))
        raise SystemExit(1)
