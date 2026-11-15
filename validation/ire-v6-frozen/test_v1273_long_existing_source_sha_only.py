"""V127.3 SHA-only metadata regression; no private real SRT in public CI."""
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent
class ExistingLongSourceCapacityReceiptTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=json.loads((ROOT/"V127_3_EXISTING_LONG_VIDEO_1481CUE_SEGMENTATION_SHA_ONLY.json").read_text(encoding="utf-8"))
        cls.policy=json.loads((ROOT/"V125_ENGINE_FIRST_PORTFOLIO_DEFERRED_POLICY.json").read_text(encoding="utf-8"))
    def test_exact_cue_census_and_limits(self):
        r=self.r
        self.assertEqual(r["existing_original_cues"],1481)
        self.assertEqual(r["parent_source_windows"],25)
        self.assertEqual(r["bounded_source_children"],13)
        self.assertEqual(r["max_cues_per_child"],120)
        self.assertTrue(r["all_parent_cues_structurally_disposed"])
        self.assertTrue(r["all_child_manifest_original_source_sha_replayed"])
        self.assertTrue(r["full_video_single_turn_default_120_cue_blocked"])
        self.assertTrue(r["first_120_cue_child_private_chat_task_prepared_not_executed"])
    def test_provisional_source_not_owner_attested_or_semantically_complete(self):
        r=self.r
        self.assertFalse(r["owner_signed_independent_source_inventory"])
        self.assertFalse(r["chatgpt_semantic_review_of_13_children_performed"])
        self.assertFalse(r["cross_child_chat_final_census_complete"])
        self.assertFalse(r["full_video_parent_atomically_published"])
        self.assertFalse(r["new_video_research_conducted"])
        self.assertFalse(r["p0_go"])
        self.assertFalse(self.policy["completed_engine"])
    def test_original_hashes_are_public_metadata_only(self):
        r=self.r
        self.assertRegex(r["existing_original_sha256"],r"^[a-f0-9]{64}$")
        self.assertRegex(r["operator_derived_inventory_sha256"],r"^[a-f0-9]{64}$")
        self.assertFalse(r["portfolio_integration_used"])
        self.assertEqual(r["research_facts_formally_approved"],0)
if __name__=="__main__":
    unittest.main()
