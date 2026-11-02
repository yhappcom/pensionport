"""Compact ChatGPT no-API answer exchange, losslessly expanded before V3 checks.

An explicit cue-run is required for every source cue. Nothing is classified
implicitly: status and reason are repeated by the deterministic runtime, not
invented by it. Claim quotations are either literal strings or exact slices
of an unchanged primary cue. The previous V1 store/checkpoint is unchanged.
"""
from __future__ import annotations

import json

from .source import require, sha256
from .semantics import verify_window_before_caching

COMPACT_SCHEMA = "IRE_V3_ONE_TURN_COMPACT_ANSWERS_V1"
FULL_SCHEMA = "IRE_V3_ONE_TURN_ANSWERS_V1"
STATUS_CODES = {"L": "LINKED", "N": "NONCLAIM_CANDIDATE", "U": "UNRESOLVED"}
INVERSE_CODES = {v: k for k, v in STATUS_CODES.items()}
MAX_ANSWERS = 10000
MAX_REASONS = 50000


def _json_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sessions(queue):
    require(type(getattr(queue, "sessions", None)) is list and
            type(getattr(queue, "plan", None)) is dict,
            "V3_COMPACT_QUEUE_REQUIRED")
    src={s.video_id:s for s in queue.sessions}
    require(len(src)==len(queue.sessions), "V3_COMPACT_SOURCE_DUPLICATED")
    return src


def _source_ref_compact(ref, primary):
    idx=ref["cue_index"]
    original=primary[idx]["text"]
    quote=ref["quote"]
    if quote==original:
        return idx
    start=original.find(quote)
    if start>=0:
        return [idx, start, start+len(quote)]
    # Legacy exact quoted text may match only normalized SRT. Preserve it
    # literally and let the original verifier decide whether it is valid.
    return [idx, quote]


def _expand_reference(ref, primary):
    if type(ref) is int:
        require(ref in primary, "V3_COMPACT_CLAIM_QUOTE_OUTSIDE_PRIMARY")
        return {"cue_index":ref,"quote":primary[ref]["text"]}
    require(type(ref) is list and len(ref) in (2,3) and
            type(ref[0]) is int and ref[0] in primary,
            "V3_COMPACT_CLAIM_QUOTE_REFERENCE_INVALID")
    idx=ref[0]
    if len(ref)==2:
        require(type(ref[1]) is str and 0<len(ref[1])<=2000,
                "V3_COMPACT_QUOTE_TEXT_INVALID")
        return {"cue_index":idx,"quote":ref[1]}
    start,end=ref[1:]
    original=primary[idx]["text"]
    require(type(start) is int and type(end) is int and
            0 <= start < end <= len(original) and end-start <=2000,
            "V3_COMPACT_CLAIM_QUOTE_OFFSET_INVALID")
    return {"cue_index":idx,"quote":original[start:end]}


def expand_compact_bundle(queue, compact):
    """Create exact legacy V1 answers from a source-bound concise bundle.

    Bad later window = failure of the entire expansion before any checkpoint
    is written by the caller. The original validator also runs after expansion.
    """
    require(type(compact) is dict and set(compact)=={
        "schema", "batch_fingerprint", "reasons", "answers"
    } and compact["schema"]==COMPACT_SCHEMA and
            compact["batch_fingerprint"]==queue.plan["batch_fingerprint"],
            "V3_COMPACT_BUNDLE_OR_ORIGINAL_MISMATCH")
    reasons=compact["reasons"]
    records=compact["answers"]
    require(type(reasons) is list and len(reasons)<=MAX_REASONS and
            all(type(v) is str and 0<len(v)<=512 for v in reasons) and
            len(reasons)==len(set(reasons)) and
            type(records) is list and len(records)<=MAX_ANSWERS,
            "V3_COMPACT_REASONS_OR_COUNT_INVALID")
    sessions=_sessions(queue)
    inflated=[]
    seen=set()
    for row in records:
        require(type(row) is dict and set(row)=={
            "video_id", "window_id", "packet_sha256", "claims", "cue_runs"
        }, "V3_COMPACT_ANSWER_ROW_INVALID")
        vid,wid=row["video_id"],row["window_id"]
        require(type(vid) is str and vid in sessions and
                type(wid) is str and (vid,wid) not in seen,
                "V3_COMPACT_ANSWER_DUPLICATE_OR_VIDEO_INVALID")
        seen.add((vid,wid))
        session=sessions[vid]
        packet=session.packet(wid)
        require(row["packet_sha256"]==packet["packet_sha256"],
                "V3_COMPACT_STALE_ORIGINAL_PACKET")
        original=packet["primary_cues"]
        primary={c["cue_index"]:c for c in original}
        primary_ids=[c["cue_index"] for c in original]
        require(type(row["claims"]) is list and
                len(row["claims"])<=1000 and
                type(row["cue_runs"]) is list and
                1<=len(row["cue_runs"])<=len(primary_ids),
                "V3_COMPACT_RUNS_OR_CLAIMS_INVALID")
        claims=[]
        for claim in row["claims"]:
            require(type(claim) is dict and set(claim)=={
                "proposition","claim_types","frame","source_refs"
            } and type(claim["source_refs"]) is list and
                    1<=len(claim["source_refs"])<=80,
                    "V3_COMPACT_CLAIM_SCHEMA_INVALID")
            claims.append({**claim,"source_refs":[
                _expand_reference(ref,primary) for ref in claim["source_refs"]]})
        dispositions=[]
        for run in row["cue_runs"]:
            require(type(run) is list and len(run)==4,
                    "V3_COMPACT_CUE_RUN_SCHEMA_INVALID")
            first,last,code,reason_id=run
            require(type(first) is int and type(last) is int and
                    type(code) is str and code in STATUS_CODES and
                    type(reason_id) is int and -1<=reason_id<len(reasons) and
                    first<=last,
                    "V3_COMPACT_CUE_RUN_INVALID")
            # The span is indexed by actual cue IDs, not by array positions.
            # It must not skip source IDs or silently inherit a default.
            idx=len(dispositions)
            expected=primary_ids[idx:idx+(last-first+1)]
            require(expected and expected==list(range(first,last+1)),
                    "V3_COMPACT_CUE_RUN_SKIP_OVERLAP_OR_OUT_OF_ORDER")
            reason=None if reason_id==-1 else reasons[reason_id]
            require((code=="L" and reason is None) or
                    (code=="N" and reason is not None) or
                    code=="U",
                    "V3_COMPACT_CUE_RUN_REASON_INVALID")
            dispositions.extend({"cue_index":i,"status":STATUS_CODES[code],
                                 "reason":reason} for i in expected)
        require(len(dispositions)==len(primary_ids),
                "V3_COMPACT_PRIMARY_CUE_NOT_ALL_CLASSIFIED")
        body={"claims":claims,"cue_dispositions":dispositions}
        # Same exact existing invariant checker as V1 / original checkpoints.
        verify_window_before_caching(session.original,session.digest,
                                     session._window(wid),body)
        inflated.append({"video_id":vid,"submission":{
            "schema":"IRE_CHAT_WINDOW_ANSWER_V1",
            "session_id":packet["session_id"],
            "window_id":wid,"packet_sha256":packet["packet_sha256"],
            **body}})
    return {"schema":FULL_SCHEMA,
            "batch_fingerprint":compact["batch_fingerprint"],
            "answers":inflated}


def compact_full_bundle(queue, full):
    """Losslessly encode validated V1 answers for measurement and reuse."""
    require(type(full) is dict and set(full)=={
        "schema","batch_fingerprint","answers"
    } and full["schema"]==FULL_SCHEMA and
            full["batch_fingerprint"]==queue.plan["batch_fingerprint"] and
            type(full["answers"]) is list and
            len(full["answers"])<=MAX_ANSWERS,
            "V3_COMPACT_FULL_BUNDLE_INVALID")
    sessions=_sessions(queue)
    reasons=[]
    reasons_seen={}
    result=[]
    seen=set()
    for row in full["answers"]:
        require(type(row) is dict and set(row)=={
            "video_id","submission"},"V3_COMPACT_FULL_ROW_INVALID")
        vid=row["video_id"]
        require(type(vid) is str and vid in sessions and
                type(row["submission"]) is dict,
                "V3_COMPACT_FULL_VIDEO_INVALID")
        a=row["submission"]
        require(set(a)=={
            "schema","session_id","window_id","packet_sha256",
            "claims","cue_dispositions"} and
                a["schema"]=="IRE_CHAT_WINDOW_ANSWER_V1",
                "V3_COMPACT_FULL_ANSWER_SCHEMA_INVALID")
        session=sessions[vid]
        pkt=session.packet(a["window_id"])
        require((vid,a["window_id"]) not in seen and
                a["packet_sha256"]==pkt["packet_sha256"] and
                a["session_id"]==pkt["session_id"],
                "V3_COMPACT_FULL_STALE_OR_DUPLICATED")
        seen.add((vid,a["window_id"]))
        body={"claims":a["claims"],"cue_dispositions":a["cue_dispositions"]}
        verify_window_before_caching(session.original,session.digest,
                                     session._window(a["window_id"]),body)
        primary={c["cue_index"]:c for c in pkt["primary_cues"]}
        claims=[{**claim,"source_refs":[
            _source_ref_compact(ref,primary) for ref in claim["source_refs"]]}
            for claim in a["claims"]]
        runs=[]
        for disp in a["cue_dispositions"]:
            reason=disp["reason"]
            if reason is not None and reason not in reasons_seen:
                reasons_seen[reason]=len(reasons)
                reasons.append(reason)
            rid=-1 if reason is None else reasons_seen[reason]
            code=INVERSE_CODES[disp["status"]]
            idx=disp["cue_index"]
            if (runs and runs[-1][1]==idx-1 and
                    runs[-1][2:]==[code,rid]):
                runs[-1][1]=idx
            else:
                runs.append([idx,idx,code,rid])
        result.append({"video_id":vid,"window_id":a["window_id"],
                       "packet_sha256":a["packet_sha256"],
                       "claims":claims,"cue_runs":runs})
    compact={"schema":COMPACT_SCHEMA,
             "batch_fingerprint":full["batch_fingerprint"],
             "reasons":reasons,"answers":result}
    require(expand_compact_bundle(queue,compact)==full,
            "V3_COMPACT_ANSWERS_NOT_LOSSLESS")
    return compact


def compact_answer_metrics(full,compact):
    return {"schema":"IRE_V3_COMPACT_ANSWER_SIZE_REPORT_V1",
            "full_bytes":len(_json_bytes(full)),
            "compact_bytes":len(_json_bytes(compact)),
            "reversible":True,
            "no_llm_api_calls":True,
            "certifies_financial_meaning":False,
            "original_answer_sha256":sha256(_json_bytes(full))}