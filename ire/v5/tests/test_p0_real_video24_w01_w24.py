"""Freeze and validate #24 real source-derived receipt without publishing private SRT."""
import base64
import hashlib
import json
from pathlib import Path
import unittest
import zlib
from ire.v5.validation.p0_generic_source_review_gate import validate_source_review

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"validation"/"private_source_derived_20261107"/"video24_w01_w24.json.zlib.b64"
EXPECTED_SHA256="ac390710dbd5eb3c323cd8bed0ad916956a8e7ed6c713c5440ca9f3f1a33a216"
EXPECTED_SOURCE="af4d89d0e69b219947fdf82cdd9f3229c1f7b1e14c05c924ac815d2511f6c531"

class RealVideo24SourceReceiptTests(unittest.TestCase):
    def test_source_and_cue_ownership(self):
        compressed=base64.b64decode(PATH.read_text("ascii").strip(),validate=True)
        raw=zlib.decompress(compressed)
        self.assertLess(len(raw),500_000)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),EXPECTED_SHA256)
        d=json.loads(raw)
        self.assertEqual(d["source_sha256"],EXPECTED_SOURCE)
        self.assertEqual(d["video_id"],"AeCOMNl11v4")
        self.assertEqual(d["total_windows"],129)
        self.assertEqual(d["total_cues"],2321)
        result=validate_source_review(d)
        self.assertEqual(result["window_count"],24)
        self.assertEqual(result["cue_count"],431)
        self.assertEqual(result["provisional_claims"],54)
        self.assertEqual(result["next_window"],"W00025")
        self.assertFalse(result["truth_approved"])
        self.assertFalse(result["independent_recall_certified"])
        self.assertEqual(sum(bool(c["evidence_ids"]) for c in d["candidates"]),20)
        self.assertFalse(d["second_pass"]["independent_blind"])
        self.assertEqual(d["windows"][1]["disposition"],"SOURCE_READ_NO_FINANCIAL_ATOMIC_CLAIM")

if __name__=="__main__":unittest.main()
