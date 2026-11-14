"""V62 additive P0 test. Synthetic fixtures only; no private owner SRT."""
import importlib.util
import pathlib
import unittest

spec=importlib.util.spec_from_file_location(
    "v62_p0_release_readiness",
    pathlib.Path(__file__).with_name("v62_p0_release_readiness.py"))
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
evaluate_readiness=mod.evaluate_readiness
InvalidReadinessInput=mod.InvalidReadinessInput

FIXTURE={
    "schema":"IRE_V6_V62_FIRSTFIVE_P0_MANUAL_REVIEW_OVERLAY_50_OF_1603_SHA_ONLY",
    "source_cues":5129,"source_windows":130,
    "source_provisional_utterances":1603,
    "reviewed_utterance_parents":50,
    "unreviewed_source_utterances":1553,
    "reviewer_semantic_subunits":100,
    "semantics_independently_gold_verified":False,
    "p0_go":False
}
KW=dict(
    external_evidence_open=4,
    missing_historical_v40_windows=108,
    historical_audio_proofs_missing=8,
    independent_gold_reviewer_attestation_verified=False,
    independent_gold_claim_level_precision_recall_measured=False
)


class P0FailClosedTests(unittest.TestCase):
    def test_actual_census_stays_no_go(self):
        r=evaluate_readiness(FIXTURE,**KW)
        self.assertEqual(r["status"],"P0_NO_GO")
        self.assertEqual(len(r["blockers"]),6)
        self.assertEqual(r["unreviewed_candidate_parents"],1553)

    def test_source_cue_count_changed(self):
        self.assertRaises(InvalidReadinessInput,evaluate_readiness,
            {**FIXTURE,"source_cues":5128},**KW)

    def test_forged_gold(self):
        self.assertRaises(InvalidReadinessInput,evaluate_readiness,
            {**FIXTURE,"semantics_independently_gold_verified":True},**KW)

    def test_forged_go(self):
        self.assertRaises(InvalidReadinessInput,evaluate_readiness,
            {**FIXTURE,"p0_go":True},**KW)

    def test_missing_historical_custody_remains_blocker(self):
        result=evaluate_readiness(FIXTURE,**KW)
        self.assertIn("HISTORICAL_V40_CUSTODY_BYTES_MISSING",
                      result["blockers"])

    def test_zero_unresolved_is_still_not_approval(self):
        f={**FIXTURE,"reviewed_utterance_parents":1603,
           "unreviewed_source_utterances":0}
        r=evaluate_readiness(f,external_evidence_open=0,
            missing_historical_v40_windows=0,historical_audio_proofs_missing=0,
            independent_gold_reviewer_attestation_verified=True,
            independent_gold_claim_level_precision_recall_measured=True)
        self.assertFalse(r["p0_go"])
        self.assertEqual(r["blockers"],
            ["EXTERNAL_INDEPENDENT_RELEASE_APPROVAL_REQUIRED"])


if __name__=="__main__":
    unittest.main()
