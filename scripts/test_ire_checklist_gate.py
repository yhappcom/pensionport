"""Synthetic negative/positive checks for strict sequential checklist policy.

Passing these tests says NOTHING about E1-E5 real source completeness.
"""
from __future__ import annotations

import copy
import unittest

from scripts.ire_checklist_gate import CATALOG, ROOT, STATE, load, validate


class ChecklistGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load(ROOT / CATALOG)

    def setUp(self):
        self.state = {
            "schema": "IRE_STRICT_SEQUENTIAL_CHECKLIST_STATE_V1",
            "as_of": "2026-11-22",
            "catalog_path": CATALOG.as_posix(),
            "target_branch": self.catalog["target_branch"],
            "protected_main_sha": self.catalog["protected_main_sha"],
            "items": [
                {"id": task["id"], "status": "READY" if i == 0 else "BLOCKED",
                 "evidence": [], "start_report": None, "end_report": None,
                 "failure_reason": None, "remediation": None}
                for i, task in enumerate(self.catalog["items"])
            ],
        }

    def report(self, item, verdict):
        return {"task_id": item["id"], "channel": "USER_CHAT",
                "declared_sent_to_user": True, "reported_at": "2026-11-22",
                "user_visible_text": "사용자에게 보고한 실제 내용 요약",
                "baseline_sha": "a" * 40, "verdict": verdict}

    def evidence(self, i, **overrides):
        task = self.catalog["items"][i]
        e = {"kind": task["required_evidence_kind"],
             "ref": "https://github.com/yhappcom/pensionport/actions/runs/1",
             "sha": "a" * 40, "scope": "SYNTHETIC_SOFTWARE_ONLY",
             "verified_by": "synthetic unittest", "verdict": "PASS"}
        e.update(overrides)
        return e

    def pass_first(self):
        row = self.state["items"][0]
        row["status"] = "PASS"
        row["start_report"] = self.report(row, "START")
        row["end_report"] = self.report(row, "PASS")
        row["evidence"] = [self.evidence(0)]
        self.state["items"][1]["status"] = "READY"

    def assert_bad(self, label, prev=None):
        errs = validate(self.catalog, self.state, previous=prev)
        self.assertTrue(any(label in x for x in errs), errs)

    def test_baseline_is_only_first_ready(self):
        self.assertEqual([], validate(self.catalog, self.state))
        self.assertEqual(60, len(self.state["items"]))

    def test_correct_pass_opens_only_immediate_next(self):
        prev = copy.deepcopy(self.state)
        self.pass_first()
        self.assertEqual([], validate(self.catalog, self.state, previous=prev))

    def test_next_cannot_be_opened_before_pass(self):
        self.state["items"][1]["status"] = "READY"
        self.assert_bad("OUT_OF_ORDER_PROGRESS")

    def test_next_cannot_be_marked_pass_when_previous_unfinished(self):
        self.state["items"][1]["status"] = "PASS"
        self.assert_bad("OUT_OF_ORDER_PROGRESS")

    def test_pass_without_evidence_rejected(self):
        self.pass_first()
        self.state["items"][0]["evidence"] = []
        self.assert_bad("PASS_MISSING_VERIFIABLE_REQUIRED_EVIDENCE")

    def test_pass_without_user_start_report_rejected(self):
        self.pass_first()
        self.state["items"][0]["start_report"] = None
        self.assert_bad("PASS_MISSING_USER_START_REPORT")

    def test_pass_without_user_end_report_rejected(self):
        self.pass_first()
        self.state["items"][0]["end_report"] = None
        self.assert_bad("PASS_MISSING_USER_END_REPORT")

    def test_progress_requires_start_user_report(self):
        self.state["items"][0]["status"] = "IN_PROGRESS"
        self.assert_bad("IN_PROGRESS_MISSING_USER_START_REPORT")

    def test_fail_blocks_successor_but_failing_itself_is_a_valid_state(self):
        row = self.state["items"][0]
        row.update(status="FAIL", failure_reason="CI regression", remediation="fix and retest")
        row["start_report"] = self.report(row, "START")
        row["end_report"] = self.report(row, "FAIL")
        self.assertEqual([], validate(self.catalog, self.state))
        self.state["items"][1]["status"] = "READY"
        self.assert_bad("OUT_OF_ORDER_PROGRESS")

    def test_hold_must_record_reason_and_remediation(self):
        row = self.state["items"][0]
        row.update(status="HOLD", failure_reason="Missing SRT", remediation="")
        row["start_report"] = self.report(row, "START")
        row["end_report"] = self.report(row, "HOLD")
        self.assert_bad("FAIL_HOLD_MISSING_REMEDIATION")

    def test_failed_reopen_requires_remediation(self):
        row = self.state["items"][0]
        row.update(status="HOLD", failure_reason="Missing source", remediation="secure source")
        row["start_report"] = self.report(row, "START")
        row["end_report"] = self.report(row, "HOLD")
        prev = copy.deepcopy(self.state)
        self.pass_first()
        self.state["items"][0]["remediation"] = None
        self.assert_bad("FAILED_ITEM_REOPENED_WITHOUT_REMEDIATION", prev)

    def test_malformed_previous_pass_report_is_red_and_later_mutation_is_red(self):
        # Reproduces P0-0-05 missing baseline_sha without allowing a hidden rewrite.
        self.pass_first()
        previous = copy.deepcopy(self.state)
        previous['items'][0]['start_report'].pop('baseline_sha')
        previous['items'][0]['end_report'].pop('baseline_sha')
        old_errors = validate(self.catalog, previous)
        self.assertTrue(any('PASS_MISSING_USER_START_REPORT' in x for x in old_errors))
        self.assertTrue(any('PASS_MISSING_USER_END_REPORT' in x for x in old_errors))
        repair_errors = validate(self.catalog, self.state, previous=previous)
        self.assertTrue(any('PREVIOUS_PASS_MUTATED' in x for x in repair_errors))
        # The immutable guard remains ON; next commit must not modify the state.
    def test_previous_pass_must_not_be_rewritten(self):
        self.pass_first()
        prev = copy.deepcopy(self.state)
        self.state["items"][0]["evidence"][0]["sha"] = "b" * 40
        self.assert_bad("PREVIOUS_PASS_MUTATED", prev)

    def test_reopen_two_items_in_one_commit_not_allowed(self):
        prev = copy.deepcopy(self.state)
        self.pass_first()
        self.state["items"][1]["status"] = "IN_PROGRESS"
        self.state["items"][1]["start_report"] = self.report(self.state["items"][1], "START")
        self.assert_bad("NEXT_UNLOCK_WITHOUT_PREVIOUS_PASS", prev)

    def test_wrong_kind_cannot_pass(self):
        self.pass_first()
        self.state["items"][0]["evidence"][0]["kind"] = "official"
        self.assert_bad("PASS_MISSING_VERIFIABLE_REQUIRED_EVIDENCE")

    def test_other_project_evidence_url_rejected(self):
        self.pass_first()
        self.state["items"][0]["evidence"][0]["ref"] = "https://github.com/other/repo/actions/1"
        self.assert_bad("PASS_MISSING_VERIFIABLE_REQUIRED_EVIDENCE")

    def test_turn2_requires_actual_user_ref_fields(self):
        evidence = self.evidence(0, kind="turn2")
        self.assertFalse(validate.__globals__["valid_evidence"](evidence, "turn2", None))
        evidence.update(turn1_ref="user-turn-1", turn2_user_message_ref="user-turn-2",
                        authentication_level="HOST_SIGNATURE_NOT_AVAILABLE")
        self.assertTrue(validate.__globals__["valid_evidence"](evidence, "turn2", None))

    def test_publication_requires_exactly_once_receipt_fields(self):
        evidence = self.evidence(0, kind="publication")
        self.assertFalse(validate.__globals__["valid_evidence"](evidence, "publication", None))
        evidence.update(publication_id="parent:123", knowledge_head="c" * 40, publication_delta="1")
        self.assertTrue(validate.__globals__["valid_evidence"](evidence, "publication", None))


if __name__ == "__main__":
    unittest.main()
