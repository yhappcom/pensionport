"""V239: bind existing distinct-turn internal semantic notes to 13 child tasks.

This is review *intake*, not a new ChatGPT turn, final V123 verdict, gold
reference or source-authority certificate.  It allows review work to reach
child scopes despite cross-context refs. Every unresolved finding stays OPEN.
"""
from __future__ import annotations

from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from v228_v193_actual_two_turn_runtime_gate import canonical as v228_canonical
from v231_e1_v228_private_turn2_custody_bridge import verify_real_turn2_private_custody
from v237_e1_parent_child_review_contract import verify_child_review_tasks

SCHEMA = "IRE_V239_E1_DISTINCT_TURN_CHILD_INTAKE_PENDING_V1"


def _need(ok,code):
    if not ok: raise InvalidInput('V239_E1_'+code)


def build_pending_child_review_intake(*,origin:dict,review_tasks:dict,
        checkpoint,cross_context_escrow:dict,
        externally_pinned_review_tasks_sha256:str,
        second_receipt:dict,private_source_note:dict,prequarantine:dict,
        externally_pinned_receipt_sha256:str,
        externally_pinned_source_note_sha256:str,
        externally_pinned_prequarantine_sha256:str,**source_args):
    tasks_check=verify_child_review_tasks(
        review_tasks=review_tasks,
        externally_pinned_review_tasks_sha256=externally_pinned_review_tasks_sha256,
        origin=origin,checkpoint=checkpoint,cross_context_escrow=cross_context_escrow,
        **source_args)
    custody=verify_real_turn2_private_custody(
        origin=origin,second_receipt=second_receipt,
        private_source_note=private_source_note,prequarantine=prequarantine,
        externally_pinned_receipt_sha256=externally_pinned_receipt_sha256,
        externally_pinned_source_note_sha256=externally_pinned_source_note_sha256,
        externally_pinned_prequarantine_sha256=externally_pinned_prequarantine_sha256)
    reviews=second_receipt['turn2_review']['atom_adjudication_rows']
    by_id={r['claim_id']:r for r in reviews}
    _need(len(by_id)==len(reviews)==review_tasks['parent_atom_count'],
          'TURN2_ATOM_REVIEWS_INCOMPLETE_OR_DUPLICATE')
    rows=[];seen=set();cross_repair=0;cross_hold=0
    for task in review_tasks['child_tasks']:
        findings=[]
        for atom in task['atom_review_tasks']:
            cid=atom['claim_id'];_need(cid not in seen and cid in by_id,
                                      'CHILD_ATOM_REVIEW_MISSING_OR_DUPLICATE')
            seen.add(cid);r=by_id[cid]
            _need(r.get('e3_final_approved') is False and
                  r.get('financial_fact_approved') is False and
                  r.get('independent_gold_certified') is False,
                  'SECOND_TURN_FALSE_AUTHORITY')
            status=r['disposition']
            is_cross=atom['requires_cross_child_semantic_review']
            cross_repair += int(is_cross and status=='REQUIRES_SOURCE_MEANING_REPAIR')
            cross_hold += int(is_cross and status!='REQUIRES_SOURCE_MEANING_REPAIR')
            findings.append({'claim_id':cid,
                'parent_atom_sha256':atom['parent_atom_sha256'],
                'turn2_atom_review_sha256':sha256(v228_canonical(r)),
                'turn2_reason':r['source_grounded_reason'],
                'turn2_disposition':status,
                'cross_child_context_source_bound':is_cross,
                'formal_v123_chat_final_verdict':None,
                'needs_financial_evidence_and_semantic_repair':True,
                'approval_permission_granted':False})
        rows.append({'segment_id':task['segment_id'],
            'source_review_task_sha256':json_digest(task),
            'child_findings':findings,'real_v123_formal_child_approved':False})
    _need(seen==set(by_id),'TURN2_CHILD_ATOM_CENSUS_LOSS')
    _need(cross_repair+cross_hold==tasks_check['cross_segment_atom_count'],
          'CROSS_CHILD_TURN2_CENSUS_LOSS')
    return {'schema':SCHEMA,'status':'DISTINCT_TURN_INTERNAL_REVIEW_ROUTED_TO_ALL_CHILDREN_V123_HOLD',
        'source_sha256':origin['source_sha256'],
        'parent_plan_sha256':checkpoint.plan_pin,
        'second_receipt_sha256':externally_pinned_receipt_sha256,
        'private_source_note_sha256':externally_pinned_source_note_sha256,
        'prequarantine_sha256':externally_pinned_prequarantine_sha256,
        'review_tasks_sha256':externally_pinned_review_tasks_sha256,
        'child_count':len(rows),'atom_review_count':len(seen),
        'cross_atom_review_count':cross_repair+cross_hold,
        'cross_atom_requires_repair':cross_repair,
        'cross_atom_hold_or_other':cross_hold,
        'child_findings':rows,
        'distinct_turn_reference_manually_observed':True,
        'host_turn_cryptographic_authentication':False,
        'e3_formal_child_approvals':0,'e4_authorized':False,'e5_published':0}


def verify_pending_child_review_intake(*,intake:dict,
                                       externally_pinned_intake_sha256:str,**inputs):
    _need(type(intake) is dict and json_digest(intake)==externally_pinned_intake_sha256,
          'INTAKE_DIGEST_PIN_MISMATCH')
    expected=build_pending_child_review_intake(**inputs)
    _need(intake==expected,'SOURCE_OR_SECOND_TURN_REVIEW_INTAKE_MUTATED')
    return {'status':'V239_ALL_DISTINCT_TURN_NOTES_SOURCE_BOUND_NO_APPROVAL',
            'child_count':expected['child_count'],
            'atom_review_count':expected['atom_review_count'],
            'cross_atom_review_count':expected['cross_atom_review_count'],
            'formal_v123_approvals':0,'e4_authorized':False,'e5_published':0}