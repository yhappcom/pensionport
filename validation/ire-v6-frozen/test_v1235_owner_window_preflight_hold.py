"""V123.5 public metadata-only V122 source-window preflight, never a private replay."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent

class OwnerWindowPreflightHold(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = json.loads((ROOT / "V123_5_V122_PRIVATE_V6_SOURCE_PLAN_PREFLIGHT_SHA_ONLY.json").read_text(encoding="utf-8"))
        cls.v122 = json.loads((ROOT / "V122_PUBLIC_SHA_ONLY.json").read_text(encoding="utf-8"))
        cls.v1234 = json.loads((ROOT / "V123_4_V122_OWNER_CHAT_REVIEW_SHA_ONLY.json").read_text(encoding="utf-8"))
        cls.policy = json.loads((ROOT / "V123_CHATGPT_FINAL_REVIEW_POLICY.json").read_text(encoding="utf-8"))

    def test_real_source_and_one_window_metadata_are_consistent(self):
        m = self.m
        self.assertEqual(m["original_srt_sha256"], self.v122["source_sha256"])
        self.assertEqual(m["archive_sha256"], self.v1234["private_archive_zip_sha256"])
        self.assertEqual(m["cue_count"], 47)
        self.assertEqual((m["window_count"],len(m["windows"])),(1,1))
        self.assertEqual((m["windows"][0]["window_id"],m["windows"][0]["first_cue"],m["windows"][0]["last_cue"]),("W00001",1,47))
        self.assertEqual(m["source_plan_schema"],"IRE_V6_SOURCE_PLAN_V1")
        self.assertEqual(m["scope_mode"],"FULL_VIDEO")
        for key in ("private_v6_source_plan_raw_sha256","private_v6_source_plan_canonical_sha256"):
            self.assertEqual(len(m[key]), 64)
            int(m[key],16)
        self.assertEqual(len(m["windows"][0]["source_text_sha256"]),64)
        int(m["windows"][0]["source_text_sha256"],16)
        self.assertTrue(m["source_plan_window_cue_coverage_pass"])
        self.assertTrue(m["source_plan_window_text_sha256_recomputed_pass"])

    def test_no_host_commit_or_approval_synthesized(self):
        m = self.m
        for key in ("v122_owner_inventory_bytes_and_pinned_inventory_sha_in_archive",
                    "v122_v6_window_models_and_reviews_for_real_host_commit_present",
                    "current_owner_v6_store_snapshot_and_latest_head_verified",
                    "current_v6_host_batch_committed","official_primary_http_response_bytes_replayed",
                    "v123_live_owner_final_gate_executed","new_research_candidate_export_allowed","p0_go"):
            self.assertIs(m[key],False,key)
        self.assertEqual(m["status"],"HOLD_MISSING_V6_HOST_BATCH_OR_STORE")
        self.assertEqual(m["financial_open_remaining"],12)
        self.assertIs(self.policy["V122_actual_v6_owner_host_batch_complete"],False)
        self.assertIs(self.v1234["v123_formal_final_review_complete"],False)

    def test_public_receipt_never_conveys_private_material(self):
        m = self.m
        self.assertTrue(m["ci_is_public_metadata_only_not_private_replay"])
        self.assertNotIn("original_srt_text",m)
        self.assertNotIn("private_review_notes",m)
        self.assertNotIn("official_http_body",m)
        self.assertTrue(m["original_zip_crc_and_member_digest_pass"])
        self.assertTrue(m["private_v114_five_stage_replay_pass"])

    def test_ci_attestation_is_previous_commit_only(self):
        m = self.m
        self.assertEqual(m["prior_ci_commit_sha"],"4eb11301af21489188c80361b740f903914c5a9f")
        self.assertEqual(m["prior_v6_ci_run_id"],43676422360)
        self.assertEqual(m["prior_cleanroom_ci_run_id"],43676426222)

if __name__ == "__main__":
    unittest.main()
