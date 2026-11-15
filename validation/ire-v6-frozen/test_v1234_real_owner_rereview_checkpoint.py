"""V123.4 public SHA-only checkpoint: do not falsely promote actual owner V122."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent

class RealOwnerRereviewCheckpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checkpoint = json.loads((ROOT / "V123_4_V122_OWNER_CHAT_REVIEW_SHA_ONLY.json").read_text(encoding="utf-8"))
        cls.v122 = json.loads((ROOT / "V122_PUBLIC_SHA_ONLY.json").read_text(encoding="utf-8"))
        cls.policy = json.loads((ROOT / "V123_CHATGPT_FINAL_REVIEW_POLICY.json").read_text(encoding="utf-8"))
        cls.protocol = (ROOT / "V6_CURRENT_CHATGPT_FINAL_APPROVAL_PROTOCOL.md").read_text(encoding="utf-8")

    def test_real_source_and_reference_counts_are_pinned_without_original_content(self):
        m = self.checkpoint
        self.assertEqual(m["source_sha256"], self.v122["source_sha256"])
        self.assertEqual(m["video_id"], self.v122["video_id"])
        self.assertEqual((m["original_cues_read_by_chat"], m["adjudicated_reference_claims_read"], m["finance_claims_re_reviewed"]), (47,17,12))
        self.assertTrue(m["archive_manifest_and_stage_replay_pass"])
        self.assertTrue(m["exact_original_srt_sha_recomputed"])
        self.assertEqual(len(m["private_new_chat_review_canonical_sha256"]),64)
        self.assertEqual(m["previous_private_B_reference_canonical_sha256"],self.v122["B_private_sha256"])
        self.assertEqual(m["previously_unmatched_reference_ids"],["R003","R017"])

    def test_no_original_body_or_private_review_written_publicly(self):
        m=self.checkpoint
        self.assertNotIn("original_srt_text", m)
        self.assertNotIn("private_review_notes", m)
        self.assertNotIn("official_http_body", m)
        self.assertFalse(m["private_original_http_body_bytes_replayed"])

    def test_no_false_store_or_chat_final_approval(self):
        m=self.checkpoint
        self.assertFalse(m["active_owner_v6_store_and_current_head_verified"])
        self.assertFalse(m["owner_signed_inventory_and_full_window_evidence_in_reviewed_archive"])
        self.assertFalse(m["current_v123_runtime_gate_executed_against_real_owner_store"])
        self.assertTrue(m["current_chat_source_first_scope_review_performed"])
        self.assertFalse(m["v123_formal_final_review_complete"])
        self.assertEqual(m["actual_gate_status"],"NOT_EXECUTED_ON_REAL_OWNER_STORE")
        self.assertEqual(m["inferred_gate_readiness_status"],"HOLD_MISSING_V6_HOST_BATCH_OR_STORE")
        self.assertEqual(m["next_gate_if_store_verified_and_finance_open_remains"],"CHAT_FINAL_HOLD_OPEN")

    def test_no_release_or_independent_quality_inflation(self):
        m=self.checkpoint
        self.assertEqual(m["financial_open_remaining"],12)
        self.assertEqual(m["new_formal_financial_fact_approvals"],0)
        self.assertFalse(m["new_research_candidate_export_allowed"])
        self.assertFalse(m["same_chat_external_gold"])
        self.assertFalse(m["p0_go"])
        self.assertIs(self.policy["engine_ci_cannot_approve_research"], True)
        self.assertIn("V123_4_V122_OWNER_CHAT_REVIEW_SHA_ONLY.json", self.protocol)

if __name__=="__main__":
    unittest.main()
