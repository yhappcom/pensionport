"""Regression gates for the hourly P0 real-SRT semantic receipt."""
import copy
import unittest
from ire.v5.validation.p0_hourly22_source_gate import (
    audited_status, load_hourly22, _scan_no_raw_source)


class P0Hourly22RealSourceGateTests(unittest.TestCase):
    def test_pilot_reads_twelve_consecutive_original_windows(self):
        r=audited_status()
        self.assertEqual(r["windows_read"],12)
        self.assertEqual(r["original_cues_read"],216)
        self.assertEqual(r["next_window"],"W00013")
        self.assertTrue(r["no_prior_window_overlap"])

    def test_second_pass_finds_additional_atomic_units_but_cannot_certify_recall(self):
        d=load_hourly22()
        self.assertEqual(d["candidate_first_pass_count"],40)
        self.assertEqual(d["compound_first_pass_replaced"],1)
        self.assertEqual(d["provisional_final_atomic_candidates"],44)
        self.assertFalse(d["independent_gold_atomic_recall_certified"])
        self.assertFalse(d["second_pass_disposition"]["independent_blind_gold"])
        self.assertEqual(len(d["second_pass_disposition"]["second_pass_new_source_claims"]),5)

    def test_no_financial_claim_window_remains_explicitly_documented(self):
        d=load_hourly22()
        self.assertEqual(d["source_windows"][1]["window_id"],"W00002")
        self.assertEqual(d["source_windows"][1]["disposition"],"NO_FINANCIAL_ATOMIC_CLAIMS")
        self.assertEqual(d["source_windows"][1]["candidate_claim_ids"],[])

    def test_markets_dividend_war_and_unsuitable_guarantees_stay_open(self):
        d=load_hourly22()
        self.assertIn("INVALID_GENERAL_RECOVERY",{x["review_status"] for x in d["evidence_reviews"]})
        self.assertIn("HISTORICAL_DATE_CORRECTION",{x["review_status"] for x in d["evidence_reviews"]})
        self.assertIn("OPEN_SPECIFIC_PRODUCT_DATA",{x["review_status"] for x in d["evidence_reviews"]})
        self.assertFalse(d["full_ledger_event_chain_submitted"])
        self.assertFalse(d["financial_truth_automatically_approved"])

    def test_private_source_and_semantic_recall_falsification_refused(self):
        _scan_no_raw_source(load_hourly22())
        with self.assertRaisesRegex(ValueError,"P0_HOURLY_PRIVATE_SRT_IN_GITHUB"):
            _scan_no_raw_source({"original_srt":"must not store"})
        self.assertEqual(audited_status()["p0_final_release"],"NO_GO")


if __name__=="__main__":
    unittest.main()
