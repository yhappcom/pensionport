"""V149 owner-only read-only V128 parent evidence gate for V126 chat answers.

No V123 pass / no V128 parent publication => NO approved research evidence.
An immutable SHA-backed parent checkpoint must be supplied separately. The
caller cannot turn unapproved 274 draft atoms into active approved knowledge.
The gateway does not independently validate semantic truth or individual tax.
"""
from __future__ import annotations
import json,re
from datetime import date
from pathlib import Path
from ire.v6.codec import ZERO_SHA, json_digest
from ire.v6.errors import QualityNotProven,InvalidInput
from v126_chat_approved_knowledge_store import PrivateKnowledgeStore
from v128_atomic_parent_knowledge import _replay_parent_publications

HEX=re.compile(r'[0-9a-f]{64}\Z')

class OwnerEvidenceHold(QualityNotProven):pass

def _check(ok, code):
    if not ok:raise OwnerEvidenceHold('V149_OWNER_EVIDENCE_'+code)

def _hash_ok(value):return isinstance(value,str) and HEX.fullmatch(value) is not None

def _parent_identity(identity):
    _check(type(identity) is dict and set(identity)=={'video_id','source_sha256','manifest_sha256','owner_inventory_pin'},'IDENTITY_SCHEMA')
    _check(type(identity['video_id']) is str and bool(identity['video_id']) and _hash_ok(identity['source_sha256']) and _hash_ok(identity['manifest_sha256']),'IDENTITY_HASH_MISSING')
    return json_digest(identity)

def prepare_verified_owner_question(store, question:str, *, owner_checkpoint:dict,
                                    selected_knowledge_ids:list, as_of:str,
                                    expected_segment_count:int=13,
                                    required_source_sha256:str|None=None)->dict:
    """Read a *durable* approved, all-child parent publication, never staging.

    A separately frozen original-source checkpoint must be carried into the
    call. No packet can be prepared from a synthetic owner with 0 V123 passes.
    """
    _check(type(store) is PrivateKnowledgeStore and store._parent_staging_only is False,'PUBLISHED_STORE_REQUIRED')
    _check(type(expected_segment_count) is int and 1<=expected_segment_count<=13,'SEGMENT_COUNT_INVALID')
    _check(type(question) is str and question.strip() and len(question)<=4000,'QUESTION_INVALID')
    _check(type(as_of) is str and date.fromisoformat(as_of).isoformat()==as_of,'ASOF_INVALID')
    _check(type(owner_checkpoint) is dict and set(owner_checkpoint)=={
        'schema','identity','parent_publication_proof_sha256','parent_chat_release_sha256',
        'child_batches_sha256','expected_knowledge_head_sha256','expected_segment_count'},'CHECKPOINT_SCHEMA')
    _check(owner_checkpoint['schema']=='IRE_V149_EXTERNALLY_FROZEN_PARENT_READ_PIN_V1' and
           owner_checkpoint['expected_segment_count']==expected_segment_count,'CHECKPOINT_CENSUS')
    pid=_parent_identity(owner_checkpoint['identity'])
    if required_source_sha256 is not None:
        _check(owner_checkpoint['identity']['source_sha256']==required_source_sha256,'WRONG_OWNER_SOURCE')
    for key in ('parent_publication_proof_sha256','parent_chat_release_sha256',
                'child_batches_sha256','expected_knowledge_head_sha256'):
        _check(_hash_ok(owner_checkpoint[key]),'CHECKPOINT_SHA_MISSING')
    # Check independently selected, immutable owner HEAD before querying entries.
    audit=store.audit(externally_pinned_head=owner_checkpoint['expected_knowledge_head_sha256'])
    _check(audit['active_claims']>0 and audit['head_sha256']!=ZERO_SHA,'NO_RELEASED_RESEARCH_KNOWLEDGE')
    with store._session() as con:
        head,states=store._audit(con)
        _check(head==owner_checkpoint['expected_knowledge_head_sha256'],'HEAD_MOVED')
        has=con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='parent_publications'").fetchone()
        _check(has is not None,'NO_V128_PARENT_PUBLICATION')
        proofs=_replay_parent_publications(con,head)
        proof=proofs.get(pid)
        _check(proof is not None,'REQUIRED_PARENT_NOT_PUBLISHED')
        _check(json_digest(proof)==owner_checkpoint['parent_publication_proof_sha256'],'PARENT_PROOF_NOT_FROZEN')
        _check(proof.get('child_segment_count')==expected_segment_count and proof.get('candidate_only_not_finance_fact') is True and proof.get('p0_go') is False,'PARENT_CHILD_OR_SCOPE_INVALID')
        request=proof.get('request',{})
        _check(request.get('child_batches_sha256')==owner_checkpoint['child_batches_sha256'] and
               proof.get('chat_release_sha256')==owner_checkpoint['parent_chat_release_sha256'] and
               request.get('parent_chat_release_sha256')==owner_checkpoint['parent_chat_release_sha256'],'CHAT_APPROVAL_OR_CHILD_BATCH_NOT_PINNED')
        _check(proof.get('to_head_sha256')==head,'OWNER_HEAD_NOT_CURRENT')
        start=proof['from_head_sha256']
        if start==ZERO_SHA:start_seq=0
        else:
            row=con.execute('SELECT seq FROM events WHERE event_sha256=?',(start,)).fetchone()
            _check(row is not None,'PARENT_START_EVENT_NOT_FOUND')
            start_seq=row[0]
        rows=con.execute('SELECT kind,knowledge_id,prev_sha256,event_sha256 FROM events WHERE seq>? ORDER BY seq',(start_seq,)).fetchall()
        _check(len(rows)==proof['entry_count'] and all(row[0]=='ADD' for row in rows),'APPROVED_PARENT_EVENT_RANGE_MISMATCH')
        eligible={row[1] for row in rows}
        _check(len(eligible)==len(rows),'DUPLICATE_PARENT_KNOWLEDGE_EVENT')
        _check(all(states.get(k)=='ACTIVE' for k in eligible),'PARENT_RECORD_REVOKED')
        _check(type(selected_knowledge_ids) is list and bool(selected_knowledge_ids) and
               selected_knowledge_ids==sorted(set(selected_knowledge_ids)) and
               set(selected_knowledge_ids)<=eligible,'UNPUBLISHED_OR_FOREIGN_KNOWLEDGE_SELECTED')
    packet=store.evidence_for_question(question,selected_knowledge_ids=selected_knowledge_ids)
    _check(packet['count']==len(selected_knowledge_ids) and
           packet['knowledge_head_sha256']==head,'QUESTION_EVIDENCE_NOT_BOUND')
    return {'schema':'IRE_V149_OWNER_PARENT_VERIFIED_QUESTION_PACKET_V1',
            'question':question,'as_of':as_of,'parent_id':pid,
            'parent_publication_proof_sha256':owner_checkpoint['parent_publication_proof_sha256'],
            'child_segment_count':expected_segment_count,
            'source_sha256':owner_checkpoint['identity']['source_sha256'],
            'approved_knowledge_head_sha256':head,'selected_knowledge_ids':selected_knowledge_ids,
            'evidence':packet,'evidence_sha256':json_digest(packet),
            'issuer_primary_body_refresh_required':packet['financial_claims_requiring_current_primary_source']>0,
            'answer_must_be_checked_by_V126_chat_research_answer_bridge':True,
            'V23_current_law_scope_review_separately_required':True,
            'separate_external_checkpoint_authenticity_not_proven_by_same_DB':True,
            'formal_financial_fact_approved':False,
            'personal_investor_eligibility_verified':False,'personal_trade_approved':False,
            'p0_e_go':False,'p0_go':False,'status':'PUBLISHED_RESEARCH_EVIDENCE_READ_FOR_FINAL_CHAT_REVIEW_ONLY'}
