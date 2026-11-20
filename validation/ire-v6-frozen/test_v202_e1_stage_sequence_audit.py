"""Immutable sequential E1 stage status regression for independent re-audit.

Historical V166 PASS remains intact. V176 route is FAIL, even when prior
synthetic CI wrote V126 entries. No stage advancement from green rejection CI.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
STATUS=HERE/"V202_E1_E5_CURRENT_ROUTE_SEQUENCE_STATUS.json"
REPORT=HERE/"V202_E1_INDEPENDENT_REAUDIT_FAIL_20261120.md"
OLD_REPORT=HERE/"V202_E1_CURRENT_V176_ROUTE_STRUCTURAL_PASS_20261120.md"


class TestCurrentE1SequenceStatus(unittest.TestCase):
    def setUp(self):
        self.data=json.loads(STATUS.read_text(encoding="utf-8"))

    def test_01_historical_v166_pass_not_rewritten_as_v176_pass(self):
        self.assertIs(self.data["historical_v166_e1_pass_preserved"],True)
        self.assertEqual(self.data["current_step"],"E1_REPAIR_ONLY")
        self.assertEqual(self.data["sequence"][0]["status"],"FAIL")
        self.assertTrue(self.data["current_e1_verdict"].startswith("FAIL_"))

    def test_02_no_stage_after_first_fail_is_entered(self):
        self.assertEqual([s["step"] for s in self.data["sequence"]],
                         ["E1","E2","E3","E4","E5"])
        self.assertEqual(self.data["sequence"][1]["status"],"BLOCKED_BY_E1")
        self.assertTrue(all(
            x["status"]=="NOT_RUN_BLOCKED_BY_E1"
            for x in self.data["sequence"][2:]))

    def test_03_no_fake_e1_positive_after_adversarial_regression(self):
        proof=self.data["e1_evidence"]
        self.assertIs(proof["current_owner_review_to_native_host_batch_proven"],False)
        self.assertIs(proof["current_owner_review_to_native_v123_proven"],False)
        self.assertIs(proof["native_current_same_input_positive_storage_test_pass"],False)
        self.assertIs(proof["previous_v202_synthetic_pass_report_retracted"],True)
        self.assertIs(proof["source_speaker_stance_attribution_drift_found"],True)
        self.assertEqual(proof["defensive_green_ci_test_count"],398)

    def test_04_original_report_exposes_erratum_and_new_hold_proof(self):
        self.assertTrue(REPORT.is_file())
        corrected=OLD_REPORT.read_text(encoding="utf-8")
        self.assertIn("판정은 **철회**",corrected)
        self.assertIn("V202_E1_INDEPENDENT_REAUDIT_FAIL",corrected)
        self.assertIn("E1 FAIL",REPORT.read_text(encoding="utf-8"))

    def test_05_no_real_or_fake_knowledge_issued_as_verified(self):
        self.assertEqual(self.data["protected"]["real_financial_knowledge_published"],0)
        self.assertIs(self.data["protected"]["main_unchanged"],True)
        self.assertIs(self.data["protected"]["owner_private_source_published"],False)


if __name__=="__main__":
    unittest.main()
