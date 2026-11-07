"""Regression tests of 44 source-grounded, non-advisory financial assessments."""
import copy
import tempfile
import unittest
from pathlib import Path

from ire.v5.review44_gate import (
    Review44Error, normalized_cues, read, verify,
)

ROOT=Path(__file__).resolve().parents[3]
FILE=ROOT/"ire/v5/advisory_knowledge/review44_20261104/triage.json"

class Remaining44TriageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline=read(FILE)

    def mutate(self,fn):
        candidate=copy.deepcopy(self.baseline)
        fn(candidate)
        return verify(ROOT,review=candidate)

    def test_all_44_legacy_links_and_dispositions_are_reproducible(self):
        r=verify(ROOT)
        self.assertEqual(r["original_source_claims_addressed"],44)
        self.assertEqual(r["education_candidates_nonblind"],12)
        self.assertEqual(r["claims_requiring_further_context_or_evidence"],21)
        self.assertEqual(r["historical_only"],8)
        self.assertEqual(r["unsafe_generalizations_blocked"],1)
        self.assertEqual(r["outside_investment_scope"],2)
        self.assertEqual(r["independent_financial_fact_approvals"],0)
        self.assertFalse(r["personalized_investment_advice_go"])
        self.assertEqual(r["original_claim_spans_byte_reverified_this_run"],0)

    def test_not_an_independent_blind_evaluation(self):
        self.assertFalse(self.baseline["human_blind_reference_labels_present"])
        with self.assertRaisesRegex(Review44Error,
                                    "REVIEW44_UNAUTHORIZED_BLIND_OR_ADVISORY_APPROVAL"):
            self.mutate(lambda x:x.update(human_blind_reference_labels_present=True))

    def test_no_unverified_advice_promotion(self):
        with self.assertRaisesRegex(Review44Error,
                                    "REVIEW44_FABRICATED_APPROVAL_OR_PROVENANCE"):
            self.mutate(lambda x:x["records"][0].update(
                individual_investment_advice_approved=True))

    def test_missing_claim_is_not_hidden(self):
        with self.assertRaisesRegex(Review44Error,"REVIEW44_RECORD_COUNT_MISMATCH"):
            self.mutate(lambda x:x["records"].pop())

    def test_old_approved_claim_is_not_reviewed_twice(self):
        with self.assertRaisesRegex(Review44Error,
                                    "REVIEW44_DUPLICATE_OR_PREVIOUSLY_ASSESSED_CLAIM"):
            self.mutate(lambda x:x["records"][0].update(claim_id="I255-03"))

    def test_fake_source_hash_is_rejected(self):
        with self.assertRaisesRegex(Review44Error,
                                    "REVIEW44_SOURCE_PROVENANCE_CHANGED"):
            self.mutate(lambda x:x["records"][0].update(
                original_cue_span_sha256="x"*64))

    def test_legacy_claim_text_cannot_be_rewritten(self):
        with self.assertRaisesRegex(Review44Error,
                                    "REVIEW44_LEGACY_CONTEXT_OR_MEANING_CHANGED"):
            self.mutate(lambda x:x["records"][0].update(
                source_paraphrase="새로운 출처 없는 확정 주장으로 교체한다."))

    def test_critical_rebalance_hazard_cannot_be_promoted(self):
        def f(x):
            next(z for z in x["records"] if z["claim_id"]=="A237-08")[
                "disposition"]="EDUCATION_CANDIDATE"
        with self.assertRaisesRegex(Review44Error,
                                    "REVIEW44_HAZARDOUS_CLAIM_UNSAFE_PROMOTION"):
            self.mutate(f)

    def test_education_candidate_requires_real_independent_source(self):
        def f(x):
            next(z for z in x["records"] if z["claim_id"]=="P217-03")[
                "official_reference_ids"]=[]
        with self.assertRaisesRegex(Review44Error,
                                    "REVIEW44_UNSUPPORTED_EDUCATION_PROMOTION"):
            self.mutate(f)

    def test_future_law_effective_date_is_invalid(self):
        with self.assertRaisesRegex(Review44Error,
                                    "REVIEW44_FUTURE_LEGAL_EFFECTIVE_DATE"):
            self.mutate(lambda x:x["external_authorities"][0].update(
                legal_effective_from="2027-01-01"))

    def test_cannot_publish_private_srt_or_claim_it_is_in_ci(self):
        test_srt=(b"1\n00:00:00,000 --> 00:00:01,000\nhello\n\n"
                  b"2\n00:00:01,001 --> 00:00:02,000\nworld\n")
        self.assertEqual([x["cue"] for x in normalized_cues(test_srt).values()],
                         [1,2])
        with tempfile.NamedTemporaryFile(suffix=".zip") as t:
            t.write(b"not-a-private-SRT-ZIP")
            t.flush()
            with self.assertRaisesRegex(Review44Error,
                                        "REVIEW44_PRIVATE_ZIP_HASH_MISMATCH"):
                verify(ROOT,private_zip=Path(t.name))

if __name__=="__main__":
    unittest.main()
