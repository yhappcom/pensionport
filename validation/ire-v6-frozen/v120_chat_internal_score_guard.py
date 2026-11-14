"""V120 ChatGPT-native source-first comparison integrity checks.

This validates data lineage, arithmetic and non-independent labels; it does NOT
validate meaning, qualify a financial fact, establish model independence, or infer
true accuracy from source coverage. Private prose must never be committed.
"""
from __future__ import annotations
import hashlib
import json
import math
import re

EXPECTED_OWNER_SOURCE_SHA256 = "19ce2a37a37079dc0a6ea4dde3d031bdc2b7bb990f0506fd1e0610442dbf0145"

class UnsafeScore(ValueError):
    pass

def required(p,code):
    if not p: raise UnsafeScore('V120_'+code)

def digest(b):
    return hashlib.sha256(b).hexdigest()

def checked_sha(value):
    return isinstance(value,str) and re.fullmatch('[a-f0-9]{64}',value) is not None

def audit(precommit,A,B,score,actual_source_bytes,old_prediction_bytes,private_A_bytes,private_B_bytes):
    """Return hash-only, non-sensitive receipt; fail on any ungrounded certification."""
    required(precommit.get('schema')=='V120_PRECOMMITTED_ASSET_DIGESTS_V1','PRECOMMIT_SCHEMA')
    required(A.get('schema')=='V120_CHAT_SOURCE_FIRST_PASS_A_PARTIAL_PRIOR_TOPIC_EXPOSURE_V1','A_SCHEMA')
    required(B.get('schema')=='V120_CHAT_COUNTEREXAMPLE_PASS_B_AND_ADJUDICATED_REFERENCE_V1','B_SCHEMA')
    required(score.get('schema')=='V120_CHAT_INTERNAL_REFERENCE_ONE_TO_ONE_CROSSCHECK_NOT_EXTERNAL_GOLD_V1','SCORE_SCHEMA')
    for k in ('source_sha256','engine_predictions_pre_reveal_sha256','first_pass_A_sha256'):
        required(checked_sha(precommit.get(k)), 'PRECOMMIT_'+k)
    required(digest(actual_source_bytes)==precommit['source_sha256']==EXPECTED_OWNER_SOURCE_SHA256,'SOURCE_SHA')
    source_text=actual_source_bytes.decode('utf-8-sig').replace('\r\n','\n').replace('\r','\n')
    blocks=re.split(r'\n\s*\n',source_text.strip())
    bycue={}
    for expected,block in enumerate(blocks,1):
        lines=block.split('\n')
        required(len(lines)>=3 and lines[0].strip()==str(expected),'SOURCE_CUE_INDEX')
        bycue[expected]=' '.join(line.strip() for line in lines[2:] if line.strip())
        required(bool(bycue[expected]),'SOURCE_CUE_EMPTY')
    required(len(bycue)==173,'SOURCE_CUE_COUNT')
    required(digest(old_prediction_bytes)==precommit['engine_predictions_pre_reveal_sha256'],'BASELINE_SHA')
    required(digest(private_A_bytes)==precommit['first_pass_A_sha256'],'A_SHA')
    required(digest(private_B_bytes)==score['B_sha256'],'B_SHA')
    required(B['A_frozen_sha256']==precommit['first_pass_A_sha256'],'A_LOCK')
    required(B['engine_predictions_pre_reveal_sha256']==precommit['engine_predictions_pre_reveal_sha256'],'BASELINE_LOCK')
    required(score['prior_prediction_sha256']==precommit['engine_predictions_pre_reveal_sha256'],'SCORE_LOCK')
    required(score['A_sha256']==precommit['first_pass_A_sha256'],'SCORE_A_LOCK')
    for item in (A,B,score):
        required(item['video_id']==precommit['video_id']=='Yb_5prWaqhk','VIDEO_ID')
    required(A['original_cue_count']==precommit['A_cue_parent_census']==173,'CUE_COUNT')
    required(precommit['blindness']=='PARTIAL_PREVIOUS_TOPIC_EXPOSURE','BLIND_TRUTH')
    required(A['prior_exposure_status']=='PRIOR_SUMMARY_TOPICS_SEEN_NOT_STRICTLY_BLIND','EXPOSURE')
    required(B['same_chat_review_not_externally_independent'] is True,'MODEL_DEPENDENCE')
    required(A['reference_gold_certified'] is False,'A_FAKE_GOLD')
    required(B['external_gold'] is False,'B_FAKE_GOLD')
    required(score['independent_gold'] is False and score['p0_go'] is False,'SCORE_FAKE_GO')
    required(score['external_certified_precision'] is None and score['external_certified_recall'] is None,'EXTERNAL_FAKE_SCORE')
    required(score['evaluation_type']=='CHAT_INTERNAL_REFERENCE_SCORE_PROVISIONAL','SCORE_LABEL')
    required(B['official_financial_fact_approved']==0,'FINANCE_FALSE_APPROVAL')
    required(B['source_audio_verified'] is False and B['video_screen_verified'] is False,'AUDIO_FALSE_VERIFIED')
    required(len(A['first_pass_claims'])==58,'A_COUNT')
    segments=A['source_segments']
    required([i for x in segments for i in range(x['range'][0],x['range'][1]+1)]==list(range(1,174)),'SOURCE_SEGMENT_CENSUS')
    required(len(B['reference_claims'])==59,'B_COUNT')
    required(len(B['revisions'])==20,'REVISION_COUNT')
    required(B['A_claim_count']==58 and B['chat_reference_claim_count']==59 and B['B_revision_count']==20,'B_CENSUS')
    assert isinstance(score['counts'],dict)
    counts=score['counts']
    for k in ('predicted_atoms','chat_reference_candidates','tp','fp','fn','high_critical_reference_candidates','high_critical_tp','high_critical_fn','A_claims','B_adjudication_revision_records'):
        required(type(counts.get(k))==int and counts[k]>=0,'COUNT_'+k)
    required(counts['predicted_atoms']==46 and counts['chat_reference_candidates']==59,'PRED_REF_COUNTS')
    required(counts['tp']+counts['fp']==46 and counts['tp']+counts['fn']==59,'TP_FP_FN')
    required(len(score['predicted_atom_verdicts'])==46 and len(score['unmatched_chat_reference'])==counts['fn'],'MATCH_CENSUS')
    refs={x['id'] for x in B['reference_claims']}
    required(len(refs)==59,'REF_DUPLICATE_ID')
    expected_hi=sum(x['risk'] in ('HIGH','CRITICAL') for x in B['reference_claims'])
    required(expected_hi==counts['high_critical_reference_candidates'],'HIGH_CENSUS')
    used=[]
    for row in score['predicted_atom_verdicts']:
        required(row['verdict'] in ('TP','FP'),'VERDICT')
        if row['verdict']=='TP':
            required(row['reference_id'] in refs,'UNKNOWN_REFERENCE')
            used.append(row['reference_id'])
        else:
            required(row['reference_id'] is None,'FALSE_MATCH_REFERENCE')
    required(len(used)==len(set(used))==counts['tp'],'ONE_TO_ONE')
    missing=set(refs)-set(used)
    required(missing=={r['reference_id'] for r in score['unmatched_chat_reference']},'FN_SET')
    required(len({r['prediction_id'] for r in score['predicted_atom_verdicts']})==46,'PRED_ID_DUPLICATE')
    missed_risk=sum(r['risk'] in ('HIGH','CRITICAL') for r in score['unmatched_chat_reference'])
    required(missed_risk==counts['high_critical_fn'],'HIGH_FN_COUNT')
    required(counts['high_critical_tp']+missed_risk==expected_hi,'HIGH_TP_FN_COUNT')
    for key,num,den in [
        ('chat_internal_precision',counts['tp'],46),
        ('chat_internal_recall',counts['tp'],59),
        ('chat_internal_high_risk_recall',counts['high_critical_tp'],expected_hi)]:
        required(type(score.get(key)) in (float,int) and math.isclose(score[key],num/den,rel_tol=0,abs_tol=1e-12),'METRIC_'+key)
    required('REFERENCE_DUPLICATE_R045_R046_POTENTIAL_OVERSPLIT' in score['limitations'],'SCORE_LIMITATION')
    required('REFERENCE_AUTHORED_BY_SAME_MODEL_IN_SAME_TURN' in score['limitations'],'NOT_INDEPENDENT')
    required('FALSE_POSITIVE_HERE_MEANS_NOT_ONE_TO_ONE_NOT_FACTUALLY_FALSE' in score['limitations'],'FP_LABEL')
    ids={p['id'] for p in A['first_pass_claims']}
    required(len(ids)==58,'A_DUP_ID')
    covered={c for p in A['first_pass_claims'] for c in p['cue_indices']}
    required(sorted(set(range(1,174))-covered)==A['context_cues_without_direct_claim'],'CONTEXT_GAP_CENSUS')
    for p in A['first_pass_claims']:
        required(all(type(c)==int and 1<=c<=173 for c in p['cue_indices']),'A_SOURCE_RANGE')
        required(checked_sha(p['source_text_sha256']),'A_SOURCE_DIGEST')
        required(digest(' | '.join(bycue[c] for c in p['cue_indices']).encode())==p['source_text_sha256'],'A_SOURCE_HASH_MISMATCH')
    for p in B['reference_claims']:
        required(all(type(c)==int and 1<=c<=173 for c in p['cue_indices']),'B_SOURCE_RANGE')
        required(checked_sha(p['source_text_sha256']),'B_SOURCE_DIGEST')
        required(digest(' | '.join(bycue[c] for c in p['cue_indices']).encode())==p['source_text_sha256'],'B_SOURCE_HASH_MISMATCH')
    return {'schema':'V120_PUBLIC_INTERNAL_SCORE_GUARD_RECEIPT_V1',
        'video_id':precommit['video_id'],'source_sha256':precommit['source_sha256'],
        'precommit_sha256':digest(json.dumps(precommit,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()),
        'pass_a_sha256':precommit['first_pass_A_sha256'],'pass_b_sha256':score['B_sha256'],
        'prior_prediction_sha256':precommit['engine_predictions_pre_reveal_sha256'],
        'prior_topic_exposure':True,'external_independent_gold':False,
        'actual_chat_internal_reference_score_provisional':True,
        'previous_predictions':46,'chat_reference_candidates':59,
        'tp':counts['tp'],'fp':counts['fp'],'fn':counts['fn'],
        'high_critical_tp':counts['high_critical_tp'],'high_critical_fn':counts['high_critical_fn'],
        'precision_provisional':score['chat_internal_precision'],
        'recall_provisional':score['chat_internal_recall'],
        'high_risk_recall_provisional':score['chat_internal_high_risk_recall'],
        'model_internal_inference_seconds':None,'official_source_http_body_sha256_pinned':False,
        'finance_facts_approved':0,'knowledge_merges':0,'p0_go':False}
