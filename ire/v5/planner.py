"""Source-only V5 adaptive batching plan; no semantic claims or model API.

Windows are receipt-addressable, sentence/pause conscious and cover every cue
exactly once. These boundaries cannot certify claim meaning; ChatGPT must review
forced continuation and adjacent context before describing financial conditions.
"""
from __future__ import annotations
import re
from .engine import cues_from_srt, sha256, require

VERSION = "IRE_V5_FIVE_VIDEO_SOURCE_PLANNER_20261104_A"
END = re.compile(r"(?:[.!?。]|(?:입니다|습니다|합니다|됩니다|네요|세요|어요|아요|겠죠|거죠|습니까))\s*$")


def prepare_full_video_manifest(source: bytes, video_id: str,
                                prior_baseline_git_blob_sha: str,
                                *, min_cues: int=6, max_cues: int=18,
                                max_chars: int=1600, pause_ms: int=2500) -> dict:
    require(type(source) is bytes and type(video_id) is str and
            type(min_cues) is int and type(max_cues) is int and
            type(max_chars) is int and type(pause_ms) is int and
            2 <= min_cues <= max_cues <= 30 and
            300 <= max_chars <= 5000 and 0 <= pause_ms <= 10000,
            "V5_SOURCE_PLANNER_CONFIGURATION_INVALID")
    cues = cues_from_srt(source)
    groups: list[list[int]] = []
    forced = set()
    current: list[int] = []
    chars = 0
    def flush():
        nonlocal current, chars
        if current:
            groups.append(current)
        current=[]
        chars=0

    for cid,cue in cues.items():
        require(len(cue.text) <= max_chars, "V5_SOURCE_SINGLE_CUE_TOO_LONG")
        if current:
            prev=cues[current[-1]]
            if len(current)>=max_cues or chars+1+len(cue.text)>max_chars:
                if not END.search(prev.text):
                    forced.add(len(groups))
                flush()
            elif (len(current)>=min_cues and
                  max(0,cue.start_ms-prev.end_ms)>=pause_ms and
                  END.search(prev.text)):
                flush()
        current.append(cid)
        chars+=len(cue.text)+1
    flush()
    windows=[]
    for i,group in enumerate(groups,1):
        text=" ".join(cues[c].text for c in group)
        windows.append({"window_id":f"W{i:05d}","primary_cue_ids":group,
                        "primary_text_sha256":sha256(text.encode("utf-8")),
                        "continuation_boundary_review_required":i-1 in forced})
    all_cue_ids=[cue for w in windows for cue in w["primary_cue_ids"]]
    require(all_cue_ids==list(cues),"V5_PLANNER_CUE_OWNERSHIP_GAP")
    return {"schema":"IRE_V5_SOURCE_PLAN_V1","video_id":video_id,
            "source_sha256":sha256(source),"source_cues":len(cues),
            "planner_version":VERSION,
            "prior_baseline_git_blob_sha":prior_baseline_git_blob_sha,
            "active_window_ids":[w["window_id"] for w in windows],
            "windows":windows}
