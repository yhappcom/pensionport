"""The 20 migrated claims have legacy video IDs, not verified original SRT cues."""
import unittest
from pathlib import Path
from ire.v5.legacy_lineage_audit import audit

ROOT=Path(__file__).resolve().parents[3]

class LegacyLineageTests(unittest.TestCase):
    def test_original_20_claims_not_misrepresented_as_original_srt_verified(self):
        r=audit(ROOT)
        self.assertEqual(r["legacy_claims"],20)
        self.assertEqual(r["unique_supporting_video_ids"],27)
        self.assertEqual(r["legacy_base_video_records"],27)
        self.assertEqual(r["canonical_overlay_video_records"],13)
        self.assertEqual(r["v3_analysis_event_video_records"],0)
        self.assertEqual(r["indexed_srt_ids_in_current_catalog"],0)
        self.assertFalse(r["original_cue_quote_verification_performed"])
        self.assertEqual(r["independent_original_srt_audits_completed"],0)
        self.assertEqual(r["independent_financial_fact_approvals"],0)
