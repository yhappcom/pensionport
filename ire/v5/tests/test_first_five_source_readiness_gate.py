"""Fail-closed tests for honest V5 readiness and optional private SRT bytes."""
from __future__ import annotations
import copy
import tempfile
import unittest
import zipfile
from pathlib import Path

from ire.v5 import first_five_source_readiness_gate as readiness

ROOT = Path(__file__).resolve().parents[3]

class FirstFiveResearchReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assessment = readiness._load(ROOT, readiness.ASSESSMENT)
        cls.manifest = readiness._load(ROOT, readiness.MANIFEST)

    def test_software_pass_does_not_imply_research_quality_pass(self):
        result = readiness.verify(ROOT)
        self.assertTrue(result["software_ci_verified_at_basis_head"])
        self.assertFalse(result["full_research_engine_validation_completed"])
        self.assertFalse(result["broad_corpus_research_go"])
        self.assertFalse(result["advisory_approval"])
        self.assertEqual(result["first_five_unconfirmed_windows"], 283)
        self.assertEqual(result["next_permitted_stage"], "FIRST_FIVE_SOURCE_REACQUISITION")

    def test_public_five_video_counts_and_source_ids_unchanged(self):
        result = readiness.verify(ROOT)
        self.assertEqual(result["first_five_total_windows"], 288)
        self.assertEqual(result["first_five_public_processed_windows"], 5)
        self.assertEqual(result["first_five_original_source_check"]["verified_srt_files"], 0)

    def test_false_full_validation_go_is_blocked(self):
        data = copy.deepcopy(self.assessment)
        data["workflow_decision"]["engine_fully_verified"] = True
        with self.assertRaisesRegex(readiness.ResearchReadinessError,
                                    "ENGINE_FALSE_FULL_RESEARCH_APPROVAL"):
            readiness.verify(ROOT, assessment=data)

    def test_pretending_source_available_without_bytes_is_blocked(self):
        data = copy.deepcopy(self.manifest)
        data["original_source_available_in_this_turn"] = True
        with self.assertRaisesRegex(readiness.ResearchReadinessError,
                                    "ENGINE_SOURCE_PROVENANCE_UNTRUSTWORTHY"):
            readiness.verify(ROOT, manifest=data)

    def test_altering_source_sha_or_video_id_is_blocked(self):
        for field, fake in (
            ("video_id", "not-the-video"),
            ("source_sha256", "0" * 64),
            ("expected_cues", 555)
        ):
            data = copy.deepcopy(self.manifest)
            data["videos"][0][field] = fake
            with self.assertRaisesRegex(readiness.ResearchReadinessError,
                                        "ENGINE_SOURCE_VIDEO_OR_HASH_FORGED"):
                readiness.verify(ROOT, manifest=data)

    def test_missing_private_archive_refused(self):
        with self.assertRaisesRegex(readiness.ResearchReadinessError,
                                    "FIRST_FIVE_SOURCE_ZIP_NOT_FOUND"):
            readiness.verify(ROOT, source_zip=ROOT / "not-existing-1-100.zip")

    def test_wrong_archive_cannot_masquerade_as_first_five(self):
        with tempfile.TemporaryDirectory() as td:
            zip_path = Path(td) / "fake-1-100.zip"
            with zipfile.ZipFile(zip_path, "w") as z:
                z.writestr("youtube-transcript-not_a_real_id.srt",
                           "1\n00:00:00,000 --> 00:00:01,000\nwrong\n")
            with self.assertRaisesRegex(readiness.ResearchReadinessError,
                                        "FIRST_FIVE_SRT_NOT_FOUND_OR_DUPLICATED"):
                readiness.verify(ROOT, source_zip=zip_path)

    def test_srt_parser_rejects_cue_number_gaps(self):
        bad=(b"1\n00:00:00,000 --> 00:00:01,000\nhi\n\n"
             b"3\n00:00:02,000 --> 00:00:03,000\nbye")
        with self.assertRaisesRegex(readiness.ResearchReadinessError,
                                    "SOURCE_CUE_SEQUENCE_GAP_OR_CONTENT_MISSING"):
            readiness._validate_cues(bad, 2)

    def test_srt_parser_accepts_overlapping_valid_cues(self):
        good=(b"1\n00:00:00,000 --> 00:00:02,000\nfirst\n\n"
              b"2\n00:00:01,000 --> 00:00:03,000\nsecond")
        readiness._validate_cues(good, 2)

if __name__ == "__main__":
    unittest.main()
