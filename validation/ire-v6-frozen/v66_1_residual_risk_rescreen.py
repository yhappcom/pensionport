"""V66 secondary lexical screening of still-unreviewed owner speech.
Does not certify all financial high-risk utterances have been discovered.
"""
from __future__ import annotations
import collections,hashlib,json,re
PUBLIC_RULE='연금|세금|세액|과세|비과세|ISA|IRP|CMA|ETF|추납|배당|손실|원금|수익률|억원|만원|투자'
PATTERN=re.compile(PUBLIC_RULE,re.I)
STRONG=re.compile(r'추납|연금|ISA|IRP|세액|과세|비과세|\d+[.,]?\d*\s*(?:만|억|%)',re.I)

def inspect_unreviewed(rows):
 if type(rows) is not list or not rows:raise ValueError('REAL_SOURCE_REVIEW_QUEUE_REQUIRED')
 unique=set();p2=[];flagged=[]
 for r in rows:
  if type(r) is not dict or not {'video_no','video_id','claim_id','window_id','source_excerpt_private','triage_bucket','source_excerpt_sha256'}<=set(r):raise ValueError('INVALID_SOURCE_QUEUE_ROW')
  key=(r['video_id'],r['window_id'],r['claim_id'])
  if key in unique:raise ValueError('DUPLICATE_PARENT_IN_QUEUE')
  unique.add(key)
  text=r['source_excerpt_private']
  if type(text) is not str:raise ValueError('SOURCE_EXCERPT_NOT_TEXT')
  if r['triage_bucket']=='P2_GENERAL_OR_CONTEXT':
   p2.append(r)
   if PATTERN.search(text):
    flagged.append({'video_no':r['video_no'],'video_id':r['video_id'],
      'window_id':r['window_id'],'parent_id':r['claim_id'],
      'source_excerpt_sha256':r['source_excerpt_sha256'],
      'strong_terms':bool(STRONG.search(text))})
 flagged.sort(key=lambda x:(x['video_id'],x['window_id'],x['parent_id']))
 sha=hashlib.sha256(json.dumps(flagged,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
 return {'schema':'IRE_V6_V66_SECONDARY_LEXICAL_P2_FINANCE_HAZARD_RESCREEN_NOT_GOLD',
   'unreviewed_total':len(rows),'previous_P2_source_rows':len(p2),
   'previous_P2_with_any_broad_finance_keywords':len(flagged),
   'previous_P2_broad_keyword_and_strong_signal':sum(x['strong_terms'] for x in flagged),
   'flagged_source_keys_sha256':sha,
   'flagged_source_keys_private':flagged,
   'original_lexical_triage_has_false_negative_risk':True,
   'all_true_financial_claims_found':False,'independent_gold':False,'p0_go':False}
