"""Prevent terminal receipt research-completion misrepresentation.

Regression: previous one-turn output declared one_request_research_complete=True
and research_state=ALL_53_NEW_VIDEO_CLAIMS_DISPOSITIONED while independent
blind review was False. The deterministic gate must not certify research.
"""
import unittest

from ire.v5.one_turn_run import assert_receipt_safety

SAFE = {
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
    "private_original_archive_verified_in_this_process": False,
    "p0_incremental_source_derivative_integrity": {"p0_go": False},
    "p0_candidate_source_window_ownership": {"p0_go": False},
    "p0_private_original_source_replay": {"p0_go": False, "source_original_bytes_replayed": False},
    "p0_multicue_context_census": {"p0_go": False},
    "p0_private_multicue_span_replay": {"p0_go": False, "source_original_bytes_replayed": False},
}

class ResearchScopeReceiptTests(unittest.TestCase):
    def test_scoped_structural_receipt_accepted(self):
        self.assertIsNone(assert_receipt_safety(dict(SAFE)))

    def test_legacy_true_research_complete_rejected(self):
        payload = dict(SAFE, one_request_research_complete=True)
        with self.assertRaisesRegex(RuntimeError, "UNSAFE_TERMINAL_RECEIPT"):
            assert_receipt_safety(payload)

    def test_legacy_53_disposition_state_rejected(self):
        payload = dict(SAFE, research_state="ALL_53_NEW_VIDEO_CLAIMS_DISPOSITIONED")
        with self.assertRaisesRegex(RuntimeError, "UNSAFE_TERMINAL_RECEIPT"):
            assert_receipt_safety(payload)

    def test_missing_scope_is_fail_closed(self):
        for field in ("research_state", "one_request_research_complete"):
            with self.subTest(field=field):
                payload = dict(SAFE)
                del payload[field]
                with self.assertRaisesRegex(RuntimeError, "UNSAFE_TERMINAL_RECEIPT"):
                    assert_receipt_safety(payload)

    def test_false_blind_review_waiver_rejected(self):
        payload = dict(SAFE, blind_review_required_for_research_fact_acceptance=False)
        with self.assertRaisesRegex(RuntimeError, "UNSAFE_TERMINAL_RECEIPT"):
            assert_receipt_safety(payload)

if __name__ == "__main__":
    unittest.main()
