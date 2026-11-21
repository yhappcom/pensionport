"""E2 V227: source-cue triage and strict E3 context normalization.

One native UNRESOLVED cue may already be covered as context.  This layer
tracks source-vs-gold certainty separately.  A lexical pair scan does NOT
certify semantic equivalence or independent recall.

No owner-private source or statement is embedded in this reusable module.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from difflib import SequenceMatcher
from hashlib import sha256
import json
import re
from typing import Any

from ire.v6.atomic_exchange import audit_host_atomic_exchange
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import make_original_plan

SCHEMA = 'IRE_V227_E2_ORIGINAL_CUE_SEMANTIC_TRIAGE_UNAPPROVED_V1'
E3_SCHEMA = 'IRE_V227_E3_CANONICAL_68_SOURCE_CONTEXT_REVIEW_HOLD_V1'
PAIR_SCHEMA = 'IRE_V227_E2_FULL_PAIRWISE_LEXICAL_SCREEN_NOT_GOLD_V1'
CLASS_MAP = {
 'SOURCE_ANCHORED_NATIVE_UNAPPROVED':'PRIMARY_SOURCE_UNAPPROVED',
 'SOURCE_CONTEXT_ONLY_UNAPPROVED':'SOURCE_CONTEXT_LINKED_NOT_PRIMARY',
 'MEDIA_SPEECH_SOURCE_ANCHORED_BUT_VISUAL_HOLD':'MEDIA_PRIMARY_AV_HOLD',
 'MEDIA_SPEECH_CONTEXT_STILL_VISUAL_HOLD':'MEDIA_CONTEXT_AV_HOLD',
 'DISCOURSE_OR_NONCLAIM_PROVISIONAL':'DISCOURSE_PROVISIONAL',
}


def need(condition: Any, label: str) -> None:
    if not condition:
        raise InvalidInput('V227_E2_'+label)


def sha(raw: bytes) -> str:
    need(type(raw) is bytes, 'NON_BYTES_INPUT')
    return sha256(raw).hexdigest()


def bytes_json(raw: bytes, label: str) -> dict:
    need(type(raw) is bytes,'NON_BYTES_'+label)
    try:
        d=json.loads(raw.decode('utf-8'))
    except (ValueError,UnicodeError,TypeError) as e:
        raise InvalidInput('V227_E2_BAD_JSON_'+label) from e
    need(type(d) is dict, 'BAD_DOC_'+label)
    return d


def canonical_bytes(d: dict) -> bytes:
    return (json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8')


def pair_similarity(x: str,y: str) -> float:
    need(type(x) is str and type(y) is str,'PAIR_TEXT')
    a=re.sub(r'\s+','',x);b=re.sub(r'\s+','',y)
    return round(SequenceMatcher(None,a,b,autojunk=False).ratio(),4)


def _source_task_context(source, atom):
    indices=sorted(set(atom['context_cue_indices']) | {r['cue_index'] for r in atom['source_refs']})
    return [{'cue_index':i,'quote':source.cues[i-1].text,
             'quote_sha256':sha(source.cues[i-1].text.encode('utf-8'))} for i in indices]


def prepare_v227_records(source, native, census, e3, *, manual_nonclaim_reasons, manual_pair_review):
    """Derive the complete 250-cue inventory, 68 uniform E3 tasks and all pairs.

    Host-authored reasons are audit notes, NEVER blind gold. Source and native
    are separately verified by the frozen engine in the external entrypoint.
    """
    need(type(manual_nonclaim_reasons) is dict,'NONCLAIM_REASONS_TYPE')
    need(type(manual_pair_review) is dict,'PAIR_REVIEW_TYPE')
    atoms=native['atoms'];amap={a['claim_id']:a for a in atoms}
    need(len(amap)==len(atoms) and 0<len(atoms)<=512,'NATIVE_ATOM_DUPLICATION_OR_SHARD_REQUIRED')
    rows=census['rows'];need(len(rows)==len(source.cues),'CENSUS_COUNT')
    results=[];outstanding=[]
    counts=Counter();unresolved=Counter()
    for position, r in enumerate(rows,1):
        need(type(r) is dict and r.get('cue_index')==position,'CENSUS_CUE_ORDER')
        actual=source.cues[position-1].text
        need(r.get('source_quote')==actual and r.get('cue_text_sha256')==sha(actual.encode('utf-8')),'CENSUS_SOURCE_QUOTE')
        cls=r.get('classification');need(cls in CLASS_MAP,'UNKNOWN_CLASSIFICATION')
        disposition=native['cue_dispositions'][position-1]
        kind=CLASS_MAP[cls]
        src_ids=r.get('source_anchor_claim_ids');ctx_ids=r.get('context_claim_ids')
        need(type(src_ids) is list and type(ctx_ids) is list,'CLAIM_ID_LIST')
        need(set(src_ids)<=set(amap) and set(ctx_ids)<=set(amap),'NONEXISTENT_CLAIM_ID')
        need(len(set(src_ids))==len(src_ids) and len(set(ctx_ids))==len(ctx_ids),'DUPLICATE_CLAIM_ID')
        actual_prim=sorted(a['claim_id'] for a in atoms if position in {rr['cue_index'] for rr in a['source_refs']})
        actual_ctx=sorted(a['claim_id'] for a in atoms if position in a['context_cue_indices'])
        need(sorted(src_ids)==actual_prim,'PRIMARY_ANCHOR_NOT_EXHAUSTIVE')
        if kind=='SOURCE_CONTEXT_LINKED_NOT_PRIMARY':
            need(not src_ids and ctx_ids and set(ctx_ids)<=set(actual_ctx),'CONTEXT_CLAIM_DROPPED')
        if kind=='MEDIA_CONTEXT_AV_HOLD':
            need(not src_ids and bool(actual_ctx) and r.get('original_audio_or_screen_review_required') is True,'MEDIA_CONTEXT_NOT_LINKED')
        if kind=='MEDIA_PRIMARY_AV_HOLD':
            need(src_ids and r.get('original_audio_or_screen_review_required') is True,'MEDIA_PRIMARY_NOT_HOLD')
        if kind=='PRIMARY_SOURCE_UNAPPROVED':need(bool(src_ids),'NON_MEDIA_PRIMARY_EMPTY')
        if kind=='DISCOURSE_PROVISIONAL':
            need(not src_ids and not ctx_ids and not actual_ctx,'DISCOURSE_HAS_CLAIM_CONTEXT')
        if src_ids:
            need(disposition.get('disposition')=='CANDIDATES' and
                 sorted(disposition.get('claim_ids',[]))==sorted(src_ids),'PRIMARY_DISPOSITION_MISMATCH')
        else:
            need(disposition.get('disposition') in ('UNRESOLVED','NO_ATOM'),'NONPRIMARY_DISPOSITION_MISMATCH')
        reason='원문의 자막과 미승인 원자 근거·문맥이 연결됐으며 의미 동치 및 추가 주장 누락은 외부 정답으로 미확정'
        if kind=='SOURCE_CONTEXT_LINKED_NOT_PRIMARY':
            reason='주장 문장의 전제·조건·문맥 조각에 해당하며 대표 자막이 아니라는 이유로 구조적으로 UNRESOLVED 처리됨; 원문 의미 누락 검사는 별도'
        if kind=='MEDIA_PRIMARY_AV_HOLD' or kind=='MEDIA_CONTEXT_AV_HOLD':
            reason='화자가 발언한 자막은 원자 문맥에 연결됐으나 원화면·차트 형상 및 금융 수치의 참은 검증할 수 없음'
        if kind=='DISCOURSE_PROVISIONAL':
            reason=manual_nonclaim_reasons.get(position)
            need(type(reason) is str and len(reason.strip())>=20,'MANUAL_DISCOURSE_REASON_MISSING')
        if kind=='DISCOURSE_PROVISIONAL' and disposition['disposition']=='NO_ATOM':
            kind='EXPLICIT_SOURCE_REVIEWED_NO_ATOM_PROVISIONAL'
        if kind in ('DISCOURSE_PROVISIONAL','EXPLICIT_SOURCE_REVIEWED_NO_ATOM_PROVISIONAL','MEDIA_CONTEXT_AV_HOLD'):
            outstanding.append(position)
        if disposition['disposition']=='UNRESOLVED':unresolved[kind]+=1
        counts[kind]+=1
        results.append({'cue_index':position,'source_quote':actual,'source_quote_sha256':sha(actual.encode('utf-8')),
           'source_audit_class':kind,'original_frozen_v6_disposition':disposition['disposition'],
           'original_primary_atom_ids':sorted(src_ids),'original_context_atom_ids':sorted(ctx_ids),
           'all_native_context_atom_ids':actual_ctx,'cue_context_review_reason':reason,
           'screen_or_audio_original_verified':False,
           'cue_disposition_is_not_independent_gold':True,'no_claim_absence_certified':False,
           'additional_hidden_subclaim_may_exist':True,'financial_fact_approved':False})
    need(set(manual_nonclaim_reasons)=={r['cue_index'] for r in results if r['source_audit_class'] in ('DISCOURSE_PROVISIONAL','EXPLICIT_SOURCE_REVIEWED_NO_ATOM_PROVISIONAL')},'NONCLAIM_REVIEW_IDS_NOT_EXACT')
    out={'schema':SCHEMA,'original_srt_sha256':source.source_sha256,
         'native_sha256':sha(canonical_bytes(native)),'census_sha256':sha(canonical_bytes(census)),
         'review_cue_count':len(results),'source_only_cue_reviewed':True,
         'original_frozen_v6_unresolved_cue_count':sum(x=='UNRESOLVED' for x in (d['disposition'] for d in native['cue_dispositions'])),
         'true_source_semantic_omission_count':None,
         'independent_gold_precision':None,'independent_gold_recall':None,
         'independent_high_risk_false_negatives':None,
         'source_audit_class_counts':dict(sorted(counts.items())),
         'frozen_unresolved_split':dict(sorted(unresolved.items())),
         'outstanding_direct_audio_or_nonclaim_review_cues':outstanding,
         'formal_e2_accuracy_certified':False,'financial_fact_approved':False,
         'rows':results}
    # Uniform E3 task source_context: prior 65 lists, last three dicts.  Do not
    # silently alter any other task field or claim-level certification.
    prior=e3['task_rows'];need(len(prior)==len(atoms),'E3_TASK_COUNT')
    task_by_id={t['claim_id']:t for t in prior}
    need(len(task_by_id)==len(prior)==len(amap) and set(task_by_id)==set(amap),'E3_TASK_IDS')
    cp=deepcopy(e3);cp['schema']=E3_SCHEMA
    converted=[]
    for task in cp['task_rows']:
        atom=amap[task['claim_id']]
        original=task.get('source_context')
        actual_task=_source_task_context(source,atom)
        if type(original) is list:
            need(all(type(r) is dict and type(r.get('cue_index')) is int and 1<=r['cue_index']<=len(source.cues)
                     and r.get('quote')==source.cues[r['cue_index']-1].text
                     and r.get('quote_sha256')==sha(r['quote'].encode('utf-8')) for r in original),'OLD_E3_CONTEXT_QUOTE_TAMPERED')
            need({x['cue_index'] for x in atom['source_refs']}.issubset({x['cue_index'] for x in original}),
                 'EXISTING_E3_PRIMARY_REF_MISSING')
            task['source_context']=original
        else:
            need(type(original) is dict,'OLD_E3_UNKNOWN_CONTEXT_SHAPE')
            need(original.get('source_refs')==atom['source_refs'] and
                 original.get('source_context_cue_indices')==atom['context_cue_indices'],'MEDIA_E3_CONTEXT_DOES_NOT_MATCH_NATIVE')
            task['source_context']=actual_task
            converted.append(task['claim_id'])
        task['v227_original_media_context_normalized']=task['claim_id'] in converted
        task['v227_text_source_check_complete']=True
        task['v227_gold_precision_or_recall_certified']=False
        need(task.get('financial_fact_approved') is False and task.get('e3_final_approved') is False,
             'E3_CLAIM_ALREADY_APPROVED')
    cp['v227_canonical_source_context_all_tasks']=True
    cp['v227_old_mixed_shape_source_task_count']=len(converted)
    cp['v227_original_media_task_ids_normalized']=converted
    cp['v227_text_source_only_reviewed_native_count']=len(prior)
    cp['v227_independent_gold_claims_certified']=0
    cp['v227_final_e3_grants']=0
    cp['e3_final_approved']=False
    cp['e4_approved']=False
    cp['e5_published']=False
    cp['v227_semantic_e2_and_finance_approval_remains_hold']=True
    # Pairwise *lexical* coverage, not gold equivalence; include all nC2 pairs.
    ids=sorted(amap)
    pairs=[];reviews=Counter()
    for i in range(len(ids)):
        for j in range(i+1,len(ids)):
            aa=amap[ids[i]];bb=amap[ids[j]]
            key=ids[i]+'|'+ids[j]
            review=manual_pair_review.get(key)
            if review is None:
                state='UNREVIEWED_SEMANTIC_PAIR_LEXICAL_ONLY';reason=None
            else:
                need(type(review) is dict,'PAIR_REVIEW_OBJECT')
                state=review.get('status');reason=review.get('source_grounded_reason')
                need(state in {'PARTIAL_OVERLAP_NOT_EQUIVALENT','RELATED_DISTINCT','CONTRAST_DISTINCT','INDEPENDENT_FRAMES_DISTINCT','POTENTIAL_DUPLICATE_HOLD'} and
                     type(reason) is str and len(reason.strip())>=24,'PAIR_REVIEW_INVALID')
                reviews[state]+=1
            pa={r['cue_index'] for r in aa['source_refs']};pb={r['cue_index'] for r in bb['source_refs']}
            overlap=sorted((set(aa['context_cue_indices'])&set(bb['context_cue_indices']))-{45,46,47})
            pairs.append({'claim_ids':[ids[i],ids[j]],'lexical_similarity':pair_similarity(aa['proposition'],bb['proposition']),
              'same_primary_cue_indices':sorted(pa&pb),'non_global_context_overlap':overlap,
              'source_first_pair_review_status':state,'source_first_review_reason':reason,
              'independently_verified_exact_equivalence':False,
              'automatically_merged':False,'financial_fact_approved':False})
    need(set(manual_pair_review)<=set(x['claim_ids'][0]+'|'+x['claim_ids'][1] for x in pairs),'PAIR_REVIEW_UNKNOWN_IDS')
    pairdoc={'schema':PAIR_SCHEMA,'source_sha256':source.source_sha256,
          'native_sha256':sha(canonical_bytes(native)),
          'all_atom_count':len(atoms),'pair_count':len(pairs),
          'manual_pair_reviewed':sum(reviews.values()),
          'manual_pair_status_counts':dict(sorted(reviews.items())),
          'remaining_pairs_have_only_lexical_screen_not_semantic_ground_truth':len(pairs)-sum(reviews.values()),
          'independently_approved_equivalent_pairs':0,
          'independent_recall_evaluation_completed':False,
          'knowledge_deduplication_approved':False,'rows':pairs}
    return out,cp,pairdoc


def audit_v227_exact_replay(files: dict,*,expected_sha256:dict,nonclaim_reasons:dict,manual_pairs:dict,window_size:int=20):
    """Public fail-closed entrypoint, including malformed owner packet envelopes."""
    try:
        return _audit_v227_core(files,expected_sha256=expected_sha256,
              nonclaim_reasons=nonclaim_reasons,manual_pairs=manual_pairs,window_size=window_size)
    except InvalidInput:
        raise
    except (KeyError,IndexError,TypeError,ValueError,AttributeError) as exc:
        raise InvalidInput('V227_E2_MALFORMED_PACKET_SCHEMA') from exc


def _audit_v227_core(files: dict,*,expected_sha256:dict,nonclaim_reasons:dict,manual_pairs:dict,window_size:int=20):
    """Verify the exact bytes and deterministic full source/atom/pair ledger.

    Original financial truth, speaker identity and blind gold are never inferred.
    """
    need(type(window_size) is int and 1<=window_size<=1000,'WINDOW_SIZE_INVALID')
    names=('srt','native','census','old_e3','source_triage','canonical_e3','all_pairs')
    need(type(files) is dict and set(files)==set(names),'INPUT_KEYS')
    need(type(expected_sha256) is dict and set(expected_sha256)==set(names),'EXPECTED_HASH_KEYS')
    for k in names:
        need(type(files[k]) is bytes and type(expected_sha256[k]) is str and len(expected_sha256[k])==64 and
             sha(files[k])==expected_sha256[k],'BAD_SHA_'+k.upper())
    native=bytes_json(files['native'],'NATIVE');census=bytes_json(files['census'],'CENSUS');old=bytes_json(files['old_e3'],'OLD_E3')
    triage=bytes_json(files['source_triage'],'TRIAGE');canonical=bytes_json(files['canonical_e3'],'NEW_E3');pairs=bytes_json(files['all_pairs'],'PAIRS')
    source,plan=make_original_plan(files['srt'],native['video_id'],expected_source_sha256=expected_sha256['srt'],window_size=window_size)
    frozen=audit_host_atomic_exchange(source,native)
    need(frozen['source_sha256']==expected_sha256['srt'],'FROZEN_SOURCE_MISMATCH')
    need(census.get('original_source_sha256')==source.source_sha256 and
         census.get('native_exchange_sha256')==expected_sha256['native'],'CENSUS_NATIVE_PIN')
    need(old.get('source_sha256')==source.source_sha256 and old.get('native_sha256')==expected_sha256['native'] and
         old.get('e3_final_approved') is False and old.get('e4_approved') is False and old.get('e5_published') is False,
         'E3_ORIGINAL_NOT_UNAPPROVED')
    exp_tri,exp_e3,exp_pairs=prepare_v227_records(source,native,census,old,
                                   manual_nonclaim_reasons=nonclaim_reasons,manual_pair_review=manual_pairs)
    need(triage==exp_tri,'TRIAGE_NOT_REPRODUCIBLE')
    need(canonical==exp_e3,'CANONICAL_E3_NOT_REPRODUCIBLE')
    need(pairs==exp_pairs,'PAIRS_NOT_REPRODUCIBLE')
    alltypes=Counter(r['original_frozen_v6_disposition'] for r in triage['rows'])
    need(sum(alltypes.values())==len(source.cues),'CUE_DISPOSITION_NOT_EXHAUSTIVE')
    need(all(t.get('source_context') and type(t['source_context']) is list and
         t.get('v227_gold_precision_or_recall_certified') is False for t in canonical['task_rows']),
         'CANONICAL_E3_RUNTIME_SHAPE')
    need(not triage['formal_e2_accuracy_certified'] and not triage['financial_fact_approved'] and
         not canonical['e3_final_approved'] and not canonical['e4_approved'] and not canonical['e5_published'] and
         not pairs['knowledge_deduplication_approved'],'PREMATURE_RELEASE')
    return {'schema':'IRE_V227_REAL_ORIGINAL_250CUE_68ATOM_RECONCILIATION_RECEIPT_HOLD_V1',
      'source_sha256':source.source_sha256,'original_cues_replayed':len(source.cues),
      'native_unapproved_atoms':len(native['atoms']),
      'frozen_v6_unresolved_cue_count':triage['original_frozen_v6_unresolved_cue_count'],
      'reconciled_review_class_counts':triage['source_audit_class_counts'],
      'separate_attention_cues':len(triage['outstanding_direct_audio_or_nonclaim_review_cues']),
      'all_e3_source_context_list_shapes_verified':len(canonical['task_rows']),
      'legacy_dict_source_context_fields_fixed':canonical['v227_old_mixed_shape_source_task_count'],
      'full_native_pairwise_lexical_pairs_checked':pairs['pair_count'],
      'manually_reviewed_pairs_not_external_gold':pairs['manual_pair_reviewed'],
      'unreviewed_semantic_pairs':pairs['remaining_pairs_have_only_lexical_screen_not_semantic_ground_truth'],
      'source_cue_internal_triage_complete':True,
      'independent_gold_precision_recall_measured':False,
      'high_risk_false_negatives_certified_zero':False,
      'audio_video_verified':False,'financial_facts_approved':0,
      'e2_final_pass':False,'e3_final_approved':False,'e4_authorized':False,'e5_published':0,
      'status':'ACTUAL_SOURCE_CUE_AND_E3_RUNTIME_SHAPE_PASS_INDEPENDENT_GOLD_HOLD'}