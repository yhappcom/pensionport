import unittest,copy
from v103_holdout_evaluation_guard import audit_holdout,sha
class T(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.sc=[];cls.fr={};cls.cues=[];cls.parents=[];cls.obs=[]
  for n in range(5):
   v='test'+str(n);w='W00001';texts={i:f'Synthetic financial cue {i} of group {n}' for i in range(1,41)}
   cls.sc.append({'video_id':v,'window_id':w,'first_cue':1,'last_cue':40,'source_window_sha256':sha(' '.join(texts.values())),'draft_parent_count':11+(n>=3)})
   cls.fr[v+'|'+w]={'video_id':v,'window_id':w,'source_sha256':sha(' '.join(texts.values())),'v93_flags':[{'video_id':v,'cue_index':1,'cue_sha256':sha(texts[1])}], 'v103_flags':[{'video_id':v,'cue_index':2,'cue_sha256':sha(texts[2])}]}
   for i in range(1,41):cls.cues.append({'video_id':v,'window_id':w,'cue_index':i,'source_text_private':texts[i],'cue_sha256':sha(texts[i])})
   for j in range(11+(n>=3)):
    ids=[j+1];cls.parents.append({'video_id':v,'window_id':w,'claim_id':f'C{j+1:05}','cue_indices':ids,'source_text_sha256':sha(' | '.join(texts[i] for i in ids))})
   cls.obs.append({'video_id':v,'window_id':w,'first_cue':1,'last_cue':2,'source_span_sha256':sha(sha(texts[1])+sha(texts[2])),'note_private':'Synthetic financial context only, not actual subject fact','needed_evidence_private':'synthetic issuer contract details','independent_gold':False,'actual_finance_error_certified':False,'personal_advice_approved':False,'p0_go':False})
 def runq(self,sc=None,fr=None,cues=None,parents=None,obs=None):
  return audit_holdout(locked={'selected':self.sc if sc is None else sc},forecast=self.fr if fr is None else fr,
     cue_rows=self.cues if cues is None else cues,parent_rows=self.parents if parents is None else parents,
     observations=self.obs if obs is None else obs,observed_risks={'v93_events':5,'v103_events':5})
 def test_valid(self):
  r=self.runq();self.assertEqual(r['v33_draft_parents_source_checked'],57)
 def test_missing_source(self):
  with self.assertRaises(ValueError):self.runq(cues=self.cues[:-1])
 def test_change_source(self):
  z=copy.deepcopy(self.cues);z[0]['source_text_private']='tampered'
  with self.assertRaises(ValueError):self.runq(cues=z)
 def test_fake_gold(self):
  z=copy.deepcopy(self.obs);z[0]['independent_gold']=True
  with self.assertRaises(ValueError):self.runq(obs=z)
 def test_fake_error_certification(self):
  z=copy.deepcopy(self.obs);z[0]['actual_finance_error_certified']=True
  with self.assertRaises(ValueError):self.runq(obs=z)
 def test_fake_advice(self):
  z=copy.deepcopy(self.obs);z[0]['personal_advice_approved']=True
  with self.assertRaises(ValueError):self.runq(obs=z)
 def test_fake_p0(self):
  z=copy.deepcopy(self.obs);z[0]['p0_go']=True
  with self.assertRaises(ValueError):self.runq(obs=z)
 def test_duplicate(self):
  z=copy.deepcopy(self.obs);z[1]=copy.deepcopy(z[0]);
  with self.assertRaises(ValueError):self.runq(obs=z)
 def test_source_window_mismatch(self):
  z=copy.deepcopy(self.sc);z[0]['source_window_sha256']='a'*64
  with self.assertRaises(ValueError):self.runq(sc=z)
 def test_parent_sha(self):
  z=copy.deepcopy(self.parents);z[0]['source_text_sha256']='f'*64
  with self.assertRaises(ValueError):self.runq(parents=z)
 def test_missing_forecast(self):
  z=copy.deepcopy(self.fr);z.pop(next(iter(z)))
  with self.assertRaises(ValueError):self.runq(fr=z)
 def test_undercount(self):
  with self.assertRaises(ValueError):audit_holdout(locked={'selected':self.sc},forecast=self.fr,cue_rows=self.cues,parent_rows=self.parents,observations=self.obs,observed_risks={'v93_events':99,'v103_events':5})
if __name__=='__main__':unittest.main()