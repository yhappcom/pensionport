import unittest,copy
from v95_performance_and_gold_gate import independent_quality,measure_source_processing,digest
class T(unittest.TestCase):
 def setUp(self):
  self.gold=[{'id':str(i),'label':'FACT' if i%4 else 'NO_FACT','high_risk':i<40} for i in range(100)]
  self.pred=[{'id':r['id'],'predicted':r['label']} for r in self.gold]
 def calc(self,gold=None,pred=None,**kw):
  g=self.gold if gold is None else gold;p=self.pred if pred is None else pred
  return independent_quality(g,p,source_sha256='0'*64,gold_sha256=digest(g),prediction_sha256=digest(p),independent_reviewer_attested=True,**kw)
 def test_no_gold_no_score(self):self.assertEqual(independent_quality(None,None)['status'],'NO_SCORE')
 def test_no_reviewers_no_score(self):self.assertEqual(independent_quality(self.gold,self.pred)['status'],'NO_SCORE')
 def test_synthetic_math_not_certified(self):
  x=self.calc();self.assertEqual(x['precision'],1);self.assertEqual(x['recall'],1);self.assertFalse(x['p0_go']);self.assertFalse(x['gold_authorship_validated_by_software'])
 def test_fp_fn(self):
  p=copy.deepcopy(self.pred);p[0]['predicted']='FACT';p[1]['predicted']='NO_FACT';x=self.calc(pred=p);self.assertEqual((x['fp'],x['fn']),(1,1))
 def test_bad_pin(self):
  with self.assertRaises(ValueError):independent_quality(self.gold,self.pred,source_sha256='0'*64,gold_sha256='x',prediction_sha256=digest(self.pred),independent_reviewer_attested=True)
 def test_missing_prediction(self):
  p=self.pred[:-1]
  with self.assertRaises(ValueError):self.calc(pred=p)
 def test_duplicate_prediction(self):
  p=copy.deepcopy(self.pred);p[0]['id']=p[1]['id']
  with self.assertRaises(ValueError):self.calc(pred=p)
 def test_local_throughput(self):
  x=measure_source_processing(lambda: sum(1 for _ in range(200)),rounds=3,min_expected=200)
  self.assertEqual(x['source_cues_per_run'],200);self.assertFalse(x['runtime_includes_model_semantic_review'])
 def test_nondeterministic(self):
  num=[1]
  def work():num[0]+=1;return num[0]
  with self.assertRaises(ValueError):measure_source_processing(work,rounds=3)
 def test_low_gold_denominator_not_pass(self):
  g=[{'id':'1','label':'FACT','high_risk':True}];p=[{'id':'1','predicted':'FACT'}];x=self.calc(gold=g,pred=p);self.assertFalse(x['scoring_thresholds_met']);self.assertFalse(x['p0_go'])
if __name__=='__main__':unittest.main()