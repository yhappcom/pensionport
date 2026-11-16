"""V87 public, fail-closed source custody for #7 targeted parent and gap review.

DOES NOT contain original SRT or private notes. A passing synthetic test is
not independent semantic recall or an approved financial recommendation.
"""
from __future__ import annotations
import hashlib,json
from collections import Counter
from pathlib import Path

OWNER_SHA='00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd'
V84_SHA='b8fa34d4f36a790608aa4e7f6662caf14567fee9c8eedef68000d1e1b3df9e2d'
V85_SHA='0c87078e870bb88536667cc5a60a68eaeff71914740c9571242dc988caaa584d'
V86_SHA='82b35be0c691aa832102255ac324e73a815c37259228370ff1c91cb53ca2e71d'
VIDEO_ID='4CQ4FjGT2gA'
TARGET_WINDOWS=('W00138','W00139','W00222','W00223','W00224','W00225')
EXPECTED_PARENT={
'W00138':('C01779','C01781','C01783','C01786','C01788','C01789','C01790'),
'W00139':('C01792','C01797','C01798','C01799','C01801','C01802','C01804'),
'W00222':('C02846','C02847','C02848','C02849','C02850','C02851','C02852'),
'W00223':('C02855','C02856','C02859','C02862','C02864'),
'W00224':('C02866','C02867','C02870','C02872','C02874'),
'W00225':('C02876','C02877','C02878','C02879','C02882','C02883')}
EXPECTED_COUNTS=(28,37,6,71)
V85_GAP_MEMBER='V85_PRIVATE_NEW5_295_UNCAPTURED_SOURCE_CONTEXT_NOT_NEGATIVE_GOLD.json'
V85_SEM_MEMBER='V85_PRIVATE_NEW5_31_MEANING_PROBES_NOT_FINANCE_APPROVAL.json'
V86_GAP_MEMBER='V86_PRIVATE_18_GAP_CUE_CONTEXTUAL_SEMANTIC_REVIEWS.json'
V86_SEM_MEMBER='V86_PRIVATE_VIDEO7_16_DISTINCT_PARENT_MEANING_REVIEWS.json'
V86_SCREEN_MEMBER='V86_PRIVATE_VIDEO7_269_WINDOW_AUTOMATED_SCREEN_ONLY.json'
V84_SEM_MEMBER='V84_PRIVATE_SIX_TO_TEN_SIX_SEMANTIC_PROBES_DO_NOT_UPLOAD_GITHUB.json'
FLAG_FIELDS=('fact_approved','independent_gold','official_parent_merged','personal_action_approved','v75_membership_verified')
ADDITIONAL_FALSE=('financial_fact_certified','independent_precision_recall_certified','personalized_advice_approved','full_window_semantics_certified')
VALID_GAP_TYPES={'TIME_FRAGMENT','INCOMPLETE_OBJECT','REFERENTIAL_TAIL','DUPLICATED_PREDICATE','DISCOURSE_BRIDGE',
'HISTORICAL_BOOKING_TAIL','CONTRAST_INCOMPLETE','DUPLICATED_COPULA','HEDGED_OPINION_END','CASHFLOW_NOUN_TAIL',
'LEDGER_LAYOUT_TAIL','HISTORICAL_EXPENSE_OBSERVATION','DISCOURSE_CONNECTOR','REPORTED_OBSERVATION_TAIL',
'SPEECH_INTENT_COMPLETION','QUESTION_TAIL','NAME_FRAGMENT','CONDITIONAL_BENEFIT_TAIL','PROPERTY_ENTITY_FRAGMENT',
'SEQUENCE_COMPLETION','DISCOURSE_REPETITION','PERSONA_DESCRIPTION_TAIL','ASSET_HEADING','INTENSIFIER',
'NARRATIVE_TRAIL','BUDGET_BRIDGE','TOPIC_INTRODUCTION_TAIL','LOCATION_ASR_UNCERTAIN'}
VALID_DISPOSITIONS={'MERGE_PREVIOUS','MERGE_ADJACENT','NEEDS_AUDIO','ASR_FRAGMENT','TOPIC_ONLY'}
VALID_PARENT_TYPES={'CASE_SPECIFIC_PENSION_EXPLANATION','HISTORICAL_PERSONAL_HISTORY','RETURN_LUMP_SUM_TESTIMONY',
'QUESTION_NOT_FACT','MIXED_REPAYMENT_AND_TOPUP_TESTIMONY','HISTORICAL_ELIGIBILITY_RECOLLECTION',
'TIME_DEPENDENT_MAXIMUM_PERIOD','HISTORICAL_SOCIAL_TREND','HYPOTHETICAL_TIMELINE_RECONSTRUCTION',
'REPAYMENT_DURATION_RECOVERY','HYPOTHETICAL_PERIOD_SUM','INCOMPLETE_PERSONAL_TIMING',
'PAYMENT_FUNDING_MEMORY','HISTORICAL_EMPLOYMENT_DATE','CREDIT_RATING_BOUNDARY_EXPLANATION',
'ASOF_CREDIT_FILTER_OPINION','TENOR_VS_ISSUANCE_ADVICE','CREDIT_TERM_OVERGENERALIZATION',
'TENOR_RISK_TRADEOFF','PERSONAL_ASOF_BUY_OPINION','UNSUPPORTED_SPREAD_PREDICTION',
'UNCERTAIN_RATE_RECALL','HISTORIC_CREDIT_SPREAD_RECALL','CONDITIONAL_FUTURE_CYCLE',
'UNVERIFIED_MARK_TO_MARKET_LOSS','READING_HISTORICAL_CASE','BOND_TRADE_LIST_TESTIMONY',
'RISING_YIELD_TRADE_TESTIMONY','LONG_DURATION_RISK_OPINION','HISTORICAL_BOND_ADVICE',
'RETROSPECTIVE_INVESTMENT_JUDGMENT','COUPON_COUNT_TESTIMONY',
'INTEREST_REINVESTMENT_MEMORY','HISTORICAL_CASH_YIELD_ARITHMETIC',
'RETROSPECTIVE_YIELD_PRAISE','QUESTION_ASOF_EVALUATION','HOLD_TO_MATURITY_QUALIFIED'}

def guard(condition,reason):
    if not condition:raise ValueError('V87_'+reason)

def sha(b):return hashlib.sha256(b).hexdigest()

def canonical(obj):return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')

def digest(obj):return sha(canonical(obj))

def verify_pinned_archive(path,pin,label):
    p=Path(path); guard(p.is_file(),label+'_MISSING');guard(sha(p.read_bytes())==pin,label+'_SHA_CHANGED')
    return p

def ensure_false(r):
    guard(r.get('status')=='SOURCE_BOUND_CHAT_SHADOW_NOT_INDEPENDENT_GOLD','BAD_STATUS')
    for k in FLAG_FIELDS+ADDITIONAL_FALSE:
        guard(r.get(k) is False,'FALSE_APPROVAL_'+k)

def verify_one_gap(r,source):
    """Check one explicitly reviewed lexical tail against immutable original V85 gap row."""
    guard(r.get('video_no')==source['video_no'] and r.get('cue_index')==source['cue_index'],'GAP_ID')
    for k in ('video_id','start_ms','end_ms','cue_text_private','cue_text_sha256','adjacent_cues_private',
              'left_candidate','right_candidate','speech_act_category'):
        guard(r.get(k)==source[k],'GAP_SOURCE_CHANGED_'+k)
    guard(r['cue_text_sha256']==sha(r['cue_text_private'].encode('utf-8')),'GAP_CUE_HASH')
    guard(r.get('adjacent_context_sha256')==digest(r['adjacent_cues_private']),'GAP_ADJACENCY_HASH')
    guard(r['speech_act_category']=='LEXICAL_TAIL','NONLEXICAL_MARKED_REVIEW')
    guard(r.get('semantic_kind') in VALID_GAP_TYPES,'GAP_SEMANTIC_KIND')
    guard(r.get('disposition') in VALID_DISPOSITIONS,'GAP_DISPOSITION')
    for k in ('meaning_private','risk_private'):
        guard(type(r.get(k)) is str and len(r[k])>=30,'MISSING_'+k)
    ensure_false(r)
    return digest([r['video_no'],r['cue_index'],r['cue_text_sha256'],r['semantic_kind'],r['disposition'],
                   sha(r['meaning_private'].encode('utf-8')),sha(r['risk_private'].encode('utf-8'))])

def expected_parent_source(cues,registries,key):
    wid,cid=key
    guard(wid in registries,'PARENT_WINDOW_ABSENT')
    matches=[x for x in registries[wid] if x['claim_id']==cid]
    guard(len(matches)==1,'PARENT_NOT_UNIQUE')
    p=matches[0];ids=p['cue_indices']
    guard(bool(ids) and len(set(ids))==len(ids),'PARENT_INDICES_BAD')
    guard(all((int(wid[1:])-1)*40 < i <= min(int(wid[1:])*40,len(cues)) for i in ids),'PARENT_WINDOW_LEAK')
    phrase=' | '.join(cues[i-1].text for i in ids)
    ctx=[{'cue_index':i,'start_ms':cues[i-1].start_ms,'end_ms':cues[i-1].end_ms,
          'text_private':cues[i-1].text} for i in range(max(1,ids[0]-2),min(len(cues),ids[-1]+2)+1)]
    guard(sha(phrase.encode('utf-8'))==p['source_text_sha256'],'V33_SOURCE_DRAFT_CHANGED')
    return {'window_id':wid,'claim_id':cid,'cue_indices':ids,'source_excerpt_private':phrase,
            'start_ms':cues[ids[0]-1].start_ms,'end_ms':cues[ids[-1]-1].end_ms,
            'adjacent_cues_private':ctx,'source_sha256':p['source_text_sha256'],
            'adjacent_context_sha256':digest(ctx)}

def verify_one_parent(r,source):
    guard(r.get('video_no')==7 and r.get('video_id')==VIDEO_ID,'PARENT_VIDEO')
    for k in ('window_id','claim_id','cue_indices','start_ms','end_ms','source_excerpt_private',
              'adjacent_cues_private','source_sha256','adjacent_context_sha256'):
        guard(r.get(k)==source[k],'PARENT_SOURCE_CHANGED_'+k)
    guard(sha(r['source_excerpt_private'].encode('utf-8'))==r['source_sha256'],'PARENT_SOURCE_HASH')
    guard(digest(r['adjacent_cues_private'])==r['adjacent_context_sha256'],'PARENT_CONTEXT_HASH')
    guard(r.get('semantic_kind') in VALID_PARENT_TYPES,'PARENT_KIND')
    guard(type(r.get('risk_domain')) is str and len(r['risk_domain'])>=5,'NO_DOMAIN')
    for k in ('speaker_meaning_private','risk_limit_private'):
        guard(type(r.get(k)) is str and len(r[k])>=35,'PARENT_MISSING_'+k)
    ensure_false(r)
    return digest([r['window_id'],r['claim_id'],r['source_sha256'],r['semantic_kind'],
                   sha(r['speaker_meaning_private'].encode('utf-8')),
                   sha(r['risk_limit_private'].encode('utf-8'))])

def verify_six_window_screens(rows,all_screens):
    guard(type(rows) is list and len(rows)==6,'SIX_SCREEN_COUNT')
    m={x['window_id']:x for x in all_screens}
    guard(len(m)==len(all_screens)==269,'V86_SCREEN_269_PRESERVATION')
    keys=[x.get('window_id') for x in rows]
    guard(tuple(keys)==TARGET_WINDOWS,'TARGET_SCREEN_IDS')
    for x in rows:guard(x==m[x['window_id']],'PRIOR_SCREEN_DRIFT')
    return digest(rows)

def verify_gap_reviews(rows,prior_gap,prior18):
    guard(type(rows) is list and len(rows)==28,'REMAINING28_CENSUS')
    p={(x['video_no'],x['cue_index']):x for x in prior_gap if x['speech_act_category']=='LEXICAL_TAIL'}
    guard(len(p)==46,'PREVIOUS46_LEXICAL_CENSUS')
    prev={(x['video_no'],x['cue_index']) for x in prior18}
    guard(len(prev)==18 and prev<=set(p),'PREVIOUS18_CENSUS')
    expected=set(p)-prev;guard(len(expected)==28,'REMAINING28_EXPECTED')
    seen=set();digests=[]
    for r in rows:
        k=(r.get('video_no'),r.get('cue_index'));guard(k in expected and k not in seen,'GAP_REPEATED_OR_WRONG')
        seen.add(k);digests.append(verify_one_gap(r,p[k]))
    guard(seen==expected,'GAP_28_INCOMPLETE')
    return digest(sorted(digests))

def verify_parent_reviews(rows,cues,reg,prior_keys):
    expected={(w,c) for w,cs in EXPECTED_PARENT.items() for c in cs}
    guard(len(expected)==37,'TARGET37_CORRUPT')
    guard(type(rows) is list and len(rows)==37,'REVIEW_37_COUNT')
    guard(not (expected&prior_keys),'PRIOR_SEMANTIC_PARENT_OVERLAP')
    seen=set();hashes=[];counts=Counter()
    for r in rows:
        k=(r.get('window_id'),r.get('claim_id'))
        guard(k in expected and k not in seen,'EXTRA_OR_DUPLICATE_PARENT');seen.add(k)
        counts[k[0]]+=1
        hashes.append(verify_one_parent(r,expected_parent_source(cues,reg,k)))
    guard(seen==expected,'TARGET37_NOT_COMPLETE')
    guard(set(counts)==set(TARGET_WINDOWS),'SIX_WINDOWS_NOT_REVIEWED')
    guard(sum(counts.values())==37,'COUNT_MISMATCH')
    return digest(sorted(hashes)),dict(sorted(counts.items()))

def event_chain(items):
    """SHA chain for local shadow review; NEVER a historical V40 ledger or gold set."""
    guard(type(items) is list and len(items)>0,'EMPTY_CHAIN')
    prev='0'*64;events=[]
    for i,(kind,key,payload_sha) in enumerate(items,1):
        guard(type(kind) is str and bool(kind),'CHAIN_KIND')
        guard(type(key) is str and bool(key),'CHAIN_KEY')
        guard(type(payload_sha) is str and len(payload_sha)==64 and all(c in '0123456789abcdef' for c in payload_sha),'CHAIN_HASH')
        next_hash=digest([i,kind,key,payload_sha,prev])
        events.append((i,kind,key,payload_sha,prev,next_hash));prev=next_hash
    guard(len({(k,key) for _,k,key,_,_,_ in events})==len(events),'CHAIN_DUPLICATE_KEY')
    return events,prev

def non_gold_disposition():
    return {'v75_source_lineage_verified':False,'official_new_unique_review_count':0,
            'independent_semantic_precision_recall':'NO_SCORE','financial_fact_approvals':0,
            'personalized_advice_approvals':0,'p0_go':False,
            'all_269_video7_windows_semantically_reviewed':False}