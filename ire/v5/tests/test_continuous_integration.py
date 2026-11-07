"""Tests use real legacy Git metadata without exposing private SRT text."""
import unittest
from pathlib import Path

from ire.v5.continuous_integration import build, QueueError

ROOT=Path(__file__).resolve().parents[3]


class ContinuousResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=build(ROOT)
        cls.items={r["video_id"]:r for r in cls.result["items"]}

    def test_791_video_id_reconciliation_is_complete(self):
        self.assertEqual(len(self.result["items"]),791)
        self.assertEqual(len(self.items),791)
        self.assertEqual(sum(self.result["work_class_counts"].values()),791)
        self.assertEqual(sum(x["type"]=="Long-form" for x in self.items.values()),703)
        self.assertEqual(sum(x["type"]=="Short" for x in self.items.values()),88)

    def test_legacy_video_references_preserved_not_reanalyzed_by_default(self):
        legacy=[x for x in self.items.values() if x["legacy_record_present"]]
        self.assertGreater(len(legacy),100)
        self.assertTrue(all(x["reanalysis_required_by_default"] is False
                            for x in legacy))

    def test_new_source_is_not_marked_analyzed_or_approved(self):
        item=self.items["ATMJeH2TyxE"]
        self.assertTrue(item["srt_in_indexed_catalog"])
        self.assertFalse(item["legacy_record_present"])
        self.assertEqual(item["work_class"],"ANALYZE_NEW_SOURCE_THEN_RECONCILE")
        self.assertFalse(item["advisory_eligible"])

    def test_existing_video_and_new_review_are_reconciled_by_id_not_ordinal(self):
        item=self.items["4TFtEQxSM38"]
        self.assertEqual(item["roster_no"],212)
        self.assertTrue(item["legacy_record_present"])
        self.assertTrue(item["srt_in_indexed_catalog"])
        self.assertTrue(item["provisional_v5_review_present"])
        self.assertEqual(item["work_class"],
                         "REVIEW_EVIDENCE_AND_KNOWLEDGE_RECONCILIATION")

    def test_existing_claims_and_reviews_not_automatically_advisory(self):
        self.assertTrue(all(x["advisory_eligible"] is False for x in self.items.values()))
        self.assertTrue(all(x["finance_facts_independently_approved_here"]==0
                            for x in self.items.values()))
        self.assertTrue(self.result["research_completed_videos_not_inferred"])
        self.assertTrue(self.result["independent_financial_approval_not_inferred"])

    def test_source_inventory_is_not_equated_with_research_completion(self):
        self.assertEqual(self.result["indexed_raw_srt_videos"],99)
        self.assertGreater(self.result["legacy_video_id_references_in_roster"],0)
        self.assertEqual(self.result["provisional_v5_review_videos"],1)

if __name__=="__main__":
    unittest.main()
