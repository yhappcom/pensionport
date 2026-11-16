"""V123.7 public SHA-only test, not a replay of owner-private research."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent
class V1237NumericTwoSemanticAtomNoFalseGo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=json.loads((ROOT/"V123_7_V122_REAL_47CUE_18ATOM_CHAT_HOLD_SHA_ONLY.json").read_text(encoding="utf-8"))
        cls.old=json.loads((ROOT/"V123_6_1_V122_CUE32_OFFICIAL_RAW2_SHA_ONLY.json").read_text(encoding="utf-8"))
        cls.v122=json.loads((ROOT/"V122_PUBLIC_SHA_ONLY.json").read_text(encoding="utf-8"))
        cls.current_protocol=(ROOT/"V6_CURRENT_CHATGPT_FINAL_APPROVAL_PROTOCOL.md").read_text(encoding="utf-8")
    def test_real_original_bound_but_not_truth_proved(self):
        m=self.p
        self.assertEqual(m["source_sha256"],self.v122["source_sha256"])
        self.assertEqual(m["source_cues"],47)
        self.assertEqual(m["source_cues_structurally_dispositioned"],47)
        self.assertEqual((m["structural_unresolved_cues"],m["structural_suspicious_no_atom_cues"]),(0,0))
        self.assertTrue(m["review_does_not_prove_semantic_exhaustiveness"])
        self.assertTrue(m["previously_fixed_cue32_condition_mapping_retained"])
    def test_number_context_two_atom_split_not_five_is_pinned(self):
        m=self.p
        self.assertEqual(m["numeric_context_cues"],[14,15,16])
        self.assertEqual(m["previous_atomic_candidates"],17)
        self.assertEqual(m["revised_atomic_candidates"],18)
        self.assertEqual(m["isa_range_numeric_tokens_at_cue14"],2)
        self.assertEqual(m["illustrative_pension_year_numeric_tokens_at_cue15"],3)
        self.assertTrue(m["case14_grouped_into_two_semantic_atoms_not_five"])
        self.assertNotEqual(m["revised_isolated_staging_head_sha256"],self.old["revised_native_staging_head_sha256"])
    def test_staging_acid_and_final_chat_open(self):
        m=self.p
        self.assertTrue(m["native_real_original_v6_staging_host_batch_committed"])
        self.assertTrue(m["idempotent_original_host_batch_replay"])
        self.assertEqual((m["staging_scope_sequence"],m["staging_model_windows_recorded"],m["staging_current_structural_proofs"]),(6,1,1))
        self.assertEqual(m["backup_sqlite_integrity_check"],"ok")
        self.assertTrue(m["isolated_staging_db_not_existing_owner_production"])
        self.assertFalse(m["inventory_independently_owner_signed"])
        self.assertFalse(m["current_production_owner_store_verified"])
        self.assertTrue(m["chat_final_gate_live_staging_executed"])
        self.assertEqual(m["chat_final_status"],"CHAT_FINAL_HOLD_OPEN")
        self.assertEqual((m["chat_final_cues_reviewed"],m["chat_final_atoms_open"],m["chat_final_finance_open"]),(47,18,18))
    def test_twelve_formal_open_never_cleared_by_web_text_or_archive(self):
        m=self.p
        self.assertEqual(m["formal_finance_docket_open_remaining"],12)
        self.assertEqual(m["private_finance_docket_web_readable_authority_scoped_cases"],11)
        self.assertEqual(m["archived_government_original_response_bytes_reverified"],2)
        self.assertEqual(m["latest_current_live_government_response_bytes_retrieved"],0)
        self.assertFalse(m["official_complete_per_claim_http_bytes_verified"])
        self.assertEqual(m["new_readonly_candidate_exports"],0)
        self.assertEqual(m["financial_facts_formally_approved"],0)
        self.assertFalse(m["master116_p4_v5_modified"])
        self.assertFalse(m["p0_go"])
    def test_receipt_is_sha_only_and_private_docket_has_no_public_payload(self):
        m=self.p
        self.assertTrue(m["private_bundle_crc_and_member_sha_verified"])
        for key in ("source_sha256","atom_exchange_sha256","operator_inventory_sha256",
                    "revised_isolated_staging_head_sha256","private_bundle_sha256","private_finance_docket_sha256"):
            self.assertEqual(len(m[key]),64)
            int(m[key],16)
        for forbidden in ("original_srt_text","private_finance_claim_text","private_review_notes","original_http_body_bytes"):
            self.assertNotIn(forbidden,m)
        self.assertIn("V123.7",self.current_protocol)

if __name__=="__main__":
    unittest.main()
