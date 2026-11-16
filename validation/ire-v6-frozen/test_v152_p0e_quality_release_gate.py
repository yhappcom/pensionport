"""V152 public synthetic negative controls. Private SRT never used by CI."""
import copy, json, unittest
from pathlib import Path

from v152_p0e_quality_release_gate import (
    audit_sha_only_source_repartition, assess_personal_eligibility_gate,
    gate_approved_knowledge_based_answer, V152QualityHold,
)

ROOT = Path(__file__).parent


class V152P0EQualityTest(unittest.TestCase):
    def setUp(self):
        self.receipt = json.loads((ROOT/"V152_SOURCE_ONLY_SHA_RECEIPT.json").read_text(encoding="utf8"))
        self.spec = json.loads((ROOT/"V152_PERSONAL_ELIGIBILITY_GATE_HOLD.json").read_text(encoding="utf8"))

    def test_01_actual_source_receipt_only_not_gold(self):
        out = audit_sha_only_source_repartition(self.receipt)
        self.assertEqual(out["sha_only_source_precheck_count"], 13)
        self.assertEqual(out["candidate_atom_count"], 276)
        self.assertEqual(out["V123_chat_scopes_final_passed"], 0)
        self.assertFalse(out["P0_E_GO"])

    def test_02_wrong_source_hash_fails(self):
        r = copy.deepcopy(self.receipt)
        r["source_sha256"] = "0"*64
        with self.assertRaisesRegex(V152QualityHold,"WRONG_OWNER_SOURCE"):
            audit_sha_only_source_repartition(r)

    def test_03_false_host_issued_claim_fails(self):
        r = copy.deepcopy(self.receipt)
        r["new_native_v6_host_event_count"] = 13
        with self.assertRaisesRegex(V152QualityHold,"COUNT_NEW_NATIVE_V6_HOST_EVENT"):
            audit_sha_only_source_repartition(r)

    def test_04_false_gold_high_risk_zero_fails(self):
        r = copy.deepcopy(self.receipt)
        r["high_risk_fn_zero_certified"] = True
        with self.assertRaisesRegex(V152QualityHold,"FALSE_COMPLETION"):
            audit_sha_only_source_repartition(r)

    def test_05_seam_1439_moved_back_fails(self):
        r = copy.deepcopy(self.receipt)
        r["scope_13"]["first_cue"] = 1441
        with self.assertRaisesRegex(V152QualityHold,"SEAM_BOUNDARY"):
            audit_sha_only_source_repartition(r)

    def test_06_wrong_atom_count_fails(self):
        r = copy.deepcopy(self.receipt)
        r["total_provisional_atoms"] = 274
        with self.assertRaisesRegex(V152QualityHold,"COUNT_TOTAL_PROVISIONAL_ATOMS"):
            audit_sha_only_source_repartition(r)

    def test_07_source_success_does_not_enable_advice(self):
        out = gate_approved_knowledge_based_answer(
            v128_parent_publication_count=0, v123_chat_approved_scopes=0,
            live_official_original_evidence_count=2,
            personal_case_complete=False)
        self.assertFalse(out["approved_knowledge_answer_issued"])

    def test_08_fake_completion_flags_never_bypass_replay(self):
        out = gate_approved_knowledge_based_answer(
            v128_parent_publication_count=1,v123_chat_approved_scopes=13,
            live_official_original_evidence_count=2,personal_case_complete=True)
        self.assertEqual(out["status"],"HOLD_REQUIRE_ACTUAL_PRIVATE_V128_SQLITE_PUBLICATION_REPLAY")

    def test_09_no_private_user_tax_data_stays_hold(self):
        out = assess_personal_eligibility_gate(self.spec,{},"ISA")
        self.assertTrue(out["missing_required_fields"])
        self.assertFalse(out["automatic_individual_approval"])

    def test_10_synthetic_complete_case_is_not_suitability_pass(self):
        case={k:"synthetic example" for k in self.spec["pension_questions_required"]}
        out=assess_personal_eligibility_gate(
            self.spec,case,"PENSION",approved_parent_verified=True,
            official_original_bytes_verified=True)
        self.assertEqual(out["status"],"REQUIRES_CHATGPT_FINAL_ELIGIBILITY_AND_SUITABILITY_REVIEW")
        self.assertFalse(out["trades_or_tax_returns_authorized"])

    def test_11_missing_official_original_stays_hold(self):
        case={k:"synthetic example" for k in self.spec["isa_questions_required"]}
        out=assess_personal_eligibility_gate(self.spec,case,"ISA",approved_parent_verified=True)
        self.assertEqual(out["status"],"HOLD_CURRENT_OFFICIAL_ORIGINAL_NOT_REVALIDATED")

    def test_12_public_manifest_cannot_claim_personal_approval(self):
        s=copy.deepcopy(self.spec);s["personal_recommendation_authorized"]=True
        with self.assertRaisesRegex(V152QualityHold,"FALSE_PERSONAL_APPROVAL"):
            assess_personal_eligibility_gate(s,{},"ISA")

if __name__=="__main__":
    unittest.main()
