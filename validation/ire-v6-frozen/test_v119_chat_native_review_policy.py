"""V119 current ChatGPT reviewer governance policy: documents, no fictitious independent gold."""
import json
import unittest
from pathlib import Path

BASE=Path(__file__).resolve().parent
def policy():
    return json.loads((BASE/"V119_CHAT_NATIVE_REVIEW_POLICY.json").read_text(encoding="utf-8"))

class ChatNativePolicy(unittest.TestCase):
    def test_01_chat_is_actual_executor(self):
        self.assertEqual(policy()["user_selected_review_executor"], "CHATGPT_IN_CHAT")
    def test_02_no_external_humans_required(self):
        p=policy()
        self.assertEqual(p["external_human_reviewers_required_for_chat_native_research"],0)
        self.assertEqual(p["external_adjudicators_required_for_chat_native_research"],0)
        self.assertIs(p["external_identity_authority_required_for_chat_native_research"],False)
    def test_03_model_api_not_required(self):
        self.assertIs(policy()["additional_model_api_required"],False)
    def test_04_chat_can_proceed_without_external_gold(self):
        self.assertIs(policy()["chat_native_research_may_proceed_without_external_gold"],True)
        self.assertIs(policy()["legacy_external_certification_optional"],True)
    def test_05_same_chat_not_externally_independent(self):
        self.assertIs(policy()["same_chat_two_pass_is_externally_independent"],False)
        self.assertEqual(policy()["blindness_if_prior_predictions_visible"],"BLIND_NOT_ESTABLISHED")
    def test_06_separate_reference_and_scores(self):
        p=policy()
        self.assertEqual(p["chat_reference_label"],"CHAT_ADJUDICATED_REFERENCE")
        self.assertEqual(p["internal_score_label"],"CHAT_INTERNAL_REFERENCE_SCORE")
    def test_07_source_first_and_disagreement_required(self):
        p=policy()
        self.assertEqual(len(p["chat_review_stages"]),6)
        self.assertIn("CHAT_SOURCE_FIRST_PASS_A",p["chat_review_stages"])
        self.assertIn("CHAT_COUNTEREXAMPLE_PASS_B",p["chat_review_stages"])
        self.assertIn("CHAT_DISAGREEMENT_ADJUDICATION_AND_OPEN",p["chat_review_stages"])
    def test_08_no_fake_accuracy(self):
        p=policy()
        for name in ("actual_chat_internal_reference_precision","actual_chat_internal_reference_recall",
                     "actual_chat_internal_reference_high_risk_recall","independently_certified_precision",
                     "independently_certified_recall","independently_certified_high_risk_recall"):
            self.assertIsNone(p[name])
        self.assertIs(p["gold_and_scoring_not_yet_executed"],True)
    def test_09_no_false_go_or_fact_approval(self):
        p=policy()
        self.assertIs(p["p0_go"],False)
        self.assertEqual(p["finance_facts_approved_now"],0)
    def test_10_keep_legacy_history_immutable(self):
        p=policy()
        self.assertIs(p["legacy_source_and_gold_receipts_rewrite_forbidden"],True)
        self.assertTrue(any("V103_" in z for z in p["historical_external_only_policy_paths"]))
        self.assertTrue(any("V107_" in z for z in p["historical_external_only_policy_paths"]))
    def test_11_prior_v109_agreement(self):
        former=json.loads((BASE/"V109_CHAT_ONLY_EVALUATION_RELEASE_POLICY.json").read_text(encoding="utf-8"))
        self.assertIs(former["external_reviewers_required_for_chat_native_research"],False)
        self.assertEqual(former["user_decision"],"CHAT_ONLY_NO_EXTERNAL_REVIEWER_OR_MODEL_API_REQUIRED")
    def test_12_corrected_document_links(self):
        for fn in ("V107_EXTERNAL_GOLD_READINESS_AND_ROOT_SECURITY_REPORT.md",
                   "V6_V108_SAME_CHAT_SOURCE_FIRST_TWO_PASS_160_CUE_63_PARENT_18_REVISIONS_NO_GOLD_REPORT.md",
                   "V6_V118_41_FINANCE_OPEN_TRIAGE_AND_INDEPENDENT_GOLD_INTAKE_REPORT.md"):
            src=(BASE/fn).read_text(encoding="utf-8")
            self.assertIn("V119_CHAT_NATIVE_REVIEW_GOVERNANCE.md",src,fn)
            self.assertIn("채팅",src,fn)
    def test_13_policy_and_prose_consistency(self):
        body=(BASE/"V119_CHAT_NATIVE_REVIEW_GOVERNANCE.md").read_text(encoding="utf-8")
        self.assertIn("CHAT_INTERNAL_REFERENCE_SCORE",body)
        self.assertIn("통계적으로 독립된 제3자",body)
        self.assertIn("외부 인간 검토자",body)
        self.assertIn("NO_SCORE",body)
        self.assertIn("P0",body)
    def test_14_private_transcripts_not_exported(self):
        self.assertIs(policy()["source_data_or_private_transcript_in_public_repo"],False)
    def test_15_protected_branches_untouched(self):
        p=policy()
        self.assertIs(p["main_modified"],False)
        self.assertIs(p["v5_or_master116_or_p4_modified"],False)

if __name__=="__main__":unittest.main()
