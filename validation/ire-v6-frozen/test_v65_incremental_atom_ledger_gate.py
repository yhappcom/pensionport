"""V65 synthetic provenance tests; no user SRT or semantic statements."""
import copy,unittest
from v65_incremental_atom_ledger_gate import audit_atomic_ledger,LedgerInvalid

def source(vid, i=1):
 return {'video_id':vid,'window_id':'W00001','parent_id':f'C{i:05d}','source_sha256':'a'*64,'triage_bucket':'P0_SCOPED_FINANCE'}
def reviewed(vid,i=1,origin='V65',unit='V65A01_C00001'):
 return {'video_id':vid,'window_id':'W00001','parent_id':f'C{i:05d}','parent_source_sha256':'a'*64,
 'review_origin':origin,'semantic_units':[{'unit_id':unit,'parent_source_sha256':'a'*64,
 'financial_truth_approved':False,'independent_gold':False}]}
class TestV65(unittest.TestCase):
 def setUp(self):
  self.s=[source('ABCdef12345'),source('ABCdef12346')]
  self.r=[reviewed('ABCdef12345',origin='V64'),reviewed('ABCdef12346',origin='V65')]
 def reject(self,s=None,r=None):
  with self.assertRaises(LedgerInvalid):audit_atomic_ledger(self.s if s is None else s,self.r if r is None else r)
 def test_legacy_plus_new_source_id(self):
  d=audit_atomic_ledger(self.s,self.r);self.assertEqual(d['reviewed_parent_by_version'],{'V64':1,'V65':1});self.assertEqual(d['source_grounded_child_semantic_unit_count'],2)
  self.assertFalse(d['p0_go'])
 def test_cross_video_same_bare_child_allowed(self):
  self.assertEqual(audit_atomic_ledger(self.s,self.r)['legacy_unqualified_child_ids_reused_cross_video'],1)
 def test_unrecognized_origin_blocked(self):
  r=copy.deepcopy(self.r);r[0]['review_origin']='V66';self.reject(r=r)
 def test_parent_excerpt_hash_changed_blocked(self):
  r=copy.deepcopy(self.r);r[0]['parent_source_sha256']='b'*64;self.reject(r=r)
 def test_duplicate_source_id_blocked(self):self.reject(s=self.s+[self.s[0]])
 def test_duplicate_qualified_child_blocked(self):
  r=copy.deepcopy(self.r);r[0]['semantic_units']*=2;self.reject(r=r)
 def test_source_other_video_forged_blocked(self):
  r=copy.deepcopy(self.r);r[0]['video_id']='ABCdef12347';self.reject(r=r)
 def test_false_finance_approval_blocked(self):
  r=copy.deepcopy(self.r);r[0]['semantic_units'][0]['financial_truth_approved']=True;self.reject(r=r)
 def test_fake_independent_gold_blocked(self):
  r=copy.deepcopy(self.r);r[0]['semantic_units'][0]['independent_gold']=True;self.reject(r=r)
 def test_child_parent_source_drift_blocked(self):
  r=copy.deepcopy(self.r);r[0]['semantic_units'][0]['parent_source_sha256']='b'*64;self.reject(r=r)
 def test_order_independent_key_digest(self):
  self.assertEqual(audit_atomic_ledger(self.s,self.r)['qualified_ledger_sha256'],audit_atomic_ledger(self.s[::-1],self.r[::-1])['qualified_ledger_sha256'])
if __name__=='__main__': unittest.main()
