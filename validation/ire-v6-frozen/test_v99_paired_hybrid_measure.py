"""V99 synthetic internal-issue comparison, never blind precision or recall."""
import copy,unittest
from test_v98_hybrid_source_guard import Fixture,SCOPE,ALERT_POS
from v99_paired_hybrid_measure import paired_compare,validate_structural_benchmark
from v98_hybrid_source_guard import sha

class TestV99(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.f=Fixture();cls.h=cls.f.route();cls.issues=[]
  # 12 intervals with a direct synthetic alert, 8 without one.
  for v,w,np,nf in SCOPE[:4]:
   first=(int(w[1:])-1)*40+1
   hits=[first+off-1 for off in ALERT_POS[w]]
   count={"W00026":3,"W00018":2,"W00117":5,"W00053":2}[w]
   for idx in hits[:count]:
    cls.issues.append({'video_id':v,'window_id':w,'first_cue':idx,'last_cue':idx,
     'source_span_sha256':sha(sha(cls.f.text(w,idx))),'independent_gold':False,'actual_error_certified':False})
  for v,w,np,nf in SCOPE[:4]:
   first=(int(w[1:])-1)*40+1
   hits={first+off-1 for off in ALERT_POS[w]}
   gaps=[i for i in range(first,first+40) if i not in hits]
   for idx in gaps[:2]:
    cls.issues.append({'video_id':v,'window_id':w,'first_cue':idx,'last_cue':idx,
     'source_span_sha256':sha(sha(cls.f.text(w,idx))),'independent_gold':False,'actual_error_certified':False})
  assert len(cls.issues)==20
  cls.ok=paired_compare(cls.f.source,cls.f.alerts,cls.issues,cls.h)
 def test_20_all_routed_not_certified(self):
  d=self.ok;self.assertEqual(d['v98_issue_spans_routed_to_review'],20)
  self.assertEqual(d['v96_issue_spans_without_direct_alert'],8)
  self.assertIsNone(d['financial_recall']);self.assertFalse(d['all_200_cues_semantically_reviewed'])
 def test_55_baseline(self):self.assertEqual(self.ok['v98_obligatory_baseline_fallback'],55)
 def test_fail_fake_independent_gold(self):
  x=copy.deepcopy(self.issues);x[0]['independent_gold']=True
  with self.assertRaises(ValueError):paired_compare(self.f.source,self.f.alerts,x,self.h)
 def test_fail_wrong_issue_span_sha(self):
  x=copy.deepcopy(self.issues);x[0]['source_span_sha256']='a'*64
  with self.assertRaises(ValueError):paired_compare(self.f.source,self.f.alerts,x,self.h)
 def test_fail_missing_issue(self):
  with self.assertRaises(ValueError):paired_compare(self.f.source,self.f.alerts,self.issues[:-1],self.h)
 def test_fail_duplicate_issue(self):
  x=copy.deepcopy(self.issues);x[0]=copy.deepcopy(x[1])
  with self.assertRaises(ValueError):paired_compare(self.f.source,self.f.alerts,x,self.h)
 def test_fail_dropped_route(self):
  h=copy.deepcopy(self.h);h['private_cue_routes'].pop()
  with self.assertRaises(ValueError):paired_compare(self.f.source,self.f.alerts,self.issues,h)
 def test_fail_fake_review_completed(self):
  h=copy.deepcopy(self.h);h['private_cue_routes'][0]['review_completed']=True
  with self.assertRaises(ValueError):paired_compare(self.f.source,self.f.alerts,self.issues,h)
 def test_fail_changed_routing_source_sha(self):
  h=copy.deepcopy(self.h);h['private_cue_routes'][0]['cue_sha256']='f'*64
  with self.assertRaises(ValueError):paired_compare(self.f.source,self.f.alerts,self.issues,h)
 def test_valid_benchmark(self):
  a={'repetitions':500,'alternated_order':True,'v91_parent_census':{'median_ms':.2,'p95_ms':.4},'v96_risk_screen':{'median_ms':.35,'p95_ms':.5},'v98_hybrid_route':{'median_ms':.7,'p95_ms':.9},'p0_go':False,'independent_gold':False}
  self.assertTrue(validate_structural_benchmark(a))
 def test_false_actual_semantic_speedup(self):
  a={'repetitions':500,'alternated_order':True,'v91_parent_census':{'median_ms':.2,'p95_ms':.4},'v96_risk_screen':{'median_ms':.35,'p95_ms':.5},'v98_hybrid_route':{'median_ms':.7,'p95_ms':.9},'p0_go':False,'independent_gold':False,'certified_workflow_speedup':2}
  with self.assertRaises(ValueError):validate_structural_benchmark(a)
 def test_invalid_timer(self):
  a={'repetitions':500,'alternated_order':True,'v91_parent_census':{'median_ms':1,'p95_ms':.5},'v96_risk_screen':{'median_ms':.2,'p95_ms':.4},'v98_hybrid_route':{'median_ms':.6,'p95_ms':.8},'p0_go':False,'independent_gold':False}
  with self.assertRaises(ValueError):validate_structural_benchmark(a)

if __name__=='__main__':unittest.main()