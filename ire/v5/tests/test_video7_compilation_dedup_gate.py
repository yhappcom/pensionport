"""Fail-closed #7 original compilation duplicate evidence; no false holdout."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from ire.v5 import video7_compilation_dedup_gate as gate

ROOT=Path(__file__).resolve().parents[3]

class Video7CompilationTests(unittest.TestCase):
    def test_940_exact_cues_with_original_reprint_still_not_blind(self):
        x=gate.audit(ROOT)
        self.assertEqual(x["compilation_cues"],10728)
        self.assertEqual(x["compilation_v5_windows"],596)
        self.assertEqual(x["owner_archive_srt_files_compared"],101)
        self.assertEqual(x["known_independent_original_video_id"],"i32DeJPzsfE")
        self.assertEqual(x["known_exact_cue_reprints"],940)
        self.assertEqual(x["known_reprint_first_to_last_cue"],[14,1973])
        self.assertFalse(x["video7_is_independent_holdout"])
        self.assertFalse(x["rest_of_compilation_is_proven_novel"])
        self.assertEqual(x["video7_auto_promoted_unique_financial_facts"],0)
        self.assertFalse(x["private_archive_replayed_in_this_process"])

    def test_missing_private_source_fails_while_ci_does_not_claim_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"private.zip"
            with self.assertRaisesRegex(gate.CompilationError,"SOURCE_ZIP_MISSING"):
                gate.audit(ROOT,path)
            path.write_bytes(b"wrong")
            with self.assertRaisesRegex(gate.CompilationError,"WRONG_PRIVATE_ARCHIVE"):
                gate.audit(ROOT,path)

    def test_false_novel_holdout_claim_rejected(self):
        data=gate.load(ROOT)
        data["video7_eligible_as_independent_blind_holdout"]=True
        with patch.object(gate,"load",return_value=data):
            with self.assertRaisesRegex(gate.CompilationError,
                                        "COMP7_FORGED_INDEPENDENT_HOLDOUT"):
                gate.audit(ROOT)

    def test_nonmatched_is_not_automatically_unique(self):
        data=gate.load(ROOT)
        data["unmatched_portion_proven_new"]=True
        with patch.object(gate,"load",return_value=data):
            with self.assertRaisesRegex(gate.CompilationError,
                                        "COMP7_FORGED_INDEPENDENT_HOLDOUT"):
                gate.audit(ROOT)

    def test_normalization_is_reproducible(self):
        self.assertEqual(gate.norm("  >> 엔화 ! ETF  "),gate.norm("엔화ETF"))
        self.assertEqual(gate.norm("aB-10- 가"),"ab10가")

if __name__=="__main__":unittest.main()
