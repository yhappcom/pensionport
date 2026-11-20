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
                         "E2_REAL_ORIGINAL_FIRST_PASS_COMPLETED_HOLD_LIVE_OWNER_GOLD")
        self.assertTrue(self.status["current_e2_verdict"].startswith("HOLD_"))

    def test_02_real_source_and_gold_not_falsely_certified(self):
        e=self.status["e2_evidence"]
        self.assertTrue(e["original_full_cue_census_implemented"])
        self.assertTrue(e["private_sqlite_hashchain_resume_and_idempotency_tested"])
        self.assertTrue(e["real_owner_srt_bytes_available_in_current_runtime"])
        self.assertFalse(e["real_13_segment_e2_review_completed"])
        self.assertFalse(e["independent_real_semantic_gold_certified"])
        self.assertFalse(e["native_fact_correction_and_relations_transferred"])
        self.assertEqual(e["knowledge_published"],0)

    def test_03_e3_e4_e5_stay_not_run_no_premature_release(self):
        self.assertEqual(self.status["sequence"][1]["status"],
                         "IN_PROGRESS_HOLD_LIVE_OWNER_AND_GOLD")
        self.assertEqual([x["status"] for x in self.status["sequence"][2:]],
                         ["NOT_RUN_CURRENT_ROUTE"]*3)
        self.assertTrue(E2_REPORT.is_file())
        txt=E2_REPORT.read_text(encoding="utf-8")
        self.assertIn("104/104",txt)
        self.assertIn("HOLD_REAL_SOURCE_AND_INDEPENDENT_GOLD",txt)


    def test_04_v208_repairs_persist_but_e2_semantics_not_certified(self):
        e=self.status["e2_evidence"]
        self.assertTrue(e["v208_private_source_review_repair_chain_tested"])
        self.assertTrue(e["v208_source_review_before_repair_enforced"])
        self.assertTrue(e["v208_private_restart_idempotent_replay_tested"])
        self.assertTrue(e["v208_malformed_hash_rejected_without_runtime_exception"])
        self.assertTrue(e["v208_cross_census_temporal_history_check_tested"])
        self.assertTrue(e["v208_real_srt_private_resume_not_tested"])
        self.assertEqual(e["ci_total_tests"],195)
        self.assertEqual(e["ci_current_e2_tests"],124)
        self.assertEqual(e["ci_existing_e2_and_e1_regression"],71)
        self.assertTrue((ROOT/"V208_E2_PRIVATE_SOURCE_REPAIR_CHAIN_AND_CONTINUATION_HOLD_20261120.md").is_file())
        self.assertFalse(e["independent_real_semantic_gold_certified"])
        self.assertFalse(e["e2_semantic_accuracy_approved"])


    def test_05_verified_real_srt_changes_source_access_not_independent_gold(self):
        e=self.status["e2_evidence"]
        self.assertTrue(e["real_owner_srt_bytes_loaded_in_chat_private_runtime"])
        self.assertFalse(e["real_owner_srt_bytes_available_in_github_ci"])
        self.assertEqual(e["real_etf_video_id"],"LVE7XN_esTc")
        self.assertEqual(e["real_etf_cues_verified"],250)
        self.assertEqual(e["real_etf_candidate_draft_count"],57)
        self.assertEqual(e["real_etf_candidate_flagged_count"],47)
        self.assertTrue(e["real_etf_250_cues_accounted_by_span_or_nonclaim"])
        self.assertTrue(e["real_etf_private_draft_saved_in_user_library"])
        self.assertFalse(e["real_etf_live_v176_owner_sqlite_accessible"])
        self.assertFalse(e["real_etf_v179_61_provisional_claims_semantically_reconciled"])
        self.assertFalse(e["independent_real_semantic_gold_certified"])
        self.assertFalse(e["e2_semantic_accuracy_approved"])
        self.assertTrue((ROOT/"V210_E2_REAL_ETF_250_CUES_SOURCE_FIRST_57_DRAFT_HOLD_20261120.md").is_file())


if __name__=="__main__":
    unittest.main()
