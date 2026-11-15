"""V128 single-invocation ChatGPT-hosted long-video run coordinator.

The in-chat host MUST supply synchronous semantic and source evidence callbacks.
This module cannot invoke ChatGPT itself (no external model API). It calls each
callback in source order, checkpoints a real V6+V123 review and proceeds until
a HOLD or all children are done; only then may parent-wide atomic knowledge
publication occur. It neither launches tasks in background nor skips review.
"""
from __future__ import annotations

from contextlib import closing

from ire.v6.errors import InvalidInput, QualityNotProven
from v128_atomic_parent_knowledge import publish_parent_once


def _stop(code):
    raise QualityNotProven("V128_HOST_" + code)


def run_all_video_scopes_in_chat(checkpoint, knowledge_store, *,
                                 review_or_load_child, review_seams, review_parent,
                                 expected_knowledge_head,
                                 externally_pinned_checkpoint_head=None,
                                 externally_pinned_knowledge_head=None):
    """Run all scopes in ONE host invocation, then atomically publish or HOLD.

    review_or_load_child is the synchronous ChatGPT host adapter:
      (segment_id, child_manifest, stage, original_raw) -> {
        'case': exact V127 child case with V6 host and ChatGPT review,
        'relation_decisions': final ChatGPT relationship judgments,
        'original_host_batch_replay_args': exact V6 original commit kwargs,
        'explicit_hold_revision': bool,
      }
    stage is 'REVIEW_REQUIRED' or 'LOAD_EXISTING_PINNED_PASS'. In the latter
    case the host must retrieve the original PRIVATE accepted review artifact,
    NOT rerun an opaque model or invent a new result.

    review_seams(checkpoint, child_cases) -> V127 seam review rows, written and
    checked by ChatGPT in the present chat invocation.
    review_parent(checkpoint, assembly, seam_rows, packets) -> explicit final
    parent ChatGPT review; NO automatic acceptance is synthesized here.
    """
    if not all(callable(c) for c in (review_or_load_child,review_seams,review_parent)):
        raise InvalidInput("V128_HOST_SYNC_CHAT_CALLBACKS_REQUIRED")
    checkpoint.progress(externally_pinned_checkpoint_head=
                        externally_pinned_checkpoint_head)
    with closing(checkpoint._connect()) as con:
        _,initial_rows=checkpoint._audit(con)
    packets=[]
    appended=0
    reused=0
    for segment_id, manifest in zip(checkpoint.child_ids,checkpoint.child_manifests):
        previous=initial_rows.get(segment_id)
        stage=("LOAD_EXISTING_PINNED_PASS" if previous is not None and
               previous["decision"]=="PASS" else "REVIEW_REQUIRED")
        # A chat host can finish one scope in one invocation; the coordinator
        # never yields control to a scheduled task or requires a user re-prompt.
        supplied=review_or_load_child(segment_id,manifest,stage,checkpoint.raw)
        if type(supplied) is not dict or set(supplied)!={
            "case","relation_decisions","original_host_batch_replay_args",
            "explicit_hold_revision"} or type(supplied["explicit_hold_revision"]) is not bool:
            _stop("REVIEW_CHILD_PACKET_MISSING_OR_SCHEMA")
        current=checkpoint.progress()
        row=checkpoint.record(segment_id,supplied["case"],
               expected_checkpoint_head=current["checkpoint_head_sha256"],
               allow_hold_revision=(supplied["explicit_hold_revision"] and
                                    previous is not None and previous["decision"]!="PASS"))
        if row["status"]=="CHILD_CHAT_CHECKPOINT_HOLD" or row["status"]=="CHILD_CHAT_CHECKPOINT_REJECT":
            return {"schema":"IRE_V128_HOST_SINGLE_INVOCATION_RUN_V1",
                    "status":"HOLD_CHILD_CHAT_SEMANTICS_OR_FINANCE",
                    "next_segment_id":segment_id,
                    "checkpoint_head_sha256":row["checkpoint_head_sha256"],
                    "child_scopes_supplied":len(packets)+1,
                    "all_video_knowledge_published":False,"p0_go":False}
        if row["status"] not in {"CHILD_CHAT_CHECKPOINT_PASS", "IDEMPOTENT_CHILD_CHECKPOINT_REPLAY"}:
            _stop("CHILD_CHECKPOINT_UNKNOWN_STATUS")
        if row["idempotent"]:
            reused+=1
        else:
            appended+=1
        packets.append({k:supplied[k] for k in (
            "case","relation_decisions","original_host_batch_replay_args")})
    cases=[p["case"] for p in packets]
    seams=review_seams(checkpoint,cases)
    if type(seams) is not list:
        _stop("SEAM_REVIEW_REQUIRED")
    final_progress=checkpoint.progress()
    head=final_progress["checkpoint_head_sha256"]
    if final_progress["ready_for_full_parent_replay"] is not True:
        _stop("PARENT_NOT_READY_FOR_SEAM_AND_FINAL_CHAT")
    assembly=checkpoint.assemble(cases,seams,expected_checkpoint_head=head)
    # Final host review is mandatory and must source-bind this exact assembly.
    parent_release=review_parent(checkpoint,assembly,seams,packets)
    receipt=publish_parent_once(
        checkpoint,knowledge_store,packets,seams,parent_release,
        expected_checkpoint_head=head,
        expected_knowledge_head=expected_knowledge_head,
        externally_pinned_knowledge_head=externally_pinned_knowledge_head)
    return {"schema":"IRE_V128_HOST_SINGLE_INVOCATION_RUN_V1",
            "status":"WHOLE_VIDEO_RESEARCH_CANDIDATE_PUBLISHED_ATOMICALLY",
            "checkpoint_head_sha256":head,
            "knowledge_head_sha256":receipt["knowledge_head_sha256"],
            "child_scopes_supplied":len(cases),
            "child_checkpoints_written":appended,
            "child_checkpoints_reused":reused,
            "all_video_knowledge_published":True,
            "publication_receipt":receipt,
            "financial_fact_formally_approved":0,
            "no_external_llm_api_called":True,
            "personal_advice_approved":False,
            "engine_791_video_quality_certified":False,
            "p0_go":False}
