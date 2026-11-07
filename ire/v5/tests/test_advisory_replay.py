"""Replay 10 current-turn source-checked hypothetical advisory questions and
mutate them to verify that unsafe or ungrounded answers fail closed.

These are developer-authored cases, not independent blind test gold.
"""
import copy
import json
import unittest
from pathlib import Path

from ire.v5.advisory_replay import evaluate,load_legacy,retrieval,ProofError

ROOT=Path(__file__).resolve().parents[3]
FOLDER=ROOT/"ire/v5/advisory_proof"

class AdvisoryProofTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.suite=json.loads((FOLDER/"cases.json").read_text("utf-8"))
        cls.answers=json.loads((FOLDER/"responses.json").read_text("utf-8"))
        cls.legacy=load_legacy(ROOT/"data/claims.jsonl")
        source=json.loads((ROOT/"ire/v5/reviews/4TFtEQxSM38_20261104.json").read_text("utf-8"))
        cls.v5_ids={c["claim_id"] for c in source["claims"]}

    def run_evaluation(self,s=None,a=None):
        return evaluate(s if s is not None else self.suite,
                        a if a is not None else self.answers,
                        self.legacy,self.v5_ids)

    def test_replay_includes_real_baseline_official_checks_and_nonapproval(self):
        result=self.run_evaluation()
        self.assertEqual(result["cases_passed"],10)
        self.assertEqual(result["cases_total"],10)
        self.assertEqual(result["retrieval_recall_at_12"],1.0)
        self.assertGreaterEqual(result["retrieval_gold_refs"],12)
        self.assertGreaterEqual(result["official_url_candidate_uses"],8)
        self.assertFalse(result["independent_human_gold"])
        self.assertFalse(result["real_time_chat_model_reexecution_in_ci"])
        self.assertFalse(result["individualized_investment_advice_approved"])
        self.assertEqual(result["independent_fact_approvals"],0)
        self.assertEqual(result["release"],"BENCHMARK_REPLAY_ONLY_ADVISORY_NO_GO")

    def test_retrieval_uses_question_not_expected_ids(self):
        for c in self.suite["cases"]:
            ranked=retrieval(c["question"],self.legacy)
            self.assertGreaterEqual(len(ranked),1)
            self.assertTrue(set(c["expected_legacy_claim_ids"])<=set(ranked))

    def test_erasing_official_citation_rejected(self):
        answers=copy.deepcopy(self.answers)
        answers["answers"][0]["evidence_ids"]=[]
        with self.assertRaisesRegex(ProofError,"EVIDENCE_CITATION_GAP_OR_FABRICATED"):
            self.run_evaluation(a=answers)

    def test_invented_original_claim_rejected(self):
        answers=copy.deepcopy(self.answers)
        answers["answers"][0]["legacy_claim_ids"].append("GOMHEE-FAKE")
        with self.assertRaisesRegex(ProofError,"UNSUPPORTED_KNOWLEDGE_CITATION"):
            self.run_evaluation(a=answers)

    def test_invented_new_video_claim_rejected(self):
        answers=copy.deepcopy(self.answers)
        answers["answers"][0]["provisional_v5_claim_ids"]=["V5-FAKE"]
        with self.assertRaisesRegex(ProofError,"UNKNOWN_NEW_VIDEO_CLAIM"):
            self.run_evaluation(a=answers)

    def test_missing_legal_caveat_rejected(self):
        answers=copy.deepcopy(self.answers)
        answers["answers"][2]["blockers"]=[]
        with self.assertRaisesRegex(ProofError,"UNRESOLVED_REQUIREMENT_OMITTED"):
            self.run_evaluation(a=answers)

    def test_required_legal_and_numeric_facts_cannot_disappear(self):
        answers=copy.deepcopy(self.answers)
        answers["answers"][3]["answer"]="연금저축 공제는 사람마다 다릅니다. 계좌 정보는 먼저 확인해야 합니다."
        with self.assertRaisesRegex(ProofError,"REQUIRED_CRITICAL_FACT_MISSING"):
            self.run_evaluation(a=answers)

    def test_false_advice_promotion_rejected(self):
        answers=copy.deepcopy(self.answers)
        answers["answers"][6]["advisory_eligible"]=True
        with self.assertRaisesRegex(ProofError,"FALSE_ADVISORY_APPROVAL"):
            self.run_evaluation(a=answers)

    def test_false_personal_trade_release_rejected(self):
        answers=copy.deepcopy(self.answers)
        answers["answers"][6]["personal_action_released"]=True
        with self.assertRaisesRegex(ProofError,"FALSE_ADVISORY_APPROVAL"):
            self.run_evaluation(a=answers)

    def test_guaranteed_return_unsafe_text_rejected(self):
        answers=copy.deepcopy(self.answers)
        answers["answers"][5]["answer"]+=" 따라서 무조건 매수하세요."
        with self.assertRaisesRegex(ProofError,"UNSAFE_ASSERTION"):
            self.run_evaluation(a=answers)

    def test_unchecked_law_effective_date_claim_rejected(self):
        answers=copy.deepcopy(self.answers)
        answers["answers"][4]["rule_effective_date_independently_attested"]=True
        with self.assertRaisesRegex(ProofError,"UNSUPPORTED_LAW_EFFECTIVE_DATE_ATTESTATION"):
            self.run_evaluation(a=answers)

    def test_expired_or_future_web_research_rejected(self):
        suite=copy.deepcopy(self.suite)
        suite["official_evidence"]["SRC-NTS-PENSION"]["observed_date"]="2024-10-31"
        with self.assertRaisesRegex(ProofError,"STALE_OR_FUTURE_EVIDENCE"):
            self.run_evaluation(s=suite)

    def test_forged_independent_human_gold_rejected(self):
        suite=copy.deepcopy(self.suite)
        suite["gold_author"]="EXTERNAL_BLIND_VALIDATOR"
        with self.assertRaisesRegex(ProofError,"FALSE_INDEPENDENT_GOLD_CLAIM"):
            self.run_evaluation(s=suite)

    def test_video_numeric_asr_disposition_cannot_be_promoted(self):
        answers=copy.deepcopy(self.answers)
        answers["answers"][8]["disposition"]="PUBLIC_EDUCATIONAL"
        with self.assertRaisesRegex(ProofError,"DISPOSITION_MISMATCH"):
            self.run_evaluation(a=answers)

    def test_question_has_no_external_model_api_requirement(self):
        self.assertFalse(self.answers["model_api_used"])
        self.assertEqual(self.answers["response_source"],"CHATGPT_SAME_TURN_AUTHORED")

if __name__=="__main__":
    unittest.main()
