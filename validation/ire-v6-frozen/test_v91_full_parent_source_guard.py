"""V91 public synthetic-only negative tests; no owner SRT or private meanings."""
import copy,unittest
from dataclasses import dataclass
from v91_full_parent_source_guard import (EXPECTED,VIDEO_ID,FALSE_FLAGS,STATUS,GAP_STATUS,
 verify_complete_draft_census,verify_parent,verify_gap,deny_promotion,expected_unassigned,sha)
from v87_targeted_source_guard import expected_parent_source
@dataclass
class Cue:
 index:int
 start_ms:int
 end_ms:int
 text:str
MEANING='가상 발화의 금융 맥락을 조건부 개인 사례로 해석하되 다른 사람의 투자성과나 제도적 정답으로 인정하지 않습니다.'
CAUTION='합성 시험에서는 투자 적합성, 현행 금융 법령과 장부 내역을 알 수 없으므로 매매나 개인 세금 계산에 대한 승인으로 사용하지 않습니다.'

class V91Synthetic(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.cues=[Cue(i,i*100,i*100+90,f'합성 금융자막 문장 {i}번 입니다') for i in range(1,10729)]
  cls.regs={};cls.screens=[];cls.rows=[];cls.gaps=[]
  for n in range(1,270):
   w=f'W{n:05d}';first=(n-1)*40+1;last=min(n*40,len(cls.cues))
   keys=EXPECTED.get(w,('SYNTHETIC_'+w,))
   parents=[]
   for j,k in enumerate(keys):
    # Every real V91 source parent is fully separate. Synthetic fixture need not mimic cue text.
    idx=first+j
    parents.append({'claim_id':k,'cue_indices':[idx],
        'source_text_sha256':sha(cls.cues[idx-1].text.encode())})
   cls.regs[w]=parents
   source=' '.join(cls.cues[i-1].text for i in range(first,last+1))
   cls.screens.append({'video_id':VIDEO_ID,'video_no':7,'window_id':w,
     'first_cue':first,'last_cue':last,'source_window_sha256':sha(source.encode()),
     'draft_parent_count':len(parents),'manual_reviewed_all_parents':False,
     'fact_approved':False,'independent_gold':False,'personal_action_approved':False})
  # For synthetic fixture, mark every remaining cue in selected windows as *assigned* to
  # a draft candidate; only one explicit nonclaim synthetic gap remains at cue 9239.
  for w in EXPECTED:
   first=(int(w[1:])-1)*40+1;last=first+39
   parents=cls.regs[w];first_parent_count=len(parents)
   for idx in range(first+first_parent_count,last+1):
    if idx==9239:continue
    parents[-1]['cue_indices'].append(idx)
   for p in parents:
    p['source_text_sha256']=sha(' | '.join(cls.cues[i-1].text for i in p['cue_indices']).encode())
  cls.selected=[s for s in cls.screens if s['window_id'] in EXPECTED]
  for w,ids in EXPECTED.items():
   for cid in ids:
    src=expected_parent_source(cls.cues,cls.regs,(w,cid))
    cls.rows.append({**src,'video_no':7,'video_id':VIDEO_ID,'status':STATUS,
      'semantic_kind':'HISTORICAL_CASE','speaker_meaning_private':MEANING,
      'scope_caution_private':CAUTION,'risk_domain':'SYNTHETIC_FINANCE',
      **{f:False for f in FALSE_FLAGS}})
  gap=cls.cues[9239-1]
  cls.gaps=[{'video_id':VIDEO_ID,'video_no':7,'window_id':'W00231','cue_index':9239,
    'source_text_private':gap.text,'source_sha256':sha(gap.text.encode()),
    'start_ms':gap.start_ms,'end_ms':gap.end_ms,'status':GAP_STATUS,
    'speech_act':'MINIMAL_RESPONSE','contextual_reason_private':
      '가상 대화에서 동의 표현만 있으며 숫자나 금융 사실의 단독 진술이 없음을 인접 문맥에서 확인했지만 독립 정답은 아닙니다.',
    **{f:False for f in ('negative_gold','fact_approved','personal_action_approved',
      'financial_fact_certified','independent_gold','full_window_semantics_certified')}}]
  used=[f'W{i:05d}' for i in range(1,270) if f'W{i:05d}' not in EXPECTED][:65]
  cls.prior={(used[i%65],f'PRIOR_{i:04d}') for i in range(205)}

 def verify(self,rows=None,gaps=None,selected=None,prior=None):
  return verify_complete_draft_census(self.rows if rows is None else rows,
   self.gaps if gaps is None else gaps,self.selected if selected is None else selected,
   self.screens,self.cues,self.regs,self.prior if prior is None else prior)
 def test_complete_55_and_five_no_go(self):
  r=self.verify();self.assertEqual(r['whole_draft_parent_census_parents'],55)
  self.assertEqual(r['cumulative_source_bound_parents'],260)
  self.assertEqual(r['cumulative_sampled_windows'],70)
  self.assertEqual(r['video7_windows_without_parent_sample'],199)
  self.assertTrue(r['all_draft_parents_in_5_windows_reviewed'])
  for f in ('p0_go','independent_gold','source_wide_atomic_claim_recall_certified',
   'full_window_semantics_certified','personalized_advice_approved','financial_fact_certified'):
   self.assertFalse(r[f])
 def test_all_parent_counts(self):self.assertEqual([len(x) for x in EXPECTED.values()],[13,10,13,9,10])
 def test_gap_census(self):self.assertEqual(expected_unassigned(self.cues,self.regs),{('W00231',9239)})
 def test_missing_one_parent(self):
  with self.assertRaises(ValueError):self.verify(rows=self.rows[:-1])
 def test_duplicate_parent(self):
  r=copy.deepcopy(self.rows);r[4]=copy.deepcopy(r[0]);
  with self.assertRaises(ValueError):self.verify(rows=r)
 def test_fake_parent_id(self):
  r=copy.deepcopy(self.rows);r[0]['claim_id']='C99999'
  with self.assertRaises(ValueError):self.verify(rows=r)
 def test_prior_overlap(self):
  prior=set(self.prior);prior.remove(next(iter(prior)));prior.add(('W00076','FAKE'))
  with self.assertRaises(ValueError):self.verify(prior=prior)
 def test_prior_missing(self):
  prior=set(self.prior);prior.pop()
  with self.assertRaises(ValueError):self.verify(prior=prior)
 def test_original_window_changed(self):
  s=copy.deepcopy(self.selected);s[0]['source_window_sha256']='0'*64
  with self.assertRaises(ValueError):self.verify(selected=s)
 def test_fake_screen_census(self):
  s=copy.deepcopy(self.selected);s[0]['draft_parent_count']=1
  with self.assertRaises(ValueError):self.verify(selected=s)
 def test_false_original_screen_go(self):
  s=copy.deepcopy(self.selected);s[0]['manual_reviewed_all_parents']=True
  with self.assertRaises(ValueError):self.verify(selected=s)
 def test_wrong_parent_cue(self):
  r=copy.deepcopy(self.rows);r[0]['cue_indices']=[1]
  with self.assertRaises(ValueError):self.verify(rows=r)
 def test_source_text_spoof(self):
  r=copy.deepcopy(self.rows);r[0]['source_excerpt_private']='fraud'
  with self.assertRaises(ValueError):self.verify(rows=r)
 def test_context_spoof(self):
  r=copy.deepcopy(self.rows);r[0]['adjacent_cues_private'][0]['text_private']='different'
  with self.assertRaises(ValueError):self.verify(rows=r)
 def test_false_p3_go(self):
  r=copy.deepcopy(self.rows);r[0]['personal_action_approved']=True
  with self.assertRaises(ValueError):self.verify(rows=r)
 def test_fake_gold(self):
  r=copy.deepcopy(self.rows);r[0]['independent_gold']=True
  with self.assertRaises(ValueError):self.verify(rows=r)
 def test_no_context_meaning(self):
  r=copy.deepcopy(self.rows);r[0]['speaker_meaning_private']='none'
  with self.assertRaises(ValueError):self.verify(rows=r)
 def test_wrong_kind(self):
  r=copy.deepcopy(self.rows);r[0]['semantic_kind']='CERTIFIED'
  with self.assertRaises(ValueError):self.verify(rows=r)
 def test_missing_gap(self):
  with self.assertRaises(ValueError):self.verify(gaps=[])
 def test_negative_gold_gap(self):
  g=copy.deepcopy(self.gaps);g[0]['negative_gold']=True
  with self.assertRaises(ValueError):self.verify(gaps=g)
 def test_wrong_gap_text(self):
  g=copy.deepcopy(self.gaps);g[0]['source_text_private']='filler'
  with self.assertRaises(ValueError):self.verify(gaps=g)
 def test_wrong_gap_speech_act(self):
  g=copy.deepcopy(self.gaps);g[0]['speech_act']='FINANCIAL_FACT'
  with self.assertRaises(ValueError):self.verify(gaps=g)
 def test_no_p3_promotion(self):
  self.assertFalse(deny_promotion(self.rows[0])['can_promote_p3'])
if __name__=='__main__':unittest.main()