"""Pinning rejects fake approval and mismatched source metadata."""
from __future__ import annotations
import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location(
    "v6_official_replay",Path(__file__).with_name("verify_pinned_official_snapshot.py"))
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def example(key):
    p=mod.RECORDS[key]
    return {"source_id":key, "artifact_name":p["filename"],
            "captured_body_sha256":p["sha256"],
            "captured_body_bytes":p["bytes"],
            "visible_effective_date":p["effective_date"],
            "finance_fact_approved":False,
            "issuer_digital_signature_verified":False,
            "independent_semantic_support_verified":False,
            "p0_go":False}

class PinnedOfficialTests(unittest.TestCase):
    def test_both_pins(self):
        self.assertEqual(set(mod.RECORDS),{"nts_pension","decree_40_3"})
        self.assertEqual(mod.RECORDS["decree_40_3"]["effective_date"],"2026-10-01")
        self.assertIsNone(mod.RECORDS["nts_pension"]["effective_date"])

    def test_no_self_approval(self):
        for key,pin in mod.RECORDS.items():
            mod.validate_record(example(key),pin)

    def test_missing_fails(self):
        with self.assertRaisesRegex(ValueError,"SNAPSHOT_RECORD_MISSING"):
            mod.validate_record(None,mod.RECORDS["nts_pension"])

    def test_wrong_sha_fails(self):
        x=example("nts_pension")
        x["captured_body_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"METADATA_DRIFT"):
            mod.validate_record(x,mod.RECORDS["nts_pension"])

    def test_wrong_effective_date_fails(self):
        x=example("decree_40_3")
        x["visible_effective_date"]="2025-01-01"
        with self.assertRaisesRegex(ValueError,"METADATA_DRIFT"):
            mod.validate_record(x,mod.RECORDS["decree_40_3"])

    def test_fake_fact_approval_fails(self):
        x=example("nts_pension")
        x["finance_fact_approved"]=True
        with self.assertRaisesRegex(ValueError,"FALSE_AUTHORITY"):
            mod.validate_record(x,mod.RECORDS["nts_pension"])

    def test_fake_p0_go_fails(self):
        x=example("decree_40_3")
        x["p0_go"]=True
        with self.assertRaisesRegex(ValueError,"FALSE_AUTHORITY"):
            mod.validate_record(x,mod.RECORDS["decree_40_3"])

    def test_wrong_file_name_fails(self):
        x=example("nts_pension")
        x["artifact_name"]="other.pdf"
        with self.assertRaisesRegex(ValueError,"METADATA_DRIFT"):
            mod.validate_record(x,mod.RECORDS["nts_pension"])


if __name__=="__main__":
    unittest.main()
