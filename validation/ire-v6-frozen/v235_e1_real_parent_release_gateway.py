"""V235: authoritative E1 source-native V127 -> V123 -> V128/V126 gateway.

The V233 checkpoint is a *plan*, not a source-reviewed V123 child case.
V232's full-video host-only batch is NOT thirteen child V6 host receipts.
This wrapper audits the real original, V231 source-only notes, V232 host,
V233 parent plan and V234 all cross-child source references before it calls
any downstream ChatGPT/V123/V128 callback or touches approved knowledge.

Cross-child atomic context cannot be truncated to meet V6's partial-scope
input contract.  Pending cross-context atoms force HOLD, not disguised PASS.
No API, automatic ChatGPT authoring or synthesized approvals.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from ire.v6 import TransactionStore
from ire.v6.codec import ZERO_SHA,json_digest
from ire.v6.errors import InvalidInput,QualityNotProven
from v126_chat_approved_knowledge_store import PrivateKnowledgeStore
from v1271_parent_resume_checkpoint import PrivateFullVideoCheckpoint
from v166_e3_chat_decision_delivery import run_full_video_with_e3_decisions
from v233_e1_v228_actual_parent_checkpoint_preflight import verify_v232_source_native_host
from v234_e1_cross_child_context_custody import verify_escrow_bytes

SCHEMA = "IRE_V235_E1_REAL_SOURCE_NATIVE_PARENT_GATEWAY_V1"


def _need(ok: Any, reason: str):
    if not ok:
        raise InvalidInput("V235_E1_" + reason)


def _rows(knowledge_store: PrivateKnowledgeStore):
    with sqlite3.connect(str(knowledge_store.path)) as con:
        existing={row[0] for row in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        return {n:(con.execute("SELECT COUNT(*) FROM "+n).fetchone()[0]
                   if n in existing else 0)
                for n in ("knowledge","events","parent_publications")}


def run_verified_source_native_parent_gateway(
        *, origin: dict, native_store: TransactionStore, scope_id: str,
        expected_host_head_sha256: str, expected_event_count: int,
        second_receipt: dict, private_source_note: dict, prequarantine: dict,
        externally_pinned_receipt_sha256: str,
        externally_pinned_source_note_sha256: str,
        externally_pinned_prequarantine_sha256: str,
        checkpoint: PrivateFullVideoCheckpoint,
        externally_pinned_parent_plan_sha256: str,
        externally_pinned_checkpoint_head_sha256: str,
        externally_pinned_source_sha256: str,
        externally_pinned_exchange_digest: str,
        cross_context_escrow: dict,
        externally_pinned_escrow_sha256: str,
        knowledge_store: PrivateKnowledgeStore,
        expected_knowledge_head_sha256: str = ZERO_SHA,
        review_or_load_child=None, review_seams=None, review_parent=None,
        ) -> dict:
    """Actual source-native verified route: HOLD until E2/E3 truth is supplied.

    For a repaired source with zero cross-child references this invokes the
    existing unmodified V123/V128/V126 implementation and checks atomicity.
    Without genuine ChatGPT child reviews it never substitutes a model verdict.
    """
    _need(type(knowledge_store) is PrivateKnowledgeStore
          and isinstance(checkpoint, PrivateFullVideoCheckpoint),
          "PRIVATE_KNOWLEDGE_AND_PARENT_REQUIRED")
    host = verify_v232_source_native_host(
        origin=origin,native_store=native_store,scope_id=scope_id,
        expected_host_head_sha256=expected_host_head_sha256,
        expected_event_count=expected_event_count,
        second_receipt=second_receipt,
        private_source_note=private_source_note,prequarantine=prequarantine,
        externally_pinned_receipt_sha256=externally_pinned_receipt_sha256,
        externally_pinned_source_note_sha256=
            externally_pinned_source_note_sha256,
        externally_pinned_prequarantine_sha256=
            externally_pinned_prequarantine_sha256)
    context = verify_escrow_bytes(
        origin=origin,checkpoint=checkpoint,escrow=cross_context_escrow,
        externally_pinned_escrow_sha256=externally_pinned_escrow_sha256,
        externally_pinned_parent_plan_sha256=
            externally_pinned_parent_plan_sha256,
        externally_pinned_checkpoint_head_sha256=
            externally_pinned_checkpoint_head_sha256,
        externally_pinned_source_sha256=externally_pinned_source_sha256,
        externally_pinned_exchange_digest=externally_pinned_exchange_digest)
    checkpoint_state=checkpoint.progress(
        externally_pinned_checkpoint_head=
            externally_pinned_checkpoint_head_sha256)
    _need(checkpoint_state["parent_plan_sha256"] ==
          externally_pinned_parent_plan_sha256 and
          checkpoint_state["parent_source_sha256"] ==
          origin["source_sha256"] and
          sum(len(m["windows"]) for m in checkpoint.child_manifests) ==
          host["host_window_count"],
          "ORIGINAL_V127_TO_V6_PLAN_NOT_PINNED")
    knowledge_audit=knowledge_store.audit(
        externally_pinned_head=expected_knowledge_head_sha256)
    before=_rows(knowledge_store)
    _need(knowledge_audit["active_claims"] == before["knowledge"]-
          knowledge_audit["revoked_claims"],
          "KNOWLEDGE_BASELINE_INCOHERENT")

    def hold(reason):
        _need(_rows(knowledge_store)==before,
              "HELD_SCOPE_LEAKED_APPROVED_KNOWLEDGE")
        return {
            "schema":SCHEMA,
            "status":reason,
            "source_sha256":host["source_sha256"],
            "v6_host_head_sha256":host["host_head_sha256"],
            "v127_parent_plan_sha256":externally_pinned_parent_plan_sha256,
            "cross_segment_atoms_pending":context["cross_segment_atom_count"],
            "cross_segment_qualifiers_pending":context[
                "cross_segment_qualifier_atom_count"],
            "cross_segment_numeric_atoms_pending":context[
                "cross_segment_numeric_atom_count"],
            "v127_children_passed":checkpoint_state["passed_child_scopes"],
            "v127_children_expected":checkpoint_state["expected_child_scopes"],
            "knowledge_before":before,"knowledge_after":before,
            "v123_chat_final_authorized":False,
            "e3_final_approved":False,"e4_authorized":False,
            "e5_published":0,
        }

    if context["cross_segment_atom_count"]:
        return hold("HOLD_CROSS_SEGMENT_CONTEXT_NOT_REPRESENTABLE_AS_CHILD_ATOMS")
    if not all(callable(fn) for fn in (
            review_or_load_child,review_seams,review_parent)):
        return hold("HOLD_REAL_CHATGPT_CHILD_SEAM_AND_PARENT_REVIEW_NOT_SUPPLIED")

    def fresh_parent_pin():
        # A callback may not change a V6/source owner while it is reviewed.
        verify_v232_source_native_host(
            origin=origin,native_store=native_store,scope_id=scope_id,
            expected_host_head_sha256=expected_host_head_sha256,
            expected_event_count=expected_event_count,
            second_receipt=second_receipt,
            private_source_note=private_source_note,prequarantine=prequarantine,
            externally_pinned_receipt_sha256=externally_pinned_receipt_sha256,
            externally_pinned_source_note_sha256=
                externally_pinned_source_note_sha256,
            externally_pinned_prequarantine_sha256=
                externally_pinned_prequarantine_sha256)
        _need(json_digest(origin["exchange"]) == externally_pinned_exchange_digest,
              "PARENT_NATIVE_ATOM_REVIEW_MUTATED_DURING_CALL")

    def child(segment_id,manifest,stage,original_raw):
        fresh_parent_pin()
        result=review_or_load_child(segment_id,manifest,stage,original_raw)
        fresh_parent_pin()
        return result

    def seam(checkpoint_obj,cases):
        fresh_parent_pin()
        result=review_seams(checkpoint_obj,cases)
        fresh_parent_pin()
        return result

    def parent(checkpoint_obj,assembly,seams,packets):
        fresh_parent_pin()
        result=review_parent(checkpoint_obj,assembly,seams,packets)
        fresh_parent_pin()
        return result

    result=run_full_video_with_e3_decisions(
        checkpoint,knowledge_store,review_or_load_child=child,
        review_seams=seam,review_parent=parent,
        expected_knowledge_head=expected_knowledge_head_sha256,
        externally_pinned_checkpoint_head=externally_pinned_checkpoint_head_sha256,
        externally_pinned_knowledge_head=expected_knowledge_head_sha256)
    fresh_parent_pin()
    after=_rows(knowledge_store)
    published=result["all_video_knowledge_published"] is True
    if published:
        new=after["parent_publications"]-before["parent_publications"]
        _need((new==1 and after["knowledge"]>before["knowledge"] and
               after["events"]-before["events"]==
               after["knowledge"]-before["knowledge"]) or
              (new==0 and after==before),
              "NON_ATOMIC_OR_DUPLICATED_PARENT_KNOWLEDGE")
    else:
        _need(after==before,"UNAPPROVED_PARENT_LEAKED_KNOWLEDGE")
    return {
        "schema":SCHEMA,
        "status":result["explicit_e3_status"],
        "source_sha256":host["source_sha256"],
        "v6_host_head_sha256":host["host_head_sha256"],
        "v127_parent_plan_sha256":externally_pinned_parent_plan_sha256,
        "cross_segment_atoms_pending":0,
        "v127_children_expected":checkpoint_state["expected_child_scopes"],
        "v127_children_reviewed_this_run":result["child_scopes_reviewed"],
        "knowledge_before":before,"knowledge_after":after,
        "v123_chat_final_authorized":published,
        "e3_final_approved":False,  # no blind gold or host identity claim
        "e4_authorized":False,  # structural research candidate only
        "e5_published":int(published),
        "research_candidate_only":True,
    }