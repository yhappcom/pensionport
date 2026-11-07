"""Static provenance and non-advisory checks for the real 201-300 ZIP census."""
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
CAT=ROOT/"ire/v5/source_catalog/201-300.json"


class RealCorpusMetadataTests(unittest.TestCase):
    def test_archive_census_has_99_separately_hashed_sources(self):
        c=json.loads(CAT.read_text("utf-8"))
        rows=c["files"]
        self.assertEqual(len(rows),99)
        self.assertEqual(len({x["video_id"] for x in rows}),99)
        self.assertEqual(sum(x["cue_count"] for x in rows),108238)
        self.assertEqual(c["summary"]["matched_to_roster"],99)
        self.assertEqual(c["summary"]["long_form_sources"],78)
        self.assertEqual(c["summary"]["shorts_sources"],21)
        self.assertEqual(c["summary"]["not_in_roster"],0)
        for x in rows:
            self.assertRegex(x["source_sha256"],r"^[0-9a-f]{64}$")
            self.assertGreater(x["cue_count"],0)
            self.assertTrue(x["roster_matched"])
            self.assertEqual(x["semantic_analysis_status"],"NOT_ANALYZED_BY_THIS_CENSUS")
        self.assertFalse(c["advisory_eligible"])
        self.assertFalse(c["source_interpretation_completed"])
        self.assertEqual(c["independent_financial_facts_approved"],0)
        self.assertEqual(c["archives"][0]["sha256"],
            "9ccd094766fc0b896d1b237edcf7ea4ef7b7622007262275f0d9e4c0518fee10")

if __name__=="__main__":
    unittest.main()
