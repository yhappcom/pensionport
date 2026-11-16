"""V155 public negative tests: owner-private original never enters GitHub CI."""
from __future__ import annotations
import copy,json,unittest
from pathlib import Path

from v155_real_owner_cue_semantic_release_gate import (
  V155NoFalseRelease,audit_v155_public_hold,audit_v155_actual_private_zip
)

R=Path(__file__).with_name("V155_OWNER_SOURCE_75_REAL_REPLAY_SHA_ONLY.json")

class V155ResearchCustodyTests(unittest.TestCase):
  def setUp(self):
    self.p=json.loads(R.read_text(encoding="utf8"))

  def mutate(self,key,value,expected):
    x=copy.deepcopy(self.p);x[key]=value
    with self.assertRaisesRegex(V155NoFalseRelease,expected):
      audit_v155_public_hold(x)

  def test_01_actual_public_custody_no_false_go(self):
    out=audit_v155_public_hold(self.p)
    self.assertEqual(out["provisional_claims"],284)
    self.assertEqual(out["original_108_remaining_open"],13)
    self.assertEqual(out["v123_final_pass"],0)
    self.assertFalse(out["p0e_go"])

  def test_02_mismatch_original_srt_rejected(self):
    self.mutate("original_source_sha256","0"*64,"ORIGINAL_SOURCE")

  def test_03_75_residual_cannot_suddenly_be_zero(self):
    self.mutate("v155_still_unresolved_from_75",0,"COUNT")

  def test_04_no_misreport_108_source_cue_partition(self):
    self.mutate("original_108_queue_now_claim_linked",108,"COUNT")

  def test_05_false_284_atom_count_is_blocked(self):
    self.mutate("revised_provisional_atoms",278,"COUNT")

  def test_06_no_fake_v123_pass(self):
    self.mutate("native_v123_approved_scopes",1,"COUNT")

  def test_07_no_fake_parent_publication(self):
    self.mutate("actual_v128_parent_publications",1,"COUNT")

  def test_08_cannot_certify_95_98_from_structural_host(self):
    self.mutate("precision95_recall98_proven",True,"FALSE_RELEASE")

  def test_09_cannot_certify_high_risk_fn_zero(self):
    self.mutate("high_risk_fn_zero_proven",True,"FALSE_RELEASE")

  def test_10_cannot_claim_personal_eligibility(self):
    self.mutate("individual_2026_eligibility_verified",True,"FALSE_RELEASE")

  def test_11_cannot_claim_independent_owner_attestation(self):
    self.mutate("owner_inventory_externally_authenticated",True,"FALSE_RELEASE")

  def test_12_private_packet_hash_required(self):
    self.mutate("full_private_packet_sha256","invalid","MISSING_PRIVATE_SHA")

  def test_13_exact_13_cue_hold_list_required(self):
    self.mutate("unresolved_source_cue_indices",[307,390],"13_CUE_INDEX")

  def test_14_b0001_14_reviews_do_not_equal_v123_pass(self):
    self.mutate("b0001_formal_v123_pass",True,"FALSE_RELEASE")

  def test_15_missing_or_fabricated_owner_packet_rejected(self):
    with self.assertRaisesRegex(V155NoFalseRelease,"PRIVATE_ZIP_HASH"):
      audit_v155_actual_private_zip(self.p,b"synthetic non-owner packet")

if __name__=="__main__":
  unittest.main()
