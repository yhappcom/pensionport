"""V242 — a parent-qualified *provisional* child V6 structural host bridge.

This never asserts that stripping a cross-child condition is semantically valid.
The full frozen parent atom and each external condition remains independently
source-pinned in a non-approving parent-qualifier envelope. The partial child
projection is useful ONLY for V6 structural staging. Formal E3/E4/E5 release
must consume/resolve that envelope separately; this code cannot publish.
"""
from __future__ import annotations

from copy import deepcopy

from ire.v6 import TransactionStore
from ire.v6.atomic_exchange import audit_host_atomic_exchange
from ire.v6.claim_census import FINANCIAL, QUALIFIER, MULTI_CLAIM
from ire.v6.codec import canonical, json_digest, sha256
from ire.v6.errors import InvalidInput, QualityNotProven
from ire.v6.host_quarantine_preflight import audit_host_quarantine_preflight
from ire.v6.prior_knowledge import audit_prior_candidates
from ire.v6.proof import audit_model_anchors
from ire.v6.source import verify_source
from v228_v193_actual_two_turn_runtime_gate import canonical as v228_canonical
from v231_e1_v228_private_turn2_custody_bridge import verify_real_turn2_private_custody
from v238_e1_child_native_scope_draft import verify_partial_native_drafts
from v241_e1_unapproved_child_host_writer import (
    SCHEMA as V241_CASE_SCHEMA, stage_child_host_only,
)

SCHEMA = 'IRE_V242_E1_PARENT_QUALIFIER_PENDING_CHILD_PROJECTION_V1'


def _need(condition, reason):
    if not condition:
        raise InvalidInput('V242_E1_' + reason)


def build_condition_linked_provisional_case(*, origin: dict, checkpoint,
        child_native_draft: dict, review_tasks: dict, cross_context_escrow: dict,
        second_receipt: dict, private_source_note: dict, prequarantine: dict,
        externally_pinned_child_draft_sha256: str,
        externally_pinned_review_tasks_sha256: str,
        externally_pinned_receipt_sha256: str,
        externally_pinned_source_note_sha256: str,
        externally_pinned_prequarantine_sha256: str,
        child_id: str, claim_id: str, prior_knowledge: dict, **parent_pins):
    """Re-derive source-linked child + external-qualifier envelope before writes.

    Allows only a single pending parent atom and only conditions/context external
    to the child. Cross-source quote/numeric/exception dependencies stay HOLD.
    """
    verify_partial_native_drafts(
        draft=child_native_draft,
        externally_pinned_draft_sha256=externally_pinned_child_draft_sha256,
        origin=origin, checkpoint=checkpoint, review_tasks=review_tasks,
        cross_context_escrow=cross_context_escrow,
        externally_pinned_review_tasks_sha256=externally_pinned_review_tasks_sha256,
        **parent_pins)
    verify_real_turn2_private_custody(
        origin=origin, second_receipt=second_receipt,
        private_source_note=private_source_note, prequarantine=prequarantine,
        externally_pinned_receipt_sha256=externally_pinned_receipt_sha256,
        externally_pinned_source_note_sha256=externally_pinned_source_note_sha256,
        externally_pinned_prequarantine_sha256=externally_pinned_prequarantine_sha256)
    _need(child_id in checkpoint.child_ids, 'UNKNOWN_CHILD')
    ix=checkpoint.child_ids.index(child_id)
    draft=child_native_draft['child_drafts'][ix]
    task=review_tasks['child_tasks'][ix]
    manifest=checkpoint.child_manifests[ix]
    _need(draft['segment_id']==child_id==task['segment_id'] and
          draft['child_manifest_sha256']==json_digest(manifest) and
          task['manifest_sha256']==json_digest(manifest),
          'CHILD_MANIFEST_OR_REVIEW_TASK_DRIFT')
    # Require actual prior failure mechanism, not permission to rewrite any atom.
    _need(not draft['local_complete_atom_ids'] and
          draft['cross_atom_ids_kept_in_parent_sidecar']==[claim_id] and
          len(task['atom_review_tasks'])==1 and
          task['atom_review_tasks'][0]['claim_id']==claim_id,
          'NOT_SINGLE_PENDING_EXTERNAL_QUALIFIER_CHILD')
    parent=next((a for a in origin['exchange']['atoms'] if a['claim_id']==claim_id),None)
    _need(parent is not None and
          task['atom_review_tasks'][0]['parent_atom']==parent and
          task['atom_review_tasks'][0]['parent_atom_sha256']==json_digest(parent),
          'PARENT_ATOM_PIN_MISMATCH')
    _need(parent['speaker']=='UNKNOWN' and parent['stance']=='UNRESOLVED' and
          task['atom_review_tasks'][0]['formal_v123_verdict'] is None and
          task['atom_review_tasks'][0]['e4_authorized'] is False,
          'PROVISIONAL_UNKNOWN_UNRESOLVED_ONLY')
    source=verify_source(origin['source_raw'],manifest,
        expected_source_sha256=parent_pins['externally_pinned_source_sha256'],
        expected_manifest_sha256=draft['child_manifest_sha256'])
    first,last=manifest['scope']['first_cue'],manifest['scope']['last_cue']
    inside=set(range(first,last+1))
    original_ref_indices={r['cue_index'] for r in parent['source_refs']}
    condition=set(parent['condition_cue_indices'])
    context=set(parent['context_cue_indices'])
    exceptions=set(parent['exception_cue_indices'])
    number_indices={n['cue_index'] for n in parent['numeric_references']}
    outside=context-inside
    _need(original_ref_indices and original_ref_indices.issubset(inside) and
          exceptions.issubset(inside) and number_indices.issubset(inside) and
          outside and outside.issubset(condition) and
          (condition&inside) and original_ref_indices.issubset(context) and
          condition.issubset(context),
          'CROSS_PRIMARY_NUMERIC_EXCEPTION_OR_NONQUALIFIER_BLOCKED')
    links=task['atom_review_tasks'][0]['source_context_references']
    ext_rows=[x for x in links if x['external_to_owner_child']]
    _need({x['cue_index'] for x in ext_rows}==outside and
          len(ext_rows)==len(outside), 'EXTERNAL_CUE_CENSUS')
    for row in ext_rows:
        idx=row['cue_index']
        _need(row['source_child_id']!=child_id and
              set(row['roles'])=={'CONTEXT','CONDITION'} and
              row['quote']==origin['source'].cues[idx-1].text and
              row['quote_sha256']==sha256(row['quote'].encode('utf-8')) and
              not row['numeric_tokens'] and not row['source_quote_spans'],
              'EXTERNAL_QUALIFIER_ROLE_OR_BYTES_DRIFT')
    # Build a deliberately incomplete child-local view; the original full atom
    # is still required by the sidecar at *every* later semantic release gate.
    provisional=deepcopy(parent)
    provisional['context_cue_indices']=sorted(context&inside)
    provisional['condition_cue_indices']=sorted(condition&inside)
    _need(len(provisional['condition_cue_indices'])>0,
          'NO_LOCAL_QUALIFIER_ANCHOR')
    reconstructed=deepcopy(provisional)
    reconstructed['context_cue_indices']=sorted(set(provisional['context_cue_indices'])|outside)
    reconstructed['condition_cue_indices']=sorted(set(provisional['condition_cue_indices'])|outside)
    _need(reconstructed==parent,'PARENT_ATOM_NOT_EXACTLY_RECONSTRUCTABLE')
    exchange=deepcopy(draft['native_draft_exchange'])
    _need(exchange['atoms']==[],'EXISTING_CHILD_PROJECTION_NOT_EMPTY')
    exchange['atoms']=[provisional]
    source_cues=sorted(original_ref_indices)
    for row in exchange['cue_dispositions']:
        if row['cue_index'] in original_ref_indices:
            parent_row=origin['exchange']['cue_dispositions'][row['cue_index']-1]
            _need(parent_row['disposition']=='CANDIDATES' and
                  parent_row['claim_ids']==[claim_id] and
                  row['disposition']=='UNRESOLVED' and not row['claim_ids'],
                  'LOCAL_CANDIDATE_SOURCE_OR_DISPOSITION_CHANGED')
            row.update(deepcopy(parent_row))
    audited=audit_host_atomic_exchange(source,exchange)
    _need(audited['proposed_atomic_claims']==1, 'PROVISIONAL_ATOM_AUDIT_COUNT')
    window=parent['owner_window_id']
    _need(list(origin['models']) and window in origin['models'],
          'PARENT_MODEL_MISSING')
    model=deepcopy(origin['models'][window]);review=deepcopy(origin['reviews'][window])
    _need([x['claim_id'] for x in model['claims']]==[claim_id] and
          review['reviewed_claim_ids']==[claim_id],
          'PARENT_MODEL_CLAIM_ID_MISMATCH')
    audit_model_anchors(source,window,model,review)
    review_rows={x['cue_index']:x for x in
                 second_receipt['turn2_review']['source_only_review_rows']}
    _need(len(review_rows)==origin['cue_count'],'TURN2_CUE_ROWS_INCOMPLETE')
    mandatory=[]
    for row in exchange['cue_dispositions']:
        idx=row['cue_index'];body=source.cues[idx-1].text
        risky=bool(FINANCIAL.search(body) or QUALIFIER.search(body)
                   or MULTI_CLAIM.search(body))
        if row['disposition']=='UNRESOLVED' or (
                row['disposition']=='NO_ATOM' and risky):
            rev=review_rows[idx]
            _need(rev.get('quote')==body and
                  rev.get('quote_sha256')==sha256(body.encode('utf-8')),
                  'TURN2_SOURCE_NOTE_QUOTE_CHANGED')
            mandatory.append({'cue_index':idx,
                'cue_text_sha256':sha256(body.encode('utf-8')),
                'reason_code':'OTHER_SOURCE_FIRST_RISK',
                'private_chat_cue_review_sha256':sha256(v228_canonical(rev)),
                'source_first_context_reviewed':True})
    quarantine=({
        'schema':'IRE_V6_HOST_SOURCE_PREQUARANTINE_V145',
        'source_sha256':source.source_sha256,
        'manifest_sha256':source.manifest_sha256,
        'review_executor':'CHATGPT_IN_CHAT',
        'private_review_sha256':externally_pinned_receipt_sha256,
        'cue_rows':mandatory,
        'audio_authenticity_verified':False,
        'semantic_claims_independently_verified':False,'p0_go':False}
        if mandatory else None)
    audit_host_quarantine_preflight(source,exchange,quarantine)
    relations=[deepcopy(r) for r in prior_knowledge['relations']
               if r['claim_id']==claim_id]
    knowledge={k:prior_knowledge[k] for k in
               ('master116_bytes','p4_22_bytes','p4_7_bytes')}
    knowledge['relations']=relations
    audit_prior_candidates(source,exchange,knowledge)
    registry={'schema':'IRE_V6_OWNER_INVENTORY_V1','entries':[
        {'video_id':source.video_id,'source_sha256':source.source_sha256,
         'manifest_sha256':source.manifest_sha256,
         'cue_census_sha256':source.cue_census_sha256}]}
    registry_bytes=canonical(registry)
    provenance={'schema':SCHEMA,'status':'PARENT_EXTERNAL_QUALIFIER_PENDING',
        'child_id':child_id, 'claim_id':claim_id,
        'original_parent_atom_sha256':json_digest(parent),
        'original_parent_exchange_sha256':origin['native_exchange_digest'],
        'source_sha256':source.source_sha256,
        'child_manifest_sha256':source.manifest_sha256,
        'review_task_sha256':json_digest(task),
        'original_cross_context_escrow_sha256':parent_pins['externally_pinned_escrow_sha256'],
        'child_provisional_atom_sha256':json_digest(provisional),
        'original_external_condition_cues':deepcopy(ext_rows),
        'reconstructs_full_original_atom':True,
        'requires_e3_parent_condition_review':True,
        'child_local_semantics_certified':False,
        'parent_qualifier_semantics_certified':False,
        'e3_final_approved':False,'e4_authorized':False,'e5_published':0}
    case={'schema':V241_CASE_SCHEMA,'segment_id':child_id,
        'source':source,'manifest':manifest,'source_raw':origin['source_raw'],
        'exchange':exchange,'models':{window:model},'reviews':{window:review},
        'knowledge':knowledge,'source_prequarantine':quarantine,
        'operator_inventory_bytes':registry_bytes,
        'operator_inventory_digest_sha256':sha256(registry_bytes),
        'parent_review_task_digest_sha256':json_digest(task),
        'parent_native_draft_exchange_sha256':json_digest(exchange),
        'model_review_evidence_sha256':json_digest({'models':{window:model},'reviews':{window:review}}),
        'original_local_atoms_staged':0,
        'original_cross_atoms_awaiting_meaning':1,
        'unresolved_child_source_cues':len(mandatory),
        'owner_identity_cryptographically_verified':False,
        'e3_formal_approved':False,'e4_authorized':False,'e5_published':0}
    return {'case':case,'provenance':provenance}


def stage_verified_condition_linked_host(*, externally_pinned_provenance_sha256:str,
        native_store:TransactionStore,scope_id:str,run_id:str,
        explicit_provisional_host_stage:bool=False,
        externally_operator_pinned_inventory_sha256:str,
        **source_bound_args):
    """Source/parent/projection re-verification before V6 structural write only."""
    _need(explicit_provisional_host_stage is True and
          type(native_store) is TransactionStore,
          'EXPLICIT_PROVISIONAL_STRUCTURAL_ONLY_PERMISSION_REQUIRED')
    result=build_condition_linked_provisional_case(**source_bound_args)
    case,link=result['case'],result['provenance']
    _need(json_digest(link)==externally_pinned_provenance_sha256,
          'PARENT_QUALIFIER_ESCROW_PIN_MISMATCH')
    _need(link['e3_final_approved'] is False and
          link['e4_authorized'] is False and
          link['e5_published']==0 and
          link['requires_e3_parent_condition_review'] is True,
          'UNAUTHORIZED_FULL_MEANING_AUTHORITY')
    output=stage_child_host_only(
        case=case,native_store=native_store,scope_id=scope_id,run_id=run_id,
        externally_operator_pinned_inventory_sha256=externally_operator_pinned_inventory_sha256,
        explicit_unapproved_host_stage=True)
    _need(output['host_event_sha256'] and output['v123_final_approved'] is False
          and output['e4_authorized'] is False and output['e5_published']==0,
          'STAGING_DID_NOT_REMAIN_UNAPPROVED')
    return {'schema':SCHEMA,'status':'STRUCTURAL_PROVISIONAL_CHILD_HOST_COMMITTED',
        'segment_id':link['child_id'],'claim_id':link['claim_id'],
        'host_event_sha256':output['host_event_sha256'],
        'parent_qualifier_provenance_sha256':json_digest(link),
        'external_condition_cues_preserved':len(link['original_external_condition_cues']),
        'full_original_atom_verified_against_provisional_projection':True,
        'prior_owner_signature_verified':False,'formal_e3_review_approved':False,
        'e4_authorized':False,'e5_published':0}