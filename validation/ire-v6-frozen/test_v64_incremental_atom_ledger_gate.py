import unittest,copy
from v64_incremental_atom_ledger_gate import audit_atomic_ledger,LedgerInvalid
A='ABCdef12345';B='ABCdef12346';H='a'*64

def source(v,n=1,triage='P0_SCOPED_FINANCE'):
    return {'video_id':v,'window_id':'W00001','parent_id':f'C{n:05d}','source_sha256':H,'triage_bucket':triage}
def review(v,n=1,unit='C00001_V62A01',origin='V62'):
    return {'video_id':v,'window_id':'W00001','parent_id':f'C{n:05d}',
            'parent_source_sha256':H,'review_origin':origin,'semantic_units':[
                {'unit_id':unit,'parent_source_sha256':H,'financial_truth_approved':False,'independent_gold':False}]}
class TestLedger(unittest.TestCase):
    def setUp(self):
        self.s=[source(A),source(B)]
        self.r=[review(A),review(B)]
    def test_legacy_child_id_from_other_video_not_clobbered(self):
        result=audit_atomic_ledger(self.s,self.r)
        self.assertEqual((result['source_grounded_parent_review_count'],result['source_grounded_child_semantic_unit_count']),(2,2))
        self.assertEqual(result['legacy_unqualified_child_ids_reused_cross_video'],1)
        self.assertFalse(result['p0_go'])
    def reject(self,s=None,r=None):
        with self.assertRaises(LedgerInvalid):audit_atomic_ledger(self.s if s is None else s,self.r if r is None else r)
    def test_duplicate_frozen_source(self):self.reject(s=self.s+self.s)
    def test_unknown_parent(self):self.reject(r=[review(A,2)])
    def test_duplicate_parent(self):self.reject(r=self.r+[copy.deepcopy(self.r[0])])
    def test_duplicate_child_same_parent(self):
        r=copy.deepcopy(self.r);r[0]['semantic_units']*=2;self.reject(r=r)
    def test_bad_parent_source_sha(self):
        r=copy.deepcopy(self.r);r[0]['parent_source_sha256']='b'*64;self.reject(r=r)
    def test_bad_child_source_sha(self):
        r=copy.deepcopy(self.r);r[0]['semantic_units'][0]['parent_source_sha256']='b'*64;self.reject(r=r)
    def test_false_gold(self):
        r=copy.deepcopy(self.r);r[0]['semantic_units'][0]['independent_gold']=True;self.reject(r=r)
    def test_false_finance_approval(self):
        r=copy.deepcopy(self.r);r[0]['semantic_units'][0]['financial_truth_approved']=True;self.reject(r=r)
    def test_bad_bucket(self):
        s=copy.deepcopy(self.s);s[0]['triage_bucket']='P0_GO';self.reject(s=s)
    def test_order_invariant(self):
        self.assertEqual(audit_atomic_ledger(self.s,self.r)['qualified_ledger_sha256'],audit_atomic_ledger(self.s[::-1],self.r[::-1])['qualified_ledger_sha256'])
    def test_new_v64_origin(self):
        x=review(A,unit='V01_C00001_V64A01',origin='V64')
        result=audit_atomic_ledger([source(A)],[x]);self.assertEqual(result['reviewed_parent_by_version'],{'V64':1})
    def test_reject_padded_cue_id(self):
        s=copy.deepcopy(self.s);s[0]['parent_id']='Cxxxx';self.reject(s=s)
if __name__=='__main__': unittest.main()
