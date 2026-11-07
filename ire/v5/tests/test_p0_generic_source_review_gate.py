"""Cross-video regression tests for source-only review receipt safety."""
import hashlib
import unittest
from ire.v5.validation.p0_generic_source_review_gate import validate_source_review, ResearchCoverageError

H=lambda s: hashlib.sha256(s.encode()).hexdigest()
def sample():
    return {"archive_sha256":H("archive"),"source_sha256":H("source"),
            "first_cue":1,"last_cue":2,"reviewed_windows":1,"reviewed_cues":2,
            "next_window":"W00002","research_complete":False,"p0_go":False,"p1_merge":False,
            "windows":[{"window_id":"W00001","first_cue":1,"last_cue":2,"cue_count":2,
                        "disposition":"SOURCE_READ_CANDIDATES_PROVISIONAL",
                        "primary_text_sha256":H("both"),
                        "cue_sha256":[{"cue":1,"sha256":H("one")},{"cue":2,"sha256":H("two")}]}],
            "candidates":[{"candidate_id":"c1","window_id":"W00001","cue":1,
                           "cue_sha256":H("one"),"truth_approved":False,
                           "prior_relation":"OPEN_UNREVIEWED"}]}

class GenericSourceReviewGateTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(validate_source_review(sample())["provisional_claims"],1)
    def test_missing_cue(self):
        d=sample();d["windows"][0]["cue_sha256"].pop()
        with self.assertRaises(ResearchCoverageError):validate_source_review(d)
    def test_claim_unowned(self):
        d=sample();d["candidates"][0]["cue"]=3
        with self.assertRaises(ResearchCoverageError):validate_source_review(d)
    def test_false_go(self):
        d=sample();d["p0_go"]=True
        with self.assertRaises(ResearchCoverageError):validate_source_review(d)
    def test_raw_srt_leak(self):
        d=sample();d["source_text"]="private"
        with self.assertRaises(ResearchCoverageError):validate_source_review(d)
    def test_empty_window_explicit(self):
        d=sample();d["candidates"]=[];d["windows"][0]["disposition"]="SOURCE_READ_NO_FINANCIAL_ATOMIC_CLAIM"
        self.assertEqual(validate_source_review(d)["provisional_claims"],0)
    def test_empty_window_cannot_hide_claim(self):
        d=sample();d["windows"][0]["disposition"]="SOURCE_READ_NO_FINANCIAL_ATOMIC_CLAIM"
        with self.assertRaises(ResearchCoverageError):validate_source_review(d)
    def test_wrong_next_pointer(self):
        d=sample();d["next_window"]="W00009"
        with self.assertRaises(ResearchCoverageError):validate_source_review(d)

if __name__=="__main__":unittest.main()
