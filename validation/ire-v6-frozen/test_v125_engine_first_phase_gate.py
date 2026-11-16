"""Engine-first/portfolio-after-completion regression. No private data."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from v125_engine_first_phase_gate import audit_engine_first_policy

class EngineFirstCompletionGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy=json.loads((ROOT/"V125_ENGINE_FIRST_PORTFOLIO_DEFERRED_POLICY.json").read_text(encoding="utf-8"))
        cls.doc=(ROOT/"V6_V125_ENGINE_FIRST_REQUIREMENTS_AND_PHASE_ORDER.md").read_text(encoding="utf-8")
    def test_requirements_and_no_false_go(self):
        result=audit_engine_first_policy(self.policy)
        self.assertEqual(result["engine_requirements_count"],10)
        self.assertEqual(result["engine_requirements_open"],10)
        self.assertFalse(result["engine_completed"])
        self.assertFalse(result["new_video_research_allowed"])
        self.assertFalse(result["portfolio_integration_allowed"])
    def test_chat_review_and_knowledge_accumulation_both_required(self):
        self.assertIn("ChatGPT 최종",self.doc)
        self.assertIn("누적 지식",self.doc)
        self.assertIn("Phase E",self.doc)
        self.assertIn("Phase R",self.doc)
        self.assertIn("Phase P",self.doc)
        self.assertFalse(self.policy["external_model_api_required"])
    def test_cannot_advance_to_portfolio_or_new_videos(self):
        for key in ("completed_engine","portfolio_integration_implementation_authorized",
                    "further_video_research_authorized","p0_go"):
            changed=copy.deepcopy(self.policy)
            changed[key]=True
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,"UNAUTHORIZED_PHASE_OR_RELEASE"):
                audit_engine_first_policy(changed)
    def test_priority_drift_rejected(self):
        p=copy.deepcopy(self.policy)
        p["user_approved_order"][1]="PORTFOLIO_DRIVE_INTEGRATION"
        with self.assertRaisesRegex(ValueError,"ORDER_BROKEN"):
            audit_engine_first_policy(p)
    def test_cannot_mark_single_engine_requirement_done(self):
        p=copy.deepcopy(self.policy)
        p["engine_completion_requirements"]["knowledge_question_retrieval_with_provenance"]="PASS"
        with self.assertRaisesRegex(ValueError,"FALSE_COMPLETION"):
            audit_engine_first_policy(p)
if __name__=="__main__":
    unittest.main()
