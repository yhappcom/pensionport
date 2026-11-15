"""V123.6 only validates safe metadata; cannot replay private original in public CI."""
import json
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent

class NativeV122PrivateStagingMetadata(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=json.loads((ROOT/"V123_6_V122_REAL_NATIVE_V6_SHA_ONLY_RESULT.json").read_text(encoding="utf-8"))
        cls.v122=json.loads((ROOT/"V122_PUBLIC_SHA_ONLY.json").read_text(encoding="utf-8"))
        cls.pin=json.loads((ROOT/"V123_6_OPERATOR_SOURCE_ANCHOR_SHA_ONLY.json").read_text(encoding="utf-8"))
        cls.policy=json.loads((ROOT/"V123_CHATGPT_FINAL_REVIEW_POLICY.json").read_text(encoding="utf-8"))
    def test_actual_source_and_prior_pin_match(self):
        m=self.m
        self.assertEqual(m["source_sha256"],self.v122["source_sha256"])
        self.assertEqual(m["operator_inventory_sha256"],self.pin["provisional_operator_inventory_bytes_sha256"])
        self.assertEqual(m["source_cue_count"],47)
        self.assertEqual(m["atomic_candidates"],17)
        self.assertEqual(m["window_count"],1)
    def test_staging_is_not_owner_production_or_release(self):
        m=self.m
        self.assertTrue(m["host_batch_called_on_original_v6"])
        self.assertTrue(m["host_batch_atomic_committed"])
        self.assertEqual(m["model_windows_recorded"],1)
        self.assertEqual(m["proof_windows_recorded"],1)
        self.assertEqual(m["stage_store_sequence"],6)
        self.assertTrue(m["same_original_inputs_idempotent_replay"])
        self.assertTrue(m["current_db_head_readback_matches_receipt"])
        self.assertEqual(m["stage_store_head_sha256"],m["host_receipt_event_sha256"])
        self.assertEqual(m["run_target"],"ISOLATED_PRIVATE_STAGING_DB_NOT_EXISTING_OWNER_OPERATIONAL_DB")
        self.assertIs(m["operator_inventory_is_user_signed"],False)
        self.assertIs(self.policy["V122_actual_v6_owner_host_batch_complete"],False)
    def test_chat_final_real_staging_holds_no_export(self):
        m=self.m
        self.assertTrue(m["chat_final_runtime_executed"])
        self.assertEqual(m["chat_final_status"],"CHAT_FINAL_HOLD_OPEN")
        self.assertEqual(m["chat_final_atoms_open"],17)
        self.assertEqual(m["chat_final_finance_open_count"],17)
        self.assertEqual(m["legacy_finance_docket_open_count"],12)
        self.assertTrue(m["final_release_wrapper_blocks"])
        self.assertTrue(m["readonly_preview_wrapper_blocks"])
        for key in ("chat_final_research_candidate_export_allowed","official_research_pass",
                    "master116_p4_v5_modified","p0_go"):
            self.assertIs(m[key],False)
        self.assertEqual(m["formal_financial_fact_approved"],0)
    def test_immutable_private_evidence_only_hashes_public(self):
        m=self.m
        for key in ("private_staging_archive_sha256","snapshot_sqlite_sha256",
                    "chat_review_private_sha256","host_receipt_bundle_sha256"):
            self.assertEqual(len(m[key]),64)
            int(m[key],16)
        self.assertEqual(m["backup_sqlite_integrity_check"],"ok")
        self.assertTrue(m["official_primary_http_bytes_missing"])
        self.assertEqual(m["unmapped_condition_cue_index"],32)
        self.assertEqual(m["numeric_review_cue_index"],14)
        self.assertEqual(m["source_first_frontier_review_cases"],31)
        self.assertNotIn("private_review_notes",m)
        self.assertNotIn("original_srt_text",m)
        self.assertNotIn("original_http_response_bytes",m)

if __name__=="__main__":
    unittest.main()
