"""V96: original-cue first private CHAT review integrity gate, not semantic recall.

Public test code carries NO private speech, no transcript and no gold labels.
Review payload is supplied only in the owner's local private context.
"""
from __future__ import annotations
import hashlib,json
from collections import Counter
STATUS='CHAT_CONTEXTUAL_REVIEW_NOT_INDEPENDENT_GOLD'
SOURCE_VIDEO_IDS={'sz5N9WJS310','6VEfKF7BzZU','OiDTNstaSpM','aNfGrcO6WPI','qtluAViPpsQ','4CQ4FjGT2gA'}
KINDS={'ASR_REVIEW','COMPOUND_REVIEW','MULTINUMERIC_REVIEW','QUALIFIER_REVIEW'}
DISPOSITIONS={
'LEXICAL_TRIGGER_ONLY','QUESTION_NOT_FACT','SPEAKER_UNCERTAINTY',
'HISTORICAL_NUMERIC_OPEN','CONDITIONAL_ADVICE','HISTORICAL_ACCOUNT',
'OPINION','SCOPE_CORRECTION_CANDIDATE','SCOPE_RESTRICTION',
'OPINION_ADVICE_LIMIT','CONTRAST_SCOPE','HYPOTHESIS',
'NUMERIC_CONFLICT_OPEN','DATED_FACT_CHECKED_LIMITED','NUMERIC_ASR_OPEN',
'ILLUSTRATIVE_ARITHMETIC','QUALIFIER_IN_CONTEXT'}
FALSE_FIELDS=('p0_go','independent_gold','fact_approved','actual_error_certified',
    'precision_recall_certified','p3_promoted','master116_merged','personal_advice_approved',
    'source_wide_atomic_recall_certified','v75_lineage_certified','audio_verified')

def require(ok,code):
    if not ok:raise ValueError('V96_'+code)
def sha(text):
    b=text.encode('utf-8') if isinstance(text,str) else text
    return hashlib.sha256(b).hexdigest()
def canonical(x):
    return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
def digest(x):return sha(canonical(x))
def cue_evidence(cues,index,span=7):
    require(type(index) is int and 1<=index<=len(cues),'CUE_RANGE')
    return [{'cue_index':c.index,'start_ms':c.start_ms,'end_ms':c.end_ms,
            'text_private':c.text} for c in cues[max(0,index-1-span):min(len(cues),index+span)]]
def verify_batch(*,rows,cues_by_video,registry_by_video,full_queue_by_video,prior_cues_by_video,
                 expected_keys,expected_source_sha,expected_public_risk_counts):
    require(type(rows) is list and len(rows)==len(expected_keys) and len(rows)>0,'ROW_CENSUS')
    require(type(expected_keys) is set and len(expected_keys)==len(rows),'EXPECTED_SET')
    require(set(cues_by_video)==set(registry_by_video)==set(full_queue_by_video)==set(prior_cues_by_video),'INPUT_VIDEO_SET')
    require(set(cues_by_video)==SOURCE_VIDEO_IDS,'SOURCE_VIDEO_CENSUS')
    require(type(expected_source_sha) is str and len(expected_source_sha)==64,'SOURCE_PIN')
    queued={}
    all_counts=Counter()
    for v,ls in full_queue_by_video.items():
        for pin in ls:
            key=(v,pin['cue_index'],pin['kind'])
            require(key not in queued,'QUEUE_DUP')
            queued[key]=pin['cue_sha256'];all_counts[pin['kind']]+=1
            cues=cues_by_video[v]
            require(type(pin['cue_index']) is int and 1<=pin['cue_index']<=len(cues),'QUEUE_RANGE')
            require(sha(cues[pin['cue_index']-1].text)==pin['cue_sha256'],'QUEUE_SOURCE_MISMATCH')
    require(dict(all_counts)==expected_public_risk_counts,'RISK_QUEUE_CENSUS')
    seen=set();read_digest=[];kind_ct=Counter();out_ct=Counter();new_cues={};numeric_open=[];split_count=0
    for r in rows:
        require(type(r) is dict,'ROW_TYPE')
        key=(r.get('video_id'),r.get('cue_index'),r.get('kind'))
        require(key in expected_keys and key not in seen,'KEY_DUP_OR_EXTRA')
        seen.add(key);vid,i,kind=key
        require(vid in SOURCE_VIDEO_IDS and kind in KINDS,'KIND_OR_VIDEO')
        require(i not in prior_cues_by_video[vid],'PREVIOUSLY_REVIEWED_CUE')
        require(r.get('source_archive_sha256')==expected_source_sha,'SOURCE_ARCHIVE_DRIFT')
        cue=cues_by_video[vid][i-1]
        require(r.get('cue_sha256')==sha(cue.text)==queued.get(key),'CUE_SHA')
        require((r.get('start_ms'),r.get('end_ms'))==(cue.start_ms,cue.end_ms),'CUE_TIME')
        require(r.get('source_text_private')==cue.text,'CUE_TEXT')
        require(r.get('window_id')==f'W{((i-1)//40+1):05d}','WINDOW_ID')
        context=cue_evidence(cues_by_video[vid],i)
        require(r.get('context_cues_private')==context,'NEIGHBOR_CONTEXT')
        require(r.get('context_sha256')==digest(context),'CONTEXT_DIGEST')
        w=r['window_id'];matches=[p for p in registry_by_video[vid][w] if i in p['cue_indices']]
        require(len(matches)==1,'PARENT_CANDIDATE_UNIQUE')
        parent=matches[0]
        require(r.get('parent_claim_id')==parent['claim_id'],'PARENT_ID')
        require(r.get('parent_cue_indices')==parent['cue_indices'],'PARENT_CUES')
        parent_text=' | '.join(cues_by_video[vid][j-1].text for j in parent['cue_indices'])
        require(r.get('parent_sha256')==sha(parent_text)==parent['source_text_sha256'],'PARENT_SOURCE_SHA')
        require(r.get('status')==STATUS,'STATUS')
        require(r.get('semantic_kind') in DISPOSITIONS,'SEMANTIC_KIND')
        for f in ('speaker_meaning_private','scope_caution_private'):
            require(type(r.get(f)) is str and len(r[f])>=20,'MISSING_REASON_'+f)
        for f in FALSE_FIELDS:require(r.get(f) is False,'FALSE_APPROVAL_'+f)
        splits=r.get('provisional_subclaims') or []
        if splits:
            span=set(parent['cue_indices']);mapped=set()
            require(len(splits)>=2,'SPLIT_NOT_ACTUALLY_MULTIPLE')
            for s in splits:
                refs=s.get('source_cue_indices')
                require(type(refs) is list and refs and len(refs)==len(set(refs)) and set(refs)<=span,'SPLIT_SOURCE_CUES')
                require(type(s.get('provisional_meaning_private')) is str and len(s['provisional_meaning_private'])>=15,'SPLIT_MEANING')
                require(s.get('fact_approved') is False,'SPLIT_FALSE_APPROVAL')
                mapped.update(refs)
            require(mapped==span,'UNACCOUNTED_PARENT_CUES')
            split_count+=1
        kind_ct[kind]+=1;out_ct[r['semantic_kind']]+=1
        new_cues.setdefault(vid,set()).add(i)
        if r['semantic_kind'] in {'NUMERIC_CONFLICT_OPEN','NUMERIC_ASR_OPEN','HISTORICAL_NUMERIC_OPEN'}:
            numeric_open.append((vid,i))
        read_digest.append([*key,r['cue_sha256'],r['context_sha256'],r['parent_sha256'],
                            r['semantic_kind'],sha(r['speaker_meaning_private']),sha(r['scope_caution_private']),
                            digest(splits)])
    require(seen==expected_keys,'MISSING_EXPECTED')
    require(sum(kind_ct.values())==len(rows),'CENSUS_END')
    return {'schema':'V96_61_ORIGINAL_RISK_CUE_CHAT_REVIEW_NOT_GOLD_V1',
        'new_reviewed_risk_cues':len(rows),'selected_kind_counts':dict(sorted(kind_ct.items())),
        'review_outcome_counts':dict(sorted(out_ct.items())),
        'new_unique_source_cues_by_video':{v:len(ids) for v,ids in sorted(new_cues.items())},
        'draft_parent_partition_proposals':split_count,
        'numeric_source_open_cases':len(numeric_open),
        'source_bound_review_sha256':digest(sorted(read_digest)),
        'p0_go':False,'independent_gold':False,'source_wide_atomic_recall_certified':False,
        'financial_facts_certified':False,'personalized_advice_approved':False,
        'selected_reviewed_risk_fraction':len(rows)/sum(all_counts.values()),
        'unreviewed_risk_signals':sum(all_counts.values())-len(rows)}