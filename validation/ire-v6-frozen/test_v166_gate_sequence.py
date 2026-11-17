"""Phase order must follow the persisted E1-E7 ledger; no automatic GO."""
import copy
import json
import unittest
from pathlib import Path

from v166_gate_sequence import PhaseOrderViolation, check_phase_order, read_and_check

HERE = Path(__file__).resolve().parent


class V166OrderedGateTests(unittest.TestCase):
    def setUp(self):
        self.document = json.loads((HERE / "V166_E1_E7_STATUS.json").read_text(encoding="utf-8"))

    def test_01_e1_and_e2_evidenced_pass_e3_not_run(self):
        r = read_and_check(HERE / "V166_E1_E7_STATUS.json")
        self.assertEqual(r["current_step"], "E3")
        self.assertEqual(r["passed_steps"], 2)
        self.assertFalse(r["semantic_or_financial_success_certified"])

    def test_02_cannot_start_e3_if_e2_regresses(self):
        d = copy.deepcopy(self.document)
        d["sequence"][1].update(status="FAIL",completed_at=None,
                blockers=["E2 source meaning failure"],retest_required=True)
        d["current_step"] = "E2"
        # E2 FAIL and E3 NOT_RUN is legitimately fail-closed. The regression
        # is a premature E3 start despite E2 still failing.
        d["sequence"][2]["status"] = "IN_PROGRESS"
        with self.assertRaises(PhaseOrderViolation):
            check_phase_order(d)

    def test_03_cannot_invent_e2_pass_without_evidence_and_date(self):
        d = copy.deepcopy(self.document)
        d["sequence"][1]["evidence_paths"] = []
        d["sequence"][1]["completed_at"] = None
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
        d["sequence"][2]["status"] = "FAIL"
        d["sequence"][2]["blockers"] = []
        d["sequence"][2]["retest_required"] = True
        with self.assertRaises(PhaseOrderViolation):
            check_phase_order(d)

    def test_07_real_ordered_progress_transition(self):
        d = copy.deepcopy(self.document)
        self.assertEqual(check_phase_order(d)["current_step"],"E3")
        d["sequence"][2].update(status="PASS", completed_at="2026-11-17T17:00:00+09:00",
               evidence_paths=["validation/ire-v6-frozen/example_e3_proof.md"],
               blockers=[],retest_required=False)
        d["current_step"]="E4"
        self.assertEqual(check_phase_order(d)["current_step"],"E4")
        d["sequence"][3]["status"]="IN_PROGRESS"
        self.assertEqual(check_phase_order(d)["current_step"],"E4")

    def test_08_cannot_claim_independent_gold_before_all_steps(self):
        d = copy.deepcopy(self.document)
        d["independent_gold_certified"] = True
        with self.assertRaises(PhaseOrderViolation):
            check_phase_order(d)


if __name__ == "__main__":
    unittest.main()
