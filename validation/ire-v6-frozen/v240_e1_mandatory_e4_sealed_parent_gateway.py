"""V240: only trusted E1 publication route invokes frozen E4 sealed authority.

V235's ordinary V128/V126 research candidate route is NOT E4-certified.
This wrapper cannot downgrade to PrivateKnowledgeStore, skip typed official
primary evidence, or infer E3 permission from an unapproved 2-turn intake.
V237/V238/V239 are verified before ANY E4 callback or durable knowledge write.
"""
from __future__ import annotations

from typing import Any

from ire.v6.codec import ZERO_SHA, json_digest
from ire.v6.errors import InvalidInput, QualityNotProven
from v166_e4_primary_approval_gate import run_e4_guarded_parent
from v166_e4_sealed_knowledge import E4SealedKnowledgeStore
from v237_e1_parent_child_review_contract import verify_child_review_tasks
from v238_e1_child_native_scope_draft import verify_partial_native_drafts
from v239_e1_source_bound_second_turn_child_intake import verify_pending_child_review_intake

SCHEMA='IRE_V240_E1_E4_SEALED_AUTHORITY_MANDATORY_V1'


def _need(ok,why):
    if not ok: raise InvalidInput('V240_E1_'+why)


def run_mandatory_e4_source_native_parent(*,
        origin:dict,checkpoint,review_tasks:dict,child_native_draft:dict,
        pending_review_intake:dict,second_receipt:dict,private_source_note:dict,
        prequarantine:dict,cross_context_escrow:dict,
        externally_pinned_review_tasks_sha256:str,
        externally_pinned_child_draft_sha256:str,
        externally_pinned_intake_sha256:str,
        externally_pinned_receipt_sha256:str,
        externally_pinned_source_note_sha256:str,
        externally_pinned_prequarantine_sha256:str,
        externally_pinned_escrow_sha256:str,
        externally_pinned_parent_plan_sha256:str,
        externally_pinned_checkpoint_head_sha256:str,
        externally_pinned_source_sha256:str,
        externally_pinned_exchange_digest:str,
        knowledge_store:E4SealedKnowledgeStore,
        expected_knowledge_head_sha256:str=ZERO_SHA,
        review_or_load_child=None,review_seams=None,review_parent=None,
        primary_manifest_for_child=None,typed_inventory_for_child=None,
        typed_manifest_for_child=None,now_as_of=None)->dict:
    """Source/turn2 verified; E4 is non-bypassable, otherwise explicit HOLD.

    For an input without cross claims, real V123/E4 callbacks are required;
    no locally supplied OPEN/HOLD review row can become an E3 final verdict.
    """
    _need(isinstance(knowledge_store,E4SealedKnowledgeStore),
          'E4_SEALED_STORE_REQUIRED_LEGACY_V126_FORBIDDEN')
    source=dict(externally_pinned_escrow_sha256=externally_pinned_escrow_sha256,
        externally_pinned_parent_plan_sha256=externally_pinned_parent_plan_sha256,
        externally_pinned_checkpoint_head_sha256=externally_pinned_checkpoint_head_sha256,
        externally_pinned_source_sha256=externally_pinned_source_sha256,
        externally_pinned_exchange_digest=externally_pinned_exchange_digest)
    task_coverage=verify_child_review_tasks(
        origin=origin,checkpoint=checkpoint,review_tasks=review_tasks,
        cross_context_escrow=cross_context_escrow,
        externally_pinned_review_tasks_sha256=externally_pinned_review_tasks_sha256,
        **source)
    native=verify_partial_native_drafts(
        origin=origin,checkpoint=checkpoint,review_tasks=review_tasks,
        cross_context_escrow=cross_context_escrow,
        draft=child_native_draft,
        externally_pinned_draft_sha256=externally_pinned_child_draft_sha256,
        externally_pinned_review_tasks_sha256=externally_pinned_review_tasks_sha256,
        **source)
    intake=verify_pending_child_review_intake(
        origin=origin,checkpoint=checkpoint,review_tasks=review_tasks,
        cross_context_escrow=cross_context_escrow,
        second_receipt=second_receipt,private_source_note=private_source_note,
        prequarantine=prequarantine,intake=pending_review_intake,
        externally_pinned_intake_sha256=externally_pinned_intake_sha256,
        externally_pinned_receipt_sha256=externally_pinned_receipt_sha256,
        externally_pinned_source_note_sha256=externally_pinned_source_note_sha256,
        externally_pinned_prequarantine_sha256=externally_pinned_prequarantine_sha256,
        externally_pinned_review_tasks_sha256=externally_pinned_review_tasks_sha256,
        **source)
    _need(task_coverage['child_count']==native['child_count']==intake['child_count']
          and task_coverage['parent_atom_count']==intake['atom_review_count'],
          'FULL_SOURCE_CHILD_INTAKE_CENSUS_DRIFT')
    baseline=knowledge_store.audit(externally_pinned_head=expected_knowledge_head_sha256)
    def held(reason):
        after=knowledge_store.audit(externally_pinned_head=expected_knowledge_head_sha256)
        _need(after==baseline,'HELD_E4_MUTATED_KNOWLEDGE')
        return {'schema':SCHEMA,'status':reason,
            'source_sha256':origin['source_sha256'],
            'review_task_count':task_coverage['child_count'],
            'reviewed_unapproved_atom_count':intake['atom_review_count'],
            'cross_child_pending_atoms':native['cross_atoms_waiting_for_semantics'],
            'child_v123_formal_approvals':0,
            'knowledge_head_sha256':expected_knowledge_head_sha256,
            'knowledge_changed':False,'e4_authorized':False,
            'e5_published':0,'host_user_turn_crypto_verified':False}
    if native['cross_atoms_waiting_for_semantics']:
        return held('HOLD_OPEN_CROSS_SCOPE_REATOMIZATION_BEFORE_E4')
    callbacks=(review_or_load_child,review_seams,review_parent,
               primary_manifest_for_child,typed_inventory_for_child,
               typed_manifest_for_child)
    if not all(callable(c) for c in callbacks) or now_as_of is None:
        return held('HOLD_V123_FINAL_REVIEWS_AND_E4_OFFICIAL_EVIDENCE_NOT_SUPPLIED')

    # Entirely separate from V235's unsealed historical research candidate
    # publication route. The FROZEN E4 gate validates each real V123 child,
    # official https source and applicability, writes a signed durable seal.
    result=run_e4_guarded_parent(
        checkpoint,knowledge_store,review_or_load_child=review_or_load_child,
        review_seams=review_seams,review_parent=review_parent,
        primary_manifest_for_child=primary_manifest_for_child,
        typed_inventory_for_child=typed_inventory_for_child,
        typed_manifest_for_child=typed_manifest_for_child,
        expected_knowledge_head=expected_knowledge_head_sha256,
        now_as_of=now_as_of)
    _need(type(result) is dict and result.get('schema')==
          'IRE_V166_E4_PARENT_APPROVAL_V1',
          'E4_NATIVE_RESULT_REQUIRED')
    published=result.get('all_video_knowledge_published') is True
    if not published:
        _need(knowledge_store.audit(
            externally_pinned_head=expected_knowledge_head_sha256)==baseline,
            'E4_HOLD_LEAKED_KNOWLEDGE')
        return held('E4_HOLD_OFFICIAL_PRIMARY_OR_CHAT_REVIEW')
    _need(result.get('status')=='E4_PARENT_RESEARCH_CANDIDATES_PUBLISHED'
          and result.get('e4_durable_certification_verified') is True,
          'E4_CERTIFICATION_MISSING_AFTER_PUBLICATION')
    seal=result.get('e4_external_owner_pin_sha256')
    _need(type(seal) is str and len(seal)==64,
          'E4_EXTERNAL_OWNER_SEAL_REQUIRED')
    # Important: a pin obtained DURING this run is NOT an external anchor.
    # It must be stored independently before approval is called final.
    return {'schema':SCHEMA,'status':'E4_RESEARCH_CANDIDATES_COMMITTED_OWNER_PIN_PENDING',
        'source_sha256':origin['source_sha256'],
        'e4_research_candidate_seal_sha256':seal,
        'e4_seal_verified_against_independent_owner_pin':False,
        'knowledge_changed':True,'e4_guarded_route_executed':True,
        'formal_financial_truth_certified':False,
        'e5_research_candidate_parent_committed':1,
        'e1_full_actual_final_pass':False}