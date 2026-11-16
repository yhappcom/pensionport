"""No private SRT; strict source-aware synthetic negative controls. NOT semantic accuracy tests."""
import unittest
from v139_p0_qualification import score_atoms,parent_preflight,advisory_preflight
SHA='f'*64

class V139P0QualificationContractTests(unittest.TestCase):
 def test_01_no_gold_does_not_emit_fake_precision(self):
  a=score_atoms(gold=None,predicted=None,source_sha256=SHA)
  self.assertEqual(a['status'],'UNMEASURABLE_NO_COMPLETE_INDEPENDENT_GOLD')
  self.assertIsNone(a['tp']);self.assertIsNone(a['precision'])
 def test_02_blind_same_chat_not_external_gold(self):
  g={'complete':True,'external_independent':False,'covered_cue_count':720,'source_sha256':SHA,'unit_schema':'ADJUDICATED_ATOMIC_PROPOSITION_V1','unit_ids':['X'],'high_risk_unit_ids':[]}
  p={'source_sha256':SHA,'covered_cue_count':720,'unit_schema':g['unit_schema'],'unit_ids':['X']}
  self.assertFalse(score_atoms(gold=g,predicted=p,source_sha256=SHA)['p0_1_pass'])
 def test_03_real_scoring_arithmetic_only_on_adjudicated_synthetic(self):
  g={'complete':True,'external_independent':True,'covered_cue_count':720,'source_sha256':SHA,'unit_schema':'ADJUDICATED_ATOMIC_PROPOSITION_V1','unit_ids':['A','B','C'],'high_risk_unit_ids':['B']}
  p={'source_sha256':SHA,'covered_cue_count':720,'unit_schema':g['unit_schema'],'unit_ids':['A','B','D']}
  r=score_atoms(gold=g,predicted=p,source_sha256=SHA)
  self.assertEqual((r['tp'],r['fp'],r['fn']),(2,1,1))
  self.assertAlmostEqual(r['precision'],2/3);self.assertAlmostEqual(r['recall'],2/3)
  self.assertFalse(r['p0_1_pass'])
 def test_04_missing_high_risk_fails_even_with_adequate_other_metrics(self):
  g={'complete':True,'external_independent':True,'covered_cue_count':720,'source_sha256':SHA,'unit_schema':'ADJUDICATED_ATOMIC_PROPOSITION_V1','unit_ids':[f'A{i}' for i in range(100)],'high_risk_unit_ids':['A99']}
  p={'source_sha256':SHA,'covered_cue_count':720,'unit_schema':g['unit_schema'],'unit_ids':[f'A{i}' for i in range(99)]}
  r=score_atoms(gold=g,predicted=p,source_sha256=SHA)
  self.assertEqual(r['high_risk_fn'],1);self.assertFalse(r['p0_1_pass'])
 def test_05_partial_source_coverage_blocks_metric(self):
  g={'complete':True,'external_independent':True,'covered_cue_count':719,'source_sha256':SHA,'unit_schema':'ADJUDICATED_ATOMIC_PROPOSITION_V1','unit_ids':['X'],'high_risk_unit_ids':[]}
  p={'source_sha256':SHA,'covered_cue_count':719,'unit_schema':g['unit_schema'],'unit_ids':['X']}
  self.assertIsNone(score_atoms(gold=g,predicted=p,source_sha256=SHA)['recall'])
 def test_06_real_thirteen_cue_queue_cannot_become_v123_pass(self):
  children=[{'segment_id':f'B{i:04d}','first_cue':(i-1)*120+1,'last_cue':min(i*120,1481),'source_sha256':SHA,'v123_status':'HOLD','unresolved_cases':1,'v123_receipt_sha256':None} for i in range(1,14)]
  r=parent_preflight(children,actual_source_sha256=SHA)
  self.assertEqual(r['status'],'HOLD')
  self.assertFalse(r['publication_authorized']);self.assertEqual(r['formal_knowledge_published'],0)
  self.assertIn('CHILD_13_NOT_V123_PASS',r['issues'])
 def test_07_child_13_must_be_last_41_cues(self):
  children=[{'segment_id':f'B{i:04d}','first_cue':(i-1)*120+1,'last_cue':min(i*120,1481),'source_sha256':SHA,'v123_status':'HOLD','unresolved_cases':0,'v123_receipt_sha256':None} for i in range(1,14)]
  children[-1]['last_cue']=1560
  self.assertIn('CHILD_SCOPE_13_INVALID',parent_preflight(children,actual_source_sha256=SHA)['issues'])
 def test_08_even_13_synthetic_pass_flags_not_a_real_publish(self):
  children=[{'segment_id':f'B{i:04d}','first_cue':(i-1)*120+1,'last_cue':min(i*120,1481),'source_sha256':SHA,'v123_status':'PASS','unresolved_cases':0,'v123_receipt_sha256':SHA} for i in range(1,14)]
  r=parent_preflight(children,actual_source_sha256=SHA,parent_review_receipt={'chat_validated_whole_parent':True},owner_db_attested=True)
  self.assertTrue(r['diagnostic_ready'])
  self.assertFalse(r['publication_authorized']);self.assertEqual(r['formal_knowledge_published'],0)
 def test_09_official_law_without_original_bytes_keeps_advisory_hold(self):
  r=advisory_preflight(source_final_passed=True,knowledge_head_attested=True,original_issuer_bytes_recalculated=False,effective_date_checked=True,applicability_checked=True,actual_v5_current_law_answer_executed=True,investor_specific_facts_verified=True)
  self.assertIn('OFFICIAL_ORIGINAL_BODY_NOT_REPLAYED',r['missing_gates'])
  self.assertFalse(r['real_personal_advice_approved'])
 def test_10_all_synthetic_flags_alone_cannot_activate_personal_orders(self):
  r=advisory_preflight(**{k:True for k in ('source_final_passed','knowledge_head_attested','original_issuer_bytes_recalculated','effective_date_checked','applicability_checked','actual_v5_current_law_answer_executed','investor_specific_facts_verified')})
  self.assertFalse(r['personal_order_enabled']);self.assertFalse(r['real_personal_advice_approved'])
if __name__=='__main__':unittest.main(verbosity=2)
