"""Negative tests: no speaker laundering, ASR certainty or zero-claim omissions."""
from dataclasses import replace
import unittest
from ire.v5.source_attribution_gate import (
    AttributedClaim, AttributionContractError, validate_attributed_claim, validate_empty_window)

H = "a"*64
C = "b"*64

class SourceAttributionGateTest(unittest.TestCase):
    def setUp(self):
        self.base = AttributedClaim(
            video_id="WGFPHeM6-6I", window_id="W00028", source_sha256=H,
            cue_index=496, cue_text_sha256=C, speaker_kind="COMMENT_CASE",
            claim_kind="PERSONAL_CASE", uncertainty_flags=frozenset({"ASR_OPEN"}),
            source_quote_verified=False, context_cues_checked=(495,496,497))
        self.hashes={495:H,496:C,497:H}

    def check(self, claim):
        validate_attributed_claim(claim,cue_hashes=self.hashes,active_window_cues={495,496,497})

    def test_comment_case_remains_personal(self):
        self.check(self.base)

    def test_comment_must_not_become_rule(self):
        with self.assertRaisesRegex(AttributionContractError,"COMMENT_CANNOT"):
            self.check(replace(self.base,claim_kind="RULE"))

    def test_uncertain_speaker_requires_flag(self):
        with self.assertRaisesRegex(AttributionContractError,"UNCERTAIN_SPEAKER_REQUIRES_FLAG"):
            self.check(replace(self.base,speaker_kind="UNCERTAIN_SPEAKER",
                               uncertainty_flags=frozenset({"ASR_OPEN"})))

    def test_asr_uncertainty_not_silently_removed(self):
        with self.assertRaisesRegex(AttributionContractError,"ASR_UNVERIFIED"):
            self.check(replace(self.base,uncertainty_flags=frozenset()))

    def test_source_hash_mismatch(self):
        with self.assertRaisesRegex(AttributionContractError,"SOURCE_CUE_ANCHOR_MISMATCH"):
            self.check(replace(self.base,cue_text_sha256=H))

    def test_context_required(self):
        with self.assertRaisesRegex(AttributionContractError,"ADJACENT_CONTEXT"):
            self.check(replace(self.base,context_cues_checked=(495,)))

    def test_no_automatic_financial_approval(self):
        with self.assertRaisesRegex(AttributionContractError,"NO_AUTOMATIC"):
            self.check(replace(self.base,fact_approved=True))

    def test_zero_financial_claim_requires_second_pass(self):
        validate_empty_window(window_id="W00025",cue_ids=[433,434],
                              source_cue_hashes={433:H,434:C},
                              disposition="NO_FINANCIAL_ATOMIC_CLAIMS",
                              reviewer_marked=True,second_pass_marked=True)
        with self.assertRaisesRegex(AttributionContractError,"NOT_SECOND_PASS"):
            validate_empty_window(window_id="W00025",cue_ids=[433,434],
                                  source_cue_hashes={433:H,434:C},
                                  disposition="NO_FINANCIAL_ATOMIC_CLAIMS",
                                  reviewer_marked=True,second_pass_marked=False)

if __name__=="__main__":
    unittest.main()
