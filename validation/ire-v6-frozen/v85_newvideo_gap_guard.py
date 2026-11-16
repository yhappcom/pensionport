"""V85 first-ten owner-source gap and candidate custody, with NO private source in Git.

The returned counts are source/lineage tests, NOT semantic precision, legal fact
approval, independent-gold recall, or individualized investment advice.
"""
from __future__ import annotations
import re,zipfile,json
from collections import Counter
from pathlib import Path
from v77_private_v33_replay import sha,digest
from v84_gap_extension_guard import (new_video_census,audit_v83_private_custody,
    check_94_speechact_reviews,check_new5_manual_samples)

V84_ARCHIVE_SHA='b8fa34d4f36a790608aa4e7f6662caf14567fee9c8eedef68000d1e1b3df9e2d'
V84_GAP_MEMBER='V84_PRIVATE_94_REVIEWED_CONTEXT_SPEECH_ACTS_DO_NOT_UPLOAD_GITHUB.json'
V84_SIX_MEMBER='V84_PRIVATE_SIX_TO_TEN_SIX_SEMANTIC_PROBES_DO_NOT_UPLOAD_GITHUB.json'
COUNT_PIN={6:{'ASSENT':8,'DISCOURSE':6,'COURTESY':1,'LAUGHTER':1,'LEXICAL_TAIL':5},
    7:{'ASSENT':108,'DISCOURSE':29,'COURTESY':14,'LAUGHTER':3,'LEXICAL_TAIL':32},
    8:{'ASSENT':11,'DISCOURSE':13,'COURTESY':1,'LAUGHTER':0,'LEXICAL_TAIL':4},
    9:{'ASSENT':30,'DISCOURSE':24,'COURTESY':0,'LAUGHTER':0,'LEXICAL_TAIL':5},
    10:{'ASSENT':0,'DISCOURSE':0,'COURTESY':0,'LAUGHTER':0,'LEXICAL_TAIL':0}}
CRITICAL_LEXICAL_KEYS=[(6,361),(7,1076),(7,2721),(7,3664),(7,4692),(7,5609),
    (7,5929),(7,7298),(7,8911),(7,9894),(7,10189),(8,801),(8,802),
    (8,953),(8,1001),(9,70),(9,780),(9,799)]
SAMPLE_KEYS={
    6:[('W00009','C00111'),('W00009','C00118'),('W00012','C00144'),('W00016','C00189'),('W00019','C00226')],
    7:[('W00010','C00130'),('W00029','C00439'),('W00048','C00720'),('W00067','C00974'),('W00086','C01197'),
       ('W00106','C01449'),('W00125','C01642'),('W00144','C01865'),('W00163','C02084'),('W00183','C02329'),
       ('W00202','C02610'),('W00221','C02839'),('W00221','C02840'),('W00240','C03028'),('W00259','C03239')],
    8:[('W00002','C00016'),('W00006','C00082'),('W00015','C00209'),('W00024','C00332')],
    9:[('W00013','C00195'),('W00019','C00293'),('W00024','C00360'),('W00029','C00425'),('W00030','C00429')],
    10:[('W00001','C00002'),('W00001','C00003')]}
ASSERT_FALSE=('fact_approved','independent_gold','official_parent_merged',
              'personal_action_approved','v75_membership_verified','negative_gold_certified')
CATEGORIES=('ASSENT','DISCOURSE','COURTESY','LAUGHTER','LEXICAL_TAIL')
VALID_KINDS={'PROCEDURAL_EXPLANATION','QUESTION','SCENARIO_AND_PREFERENCE',
 'ACTION_SUGGESTION','NUMERIC_PROJECTION','HISTORICAL_ALLOCATION','ACCOUNT_AGGREGATION',
 'MOTIVATIONAL_OVERGENERALIZATION','REPORTED_DIALOGUE_AND_OPINION',
 'IMPLEMENTATION_WORKFLOW','ASSUMPTION_AND_SIMULATION','TESTIMONIAL_AND_SUGGESTION',
 'HISTORICAL_RULE_RECALL','PERSONAL_ACCOUNT_AND_AMOUNT','HISTORICAL_SINGLE_STOCK_PNL',
 'INVESTMENT_LEARNING_AND_DURATION_RISK','CREDIT_DURATION_FILTER',
 'YIELD_COMPARISON_FILTER','COUNTERFACTUAL_ESTIMATE','REFLECTIVE_INVESTMENT_RULE',
 'PENSION_PRODUCT_ELIGIBILITY','TWO_RISK_SCENARIOS','HEDGING_TIME_HORIZON_OPINION',
 'RISK_WARNING_AND_ADVICE','HISTORICAL_RATE_AND_CAUSAL_HYPOTHESIS',
 'FX_BENCHMARK_OPINION','OPPORTUNITY_COST','FX_SPREAD_EXPLANATION',
 'HISTORICAL_FEE_NUMERIC','QUESTION_AND_GENERAL_ADVICE','TAX_DEFERRAL_EXPLANATION'}

def require(c,code):
    if not c: raise ValueError('V85_'+code)

def categorize(text):
    t=re.sub(r'^\s*>>\s*','',text.strip()).strip(' ,.?!~')
    if t in ('네','예','응','맞아요','그렇죠','그죠','네네','예예'):return 'ASSENT'
    if t in ('음','어','아','오','와','야','아하'):return 'DISCOURSE'
    if t in ('안녕하세요','감사합니다'):return 'COURTESY'
    if any(s in t for s in ('웃음','ㅎㅎ','ㅋㅋ')):return 'LAUGHTER'
    return 'LEXICAL_TAIL'

def adjacent(cues,index):
    return [{'cue_index':j,'start_ms':cues[j-1].start_ms,
        'end_ms':cues[j-1].end_ms,'text_private':cues[j-1].text}
        for j in range(max(1,index-2),min(len(cues),index+2)+1)]

def expected_unassigned(reg,cues,video_id,video_no):
    # Each segment is source bound by V33 candidate checks, not guessed from text.
    assigned={i for rows in reg.values() for r in rows for i in r['cue_indices']}
    mapping={i:(w,row['claim_id']) for w,rows in reg.items() for row in rows for i in row['cue_indices']}
    out=[]
    for c in cues:
        if c.index in assigned:continue
        left=next((mapping[i] for i in range(c.index-1,max(0,c.index-5),-1) if i in mapping),None)
        right=next((mapping[i] for i in range(c.index+1,min(len(cues)+1,c.index+6)) if i in mapping),None)
        out.append({'video_no':video_no,'video_id':video_id,'cue_index':c.index,
            'cue_text_private':c.text,'cue_text_sha256':sha(c.text.encode('utf-8')),
            'start_ms':c.start_ms,'end_ms':c.end_ms,
            'adjacent_cues_private':adjacent(cues,c.index),
            'left_candidate':list(left) if left else None,
            'right_candidate':list(right) if right else None,
            'speech_act_category':categorize(c.text)})
    return out

def validate_gap_records(cues_byvid,reg_byvid,records):
    require(type(records) is list and len(records)==295,'GAP_COUNT_DRIFT')
    video_ids={6:'3MyhYE2jmuE',7:'4CQ4FjGT2gA',8:'OfkY343OaNs',9:'YNOSY15ppf8',10:'VKr060rIirM'}
    expected={}
    for n,vid in video_ids.items():
        for row in expected_unassigned(reg_byvid[vid],cues_byvid[vid],vid,n):
            key=(n,row['cue_index']);require(key not in expected,'SOURCE_ID_COLLISION');expected[key]=row
    require(len(expected)==295,'SOURCE_GAP_REPLAY_DRIFT')
    checked={};counts=Counter();byvideo={};shadow=[]
    for r in records:
        require(type(r) is dict,'GAP_RECORD_INVALID')
        key=(r.get('video_no'),r.get('cue_index'))
        require(key in expected and key not in checked,'GAP_WRONG_OR_DUPLICATE_ID')
        e=expected[key];checked[key]=1
        for k in ('video_id','cue_text_private','cue_text_sha256','start_ms','end_ms',
                 'adjacent_cues_private','left_candidate','right_candidate','speech_act_category'):
            require(r.get(k)==e[k],'SOURCE_CONTEXT_OR_CLASS_CHANGED')
        require(r.get('adjacent_context_sha256')==digest(e['adjacent_cues_private']),
                'NEIGHBOR_DIGEST_MISMATCH')
        require(r.get('status')=='SOURCE_BOUND_AUX_CONTEXT_NOT_ATOMIC_FACT','FALSE_GAP_STATUS')
        for f in ASSERT_FALSE:require(r.get(f) is False,'FALSE_APPROVAL_'+f.upper())
        require(r.get('critical_lexical')==(key in CRITICAL_LEXICAL_KEYS),'CRITICAL_WARNING_DRIFT')
        require(isinstance(r.get('interpretation_private'),str) and len(r['interpretation_private'])>=20,
                'NO_PRIVATE_MEANING')
        require(isinstance(r.get('scope_warning_private'),str) and len(r['scope_warning_private'])>=20,
                'NO_PRIVATE_RISK_SCOPE')
        if e['speech_act_category']=='LEXICAL_TAIL':
            require(r.get('lexical_independent_claim_status')=='OPEN_NEEDS_CONTEXT_OR_AUDIO',
                    'LEXICAL_EXCLUDED_AS_NONCLAIM')
        else:
            require(r.get('lexical_independent_claim_status')=='NOT_ASSESSED_SEMANTIC_GOLD',
                    'FALSE_NEGATIVE_GOLD')
        counts[e['speech_act_category']]+=1
        bv=byvideo.setdefault(key[0],Counter());bv[e['speech_act_category']]+=1
        shadow.append([key[0],key[1],e['cue_text_sha256'],e['speech_act_category'],
                       r['critical_lexical'],sha(r['interpretation_private'].encode('utf-8'))])
    require(set(checked)==set(expected),'NOT_FULL_GAP_COVERAGE')
    require(set(byvideo)=={6,7,8,9},'EXPECTED_VIDEO_GAPS_MISSING')
    for n,cs in COUNT_PIN.items():
        if n==10:continue
        require(dict(byvideo[n])=={k:v for k,v in cs.items() if v},'PER_VIDEO_CATEGORY_DRIFT')
    require(dict(counts)=={'ASSENT':157,'DISCOURSE':72,'COURTESY':16,'LAUGHTER':4,'LEXICAL_TAIL':46},
           'CATEGORY_CENSUS_DRIFT')
    require(sum(r['critical_lexical'] for r in records)==18,'CRITICAL_LEXICAL_CENSUS_DRIFT')
    return {'unassigned_cues':295,'per_video_category_counts':{str(k):dict(sorted(v.items())) for k,v in sorted(byvideo.items())},
      'speech_act_counts':dict(sorted(counts.items())),'lexical_cues_open':46,'source_risk_anchor_count':18,
      'cue_review_digest_sha256':digest(sorted(shadow)),'semantic_recall_certified':False}

def validate_31_candidates(cues_byvid,reg_byvid,rows,previous_six):
    require(type(rows) is list and len(rows)==31,'NEW_SAMPLE_COUNT_DRIFT')
    prev_keys={(r['video_id'],r['window_id'],r['claim_id']) for r in previous_six}
    require(len(prev_keys)==6,'PREVIOUS_SIX_SAMPLES_CORRUPT')
    vidmap={6:'3MyhYE2jmuE',7:'4CQ4FjGT2gA',8:'OfkY343OaNs',9:'YNOSY15ppf8',10:'VKr060rIirM'}
    expected={(n,w,c) for n,arr in SAMPLE_KEYS.items() for w,c in arr}
    require(len(expected)==31,'PIN_COUNT_ERROR')
    seen=set();digest_rows=[]
    for r in rows:
        n=r.get('video_no');vid=vidmap.get(n);wid=r.get('window_id');cid=r.get('claim_id');key=(n,wid,cid)
        require(key in expected and key not in seen,'UNEXPECTED_OR_DUPLICATE_MANUAL_SAMPLE');seen.add(key)
        require(r.get('video_id')==vid and (vid,wid,cid) not in prev_keys,'PREVIOUS_SIX_DUPLICATED')
        candidates=[x for x in reg_byvid[vid][wid] if x['claim_id']==cid];require(len(candidates)==1,'CANDIDATE_MISSING')
        m=candidates[0];cc=cues_byvid[vid];ids=m['cue_indices'];text=' | '.join(cc[i-1].text for i in ids)
        require(r.get('cue_indices')==ids and r.get('source_excerpt_private')==text,'CANDIDATE_SOURCE_PROSE_TAMPER')
        require(r.get('source_sha256')==sha(text.encode('utf-8'))==m['source_text_sha256'],'CANDIDATE_DIGEST_MISMATCH')
        require(r.get('start_ms')==cc[ids[0]-1].start_ms and r.get('end_ms')==cc[ids[-1]-1].end_ms,
                'CANDIDATE_TIME_MISMATCH')
        require(r.get('adjacent_context_private')==[{'cue_index':i,'text':cc[i-1].text} for i in range(max(1,ids[0]-2),min(len(cc),ids[-1]+2)+1)],
                'CANDIDATE_ADJACENCY_DRIFT')
        require(r.get('utterance_kind') in VALID_KINDS,'MISSING_UTTERANCE_TYPE')
        require(isinstance(r.get('speaker_meaning_private'),str) and len(r['speaker_meaning_private'])>=30,
                'MEANING_NOT_REVIEWED')
        require(isinstance(r.get('scope_caution_private'),str) and len(r['scope_caution_private'])>=30,
                'RISK_NOT_REVIEWED')
        require(r.get('status')=='SOURCE_BOUND_PRELIMINARY_SEMANTIC_NOT_GOLD','FALSE_SEMANTIC_STATUS')
        for f in ASSERT_FALSE:require(r.get(f) is False,'FALSE_SAMPLE_APPROVAL_'+f.upper())
        digest_rows.append([n,wid,cid,r['source_sha256'],sha(r['speaker_meaning_private'].encode('utf-8')),
                            sha(r['scope_caution_private'].encode('utf-8')),r['utterance_kind']])
    require(seen==expected,'SELECTED_SOURCE_COVERAGE_DRIFT')
    return {'new_source_bound_semantic_parent_reviews':31,'per_video_new_reviews':{str(n):len(arr) for n,arr in SAMPLE_KEYS.items()},
      'new_semantic_custody_sha256':digest(sorted(digest_rows)),'previous_v84_six_overlap':0,
      'independent_financial_fact_approvals':0,'independent_gold_precision_recall':False}

def audit_previous_v84(owner,v83,v84):
    require(sha(Path(v84).read_bytes())==V84_ARCHIVE_SHA,'V84_PRIVATE_ZIP_CHANGED')
    with zipfile.ZipFile(v84) as z:
        require(z.testzip() is None,'V84_ZIP_CRC_BAD')
        previous_94=json.loads(z.read(V84_GAP_MEMBER))
        previous_six=json.loads(z.read(V84_SIX_MEMBER))
    prev,first5=audit_v83_private_custody(v83,owner)
    older=check_94_speechact_reviews(prev,previous_94)
    second,regs,cues=new_video_census(owner)
    six=check_new5_manual_samples(cues,regs,previous_six)
    require(older['new_source_context_speechacts_reviewed']==94 and six['manual_six_to_ten_parent_reviews']==6,
            'PREVIOUS_V84_RECONSTRUCTION_FAILED')
    return {'previous_v84_six':previous_six,'first5':first5,'six_to_ten':second,'cues':cues,'registry':regs}