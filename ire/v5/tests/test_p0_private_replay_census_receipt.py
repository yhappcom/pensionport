"""Private P0 replay must account for the entire structurally declared census.

Synthetic receipt-only regression. This does NOT claim that private SRT bytes
were supplied to public CI or that financial semantics were independently judged.
"""
from copy import deepcopy
import unittest

from ire.v5.one_turn_run import assert_receipt_safety
from ire.v5.tests.test_research_scope_receipt import SAFE


def replay_receipt():
    receipt = deepcopy(SAFE)
    receipt["private_original_archive_verified_in_this_process"] = True
    receipt["p0_candidate_source_window_ownership"].update({
        "verified_provisional_claim_anchors": 26,
        "batches": 1,
        "cross_window_context_open": 3,
    })
    receipt["p0_private_original_source_replay"].update({
        "source_original_bytes_replayed": True,
        "validated_claim_anchor_hashes_and_times": 26,
        "validated_research_batches": 1,
    })
    receipt["p0_multicue_context_census"].update({
        "claims_with_complete_declared_context_census": 3,
        "cue_roles_reviewed_structurally": 15,
    })
    receipt["p0_private_multicue_span_replay"].update({
        "source_original_bytes_replayed": True,
        "original_private_cues_replayed": 15,
        "multicue_cases_structurally_reviewed": 3,
    })
    return receipt


class ReplayCountReconciliationTests(unittest.TestCase):
    def test_matching_private_counts_accepted_without_semantic_certification(self):
        receipt = replay_receipt()
        self.assertIsNone(assert_receipt_safety(receipt))
        self.assertIs(receipt["p0_engine_quality_certified"], False)

    def test_each_underreported_private_count_fails_closed(self):
        for gate, key in (
            ("p0_private_original_source_replay",
             "validated_claim_anchor_hashes_and_times"),
            ("p0_private_original_source_replay", "validated_research_batches"),
            ("p0_private_multicue_span_replay", "original_private_cues_replayed"),
            ("p0_private_multicue_span_replay",
             "multicue_cases_structurally_reviewed"),
        ):
            with self.subTest(key=key):
                receipt = replay_receipt()
                receipt[gate][key] -= 1
                with self.assertRaisesRegex(RuntimeError,
                                            "UNSAFE_PRIVATE_REPLAY_CENSUS_MISMATCH"):
                    assert_receipt_safety(receipt)

    def test_cross_window_claim_count_mismatch_rejected(self):
        receipt = replay_receipt()
        receipt["p0_multicue_context_census"][
            "claims_with_complete_declared_context_census"] = 2
        with self.assertRaisesRegex(RuntimeError, "UNSAFE_PRIVATE_REPLAY_CENSUS_MISMATCH"):
            assert_receipt_safety(receipt)

    def test_missing_wrong_type_and_boolean_counts_rejected(self):
        for value in (None, True, "26", -1):
            with self.subTest(value=value):
                receipt = replay_receipt()
                receipt["p0_private_original_source_replay"][
                    "validated_claim_anchor_hashes_and_times"] = value
                with self.assertRaisesRegex(RuntimeError,
                                            "UNSAFE_PRIVATE_REPLAY_CENSUS_MISMATCH"):
                    assert_receipt_safety(receipt)
        receipt = replay_receipt()
        del receipt["p0_private_multicue_span_replay"]["original_private_cues_replayed"]
        with self.assertRaisesRegex(RuntimeError, "UNSAFE_PRIVATE_REPLAY_CENSUS_MISMATCH"):
            assert_receipt_safety(receipt)

    def test_public_without_private_bytes_remains_not_verified(self):
        receipt = deepcopy(SAFE)
        self.assertIsNone(assert_receipt_safety(receipt))
        self.assertIs(receipt["private_original_archive_verified_in_this_process"], False)


if __name__ == "__main__":
    unittest.main()
