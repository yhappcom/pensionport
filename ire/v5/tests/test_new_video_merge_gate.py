"""Ensure the 2025 tax-video cannot corrupt prior 13 knowledge topics."""
import copy
import unittest
from pathlib import Path
from ire.v5 import new_video_merge_gate as gate

ROOT=Path(__file__).resolve().parents[3]

class UnseenVideoIncrementalMergeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=gate.load(ROOT/gate.OVERLAY)

    def altered(self,fn):
        g=copy.deepcopy(self.base);fn(g)
        return gate.verify(ROOT,overlay=g)

    def test_real_video_linked_without_knowledge_promotion(self):
        r=gate.verify(ROOT)
        self.assertEqual(r["prior_education_topics_unchanged"],13)
        self.assertEqual(r["original_video_claims_reconciled"],13)
        self.assertEqual(r["existing_core_or_education_links"],5)
        self.assertEqual(r["new_scoped_tax_topics_held_as_provisional"],3)
        self.assertEqual(r["new_approved_tax_topics"],0)
        self.assertFalse(r["personal_investment_advice_enabled"])

    def test_unverified_2025_proposal_cannot_auto_merge(self):
        with self.assertRaisesRegex(gate.IncrementalMergeError,"MERGE_FALSE_ADVICE_OR_APPROVAL"):
            self.altered(lambda x:x.update(new_approved_education_topics=3))

    def test_unseen_claim_id_or_original_hash_changed_rejected(self):
        with self.assertRaisesRegex(gate.IncrementalMergeError,
                                    "MERGE_SOURCE_CUE_OR_TEMPORAL_QUALIFICATION_CHANGED"):
            self.altered(lambda x:x["normalized_existing_context_links"][0].update(
                source_cue_span_sha256="0"*64))

    def test_2025_proposal_cannot_be_latest_authority(self):
        def alter(x):
            x["new_provisional_topics"][0]["source_current"]=["M25","L26DIV"]
        with self.assertRaisesRegex(gate.IncrementalMergeError,
                                    "MERGE_2025_DRAFT_FALSELY_CURRENT"):
            self.altered(alter)

    def test_new_tax_concept_needs_current_two_sources(self):
        def alter(x):
            x["new_provisional_topics"][1]["source_current"]=["B26STT"]
        with self.assertRaisesRegex(gate.IncrementalMergeError,
                                    "MERGE_UNSUPPORTED_NEW_TAX_FACT_ESCALATED"):
            self.altered(alter)

    def test_unrelated_legacy_claim_id_not_invented(self):
        def alter(x):
            x["normalized_existing_context_links"][0][
                "existing_context"]=["FAKE-C999"]
            x["normalized_existing_context_links"][0][
                "existing_knowledge_relation"]={
                "target_id":"FAKE-C999","relation":"SUPPORTS"}
        with self.assertRaisesRegex(gate.IncrementalMergeError,
                                    "MERGE_SOURCE_CUE_OR_TEMPORAL_QUALIFICATION_CHANGED"):
            self.altered(alter)

    def test_missing_existing_link_is_detected(self):
        def alter(x):
            x["normalized_existing_context_links"][0][
                "existing_knowledge_relation"]=None
        with self.assertRaisesRegex(gate.IncrementalMergeError,
                                    "MERGE_SOURCE_CUE_OR_TEMPORAL_QUALIFICATION_CHANGED"):
            self.altered(alter)

    def test_no_fake_external_blind_review(self):
        with self.assertRaisesRegex(gate.IncrementalMergeError,
                                    "MERGE_FALSE_ADVICE_OR_APPROVAL"):
            self.altered(lambda x:x.update(independent_human_reviewer_completed=True))

if __name__=="__main__":
    unittest.main()
