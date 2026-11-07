"""Adversarial tests of a genuinely previously unseen 214-cue video."""
import copy
import tempfile
import unittest
from pathlib import Path

from ire.v5 import new_video_batch_gate as gate

ROOT=Path(__file__).resolve().parents[3]

class UnseenVideoOneTurnTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=gate.read(ROOT/gate.STUDY)

    def altered(self,modify):
        o=copy.deepcopy(self.original)
        modify(o)
        return gate.verify(ROOT,review=o)

    def test_actual_new_video_214_cues_13_claims_17_authorities(self):
        result=gate.verify(ROOT)
        self.assertEqual(result["roster_no"],231)
        self.assertEqual(result["video_id"],"C7KctGzg-K0")
        self.assertEqual(result["source_cues_full_video_covered"],214)
        self.assertEqual(result["source_claims_extracted_and_checked"],13)
        self.assertEqual(result["verified_separate_public_source_references"],17)
        self.assertEqual(result["old_core_or_education_context_links"],5)
        self.assertEqual(result["new_knowledge_provisional_only"],3)
        self.assertEqual(result["superseded_draft_and_reversed_policy_detected"],2)
        self.assertEqual(result["all_private_original_cue_windows_byte_verified_now"],0)
        self.assertFalse(result["personalized_investment_advice_approved"])

    def test_source_video_identity_must_match_original_zip_catalog(self):
        with self.assertRaisesRegex(gate.IncrementalReviewError,
                                    "NEW_VIDEO_CENSUS_SOURCE_MISMATCH"):
            self.altered(lambda x:x["video"].update(
                original_srt_sha256="0"*64))

    def test_no_skipped_middle_cues(self):
        with self.assertRaisesRegex(gate.IncrementalReviewError,
                                    "NEW_VIDEO_MISSING_CUE_COVERAGE"):
            self.altered(lambda x:x["coverage_segments"][7].update(
                start=122))

    def test_no_forged_span_digest(self):
        with self.assertRaisesRegex(gate.IncrementalReviewError,
                                    "NEW_VIDEO_ATOMIC_SOURCE_CUE_ANCHOR_INVALID"):
            self.altered(lambda x:x["research_claims"][0].update(
                source_cue_span_sha256="bad"))

    def test_original_youtube_script_does_not_authorize_personal_advice(self):
        with self.assertRaisesRegex(gate.IncrementalReviewError,
                                    "NEW_VIDEO_UNVERIFIED_TAX_ADVICE_PROMOTED"):
            self.altered(lambda x:x["research_claims"][0].update(
                personal_investment_advice_approved=True))

    def test_2025_dividend_threshold_not_passed_as_2026_current_law(self):
        def corrupt(x):
            c=next(r for r in x["research_claims"]
                   if r["claim_id"]=="C231-02")
            c["authoritative_comparison"]="2025 35% 최고세율과 20% 배당성향을 2026에도 그대로 시행한다고 주장한다. 공식적인 시행 법령 내용을 확인하지 않은 채 원래의 제안 수치와 법률 조건을 모두 현행으로 잘못 안내하려는 부적절한 시험."
        with self.assertRaisesRegex(gate.IncrementalReviewError,
                                    "NEW_VIDEO_2025_DIVIDEND_PROPOSAL_FALSELY_CURRENT"):
            self.altered(corrupt)

    def test_10b_major_shareholder_proposal_not_enacted(self):
        def corrupt(x):
            c=next(r for r in x["research_claims"]
                   if r["claim_id"]=="C231-12")
            c["disposition"]="ENACTED_MARKET_SEGMENTED_WITH_ASR_WARNING"
        with self.assertRaisesRegex(gate.IncrementalReviewError,
                                    "NEW_VIDEO_10B_WAS_NOT_ENACTED"):
            self.altered(corrupt)

    def test_13_pct_stock_estimate_has_no_independent_original_table(self):
        def corrupt(x):
            c=next(r for r in x["research_claims"]
                   if r["claim_id"]=="C231-03")
            c["disposition"]="ENACTED_CORPORATE_TAX_GENERAL"
        with self.assertRaisesRegex(gate.IncrementalReviewError,
                                    "NEW_VIDEO_UNSAFE_TRADE_TAX_OR_UNVERIFIED_ESTIMATE"):
            self.altered(corrupt)

    def test_missing_tax_rule_reference_fails_closed(self):
        def corrupt(x):
            c=next(r for r in x["research_claims"]
                   if r["claim_id"]=="C231-02")
            c["authority_ids"].remove("L26DIV")
        with self.assertRaisesRegex(gate.IncrementalReviewError,
                                    "NEW_VIDEO_2025_DIVIDEND_PROPOSAL_FALSELY_CURRENT"):
            self.altered(corrupt)

    def test_new_provisional_concept_cannot_claim_prior_13_approval(self):
        with self.assertRaisesRegex(gate.IncrementalReviewError,
                                    "NEW_VIDEO_SILENT_LEGACY_OR_KNOWLEDGE_PROMOTION"):
            self.altered(lambda x:x["reconciled_against_prior"].update(
                auto_education_approval_count=3))

    def test_new_knowledge_relation_refs_existing_real_20_or_13(self):
        def corrupt(x):
            c=next(r for r in x["research_claims"]
                   if r["claim_id"]=="C231-12")
            c["reconciliation_link"]["target_id"]="GOMHEE-C999999"
        with self.assertRaisesRegex(gate.IncrementalReviewError,
                                    "NEW_VIDEO_INVALID_OLD_KNOWLEDGE_RELATION"):
            self.altered(corrupt)

    def test_raw_source_archive_not_falsely_available_to_ci(self):
        with self.assertRaisesRegex(gate.IncrementalReviewError,
                                    "NEW_VIDEO_FALSE_SOURCE_OR_LEGACY_PROVENANCE"):
            self.altered(lambda x:x["video"].update(
                private_original_bytes_available_to_github_ci=True))

    def test_private_archive_hash_must_match_if_supplied(self):
        with tempfile.TemporaryDirectory() as dirname:
            p=Path(dirname)/"201-300.zip"
            p.write_bytes(b"fabricated subtitle archive")
            with self.assertRaisesRegex(gate.IncrementalReviewError,
                                        "NEW_VIDEO_PRIVATE_ARCHIVE_TAMPERED"):
                gate.verify(ROOT,private_zip=p)

if __name__=="__main__":
    unittest.main()
