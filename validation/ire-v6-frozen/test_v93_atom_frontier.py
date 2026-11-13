import unittest,copy
from dataclasses import dataclass
from v93_atom_frontier import scan_source,review_subclaims
@dataclass
class Cue:
 index:int;start_ms:int;end_ms:int;text:str
class T(unittest.TestCase):
 def setUp(self):
  self.cues=[Cue(i,i*100,i*100+50,'일상 일반 답변입니다') for i in range(1,81)]
  self.cues[9].text='ISA 계좌는 3년 조건이 있고 다만 상품 위험도 있습니다'
  self.cues[29].text='금리 5% 채권 10% 그리고 주식 배분 30%'
  self.cues[79].text='계좌 세금 변경을 정확히 보세요'
  self.reg={'W00001':[{'claim_id':'C00001','cue_indices':list(range(1,40))}], 'W00002':[{'claim_id':'C00002','cue_indices':list(range(41,81))}]}
 def check(self,cues=None,reg=None):return scan_source(self.cues if cues is None else cues,self.reg if reg is None else reg,expected_video_id='SYNTHETIC',expected_cues=80,expected_windows=2)
 def test_valid(self):
  x=self.check();self.assertEqual(x['source_cues_checked'],80);self.assertEqual(x['source_cues_without_draft_parent'],1);self.assertTrue(x['risk_case_count']>=3);self.assertFalse(x['p0_go'])
 def test_uncaptured_finance(self):
  self.cues[39].text='ISA 2026년 세액';x=self.check();self.assertIn('UNCAPTURED_FINANCE_CUE',x['risk_count_by_kind'])
 def test_private_queue_source_only(self):
  r=scan_source(self.cues,self.reg,expected_video_id='SYNTHETIC',expected_cues=80,expected_windows=2,include_private_queue=True)
  self.assertEqual(len(r['private_review_cases']),r['risk_case_count'])
  self.assertNotIn('private_review_cases',self.check())
  self.assertNotIn('text',r['private_review_cases'][0])
 def test_unsorted_cue(self):
  q=copy.deepcopy(self.cues);q[0].index=2
  with self.assertRaises(ValueError):self.check(cues=q)
 def test_bad_registry(self):
  r=copy.deepcopy(self.reg);r['W00001'][0]['cue_indices']=[100]
  with self.assertRaises(ValueError):self.check(reg=r)
 def test_cross_window(self):
  r=copy.deepcopy(self.reg);r['W00002'][0]['cue_indices'].append(2)
  with self.assertRaises(ValueError):self.check(reg=r)
 def test_subclaim_valid(self):
  x=review_subclaims({'cue_indices':[1,2]},[{'cue_indices':[1],'stance':'FACT_CANDIDATE','independent_fact_approved':False},{'cue_indices':[2],'stance':'EXCEPTION','independent_fact_approved':False}]);self.assertFalse(x['semantic_truth_certified'])
 def test_subclaim_uncovered(self):
  with self.assertRaises(ValueError):review_subclaims({'cue_indices':[1,2]},[{'cue_indices':[1],'stance':'FACT_CANDIDATE','independent_fact_approved':False}])
 def test_subclaim_fake_go(self):
  with self.assertRaises(ValueError):review_subclaims({'cue_indices':[1]},[{'cue_indices':[1],'stance':'FACT_CANDIDATE','independent_fact_approved':True}])
 def test_subclaim_outside_source(self):
  with self.assertRaises(ValueError):review_subclaims({'cue_indices':[1]},[{'cue_indices':[2],'stance':'QUESTION','independent_fact_approved':False}])
if __name__=='__main__':unittest.main()