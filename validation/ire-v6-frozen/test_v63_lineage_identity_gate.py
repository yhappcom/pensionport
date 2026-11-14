import copy,unittest
from v63_lineage_identity_gate import audit_lineage,LineageIdentityError

def item(v,unit):
    return {'video_id':v,'window_id':'W00001','parent_id':'C00001',
      'parent_source_sha256':'a'*64,'review_origin':'V63',
      'semantic_units':[{'unit_id':unit,'parent_source_sha256':'a'*64,
                         'financial_truth_approved':False,'independent_gold':False}]}

class NamespaceTests(unittest.TestCase):
    def test_identical_bare_id_other_video_is_not_same_claim(self):
        x=audit_lineage([item('ABCdef12345','C00001_V63A01'),item('ABCdef12346','C00001_V63A01')])
        self.assertEqual((x['parents'],x['children']), (2,2))
        self.assertEqual(x['unqualified_child_ids_reused_across_distinct_videos'],1)
        self.assertFalse(x['p0_go'])
    def test_same_qualified_parent_duplicates_rejected(self):
        a=item('ABCdef12345','C00001_V63A01')
        with self.assertRaises(LineageIdentityError):audit_lineage([a,copy.deepcopy(a)])
    def test_duplicate_child_within_same_parent_rejected(self):
        a=item('ABCdef12345','C00001_V63A01');a['semantic_units'].append(copy.deepcopy(a['semantic_units'][0]))
        with self.assertRaises(LineageIdentityError):audit_lineage([a])
    def test_bad_source_hash_rejected(self):
        a=item('ABCdef12345','C00001_V63A01');a['semantic_units'][0]['parent_source_sha256']='b'*64
        with self.assertRaises(LineageIdentityError):audit_lineage([a])
    def test_false_gold_rejected(self):
        a=item('ABCdef12345','C00001_V63A01');a['semantic_units'][0]['independent_gold']=True
        with self.assertRaises(LineageIdentityError):audit_lineage([a])
    def test_false_finance_approved_rejected(self):
        a=item('ABCdef12345','C00001_V63A01');a['semantic_units'][0]['financial_truth_approved']=True
        with self.assertRaises(LineageIdentityError):audit_lineage([a])
    def test_wrong_video_format_rejected(self):
        a=item('bad','C00001_V63A01')
        with self.assertRaises(LineageIdentityError):audit_lineage([a])
    def test_parent_source_key_required(self):
        a=item('ABCdef12345','C00001_V63A01');a.pop('parent_source_sha256')
        with self.assertRaises(LineageIdentityError):audit_lineage([a])
    def test_deterministic_order_invariant(self):
        a=item('ABCdef12345','C00001_V63A01');b=item('ABCdef12346','C00001_V63A01')
        self.assertEqual(audit_lineage([a,b])['canonical_identity_sha256'],audit_lineage([b,a])['canonical_identity_sha256'])

if __name__=='__main__':unittest.main()
