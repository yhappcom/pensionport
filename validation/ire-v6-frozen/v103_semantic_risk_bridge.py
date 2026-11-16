"""V103 source-first context risk *triage*; no financial-fact approval.

No private transcript. Risk events complement V93, never replace mandatory
full-source V98 review. Designed before heldout annotations were read.
"""
from __future__ import annotations
import hashlib,json,re
from collections import Counter
from v93_atom_frontier import FIN

LOAN=re.compile(r'(대출|차입|빚|빌려|빌린|빌렸|빌리|갚|상환|담보|빚투|부채)')
ABSOLUTE=re.compile(r'(무조건|반드시|확정|보장|절대|안전|장담|항상|100%|원금\s*보전|원금\s*보장)')
FIN_EXT=re.compile(r'(연금|퇴직|분산|투자|저축|계좌|종목|주식|펀드|채권|금\b|금값|집값|적금|예금|자산|수익|환급|세액|금리|매수|매도|보험|부동산|적립식|국민연금|IRA|IRP|ISA|ETF|TDF|CMA|대출|빚|상환|차입)',re.I)
FLOW=re.compile(r'(벌었|벌었다|늘었|늘어|증가|올랐|오른|불어|손해|잃었|손실|이익|원금|매도|팔았|팔고|샀|사고|투입|입금|납입|이체|재투자|재매수|할부)')
TIME=re.compile(r'(\d+\s*(?:년|개월|달|일)|몇\s*(?:년|개월|달)|작년|올해|내년|그때|당시|지금|매달|매월)')
NUM=re.compile(r'(?<![0-9A-Za-z])\d[0-9,.]*(?:%|만|억|원|배|세|년|개월|달)?')
RESPONSE=re.compile(r'(아닌|아니요|아니|정정|그건|그런게|다시 말|틀렸|잘못|정확하게)')
TRIGGER_ORDER=('LOAN_BALANCE_REVIEW','GUARANTEE_SCOPE_REVIEW','AMOUNT_TIME_REVIEW','CASHFLOW_CAUSALITY_REVIEW','SPEAKER_CORRECTION_REVIEW')

def sha(s):return hashlib.sha256(s.encode('utf-8')).hexdigest()
def canon(o):return json.dumps(o,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False)
def digest(o):return sha(canon(o))
def require(x,c):
 if not x:raise ValueError('V103_'+c)

def contextual_signal_events(cues,*,video_id,source_zip_sha256,expected_source_zip_sha256):
 """Cue objects with index,text and timestamps; emits SHA-only public-safe risk events."""
 require(source_zip_sha256==expected_source_zip_sha256 and re.fullmatch(r'[0-9a-f]{64}',source_zip_sha256),'SOURCE_PIN')
 require(type(cues)==list and bool(cues) and type(video_id)==str and bool(video_id),'INPUT')
 bycue={}
 for k,c in enumerate(cues,1):
  require(type(c.index) is int and c.index==k and isinstance(c.text,str) and bool(c.text),'SOURCE_ORDER')
  require(type(c.start_ms) is int and type(c.end_ms) is int and c.end_ms>=c.start_ms,'SOURCE_TIME')
  bycue[k]=c.text
 events=[];trigger=Counter();wins=Counter()
 for i,c in enumerate(cues,1):
  w=(i-1)//40+1
  first=(w-1)*40+1;last=min(len(cues),w*40)
  close=' '.join(bycue[j] for j in range(max(first,i-2),min(last,i+2)+1))
  t=c.text
  financial_local=bool(FIN_EXT.search(close))
  kind=[]
  if LOAN.search(t):kind.append('LOAN_BALANCE_REVIEW')
  if ABSOLUTE.search(t) and financial_local:kind.append('GUARANTEE_SCOPE_REVIEW')
  if (TIME.search(t) or NUM.search(t)) and FLOW.search(close) and financial_local and (TIME.search(close) and NUM.search(close)):
   kind.append('AMOUNT_TIME_REVIEW')
  if FLOW.search(t) and financial_local and (LOAN.search(close) or re.search(r'(수익|매도|매수|샀|팔았|증가|감소|금액|원금|자산)',close)):
   kind.append('CASHFLOW_CAUSALITY_REVIEW')
  if RESPONSE.search(t) and financial_local:kind.append('SPEAKER_CORRECTION_REVIEW')
  for k in TRIGGER_ORDER:
   if k in kind:
    events.append({'video_id':video_id,'cue_index':i,'window_id':f'W{w:05d}','kind':k,'cue_sha256':sha(t),
       'independent_fact_approved':False,'automated_true_error_certified':False})
    trigger[k]+=1;wins[f'W{w:05d}']+=1
 require(len(set((e['cue_index'],e['kind']) for e in events))==len(events),'DUPLICATE')
 return {'schema':'V103_CONTEXT_RISK_TRIAGE_NON_APPROVAL_V1','video_id':video_id,'source_cues_checked':len(cues),'risk_events':events,
         'risk_event_count':len(events),'risk_kind_counts':dict(sorted(trigger.items())),'risky_windows':len(wins),'risk_event_digest_sha256':digest(events),
         'source_text_public':False,'independent_gold':False,'certified_precision':None,'certified_recall':None,'p0_go':False}

def score_internal_overlap(*,internal_spans,baseline_alerts,new_events,source_by_index):
 """Internal same-host directional diagnostics only; not recall or precision."""
 require(type(internal_spans)==list and type(baseline_alerts)==list and type(new_events)==list,'LISTS')
 def hits(events,span):
  return any(span['first_cue']<=e['cue_index']<=span['last_cue'] and e['video_id']==span['video_id'] for e in events)
 hits93=sum(hits(baseline_alerts,x) for x in internal_spans)
 hitsnew=sum(hits(new_events,x) for x in internal_spans)
 hitsunion=sum(hits(baseline_alerts+new_events,x) for x in internal_spans)
 for x in internal_spans:
  require(x.get('independent_gold') is False and x.get('actual_error_certified') is False,'FAKE_GOLD')
  require(x['first_cue']<=x['last_cue'] and all((x['video_id'],i) in source_by_index for i in range(x['first_cue'],x['last_cue']+1)),'SOURCE_SPAN')
 return {'internal_issue_spans_not_gold':len(internal_spans),'v93_direct_overlap':hits93,
         'v103_context_direct_overlap':hitsnew,'v93_v103_union_direct_overlap':hitsunion,
         'certified_financial_precision':None,'certified_financial_recall':None,'independent_gold':False,
         'p0_go':False,'full_source_review_still_required':True}