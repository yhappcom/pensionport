"""Adversarial tests for 22 fine-grained assertions from video #232."""
import copy
import unittest
from pathlib import Path

from ire.v5 import semantic_evidence_gate as gate

ROOT = Path(__file__).resolve().parents[3]


class IPOFineMeaningEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = gate.read(ROOT / gate.OVERLAY)

    def mutate(self, change):
        o = copy.deepcopy(self.original)
        change(o)
        return gate.verify(ROOT, overlay=o)

    def test_22_fine_assertions_stay_pinned_to_12_original_claims(self):
        result = gate.verify(ROOT)
        self.assertEqual(result["rechecked_semantic_units"], 22)
        self.assertEqual(result["parent_original_claims_preserved"], 12)
        self.assertEqual(result["original_source_cues_parent_covered"], 185)
        self.assertFalse(result["financial_fact_certified"])

    def test_bad_parent_mapping_rejected(self):
        with self.assertRaisesRegex(gate.SemanticEvidenceGateError,
                                    "SEMANTIC_ATOMIC_ANCHOR_OR_REVIEW_MISSING"):
            self.mutate(lambda j: j["semantic_assertions"][1].update(
                parent_claim_id="C232-12"))

    def test_empty_authority_rejected(self):
        with self.assertRaisesRegex(gate.SemanticEvidenceGateError,
                                    "SEMANTIC_EVIDENCE_IDS_FABRICATED"):
            self.mutate(lambda j: j["semantic_assertions"][0].update(
                source_ids=["FAKE"]))

    def test_changing_raw_srt_hash_rejected(self):
        with self.assertRaisesRegex(gate.SemanticEvidenceGateError,
                                    "SEMANTIC_SOURCE_BASELINE_MISMATCH"):
            self.mutate(lambda j: j.update(original_srt_sha256="0"*64))

    def test_fake_independent_financial_certification_rejected(self):
        with self.assertRaisesRegex(gate.SemanticEvidenceGateError,
                                    "SEMANTIC_PRETENDS_APPROVED_OR_SCREEN_VERIFIED"):
            self.mutate(lambda j: j.update(
                financial_fact_independently_certified=True))

    def test_wrong_ipo_2023_price_return_rejected(self):
        with self.assertRaisesRegex(gate.SemanticEvidenceGateError,
                                    "SEMANTIC_OLD_ARITHMETIC_OR_EFFECTIVE_DATE_LOST"):
            self.mutate(lambda j: j["semantic_assertions"][2].update(
                independent_evidence_analysis="주식의 고정 수익률은 +130%로 확정됨."*3))

    def test_2026_november_13_proposal_cannot_be_called_effective_today(self):
        with self.assertRaisesRegex(gate.SemanticEvidenceGateError,
                                    "SEMANTIC_2026_FUTURE_RULE_FALSELY_EFFECTIVE"):
            self.mutate(lambda j: j["temporal_rule_updates"][1].update(
                status="EFFECTIVE_CURRENT"))

    def test_all_february_ttasang_false_claim_not_approved(self):
        with self.assertRaisesRegex(gate.SemanticEvidenceGateError,
                                    "SEMANTIC_MISSING_CRITICAL_ERRORS_AND_PARTIAL_EVIDENCE"):
            self.mutate(lambda j: j["semantic_assertions"][13].update(
                adjudication="VERIFIED_ALL_FEBRUARY_TTASANG"))

    def test_share_unit_price_not_size_proxy(self):
        with self.assertRaisesRegex(gate.SemanticEvidenceGateError,
                                    "SEMANTIC_MISSING_CRITICAL_ERRORS_AND_PARTIAL_EVIDENCE"):
            self.mutate(lambda j: j["semantic_assertions"][19].update(
                adjudication="IPO_SMALL_COMPANY_CONFIRMED"))

    def test_personal_trade_recommendation_rejected(self):
        with self.assertRaisesRegex(gate.SemanticEvidenceGateError,
                                    "SEMANTIC_UNREVIEWED_FACT_PROMOTED"):
            self.mutate(lambda j: j["semantic_assertions"][21].update(
                individual_advice_approved=True))


if __name__ == "__main__":
    unittest.main()
