"""V86 fail-closed independent source context/long-form screening gate.

Source/fixture guard only: its automated flags are NEVER golden labels,
legal compliance approvals, or ChatGPT semantic review for all windows.
"""
from __future__ import annotations
import hashlib,json,re
from collections import Counter
from pathlib import Path

SOURCE_SHA='00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd'
V85_SHA='0c87078e870bb88536667cc5a60a68eaeff71914740c9571242dc988caaa584d'
VIDEO_ID='4CQ4FjGT2gA'
V85_GAP_MEMBER='V85_PRIVATE_NEW5_295_UNCAPTURED_SOURCE_CONTEXT_NOT_NEGATIVE_GOLD.json'
V85_REVIEW_MEMBER='V85_PRIVATE_NEW5_31_MEANING_PROBES_NOT_FINANCE_APPROVAL.json'
EXPECTED_CRITICAL=((6,361),(7,1076),(7,2721),(7,3664),(7,4692),(7,5609),
(7,5929),(7,7298),(7,8911),(7,9894),(7,10189),(8,801),(8,802),(8,953),
(8,1001),(9,70),(9,780),(9,799))
EXPECTED_PARENT=(("W00010","C00131"),("W00027","C00416"),
("W00029","C00437"),("W00068","C00994"),("W00092","C01271"),
("W00105","C01435"),("W00118","C01564"),("W00141","C01816"),
("W00149","C01912"),("W00149","C01913"),("W00183","C02331"),
("W00223","C02857"),("W00223","C02858"),("W00248","C03118"),
("W00255","C03200"),("W00269","C03340"))
NO_GO_FIELDS=('fact_approved','independent_gold','official_parent_merged',
              'personal_action_approved','v75_membership_verified')
SCREEN_PATTERNS={
 'PENSION_TAX': re.compile(r'연금|추납|국민연금|퇴직금|ISA|IRP|세액|절세|비과세|종합과세|소득세|증여'),
 'CREDIT_RATE': re.compile(r'BBB|A0|신용|회사채|채권|금리|국채|원금|보장|이자|예금|적금'),
 'INVESTMENT_RISK': re.compile(r'손실|위험|하락|매도|매수|리밸런싱|분산|금|달러|ETF|환율|주식|수익률'),
 'NUMBER_AMOUNT': re.compile(r'\d[\d,.]*(?:%|억|만원|만|원|년|개월|세|배|주)'),
 'QUESTION': re.compile(r'\?|어떻게|할까요|될까요|되나요|맞나요|그러면'),
 'UNCERTAINTY': re.compile(r'아마|같아요|모르|가정|가령|만약|느낌|생각|경우|수도|전제')}

def require(cond,code):
 if not cond: raise ValueError('V86_'+code)

def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def digest(obj):return sha_bytes(json.dumps(obj,ensure_ascii=False,sort_keys=True,
                          separators=(',',':'),allow_nan=False).encode('utf-8'))

def safe_false(row):
 for k in NO_GO_FIELDS:require(row.get(k) is False,'FALSE_APPROVAL_'+k)
 require(row.get('status') in ('CHAT_CONTEXTUAL_SHADOW_NOT_GOLD','SOURCE_BOUND_AUTOMATED_SCREEN_NOT_GOLD'),
         'FALSE_STATUS')

def check_cue_review(r,source,expected_kind):
 """Verify original excerpt, context and model meaning are bound to one cue."""
 require(r['video_no']==source['video_no'] and r['cue_index']==source['cue_index'],'CUE_ID')
 require(r['video_id']==source['video_id'] and r['cue_text_private']==source['cue_text_private'],'CUE_SOURCE')
 require(r['cue_text_sha256']==sha_bytes(source['cue_text_private'].encode()),'CUE_HASH')
 require(r['start_ms']==source['start_ms'] and r['end_ms']==source['end_ms'],'CUE_TIME')
 require(r['adjacent_cues_private']==source['adjacent_cues_private'],'CUE_CONTEXT')
 require(r['adjacent_context_sha256']==digest(source['adjacent_cues_private']),'CUE_CONTEXT_HASH')
 require(r['semantic_kind']==expected_kind,'CUE_KIND_CHANGED')
 require(isinstance(r.get('interpretation_private'),str) and len(r['interpretation_private'])>20,'NO_CUE_SEMANTICS')
 require(isinstance(r.get('caution_private'),str) and len(r['caution_private'])>20,'NO_CUE_CAUTION')
 require(r['status']=='CHAT_CONTEXTUAL_SHADOW_NOT_GOLD','STATUS_CUE')
 safe_false(r)
 return digest([r['video_no'],r['cue_index'],r['cue_text_sha256'],r['semantic_kind'],
   sha_bytes(r['interpretation_private'].encode('utf-8')),
   sha_bytes(r['caution_private'].encode('utf-8'))])

def check_parent_review(r,source,expected_kind):
 require(r['video_no']==7 and r['video_id']==VIDEO_ID,'VIDEO_ID_PARENT')
 require((r['window_id'],r['claim_id'])==(source['window_id'],source['claim_id']),'PARENT_KEY')
 for k in ('cue_indices','source_excerpt_private','start_ms','end_ms','adjacent_cues_private'):
  require(r.get(k)==source[k],'PARENT_OR_ADJACENT_MUTATED')
 require(r.get('source_sha256')==sha_bytes(source['source_excerpt_private'].encode()),'PARENT_HASH')
 require(r.get('adjacent_context_sha256')==digest(source['adjacent_cues_private']),'PARENT_CONTEXT_HASH')
 require(r.get('semantic_kind')==expected_kind,'PARENT_KIND_CHANGED')
 require(len(r.get('interpretation_private',''))>30 and len(r.get('caution_private',''))>30,'PARENT_NO_REVIEW')
 require(isinstance(r.get('scope_risk'),str) and r['scope_risk'],'NO_SCOPE_RISK')
 require(r['status']=='CHAT_CONTEXTUAL_SHADOW_NOT_GOLD','STATUS_PARENT')
 safe_false(r)
 return digest([r['window_id'],r['claim_id'],r['source_sha256'],r['semantic_kind'],
     sha_bytes(r['interpretation_private'].encode('utf-8'))])

def screen_windows(cues,regs):
 """Full source-bound automated 40-cue partition; a risk screen is not a claim verdict."""
 require(len(regs)==(len(cues)+39)//40,'WINDOW_COUNT_DRIFT')
 rows=[]; seen=set(); assigned=set()
 for n in range(1,len(regs)+1):
  wid=f'W{n:05d}';require(wid in regs,'WINDOW_MISSING')
  batch=cues[(n-1)*40:n*40]
  require(batch and len(batch)<=40,'WINDOW_BOUNDARY')
  require([c.index for c in batch]==list(range((n-1)*40+1,(n-1)*40+1+len(batch))),
          'WINDOW_CUE_GAP')
  local=set();rs=regs[wid]
  for p in rs:
   require(p['claim_id'] not in seen,'DUPLICATE_DRAFT_PARENT');seen.add(p['claim_id'])
   ids=p['cue_indices'];require(ids and len(ids)==len(set(ids)),'DUPLICATE_OR_EMPTY_CUES')
   require(all((n-1)*40 < i <= min(n*40,len(cues)) for i in ids),'CROSS_WINDOW_CUE')
   require(not set(ids)&local,'OVERLAPPING_SOURCE_DRAFT')
   local.update(ids);assigned.update(ids)
   joined=' | '.join(cues[i-1].text for i in ids)
   require(sha_bytes(joined.encode())==p['source_text_sha256'],'CANDIDATE_HASH')
  full=' '.join(c.text for c in batch)
  matches={name:len(pat.findall(full)) for name,pat in SCREEN_PATTERNS.items()}
  score=3*matches['PENSION_TAX']+3*matches['CREDIT_RATE']+2*matches['INVESTMENT_RISK']+matches['NUMBER_AMOUNT']+matches['QUESTION']+matches['UNCERTAINTY']
  rows.append({'video_no':7,'video_id':VIDEO_ID,'window_id':wid,
   'first_cue':batch[0].index,'last_cue':batch[-1].index,
   'source_window_sha256':sha_bytes(full.encode()),
   'draft_parent_count':len(rs),'draft_assigned_cues':len(local),
   'source_cues_without_candidate':len(batch)-len(local),
   'screen_hits':matches,'screen_score_heuristic_only':score,
   'screen_status':'SOURCE_BOUND_AUTOMATED_SCREEN_NOT_GOLD',
   'manual_reviewed_all_parents':False,'independent_gold':False,
   'fact_approved':False,'personal_action_approved':False})
 require(len(seen)==sum(len(x) for x in regs.values()),'PARENT_TOTAL')
 require(len(assigned)+sum(x['source_cues_without_candidate'] for x in rows)==len(cues),'CUE_PARTITION')
 return rows

def validate_screen(rows,cues,regs):
 require(len(rows)==269,'SCREEN_269_REQUIRED')
 expected=screen_windows(cues,regs)
 require(rows==expected,'WINDOW_SCREEN_CHANGED')
 require(sum(x['draft_parent_count'] for x in rows)==3341,'SOURCE_PARENT_3341')
 require(sum(x['source_cues_without_candidate'] for x in rows)==186,'SOURCE_GAPS_186')
 require(len(cues)==10728,'SOURCE_CUES_10728')
 return {'screened_windows':269,'draft_parents':3341,'unassigned_cues':186,
   'screened_window_digest_sha256':digest(rows),
   'manual_semantic_reviews_for_269_windows':False,'precision_recall':'NO_SCORE'}