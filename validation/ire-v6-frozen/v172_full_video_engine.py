"""V172: exhaustive, single-invocation E4 preflight before guarded native parent.

ENGINE CONTRACT: inspect *every* child, even when an earlier child has a V123
HOLD or E4 missing original. Do not transform OPEN to PASS, write research
knowledge or generate fictitious ChatGPT input. A host must supply the actual
source-pinned child cases. Only the frozen V166 E4-sealed parent can publish.

Production call must pin `expected_scope_count` to the actual owner's complete
manifest (13 for the B0001..B0013 video), not a convenient test fraction.
"""
from __future__ import annotations

from ire.v6.errors import InvalidInput, QualityNotProven
from v166_e4_primary_approval_gate import (
    assess_e4_primary_authority_gate, run_e4_guarded_parent,
)
from v166_e4_sealed_knowledge import E4SealedKnowledgeStore

SCHEMA = "IRE_V172_EXHAUSTIVE_VIDEO_E4_NATIVE_RUN_V1"


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise InvalidInput("V172_ENGINE_" + message)


def run_exhaustive_full_video(
    checkpoint, knowledge_store, *,
    review_or_load_child, review_seams, review_parent,
    primary_manifest_for_child, typed_inventory_for_child,
    typed_manifest_for_child, expected_knowledge_head,
    now_as_of, expected_scope_count,
) -> dict:
    """One command: inspect every pinned child, then *conditionally* publish.

    HOLD, REJECT, incomplete source and a per-child verifier error all remain
    non-releasing results. The preflight is read-only for both checkpoint and
    knowledge: unlike V128 it does not stop at the first HOLD or make any
    provisional knowledge writes. If all child preflights PASS, replay them
    through the original E4 guarded parent, including seam and parent ChatGPT
    review and native V128 atomic publication. This is not a model API.
    """
    _require(isinstance(knowledge_store, E4SealedKnowledgeStore),
             "SEALED_E4_STORE_REQUIRED")
    _require(type(expected_scope_count) is int and expected_scope_count >= 1,
             "EXPECTED_SCOPE_COUNT_REQUIRED")
    ids = getattr(checkpoint, "child_ids", None)
    manifests = getattr(checkpoint, "child_manifests", None)
    _require(type(ids) in (list, tuple) and type(manifests) in (list, tuple)
             and len(ids) == len(manifests) == expected_scope_count
             and len(set(ids)) == len(ids),
             "COMPLETE_PINNED_VIDEO_SCOPE_CENSUS")
    _require(all(callable(c) for c in (
        review_or_load_child, review_seams, review_parent,
        primary_manifest_for_child, typed_inventory_for_child,
        typed_manifest_for_child)), "LIVE_CHAT_HOST_CALLBACKS_REQUIRED")
    _require(type(now_as_of) is str and bool(now_as_of)
             and type(expected_knowledge_head) is str,
             "DATE_OR_KNOWLEDGE_HEAD_REQUIRED")
    # Catch an improperly configured host *before* invoking any child callbacks.
    checkpoint.progress()
    original_raw = checkpoint.raw
    supplied = {}
    rows = []
    for sid, manifest in zip(ids, manifests):
        # Do not request a previously held revision just by reopening a stream:
        # these callbacks provide the current revision and V128 enforces any
        # explicit hold revision on the second, guarded replay.
        decision = None
        try:
            packet = review_or_load_child(sid, manifest, "PREFLIGHT_ALL_SCOPES", original_raw)
            _require(type(packet) is dict and type(packet.get("case")) is dict,
                     "CHILD_PACKET_MISSING")
            # Snapshot original supplied case/relationships. Callback is not
            # re-invoked during final publication, so no second model call or
            # swapped review after preflight is possible in this coordinator.
            supplied[sid] = packet
            case = packet["case"]
            _require(case.get("manifest") == manifest,
                     "CHILD_MANIFEST_NOT_FROZEN_PARENT")
            assessment = assess_e4_primary_authority_gate(
                case, primary_manifest_for_child(sid, case), now_as_of=now_as_of,
                typed_inventory=typed_inventory_for_child(sid, case),
                typed_manifest=typed_manifest_for_child(sid, case),
            )
            status = assessment["status"]
            reason = assessment.get("reason_code")
            decision = assessment.get("native_chat_decision")
            pass_gate = status == "E4_PASS_RESEARCH_CANDIDATES_ONLY"
            # Unknown success-like statuses MUST NOT be interpreted as PASS.
            _require(pass_gate or status == "E4_HOLD_INELIGIBLE_APPROVAL",
                     "UNKNOWN_PRIMARY_GATE_STATUS")
            n_open = assessment.get("native_unapproved_open_claim_count", 0)
        except Exception as exc:
            # A child failing an auditable verification must not prevent
            # remaining children from being examined. No private exception
            # message, URL, quote or stack trace is included in receipts.
            status, reason, pass_gate, n_open = (
                "E4_CHILD_VERIFIER_ERROR", type(exc).__name__, False, None)
        rows.append({
            "segment_id": sid, "native_decision": decision,
            "e4_status": status, "reason_code": reason,
            "open_atom_count": n_open,
            "e4_child_pass": pass_gate,
        })
    _require(len(rows) == expected_scope_count, "DID_NOT_EXAMINE_ENTIRE_VIDEO")
    blocked = [r["segment_id"] for r in rows if not r["e4_child_pass"]]
    base = {
        "schema": SCHEMA,
        "owner_video_scope_count": expected_scope_count,
        "child_scopes_examined": len(rows),
        "child_preflights": rows,
        "blocked_scope_ids": blocked,
        "blocked_scope_count": len(blocked),
        "all_children_native_and_e4_preflight_pass": not blocked,
        "chatgpt_automatically_invoked_by_python": False,
        "any_child_open_promoted_by_coordinator": False,
        "personal_advice_approved": False,
        "p0_go": False,
    }
    if blocked:
        return {**base,
            "status": "EXHAUSTIVE_E4_HOLD_ALL_SCOPES_CHECKED",
            "official_parent_invoked": False,
            "all_video_knowledge_published": False,
            "e5_authorized": False,
        }

    def pinned_child(sid, manifest, stage, raw):
        _require(sid in supplied and manifest == manifests[ids.index(sid)]
                 and raw == original_raw,
                 "CHILD_PACKET_CHANGED_BETWEEN_PREFLIGHT_AND_PUBLICATION")
        # It is safe to re-use the same immutable chat-produced packet; the
        # existing V128 checkpoint makes the final stage decision.
        return supplied[sid]

    # No custom ad-hoc publishing path. The *original* E4 approval runner
    # re-fetches original issuer bytes and runs E3->V128 parent ACID release.
    try:
        committed = run_e4_guarded_parent(
            checkpoint, knowledge_store,
            review_or_load_child=pinned_child,
            review_seams=review_seams, review_parent=review_parent,
            primary_manifest_for_child=primary_manifest_for_child,
            typed_inventory_for_child=typed_inventory_for_child,
            typed_manifest_for_child=typed_manifest_for_child,
            expected_knowledge_head=expected_knowledge_head,
            now_as_of=now_as_of,
        )
    except (InvalidInput, QualityNotProven, OSError, ValueError) as exc:
        return {**base,
            "status": "PARENT_REPLAY_FAILED_NO_CERTIFIED_RELEASE",
            "parent_error_type": type(exc).__name__,
            "official_parent_invoked": True,
            "all_video_knowledge_published": False,
            "e5_authorized": False,
        }
    authorized = (
        committed.get("status") == "E4_PARENT_RESEARCH_CANDIDATES_PUBLISHED"
        and committed.get("e4_durable_certification_verified") is True
        and committed.get("all_video_knowledge_published") is True
    )
    return {**base,
        "status": "E4_SEALED_PARENT_PUBLISHED_RESEARCH_ONLY" if authorized
                  else "PARENT_REPLAY_FAILED_NO_CERTIFIED_RELEASE",
        "official_parent_invoked": True,
        "all_video_knowledge_published": authorized,
        "e4_owner_pin_sha256": committed.get("e4_external_owner_pin_sha256") if authorized else None,
        "e5_authorized": authorized,
    }