"""Prevent silent removal of mandatory V5 preflight steps from local or CI."""
import unittest

from ire.v5.preflight import planned_checks


class PreflightContractTests(unittest.TestCase):
    def test_same_full_ordered_checks_for_local_and_ci(self):
        steps=planned_checks()
        names=[name for name,_ in steps]
        self.assertEqual(names,[
            "compile_v5",
            "video_id_reconciliation",
            "no_unreviewed_pilot_promotion",
            "advisory_replay_safety",
            "twenty_plus_five_intake",
            "five_original_source_studies",
            "provisional_knowledge_reconciliation",
            "independent_authority_crosscheck",
            "deduplicated_education_safety",
            "remaining_44_source_triage",
            "single_turn_final_33_research_verdicts",
            "integrated_thirteen_education_topics",
            "advisory_access_rehearsal_53_claims",
            "unseen_original_video_full_research_and_reconcile",
            "unseen_video_incremental_knowledge_reconciliation",
            "second_unseen_video_full_source_temporal_gate",
            "fine_grained_ipo_semantic_and_current_law_recheck",
            "user_approved_chat_source_scoped_fact_gate",
            "first_three_legacy_reconciliation_batches_60_and_master_116",
            "sixty_legacy_claim_advisory_decision_support",
            "new_chat_unseen_advisory_routing_official_scope_and_arithmetic",
            "all_v5_regression_tests",
        ])
        self.assertEqual(len(names),len(set(names)))
        self.assertIn("test_*.py",steps[-1][1])
        self.assertEqual(steps[-1][1][:4],(
            "-m","unittest","discover","-s"))

    def test_preflight_is_fail_closed(self):
        import inspect
        from ire.v5.preflight import run
        source=inspect.getsource(run)
        self.assertIn("result.returncode",source)
        self.assertIn("return result.returncode",source)
        self.assertNotIn("check=False) or",source)
