"""Deterministic 53-claim safety rehearsal; NOT an independent model exam."""
import unittest
from pathlib import Path
from ire.v5 import advisory_education_rehearsal as policy

ROOT=Path(__file__).resolve().parents[3]

class AdvisoryEducationRehearsalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=policy.create_policy(ROOT)

    def test_all_fifty_three_original_claims_are_routed(self):
        r=policy.audit(ROOT)
        self.assertEqual(r["source_claims_checked"],53)
        self.assertEqual(r["structured_education_claims_available"],17)
        self.assertEqual(r["other_claims_rejected_for_education"],36)
        self.assertEqual(r["personalized_action_requests_refused"],53)
        self.assertEqual(r["new_and_existing_education_concepts"],13)
        self.assertFalse(r["real_personalized_investment_advice_approved"])

    def test_tax_isa_general_education_has_source_and_type_change_warning(self):
        r=policy.apply(self.p,"I255-03","general_education")
        self.assertEqual(r["decision"],"GENERAL_EDUCATION_WITH_SCOPE_ONLY")
        self.assertTrue(any("ISA" in x for x in r["safe_general_statements"]))
        self.assertTrue(any("law.go.kr" in x for x in r["official_reference_urls"]))
        self.assertIn("HOLD_CONTEXT",r["context_specific_warnings"])
        self.assertFalse(r["personal_advice_approved"])

    def test_pension_55_5_has_two_video_supports(self):
        r1=policy.apply(self.p,"P217-03","general_education")
        r2=policy.apply(self.p,"R250-07","general_education")
        self.assertEqual(r1["decision"],"GENERAL_EDUCATION_WITH_SCOPE_ONLY")
        self.assertEqual(r1["knowledge_ids"],r2["knowledge_ids"])
        self.assertEqual(r1["knowledge_ids"],["EDU-KR-PENSION-55-5"])

    def test_nonapproved_numeric_asr_claim_not_leaked(self):
        r=policy.apply(self.p,"P217-04","general_education")
        self.assertEqual(r["decision"],"NOT_RELEASED_AS_EDUCATION")
        self.assertIn("NUMERIC_OR_ASR_OPEN",r["review_statuses"])

    def test_no_outdated_2025_etf_ranking_promoted(self):
        r=policy.apply(self.p,"E229-06","general_education")
        self.assertEqual(r["decision"],"NOT_RELEASED_AS_EDUCATION")
        self.assertIn("HISTORICAL_ONLY",r["review_statuses"])

    def test_no_unconditional_dca_profit_promise(self):
        r=policy.apply(self.p,"A237-05","general_education")
        self.assertEqual(r["decision"],"NOT_RELEASED_AS_EDUCATION")
        self.assertIn("BLOCK_UNSAFE_PROJECTION",r["review_statuses"])

    def test_no_personal_etf_portfolio_directive(self):
        r=policy.apply(self.p,"A237-01","personal_action")
        self.assertEqual(r["decision"],"REFUSE_PERSONALIZED_ADVICE")
        self.assertEqual(len(r["missing_checks"]),4)
        self.assertFalse(r["personal_advice_approved"])

    def test_pension_tax_answer_does_not_authorize_withdrawal(self):
        r=policy.apply(self.p,"P217-07","personal_action")
        self.assertEqual(r["decision"],"REFUSE_PERSONALIZED_ADVICE")
        self.assertTrue(r["verified_public_education_available"])

    def test_guaranteed_return_query_refused_even_for_approved_education(self):
        for cid in ("A237-04","A237-03","P217-07","E229-01"):
            with self.subTest(claim=cid):
                self.assertEqual(policy.apply(
                    self.p,cid,"guaranteed_return")["decision"],
                    "REFUSE_PROFIT_OR_LOSS_GUARANTEE")

    def test_unknown_claim_does_not_get_best_effort_fake_citation(self):
        r=policy.apply(self.p,"INVENTED-999","general_education")
        self.assertEqual(r["decision"],"REFUSE_UNKNOWN_CLAIM")
        self.assertNotIn("official_reference_urls",r)

    def test_unknown_intent_is_not_assumed_to_be_education(self):
        with self.assertRaisesRegex(policy.AdvisoryAccessError,
                                    "UNKNOWN_QUERY_INTENT_FAIL_CLOSED"):
            policy.apply(self.p,"I255-03","act_without_confirmation")

if __name__=="__main__":
    unittest.main()
