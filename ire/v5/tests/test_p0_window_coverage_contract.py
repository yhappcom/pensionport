"""Regressions for the generic P0 window accounting contract."""
import unittest
from ire.v5.validation.p0_window_coverage_contract import (
    ReviewedWindow, WindowCoverageError, validate_new_window_batch
)

S="cd99dbf5576b74f2b256f2e08d6b869fdfbed7b08e8fcb5bb1f1296e50deea06"
COUNTS={37:4,38:5,39:1,40:2,42:4,43:5,44:2,45:2,47:2,48:2,49:2,50:3}
def sample():
    return [ReviewedWindow(f"W{n:05d}",(n-1)*18+1,n*18,count,S,
            "MODEL_SEMANTIC_PROVISIONAL") for n,count in COUNTS.items()]
def check(windows,prior=None,expected=None):
    return validate_new_window_batch(windows,previously_reviewed=prior or {"W00041","W00046"},
        expected_source_sha256=S,expected_window_ids=expected or {w.window_id for w in sample()},
        next_window_id="W00051")

class CoverageContractTests(unittest.TestCase):
    def test_12_new_windows_216_cues_34_candidates(self):
        self.assertEqual(check(sample())["new_cues"],216)
        self.assertEqual(check(sample())["provisional_claims"],34)
    def test_prior_scoped_context_cannot_be_recounted(self):
        with self.assertRaisesRegex(WindowCoverageError,"PREVIOUSLY_REVIEWED"):
            check(sample()+[ReviewedWindow("W00041",721,738,1,S,"MODEL_SEMANTIC_PROVISIONAL")],
                  expected={w.window_id for w in sample()}|{"W00041"})
    def test_source_drift_rejected(self):
        x=sample();x[0]=ReviewedWindow("W00037",649,666,4,"0"*64,"MODEL_SEMANTIC_PROVISIONAL")
        with self.assertRaisesRegex(WindowCoverageError,"SOURCE_HASH_DRIFT"):check(x)
    def test_cue_overlap_rejected(self):
        x=sample();x[1]=ReviewedWindow("W00038",666,684,5,S,"MODEL_SEMANTIC_PROVISIONAL")
        with self.assertRaisesRegex(WindowCoverageError,"CUE_OWNERSHIP_OVERLAP"):check(x)
    def test_claimless_without_review_rejected(self):
        x=sample();x[0]=ReviewedWindow("W00037",649,666,0,S,"MODEL_SEMANTIC_PROVISIONAL")
        with self.assertRaisesRegex(WindowCoverageError,"UNEXPLAINED_EMPTY_WINDOW"):check(x)
    def test_explicit_claimless_review_allowed(self):
        x=sample();x[0]=ReviewedWindow("W00037",649,666,0,S,"REVIEWED_NO_FINANCIAL_CLAIMS")
        self.assertEqual(check(x)["provisional_claims"],30)
    def test_duplicate_window_id_rejected(self):
        x=sample();x[1]=x[0]
        with self.assertRaisesRegex(WindowCoverageError,"WINDOW_OWNERSHIP_DRIFT"):check(x)
    def test_missing_expected_window_rejected(self):
        with self.assertRaisesRegex(WindowCoverageError,"WINDOW_OWNERSHIP_DRIFT"):check(sample()[:-1])
    def test_not_research_approval(self):
        x=check(sample());self.assertFalse(x["fact_approval"]);self.assertFalse(x["independent_recall_certified"])

if __name__=="__main__":unittest.main()
