"""V242: native structural custody for an empty-local child with inherited cues.

Only a source-anchored, UNRESOLVED local *view* is put in the native V6 host.
The FULL parent atom and external qualifier still reside in a hash-pinned
cross-scope evidence envelope. Neither this view nor its V6 receipt is an E3
final decision, a lossless V123 atom, or E4/E5 release authority.

No change to frozen V6 grammar or existing V241 child databases is necessary.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from ire.v6 import TransactionStore
from ire.v6.atomic_exchange import audit_host_atomic_exchange
from ire.v6.codec import canonical, json_digest, sha256
from ire.v6.errors import InvalidInput, QualityNotProven
from ire.v6.host_quarantine_preflight import audit_host_quarantine_preflight
from ire.v6.prior_knowledge import audit_prior_candidates
from ire.v6.proof import audit_model_anchors
from ire.v6.source import verify_source
from ire.v6.trust import verify_owner_inventory
from ire.v6.claim_census import FINANCIAL, QUALIFIER, MULTI_CLAIM
from v228_v193_actual_two_turn_runtime_gate import canonical as v228_canonical
from v231_e1_v228_private_turn2_custody_bridge import verify_real_turn2_private_custody
from v238_e1_child_native_scope_draft import verify_partial_native_drafts
from v241_e1_unapproved_child_host_writer import SCHEMA as V241_SCHEMA, stage_child_host_only

SCHEMA = 'IRE_V242_E1_UNAPPROVED_LOCAL_ANCHOR_WITH_INHERITED_CONDITIONS_V1'


def _need(condition, reason):
    if not condition:
        raise InvalidInput('V242_E1_' + reason)


def build_pending_cross_child_host_case(*, origin, checkpoint, child_native_draft,
        review_tasks, cross_context_escrow, second_receipt, private_source_note,
        prequarantine, prior_knowledge, child_id,
        externally_pinned_child_draft_sha256,
        externally_pinned_review_tasks_sha256,
        externally_pinned_receipt_sha256,
        externally_pinned_source_note_sha256,
        externally_pinned_prequarantine_sha256,
        **parent_pins):
    """Preflight exact original source and every external edge, no SQLite write.

    This is intentionally limited: one cross-atom, all primary quotes local,
    outside references ONLY CONTEXT/CONDITION (no numbers/exceptions), and
    the source stance stays UNRESOLVED. Never silently split other cases.
    """
    verified=verify_partial_native_drafts(
        draft=child_native_draft,
        externally_pinned_draft_sha256=externally_pinned_child_draft_sha256,
        origin=origin, checkpoint=checkpoint, review_tasks=review_tasks,
        cross_context_escrow=cross_context_escrow,
        externally_pinned_review_tasks_sha256=externally_pinned_review_tasks_sha256,
        **parent_pins)
    verify_real_turn2_private_custody(
        origin=origin,second_receipt=second_receipt,
        private_source_note=private_source_note,prequarantine=prequarantine,
        externally_pinned_receipt_sha256=externally_pinned_receipt_sha256,
        externally_pinned_source_note_sha256=externally_pinned_source_note_sha256,
        externally_pinned_prequarantine_sha256=externally_pinned_prequarantine_sha256)
    _need(verified['child_count']==len(checkpoint.child_ids), 'CHILD_SCOPE_CENSUS')
    _need(child_id in checkpoint.child_ids, 'UNKNOWN_CHILD')
    i=checkpoint.child_ids.index(child_id)
    draft=child_native_draft['child_drafts'][i]
    task=review_tasks['child_tasks'][i]
    manifest=checkpoint.child_manifests[i]
    _need(draft['segment_id']==child_id and task['segment_id']==child_id and
          not draft['local_complete_atom_ids'] and
          len(draft['cross_atom_ids_kept_in_parent_sidecar'])==1 and
          len(task['atom_review_tasks'])==1, 'ONLY_ONE_EMPTY_CROSS_CHILD_ALLOWED')
    cid=draft['cross_atom_ids_kept_in_parent_sidecar'][0]
    match=task['atom_review_tasks'][0]
    _need(cid==match['claim_id'] and
          match['requires_cross_child_semantic_review'] is True and
          match['formal_v123_verdict'] is None and
          match['e4_authorized'] is False, 'CROSS_REVIEW_NOT_OPEN')
    parents=[a for a in origin['exchange']['atoms'] if a['claim_id']==cid]
    _need(len(parents)==1 and match['parent_atom']==parents[0] and
          match['parent_atom_sha256']==json_digest(parents[0]), 'PARENT_ATOM_SHA_OR_REVIEW_DRIFT')
    atom=parents[0]
    first,last=manifest['scope']['first_cue'],manifest['scope']['last_cue']
    inside=set(range(first,last+1))
    _need(atom['stance']=='UNRESOLVED' and atom['speaker'] in ('UNKNOWN','NARRATOR','GUEST','QUESTIONER') and
          atom['source_refs'] and all(r['cue_index'] in inside for r in atom['source_refs']) and
          all(n['cue_index'] in inside for n in atom['numeric_references']) and
          all(x in inside for x in atom['exception_cue_indices']),
          'NONLOCAL_PRIMARY_EXCEPTION_OR_NUMERIC_MUST_REMAIN_HOLD')
    outside=sorted(set(atom['context_cue_indices'])-inside)
    _need(bool(outside) and set(outside).issubset(set(atom['condition_cue_indices'])) and
          set(atom['condition_cue_indices']).issubset(set(atom['context_cue_indices'])),
          'OUTSIDE_ONLY_INHERITED_CONDITIONS_ALLOWED')
    _need(len(atom['context_cue_indices'])-len(outside)>0 and
          all(a['cue_index'] in atom['context_cue_indices'] for a in atom['source_refs']),
          'LOCAL_PRIMARY_CONTEXT_REQUIRED')
    external=[r for r in match['source_context_references'] if r['external_to_owner_child']]
    _need([r['cue_index'] for r in external]==outside and
          all(set(r['roles'])=={'CONTEXT','CONDITION'} and
              r['quote']==origin['source'].cues[r['cue_index']-1].text and
              r['quote_sha256']==sha256(r['quote'].encode('utf-8')) and
              r['source_child_id']!=child_id for r in external),
          'EXTERNAL_CONDITION_QUOTE_OR_ROLE_DRIFT')
    escrow=[r for r in cross_context_escrow['cross_segment_atom_rows']
            if r['claim_id']==cid]
    _need(len(escrow)==1 and escrow[0]['original_atom_sha256']==json_digest(atom) and
          escrow[0]['primary_segment_id']==child_id and
          escrow[0]['meaning_approved'] is False and
          escrow[0]['finance_approved'] is False and
          escrow[0]['status']=='OPEN_REQUIRES_CHATGPT_CROSS_SCOPE_SOURCE_SEMANTIC_REVIEW',
          'PARENT_ESCROW_NOT_OPEN_OR_MISMATCH')
    src=verify_source(origin['source_raw'],manifest,
        expected_source_sha256=parent_pins['externally_pinned_source_sha256'],
        expected_manifest_sha256=draft['child_manifest_sha256'])
    local=deepcopy(atom)
    local['context_cue_indices']=[n for n in atom['context_cue_indices'] if n in inside]
    local['condition_cue_indices']=[n for n in atom['condition_cue_indices'] if n in inside]
    # Every field other than inherited cue lists remains byte-for-byte original.
    _need(local['source_refs']==atom['source_refs'] and
          local['proposition']==atom['proposition'] and
          local['stance']=='UNRESOLVED' and local['kind']==atom['kind'],
          'LOCAL_ONLY_VIEW_CHANGED_OR_APPROVED')
    exchange=deepcopy(draft['native_draft_exchange'])
    _need(not exchange['atoms'], 'PARENT_DRAFT_ALREADY_HAS_ATOMS')
    exchange['atoms']=[local]
    primary=set(r['cue_index'] for r in atom['source_refs'])
    original_rows={r['cue_index']:r for r in origin['exchange']['cue_dispositions']}
    for r in exchange['cue_dispositions']:
        if r['cue_index'] in primary:
            parent=original_rows[r['cue_index']]
            _need(parent['disposition']=='CANDIDATES' and cid in parent['claim_ids'] and
                  set(parent['claim_ids'])=={cid}, 'PRIMARY_CUE_HAS_DIFFERENT_PARENT_CANDIDATE')
            r.update(disposition='CANDIDATES',claim_ids=[cid],note=parent['note'])
    audit=audit_host_atomic_exchange(src,exchange)
    _need(audit['proposed_atomic_claims']==1 and
          audit['semantic_claims_independently_verified'] is False and
          audit['p0_go'] is False, 'VIEW_COULD_BE_TREATED_AS_APPROVED')
    wid=atom['owner_window_id']
    _need(set(w for w,_,_ in src.primary_windows)=={wid},'EXACTLY_ONE_SOURCE_WINDOW')
    model=deepcopy(origin['models'][wid]);review=deepcopy(origin['reviews'][wid])
    _need([c['claim_id'] for c in model['claims']]==[cid] and
          review['reviewed_claim_ids']==[cid] and
          review['independent_gold_verified'] is False,
          'PARENT_WINDOW_MODEL_REVIEW_REWRITTEN')
    audit_model_anchors(src,wid,model,review)
    # Same original verified source-only turn review; not a new ChatGPT decision.
    by_idx={r['cue_index']:r for r in second_receipt['turn2_review']['source_only_review_rows']}
    mandatory=[]
    for row in exchange['cue_dispositions']:
        idx=row['cue_index'];cue=src.cues[idx-1].text
        risk=bool(FINANCIAL.search(cue) or QUALIFIER.search(cue) or MULTI_CLAIM.search(cue))
        if row['disposition']=='UNRESOLVED' or (row['disposition']=='NO_ATOM' and risk):
            reviewed=by_idx.get(idx)
            _need(reviewed is not None and reviewed['quote']==cue and
                  reviewed['quote_sha256']==sha256(cue.encode('utf-8')),
                  'CHILD_SOURCE_FIRST_REVIEW_DRIFT')
            mandatory.append({'cue_index':idx,'cue_text_sha256':sha256(cue.encode('utf-8')),
                'reason_code':'OTHER_SOURCE_FIRST_RISK',
                'private_chat_cue_review_sha256':sha256(v228_canonical(reviewed)),
                'source_first_context_reviewed':True})
    quarantine={'schema':'IRE_V6_HOST_SOURCE_PREQUARANTINE_V145',
        'source_sha256':src.source_sha256,'manifest_sha256':src.manifest_sha256,
        'review_executor':'CHATGPT_IN_CHAT',
        'private_review_sha256':externally_pinned_receipt_sha256,
        'cue_rows':mandatory,'audio_authenticity_verified':False,
        'semantic_claims_independently_verified':False,'p0_go':False} if mandatory else None
    audit_host_quarantine_preflight(src,exchange,quarantine)
    rows=[deepcopy(x) for x in prior_knowledge['relations'] if x['claim_id']==cid]
    _need(len(rows)==1 and rows[0]['relationship'] in ('OPEN','NOVEL_PENDING') and
          rows[0]['independent_semantic_review_verified'] is False and
          rows[0]['personalized_action_approved'] is False,
          'PRIOR_RELATION_NOT_OPEN')
    knowledge={k:prior_knowledge[k] for k in ('master116_bytes','p4_22_bytes','p4_7_bytes')}
    knowledge['relations']=rows
    audit_prior_candidates(src,exchange,knowledge)
    inventory={'schema':'IRE_V6_OWNER_INVENTORY_V1','entries':[{
        'video_id':src.video_id,'source_sha256':src.source_sha256,
        'manifest_sha256':src.manifest_sha256,'cue_census_sha256':src.cue_census_sha256}]}
    inventory_bytes=canonical(inventory)
    verify_owner_inventory(origin['source_raw'],manifest,inventory_bytes,
        expected_inventory_sha256=sha256(inventory_bytes))
    # This portable packet retains the full ORIGINAL claim and every external
    # source quote: local-only view is never a valid V123/E4 review without it.
    binding={'schema':SCHEMA,'segment_id':child_id,'claim_id':cid,
        'source_sha256':src.source_sha256,
        'child_manifest_sha256':src.manifest_sha256,
        'parent_plan_sha256':checkpoint.plan_pin,
        'parent_exchange_sha256':json_digest(origin['exchange']),
        'parent_atom_sha256':json_digest(atom),
        'parent_atom':deepcopy(atom),
        'local_only_provisional_atom_sha256':json_digest(local),
        'parent_escrow_sha256':parent_pins['externally_pinned_escrow_sha256'],
        'review_tasks_sha256':externally_pinned_review_tasks_sha256,
        'child_native_draft_sha256':externally_pinned_child_draft_sha256,
        'turn2_internal_unapproved_sha256':externally_pinned_receipt_sha256,
        'external_cues':deepcopy(external),
        'dropped_only_in_native_local_view':outside,
        'local_context_indices':local['context_cue_indices'],
        'local_condition_indices':local['condition_cue_indices'],
        'must_recombine_parent_conditions_before_v123_e4':True,
        'eligible_for_formal_semantic_approval':False,
        'independent_gold_verified':False,'e4_authorized':False,'e5_published':0}
    digest=json_digest(binding)
    case={'schema':V241_SCHEMA,'segment_id':child_id,'source':src,
        'source_raw':origin['source_raw'],'manifest':manifest,
        'exchange':exchange,'models':{wid:model},'reviews':{wid:review},
        'knowledge':knowledge,'source_prequarantine':quarantine,
        'operator_inventory_bytes':inventory_bytes,
        'operator_inventory_digest_sha256':sha256(inventory_bytes),
        'parent_review_task_digest_sha256':json_digest(task),
        'parent_native_draft_exchange_sha256':json_digest(exchange),
        'model_review_evidence_sha256':json_digest({'models':{wid:model},'reviews':{wid:review}}),
        'original_local_atoms_staged':0,'original_cross_atoms_awaiting_meaning':1,
        'unresolved_child_source_cues':len(mandatory),
        'owner_identity_cryptographically_verified':False,
        'e3_formal_approved':False,'e4_authorized':False,'e5_published':0,
        'v242_pending_parent_binding':binding,
        'v242_pending_parent_binding_sha256':digest,
        'v242_parent_semantic_qualifier_discharged':False,
        'v242_forbidden_as_v123_formal_child_atom':True}
    return case


def stage_pending_cross_child_host_only(*, case, original_build_kwargs:dict,
        native_store:TransactionStore,run_id:str,
        externally_pinned_parent_binding_sha256:str,
        explicit_unapproved_host_stage:bool=False):
    """Rebuild original evidence before invoking FROZEN V6 host transaction.

    The FULL SHA-256 of the external evidence is the durable native scope ID.
    The native V6 atom is only a source-local UNRESOLVED review view.
    """
    _need(explicit_unapproved_host_stage is True and type(native_store) is TransactionStore,
          'EXPLICIT_NATIVE_UNAPPROVED_STAGING_REQUIRED')
    expected=build_pending_cross_child_host_case(**original_build_kwargs)
    _need(case==expected and case['e3_formal_approved'] is False and
          case['e4_authorized'] is False and case['e5_published']==0 and
          case['v242_forbidden_as_v123_formal_child_atom'] is True,
          'CASE_CHANGED_SINCE_SOURCE_FIRST_REVIEW')
    digest=case['v242_pending_parent_binding_sha256']
    _need(digest==externally_pinned_parent_binding_sha256 and
          json_digest(case['v242_pending_parent_binding'])==digest,
          'OUTSIDE_PARENT_CONDITION_PIN_MISMATCH')
    scope_id='v242_'+digest
    receipt=stage_child_host_only(case=case,native_store=native_store,
        scope_id=scope_id,run_id=run_id,
        externally_operator_pinned_inventory_sha256=
            case['operator_inventory_digest_sha256'],
        explicit_unapproved_host_stage=True)
    snap=TransactionStore(native_store.path).snapshot(scope_id)
    _need(snap['ledger_head_sha256']==receipt['host_event_sha256'] and
          snap['sequence']==6 and receipt['e5_published']==0 and
          receipt['v123_final_approved'] is False,
          'NATIVE_HOST_REOPEN_OR_APPROVAL_LEAK')
    return {'schema':SCHEMA,'status':'V242_REAL_NATIVE_HOST_LOCAL_VIEW_PENDING_PARENT_CONDITION',
        'segment_id':case['segment_id'],'scope_id':scope_id,
        'parent_condition_sha256':digest,'source_sha256':case['source'].source_sha256,
        'model_and_proof_events_reopened':True,
        'native_host_receipt_event_sha256':receipt['host_event_sha256'],
        'native_host_event_count':snap['sequence'],
        'parent_original_atom_preserved':True,
        'parent_external_semantics_resolved':False,
        'e2_semantic_review_approved':False,'e3_formal_child_approved':False,
        'e4_authorized':False,'e5_published':0,
        'host_user_identity_cryptographically_verified':False}