"""V241: real, separately scoped V6 host staging for source-bound child drafts.

Fail closed BEFORE any SQLite write for a child with no fully local atoms.
All cross atoms remain in V237/V239 private review intake, not dropped or
approved.  Inventory digests here are operator-held, NOT signed owner IDs.
The only permitted write is V6 model/structural proof/REVIEW_PROPOSED.
"""
from __future__ import annotations
from copy import deepcopy

from ire.v6 import TransactionStore
from ire.v6.codec import canonical,json_digest,sha256
from ire.v6.errors import InvalidInput,QualityNotProven
from ire.v6.source import verify_source
from ire.v6.trust import verify_owner_inventory
from ire.v6.host_quarantine_preflight import audit_host_quarantine_preflight
from ire.v6.prior_knowledge import audit_prior_candidates
from ire.v6.proof import audit_model_anchors
from ire.v6.claim_census import FINANCIAL,QUALIFIER,MULTI_CLAIM
from v228_v193_actual_two_turn_runtime_gate import canonical as v228_canonical
from v231_e1_v228_private_turn2_custody_bridge import verify_real_turn2_private_custody
from v238_e1_child_native_scope_draft import verify_partial_native_drafts

SCHEMA='IRE_V241_E1_REAL_CHILD_V6_HOST_PREAUTHORIZED_STRUCTURAL_STAGE_V1'


def _need(ok,why):
    if not ok:raise InvalidInput('V241_E1_'+why)


def build_unapproved_child_host_case(*,origin,checkpoint,child_native_draft,review_tasks,
        cross_context_escrow,second_receipt,private_source_note,prequarantine,
        externally_pinned_child_draft_sha256,
        externally_pinned_review_tasks_sha256,
        externally_pinned_receipt_sha256,
        externally_pinned_source_note_sha256,
        externally_pinned_prequarantine_sha256,
        child_id:str,prior_knowledge:dict,
        **parent_pins):
    """Preflight all source, cross-link, prior+model+quarantine before writes."""
    verified=verify_partial_native_drafts(
        draft=child_native_draft,
        externally_pinned_draft_sha256=externally_pinned_child_draft_sha256,
        origin=origin,checkpoint=checkpoint,review_tasks=review_tasks,
        cross_context_escrow=cross_context_escrow,
        externally_pinned_review_tasks_sha256=externally_pinned_review_tasks_sha256,
        **parent_pins)
    verify_real_turn2_private_custody(
        origin=origin,second_receipt=second_receipt,private_source_note=private_source_note,
        prequarantine=prequarantine,
        externally_pinned_receipt_sha256=externally_pinned_receipt_sha256,
        externally_pinned_source_note_sha256=externally_pinned_source_note_sha256,
        externally_pinned_prequarantine_sha256=externally_pinned_prequarantine_sha256)
    _need(child_id in checkpoint.child_ids,'UNKNOWN_CHILD')
    index=checkpoint.child_ids.index(child_id)
    child=child_native_draft['child_drafts'][index]
    _need(child['segment_id']==child_id,'CHILD_ORDER_DRIFT')
    manifest=checkpoint.child_manifests[index]
    src=verify_source(origin['source_raw'],manifest,
        expected_source_sha256=parent_pins['externally_pinned_source_sha256'],
        expected_manifest_sha256=child['child_manifest_sha256'])
    exchange=child['native_draft_exchange']
    _need(child['native_draft_exchange_sha256']==json_digest(exchange),
          'CHILD_EXCHANGE_REPACKAGED')
    local=set(child['local_complete_atom_ids'])
    if not local:
        raise QualityNotProven('V241_E1_EMPTY_CHILD_LOCAL_ATOMS_REQUIRE_SOURCE_MEANING_REPAIR')
    scoped_models={};scoped_reviews={}
    for wid,_,_ in src.primary_windows:
        orig_model,orig_review=origin['models'][wid],origin['reviews'][wid]
        claims=[deepcopy(a) for a in orig_model['claims'] if a['claim_id'] in local]
        if not claims:
            # No invented claim just to appease V6's nonempty-window rule.
            raise QualityNotProven('V241_E1_EMPTY_WINDOW_REQUIRES_SOURCE_MEANING_REPAIR')
        model=dict(orig_model,claims=claims)
        review=dict(orig_review,reviewed_claim_ids=sorted(x['claim_id'] for x in claims))
        audit_model_anchors(src,wid,model,review)
        scoped_models[wid],scoped_reviews[wid]=model,review
    rows_by_id={x['cue_index']:x for x in
                second_receipt['turn2_review']['source_only_review_rows']}
    _need(len(rows_by_id)==origin['cue_count'],'TURN2_CUE_REVIEW_CENSUS')
    mandatory=[]
    for row in exchange['cue_dispositions']:
        idx=row['cue_index'];body=src.cues[idx-1].text
        is_risky=bool(FINANCIAL.search(body) or QUALIFIER.search(body)
                      or MULTI_CLAIM.search(body))
        if row['disposition']=='UNRESOLVED' or (
                row['disposition']=='NO_ATOM' and is_risky):
            reviewed=rows_by_id[idx]
            _need(reviewed.get('quote')==body and
                  reviewed.get('quote_sha256')==sha256(body.encode('utf-8')),
                  'CHILD_SOURCE_ONLY_REVIEW_QUOTE_DRIFT')
            mandatory.append({'cue_index':idx,
                'cue_text_sha256':sha256(body.encode('utf-8')),
                'reason_code':'OTHER_SOURCE_FIRST_RISK',
                'private_chat_cue_review_sha256':sha256(v228_canonical(reviewed)),
                'source_first_context_reviewed':True})
    child_quarantine=({'schema':'IRE_V6_HOST_SOURCE_PREQUARANTINE_V145',
        'source_sha256':src.source_sha256,
        'manifest_sha256':src.manifest_sha256,
        'review_executor':'CHATGPT_IN_CHAT',
        'private_review_sha256':externally_pinned_receipt_sha256,
        'cue_rows':mandatory,
        'audio_authenticity_verified':False,
        'semantic_claims_independently_verified':False,'p0_go':False}
        if mandatory else None)
    audit_host_quarantine_preflight(src,exchange,child_quarantine)
    _need(set(a['claim_id'] for a in exchange['atoms'])==local,
          'CHILD_ATOM_MODEL_MAPPING_LOSS')
    relations=[deepcopy(r) for r in prior_knowledge['relations'] if r['claim_id'] in local]
    knowledge={k:prior_knowledge[k] for k in
               ('master116_bytes','p4_22_bytes','p4_7_bytes')}
    knowledge['relations']=relations
    audit_prior_candidates(src,exchange,knowledge)
    registry={'schema':'IRE_V6_OWNER_INVENTORY_V1','entries':[{
        'video_id':src.video_id,'source_sha256':src.source_sha256,
        'manifest_sha256':src.manifest_sha256,
        'cue_census_sha256':src.cue_census_sha256}]}
    inventory_bytes=canonical(registry)
    # Derived inventory is inspectable from pinned V228 original; not a
    # cryptographically independent source owner attestation.
    return {'schema':SCHEMA,'segment_id':child_id,'source':src,
        'manifest':manifest,'source_raw':origin['source_raw'],
        'exchange':exchange,'models':scoped_models,'reviews':scoped_reviews,
        'knowledge':knowledge,'source_prequarantine':child_quarantine,
        'operator_inventory_bytes':inventory_bytes,
        'operator_inventory_digest_sha256':sha256(inventory_bytes),
        'parent_review_task_digest_sha256':child['cross_atom_source_review_sha256'],
        'parent_native_draft_exchange_sha256':child['native_draft_exchange_sha256'],
        'model_review_evidence_sha256':json_digest({'models':scoped_models,'reviews':scoped_reviews}),
        'original_local_atoms_staged':len(local),
        'original_cross_atoms_awaiting_meaning':len(child['cross_atom_ids_kept_in_parent_sidecar']),
        'unresolved_child_source_cues':len(mandatory),
        'owner_identity_cryptographically_verified':False,
        'e3_formal_approved':False,'e4_authorized':False,'e5_published':0}


def stage_child_host_only(*,case:dict,native_store:TransactionStore,
                          scope_id:str,run_id:str,
                          externally_operator_pinned_inventory_sha256:str,
                          explicit_unapproved_host_stage:bool=False)->dict:
    """No approved knowledge store is reachable from this function."""
    _need(explicit_unapproved_host_stage is True and
          type(native_store) is TransactionStore and
          type(case) is dict and case.get('schema')==SCHEMA,
          'EXPLICIT_OWNER_SCOPED_HOST_ONLY_STAGE_REQUIRED')
    _need(case['operator_inventory_digest_sha256']==
          externally_operator_pinned_inventory_sha256,
          'OPERATOR_HELD_CHILD_INVENTORY_PIN_MISMATCH')
    verify_owner_inventory(case['source_raw'],case['manifest'],
        case['operator_inventory_bytes'],
        expected_inventory_sha256=externally_operator_pinned_inventory_sha256)
    # Re-run *all* source-first checks at the final commit boundary.
    src=case['source'];exchange=case['exchange']
    _need(sha256(case['source_raw'])==src.source_sha256 and
          json_digest(case['manifest'])==src.manifest_sha256 and
          json_digest(exchange)==case['parent_native_draft_exchange_sha256'] and
          json_digest({'models':case['models'],'reviews':case['reviews']})==
              case['model_review_evidence_sha256'],
          'HOST_INPUT_CHANGED_AFTER_SOURCE_BOUND_PREFLIGHT')
    all_ids={a['claim_id']:a for a in exchange['atoms']}
    model_ids=set()
    for wid,model in case['models'].items():
        for claim in model['claims']:
            cid=claim['claim_id']
            _need(cid in all_ids and cid not in model_ids and
                  all(claim[k]==all_ids[cid][k] for k in
                      ('claim_id','owner_window_id','proposition','kind','source_refs')) and
                  all_ids[cid]['owner_window_id']==wid,
                  'STAGED_ATOM_MODEL_LINK_CHANGED')
            model_ids.add(cid)
    _need(model_ids==set(all_ids),'HOST_MODEL_ATOM_SET_DRIFT')
    audit_host_quarantine_preflight(src,exchange,case['source_prequarantine'])
    audit_prior_candidates(src,exchange,case['knowledge'])
    for wid in case['models']:
        audit_model_anchors(src,wid,case['models'][wid],case['reviews'][wid])
    c=native_store.create_scope(scope_id=scope_id,video_id=src.video_id,
        source_sha256=src.source_sha256,manifest_sha256=src.manifest_sha256,
        command_id='v241_source_native_child_create_scope')
    a=native_store.attest_source(scope_id=scope_id,
        command_id='v241_source_native_child_attest_source',
        expected_head=c['event_sha256'],raw=case['source_raw'],manifest=case['manifest'])
    b=native_store.attest_owner_inventory(scope_id=scope_id,
        command_id='v241_source_native_child_operator_inventory',
        expected_head=a['event_sha256'],raw=case['source_raw'],manifest=case['manifest'],
        inventory_bytes=case['operator_inventory_bytes'],
        expected_inventory_sha256=externally_operator_pinned_inventory_sha256)
    result=native_store.submit_host_atomic_batch(
        scope_id=scope_id,run_id=run_id,expected_head=b['event_sha256'],
        raw=case['source_raw'],manifest=case['manifest'],
        inventory_bytes=case['operator_inventory_bytes'],
        expected_inventory_sha256=externally_operator_pinned_inventory_sha256,
        exchange=exchange,knowledge=case['knowledge'],
        window_models=case['models'],window_reviews=case['reviews'],
        quarantine_preflight=case['source_prequarantine'])
    _need(result['atomic_batch_committed'] is True and
          result['semantic_truth_certified'] is False,
          'CHILD_HOST_NOT_STAGED_OR_FALSE_SEMANTIC_APPROVAL')
    after=TransactionStore(native_store.path).snapshot(scope_id)
    _need(after['ledger_head_sha256']==result['event_sha256'] and
          after['progress']['verified_proofs']==0 and
          not after['progress']['research_report_closed'],
          'CHILD_HOST_REOPENED_NONPENDING_STATE')
    return {'schema':SCHEMA,'status':'REAL_CHILD_SOURCE_NATIVE_HOST_STAGED_UNAPPROVED',
        'segment_id':case['segment_id'],'source_sha256':src.source_sha256,
        'child_manifest_sha256':src.manifest_sha256,
        'host_event_sha256':result['event_sha256'],
        'host_bundle_sha256':result['bundle_sha256'],
        'local_atoms_staged':case['original_local_atoms_staged'],
        'cross_atoms_remain_open':case['original_cross_atoms_awaiting_meaning'],
        'original_source_cues_quarantined':case['unresolved_child_source_cues'],
        'operator_inventory_sha256':externally_operator_pinned_inventory_sha256,
        'independent_owner_signature_proven':False,
        'v123_final_approved':False,'e4_authorized':False,'e5_published':0}