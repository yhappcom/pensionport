"""Terminal receipt must never misrepresent deterministic CI as blind research approval."""
from __future__ import annotations

from copy import deepcopy
import unittest

from ire.v5.one_turn_run import assert_receipt_safety


def safe_receipt():
    return {
        "blind_review_required_for_research_fact_acceptance": True,
        "independent_human_blind_evaluation_completed": False,
        "formal_personal_investment_advice_authorized": False,
        "p0_cross_window_semantic_completeness_certified": False,
        "p0_corpus_research_complete": False,
        "p0_independent_semantic_recall_measured": False,
        "p0_engine_quality_certified": False,
        "one_request_research_complete": False,
        "research_state": "DETERMINISTIC_VALIDATION_ONLY_RESEARCH_OPEN",
        "terminal_outcome": "DETERMINISTIC_CHECKS_COMPLETED_RESEARCH_NOT_CERTIFIED",
    }


class ReceiptBlindReviewContractTests(unittest.TestCase):
    def test_safe_terminal_receipt_is_accepted(self):
        self.assertIsNone(assert_receipt_safety(safe_receipt()))

    def test_original_false_blind_review_required_is_rejected(self):
        # Real prior one-turn receipt had this exact unsafe boolean.
        bad = safe_receipt()
        bad["blind_review_required_for_research_fact_acceptance"] = False
        with self.assertRaisesRegex(RuntimeError, "UNSAFE_TERMINAL_RECEIPT"):
            assert_receipt_safety(bad)

    def test_original_research_closed_label_is_rejected(self):
        bad = safe_receipt()
        bad["terminal_outcome"] = "RESEARCH_CLOSED_NOT_ADVICE_RELEASED"
        with self.assertRaisesRegex(RuntimeError, "UNSAFE_TERMINAL_RECEIPT"):
            assert_receipt_safety(bad)

    def test_false_independent_blind_claim_is_rejected(self):
        bad = safe_receipt()
        bad["independent_human_blind_evaluation_completed"] = True
        with self.assertRaisesRegex(RuntimeError, "UNSAFE_TERMINAL_RECEIPT"):
            assert_receipt_safety(bad)

    def test_false_p0_completion_or_semantic_certification_is_rejected(self):
        for field in ("p0_corpus_research_complete",
                      "p0_cross_window_semantic_completeness_certified"):
            with self.subTest(field=field):
                bad = safe_receipt()
                bad[field] = True
                with self.assertRaisesRegex(RuntimeError, "UNSAFE_TERMINAL_RECEIPT"):
                    assert_receipt_safety(bad)

    def test_unmeasured_recall_cannot_be_relabelled_as_measured(self):
        bad = safe_receipt()
        bad["p0_independent_semantic_recall_measured"] = True
        with self.assertRaisesRegex(RuntimeError, "UNSAFE_TERMINAL_RECEIPT"):
            assert_receipt_safety(bad)

    def test_uncertified_engine_cannot_be_relabelled_as_certified(self):
        bad = safe_receipt()
        bad["p0_engine_quality_certified"] = True
        with self.assertRaisesRegex(RuntimeError, "UNSAFE_TERMINAL_RECEIPT"):
            assert_receipt_safety(bad)

    def test_quality_attestation_fields_are_required_strict_false(self):
        for field in ("p0_independent_semantic_recall_measured",
                      "p0_engine_quality_certified"):
            for invalid in (None, 0, "false"):
                with self.subTest(field=field, invalid=invalid):
                    bad = safe_receipt()
                    bad[field] = invalid
                    with self.assertRaisesRegex(RuntimeError, "UNSAFE_TERMINAL_RECEIPT"):
                        assert_receipt_safety(bad)
            bad = safe_receipt()
            del bad[field]
            with self.assertRaisesRegex(RuntimeError, "UNSAFE_TERMINAL_RECEIPT"):
                assert_receipt_safety(bad)

    def test_personal_advice_authorization_is_rejected(self):
        bad = safe_receipt()
        bad["formal_personal_investment_advice_authorized"] = True
        with self.assertRaisesRegex(RuntimeError, "UNSAFE_TERMINAL_RECEIPT"):
            assert_receipt_safety(bad)

    def test_missing_or_nonboolean_review_flag_is_rejected(self):
        for value in (None, 1, "true"):
            with self.subTest(value=value):
                bad = safe_receipt()
                bad["blind_review_required_for_research_fact_acceptance"] = value
                with self.assertRaisesRegex(RuntimeError, "UNSAFE_TERMINAL_RECEIPT"):
                    assert_receipt_safety(bad)
        bad = safe_receipt()
        del bad["blind_review_required_for_research_fact_acceptance"]
        with self.assertRaisesRegex(RuntimeError, "UNSAFE_TERMINAL_RECEIPT"):
            assert_receipt_safety(bad)


if __name__ == "__main__":
    unittest.main()
