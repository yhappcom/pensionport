"""V4 Chat-authored draft to V3 adaptive checkpoints; NO model API and NO fact approval."""
from __future__ import annotations
import argparse
import json
from typing import Any
from .chat_bridge import ConversationResearchSession
from .semantics import verify_window_before_caching
from .source import require,sha256
from .v3_adaptive import PLANNER_VERSION
from .v3_semantic_audit import window_semantic_audit
from .cli import private_file

SCHEMA="IRE_V4_P0_ADAPTIVE_PROVISIONAL_V1"
ACCEPT_SCHEMA="IRE_V4_P0_V3_INTAKE_RECEIPT_V1"

def _canon(item: Any) -> bytes:
    return json.dumps(item,sort_keys=True,ensure_ascii=False,
                      separators=(",",":"),allow_nan=False).encode("utf-8")

def make_answer(session: ConversationResearchSession, row: dict) -> dict:
    """Translate Chat-model authored draft and strictly replay real V3 validators."""
    require(type(row) is dict and set(row)>={
        "window_id","first_cue","last_cue","primary_count","primary_source_hash",
        "forced_continuation_review","claims","cue_dispositions"},
        "V4_DRAFT_REQUIRED_FIELDS_MISSING")
    wid=row["window_id"]
    require(type(wid) is str,"V4_WINDOW_ID_BAD")
    packet=session.packet(wid)
    w=session._window(wid)
    ids=w["source_cue_ids"]
    require((row["first_cue"],row["last_cue"],row["primary_count"])==
            (ids[0],ids[-1],len(ids)),"V4_WINDOW_PLAN_DRIFT")
    require(row["primary_source_hash"]==w["source_text_sha256"] and
            row["forced_continuation_review"]==
            w["continuation_boundary_review_required"],
            "V4_WINDOW_HASH_OR_CONTINUATION_DRIFT")
    claims=[];links={i:set() for i in ids};seen=set()
    for c in row["claims"]:
        require(type(c) is dict and set(c)=={
            "claim_id","proposition","claim_types","frame","source_refs","annotation_status"},
            "V4_DRAFT_CLAIM_SCHEMA_INVALID")
        cid=c["claim_id"]
        require(type(cid) is str and cid not in seen and
                c["annotation_status"]=="UNREVIEWED",
                "V4_DRAFT_DUPLICATE_OR_PREAPPROVED_CLAIM")
        seen.add(cid)
        for ref in c["source_refs"]:
            index=ref["cue_index"]
            require(index in links,"V4_HALO_OR_WRONG_WINDOW_SOURCE")
            links[index].add(cid)
        claims.append({k:c[k] for k in
                      ("proposition","claim_types","frame","source_refs")})
    require(len(row["cue_dispositions"])==len(ids),"V4_CUE_CENSUS_GAP")
    dispositions=[]
    for expected,dis in zip(ids,row["cue_dispositions"]):
        require(type(dis) is dict and set(dis)=={
            "cue_index","status","claim_ids","reason"} and
            dis["cue_index"]==expected and
            set(dis["claim_ids"])==links[expected],
            "V4_REVERSE_CLAIM_LINK_OR_CUE_ORDER_BAD")
        dispositions.append({k:dis[k] for k in
                            ("cue_index","status","reason")})
    answer={"claims":claims,"cue_dispositions":dispositions}
    verify_window_before_caching(session.original,session.digest,w,answer)
    audit=window_semantic_audit(packet,answer)
    require(not audit["critical"],"V4_V3_SEMANTIC_CRITICAL_REVIEW_REQUIRED")
    return {"window_id":wid,"answer":answer,
            "packet_sha256":packet["packet_sha256"],
            "answer_sha256":sha256(_canon(answer)),
            "v3_warning_count":len(audit["warnings"])}

def accept_private_draft(raw: bytes, video_id: str, draft: dict,
                         private_root: str, *, perform_accept:bool=False) -> dict:
    """All source-linked claims are preflighted before any immutable V3 answer write."""
    require(type(draft) is dict and draft.get("schema")==SCHEMA,"V4_DRAFT_SCHEMA_WRONG")
    require(draft.get("original_sha256")==sha256(raw),"V4_SOURCE_SHA_MISMATCH")
    require(draft.get("planner_version")==PLANNER_VERSION,
            "V4_ADAPTIVE_PLANNER_VERSION_CHANGED")
    session=ConversationResearchSession(raw,video_id,sha256(raw),
              private_root,window_strategy="V3_ADAPTIVE")
    require(draft.get("cue_count")==len(session.cues),
            "V4_SOURCE_CUE_COUNT_CHANGED")
    windows=draft.get("windows")
    require(type(windows) is list and bool(windows),
            "V4_NO_SOURCE_DRAFT_WINDOWS")
    compiled=[];global_claims=set();window_ids=set()
    for row in windows:
        wid=row["window_id"]
        require(wid not in window_ids,"V4_DUPLICATE_WINDOW_IN_DRAFT")
        window_ids.add(wid)
        for c in row["claims"]:
            require(c["claim_id"] not in global_claims,
                    "V4_DUPLICATE_GLOBAL_CLAIM_ID")
            global_claims.add(c["claim_id"])
        compiled.append(make_answer(session,row))
    accepted=0;skipped=0
    if perform_accept:
        for row in compiled:
            old=session._answer_original(row["window_id"])
            if old is not None:
                require(sha256(_canon(old))==row["answer_sha256"],
                        "V4_V3_CHECKPOINT_CONFLICT")
                skipped+=1
                continue
            session.accept({"schema":"IRE_CHAT_WINDOW_ANSWER_V1",
                "session_id":session.session_id,
                "window_id":row["window_id"],
                "packet_sha256":row["packet_sha256"],**row["answer"]})
            accepted+=1
    state=session.status()
    return {"schema":ACCEPT_SCHEMA,"video_id":video_id,
        "source_sha256":session.digest,"planner_version":PLANNER_VERSION,
        "session_id":session.session_id,"source_cues":len(session.cues),
        "total_source_windows":len(session.windows),
        "source_bound_provisional_draft_windows":len(compiled),
        "draft_claims":len(global_claims),
        "v3_semantic_warning_count":sum(x["v3_warning_count"] for x in compiled),
        "v3_accepted_now":accepted,"idempotent_existing":skipped,
        "total_v3_accepted":state["accepted_windows"],
        "remaining_v3_windows":state["remaining_windows"],
        "formal_v3_accept_performed":perform_accept,
        "financial_truth_approved":False,"independent_semantic_gold":False,
        "research_complete":False,"release":"BLOCKED_NOT_FULL_RESEARCH"}

def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--private-source-srt",required=True)
    parser.add_argument("--private-draft-json",required=True)
    parser.add_argument("--private-session-root",required=True)
    parser.add_argument("--video-id",required=True)
    parser.add_argument("--accept",action="store_true")
    opts=parser.parse_args()
    try:
        raw=private_file(opts.private_source_srt).read_bytes()
        draft=json.loads(private_file(opts.private_draft_json).read_text("utf-8"))
        result=accept_private_draft(raw,opts.video_id,draft,
                                   opts.private_session_root,perform_accept=opts.accept)
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        return 0
    except (ValueError,KeyError,TypeError,UnicodeError,OSError):
        print(json.dumps({"schema":ACCEPT_SCHEMA,"status":"FAILED_CLOSED"}))
        return 2
if __name__=="__main__":
    raise SystemExit(main())
