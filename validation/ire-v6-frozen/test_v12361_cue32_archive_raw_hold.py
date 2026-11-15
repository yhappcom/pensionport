"""Public SHA-only regression: actual original raw body pins + conservative V123.6.1 hold."""
import hashlib
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent
class NativeScopeRiskAndOfficialRawRecheck(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=json.loads((ROOT/"V123_6_1_V122_CUE32_OFFICIAL_RAW2_SHA_ONLY.json").read_text(encoding="utf-8"))
        cls.old=json.loads((ROOT/"V123_6_V122_REAL_NATIVE_V6_SHA_ONLY_RESULT.json").read_text(encoding="utf-8"))
        cls.owner=json.loads((ROOT/"V122_PUBLIC_SHA_ONLY.json").read_text(encoding="utf-8"))
        cls.capture=json.loads((ROOT/"public_official_raw_20261108/capture_manifest.json").read_text(encoding="utf-8"))
    def test_source_and_new_actual_staging_record_kept_separate(self):
        m=self.m
        self.assertEqual(m["original_srt_sha256"],self.owner["source_sha256"])
        self.assertEqual(m["prior_native_staging_head_sha256"],self.old["stage_store_head_sha256"])
        self.assertNotEqual(m["revised_native_staging_head_sha256"],self.old["stage_store_head_sha256"])
        self.assertTrue(m["cue_32_condition_mapping_corrected"])
        self.assertEqual(m["source_first_frontier_review_cases_before"],31)
        self.assertEqual(m["source_first_frontier_review_cases_after"],30)
        self.assertTrue(m["remaining_cue_14_multi_number_semantic_review_open"])
        self.assertTrue(m["second_isolated_real_v6_host_batch_committed"])
        self.assertEqual(m["second_isolated_native_v123_gate_status"],"CHAT_FINAL_HOLD_OPEN")
    def test_actual_government_body_bytes_rehashed_in_ci(self):
        m=self.m
        data={x["source_id"]:x for x in self.capture["records"]}
        self.assertEqual(len(m["original_government_captures"]),2)
        for item in m["original_government_captures"]:
            orig=data[item["source_id"]]
            b=(ROOT/"public_official_raw_20261108"/orig["artifact_name"]).read_bytes()
            self.assertEqual(hashlib.sha256(b).hexdigest(),item["body_sha256"])
            self.assertEqual(len(b),item["body_bytes"])
            self.assertEqual(orig["captured_body_sha256"],item["body_sha256"])
            self.assertFalse(item["legal_scope_final_adjudicated"])
            self.assertFalse(item["finance_claim_approved"])
            self.assertEqual(orig["visible_effective_date"],item["effective_as_of"])
    def test_no_false_research_release_from_partial_archive(self):
        m=self.m
        self.assertEqual(m["legacy_finance_docket_open"],12)
        self.assertEqual(m["v123_gate_financial_atoms_open"],17)
        self.assertFalse(m["all_twelve_finance_docket_cases_cleared"])
        self.assertFalse(m["current_live_source_refresh_verified"])
        self.assertFalse(m["independently_owner_signed_inventory_supplied"])
        self.assertFalse(m["production_owner_db_head_verified"])
        self.assertEqual(m["new_knowledge_candidates_released"],0)
        self.assertEqual(m["formal_financial_fact_approvals"],0)
        self.assertFalse(m["p0_go"])
        self.assertFalse(m["master116_p4_v5_modified"])
if __name__=="__main__":
    unittest.main()
