"""V171: source-pinned *draft* re-atomization of a mixed speech act.

A chat-authored semantic split must be checked by the frozen V6 native atomic
exchange auditor. The changed exchange is NOT a released V123 review: native
host staging, V123 full review, E4 issuer verification, and E5 parent gating
remain separate mandatory operations. No model/API call and no storage write.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re

SCHEMA = 'IRE_V171_SOURCE_BOUND_SEMANTIC_SPLIT_V1'
RECEIPT = 'IRE_V171_UNRELEASED_REATOMIZATION_DRAFT_V1'
CID = re.compile(r'C\d{5,8}\Z')
KINDS = {'FACT','OPINION','QUESTION','HYPOTHETICAL','RECOMMENDATION','MATH'}
STANCES = {'AFFIRMED','NEGATED','CORRECTED','CONDITIONAL','QUOTED','UNRESOLVED'}


def sha(b): return hashlib.sha256(b).hexdigest()
def digest(v): return sha(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',', ':'),allow_nan=False).encode())
def need(ok, why):
    if not ok: raise ValueError('V171_REATOM_'+why)


def compile_split(source, original_exchange, original_review, split, *, whole_video_claim_ids, native_audit):
    """Take a *new* ChatGPT-authored split; never amend source or old review.

    `source` is V6 VerifiedSource, and `native_audit` MUST be the frozen
    `ire.v6.atomic_exchange.audit_host_atomic_exchange` function, not a fake
    success flag. Caller separately preserves owner bytes and host store.
    """
    need(callable(native_audit) and getattr(native_audit,'__module__',None)==
         'ire.v6.atomic_exchange' and getattr(native_audit,'__name__',None)==
         'audit_host_atomic_exchange', 'FROZEN_NATIVE_V6_AUDIT_REQUIRED')
    prior=native_audit(source,original_exchange)
    need(type(split) is dict and set(split)=={
        'schema','source_sha256','manifest_sha256','old_exchange_sha256',
        'old_review_sha256','old_claim_id','old_atom_sha256','new_atoms',
        'chat_semantic_note','chat_semantic_note_sha256',
        'reviewer_source_first_checked','reviewer_condition_exception_checked',
        'reviewer_counterexample_checked','reviewer_rebuttal_context_checked',
        'audio_authenticated','independent_gold_certified',
        'financial_truth_certified','personal_advice_approved',
        'approved_knowledge_release'}, 'SPLIT_SCHEMA')
    need(split['schema']==SCHEMA and
         split['source_sha256']==source.source_sha256 and
         split['manifest_sha256']==source.manifest_sha256 and
         split['old_exchange_sha256']==digest(original_exchange) and
         split['old_review_sha256']==digest(original_review),
         'OWNER_SOURCE_EXCHANGE_OR_REVIEW_VERSION_DRIFT')
    need(all(split[x] is True for x in (
        'reviewer_source_first_checked','reviewer_condition_exception_checked',
        'reviewer_counterexample_checked','reviewer_rebuttal_context_checked')) and
         all(split[x] is False for x in (
        'audio_authenticated','independent_gold_certified',
        'financial_truth_certified','personal_advice_approved',
        'approved_knowledge_release')), 'UNREVIEWED_OR_FALSE_AUTHORITY')
    note=split['chat_semantic_note']
    need(type(note) is str and len(note.strip())>=100 and
         sha(note.encode('utf-8'))==split['chat_semantic_note_sha256'],
         'ACTUAL_CHAT_NOTE_REQUIRED')
    cid=split['old_claim_id']
    old_atoms={x['claim_id']:x for x in original_exchange['atoms']}
    old_verdicts={x['claim_id']:x for x in original_review['atom_verdicts']}
    need(cid in old_atoms and cid in old_verdicts and
         split['old_atom_sha256']==digest(old_atoms[cid]) and
         old_verdicts[cid]['atom_sha256']==split['old_atom_sha256'] and
         old_verdicts[cid]['status']=='OPEN','ONLY_ORIGINAL_OPEN_ATOM_REPAIRABLE')
    need(original_review.get('source_sha256')==source.source_sha256 and
         original_review.get('manifest_sha256')==source.manifest_sha256 and
         type(whole_video_claim_ids) is set and
         set(old_atoms).issubset(whole_video_claim_ids),
         'GLOBAL_CLAIM_NAMESPACE_REQUIRED')
    before=old_atoms[cid]
    replacements=split['new_atoms']
    need(type(replacements) is list and len(replacements)==2 and
         all(type(x) is dict and set(x)==set(before) for x in replacements),
         'EXACTLY_TWO_NATIVE_ATOMS_REQUIRED')
    ids=[x['claim_id'] for x in replacements]
    need(ids[0]==cid and type(ids[1]) is str and CID.fullmatch(ids[1]) and
         ids[1] not in whole_video_claim_ids,'MUST_RETAIN_OLD_ID_AND_NEW_GLOBAL_ID')
    need({x['kind'] for x in replacements}=={'FACT','OPINION'},
         'FACTUAL_DEPENDENCY_MUST_BE_SPLIT_FROM_OPINION')
    original_source_indices={r['cue_index'] for r in before['source_refs']}
    covered=set()
    for x in replacements:
        need(x['kind'] in KINDS and x['stance'] in STANCES and
             x['owner_window_id']==before['owner_window_id'] and
             x['speaker']==before['speaker'] and
             x['as_of']==before['as_of'] and
             type(x['proposition']) is str and len(x['proposition'].strip())>=20,
             'SPEAKER_OR_SCOPE_REWRITTEN')
        need(type(x['source_refs']) is list and x['source_refs'] and
             len({r['cue_index'] for r in x['source_refs']})==len(x['source_refs']) and
             [r['cue_index'] for r in x['source_refs']]==sorted(r['cue_index'] for r in x['source_refs']),
             'NEW_SOURCE_REFS_INVALID')
        new_refs={r['cue_index'] for r in x['source_refs']}
        need(new_refs.issubset(original_source_indices) and
             x['context_cue_indices']==before['context_cue_indices'] and
             x['condition_cue_indices']==before['condition_cue_indices'] and
             x['exception_cue_indices']==before['exception_cue_indices'] and
             x['numeric_references']==before['numeric_references'],
             'CONDITIONS_EXCEPTIONS_NUMBERS_OR_SOURCE_CONTEXT_LOST')
        for r in x['source_refs']:
            need(type(r) is dict and set(r)=={'cue_index','quote'} and
                 type(r['quote']) is str and len(r['quote'].strip())>=2 and
                 r['quote'] in source.cues[r['cue_index']-1].text,
                 'ORIGINAL_VERBATIM_QUOTE_MISSING')
        covered.update(new_refs)
    need(covered==original_source_indices,'OLD_SOURCE_REFERENCE_LOST')
    updated=copy.deepcopy(original_exchange)
    pos=next(i for i,a in enumerate(updated['atoms']) if a['claim_id']==cid)
    updated['atoms'][pos:pos+1]=copy.deepcopy(replacements)
    for cue in updated['cue_dispositions']:
        idx=cue['cue_index']
        if idx not in original_source_indices: continue
        expected=set(cue['claim_ids'])-{cid}
        expected.update(x['claim_id'] for x in replacements
                        if idx in {r['cue_index'] for r in x['source_refs']})
        cue['claim_ids']=sorted(expected)
    # Actual unchanged frozen V6 code must audit all cue dispositions,
    # numbers, ownership, source bytes and candidate references.
    checked=native_audit(source,updated)
    need(checked['original_scoped_cues_enumerated']==
         prior['original_scoped_cues_enumerated'] and
         checked['proposed_atomic_claims']==prior['proposed_atomic_claims']+1 and
         checked['every_cue_has_explicit_disposition'] is True,
         'FROZEN_NATIVE_STRUCTURAL_REPLAY_FAILED')
    new_review=copy.deepcopy(original_review)
    vpos=next(i for i,v in enumerate(new_review['atom_verdicts']) if v['claim_id']==cid)
    before_v=old_verdicts[cid]
    made=[]
    for x in replacements:
        v=copy.deepcopy(before_v)
        v['claim_id']=x['claim_id'];v['atom_sha256']=digest(x)
        v['status']='OPEN';v['high_risk']=bool(before_v['high_risk'] or x['kind']=='FACT')
        v['speaker_stance_checked']=False
        v['conditions_exceptions_checked']=False
        v['numeric_period_checked']=False
        v['counterexample_checked']=False
        v['private_review_note_sha256']=split['chat_semantic_note_sha256']
        made.append(v)
    new_review['atom_verdicts'][vpos:vpos+1]=made
    # Existing host event is stale after a changed exchange. The draft is
    # deliberately not a fully valid new V123 chat approval record.
    new_review['atom_candidate_digest']=checked['atom_candidate_digest']
    new_review['cue_disposition_digest']=checked['cue_disposition_digest']
    new_review['source_first_pass_completed']=False
    new_review['counterexample_pass_completed']=False
    new_review['disagreements_adjudicated']=False
    receipt={
        'schema':RECEIPT,'source_sha256':source.source_sha256,
        'old_exchange_sha256':digest(original_exchange),
        'new_exchange_sha256':digest(updated),
        'old_review_sha256':digest(original_review),
        'draft_review_sha256':digest(new_review),
        'old_claim_id':cid,'new_claim_ids':ids,
        'original_atom_count':len(original_exchange['atoms']),
        'draft_atom_count':len(updated['atoms']),
        'fact_status':'OPEN','opinion_status':'OPEN',
        'new_host_batch_staging_required':True,
        'full_chat_final_review_required':True,
        'all_video_cross_segment_census_required':True,
        'native_v123_final_approval':False,'e4_approved':False,
        'e5_authorized':False,'knowledge_publication_authorized':False,
        'original_exchange_or_review_modified':False,
        'independent_semantic_accuracy_certified':False,
    }
    return {'receipt':{**receipt,'receipt_sha256':digest(receipt)},
            'draft_exchange':updated,'draft_review':new_review}