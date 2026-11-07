"""Adversarial checks for source-scoped fact acceptance without blind review."""
from __future__ import annotations
import copy
import unittest
from pathlib import Path

from ire.v5 import chat_evidence_acceptance_gate as gate

ROOT = Path(__file__).resolve().parents[3]


class ChatEvidenceAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = gate._read(ROOT / gate.POLICY)

    def altered(self, change):
        d = copy.deepcopy(self.base)
        change(d)
        return gate.verify(ROOT, d)

    def test_user_policy_recognizes_nine_facts_three_partials_without_blind(self):
        report = gate.verify(ROOT)
        self.assertEqual(report["atomic_claims_adjudicated"], 22)
        self.assertEqual(report["fully_accepted_facts"], 9)
        self.assertEqual(report["narrowly_accepted_partial_facts"], 3)
        self.assertEqual(report["not_accepted_as_facts"], 10)
        self.assertFalse(report["independent_blind_review_required"])
        self.assertFalse(report["real_personalized_investment_advice_approved"])

    def test_policy_cannot_require_external_blind_reviewer(self):
        with self.assertRaisesRegex(gate.AcceptanceGateError, "EVIDENCE_POLICY"):
            self.altered(lambda d: d.update(
                independent_human_blind_evaluation_required=True))

    def test_link_only_without_specific_fact_is_not_evidence(self):
        with self.assertRaisesRegex(gate.AcceptanceGateError, "EVIDENCE_FACT_CANNOT"):
            self.altered(lambda d: d["claims"][0].update(accepted_fact=None))

    def test_false_ipo_claim_cannot_be_promoted(self):
        with self.assertRaisesRegex(gate.AcceptanceGateError, "EVIDENCE_UNPROVEN"):
            self.altered(lambda d: d["claims"][10].update(
                verdict="ACCEPTED_FACT",
                accepted_fact="모든 약세장에서는 IPO 투자에 초과수익이 반드시 발생한다는 경험 법칙이 사실이다.",
                source_ids=["KRX-OFFER"]))

    def test_fabricated_citation_not_in_semantic_claim_rejected(self):
        with self.assertRaisesRegex(gate.AcceptanceGateError, "EVIDENCE_FACT_CITATION"):
            self.altered(lambda d: d["claims"][0].update(
                source_ids=["MEDIA-OBZEN-2023"]))

    def test_partial_stock_price_stays_limited(self):
        with self.assertRaisesRegex(gate.AcceptanceGateError, "EVIDENCE_PARTIAL"):
            self.altered(lambda d: d["claims"][9].pop("narrow_exclusion"))

    def test_2026_future_law_cannot_be_miscast_as_effective_now(self):
        with self.assertRaisesRegex(gate.AcceptanceGateError, "EVIDENCE_FUTURE_RULE"):
            self.altered(lambda d: d["future_context_facts"][0].update(
                status="EFFECTIVE_CURRENT"))

    def test_2023_first_day_rule_wrong_date_is_rejected(self):
        with self.assertRaisesRegex(gate.AcceptanceGateError, "EVIDENCE_2023_RULE"):
            self.altered(lambda d: d["claims"][5].update(
                accepted_fact="IPO 상장일 가격제한폭 변경은 2023-07-01부터 적용되는 공모가의 60~400%다."))

    def test_corrected_market_cap_formula_cannot_be_dropped(self):
        with self.assertRaisesRegex(gate.AcceptanceGateError, "EVIDENCE_CRITICAL_CORRECTION"):
            self.altered(lambda d: d["claims"][19].update(verdict="CONTEXT_ONLY",
                                                            accepted_fact=None,
                                                            source_ids=[]))

    def test_no_auto_personal_trade_approval(self):
        with self.assertRaisesRegex(gate.AcceptanceGateError, "EVIDENCE_SCOPE_OR_APPROVAL"):
            self.altered(lambda d: d["claims"][1].update(personal_advice_approved=True))

    def test_incomplete_22_claims_not_allowed(self):
        with self.assertRaisesRegex(gate.AcceptanceGateError, "EVIDENCE_EACH_ATOMIC"):
            self.altered(lambda d: d["claims"].pop())


if __name__ == "__main__":
    unittest.main()
