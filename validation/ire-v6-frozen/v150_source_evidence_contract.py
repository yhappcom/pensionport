"""V150 evidence-only completeness contract. Never converts known source gaps to PASS."""
from __future__ import annotations
import json,hashlib
from pathlib import Path

SOURCE_SHA='638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d'

class SourceContractError(ValueError):pass


def audit_public_owner_progress(obj):
    if not isinstance(obj,dict) or obj.get('schema')!='V150_P0E_REAL_SOURCE_SHA_ONLY_V1':
        raise SourceContractError('BAD_PUBLIC_SOURCE_SCHEMA')
    must={'original_cues':1481,'native_v6_provisional_atoms':274,'unreferenced_original_cues':254,
          'unreferenced_critical_cues_explicitly_reviewed':17,'unreferenced_queue_still_pending':237,
          'b0012_source_only_gold_units':16,'b0012_v6_predicted_units':16,
          'b0012_clear_one_to_one_pairs':12,'b0012_granularity_disputes':4,
          'real_v123_approved_scopes':0,'real_v128_knowledge_rows':0}
    if obj.get('source_sha256')!=SOURCE_SHA or any(obj.get(k)!=v for k,v in must.items()):
        raise SourceContractError('OWNER_CENSUS_OR_SOURCE_DRIFT')
    if obj.get('b0012_full_precision_recall_measured') is not False or obj.get('full_precision_recall_measured') is not False:
        raise SourceContractError('UNPROVEN_ACCURACY_FALSE_APPROVAL')
    if obj.get('p0_go') is not False or obj.get('p0e_go') is not False:
        raise SourceContractError('PREMATURE_RELEASE')
    if obj['unreferenced_critical_cues_explicitly_reviewed']+obj['unreferenced_queue_still_pending']!=254:
        raise SourceContractError('CUE_GAP_LOSS')
    return {'schema':'V150_CONSERVATIVE_GOLD_READINESS_V1','status':'SOURCE_FIRST_PARTIAL_REVIEW_NOT_FULL_GOLD',
       'original_cues':1481,'unreferenced_critical_reviewed':17,'unreferenced_pending':237,
       'b0012_no_false_score':True,'p0_e_go':False}


def audit_original_review(raw:bytes,queue:list,review:dict,blind:dict,adjudication:dict):
    if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA:raise SourceContractError('OWNER_SRT_SHA_DRIFT')
    if len(queue)!=254 or len({x['cue_index'] for x in queue})!=254:
        raise SourceContractError('QUEUE_DUPLICATE_OR_MISSING')
    if review.get('schema')!='V150_SOURCE_PINNED_CRITICAL_GAPS_V1' or review.get('source_sha256')!=SOURCE_SHA:
        raise SourceContractError('REVIEW_WRONG_ORIGINAL')
    reviewed=review.get('high_priority_reviewed_cues')
    if not isinstance(reviewed,list) or len(reviewed)!=17:raise SourceContractError('HIGH_RISK_REVIEW_CENSUS')
    queue_index={q['cue_index']:q for q in queue}
    seen=set()
    for r in reviewed:
        i=r['cue_index'];note=r.get('chat_source_only_review_note')
        if i in seen or i not in queue_index or r.get('source_text_sha256')!=queue_index[i]['source_text_sha256']:
            raise SourceContractError('HIGH_RISK_SOURCE_PIN')
        seen.add(i)
        if not isinstance(note,str) or len(note)<15 or r.get('v123_approved') is not False:
            raise SourceContractError('UNREVIEWED_AUTOPROMOTION')
        for c in r['context']:
            if hashlib.sha256(c['text'].encode()).hexdigest()!=c['sha256']:
                raise SourceContractError('CONTEXT_SHA_DRIFT')
    if blind.get('source_srt_sha256')!=SOURCE_SHA or len(blind.get('rows',[]))!=16:
        raise SourceContractError('BLIND_REFERENCE_GAP')
    if adjudication.get('source_only_frozen_sha256')!=hashlib.sha256((json.dumps(blind,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()).hexdigest():
        raise SourceContractError('BLIND_FREEZE_NOT_PINNED')
    if adjudication.get('safe_to_calculate_full_scope_precision_recall') is not False or adjudication.get('externally_independent_gold') is not False:
        raise SourceContractError('SAME_CHAT_FALSE_CERTIFICATION')
    return True
