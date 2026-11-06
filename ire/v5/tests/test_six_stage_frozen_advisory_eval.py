"""Evaluate frozen new question pack against actual P3 outputs, not mocks."""
from pathlib import Path
import unittest
from ire.v5 import six_stage_frozen_advisory_eval as frozen

ROOT=Path(__file__).resolve().parents[3]

class SixStageFrozenAdvisoryTests(unittest.TestCase):
    def test_twelve_new_questions_reach_real_p3_pipeline(self):
        d=frozen.run(ROOT)
        self.assertEqual(d["new_questions_executed_against_actual_p3_pipeline"],12)
        self.assertEqual(d["structural_routing_and_no_action_checks_passed"],12)
        self.assertEqual(len(d["cases"]),12)
        self.assertTrue(all(x["structural_pass"] for x in d["cases"]))
        self.assertFalse(d["human_blind_fact_grade_completed"])
        self.assertFalse(d["investment_decision_usefulness_independently_measured"])
        self.assertFalse(d["overall_advisory_product_approval"])

    def test_numbers_are_independent_arithmetic_not_promised_returns(self):
        d=frozen.run(ROOT)
        self.assertEqual(d["hypothetical_monthly_6pct_distribution_krw"],4_000_000)
        self.assertEqual(d["hypothetical_gift_sum_million_krw"],240)
        self.assertAlmostEqual(d["corrected_yen_870_to_950_pct"],9.1954,places=3)

    def test_frozen_tests_cannot_masquerade_as_blind_evaluator(self):
        frozen.load(ROOT)
        self.assertEqual(len(frozen.load(ROOT)["cases"]),12)
        self.assertFalse(frozen.load(ROOT)["independent_human_reviewer_completed"])

if __name__=="__main__": unittest.main()
