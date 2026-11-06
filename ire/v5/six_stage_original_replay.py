"""Ten-video source replay and conservative cross-validation intake gate.

With --source-zip, re-open all 10 original SRT byte streams, validate each
member's hash and exact V5 planner window rollup, and replay #1-5 against
historical 288 published window boundaries. Without it GitHub CI validates
only pinned metadata: never pretend it has private source bytes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

from .first_five_window_review_gate import source_windows

MANIFEST=Path("ire/v5/validation/first_ten_original_crossvalidation_20261106.json")
ORIGINAL_SHA="088869c583b2d3ed93d68e4dd5348b1f506877ea2bdc1d66466c199ec80e7716"
OLD_ARCHIVE_SHA="00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd"
IDS=("sz5N9WJS310","6VEfKF7BzZU","OiDTNstaSpM","aNfGrcO6WPI","qtluAViPpsQ",
     "3MyhYE2jmuE","4CQ4FjGT2gA","OfkY343OaNs","YNOSY15ppf8","VKr060rIirM")
CUES=(1195,1347,785,758,1044,807,10728,1039,1277,34)
WINDOWS=(67,76,44,43,58,45,596,59,71,2)
KNOWN_STATUS={"CORRECTION_REQUIRED_NOT_APPROVED","SCOPE_OPEN_NOT_APPROVED",
  "HYPOTHESIS_ONLY","COMPILATION_DEDUP_REQUIRED","CONDITIONAL_STRATEGY",
  "GENERAL_COST_EDUCATION","OVERGENERALIZATION_QUARANTINED"}

class SixStageSourceError(ValueError): pass

def require(ok,label):
    if not ok: raise SixStageSourceError(label)

def digest(data:bytes):
    return hashlib.sha256(data).hexdigest()

def window_rollup(windows:list[dict]):
    packed="".join(w["window_id"]+":"+w["primary_text_sha256"]+"\n"
                   for w in windows)
    return digest(packed.encode())

def read(root:Path):
    return json.loads((root/MANIFEST).read_text(encoding="utf-8"))

def audit(root:Path,source_zip:Path|None=None,replacement:dict|None=None):
    root=Path(root)
    d=read(root) if replacement is None else replacement
    archive=d.get("source_archive",{})
    require(d.get("schema")=="IRE_V5_FIRST_TEN_ORIGINAL_INTAKE_AND_CROSSVALIDATION_V1"
            and d.get("as_of")=="2026-11-06"
            and archive.get("name")=="1-100.zip"
            and archive.get("sha256")==ORIGINAL_SHA
            and archive.get("historical_1_70_zip_sha256")==OLD_ARCHIVE_SHA
            and archive.get("same_archive_as_historical") is False
            and archive.get("raw_srt_text_uploaded_to_github") is False,
            "SIX_STAGE_FALSE_ARCHIVE_IDENTITY")
    require(d.get("first_five_original_cues")==5129
            and d.get("first_five_source_windows")==288
            and d.get("next_five_original_cues")==13885
            and d.get("next_five_source_windows")==773
            and d.get("archive_files_hash_replayed_in_chat_host") is True
            and d.get("archive_files_hash_replayed_in_github_ci") is False
            and d.get("all_5_video_financial_claims_formally_approved") is False
            and d.get("extra_five_blind_holdout_qualified") is False
            and d.get("composite_video_7_must_be_deduplicated") is True
            and d.get("formal_master_116_modified") is False
            and d.get("existing_p4_29_education_nodes_modified") is False
            and d.get("original_audio_validation_completed") is False
            and d.get("independent_atomic_claim_recall_certified") is False
            and d.get("scope_release")==
                "SOURCE_REPLAY_AND_14_RISK_CHALLENGES_ONLY_NOT_FULL_773_WINDOW_CLAIM_RESEARCH",
            "SIX_STAGE_FALSE_RESEARCH_RELEASE")
    rows=d.get("video_records")
    require(type(rows) is list and len(rows)==10,"SIX_STAGE_MISSING_VIDEO")
    for i,(v,vid,cues,windows) in enumerate(zip(rows,IDS,CUES,WINDOWS),1):
        require(v.get("sequence")==i and v.get("video_id")==vid
                and v.get("cues")==cues and v.get("windows")==windows
                and v.get("source_bytes",0)>0
                and v.get("original_archive_member")==
                    f"1-100/youtube-transcript-{vid}.srt"
                and re.fullmatch("[0-9a-f]{64}",str(v.get("source_sha256","")))
                and re.fullmatch("[0-9a-f]{64}",
                                 str(v.get("window_hash_rollup_sha256","")))
                and v.get("formal_financial_claim_approved") is False,
                "SIX_STAGE_INVALID_VIDEO_SOURCE_METADATA")
    challenges=d.get("risk_challenges")
    official=d.get("official_references",{})
    require(type(challenges) is list and len(challenges)==14
            and len({x.get("case_id") for x in challenges})==14
            and isinstance(official,dict) and len(official)>=5,
            "SIX_STAGE_CROSSVIDEO_CHALLENGES_INCOMPLETE")
    for c in challenges:
        n=c.get("video_no")
        span=c.get("cues")
        require(type(n) is int and 6<=n<=10
                and type(span) is list and len(span)==2
                and type(span[0]) is int and type(span[1]) is int
                and 1<=span[0]<=span[1]<=CUES[n-1]
                and c.get("status") in KNOWN_STATUS
                and len(c.get("claim",""))>=12
                and len(c.get("resolution",""))>=24
                and (c.get("reference") in official
                     if c.get("reference") is not None else True),
                "SIX_STAGE_RISK_SOURCE_UNANCHORED")
        if n==7:
            require(c["status"]=="COMPILATION_DEDUP_REQUIRED",
                    "SIX_STAGE_COMPILATION_FAKE_INDEPENDENCE")
    q=d.get("quality_levels",{})
    require(q.get("source_identity")=="CHAT_HOST_VERIFIED"
            and q.get("window_replay")=="CHAT_HOST_VERIFIED"
            and q.get("first_five_atomic_claim_complete")=="NOT_PROVEN"
            and q.get("next_five_atomic_claim_complete")=="NOT_PROVEN"
            and q.get("new_p4_nodes_from_extra_five")==0
            and q.get("formal_v5_engine_receipts_from_extra_five")==0,
            "SIX_STAGE_PREMATURE_GRAPH_PROMOTION")

    # The committed source contract is verifiable even when CI cannot access
    # the user's private ZIP. Explicit source-zip mode is independently fail
    # closed on the exact published 1-100 archive and all original members.
    source_replayed=False
    if source_zip is not None:
        src=Path(source_zip)
        require(src.is_file(),"SIX_STAGE_SOURCE_ZIP_MISSING")
        require(digest(src.read_bytes())==ORIGINAL_SHA,
                "SIX_STAGE_SOURCE_ZIP_SHA_MISMATCH")
        with zipfile.ZipFile(src) as z:
            for n,row in enumerate(rows,1):
                candidates=[name for name in z.namelist()
                    if name==row["original_archive_member"]]
                require(len(candidates)==1,
                        "SIX_STAGE_SOURCE_MEMBER_MISSING_OR_DUPLICATE")
                raw=z.read(candidates[0])
                require(len(raw)==row["source_bytes"]
                        and digest(raw)==row["source_sha256"],
                        "SIX_STAGE_SOURCE_SRT_SHA_MISMATCH")
                windows=source_windows(raw)
                require(len(windows)==row["windows"] and
                        window_rollup(windows)==row["window_hash_rollup_sha256"],
                        "SIX_STAGE_SOURCE_WINDOW_ROLLUP_CHANGED")
                if n<=5:
                    prior=root/("ire/v5/validation/v5_first_five_video_"
                        f"{n:02d}_window_review_20261106.json")
                    record=json.loads(prior.read_text("utf-8"))
                    existing=record["records"]
                    require(len(existing)==len(windows) and all(
                        all(v[k]==x[k] for k,v in w.items())
                        for w,x in zip(windows,existing)),
                        "SIX_STAGE_FIRST_FIVE_FROZEN_WINDOW_MISMATCH")
        source_replayed=True
    return {
      "schema":"IRE_V5_SIX_STAGE_FIRST_TEN_SOURCE_AND_CROSSVIDEO_GATE_V1",
      "first_five_original_source_windows":288,
      "first_five_original_cues":5129,
      "new_five_original_source_windows":773,
      "new_five_original_cues":13885,
      "original_srt_archives_replayed_in_current_process":source_replayed,
      "verified_replayed_source_member_count":10 if source_replayed else 0,
      "total_source_cues":19014,
      "source_anchored_crossvideo_risk_challenges":14,
      "compilation_video7_not_independent":True,
      "new_formal_financial_fact_certifications":0,
      "new_active_p4_nodes":0,
      "personalized_advice_authorized":False,
      "full_5_video_atomic_recall_proven":False,
      "extra_5_video_atomic_recall_proven":False,
      "release":"SOURCE_CENSUS_AND_QUARANTINED_RISK_CHALLENGES_ONLY",
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--source-zip",type=Path)
    args=p.parse_args()
    print(json.dumps(audit(args.root,source_zip=args.source_zip),
                     ensure_ascii=False,sort_keys=True))

if __name__=="__main__":main()
