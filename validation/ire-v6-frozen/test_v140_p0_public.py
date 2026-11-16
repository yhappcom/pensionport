"""Public source-free negative controls for V140. Not actual ChatGPT semantics."""
import unittest,json
from pathlib import Path
from v140_p0_source_gate import audit_public_receipt,SourceCustodyError
ROOT=Path(__file__).parent
class PublicV140EvidenceHold(unittest.TestCase):
 def setUp(self):
  self.r=json.loads((ROOT/'V140_SOURCE_FIRST_RISK_SHA_ONLY.json').read_text('utf-8'))
 def test_01_real_source_hash_only_not_replayed(self):
  x=audit_public_receipt(self.r)
  self.assertFalse(x['private_original_replay_by_public_ci'])
  self.assertFalse(x['p0_go'])
 def test_02_cannot_fake_720_gold(self):
  self.r['full_720_independent_gold']=True
  with self.assertRaisesRegex(SourceCustodyError,'PUBLIC_FALSE_CERTIFICATION'):audit_public_receipt(self.r)
 def test_03_cannot_fake_high_risk_zero(self):
  self.r['high_risk_fn_zero_proven']=True
  with self.assertRaisesRegex(SourceCustodyError,'PUBLIC_FALSE_CERTIFICATION'):audit_public_receipt(self.r)
 def test_04_cannot_fake_761_exhaustiveness(self):
  self.r['all_remaining_761_cues_exhaustively_atom_dispositioned']=True
  with self.assertRaisesRegex(SourceCustodyError,'PUBLIC_FALSE_CERTIFICATION'):audit_public_receipt(self.r)
 def test_05_cannot_fake_all_13_v123_pass(self):
  self.r['full_13_v123_final_passed']=13
  with self.assertRaisesRegex(SourceCustodyError,'PUBLIC_FALSE_PUBLICATION'):audit_public_receipt(self.r)
 def test_06_cannot_fake_knowledge_published(self):
  self.r['knowledge_export_allowed']=True
  with self.assertRaisesRegex(SourceCustodyError,'PUBLIC_FALSE_CERTIFICATION'):audit_public_receipt(self.r)
 def test_07_cannot_fake_current_law_issuer_bytes(self):
  self.r['p0_3_issuer_original_bytes_authenticated']=True
  with self.assertRaisesRegex(SourceCustodyError,'PUBLIC_FALSE_CERTIFICATION'):audit_public_receipt(self.r)
 def test_08_cannot_fake_advisory_end_to_end(self):
  self.r['p0_3_real_approved_knowledge_advisory_e2e']=True
  with self.assertRaisesRegex(SourceCustodyError,'PUBLIC_FALSE_CERTIFICATION'):audit_public_receipt(self.r)
 def test_09_bad_source_id_rejected(self):
  self.r['source_sha256']='0'*64
  with self.assertRaisesRegex(SourceCustodyError,'PUBLIC_RECEIPT_INVALID'):audit_public_receipt(self.r)
 def test_10_private_packet_sha_must_be_pinned(self):
  self.r['private_source_review_sha256']='g'*64
  with self.assertRaisesRegex(SourceCustodyError,'PUBLIC_PRIVATE_PACKET_SHA_NOT_PINNED'):audit_public_receipt(self.r)
if __name__=='__main__': unittest.main(verbosity=2)
