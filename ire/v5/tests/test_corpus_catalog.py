"""Synthetic ZIP tests; private real SRT bytes are not committed to public Git."""
import tempfile
import unittest
import zipfile
from pathlib import Path
from ire.v5.corpus_catalog import catalog, inspect_srt, load_roster_ids

SRT=(b"1\n00:00:00,000 --> 00:00:01,000\nAn example.\n\n"
     b"2\n00:00:00,900 --> 00:00:02,000\nOfficial evidence is still needed.\n")

class SourceCatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder=Path(self.tmp.name)

    def archive(self,name,entries):
        dest=self.folder/name
        with zipfile.ZipFile(dest,"w",compression=zipfile.ZIP_DEFLATED) as z:
            for filename,source in entries:
                z.writestr(filename,source)
        return dest

    def test_real_srt_structure_without_semantic_approval(self):
        src=self.archive("one.zip",[
            ("201-300/youtube-transcript-sz5N9WJS310.srt",SRT),
            ("__MACOSX/201-300/._youtube-transcript-sz5N9WJS310.srt",b"AppleDouble"),
            ("201-300/.DS_Store",b"ignored")])
        r=catalog([src],{"sz5N9WJS310"})
        self.assertEqual(r["summary"]["srt_files"],1)
        self.assertEqual(r["summary"]["source_cues"],2)
        self.assertEqual(r["summary"]["matched_to_roster"],1)
        self.assertFalse(r["source_interpretation_completed"])
        self.assertFalse(r["advisory_eligible"])
        self.assertNotIn("Official evidence",str(r))

    def test_non_roster_id_is_explicit(self):
        src=self.archive("other.zip",[("youtube-transcript-abcdefghijk.srt",SRT)])
        self.assertEqual(catalog([src],{"sz5N9WJS310"})["summary"]["not_in_roster"],1)

    def test_identical_archive_overlap_is_idempotent(self):
        a=self.archive("a.zip",[("youtube-transcript-sz5N9WJS310.srt",SRT)])
        b=self.archive("b.zip",[("youtube-transcript-sz5N9WJS310.srt",SRT)])
        r=catalog([a,b])
        self.assertEqual(r["summary"]["srt_files"],1)
        self.assertEqual(r["summary"]["identical_duplicate_files_ignored"],1)

    def test_same_video_conflicting_bytes_are_rejected(self):
        a=self.archive("a.zip",[("youtube-transcript-sz5N9WJS310.srt",SRT)])
        b=self.archive("b.zip",[("youtube-transcript-sz5N9WJS310.srt",SRT+b" ")])
        with self.assertRaisesRegex(ValueError,"VIDEO_ID_CONFLICTING_ORIGINALS"):
            catalog([a,b])

    def test_incomplete_or_misnumbered_srt_rejected(self):
        a=self.archive("bad.zip",[("youtube-transcript-sz5N9WJS310.srt",b"1\nbad time\nx")])
        with self.assertRaises(ValueError):
            catalog([a])

    def test_numeric_filename_not_mapped_by_guess(self):
        a=self.archive("bad.zip",[("201.srt",SRT)])
        with self.assertRaisesRegex(ValueError,"SRT_FILENAME_VIDEO_ID_UNRESOLVED"):
            catalog([a])

    def test_path_traversal_rejected(self):
        a=self.archive("bad.zip",[("../youtube-transcript-sz5N9WJS310.srt",SRT)])
        with self.assertRaisesRegex(ValueError,"UNSAFE_ZIP_MEMBER"):
            catalog([a])

    def test_roster_extracts_video_ids_not_number_order(self):
        roster=self.folder/"roster.md"
        roster.write_text("| No | ID |\n| 1 | "+chr(96)+"sz5N9WJS310"+chr(96)+" |\n")
        self.assertEqual(load_roster_ids(roster),{"sz5N9WJS310"})
