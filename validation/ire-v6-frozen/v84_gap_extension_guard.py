"""Source-only V84 gate for previously uncovered cues and new #6-10 SRT.

No private source in this public module. Counts and SHA pin original bytes,
not semantic precision/recall, official approval, or personal suitability.
"""
from __future__ import annotations
import hashlib, json, re, zipfile
from collections import Counter
from pathlib import Path
from v77_private_v33_replay import audit as first5_audit, parse_srt, registry, sha, digest

SOURCE_ARCHIVE_SHA='00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd'
PREVIOUS_V83_ZIP_SHA='1c9eeb56ca761627479f59accdc5b32f681a1168a84918353af288b28e7b97cd'
V83_MEMBER='V83_PRIVATE_104_UNASSIGNED_CUE_CONTEXT_BOUND_10_ALERTS_DO_NOT_UPLOAD_GITHUB.json'
# 791-video public roster #6 through #10: includes long-form #7 and Shorts #10.
NEW_VIDEO_PINS=[
 (6,'3MyhYE2jmuE',807,'493c52ea3e56cb9be756d70f4de90d3b069c40dff5743d69bd8a8770f32c1bcc',21,252,21),
 (7,'4CQ4FjGT2gA',10728,'70a4fab14f26618780fa1fc9b1473df829c851d06125ae3745ecc3b6eadc79ca',269,3341,186),
 (8,'OfkY343OaNs',1039,'d97852825e0b09d58eb76957e22cd7ef41f5d8a59013795bc4c949c1e651c921',26,358,29),
 (9,'YNOSY15ppf8',1277,'b48c51ac62ddf27a0d667e018ad1fbf3717e2bb447a66d9c48ed114eeeb6c2ce',32,468,59),
 (10,'VKr060rIirM',34,'1263d79eaf2f203b81e39231a05b884f6069bd9c3e4e3e20a213ad86cfdd2c95',1,7,0),
]
# Risk warnings are source-context annotations, not autonomous true/false labels.
SPEECH_ACT_WARNING_ANCHORS={
 (1,599):'PENSION_CASHFLOW_CONFIRMATION',
 (1,715):'PENSION_WITHDRAWAL_ASSENT',
 (1,1038):'INSURANCE_TERMINATION_ASSENT',
 (2,373):'CMA_RATE_ASOF',
 (2,393):'CMA_DEPOSIT_INSURANCE_STATUS',
 (3,261):'IRP_ADDITIONAL_DEPOSIT_ASSENT',
 (3,372):'RETIREMENT_AMOUNT_ECHO',
 (4,178):'EQUITY_SELL_OR_HOLD_AGREEMENT',
 (4,378):'EQUITY_HOLD_CHOICE_AGREEMENT',
 (4,413):'RATE_PERIOD_AGREEMENT',
 (5,12):'PREDICATE_COMPLETION',
 (5,434):'EQUITY_BUY_CAUTION_ASSENT',
 (5,1044):'PREDICATE_DUPLICATION',
}
CATEGORIES={'ASSENT_OR_CONFIRMATION','DISCOURSE_OR_SURPRISE','COURTESY',
            'LAUGHTER','PREDICATE_TAIL'}
EXPECTED_CATEGORY_COUNTS={'ASSENT_OR_CONFIRMATION':51,'DISCOURSE_OR_SURPRISE':35,
                          'COURTESY':4,'LAUGHTER':2,'PREDICATE_TAIL':2}
PRIOR_REVIEWED_GAP_COUNT=10
NEW_V84_GAP_COUNT=94
FINANCIAL_FACT_APPROVAL=False


def require(condition,code):
    if not condition: raise ValueError('V84_'+code)


def classify_speech_act(text):
    t=re.sub(r'^>>\s*','',text.strip()).strip(',.?! ')
    if t in ('네','예','응','맞아요','그죠'):return 'ASSENT_OR_CONFIRMATION'
    if t in ('음','어','아','오','헐'):return 'DISCOURSE_OR_SURPRISE'
    if t in ('안녕하세요','감사합니다'):return 'COURTESY'
    if t in ('[웃음]','웃음'):return 'LAUGHTER'
    if t in ('있어요','입니다'):return 'PREDICATE_TAIL'
    return 'UNKNOWN_REQUIRES_REVIEW'


def new_video_census(owner_zip):
    require(sha(Path(owner_zip).read_bytes())==SOURCE_ARCHIVE_SHA,'OWNER_ZIP_SHA_MISMATCH')
    cohort=[]; summaries=[]; all_regs={}; all_cues={}
    with zipfile.ZipFile(owner_zip) as z:
        require(z.testzip() is None,'OWNER_ZIP_CRC_BAD')
        names=[n for n in z.namelist() if not n.startswith('__MACOSX/')]
        for n,vid,expected,raw_pin,wins,cands,gaps in NEW_VIDEO_PINS:
            hits=[a for a in names if a.endswith(f'youtube-transcript-{vid}.srt')]
            require(len(hits)==1,'VIDEO_MEMBER_MISSING_DUPLICATE')
            raw=z.read(hits[0]);require(sha(raw)==raw_pin,'VIDEO_RAW_SOURCE_SHA_MISMATCH')
            cues=parse_srt(raw);require(len(cues)==expected,'SRT_CUE_CENSUS_DRIFT')
            regs=registry(cues);require(len(regs)==wins,'SOURCE_WINDOW_DRIFT')
            n_candidates=sum(map(len,regs.values()));require(n_candidates==cands,'SOURCE_CANDIDATE_DRIFT')
            assigned=set()
            for wid,rows in regs.items():
                for row in rows:
                    indices=row['cue_indices'];require(bool(indices),'EMPTY_CANDIDATE')
                    require(len(indices)==len(set(indices)),'INTERNAL_DUPLICATED_CUES')
                    require(not (assigned & set(indices)),'OVERLAPPING_SOURCE_CANDIDATES')
                    assigned.update(indices)
                    txt=' | '.join(cues[i-1].text for i in indices)
                    require(sha(txt.encode('utf-8'))==row['source_text_sha256'],'CANDIDATE_TEXT_SHA_DRIFT')
                n_window=int(wid[1:]);a=(n_window-1)*40;b=min(a+40,len(cues))
                wintext=' '.join(c.text for c in cues[a:b])
                cohort.append([n,wid,sha(wintext.encode('utf-8')),digest(rows)])
            missing=len(cues)-len(assigned);require(missing==gaps,'UNCOVERED_CUE_COUNT_DRIFT')
            require(len(assigned)+missing==expected,'SOURCE_PARTITION_DRIFT')
            summaries.append({'video_no':n,'video_id':vid,'srt_sha256':raw_pin,
                'cues':len(cues),'end_ms':cues[-1].end_ms,'source_windows':len(regs),
                'draft_parent_candidates':n_candidates,'source_cues_assigned':len(assigned),
                'unassigned_cues':missing})
            all_regs[vid]=regs;all_cues[vid]=cues
    require(sum(x['cues'] for x in summaries)==13885,'FIVE_VIDEO_CUE_TOTAL_DRIFT')
    require(sum(x['source_windows'] for x in summaries)==349,'FIVE_VIDEO_WINDOW_TOTAL_DRIFT')
    require(sum(x['draft_parent_candidates'] for x in summaries)==4426,'FIVE_VIDEO_DRAFT_TOTAL_DRIFT')
    require(sum(x['unassigned_cues'] for x in summaries)==295,'FIVE_VIDEO_GAP_TOTAL_DRIFT')
    return ({'six_to_ten_videos':summaries,'six_to_ten_cohort_source_draft_sha256':digest(cohort),
             'six_to_ten_cues':13885,'six_to_ten_windows':349,
             'six_to_ten_draft_candidates':4426,'six_to_ten_unassigned_cues':295,
             'six_to_ten_claim_recall_certified':False},all_regs,all_cues)


def audit_v83_private_custody(v83_zip,owner_zip):
    require(sha(Path(v83_zip).read_bytes())==PREVIOUS_V83_ZIP_SHA,'V83_PRIVATE_ZIP_CHANGED')
    with zipfile.ZipFile(v83_zip) as z:
        require(z.testzip() is None,'V83_PRIVATE_ZIP_CRC_BAD')
        prev=json.loads(z.read(V83_MEMBER))
    first5,regs,cues=first5_audit(owner_zip)
    require(first5['v42_cohort_digest_matches'] is True,'V42_ORIGINAL_REPLAY_DRIFT')
    from v83_source_gap_context_guard import auxiliary_expected
    pinlist=[(n,vid,cnt,_) for n,vid,cnt,_ in __import__('v77_private_v33_replay').VIDEO_PINS]
    baseline=auxiliary_expected(cues,regs,pinlist)
    require(len(prev)==len(baseline)==104,'PREVIOUS_GAPS_DRIFT')
    indexed={(r['video_no'],r['cue_index']):r for r in baseline}
    used=set();n_previously=0
    for p in prev:
        key=(p['video_no'],p['cue_index'])
        require(key in indexed and key not in used,'V83_GAP_DUPLICATE_OR_WRONG_SOURCE')
        used.add(key);e=indexed[key]
        for f in ('video_id','cue_text_sha256','cue_text_private','start_ms','end_ms','adjacent_cues_private',
                  'left_existing_candidate','right_existing_candidate','source_status'):
            require(p[f]==e[f],'V83_SOURCE_OR_CONTEXT_MISMATCH')
        for f in ('fact_approved','independent_gold','official_parent_merged',
                  'personal_action_approved','v75_membership_verified'):
            require(p.get(f) is False,'FALSE_GOLD_OR_FINANCE_APPROVAL')
        if p['context_interpretation_private'] is not None:n_previously+=1
    require(used==set(indexed) and n_previously==10,'V83_PREVIOUS_REVIEW_CENSUS_DRIFT')
    return prev,first5


def check_94_speechact_reviews(previous_rows,new_reviews):
    require(type(previous_rows) is list and len(previous_rows)==104,'PREVIOUS_GAP_COUNT_DRIFT')
    require(type(new_reviews) is list and len(new_reviews)==94,'V84_REVIEW_COUNT_DRIFT')
    prev={(r['video_no'],r['cue_index']):r for r in previous_rows}
    require(len(prev)==104,'V83_SOURCE_ID_DUPLICATED')
    all_keys=set();count=Counter();risks=[];sha_rows=[]
    for r in new_reviews:
        require(type(r) is dict,'INVALID_REVIEW_ROW')
        key=(r['video_no'],r['cue_index'])
        require(key in prev and key not in all_keys,'UNEXPECTED_OR_DUPLICATED_REVIEW')
        all_keys.add(key);p=prev[key]
        require(p['context_interpretation_private'] is None,'REVIEWED_V83_RECORD_MODIFIED')
        require(p['video_id']==r.get('video_id') and
                p['cue_text_sha256']==r.get('cue_text_sha256') and
                p['start_ms']==r.get('start_ms') and p['end_ms']==r.get('end_ms'),
                'REVIEW_SOURCE_BINDING_CHANGED')
        require(r.get('source_adjacent_cues_sha256')==digest(p['adjacent_cues_private']),
                'NEIGHBOR_SHA_MISMATCH')
        category=classify_speech_act(p['cue_text_private'])
        require(category in CATEGORIES and r.get('speech_act_category')==category,
                'SEMANTIC_SPEECH_ACT_CATEGORY_CHANGED')
        require(isinstance(r.get('interpretation_private'),str) and
                len(r['interpretation_private'])>=15,'SEMANTIC_REVIEW_NOTE_MISSING')
        require(isinstance(r.get('caution_private'),str) and
                len(r['caution_private'])>=15,'REVIEW_CAUTION_MISSING')
        for f in ('fact_approved','independent_gold','official_parent_merged',
                  'personal_action_approved','v75_membership_verified','negative_gold_certified'):
            require(r.get(f) is False,'FALSE_APPROVAL_OR_NEGATIVE_GOLD')
        require(r.get('status')=='SPEECH_ACT_CONTEXT_REVIEW_NOT_INDEPENDENT_GOLD',
                'PROVISIONAL_SPEECH_ACT_STATUS_MISMATCH')
        warning=SPEECH_ACT_WARNING_ANCHORS.get(key)
        require(r.get('context_risk_code')==warning,'CONTEXT_RISK_CODE_CHANGED')
        if warning:risks.append([*key,warning,sha(r['caution_private'].encode())])
        count[category]+=1
        sha_rows.append({'video_no':r['video_no'],'cue_index':r['cue_index'],
                'cue_sha256':r['cue_text_sha256'],'neighbor_sha256':r['source_adjacent_cues_sha256'],
                'speech_act_category':category,'context_risk_code':warning,
                'interpretation_sha256':sha(r['interpretation_private'].encode('utf-8'))})
    require(len(all_keys)==94 and all_keys=={k for k,p in prev.items() if p['context_interpretation_private'] is None},
            'REMAINING_94_NOT_EXHAUSTIVE')
    require(dict(count)==EXPECTED_CATEGORY_COUNTS,'SPEECH_ACT_CATEGORY_COUNTS_CHANGED')
    require(len(risks)==len(SPEECH_ACT_WARNING_ANCHORS),'PRIORITY_SPEECH_ACT_RISK_CENSUS_DRIFT')
    return {'previous_context_alerts_preserved':10,'new_source_context_speechacts_reviewed':94,
            'total_first_five_cues_revisited':104,'category_counts':dict(sorted(count.items())),
            'new_context_risk_flags':len(risks),'speech_act_review_sha256':digest(sorted(sha_rows,key=lambda r:(r['video_no'],r['cue_index']))),
            'context_risk_sha256':digest(sorted(risks)),'formal_gold_precision_recall_measured':False,
            'independent_negative_gold_labels':0,'new_atomic_claims_approved':0}


def check_new5_manual_samples(cues_byvid,reg_byvid,manual):
    require(len(manual)==6,'MANUAL_SIX_REVIEW_CENSUS_DRIFT')
    keys=set();out=[]
    video_ids={v[0]:v[1] for v in NEW_VIDEO_PINS}
    for row in manual:
        n=row['video_no'];vid=video_ids[n];wid=row['window_id'];cid=row['claim_id'];key=(vid,wid,cid)
        require(key not in keys,'DUPLICATE_MANUAL_PARENT');keys.add(key)
        require(row['video_id']==vid,'FOREIGN_VIDEO_SOURCE')
        match=[x for x in reg_byvid[vid][wid] if x['claim_id']==cid]
        require(len(match)==1,'MANUAL_SOURCE_CANDIDATE_MISSING')
        m=match[0];cc=cues_byvid[vid];indexes=m['cue_indices']
        prose=' | '.join(cc[i-1].text for i in indexes)
        require(row['source_excerpt_private']==prose and row['cue_indices']==indexes,'MANUAL_PROSE_CUE_TAMPER')
        require(row['source_sha256']==sha(prose.encode())==m['source_text_sha256'],'MANUAL_PROSE_SHA_TAMPER')
        require(len(row['speaker_meaning_private'])>=20 and len(row['scope_caution_private'])>=20,
                'MANUAL_SEMANTIC_CUSTODY_MISSING')
        for f in ('fact_approved','independent_gold','official_parent_merged','personal_action_approved','v75_membership_verified'):
            require(row.get(f) is False,'MANUAL_FALSE_GOLD_OR_ADVICE_APPROVAL')
        require(row.get('status')=='SOURCE_BOUND_FINANCE_MEANING_PRELIMINARY_OPEN','UNAPPROVED_SOURCE_STATUS_INVALID')
        out.append({'video_no':n,'video_id':vid,'window_id':wid,'claim_id':cid,
                    'source_sha256':row['source_sha256'],
                    'meaning_sha256':sha(row['speaker_meaning_private'].encode()),
                    'caution_sha256':sha(row['scope_caution_private'].encode())})
    require(len({x['video_no'] for x in out})==5,'MISSING_VIDEO_MANUAL_REVIEW')
    return {'manual_six_to_ten_parent_reviews':6,'manual_review_source_key_sha256':digest(sorted(out,key=lambda x:(x['video_no'],x['claim_id']))),
            'independent_gold_precision_recall_measured':False,'financial_facts_approved':0}