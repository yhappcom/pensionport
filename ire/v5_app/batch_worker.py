"""Public GitHub Actions control plane for batches of 4-5 private videos.

Handles only SHA-256, claimed progress and next-source hints. Never handles
private SRT, encrypted backup keys, financial claims or official fact approval.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
from .worker import ControlError, check, positive_int, SHA256, VIDEO, ID, REQUEST_FILE, emit_state

SCHEMA = "IRE_V5_APP_FIVE_VIDEO_COMMAND_V1"
STATE_SCHEMA = "IRE_V5_APP_FIVE_VIDEO_PUBLIC_STATE_V1"
START_KEYS = {"schema", "job_id", "sequence", "operation", "videos"}
CHECKPOINT_KEYS = {"schema", "job_id", "sequence", "operation", "progress"}
SOURCE_KEYS = {"video_id", "source_cues", "source_sha256", "windows_total", "prior_git_blob_sha"}
PROGRESS_KEYS = {"video_id", "processed_windows", "claims", "evidence_reviews", "relation_reviews", "event_receipts", "event_chain_sha256"}
BLOB = re.compile(r"^[0-9a-f]{40}$")


def reduce_five_video_commands(commands: list[dict]) -> dict:
    check(type(commands) is list and len(commands) > 0, "FIVE_VIDEO_COMMANDS_MISSING")
    state = None
    for pos, command in enumerate(commands, 1):
        check(type(command) is dict and
              command.get("schema") == SCHEMA and
              type(command.get("job_id")) is str and
              ID.fullmatch(command["job_id"]) is not None and
              type(command.get("sequence")) is int and command["sequence"] == pos,
              "FIVE_VIDEO_COMMAND_HEADER_INVALID")
        if pos == 1:
            check(command.get("operation") == "OPEN" and
                  set(command) == START_KEYS and
                  type(command.get("videos")) is list and
                  4 <= len(command["videos"]) <= 5,
                  "FIVE_VIDEO_OPEN_INVALID")
            vids=[]
            for src in command["videos"]:
                check(type(src) is dict and set(src) == SOURCE_KEYS and
                      type(src["video_id"]) is str and
                      VIDEO.fullmatch(src["video_id"]) is not None and
                      src["video_id"] not in [r["video_id"] for r in vids] and
                      type(src["source_sha256"]) is str and
                      SHA256.fullmatch(src["source_sha256"]) is not None and
                      type(src["prior_git_blob_sha"]) is str and
                      BLOB.fullmatch(src["prior_git_blob_sha"]) is not None and
                      positive_int(src["source_cues"]) and src["source_cues"]>0 and
                      positive_int(src["windows_total"]) and 0 < src["windows_total"] <= src["source_cues"],
                      "FIVE_VIDEO_SOURCE_INVALID")
                vids.append({**src,"processed_windows_reported":0,
                             "claims_reported":0,"evidence_reviews_reported":0,
                             "relation_reviews_reported":0,"event_receipts_reported":0,
                             "event_chain_sha256_reported":None})
            state={"schema":STATE_SCHEMA,"job_id":command["job_id"],
                   "video_count":len(vids),"videos":vids,"last_sequence":1}
            continue
        check(command.get("operation") == "CHECKPOINT" and
              set(command) == CHECKPOINT_KEYS and
              command["job_id"] == state["job_id"] and
              type(command.get("progress")) is list and
              len(command["progress"]) == state["video_count"],
              "FIVE_VIDEO_CHECKPOINT_INVALID")
        indexed={r["video_id"]:r for r in state["videos"]}
        seen=set()
        for progress in command["progress"]:
            check(type(progress) is dict and set(progress) == PROGRESS_KEYS and
                  type(progress.get("video_id")) is str and
                  progress["video_id"] in indexed and progress["video_id"] not in seen,
                  "FIVE_VIDEO_CHECKPOINT_VIDEO_INVALID")
            vid=progress["video_id"]
            seen.add(vid)
            old=indexed[vid]
            for k,stored in (("processed_windows","processed_windows_reported"),
                             ("claims","claims_reported"),
                             ("evidence_reviews","evidence_reviews_reported"),
                             ("relation_reviews","relation_reviews_reported"),
                             ("event_receipts","event_receipts_reported")):
                check(positive_int(progress[k]) and progress[k]>=old[stored],
                      "FIVE_VIDEO_REPORTED_METRIC_REWIND")
            check(progress["processed_windows"]<=old["windows_total"] and
                  progress["evidence_reviews"]<=progress["claims"] and
                  progress["relation_reviews"]<=progress["claims"] and
                  progress["event_receipts"]>=int(progress["processed_windows"]>0) and
                  type(progress["event_chain_sha256"]) is str and
                  SHA256.fullmatch(progress["event_chain_sha256"]) is not None,
                  "FIVE_VIDEO_REPORTED_PROGRESS_INCONSISTENT")
            old.update({"processed_windows_reported":progress["processed_windows"],
                        "claims_reported":progress["claims"],
                        "evidence_reviews_reported":progress["evidence_reviews"],
                        "relation_reviews_reported":progress["relation_reviews"],
                        "event_receipts_reported":progress["event_receipts"],
                        "event_chain_sha256_reported":progress["event_chain_sha256"]})
        state["last_sequence"]=pos
    all_windows=sum(v["windows_total"] for v in state["videos"])
    processed=sum(v["processed_windows_reported"] for v in state["videos"])
    return {**state,
       "total_cues_reported":sum(v["source_cues"] for v in state["videos"]),
       "windows_total_reported":all_windows,"windows_processed_reported":processed,
       "windows_remaining_reported":all_windows-processed,
       "next_source_window_hints":[{"video_id":v["video_id"],
              "next_candidate_window": (f'W{v["processed_windows_reported"]+1:05d}'
                   if v["processed_windows_reported"]<v["windows_total"] else None)}
                   for v in state["videos"]],
       "action_required":"CHATGPT_PRIVATE_FIVE_VIDEO_SOURCE_ANALYSIS_OR_EVIDENCE_REVIEW",
       "claim_review_and_official_scope_independently_attested":False,
       "source_and_receipts_readable_by_github":False,
       "github_actions_executed_control_plane":True,
       "all_five_videos_research_complete":False,
       "single_chat_turn_five_video_research_proven":False,
       "financial_advice_approved":False,
       "public_state_verdict":"BATCH_CONTROL_READY_RESEARCH_UNVERIFIED"}


def load_batch_job(folder: Path) -> dict:
    check(folder.is_dir() and not folder.is_symlink() and
          ID.fullmatch(folder.name) is not None,"FIVE_VIDEO_JOB_DIR_INVALID")
    paths=sorted(folder.iterdir())
    check(bool(paths) and all(p.is_file() and not p.is_symlink() and
          REQUEST_FILE.fullmatch(p.name) is not None and
          p.stat().st_size <= 32000 for p in paths),
          "FIVE_VIDEO_JOB_FILES_INVALID")
    docs=[]
    for i,p in enumerate(paths,1):
        check(p.name==f"{i:06d}.json","FIVE_VIDEO_FILE_SEQUENCE_INVALID")
        docs.append(json.loads(p.read_text("utf-8")))
    return reduce_five_video_commands(docs)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--requests",required=True)
    p.add_argument("--states",required=True)
    args=p.parse_args()
    root=Path(args.requests);dest=Path(args.states)
    check(root.is_dir(),"FIVE_VIDEO_REQUEST_ROOT_MISSING")
    count=0
    for folder in sorted(root.iterdir()):
        state=load_batch_job(folder)
        emit_state(dest / (state["job_id"]+".json"),state)
        print(json.dumps({"job_id":state["job_id"],
               "source_videos":state["video_count"],
               "unprocessed_windows":state["windows_remaining_reported"],
               "financial_facts_approved":0},sort_keys=True))
        count+=1
    check(count>0,"FIVE_VIDEO_NO_JOBS")
    return 0

if __name__=="__main__":raise SystemExit(main())
