"""Private current-ChatGPT one-turn SRT task renderer and atomic host receipt.

No model API: the actual chat must supply atomic claims and financial checks.
Tasks exposing private original cue text must never enter public logs or GitHub.
An oversized scope fails closed, never falsely marked as processed.
"""
from __future__ import annotations

import json

from .codec import json_digest, require_hash, require_identifier
from .errors import DomainConflict, InvalidInput, QualityNotProven
from .trust import verify_owner_inventory

TASK_SCHEMA="IRE_V6_PRIVATE_CHATGPT_HOST_TURN_V1"
MAX_CUES=120
MAX_PAYLOAD_BYTES=200000


def prepare_private_host_turn(raw,manifest,inventory_bytes,*,
                              scope_id,expected_inventory_sha256,expected_head,
                              max_cues=MAX_CUES,max_payload_bytes=MAX_PAYLOAD_BYTES):
    """Return private cue packet only when its bounded whole scope fits."""
    scope_id=require_identifier(scope_id,name="SCOPE_ID")
    require_hash(expected_head,"HOST_TURN_LEDGER_BASE")
    if (type(max_cues) is not int or not 1<=max_cues<=20000 or
        type(max_payload_bytes) is not int or
        not 1024<=max_payload_bytes<=800000):
        raise InvalidInput("HOST_TURN_LIMITS_INVALID")
    pinned=verify_owner_inventory(raw,manifest,inventory_bytes,
                         expected_inventory_sha256=expected_inventory_sha256)
    src=pinned.source
    count=src.scope_last_cue-src.scope_first_cue+1
    full_video=src.scope_first_cue==1 and src.scope_last_cue==len(src.cues)
    base={"schema":TASK_SCHEMA,"scope_id":scope_id,
          "video_id":src.video_id,"source_sha256":src.source_sha256,
          "manifest_sha256":src.manifest_sha256,
          "owner_inventory_sha256":pinned.inventory_sha256,
          "cue_census_sha256":src.cue_census_sha256,
          "expected_ledger_head_sha256":expected_head,
          "first_cue":src.scope_first_cue,"last_cue":src.scope_last_cue,
          "original_cue_count":len(src.cues),"scoped_cue_count":count,
          "scope_full_video":full_video,
          "full_video_research_completed":False,
          "independent_gold_supplied_to_model":False,
          "p0_go":False}
    if count>max_cues:
        return dict(base,status="HOST_TURN_BLOCKED_SCOPE_TOO_MANY_CUES",
                    requires_explicit_smaller_source_plan=True,
                    turn_payload_available=False)
    windows=[]
    for wid,first,last in src.primary_windows:
        cues=[{"cue_index":i,"start_ms":src.cues[i-1].start_ms,
               "end_ms":src.cues[i-1].end_ms,"text":src.cues[i-1].text}
              for i in range(first,last+1)]
        windows.append({"window_id":wid,"first_cue":first,
                        "last_cue":last,"primary_cues":cues,
                        "neighbor_first_cue":max(src.scope_first_cue,first-2),
                        "neighbor_last_cue":min(src.scope_last_cue,last+2)})
    payload={"schema":TASK_SCHEMA,"scope_id":scope_id,
             "source_sha256":src.source_sha256,
             "manifest_sha256":src.manifest_sha256,
             "expected_ledger_head_sha256":expected_head,
             "original_cue_count":len(src.cues),
             "scoped_cue_count":count,
             "scope_full_video":full_video,"windows":windows,
             "source_first_exhaustive_cue_dispositions_required":True,
             "extract_conditions_exceptions_speaker_stance_and_as_of":True,
             "all_proposals_require_exact_original_quotes":True,
             "independent_gold_must_not_be_shown_to_model":True}
    packet_bytes=len(json.dumps(payload,ensure_ascii=False,sort_keys=True,
                    separators=(",",":")).encode("utf-8"))
    if packet_bytes>max_payload_bytes:
        return dict(base,status="HOST_TURN_BLOCKED_PRIVATE_PAYLOAD_TOO_LARGE",
                    requires_explicit_smaller_source_plan=True,
                    turn_payload_available=False,
                    payload_byte_count=packet_bytes)
    return dict(base,status="HOST_TURN_READY_NOT_EXECUTED",
                requires_explicit_smaller_source_plan=False,
                turn_payload_available=True,
                private_payload_sha256=json_digest(payload),
                turn_payload=payload,
                payload_byte_count=packet_bytes)


def commit_private_host_turn(store,task,*,raw,manifest,inventory_bytes,
                             expected_inventory_sha256,run_id,
                             exchange,knowledge,window_models,window_reviews,
                             max_cues=MAX_CUES,
                             max_payload_bytes=MAX_PAYLOAD_BYTES):
    """Replay exact private input then submit V11 ACID host model/proof batch."""
    if type(task) is not dict or task.get("schema")!=TASK_SCHEMA:
        raise InvalidInput("HOST_TURN_TASK_SCHEMA_INVALID")
    scope_id=require_identifier(task.get("scope_id"),name="SCOPE_ID")
    expected=require_hash(task.get("expected_ledger_head_sha256"),
                          "HOST_TURN_LEDGER_BASE")
    replay=prepare_private_host_turn(raw,manifest,inventory_bytes,
                   scope_id=scope_id,
                   expected_inventory_sha256=expected_inventory_sha256,
                   expected_head=expected,max_cues=max_cues,
                   max_payload_bytes=max_payload_bytes)
    if not replay["turn_payload_available"]:
        raise QualityNotProven("HOST_TURN_SOURCE_SCOPE_CANNOT_BE_COMPLETED")
    if task!=replay:
        raise DomainConflict("HOST_TURN_PRIVATE_SOURCE_PACKET_DRIFT")
    result=store.submit_host_atomic_batch(
        scope_id=scope_id,run_id=run_id,expected_head=expected,
        raw=raw,manifest=manifest,
        inventory_bytes=inventory_bytes,
        expected_inventory_sha256=expected_inventory_sha256,
        exchange=exchange,knowledge=knowledge,
        window_models=window_models,window_reviews=window_reviews)
    return {"schema":"IRE_V6_HOST_TURN_BRIDGE_RECEIPT_V1",
            "video_id":task["video_id"],
            "private_task_payload_sha256":task["private_payload_sha256"],
            "source_sha256":task["source_sha256"],
            "source_scope_full_video":task["scope_full_video"],
            "atomic_batch_receipt":result,
            "model_api_called":False,
            "human_semantic_review_pending":True,
            "independent_gold_recall_measured":False,
            "full_video_research_completed":False,
            "research_complete":False,"p0_go":False}
