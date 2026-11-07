"""One-turn research completion is separate from independent approval."""
from __future__ import annotations
import copy
import unittest
from pathlib import Path

from ire.v5.one_turn_resolution_gate import FinalizationError,verify,load

ROOT=Path(__file__).resolve().parents[3]
FILE=ROOT/"ire/v5/advisory_knowledge/one_turn33_20261104/decisions.json"

class OneTurnThirtyThreeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=load(FILE)

    def mutated(self,cb):
        data=copy.deepcopy(self.d)
        cb(data)
        return verify(ROOT,data)

    def test_exactly_53_claims_accounted_for_no_more_progress_prompts(self):
        v=verify(ROOT)
        self.assertEqual(v["original_new_claims"],53)
        self.assertEqual(v["prior_high_risk_claims"],9)
        self.assertEqual(v["this_turn_claims_terminated"],33)
        self.assertEqual(v["historical_or_excluded_claims"],11)
        self.assertEqual(v["claims_without_disposition"],0)
        self.assertEqual(v["conditional_product_personal_claims"],19)
        self.assertEqual(v["numeric_asr_claims_context_reconciled"],2)
        self.assertEqual(v["education_candidates_public_source_crosschecked"],12)
        self.assertEqual(v["new_nonduplicated_education_concepts"],9)
        self.assertEqual(v["total_provisional_scoped_education_concepts"],13)
        self.assertFalse(v["formal_personalized_financial_advice_go"])

    def test_missing_claim_fails_not_marked_complete(self):
        with self.assertRaisesRegex(FinalizationError,"RESEARCH_DID_NOT_COMPLETE_ALL_33"):
            self.mutated(lambda d:d["cases"].pop())

    def test_known_claim_cannot_replace_another_video(self):
        with self.assertRaisesRegex(FinalizationError,"ORIGINAL_CUE_OR_CLAIM_MISMATCH"):
            self.mutated(lambda d:d["cases"][0].update(video_id="tDD5GzvDYq8"))

    def test_official_publisher_references_cannot_be_fabricated(self):
        with self.assertRaisesRegex(FinalizationError,"MISSING_OFFICIAL_REFERENCE"):
            self.mutated(lambda d:d["cases"][0].update(official_reference_ids=["SOURCE-NOT-IN-CATALOG"]))

    def test_author_independence_required_for_educational_candidate(self):
        def change(d):
            edu=next(x for x in d["cases"] if x["claim_id"]=="E229-01")
            edu["official_reference_ids"]=["KRX-ETF","KRX-PRICE-NAV"]
        with self.assertRaisesRegex(FinalizationError,
                                    "EDUCATION_NOT_CHECKED_AGAINST_INDEPENDENT_PUBLISHERS"):
            self.mutated(change)

    def test_false_personal_advice_approval_fails(self):
        with self.assertRaisesRegex(FinalizationError,"UNREVIEWED_FACT_FALSELY_PROMOTED"):
            self.mutated(lambda d:d["cases"][0].update(personal_action_release=True))

    def test_false_blind_human_grade_fails(self):
        with self.assertRaisesRegex(FinalizationError,"SINGLE_TURN_FICTITIOUS_APPROVAL"):
            self.mutated(lambda d:d.update(external_human_blind_review_completed=True))

    def test_source_audio_not_claimed_authenticated(self):
        def change(d):
            n=next(x for x in d["cases"] if x["claim_id"]=="P217-04")
            n["original_audio_authenticated"]=True
        with self.assertRaisesRegex(FinalizationError,
                                    "NUMERIC_ASR_AUDIO_UNSUPPORTED_CERTIFICATION"):
            self.mutated(change)

    def test_asr_cue_177_error_is_explicit(self):
        d=next(x for x in self.d["cases"] if x["claim_id"]=="P217-04")
        self.assertEqual(d["arithmetic"]["erroneous_asr_cue"],177)
        self.assertEqual(d["arithmetic"]["total_10k_krw"],8400)
        self.assertFalse(d["original_audio_authenticated"])

    def test_isa_dividend_scenario_only_arithmetic(self):
        d=next(x for x in self.d["cases"] if x["claim_id"]=="I255-06")
        self.assertEqual(d["arithmetic"]["principal_krw"],1000000)
        self.assertEqual(d["arithmetic"]["assumed_next_dividend_krw"],100000)
        self.assertIn("가정",d["scoped_general_conclusion"])
        self.assertFalse(d["personal_action_release"])

    def test_historical_2025_fee_ranking_stays_excluded(self):
        ids={x["claim_id"] for x in self.d["cases"]}
        self.assertNotIn("E229-06",ids)
        self.assertNotIn("A237-08",ids)

    def test_33_source_spans_have_frozen_recomputed_hashes(self):
        self.assertEqual(self.d["original_span_integrity_fnv64"],"98fff0509406a4fe")
        self.assertEqual(len({x["original_span_sha256"] for x in self.d["cases"]}),33)

if __name__=="__main__":
    unittest.main()
