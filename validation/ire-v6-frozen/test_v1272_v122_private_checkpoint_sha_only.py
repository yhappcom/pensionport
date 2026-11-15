"""V127.2 SHA-only structural receipt; public CI has no owner-private SRT."""
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent

class ExistingPrivateV122CheckpointMetadataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/"V127_2_EXISTING_V122_REAL_STAGING_CHECKPOINT_HOLD_SHA_ONLY.json").read_text(encoding="utf-8"))
        cls.policy=json.loads((ROOT/"V125_ENGINE_FIRST_PORTFOLIO_DEFERRED_POLICY.json").read_text(encoding="utf-8"))
    def test_original_staged_head_and_hold(self):
        d=self.data
        self.assertEqual(d["original_cue_count"],47)
        self.assertEqual(d["provisional_atom_count"],18)
        self.assertTrue(d["existing_isolated_v6_db_head_replayed"])
        self.assertEqual(d["checkpoint_status"],"CHILD_CHAT_CHECKPOINT_HOLD")
        self.assertEqual(d["checkpoint_held_child_scopes"],d["checkpoint_expected_child_scopes"])
        self.assertTrue(d["checkpoint_retry_idempotent"])
    def test_never_promote_private_staging_to_owner_completion(self):
        d=self.data
        for field in ("original_owner_inventory_independently_signed",
                      "owner_operational_production_db_head_verified",
                      "research_candidate_export_allowed","p0_go",
                      "new_video_research_executed"):
            self.assertFalse(d[field],field)
        self.assertEqual(d["existing_finance_open_docket"],12)
        self.assertEqual(d["real_finance_facts_approved"],0)
        self.assertFalse(self.policy["completed_engine"])
    def test_public_metadata_contains_only_pins_and_no_private_text(self):
        d=self.data
        for key in ("checkpoint_head_sha256","private_checkpoint_db_sha256",
                    "private_checkpoint_bundle_sha256","existing_original_source_sha256"):
            self.assertRegex(d[key],r"^[0-9a-f]{64}$")
        self.assertEqual(d["video_id"],"EYya0e4APBE")
        self.assertEqual(d["private_bundle_library_path"].split("/")[-1],
            "V1271_EXISTING_V122_47CUE_18ATOM_CHAT_HOLD_CHECKPOINT_PRIVATE.zip")
if __name__=="__main__":
    unittest.main()
