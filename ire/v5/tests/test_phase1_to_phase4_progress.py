"""P1/P3/P4 progress must not be confused with a signed research close."""
import copy
from pathlib import Path
import tempfile
import unittest

from ire.v5 import phase1_to_phase4_progress as m
from ire.v5.first_five_window_review_gate import WindowReviewError

ROOT = Path(__file__).resolve().parents[3]


class ScopedProgressTests(unittest.TestCase):
    def test_actual_historical_public_and_private_counts_remain_distinct(self):
        a = m.audit(ROOT)
        p1 = a["P1_public_private_receipt_reconciliation"]
        self.assertEqual(p1["public_formal_processed_windows"], 5)
        self.assertEqual(p1["historical_private_reviewed_windows"], 40)
        self.assertFalse(p1["actual_private_replay_this_execution"])
        self.assertEqual(p1["promoted_public_processed_windows"], 0)
        self.assertFalse(p1["research_completion"])

    def test_next_27_cues_queued_without_fictional_research_approval(self):
        data = m.audit(ROOT)["P3_video1_next_batch"]
        self.assertEqual(data["windows_queued"], 27)
        self.assertEqual(data["window_ids"], [f"W{i:05d}" for i in range(41, 68)])
        self.assertFalse(data["meaning_extraction_complete_on_original_now"])
        self.assertFalse(data["formal_source_fact_approval"])
        self.assertTrue(all(not x["formal_research_receipt_issued"] for x in data["queue"]))

    def test_merge_preview_never_mutates_116_or_b04(self):
        d = m.audit(ROOT)["P4_incremental_knowledge_premerge"]
        self.assertEqual(d["legacy_master_claims_preserved"], 116)
        self.assertEqual(d["existing_scoped_education_nodes"], 9)
        self.assertEqual(len(d["candidate_links"]), 9)
        self.assertFalse(d["master_changed"])
        self.assertFalse(d["knowledge_graph_merged"])

    def test_public_fake_completion_rejected(self):
        p = m.read(ROOT / m.PUBLIC)
        p["windows_processed_reported"] = 40
        with self.assertRaisesRegex(m.ProgressReviewError, "P1_PUBLIC_CONTROL_PLANE"):
            m.audit(ROOT, public_override=p)

    def test_unauthorized_window_fact_promotion_rejected(self):
        d = m.read(ROOT / m.COMPACT)
        d["records"][40]["fact_approved"] = True
        with self.assertRaisesRegex(m.ProgressReviewError, "P3_PROVISIONAL_WINDOW"):
            m.audit(ROOT, compact_override=d)

    def test_cue_gap_rejected_even_with_valid_hashes(self):
        d = m.read(ROOT / m.COMPACT)
        d["records"][40]["first_cue"] += 1
        with self.assertRaisesRegex(m.ProgressReviewError, "P3_CUE_GAP"):
            m.audit(ROOT, compact_override=d)

    def test_wrong_private_zip_cannot_be_called_source_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory) / "fake.zip"
            src.write_bytes(b"not the private original archive")
            with self.assertRaises(WindowReviewError):
                m.audit(ROOT, source_zip=src)


if __name__ == "__main__":
    unittest.main()
