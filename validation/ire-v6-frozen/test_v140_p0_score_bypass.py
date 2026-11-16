"""Regression: fabricated 1-atom 'independent 720-cue gold' must not grant P0."""
import unittest
from v139_p0_qualification import score_atoms

class V140SelfAttestedQualityBypass(unittest.TestCase):
 def test_01_one_fake_gold_unit_with_720_count_cannot_pass(self):
  g={'complete':True,'external_independent':True,'covered_cue_count':720,
     'source_sha256':'f'*64,'unit_schema':'ADJUDICATED_ATOMIC_PROPOSITION_V1',
     'unit_ids':['ONLY_ONE_ITEM'],'high_risk_unit_ids':[]}
  p={'source_sha256':'f'*64,'covered_cue_count':720,
     'unit_schema':g['unit_schema'],'unit_ids':['ONLY_ONE_ITEM']}
  r=score_atoms(gold=g,predicted=p,source_sha256='f'*64)
  self.assertEqual((r['precision'],r['recall']),(1,1))
  self.assertTrue(r['numeric_targets_met_on_declared_units_only'])
  self.assertFalse(r['genuine_720_source_gold_authenticated'])
  self.assertFalse(r['p0_1_pass'])
 def test_02_ordinary_3unit_arithmetic_preserved_but_not_approved(self):
  g={'complete':True,'external_independent':True,'covered_cue_count':720,
     'source_sha256':'f'*64,'unit_schema':'ADJUDICATED_ATOMIC_PROPOSITION_V1',
     'unit_ids':['A','B','C'],'high_risk_unit_ids':['B']}
  p={'source_sha256':'f'*64,'covered_cue_count':720,
     'unit_schema':g['unit_schema'],'unit_ids':['A','B','D']}
  r=score_atoms(gold=g,predicted=p,source_sha256='f'*64)
  self.assertEqual((r['tp'],r['fp'],r['fn']),(2,1,1))
  self.assertFalse(r['p0_1_pass'])
 def test_03_external_false_is_unmeasurable(self):
  g={'complete':True,'external_independent':False,'covered_cue_count':720,
     'source_sha256':'f'*64,'unit_schema':'ADJUDICATED_ATOMIC_PROPOSITION_V1',
     'unit_ids':['A'],'high_risk_unit_ids':[]}
  p={'source_sha256':'f'*64,'covered_cue_count':720,
     'unit_schema':g['unit_schema'],'unit_ids':['A']}
  r=score_atoms(gold=g,predicted=p,source_sha256='f'*64)
  self.assertIsNone(r['precision']);self.assertFalse(r['p0_1_pass'])
if __name__=='__main__':unittest.main(verbosity=2)
