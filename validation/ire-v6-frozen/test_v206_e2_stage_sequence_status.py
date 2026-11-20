"""Current E2 sequential-stage verdict is a HOLD until real source/gold."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent
STATE=ROOT/"V202_E1_E5_CURRENT_ROUTE_SEQUENCE_STATUS.json"
E2_REPORT=ROOT/"V206_E2_FULL_SOURCE_SEMANTIC_CENSUS_IMPLEMENTED_REAL_GOLD_HOLD_20261120.md"


class TestV206E2StageGate(unittest.TestCase):
    def setUp(self):
        self.status=json.loads(STATE.read_text(encoding="utf-8"))

    def test_01_e1_historical_pass_not_e2_quality_pass(self):
        self.assertEqual(self.status["sequence"][0]["status"],"PASS")
        self.assertTrue(self.status["current_e1_verdict"].startswith("PASS_V203_"))
        self.assertEqual(self.status["current_step"],
                         "E2_SOURCE_SEMANTIC_IN_PROGRESS_HOLD_REAL_VIDEO")
        self.assertTrue(self.status["current_e2_verdict"].startswith("HOLD_"))

    def test_02_real_source_and_gold_not_falsely_certified(self):
        e=self.status["e2_evidence"]
        self.assertTrue(e["original_full_cue_census_implemented"])
        self.assertTrue(e["private_sqlite_hashchain_resume_and_idempotency_tested"])
        self.assertFalse(e["real_owner_srt_bytes_available_in_current_runtime"])
        self.assertFalse(e["real_13_segment_e2_review_completed"])
        self.assertFalse(e["independent_real_semantic_gold_certified"])
        self.assertFalse(e["native_fact_correction_and_relations_transferred"])
        self.assertEqual(e["knowledge_published"],0)

    def test_03_e3_e4_e5_stay_not_run_no_premature_release(self):
        self.assertEqual(self.status["sequence"][1]["status"],
                         "IN_PROGRESS_HOLD_REAL_SOURCE_AND_GOLD")
        self.assertEqual([x["status"] for x in self.status["sequence"][2:]],
                         ["NOT_RUN_CURRENT_ROUTE"]*3)
        self.assertTrue(E2_REPORT.is_file())
        txt=E2_REPORT.read_text(encoding="utf-8")
        self.assertIn("104/104",txt)
        self.assertIn("HOLD_REAL_SOURCE_AND_INDEPENDENT_GOLD",txt)


if __name__=="__main__":
    unittest.main()
