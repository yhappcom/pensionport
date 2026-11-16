"""V88 public, synthetic-testable source-custody and no-false-GO gate.
Never includes source SRT, private interpretations, or private V75 lineage.
Public CI only tests synthetic fixtures; the private replay requires owner SRT.
"""
from __future__ import annotations
import hashlib,json
from collections import Counter
from v87_targeted_source_guard import expected_parent_source, event_chain

VIDEO_ID='4CQ4FjGT2gA'
EXPECTED={
'W00093':('C01278','C01279','C01281','C01283'),
'W00110':('C01481','C01482','C01483','C01490'),
'W00140':('C01807','C01808','C01809','C01812'),
'W00143':('C01840','C01844','C01845','C01849'),
'W00151':('C01935','C01936','C01938','C01945'),
'W00162':('C02072','C02074','C02075','C02079'),
'W00174':('C02205','C02206','C02208','C02212'),
'W00226':('C02885','C02886','C02887','C02888'),
'W00238':('C03003','C03005','C03006','C03009'),
'W00239':('C03011','C03012','C03014','C03015')}
CATEGORIES={'QUESTION_NOT_FACT','DESCRIPTIVE_FINANCE','REPORTED_NUMERIC','HISTORICAL_CASE','CONDITIONAL_ADVICE','HYPOTHESIS','OPINION'}
FALSE_FLAGS=('fact_approved','independent_gold','official_parent_merged','personal_action_approved','v75_membership_verified',
'financial_fact_certified','independent_precision_recall_certified','personalized_advice_approved','full_window_semantics_certified')
STATUS='SOURCE_BOUND_CHAT_SHADOW_NOT_INDEPENDENT_GOLD'
V84_SHA='b8fa34d4f36a790608aa4e7f6662caf14567fee9c8eedef68000d1e1b3df9e2d'
V85_SHA='0c87078e870bb88536667cc5a60a68eaeff71914740c9571242dc988caaa584d'
V86_SHA='82b35be0c691aa832102255ac324e73a815c37259228370ff1c91cb53ca2e71d'
V87_SHA='ff028b1c51f2429980fca26a1ddf0f607ed7d2a198b1a53fc7597a9928eb58b4'
OWNER_SHA='00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd'

def require(v,reason):
    if not v:raise ValueError('V88_'+reason)
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
def digest(x):return sha(canonical(x))
def check_disposition(row):
    require(row.get('status')==STATUS,'BAD_STATUS')
    for flag in FALSE_FLAGS:require(row.get(flag) is False,'FALSE_GO_'+flag)
    require(row.get('audio_verified') is False,'FALSE_AUDIO_VERIFICATION')
    require(row.get('law_current_verified') is False,'FALSE_LAW_APPROVAL')
    require(row.get('semantic_kind') in CATEGORIES,'UNSUPPORTED_SEMANTIC_CLASS')
    for k in ('speaker_meaning_private','scope_caution_private'):
        require(type(row.get(k)) is str and len(row[k])>=55,'MISSING_'+k)
    require(type(row.get('risk_domain')) is str and len(row['risk_domain'])>=5,'MISSING_DOMAIN')
    return True

def check_one_review(row,cues,reg):
    require(row.get('video_no')==7 and row.get('video_id')==VIDEO_ID,'FOREIGN_VIDEO')
    w=row.get('window_id');c=row.get('claim_id')
    require(w in EXPECTED and c in EXPECTED[w],'UNEXPECTED_PARENT_ID')
    src=expected_parent_source(cues,reg,(w,c))
    for field in ('window_id','claim_id','cue_indices','source_excerpt_private','start_ms','end_ms',
        'adjacent_cues_private','source_sha256','adjacent_context_sha256'):
        require(row.get(field)==src[field],'SOURCE_CHANGED_'+field)
    require(sha(row['source_excerpt_private'].encode('utf-8'))==row['source_sha256'],'SOURCE_HASH')
    require(digest(row['adjacent_cues_private'])==row['adjacent_context_sha256'],'ADJACENT_HASH')
    check_disposition(row)
    return digest([w,c,row['source_sha256'],row['semantic_kind'],
        sha(row['speaker_meaning_private'].encode('utf-8')),sha(row['scope_caution_private'].encode('utf-8'))])

def verify_batch(rows,cues,regs,previous,selected_screens):
    require(type(rows) is list and len(rows)==40,'FORTY_PARENT_COUNT')
    require(type(previous) is set and len(previous)==69,'PRIOR69_INCOMPLETE')
    require(len({w for w,c in previous})==31,'PRIOR31_WINDOWS_DRIFT')
    all_w=set(EXPECTED)
    require(not (all_w & {w for w,c in previous}),'TARGET_WINDOW_ALREADY_REVIEWED')
    expected={(w,c) for w,cs in EXPECTED.items() for c in cs}
    require(len(expected)==40,'EXPECTED_MAP_CORRUPT')
    require(type(selected_screens) is list and len(selected_screens)==10,'SCREEN10_COUNT')
    require({x.get('window_id') for x in selected_screens}==all_w,'SCREEN_IDS_BAD')
    for s in selected_screens:
        require(s.get('video_id')==VIDEO_ID and s.get('video_no')==7,'SCREEN_VIDEO_WRONG')
        require(s.get('screen_status') is not None,'NO_SCREEN_STATUS')
        require(s.get('manual_reviewed_all_parents') is False,'FALSE_FULL_WINDOW_REVIEW')
        n=int(s['window_id'][1:]); a=(n-1)*40; b=min(n*40,len(cues)); batch=cues[a:b]
        require(bool(batch) and [q.index for q in batch]==list(range(a+1,b+1)),'SCREEN_CUE_INDEX_DRIFT')
        require(s.get('first_cue')==a+1 and s.get('last_cue')==b,'SCREEN_BOUNDS')
        require(s.get('draft_parent_count')==len(regs[s['window_id']]),'SCREEN_DRAFT_PARENT_COUNT')
        require(s.get('source_window_sha256')==sha(' '.join(q.text for q in batch).encode('utf-8')),'SCREEN_ORIGINAL_HASH')
        for k in ('fact_approved','independent_gold','personal_action_approved'):
            require(s.get(k) is False,'SCREEN_FALSE_APPROVAL_'+k)
    seen=set(); hashes=[]; count=Counter()
    for r in rows:
        key=(r.get('window_id'),r.get('claim_id'))
        require(key in expected and key not in seen and key not in previous,'DUPLICATE_OR_UNEXPECTED')
        seen.add(key);count[key[0]]+=1
        hashes.append(check_one_review(r,cues,regs))
    require(seen==expected,'MISSING_PARENT')
    require(set(count)==all_w and all(v==4 for v in count.values()),'WINDOW_COUNT_BAD')
    require(len(previous|seen)==109,'TOTAL109_INVALID')
    require(len({w for w,c in previous|seen})==41,'TOTAL41_WINDOWS_INVALID')
    return {'new_parent_count':40,'new_window_count':10,'new_parent_digest_sha256':digest(sorted(hashes)),
        'prior_parent_count':69,'cumulative_parent_count':109,
        'cumulative_windows_with_samples':41,'cumulative_windows_without_samples':228,
        'prior_3_need_audio_unchanged':3,'official_new_unique_count':0,
        'full_window_semantic_approval':False,'precision_recall':'NO_SCORE',
        'approved_financial_facts':0,'personal_advice_approved':False,'p0_go':False}