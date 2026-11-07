"""Evidence-only #1-#5 source-span bridge for the 60-claim advisory router.

Not a current-financial-fact certificate, full 288-window semantic ledger, or
personalized trade authority. No private SRT text is published or imported.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

QA = Path('ire/v5/validation/first_five_original_qa_25_20261105.json')
FOLLOWUP = Path('ire/v5/validation/first_five_followup_20_20261106.json')
MANIFEST = Path('ire/v5/validation/first_five_source_manifest_20261105.json')
CANONICAL = Path('data/claims.jsonl')
VIDEO_CLAIMS = {1: None, 2: None, 3: 'GOMHEE-C64', 4: 'GOMHEE-C63', 5: 'GOMHEE-C62'}
# Explicit synonyms; never make a generic topic match a direct source citation.
QA_TERMS = {
 'F01':('추납','추후납부'), 'F02':('추납 1800','추납 수익률','추납 배당'),
 'F03':('1500만원','1,500만원','연금 인출상한','사적연금 과세'),
 'F04':('배당 원금','배당금 원금','원금 고갈'),
 'F05':('ISA 50년','ISA 장기유지','ISA 3년 만기'),
 'F06':('3개 5개 7개','연령별 계좌','계좌 7개'),
 'F07':('CMA 금리 비교','예금 CMA 금리'),
 'F08':('CMA 위험','CMA 원금보장','CMA 무위험','CMA 예금자보호','RP형 CMA'),
 'F09':('패시브 액티브 50','패시브 액티브 반반','패시브와 액티브 비중'),
 'F10':('주도주 몰빵','주식 몰빵','주도주 집중'),
 'F11':('IRP 증권사 이전','IRP 증권사','퇴직금 IRP 이전'),
 'F12':('퇴직급여 IRP 인출','IRP 연금개시','IRP 납입용'),
 'F13':('퇴직금 파킹 ETF','KOFR SOFR','SOFR ETF'),
 'F14':('파킹 ETF 3%','파킹 ETF 원금','파킹 ETF 수익률'),
 'F15':('보험 해지 배당','해지환급금 배당','보험 해지 6%'),
 'F16':('손실 주식 유지','손실주식 장기보유'),
 'F17':('하락한 주식 매수','낙폭 저평가'),
 'F18':('반도체 손실주식','반도체 주식 킵','손실 종목 보유'),
 'F19':('경상수지 GDP','GDP 경상수지','2026 성장률'),
 'F20':('2022 코스피 저점','코스피 반등 사례'),
 'F21':('월급 50%','월급 반반','사회초년생 저축 비율'),
 'F22':('자사주 매수','회사 주식 투자','재직 회사 주식'),
 'F23':('재직 업종 ETF','직장 산업 ETF','동일업종 ETF'),
 'F24':('좋은 빚','낮은 금리 부채','레버리지 부채'),
 'F25':('가계부','지출 관리','현금흐름 기록'),
}
class BridgeError(ValueError): pass

def check(ok: bool, msg: str) -> None:
 if not ok: raise BridgeError(msg)

def load(root: Path) -> list[dict]:
 root=Path(root)
 q=json.loads((root/QA).read_text('utf-8'))
 d=json.loads((root/FOLLOWUP).read_text('utf-8'))
 m=json.loads((root/MANIFEST).read_text('utf-8'))
 videos={i+1:v for i,v in enumerate(m['videos'])}
 claims={c['claim_id']:c for l in (root/CANONICAL).read_text('utf-8').splitlines() if l.strip() for c in [json.loads(l)]}
 check(q['schema']=='IRE_V5_FIRST_FIVE_ORIGINAL_QA_V1' and len(q['cases'])==25 and
       q['financial_fact_approvals_created']==0 and q['research_full_quality_approved'] is False,
       'BRIDGE_BASE_QA_NOT_FROZEN')
 check(d.get('schema')=='IRE_V5_FIRST_FIVE_FOLLOWUP_20_V1' and
       d.get('as_of')=='2026-11-06' and len(d.get('cases',[]))==20 and
       d.get('focused_new_spans')==20 and d.get('fully_researched_288_windows') is False and
       d.get('source_census_is_not_semantic_completion') is True and
       d.get('prior_public_processed_windows')==5 and
       d.get('financial_fact_approvals')==d.get('personal_action_approvals')==0 and
       d.get('source_archive_sha256')==q['source_zip_sha256'],
       'BRIDGE_UNEARNED_COMPLETION_OR_APPROVAL')
 result=[]
 seen=set()
 for kind,rows in [('20261105_QA25',q['cases']),('20261106_FOLLOWUP20',d['cases'])]:
  for row in rows:
   ident=row.get('id'); n=row.get('video_number'); v=videos.get(n)
   check(isinstance(ident,str) and ident not in seen and v is not None and
         row.get('video_id')==v['video_id'] and type(row.get('first_cue')) is int and
         type(row.get('last_cue')) is int and
         1<=row['first_cue']<=row['last_cue']<=v['expected_cues'],
         'BRIDGE_INVALID_OR_FABRICATED_SOURCE_SPAN')
   seen.add(ident)
   hash_value=row.get('original_normalized_span_sha256') if kind=='20261105_QA25' else row.get('source_span_hash_sha256')
   check(bool(re.fullmatch(r'[0-9a-f]{64}',str(hash_value))), 'BRIDGE_INVALID_TEXT_HASH')
   legacy=VIDEO_CLAIMS[n]
   check(row.get('legacy_claim_id')==legacy and
         (legacy is None or v['video_id'] in claims[legacy]['supporting_videos']),
         'BRIDGE_WRONG_B04_OR_FABRICATED_PRIOR_LINK')
   if kind=='20261105_QA25':
    check(ident in QA_TERMS and row.get('personal_advice_approved') is False and
          row.get('official_financial_fact_automatically_approved') is False and
          row.get('source_original_fidelity_spot_reviewed') is True,
          'BRIDGE_QA_UNSAFE_APPROVAL')
    terms=QA_TERMS[ident]
    meaning=row['observed_risk_or_claim']
    limit=row['safe_advisory_restriction']
    severity=row['severity']
   else:
    check(ident==f'S{len(result)-25+1:02d}' and
          row.get('official_fact_approved') is False and
          row.get('personal_action_approved') is False and
          row.get('relation_state')=='PROVISIONAL_NOT_MERGED' and
          row.get('financial_evidence_state')=='OPEN_CURRENT_OFFICIAL_APPLICABILITY' and
          row.get('release_state')=='RETRIEVABLE_SOURCE_CONTEXT_NOT_APPROVED_ADVICE',
          'BRIDGE_FOLLOWUP_FALSE_PROMOTION')
    terms=row.get('query_terms',[])
    check(isinstance(terms,list) and len(terms)>=3 and len(set(terms))==len(terms)
          and all(isinstance(t,str) and len(t)>=3 for t in terms),
          'BRIDGE_WEAK_QUERY_TERMS')
    meaning=row['provisional_meaning']
    limit=row['critical_limit']
    severity='OPEN'
   check(len(meaning)>=12 and len(limit)>=18,
         'BRIDGE_MISSING_MEANING_OR_CRITICAL_SCOPE')
   result.append({'evidence_id':ident,'video_number':n,'video_id':v['video_id'],
          'cue_range':[row['first_cue'],row['last_cue']],
          'source_span_sha256':hash_value,'terms':list(terms),
          'provisional_meaning':meaning,'critical_limit':limit,'severity':severity,
          'prior_legacy_claim_id':legacy,'prior_link_status':
             'B04_PENDING_NOT_APPROVED' if legacy else 'NEW_SOURCE_ONLY_PROVISIONAL',
          'evidence_batch':kind,'current_law_verified_by_ci':False,
          'financial_fact_approved':False,'personal_action_approved':False})
 check(len(result)==45 and len({x['evidence_id'] for x in result})==45 and
       {x['video_number'] for x in result}==set(range(1,6)) and
       [sum(x['video_number']==n for x in result) for n in range(1,6)]==[9]*5,
       'BRIDGE_INCOMPLETE_SELECTED_SPAN_INDEX')
 return result

def retrieve(index: list[dict], question: str, limit: int=5) -> list[dict]:
 q=question.casefold().replace(',','').replace(' ','')
 ranked=[]
 for item in index:
  terms=[t.casefold().replace(',','').replace(' ','') for t in item['terms']]
  score=sum(2+min(len(t),20) for t in terms if t in q)
  if score: ranked.append((score,item))
 ranked.sort(key=lambda z:(-z[0],z[1]['evidence_id']))
 return [{k:v for k,v in item.items() if k!='terms'} for _,item in ranked[:limit]]

def audit(root: Path) -> dict:
 index=load(root)
 samples=(
  ('추납 1800만원과 연금저축 차이','F01'),
  ('연금 1500만원 인출상한과 세금','F03'),
  ('CMA 위험과 예금자보호 비교','F08'),
  ('패시브 액티브 50 대 50 비중','F09'),
  ('퇴직금 IRP 증권사 이전 비용','F11'),
  ('파킹 ETF 3% 원금보장인가','F14'),
  ('보험 해지 배당 대체 가능한가','F15'),
  ('반도체 손실주식 팔지 말고 보유?','F18'),
  ('재직 회사 주식 투자 집중 위험','F22'),
  ('재직 업종 ETF 투자 위험','F23'),
  ('연금저축보험 연금저축펀드 전환','S04'),
  ('국내주식형 ETF 매매차익 과세 IRP','S03'),
  ('퇴직 국채 채권 만기보유','S10'),
  ('TDF 2060 사회초년생 연금저축','S18'),
  ('첫 연말정산 소득공제 세액공제','S19'),
 )
 for q,id in samples:
  got=retrieve(index,q)
  check(any(x['evidence_id']==id for x in got), 'BRIDGE_RETRIEVAL_MISS_'+id)
  check(all(x['financial_fact_approved'] is False and
            x['personal_action_approved'] is False and x['critical_limit'] for x in got),
        'BRIDGE_UNSAFE_RETRIEVAL_'+id)
 check(retrieve(index,'내일 영화관 상영 스케줄')==[], 'BRIDGE_FALSE_POSITIVE_UNRELATED')
 return {'schema':'IRE_V5_FIRST_FIVE_PROVISIONAL_RETRIEVAL_V1',
         'qa_spans_prior':25,'new_span_reviews':20,
         'source_videos_indexed':5,'hand_authored_query_scenarios':len(samples),
         'source_windows_planned':288,'prior_public_batch_windows_processed':5,
         'remaining_windows_semantic_complete':False,
         'approved_financial_facts':0,'approved_personal_actions':0,
         'legacy_B04_claim_ids_only':['GOMHEE-C62','GOMHEE-C63','GOMHEE-C64'],
         'true_blind_live_advisory_accuracy_measured':False,
         'research_full_go':False}

def main() -> int:
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'))
 p.add_argument('--question',default=None);a=p.parse_args()
 print(json.dumps(retrieve(load(a.root),a.question) if a.question else audit(a.root),ensure_ascii=False,indent=2))
 return 0
if __name__=='__main__': raise SystemExit(main())
