"""One-turn engine issues a research receipt only after all checks pass."""
import contextlib
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from ire.v5 import one_turn_run

ROOT=Path(__file__).resolve().parents[3]

class SingleRequestOrchestratorTests(unittest.TestCase):
    def test_real_one_turn_all_gates_emit_terminal_receipt(self):
        output=io.StringIO()
        with patch.object(one_turn_run,"preflight_run",return_value=0) as p, \
             contextlib.redirect_stdout(output):
            rc=one_turn_run.run(ROOT)
        self.assertEqual(rc,0)
        p.assert_called_once()
        row=output.getvalue().split("ONE_TURN_RESEARCH_RECEIPT ",1)[1]
        payload=json.loads(row)
        self.assertTrue(payload["one_request_research_complete"])
        self.assertFalse(payload["repeat_user_progress_command_required"])
        self.assertEqual(payload["claims"]["claims_without_disposition"],0)
        self.assertEqual(payload["education_knowledge"]["knowledge_concepts"],13)
        self.assertEqual(payload["advisory_access_rehearsal"]["source_claims_checked"],53)
        self.assertEqual(payload["new_video_vertical_slice"]["source_cues_full_video_covered"],214)
        self.assertEqual(payload["new_video_vertical_slice"]["source_claims_extracted_and_checked"],13)
        self.assertEqual(payload["new_video_vertical_slice"]["new_knowledge_provisional_only"],3)
        self.assertEqual(payload["new_video_incremental_merge"]["original_video_claims_reconciled"],13)
        self.assertEqual(payload["new_video_incremental_merge"]["new_approved_tax_topics"],0)
        self.assertFalse(payload["new_video_vertical_slice"]["personalized_investment_advice_approved"])
        self.assertEqual(payload["advisory_access_rehearsal"]["other_claims_rejected_for_education"],36)
        self.assertEqual(payload["second_unseen_video_full_research"]["source_cues_covered"],185)
        self.assertEqual(payload["second_unseen_video_full_research"]["anchored_material_claims"],12)
        self.assertFalse(payload["second_unseen_video_full_research"]["personal_advice_approved"])
        self.assertEqual(payload["second_unseen_video_semantic_evidence_recheck"]["rechecked_semantic_units"],22)
        self.assertFalse(payload["second_unseen_video_semantic_evidence_recheck"]["financial_fact_certified"])
        self.assertEqual(payload["source_scoped_chat_researched_facts"]["fully_accepted_facts"],9)
        self.assertEqual(payload["source_scoped_chat_researched_facts"]["narrowly_accepted_partial_facts"],3)
        self.assertEqual(payload["source_scoped_chat_researched_facts"]["not_accepted_as_facts"],10)
        self.assertFalse(payload["blind_review_required_for_research_fact_acceptance"])
        self.assertEqual(payload["legacy_research_consolidation"]["master_claims_indexed"],116)
        self.assertEqual(payload["legacy_research_consolidation"]["first_batch_claims_integrated"],20)
        self.assertEqual(payload["legacy_research_consolidation"]["second_batch_claims_integrated"],20)
        self.assertEqual(payload["legacy_research_consolidation"]["two_batches_claims_detailed_triaged"],40)
        self.assertEqual(payload["legacy_research_consolidation"]["third_batch_claims_integrated"],20)
        self.assertEqual(payload["legacy_research_consolidation"]["three_batches_claims_detailed_triaged"],60)
        self.assertEqual(payload["legacy_research_consolidation"]["remaining_batches_not_claimed_complete"],3)
        self.assertEqual(payload["sixty_claim_decision_support"]["legacy_claims_traced"],60)
        self.assertEqual(payload["sixty_claim_decision_support"]["decision_domains"],15)
        self.assertEqual(payload["sixty_claim_decision_support"]["question_scenarios_routed"],20)
        self.assertEqual(payload["sixty_claim_decision_support"]["legacy_claims_promoted_to_new_financial_fact"],0)
        self.assertFalse(payload["sixty_claim_decision_support"]["actual_model_advisory_answer_accuracy_test"])
        self.assertFalse(payload["formal_personal_investment_advice_authorized"])
        self.assertFalse(payload["independent_human_blind_evaluation_completed"])

    def test_no_receipt_on_preflight_error(self):
        output=io.StringIO()
        with patch.object(one_turn_run,"preflight_run",return_value=9), \
             contextlib.redirect_stdout(output):
            rc=one_turn_run.run(ROOT)
        self.assertEqual(rc,9)
        self.assertNotIn("ONE_TURN_RESEARCH_RECEIPT {",output.getvalue())
        self.assertIn("NOT_ISSUED",output.getvalue())

    def test_no_external_api_calls_or_fake_blind_approval(self):
        import inspect
        source=inspect.getsource(one_turn_run)
        self.assertNotIn("openai.com/v1",source)
        self.assertIn("ACTIVE_CHAT_HOST_MUST_SUPPLY",source)
        self.assertIn('"formal_personal_investment_advice_authorized":False',source)

if __name__=="__main__":
    unittest.main()
