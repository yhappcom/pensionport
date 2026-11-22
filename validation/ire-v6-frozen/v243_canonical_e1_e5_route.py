"""V243 official E1→ChatGPT V123/E3→V166 E4→V128 E5 route.

No LLM API. The ChatGPT HOST must supply source-first callbacks and attest that
TWO separate user-command stages for the source-first review and final
semantic review. V193 checks their recorded distinctness but cannot authenticate
ChatGPT host message IDs. This procedural check must not be mistaken for E3
semantic approval: the frozen V123/E4 source and official law gates still
decide whether any candidate can proceed to atomic V128/E5 publication.

The sole documented external research-publication interface is
run_canonical_research_route(). Legacy modules remain internal/history; no
standalone "publish" CLI is exported by this module. Python imports are not a
security boundary; a legacy direct-V126 write can physically modify SQLite but
cannot produce an externally pinned V166 E4 seal.
"""
from __future__ import annotations

from ire.v6.codec import ZERO_SHA, sha256, json_digest
from copy import deepcopy
from v245_e1_typed_parent_review_overlay import verify_typed_parent_review_overlay
from ire.v6.errors import InvalidInput, QualityNotProven
from v193_e3_two_user_turn_contract import validate_manual_turn_receipt
from v166_e4_sealed_knowledge import E4SealedKnowledgeStore
from v166_e4_primary_approval_gate import run_e4_guarded_parent

SCHEMA = "IRE_V243_CANONICAL_E1_E5_RESEARCH_ROUTE_V1"
__all__ = ("run_canonical_research_route",)


def _hold(checkpoint, *, reason, manual):
    return {
        "schema": SCHEMA,
        "status": "HOLD_AWAIT_SEPARATE_USER_VERIFICATION_COMMAND",
        "reason_code": reason,
        "source_sha256": checkpoint.parent.source_sha256,
        "original_source_bytes_rechecked": True,
        "checkpoint_head_sha256": checkpoint.progress()["checkpoint_head_sha256"],
        "claimed_distinct_user_commands": manual["recorded_distinct_user_commands"],
        "trusted_host_two_user_turns_verified": False,
        "manual_two_user_commands_recorded_not_platform_authenticated": False,
        "e4_invoked": False,
        "e5_invoked": False,
        "all_video_knowledge_published": False,
        "formal_financial_fact_approved": False,
        "personal_advice_approved": False,
        "p0_go": False,
    }


def run_canonical_research_route(
    checkpoint, knowledge_store, *,
    first_user_turn: dict, second_user_turn: dict | None,
    original_source_raw: bytes, source_sha256: str, owner_freeze_sha256: str,
    expected_knowledge_head: str,
    review_or_load_child, review_seams, review_parent,
    primary_manifest_for_child, typed_inventory_for_child,
    typed_manifest_for_child, now_as_of: str,
    parent_typed_review_overlay=None,
    expected_parent_typed_overlay_sha256=None,
    parent_native_raw=None, parent_cue_raw=None,
    parent_e3_raw=None, parent_pairs_raw=None,
    expected_parent_native_sha256=None,
    expected_parent_source_graph_sha256=None,
    required_parent_condition_claim=None,
) -> dict:
    """One *supported* executable API; fail closed before all E4/E5 writes.

    V193 verifies the *recorded workflow* for distinct user commands; its
    untrusted references do not authenticate the platform or approve a single
    source assertion. The actual veto authority is frozen V123 source-first
    ChatGPT review plus V166 E4 official-primary-source checks, followed by
    V128/E5 atomic SQLite publication and external owner-seal validation.

    Production operations must invoke phase 1 and phase 2 in distinct actual
    chat turns and preserve their private source+checkpoint receipts.
    Programmatic unit tests can prove this wiring using synthetic original
    subtitle and patched official HTTP; they cannot prove any real ETF E3
    verdict, host message identity, financial truth or user endorsement.
    """
    if not isinstance(knowledge_store, E4SealedKnowledgeStore):
        raise InvalidInput("V243_E4_SEALED_KNOWLEDGE_STORE_REQUIRED")
    if not all(callable(fn) for fn in (
        review_or_load_child,review_seams,review_parent,
        primary_manifest_for_child,typed_inventory_for_child,typed_manifest_for_child
    )):
        raise InvalidInput("V243_MANDATORY_HOST_AND_PRIMARY_CALLBACKS")
    if type(original_source_raw) is not bytes:
        raise InvalidInput("V243_ORIGINAL_SOURCE_BYTES_REQUIRED")
    if (type(source_sha256) is not str or type(owner_freeze_sha256) is not str or
        type(expected_knowledge_head) is not str):
        raise InvalidInput("V243_SOURCE_AND_HEAD_PINS_REQUIRED")
    progress=checkpoint.progress(externally_pinned_checkpoint_head=owner_freeze_sha256)
    if (sha256(original_source_raw) != source_sha256 or
        original_source_raw != checkpoint.raw or
        checkpoint.parent.source_sha256 != source_sha256 or
        progress["checkpoint_head_sha256"] != owner_freeze_sha256):
        raise QualityNotProven("V243_OWNER_SOURCE_OR_FREEZE_DRIFT")
    if (type(checkpoint.child_ids) is not list or not checkpoint.child_ids or
        len(set(checkpoint.child_ids))!=len(checkpoint.child_ids)):
        raise InvalidInput("V243_CHILD_CENSUS_INVALID")

    # A 13-child real long-form input cannot silently pass a child-local
    # V6 projection that discarded external conditions and numeric sources.
    # A private full-parent V245 typed overlay is mandatory for this scope.
    overlay_inputs=None
    overlay_args=(parent_typed_review_overlay,
        expected_parent_typed_overlay_sha256,parent_native_raw,parent_cue_raw,
        parent_e3_raw,parent_pairs_raw,expected_parent_native_sha256,
        expected_parent_source_graph_sha256)
    if len(checkpoint.child_ids)>=13 or any(x is not None for x in overlay_args):
        if any(x is None for x in overlay_args):
            raise InvalidInput("V243_PARENT_TYPED_OVERLAY_REQUIRED_FOR_13_CHILD_SOURCE")
        verification=verify_typed_parent_review_overlay(
            parent_typed_review_overlay,
            expected_overlay_sha256=expected_parent_typed_overlay_sha256,
            source_raw=original_source_raw,
            native_raw=parent_native_raw,cue_raw=parent_cue_raw,
            e3_raw=parent_e3_raw,pairs_raw=parent_pairs_raw,
            expected_source_sha256=source_sha256,
            expected_native_sha256=expected_parent_native_sha256,
            expected_graph_sha256=expected_parent_source_graph_sha256,
            expected_cue_count=len(checkpoint.parent.cues),
            expected_child_count=len(checkpoint.child_ids),
            expected_atom_count=parent_typed_review_overlay.get("atom_count"),
            expected_cross_atom_count=parent_typed_review_overlay.get("cross_atom_count"),
            expected_cross_edge_count=parent_typed_review_overlay.get("cross_typed_edge_count"),
            window_size=checkpoint.max_cues,
            required_cross_scope_claim=required_parent_condition_claim)
        if (verification["status"]!="PARENT_TYPED_CHILD_INPUTS_SOURCE_VERIFIED_NOT_APPROVED"
                or parent_typed_review_overlay["source_sha256"]!=source_sha256
                or parent_typed_review_overlay["child_count"]!=len(checkpoint.child_ids)):
            raise QualityNotProven("V243_PARENT_TYPED_OVERLAY_INVALID")
        overlay_inputs=parent_typed_review_overlay["child_review_inputs"]
        for sid,m,inp in zip(checkpoint.child_ids,checkpoint.child_manifests,overlay_inputs):
            if (inp["child_id"]!=sid or
                inp["child_plan_sha256"]!=json_digest({
                    "child_id":sid,
                    "owner_window_id":f"W{int(sid[1:]):05d}",
                    "first_cue":m["scope"]["first_cue"],
                    "last_cue":m["scope"]["last_cue"],
                    "cue_count":m["scope"]["last_cue"]-m["scope"]["first_cue"]+1,
                    "original_window_text_sha256":sha256(" ".join(
                        c.text for c in checkpoint.parent.cues[
                            m["scope"]["first_cue"]-1:m["scope"]["last_cue"]]
                    ).encode("utf-8")),
                    "cue_byte_lineage_sha256":json_digest([
                        {"cue_index":i,"child_id":sid,
                         "owner_window_id":f"W{int(sid[1:]):05d}",
                         "start_ms":checkpoint.parent.cues[i-1].start_ms,
                         "end_ms":checkpoint.parent.cues[i-1].end_ms,
                         "source_quote_sha256":sha256(
                             checkpoint.parent.cues[i-1].text.encode("utf-8"))}
                        for i in range(m["scope"]["first_cue"],
                                       m["scope"]["last_cue"]+1)]),
                })):
                raise InvalidInput("V243_CHILD_INPUT_NOT_SAME_PINNED_PARENT_PLAN")
    def typed_bound_child(segment_id,manifest,stage,original_raw):
        if overlay_inputs is None:
            return review_or_load_child(segment_id,manifest,stage,original_raw)
        if segment_id not in checkpoint.child_ids:
            raise InvalidInput("V243_TYPED_CHILD_UNKNOWN_SEGMENT")
        inp=overlay_inputs[checkpoint.child_ids.index(segment_id)]
        response=review_or_load_child(
            segment_id,manifest,stage,original_raw,deepcopy(inp))
        # The frozen V128 packet has an EXACT four-key schema. Transport
        # context acknowledgement out of band, never smuggle extra keys into
        # the native V128 review packet or change its sealed implementation.
        if type(response) is not tuple or len(response)!=2:
            raise InvalidInput("V243_CHILD_CHAT_INPUT_NOT_ACKNOWLEDGED_AS_FULL_PARENT")
        packet, acknowledgement=response
        if (type(packet) is not dict or type(acknowledgement) is not dict or
            acknowledgement.get("parent_typed_review_input_sha256")!=
                inp["review_input_sha256"] or
            acknowledgement.get("parent_typed_overlay_sha256")!=
                parent_typed_review_overlay["typed_overlay_sha256"]):
            raise InvalidInput("V243_CHILD_CHAT_INPUT_NOT_ACKNOWLEDGED_AS_FULL_PARENT")
        return packet

    manual=validate_manual_turn_receipt(
        first=first_user_turn,second=second_user_turn,
        source_sha256=source_sha256,owner_head_sha256=owner_freeze_sha256,
        batch_count=len(checkpoint.child_ids),
        independent_gold_certified=False,
        e3_approved=False,v123_e4_approved=False,e5_published=False)
    # The V193 manual receipt only establishes caller-reported command
    # distinctness, not platform provenance or ChatGPT semantic correctness.
    # This procedural stage must never be promoted to "E3 PASS"; it permits
    # a source-pinned candidate to *reach* the real V123/E4 approval gates.
    if (second_user_turn is None or
        manual.get("phase") != "TWO_DISTINCT_USER_COMMANDS_CLAIMED_UNVERIFIED" or
        manual.get("recorded_distinct_user_commands") != 2 or
        manual.get("host_separate_turns_verified") is not False or
        manual.get("two_user_turns_proven") is not False or
        manual.get("e3_semantic_accuracy_certified") is not False or
        manual.get("v123_e4_approved") is not False or
        manual.get("e5_published") is not False):
        return _hold(checkpoint,reason="SEPARATE_USER_REVIEW_COMMAND_NOT_RECORDED",manual=manual)
    # Full external source meaning cannot be approved simply because a
    # child packet acknowledged receiving the entire parent. V123/V6 child
    # grammar is local-scope; any still-UNRESOLVED cross-child parent atom
    # must remain in a private SOURCE-FIRST formal review input envelope.
    # E4 and E5 never execute while that owner semantic decision is pending.
    if overlay_inputs is not None and parent_typed_review_overlay["cross_atom_count"]>0:
        return {
            "schema": SCHEMA,
            "status":"HOLD_PARENT_CROSS_CHILD_SEMANTIC_REVIEW_REQUIRED",
            "source_sha256":source_sha256,
            "checkpoint_head_sha256":owner_freeze_sha256,
            "typed_parent_overlay_sha256":parent_typed_review_overlay["typed_overlay_sha256"],
            "parent_source_graph_sha256":expected_parent_source_graph_sha256,
            "unapproved_cross_child_parent_atoms":parent_typed_review_overlay["cross_atom_count"],
            "exact_external_typed_source_edges":parent_typed_review_overlay["cross_typed_edge_count"],
            "formal_child_review_inputs_private":deepcopy(overlay_inputs),
            "private_source_text_do_not_export_to_github":True,
            "manual_two_user_commands_recorded_not_platform_authenticated":True,
            "trusted_host_two_user_turns_verified":False,
            "e4_invoked":False,"e5_invoked":False,
            "all_video_knowledge_published":False,
            "formal_financial_fact_approved":False,
            "personal_advice_approved":False,"p0_go":False,
        }
    # Approval authority remains inside the unmodified V123→E4→V128
    # chain. No locally-authored user ref or CI parameter can self-approve.
    # Capture the trustworthy logical row fingerprint BEFORE touching the E4
    # store. A failed or HELD E4 must never leave a publishable knowledge row.
    before_knowledge=knowledge_store._logical_fingerprint()
    outcome=run_e4_guarded_parent(
        checkpoint,knowledge_store,
        review_or_load_child=typed_bound_child,
        review_seams=review_seams,review_parent=review_parent,
        primary_manifest_for_child=primary_manifest_for_child,
        typed_inventory_for_child=typed_inventory_for_child,
        typed_manifest_for_child=typed_manifest_for_child,
        expected_knowledge_head=expected_knowledge_head,
        now_as_of=now_as_of)
    if outcome.get("schema")!="IRE_V166_E4_PARENT_APPROVAL_V1":
        raise QualityNotProven("V243_E4_ROUTE_RECEIPT_INVALID")
    approved=outcome.get("status")=="E4_PARENT_RESEARCH_CANDIDATES_PUBLISHED"
    if approved != (outcome.get("all_video_knowledge_published") is True):
        raise QualityNotProven("V243_E4_E5_STATUS_DIVERGENCE")
    after_knowledge=knowledge_store._logical_fingerprint()
    owner_pin=None
    idempotent_owner_pinned_replay=False
    new_parent_commit=False
    if approved:
        # An in-process HMAC seal does not prove separate owner custody. Reopen
        # the actual E4 certificate and exact SQLite logical rows. Never treat
        # a returned dict with a success-looking status as a durable E5 write.
        owner_pin=outcome.get("e4_external_owner_pin_sha256")
        if (type(owner_pin) is not str or len(owner_pin)!=64 or
            any(x not in "0123456789abcdef" for x in owner_pin)):
            raise QualityNotProven("V243_E4_SEAL_OWNER_PIN_MISSING")
        certified=knowledge_store.verify_e4_certificate(
            externally_pinned_seal_sha256=owner_pin)
        new_parent_commit=(
            certified["parent_count"]==before_knowledge["parent_count"]+1
            and certified["knowledge_count"]>before_knowledge["knowledge_count"]
            and after_knowledge["events_count"]>before_knowledge["events_count"])
        idempotent_owner_pinned_replay=(
            certified["parent_count"]>=1
            and certified["parent_count"]==before_knowledge["parent_count"]
            and after_knowledge==before_knowledge
            # A previous E4 certificate must be explicitly pinned and
            # verified by the store; fresh output is never its own proof.
            and knowledge_store._trusted_prior_owner_pin is not None
            and knowledge_store._trusted_prior_owner_pin==owner_pin)
        if (certified["knowledge_head_sha256"]!=after_knowledge["knowledge_head_sha256"]
                or not (new_parent_commit or idempotent_owner_pinned_replay)
                or certified["parent_count"]!=after_knowledge["parent_count"]
                or outcome.get("e4_durable_certification_verified") is not True
                or outcome.get("e3_parent_status")!="PUBLISHED_RESEARCH_CANDIDATES_ONLY"
                or len(outcome.get("child_preflights",[]))!=len(checkpoint.child_ids)
                or any(x.get("e4_status")!="E4_PASS_RESEARCH_CANDIDATES_ONLY"
                       for x in outcome["child_preflights"])):
            raise QualityNotProven("V243_E4_E5_COMMIT_OR_SEAL_NOT_CONSISTENT")
    elif before_knowledge!=after_knowledge:
        # A hostile callback or legacy direct SQLite writer may still modify
        # the same FILE. That event must be reported as an integrity incident,
        # never silently downgraded to an ordinary HOLD.
        raise QualityNotProven("V243_E4_HELD_BUT_KNOWLEDGE_DATABASE_MUTATED")
    if (outcome.get("formal_financial_fact_formally_approved") is True or
        outcome.get("financial_fact_formally_approved") is True or
        outcome.get("personal_advice_approved") is True or outcome.get("p0_go") is True):
        raise QualityNotProven("V243_FALSE_FINANCIAL_FACT_OR_ADVISORY_GO")
    return {
        "schema": SCHEMA,
        "status": (
            "RESEARCH_CANDIDATE_PARENT_IDEMPOTENT_REPLAY_NO_NEW_WRITE"
            if idempotent_owner_pinned_replay else
            "RESEARCH_CANDIDATE_PARENT_COMMITTED_AWAIT_OWNER_PIN_CUSTODY"
            if approved else "HOLD_E4_PRIMARY_EVIDENCE"),
        "source_sha256": source_sha256,
        "original_source_bytes_rechecked": True,
        "checkpoint_head_sha256": checkpoint.progress()["checkpoint_head_sha256"],
        "claimed_distinct_user_commands":manual["recorded_distinct_user_commands"],
        "trusted_host_two_user_turns_verified": False,
        "manual_two_user_commands_recorded_not_platform_authenticated": True,
        "v193_process_claim_is_not_e3_semantic_certification": True,
        "typed_parent_full_context_delivered_to_each_child":overlay_inputs is not None,
        "typed_parent_overlay_sha256":(parent_typed_review_overlay["typed_overlay_sha256"]
                                          if overlay_inputs is not None else None),
        "e4_invoked": True,
        "e4_receipt": outcome,
        "e5_invoked": approved,
        "e5_new_parent_committed":new_parent_commit,
        "e5_idempotent_replay_no_new_sqlite_rows":idempotent_owner_pinned_replay,
        "all_video_knowledge_published": approved,
        "e4_external_pin_returned_not_yet_owner_custodied": owner_pin,
        "externally_independent_owner_pin_reverified": False,
        "e4_sqlite_parent_logically_replayed_after_commit": approved,
        "formal_financial_fact_approved": False,
        "personal_advice_approved": False,
        "p0_go": False,
    }
