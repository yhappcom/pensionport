"""No owner SRT in synthetic tests; private replay is a separate test."""
import copy,unittest
from v66_1_incremental_atom_ledger_gate import audit_atomic_ledger,LedgerInvalid
from v66_1_residual_risk_rescreen import inspect_unreviewed

def src(v='ABCdef12345',bucket='P2_GENERAL_OR_CONTEXT',text='연금 추납 1800만원은 질문입니다'):
 return {'video_id':v,'window_id':'W00001','parent_id':'C00001','source_sha256':'a'*64,'triage_bucket':bucket,
 'video_no':1,'claim_id':'C00001','source_excerpt_private':text,'source_excerpt_sha256':'a'*64}
def reviewed(v='ABCdef12345',u='V01_C00001_V66A01',origin='V66'):
 return {'video_id':v,'window_id':'W00001','parent_id':'C00001','parent_source_sha256':'a'*64,'review_origin':origin,'semantic_units':[
 {'unit_id':u,'parent_source_sha256':'a'*64,'financial_truth_approved':False,'independent_gold':False}]}
def canonical(s):return {k:s[k] for k in ('video_id','window_id','parent_id','source_sha256','triage_bucket')}
class TestV66(unittest.TestCase):
 def setUp(self):
  self.s=[canonical(src('ABCdef12345')),canonical(src('ABCdef12346'))]
  self.r=[reviewed('ABCdef12345'),reviewed('ABCdef12346')]
 def reject(self,s=None,r=None):
  with self.assertRaises(LedgerInvalid):audit_atomic_ledger(self.s if s is None else s,self.r if r is None else r)
 def test_v66_origin_is_permitted_but_not_approved(self):
  result=audit_atomic_ledger(self.s,self.r)
  self.assertEqual(result['reviewed_parent_by_version'],{'V66':2})
  self.assertFalse(result['p0_go'])
 def test_reused_child_name_other_video_not_mixed(self):
  self.assertEqual(audit_atomic_ledger(self.s,self.r)['legacy_unqualified_child_ids_reused_cross_video'],1)
 def test_duplicate_source_rejected(self):self.reject(s=self.s+[self.s[0]])
 def test_duplicate_review_rejected(self):self.reject(r=self.r+[self.r[0]])
 def test_modified_parent_sha_rejected(self):
  r=copy.deepcopy(self.r);r[0]['parent_source_sha256']='b'*64;self.reject(r=r)
 def test_modified_child_source_sha_rejected(self):
  r=copy.deepcopy(self.r);r[0]['semantic_units'][0]['parent_source_sha256']='b'*64;self.reject(r=r)
 def test_false_truth_rejected(self):
  r=copy.deepcopy(self.r);r[0]['semantic_units'][0]['financial_truth_approved']=True;self.reject(r=r)
 def test_false_gold_rejected(self):
  r=copy.deepcopy(self.r);r[0]['semantic_units'][0]['independent_gold']=True;self.reject(r=r)
 def test_unknown_parent_rejected(self):
  r=copy.deepcopy(self.r);r[0]['parent_id']='C99999';self.reject(r=r)
 def test_bad_parent_key_rejected(self):
  s=copy.deepcopy(self.s);s[0]['window_id']='BAD';self.reject(s=s)
 def test_unreviewed_lexical_finance_in_P2_is_detected(self):
  x=inspect_unreviewed([src()]);self.assertEqual(x['previous_P2_with_any_broad_finance_keywords'],1)
  self.assertTrue(x['original_lexical_triage_has_false_negative_risk'])
 def test_context_only_P2_not_mislabeled_as_all_finance(self):
  x=inspect_unreviewed([src(text='안녕하세요 다음 질문입니다')]);self.assertEqual(x['previous_P2_with_any_broad_finance_keywords'],0)
 def test_duplicate_unreviewed_source_rejected(self):
  with self.assertRaises(ValueError):inspect_unreviewed([src(),src()])
 def test_case_and_order_consistency(self):
  x=inspect_unreviewed([src('ABCdef12345'),src('ABCdef12346')]);y=inspect_unreviewed([src('ABCdef12346'),src('ABCdef12345')]);self.assertEqual(x['flagged_source_keys_sha256'],y['flagged_source_keys_sha256'])
if __name__=='__main__':unittest.main()
