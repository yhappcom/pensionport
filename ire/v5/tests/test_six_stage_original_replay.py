"""Never confuse 10-video private source replay with full financial approval."""
import copy
from pathlib import Path
import tempfile
import unittest

from ire.v5 import six_stage_original_replay as gate

ROOT=Path(__file__).resolve().parents[3]


class SixStageOriginalReplayTests(unittest.TestCase):
    def test_existing10_srt_metadata_frozen_without_private_ci_zip(self):
        d=gate.audit(ROOT)
        self.assertEqual(d["first_five_original_source_windows"],288)
        self.assertEqual(d["new_five_original_source_windows"],773)
        self.assertEqual(d["total_source_cues"],19014)
        self.assertEqual(d["source_anchored_crossvideo_risk_challenges"],14)
        self.assertFalse(d["original_srt_archives_replayed_in_current_process"])
        self.assertEqual(d["verified_replayed_source_member_count"],0)
        self.assertFalse(d["extra_5_video_atomic_recall_proven"])
        self.assertEqual(d["new_active_p4_nodes"],0)

    def test_forged_original_source_replay_claim_is_rejected(self):
        d=gate.read(ROOT)
        d["archive_files_hash_replayed_in_github_ci"]=True
        with self.assertRaisesRegex(gate.SixStageSourceError,
                                    "SIX_STAGE_FALSE_RESEARCH_RELEASE"):
            gate.audit(ROOT,replacement=d)

    def test_forged_formal_integration_is_rejected(self):
        d=gate.read(ROOT)
        d["quality_levels"]["new_p4_nodes_from_extra_five"]=3
        with self.assertRaisesRegex(gate.SixStageSourceError,
                                    "SIX_STAGE_PREMATURE_GRAPH_PROMOTION"):
            gate.audit(ROOT,replacement=d)

    def test_source_boundary_tampering_is_rejected(self):
        d=gate.read(ROOT)
        d["video_records"][9]["cues"]=35
        with self.assertRaisesRegex(gate.SixStageSourceError,
                                    "SIX_STAGE_INVALID_VIDEO"):
            gate.audit(ROOT,replacement=d)

    def test_compilation_cannot_claim_independent_holdout(self):
        d=gate.read(ROOT)
        d["risk_challenges"][4]["status"]="CONDITIONAL_STRATEGY"
        with self.assertRaisesRegex(gate.SixStageSourceError,
                                    "SIX_STAGE_COMPILATION_FAKE_INDEPENDENCE"):
            gate.audit(ROOT,replacement=d)

    def test_missing_private_archive_fails_only_when_replay_requested(self):
        with tempfile.TemporaryDirectory() as folder:
            missing=Path(folder)/"original.zip"
            with self.assertRaisesRegex(gate.SixStageSourceError,
                                        "SIX_STAGE_SOURCE_ZIP_MISSING"):
                gate.audit(ROOT,source_zip=missing)
            missing.write_bytes(b"fake zip")
            with self.assertRaisesRegex(gate.SixStageSourceError,
                                        "SIX_STAGE_SOURCE_ZIP_SHA_MISMATCH"):
                gate.audit(ROOT,source_zip=missing)


if __name__=="__main__":unittest.main()
