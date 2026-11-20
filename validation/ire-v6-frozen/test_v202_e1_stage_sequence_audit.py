"""E1 stage ledger regression: historical failed versions remain, latest E1 PASS.

Tests must disallow fabricated stage-advancement or CI-only overclaims.
"""
from __future__ import annotations
import json
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
STATUS=HERE/"V202_E1_E5_CURRENT_ROUTE_SEQUENCE_STATUS.json"
NEW_REPORT=HERE/"V203_E1_REAL_V176_ORIGIN_TO_NATIVE_V128_STRUCTURAL_PASS_20261120.md"
FAIL_REPORT=HERE/"V202_E1_INDEPENDENT_REAUDIT_FAIL_20261120.md"
OLD_PASS_REPORT=HERE/"V202_E1_CURRENT_V176_ROUTE_STRUCTURAL_PASS_20261120.md"


class TestCurrentE1SequenceStatus(unittest.TestCase):
    def setUp(self):
        self.data=json.loads(STATUS.read_text(encoding="utf-8"))

    def test_01_preserve_old_v166_pass_and_v202_fail_without_faking_history(self):
        self.assertIs(self.data["historical_v166_e1_pass_preserved"],True)
        self.assertEqual(self.data["current_step"],"E2_READY_NOT_STARTED")
        self.assertEqual(self.data["sequence"][0]["status"],"PASS")
        self.assertTrue(self.data["current_e1_verdict"].startswith("PASS_V203_"))
        self.assertTrue(self.data["e1_evidence"]["prior_v202_false_pass_retracted"])

    def test_02_following_stages_stay_unstarted_until_separately_verified(self):
        self.assertEqual([s["step"] for s in self.data["sequence"]],
                         ["E1","E2","E3","E4","E5"])
        self.assertEqual(self.data["sequence"][1]["status"],
                         "READY_NOT_STARTED_CURRENT_ROUTE")
        self.assertTrue(all(
            x["status"]=="NOT_RUN_CURRENT_ROUTE"
            for x in self.data["sequence"][2:]))

    def test_03_proof_is_actual_v176_host_origin_not_preseeded(self):
        e=self.data["e1_evidence"]
        self.assertIs(e["exact_owner_journal_derived_native_exchange"],True)
        self.assertIs(e["native_child_host_bundles_newly_committed_from_v176"],True)
        self.assertIs(e["original_v166_preseed_host_not_reused"],True)
        self.assertIs(e["frozen_v126_exact_host_replay_invoked"],True)
        self.assertEqual(e["original_v176_owner_cues"],4)
        self.assertEqual(e["original_v176_source_atoms"],3)
        self.assertEqual(e["native_child_scope_count"],2)
        self.assertEqual(e["positive_synthetic_sqlite_added"],
                         {"events":2,"knowledge":2,"parent_publications":1})
        self.assertEqual(e["evidence_ci_total_tests"],413)

    def test_04_adversarial_old_red_and_new_pass_both_preserved(self):
        self.assertTrue(NEW_REPORT.is_file())
        self.assertTrue(FAIL_REPORT.is_file())
        old=OLD_PASS_REPORT.read_text(encoding="utf-8")
        self.assertIn("판정은 **철회**",old)
        new=NEW_REPORT.read_text(encoding="utf-8")
        self.assertIn("V202_E1_INDEPENDENT_REAUDIT_FAIL",new)
        self.assertIn("413 / 413",new)

    def test_05_no_misleading_claim_of_real_chat_quality_or_finance_approval(self):
        e=self.data["e1_evidence"]
        self.assertFalse(e["native_financial_fact_approved"])
        self.assertFalse(e["real_owner_original_srt_runtime_confirmed"])
        self.assertFalse(e["real_13_child_video_knowledge_published"])
        self.assertFalse(e["independent_semantic_gold_certified"])
        self.assertEqual(self.data["protected"]["real_financial_knowledge_published"],0)
        self.assertTrue(self.data["protected"]["main_unchanged"])
        self.assertFalse(self.data["protected"]["owner_private_source_published"])


if __name__=="__main__":
    unittest.main()
