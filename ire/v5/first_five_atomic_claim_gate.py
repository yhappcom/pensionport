"""Original #1-#5 financially material atomic-claim *candidate* source gate.

This is NOT complete claim recall for the 288 windows, approval of current rules,
independent human scoring, or permission for portfolio trades. Source ZIP mode
reopens private original SRT bytes and independently rechecks precise cue text.
No source text is included in the GitHub JSON.
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlparse
import zipfile

from .first_five_window_review_gate import source_windows

LEDGER=Path('ire/v5/validation/first_five_atomic_20261106.json')
CENSUS=Path('ire/v5/validation')
CANONICAL=Path('data/claims.jsonl')
VIDEO_IDS=('sz5N9WJS310','6VEfKF7BzZU','OiDTNstaSpM','aNfGrcO6WPI','qtluAViPpsQ')
WINDOWS=(67,76,44,43,58)
CUE_COUNTS=(1195,1347,785,758,1044)
RAW_ZIP='00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd'
HOSTS={'m.nps.or.kr','www.nps.or.kr','nts.go.kr','j.nts.go.kr',
       'regulation.krx.co.kr','www.krx.co.kr','www.bok.or.kr',
       'www.moel.go.kr','moel.go.kr','www.imeritz.com','www.investor.gov'}
KINDS={'RULE','PRODUCT','MODEL','STRATEGY','EMPIRICAL','ASR','BEHAVIOR'}
RELATIONS={
 1:{'NEW_UNAPPROVED_NO_CORE_LEGACY'},2:{'NEW_UNAPPROVED_NO_CORE_LEGACY'},
 3:{'TOPIC_ONLY_UNAPPROVED','C64_ALIGNED'},
 4:{'TOPIC_ONLY_UNAPPROVED','C63_ALIGNED','C63_CONFLICT'},
 5:{'TOPIC_ONLY_UNAPPROVED','C62_ALIGNED','C62_NOT_SAME'},
}

class AtomicResearchError(ValueError):pass

def require(ok:bool,code:str)->None:
    if not ok: raise AtomicResearchError(code)

def _read(root:Path,path:Path)->dict:
    return json.loads((root/path).read_text('utf-8'))

def _source_cue_digest(blocks:list[str],first:int,last:int)->str:
    rows=[]
    for n in range(first,last+1):
        fields=blocks[n-1].splitlines()
        require(fields and int(fields[0])==n,'ATOMIC_PRIVATE_ORIGINAL_SEQUENCE_CHANGED')
        rows.append(f'{n}|'+ ' '.join(x.strip() for x in fields[2:]))
    return hashlib.sha256('\n'.join(rows).encode('utf-8')).hexdigest()

def _actual_math(kind:str)->Decimal:
    r=Decimal('0.07')/12
    if kind=='COMPOUND_LUMP_SUM_12Y_7PCT':return Decimal(18000000)*Decimal('1.07')**12
    if kind=='MONTHLY_PENSION_PAYBACK_SIMPLE':return Decimal(18000000)/Decimal(250000)
    if kind=='ANNUITY_DUE_FALSE_MONTHLY_POSTPAY_10Y':return Decimal(300000)*((1+r)**120-1)/r
    if kind=='ANNUITY_DUE_FALSE_MONTHLY_POSTPAY_7Y':return Decimal(300000)*((1+r)**84-1)/r
    if kind=='DISTRIBUTION_800M_6PCT_MONTHLY':return Decimal(800000000)*Decimal('.06')/12
    if kind=='CMA_100M_2_5PCT_SIMPLE_DAY':return Decimal(100000000)*Decimal('.025')/365
    if kind=='IRP_300M_3PCT_YEARLY':return Decimal(300000000)*Decimal('.03')
    if kind=='INSURANCE_50M_6PCT_MONTHLY':return Decimal(50000000)*Decimal('.06')/12
    raise AtomicResearchError('ATOMIC_UNKNOWN_MATH_FORMULA_'+kind)

def load(root:Path,replacement:dict|None=None)->list[dict]:
    root=Path(root)
    d=_read(root,LEDGER) if replacement is None else replacement
    require(d.get('schema')=='IRE_V5_FIRST_FIVE_ATOMIC_CLAIM_FOCUSED_V1'
      and d.get('as_of')=='2026-11-06' and d.get('source_archive_sha256')==RAW_ZIP
      and d.get('source_cues_total')==5129
      and d.get('previous_window_semantic_census_total')==288
      and d.get('full_288_window_atomic_claim_recall_certified') is False
      and d.get('historical_five_public_batch_receipts_modified') is False
      and d.get('current_factual_rule_approvals_automatically_granted')==0
      and d.get('personal_action_approvals')==0
      and d.get('legacy_B04_claims_formally_approved') is False
      and d.get('cases_narrow_hand_authored_not_blind') is True,
      'ATOMIC_FALSE_FULL_APPROVAL_OR_SOURCE_CENSUS')
    sources=d.get('official_sources',[])
    lookup={x['id']:x for x in sources}
    require(len(lookup)==len(sources)==11,'ATOMIC_OFFICIAL_SOURCE_SET_CHANGED')
    for sid,x in lookup.items():
        u=urlparse(x.get('url',''))
        require(u.scheme=='https' and u.hostname in HOSTS
           and x.get('checked_in_chat')=='2026-11-06'
           and x.get('independent_raw_document_bytes_attested') is False
           and x.get('personal_applicability_checked') is False
           and len(x.get('verified_scope',''))>=30,
           'ATOMIC_FALSE_OFFICIAL_SOURCE_OR_APPLICABILITY_'+sid)
    canonical={c['claim_id']:c for l in (root/CANONICAL).read_text('utf-8').splitlines()
               if l.strip() for c in [json.loads(l)]}
    for i,(cid,vid) in enumerate([('GOMHEE-C62',VIDEO_IDS[4]),('GOMHEE-C63',VIDEO_IDS[3]),('GOMHEE-C64',VIDEO_IDS[2])]):
        require(cid in canonical and vid in canonical[cid]['supporting_videos'],
                'ATOMIC_LEGACY_CORE_SOURCE_LINK_CHANGED')
    rows=d.get('rows',[])
    require(len(rows)==d.get('atomic_candidate_claims')==68,
            'ATOMIC_CLAIM_COUNT_CHANGED')
    counts=Counter();unique=set(); ids=set()
    for i,row in enumerate(rows,1):
        v=row.get('video_number');
        require(row.get('id')==f'FV5-A{i:03d}' and row['id'] not in ids
               and type(v) is int and 1<=v<=5
               and row.get('video_id')==VIDEO_IDS[v-1],
               'ATOMIC_SOURCE_ROW_ID_OR_VIDEO_MISMATCH')
        ids.add(row['id']); counts[v]+=1
        id_=row.get('window_id')
        require(isinstance(id_,str) and re.fullmatch(r'W\d{5}',id_)
                and 1<=int(id_[1:])<=WINDOWS[v-1],
                'ATOMIC_INVALID_WINDOW_ID')
        census=_read(root,CENSUS/f'v5_first_five_video_{v:02d}_window_review_20261106.json')
        window=census['records'][int(id_[1:])-1]
        require(row.get('first_cue')==window['first_cue']
                and row.get('last_cue')==window['last_cue']
                and row.get('window_primary_text_sha256')==window['primary_text_sha256']
                and re.fullmatch('[0-9a-f]{64}',str(row.get('source_cue_text_sha256',''))),
                'ATOMIC_CHANGED_OR_MISSING_ORIGINAL_CUE_WINDOW')
        unique.add((v,id_))
        cid=row.get('historic_legacy_claim_id')
        target={3:'GOMHEE-C64',4:'GOMHEE-C63',5:'GOMHEE-C62'}.get(v)
        require(cid==target and row.get('legacy_relation_state') in RELATIONS[v]
                and row.get('provisional_not_merged') is True
                and row.get('financial_fact_approved_for_personal_advice') is False
                and row.get('personalized_trade_action_approved') is False
                and row.get('independent_blind_recall_measured') is False,
                'ATOMIC_UNEARNED_LEGACY_LINK_OR_TRADE_APPROVAL')
        sid=row.get('narrow_official_context_id')
        expected_status=('ARITHMETIC_HYPOTHESIS_NOT_EXPECTED_RETURN' if row.get('kind')=='MODEL' else
            'ASR_OR_NUMBER_AMBIGUITY_HOLD' if row.get('kind')=='ASR' else
            'OFFICIAL_NARROW_CONTEXT_REVIEWED_PERSONAL_APPLICATION_OPEN' if sid else
            'OPEN_OR_OPINION_NOT_OFFICIAL_CERTIFIED')
        require((sid is None or sid in lookup)
                and row.get('evidence_state')==expected_status
                and row.get('kind') in KINDS
                and len(row.get('atomic_interpretation',''))>=25
                and len(row.get('critical_scope_and_exceptions',''))>=20
                and len(row.get('query_terms',[]))>=1,
                'ATOMIC_FALSE_FACT_EVIDENCE_OR_SCOPE')
    require(counts==Counter({1:16,2:13,3:13,4:13,5:13})
           and len(unique)==d['unique_windows_with_atomic_candidates']==67
           and d.get('claim_count_by_video')=={str(v):counts[v] for v in range(1,6)},
           'ATOMIC_CANDIDATE_DISTRIBUTION_OR_WINDOW_COVERAGE')
    math=d.get('math_assertions',[])
    require(len(math)==8,'ATOMIC_MATH_SET_CHANGED')
    for i,item in enumerate(math,1):
        require(item.get('id')==f'M{i:02d}' and item.get('reference_id') in ids
                and isinstance(item.get('note'),str) and len(item['note'])>20,
                'ATOMIC_INVALID_MATH_PROVENANCE')
        actual=int(_actual_math(item['kind']).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
        expected=item.get('expected_months') if item['kind']=='MONTHLY_PENSION_PAYBACK_SIMPLE' else item.get('expected_rounded_krw')
        require(actual==expected,'ATOMIC_MATH_MISMATCH_'+item['id'])
    return rows

def retrieve(index:list[dict],question:str,limit:int=8)->list[dict]:
    if not isinstance(question,str) or len(question.strip())<5:return []
    norm=lambda s:re.sub(r'\s+|,','',s.casefold())
    q=norm(question); scored=[]
    for row in index:
        hits=[t for t in row['query_terms'] if norm(t) in q]
        if hits:scored.append((sum(len(norm(t)) for t in hits),row))
    scored.sort(key=lambda z:(-z[0],z[1]['id']))
    keep=['id','video_number','video_id','window_id','first_cue','last_cue',
          'window_primary_text_sha256','atomic_interpretation','critical_scope_and_exceptions',
          'narrow_official_context_id','evidence_state','historic_legacy_claim_id',
          'legacy_relation_state','personalized_trade_action_approved']
    return [{key:row[key] for key in keep} for _,row in scored[:limit]]

def verify(root:Path,source_zip:Path|None=None,replacement:dict|None=None)->dict:
    root=Path(root);rows=load(root,replacement)
    raw={'private_original_zip_reopened_in_this_execution':False,
         'private_68_source_cue_digests_matching':None}
    if source_zip is not None:
        p=Path(source_zip)
        require(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==RAW_ZIP,
                'ATOMIC_PRIVATE_ZIP_SHA_MISMATCH')
        num=0
        with zipfile.ZipFile(p) as z:
            for v,vid in enumerate(VIDEO_IDS,1):
                name=f'1-70/youtube-transcript-{vid}.srt'
                require(name in z.namelist(),'ATOMIC_PRIVATE_FILE_ID_MISSING')
                blob=z.read(name)
                actual=source_windows(blob)
                require(len(actual)==WINDOWS[v-1],'ATOMIC_PRIVATE_PLANNER_CENSUS_CHANGED')
                blocks=re.split(r'\n\s*\n',blob.decode('utf-8-sig').replace('\r\n','\n').strip())
                require(len(blocks)==CUE_COUNTS[v-1],'ATOMIC_PRIVATE_CUE_COUNT_CHANGED')
                for row in [x for x in rows if x['video_number']==v]:
                    w=actual[int(row['window_id'][1:])-1]
                    require(w['first_cue']==row['first_cue']
                            and w['last_cue']==row['last_cue']
                            and w['primary_text_sha256']==row['window_primary_text_sha256']
                            and _source_cue_digest(blocks,row['first_cue'],row['last_cue'])==row['source_cue_text_sha256'],
                            'ATOMIC_PRIVATE_SOURCE_TEXT_MISMATCH_'+row['id'])
                    num+=1
        raw={'private_original_zip_reopened_in_this_execution':True,
             'private_68_source_cue_digests_matching':num}
    scenarios=[
        ('연금 1500 인출상한 세금','FV5-A007'),
        ('국민연금 연기연금 7.2%','FV5-A005'),
        ('30만원 적립 7년 10년','FV5-A004'),
        ('CMA 예금자보호','FV5-A022'),
        ('CMA 전재산 무위험','FV5-A026'),
        ('KRX 금시장 비과세','FV5-A018'),
        ('퇴직 IRP 이전','FV5-A030'),
        ('IRP 수수료','FV5-A035'),
        ('파킹 ETF 3%','FV5-A036'),
        ('보험 해지 배당','FV5-A038'),
        ('경상수지 20%','FV5-A051'),
        ('앱 삭제 3년 5년','FV5-A046'),
        ('월급 50% 소비 저축','FV5-A058'),
        ('재직정보 주식 위험','FV5-A061'),
        ('업종 ETF 집중위험','FV5-A063'),
    ]
    for q,eid in scenarios:
        hits=retrieve(rows,q)
        require(any(x['id']==eid for x in hits),'ATOMIC_RETRIEVAL_MISS_'+eid)
        require(all(x['personalized_trade_action_approved'] is False and
                    len(x['critical_scope_and_exceptions'])>20 for x in hits),
                'ATOMIC_UNSAFE_RETRIEVAL')
    require(retrieve(rows,'오늘 저녁 영화관 상영 일정')==[],
            'ATOMIC_UNRELATED_QUERY_RETURNED')
    return {'schema':'IRE_V5_FIRST_FIVE_ATOMIC_CLAIM_QA_V1',
      'candidate_atomic_claims':68,'five_source_videos':5,
      'unique_windows_examined_for_claim_candidates':67,
      'full_original_source_windows':288,'remaining_windows_not_atomically_proven':221,
      'focused_official_context_lookups':sum(bool(r['narrow_official_context_id']) for r in rows),
      'independent_arithmetic_checks':8,'retrieval_regression_queries':len(scenarios),
      'preexisting_five_video_event_receipts_modified':False,
      'all_288_windows_atomic_recall_measured':False,
      'new_financial_facts_for_personal_advice_approved':0,
      'B04_C62_C64_formally_merged':False,'personalized_trade_approved':False,
      'full_research_quality_go':False,'CI_does_not_reverify_live_official_pages':True,
      **raw}

def main()->None:
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'))
    p.add_argument('--source-zip',type=Path)
    p.add_argument('--question')
    a=p.parse_args()
    root=a.root
    result=retrieve(load(root),a.question) if a.question else verify(root,a.source_zip)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()
