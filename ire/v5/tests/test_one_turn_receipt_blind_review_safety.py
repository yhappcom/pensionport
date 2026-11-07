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
        "private_original_archive_verified_in_this_process": False,
        "p0_incremental_source_derivative_integrity": {"p0_go": False},
        "p0_candidate_source_window_ownership": {"p0_go": False},
        "p0_private_original_source_replay": {"p0_go": False, "source_original_bytes_replayed": False},
        "p0_multicue_context_census": {"p0_go": False},
        "p0_private_multicue_span_replay": {"p0_go": False, "source_original_bytes_replayed": False},
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

    def test_nested_gate_cannot_claim_p0_go(self):
        for field in ("p0_incremental_source_derivative_integrity",
                      "p0_candidate_source_window_ownership",
                      "p0_private_original_source_replay",
                      "p0_multicue_context_census",
                      "p0_private_multicue_span_replay"):
            with self.subTest(field=field):
                bad = safe_receipt()
                bad[field]["p0_go"] = True
                with self.assertRaisesRegex(RuntimeError, "UNSAFE_NESTED_P0_APPROVAL"):
                    assert_receipt_safety(bad)

    def test_missing_or_untyped_nested_gate_fails_closed(self):
        for field in ("p0_incremental_source_derivative_integrity",
                      "p0_candidate_source_window_ownership",
                      "p0_private_original_source_replay",
                      "p0_multicue_context_census",
                      "p0_private_multicue_span_replay"):
            for invalid in (None, [], {"p0_go": 0}, {"p0_go": "false"}):
                with self.subTest(field=field, invalid=invalid):
                    bad = safe_receipt()
                    bad[field] = invalid
                    with self.assertRaisesRegex(RuntimeError, "UNSAFE_NESTED_P0_APPROVAL"):
                        assert_receipt_safety(bad)

    def test_private_replay_attestation_must_match_both_private_gates(self):
        for field in ("p0_private_original_source_replay",
                      "p0_private_multicue_span_replay"):
            with self.subTest(field=field):
                bad = safe_receipt()
                bad[field]["source_original_bytes_replayed"] = True
                with self.assertRaisesRegex(RuntimeError, "UNSAFE_PRIVATE_REPLAY_ATTESTATION"):
                    assert_receipt_safety(bad)
        bad = safe_receipt()
        bad["private_original_archive_verified_in_this_process"] = True
        with self.assertRaisesRegex(RuntimeError, "UNSAFE_PRIVATE_REPLAY_ATTESTATION"):
            assert_receipt_safety(bad)
        good = safe_receipt()
        good["private_original_archive_verified_in_this_process"] = True
        for field in ("p0_private_original_source_replay",
                      "p0_private_multicue_span_replay"):
            good[field]["source_original_bytes_replayed"] = True
        # A positive private-replay attestation must also carry complete,
        # matching source/anchor/window/context-cue census evidence. The
        # legacy fixture had only booleans and must not bypass the new gate.
        from ire.v5.tests.test_p0_private_replay_census_receipt import replay_receipt
        complete = replay_receipt()
        self.assertIsNone(assert_receipt_safety(complete))
        with self.assertRaisesRegex(RuntimeError, "UNSAFE_PRIVATE_REPLAY_CENSUS_MISMATCH"):
            assert_receipt_safety(good)

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
