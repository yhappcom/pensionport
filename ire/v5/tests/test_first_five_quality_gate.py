"""Risk-case quality gate must not turn a green CI into research approval."""
import copy
import unittest
from pathlib import Path
from ire.v5 import first_five_quality_gate as gate

ROOT=Path(__file__).resolve().parents[3]

class FirstFiveOriginalQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger=gate.read(ROOT,gate.FILE)

    def test_quality_source_review_does_not_approve_full_research(self):
        out=gate.verify(ROOT)
        self.assertEqual(out["focused_qa_source_cases"],25)
        self.assertEqual(out["focused_qa_unique_source_cues"],892)
        self.assertEqual(out["critical_risk_cases_not_released"],6)
        self.assertEqual(out["pilot_video_ids_not_in_116_claim_ledger"],2)
        self.assertEqual(out["pilot_video_legacy_claims_outside_60_claim_route"],3)
        self.assertFalse(out["full_research_quality_go"])
        self.assertFalse(out["next_five_video_expansion_go"])
        self.assertFalse(out["personal_advice_release"])
        self.assertFalse(out["private_archive_reopened_in_this_gate"])

    def test_false_claim_of_full_semantic_coverage_fails(self):
        bad=copy.deepcopy(self.ledger)
        bad["focused_span_reviewed_is_corpus_complete"]=True
        with self.assertRaisesRegex(gate.ResearchQualityError,
                                    "QA_FALSE_CORPUS_COMPLETION"):
            gate.verify(ROOT,ledger=bad)

    def test_source_cue_escape_fails(self):
        bad=copy.deepcopy(self.ledger)
        bad["cases"][0]["first_cue"]=0
        with self.assertRaisesRegex(gate.ResearchQualityError,
                                    "QA_CASE_SOURCE_ID_OR_SPAN_MISMATCH"):
            gate.verify(ROOT,ledger=bad)

    def test_bad_source_hash_fails(self):
        bad=copy.deepcopy(self.ledger)
        bad["cases"][0]["original_normalized_span_sha256"]="not-a-sha"
        with self.assertRaisesRegex(gate.ResearchQualityError,
                                    "QA_UNANCHORED_OR_AUTO_APPROVED"):
            gate.verify(ROOT,ledger=bad)

    def test_fabricated_personal_approval_blocked(self):
        bad=copy.deepcopy(self.ledger)
        bad["cases"][7]["personal_advice_approved"]=True
        with self.assertRaisesRegex(gate.ResearchQualityError,
                                    "QA_UNANCHORED_OR_AUTO_APPROVED"):
            gate.verify(ROOT,ledger=bad)

    def test_missing_critical_finding_fails(self):
        bad=copy.deepcopy(self.ledger)
        bad["cases"][7]["severity"]="MEDIUM"
        with self.assertRaisesRegex(gate.ResearchQualityError,
                                    "QA_CASE_DISTRIBUTION_OR_COUNT_MISMATCH"):
            gate.verify(ROOT,ledger=bad)

    def test_claim_mapping_cannot_invent_core_coverage(self):
        bad=copy.deepcopy(self.ledger)
        bad["cases"][0]["legacy_claim_id"]="GOMHEE-C01"
        with self.assertRaisesRegex(gate.ResearchQualityError,
                                    "QA_FALSE_DIRECT_CORE_LINK"):
            gate.verify(ROOT,ledger=bad)

    def test_wrong_issuer_link_fails(self):
        bad=copy.deepcopy(self.ledger)
        bad["cases"][7]["official_crosscheck_id"]="NOT_AN_ISSUER"
        with self.assertRaisesRegex(gate.ResearchQualityError,
                                    "QA_UNKNOWN_OR_FABRICATED_OFFICIAL_SOURCE"):
            gate.verify(ROOT,ledger=bad)

    def test_without_source_zip_no_byte_recheck_claimed(self):
        out=gate.verify(ROOT)
        self.assertIsNone(out["private_25_span_hashes_matching"])
        self.assertFalse(out["private_25_span_hashes_byte_rechecked_in_this_gate"])

if __name__=="__main__":
    unittest.main()
