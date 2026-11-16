"""Public no-owner-source regression for V146 semantic status self-attestation."""
from __future__ import annotations
import copy,json,unittest
from pathlib import Path
from ire.v6.errors import InvalidInput
from v146_meaning_release_safety_gate import assess_v146_public_receipt


class TestV146SourceSemanticReleaseSafety(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.original=json.loads((Path(__file__).parent/'V146_SEMANTIC_REVIEW_SHA_ONLY.json').read_text(encoding='utf-8'))

 def test_01_real_sha_only_receipt_is_partial_and_hold(self):
  result=assess_v146_public_receipt(self.original)
  self.assertEqual(result['actual_targeted_source_meant_claims'],72)
  self.assertEqual(result['new_knowledge_entries'],0)
  self.assertFalse(result['p0_go'])

 def test_02_spoofed_v123_13_of_13_pass_rejected(self):
  r=copy.deepcopy(self.original);r['v123_formally_passed_scopes']=13
  with self.assertRaises(InvalidInput):assess_v146_public_receipt(r)

 def test_03_spoofed_final_knowledge_publication_rejected(self):
  for name,value in [('v128_durable_knowledge_items',1),('all_video_v123_pass',True),('p0_go',True)]:
   r=copy.deepcopy(self.original);r[name]=value
   with self.subTest(name=name),self.assertRaises(InvalidInput):assess_v146_public_receipt(r)

 def test_04_false_independent_gold_or_finance_issuer_checked_rejected(self):
  for name,value in [('independent_semantic_precision_recall_measured',True),('official_issuer_original_body_bytes_cryptographically_verified',1),('formal_financial_advice_approved',True)]:
   r=copy.deepcopy(self.original);r[name]=value
   with self.subTest(name=name),self.assertRaises(InvalidInput):assess_v146_public_receipt(r)

 def test_05_invalid_original_cue_or_claim_count_rejected(self):
  for name,value in [('original_cues',1480),('baseline_atoms',275),('baseline_v6_host_scopes',12),('speaker_unknown_baseline_claims',0)]:
   r=copy.deepcopy(self.original);r[name]=value
   with self.subTest(name=name),self.assertRaises(InvalidInput):assess_v146_public_receipt(r)

 def test_06_false_72_case_census_rejected(self):
  r=copy.deepcopy(self.original);r['targeted_issue_categories']['HYPOTHETICAL_PROBABILITY']=200
  with self.assertRaises(InvalidInput):assess_v146_public_receipt(r)

 def test_07_wrong_private_digest_rejected(self):
  r=copy.deepcopy(self.original);r['private_rows_sha256']='0'*12
  with self.assertRaises(InvalidInput):assess_v146_public_receipt(r)

 def test_08_cannot_auto_clear_272_formal_open_claims(self):
  r=copy.deepcopy(self.original);r['formally_open_v123_baseline_claims']=202
  with self.assertRaises(InvalidInput):assess_v146_public_receipt(r)

if __name__=='__main__':unittest.main(verbosity=2)
