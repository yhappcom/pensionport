"""Synthetic quality adversarial tests; owner original speech stays private."""
import copy
import unittest
from v68_context_risk_gate import risk_gate, require_research_quality_for_advice, SourceQualityError, _sha

VID='FAKE1234567'

def fixture(mid='네 맞아요', left='이 돈을 국민연금으로 추납할 경우', right='월 0.6% 가산됩니다'):
    texts={1:[left,mid,right]}
    rows=[]
    for i,t in enumerate(texts[1],1):
        row={'video_no':1,'video_id':VID,'window_id':'W00001','claim_id':f'C{i:05d}',
             'cue_indices':[i],'source_excerpt_private':t,
             'source_excerpt_sha256':_sha(t),'triage_bucket':'P2_GENERAL_OR_CONTEXT'}
        rows.append(row)
    pending=[{**r,'human_atomic_review_completed':False,'independent_gold':False,
              'approval_restricted':True} for r in rows]
    return rows,pending,texts

class TestV68(unittest.TestCase):
    def run_v68(self,s,p,t):return risk_gate(s,p,t,expected_source=3,expected_pending=3)
    def reject(self,mutator):
        s,p,t=fixture()
        s,p,t=copy.deepcopy((s,p,t));mutator(s,p,t)
        with self.assertRaises(SourceQualityError):self.run_v68(s,p,t)
    def test_context_signal_catches_previous_general_cue(self):
        s,p,t=fixture()
        receipt,docket=self.run_v68(s,p,t)
        self.assertEqual(receipt['p2_direct_financial_or_quantity_signal'],2)
        self.assertEqual(receipt['p2_additional_signal_only_within_2_original_cues'],1)
        self.assertTrue(any(x['parent_id']=='C00002' and
                            x['priority_tier']=='CONTEXT_ONLY_ESCALATION'
                            for x in docket))
        self.assertFalse(receipt['p0_go'])
    def test_zero_signal_never_cleared_as_nonfinancial(self):
        s,p,t=fixture(left='안녕하세요',mid='좋은 날입니다',right='감사합니다')
        receipt,docket=self.run_v68(s,p,t)
        self.assertEqual(receipt['p2_total_context_escalated'],0)
        self.assertTrue(all(not x['approved_as_nonfinancial'] for x in docket))
        with self.assertRaises(SourceQualityError):require_research_quality_for_advice(receipt)
    def test_mutated_original_byte_fails(self):
        self.reject(lambda s,p,t:t[1].__setitem__(1,'다른 원문입니다'))
    def test_mutated_source_excerpt_sha_fails(self):
        self.reject(lambda s,p,t:s[0].__setitem__('source_excerpt_sha256','0'*64))
    def test_mutated_pending_excerpt_fails(self):
        self.reject(lambda s,p,t:p[0].__setitem__('source_excerpt_private','잘못 바꾼 주장'))
    def test_mutated_pending_bucket_fails(self):
        self.reject(lambda s,p,t:p[0].__setitem__('triage_bucket','P0_SCOPED_FINANCE'))
    def test_false_manual_review_fails(self):
        self.reject(lambda s,p,t:p[0].__setitem__('human_atomic_review_completed',True))
    def test_false_independent_gold_fails(self):
        self.reject(lambda s,p,t:p[0].__setitem__('independent_gold',True))
    def test_false_advice_approval_fails(self):
        self.reject(lambda s,p,t:p[0].__setitem__('approval_restricted',False))
    def test_duplicate_pending_fails(self):
        self.reject(lambda s,p,t:p.__setitem__(1,p[0]))
    def test_source_cue_indices_out_of_bounds_fails(self):
        self.reject(lambda s,p,t:s[0].__setitem__('cue_indices',[4]))
    def test_source_parent_duplicate_fails(self):
        self.reject(lambda s,p,t:s.__setitem__(1,copy.deepcopy(s[0])))
    def test_extra_video_fails(self):
        self.reject(lambda s,p,t:t.__setitem__(2,['별도 영상입니다']))
    def test_row_count_mismatch_fails(self):
        s,p,t=fixture()
        with self.assertRaises(SourceQualityError):risk_gate(s,p,t,expected_source=3,expected_pending=4)
    def test_context_window_hash_changes_if_neighbor_changes(self):
        s,p,t=fixture()
        a,rows_a=self.run_v68(s,p,t)
        s2,p2,t2=fixture(left='국민연금 연기 중입니다')
        b,rows_b=self.run_v68(s2,p2,t2)
        self.assertNotEqual(rows_a[1]['context_sha256'],rows_b[1]['context_sha256'])
        self.assertNotEqual(a['parent_provenance_and_context_docket_sha256'],b['parent_provenance_and_context_docket_sha256'])
    def test_advisory_release_fail_closed_even_if_fake_zero_pending(self):
        fake={'schema':'IRE_V6_V68_REAL_SOURCE_CONTEXT_QUALITY_FAIL_CLOSED_GUARD_SHA_ONLY',
              'source_parent_pending_review':0,'independent_gold':True,'p0_go':True}
        with self.assertRaises(SourceQualityError):require_research_quality_for_advice(fake)

if __name__=='__main__':unittest.main()
