"""Adversarial regression checks for a second unseen full-SRT V5 ingestion."""
import copy
import unittest
from pathlib import Path

from ire.v5 import new_video_followup_gate as gate

ROOT = Path(__file__).resolve().parents[3]


class SecondUnseenVideoGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.study = gate.read_json(ROOT / gate.DEFAULT_STUDY)

    def check_altered(self, alter):
        clone = copy.deepcopy(self.study)
        alter(clone)
        return gate.verify(ROOT, review=clone)

    def test_real_second_video_185_cues_12_claims(self):
        result = gate.verify(ROOT)
        self.assertEqual(result["video_id"], "WIXWPJjhF50")
        self.assertEqual(result["source_cues_covered"], 185)
        self.assertEqual(result["anchored_material_claims"], 12)
        self.assertEqual(result["prior_education_nodes_preserved"], 13)
        self.assertEqual(result["legacy_context_links"], 1)
        self.assertEqual(result["new_provisional_concepts_only"], 2)
        self.assertEqual(result["private_original_claim_spans_byte_rechecked_now"], 0)
        self.assertFalse(result["personal_advice_approved"])

    def test_fabricated_source_hash_fails(self):
        with self.assertRaisesRegex(gate.StudyGateError,
                                    "VIDEO_ARCHIVE_ROSTER_HASH_MISMATCH"):
            self.check_altered(lambda j: j["video"].update(
                original_srt_sha256="0"*64))

    def test_missing_middle_cues_fails(self):
        with self.assertRaisesRegex(gate.StudyGateError,
                                    "CUE_COVERAGE_GAP_OR_OVERLAP"):
            self.check_altered(lambda j: j["coverage_segments"][7].update(
                start=110))

    def test_unanchored_claim_fails(self):
        with self.assertRaisesRegex(gate.StudyGateError,
                                    "CLAIM_ANCHOR_OR_RESEARCH_MISSING"):
            self.check_altered(lambda j: j["research_claims"][0].update(
                source_cue_span_sha256="not-a-real-digest"))

    def test_false_human_approval_fails(self):
        with self.assertRaisesRegex(gate.StudyGateError,
                                    "FALSE_PERSONAL_ADVICE_OR_FACT_PROMOTION"):
            self.check_altered(lambda j: j["research_claims"][4].update(
                external_human_blind_approved=True))

    def test_no_promotion_of_pending_education(self):
        with self.assertRaisesRegex(gate.StudyGateError,
                                    "KNOWLEDGE_SILENTLY_REPLACED"):
            self.check_altered(lambda j: j["reconciled_against_prior"].update(
                auto_education_approval_count=2))

    def test_old_price_arithmetic_cannot_be_mislabeled(self):
        with self.assertRaisesRegex(gate.StudyGateError,
                                    "IPO_HISTORICAL_CURRENT_RULE_CONFUSED"):
            self.check_altered(lambda j: j["numeric_rule_crosscheck"].update(
                old_max_return_pct=130))

    def test_400pct_price_is_300pct_gain_not_400pct_gain(self):
        with self.assertRaisesRegex(gate.StudyGateError,
                                    "IPO_HISTORICAL_CURRENT_RULE_CONFUSED"):
            self.check_altered(lambda j: j["numeric_rule_crosscheck"].update(
                current_max_return_pct=400))

    def test_2023_monthly_prices_cannot_be_current_verified(self):
        with self.assertRaisesRegex(gate.StudyGateError,
                                    "CONTEXT_REFERENCE_FALSLY_CERTIFIES_STATISTIC"):
            self.check_altered(lambda j: j["research_claims"][4].update(
                disposition="CURRENT_RULE_CONFIRMED"))

    def test_unknown_evidence_id_fails(self):
        with self.assertRaisesRegex(gate.StudyGateError,
                                    "CLAIM_AUTHORITIES_OR_EVIDENCE_ROLE_INVALID"):
            self.check_altered(lambda j: j["research_claims"][1].update(
                authority_ids=["UNKNOWN-UNVERIFIED"]))

    def test_fake_existing_knowledge_reference_fails(self):
        with self.assertRaisesRegex(gate.StudyGateError,
                                    "INVALID_OR_DUPLICATE_PRIOR_RELATION"):
            self.check_altered(lambda j: j["reconciled_against_prior"][
                "legacy_claim_relationships"][0].update(target_id="GOMHEE-C999"))

    def test_new_concept_cannot_be_preapproved(self):
        with self.assertRaisesRegex(gate.StudyGateError,
                                    "NEW_CONCEPTS_UNSAFELY_PROMOTED"):
            self.check_altered(lambda j: j["reconciled_against_prior"][
                "new_provisional_concepts"][0].update(approval=True))

    def test_private_zip_wrong_hash_fails_without_exposing_srt(self):
        import tempfile
        with tempfile.TemporaryDirectory() as name:
            fake = Path(name) / "201-300.zip"
            fake.write_bytes(b"not an original archive")
            with self.assertRaisesRegex(gate.StudyGateError,
                                        "PRIVATE_ZIP_DIGEST_MISMATCH"):
                gate.verify(ROOT, private_zip=fake)


if __name__ == "__main__":
    unittest.main()
