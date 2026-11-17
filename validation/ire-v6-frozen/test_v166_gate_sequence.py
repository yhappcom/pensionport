"""Order-control tests: green does not mean E1 engine passed."""
import copy
import json
import unittest
from pathlib import Path

from v166_gate_sequence import PhaseOrderViolation, check_phase_order, read_and_check

HERE = Path(__file__).resolve().parent


class V166OrderedGateTests(unittest.TestCase):
    def setUp(self):
        self.document = json.loads((HERE / "V166_E1_E7_STATUS.json").read_text(encoding="utf-8"))

    def test_01_persisted_status_valid_and_e1_not_pass(self):
        r = read_and_check(HERE / "V166_E1_E7_STATUS.json")
        self.assertEqual(r["current_step"], "E1")
        self.assertEqual(r["passed_steps"], 0)
        self.assertFalse(r["semantic_or_financial_success_certified"])

    def test_02_cannot_start_e2_before_e1_pass(self):
        d = copy.deepcopy(self.document)
        d["sequence"][1]["status"] = "IN_PROGRESS"
        with self.assertRaises(PhaseOrderViolation):
            check_phase_order(d)

    def test_03_cannot_invent_e1_pass_without_evidence_and_date(self):
        d = copy.deepcopy(self.document)
        d["sequence"][0].update(status="PASS", blockers=[], retest_required=False)
        with self.assertRaises(PhaseOrderViolation):
            check_phase_order(d)

    def test_04_no_unreviewed_final_go(self):
        d = copy.deepcopy(self.document)
        d["one_video_poc_pass"] = True
        with self.assertRaises(PhaseOrderViolation):
            check_phase_order(d)

    def test_05_cannot_reorder_or_weaken_user_criteria(self):
        d = copy.deepcopy(self.document)
        d["sequence"][4]["criterion"] = "CI green"
        with self.assertRaises(PhaseOrderViolation):
            check_phase_order(d)

    def test_06_failure_requires_blocker_and_retest(self):
        d = copy.deepcopy(self.document)
        d["sequence"][0]["blockers"] = []
        with self.assertRaises(PhaseOrderViolation):
            check_phase_order(d)

    def test_07_real_ordered_progress_transition(self):
        d = copy.deepcopy(self.document)
        d["sequence"][0].update(status="PASS", blockers=[], retest_required=False,
                                completed_at="2026-11-17T00:00:00+09:00")
        d["current_step"] = "E2"
        self.assertEqual(check_phase_order(d)["current_step"], "E2")
        d["sequence"][1]["status"] = "IN_PROGRESS"
        self.assertEqual(check_phase_order(d)["current_step"], "E2")

    def test_08_v166_status_cannot_claim_independent_gold(self):
        d = copy.deepcopy(self.document)
        d["independent_gold_certified"] = True
        with self.assertRaises(PhaseOrderViolation):
            check_phase_order(d)


if __name__ == "__main__":
    unittest.main()
