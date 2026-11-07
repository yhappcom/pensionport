"""Source anchors can be confirmed from SRT but never become formal law approvals."""
import copy
from pathlib import Path
import tempfile
import unittest
from ire.v5 import p3_original_27_source_gate as p3

ROOT=Path(__file__).resolve().parents[3]


class P3Original27SourceTests(unittest.TestCase):
    def test_source_anchored_27_windows_and_89_claims_are_distinct_from_certs(self):
        r=p3.verify(ROOT)
        self.assertEqual(r["original_27_windows_checked"],27)
        self.assertEqual(r["original_cues_dispositioned"],486)
        self.assertEqual(r["source_anchored_candidates"],89)
        self.assertEqual(r["regulatory_overgeneralizations_quarantined"],14)
        self.assertEqual(r["official_scope_supported_source_statements"],10)
        self.assertEqual(r["asr_suspicions_await_audio"],2)
        self.assertFalse(r["original_private_source_replayed_this_process"])
        self.assertFalse(r["full_atomic_recall_independently_proven"])
        self.assertEqual(r["formal_financial_fact_certifications"],0)

    def test_forged_certification_is_rejected(self):
        d=p3.read(ROOT,p3.LEDGER)
        d["windows"][0]["claims"][0]["formal_financial_fact_approved"]=True
        with self.assertRaisesRegex(p3.P3SourceError,"P3_ATOMIC_CLAIM"):
            p3.verify(ROOT,replacement=d)

    def test_removed_source_cue_disposition_is_rejected(self):
        d=p3.read(ROOT,p3.LEDGER)
        # Removing a source-anchored span without assigning its cues to context
        # must never silently certify full-cue recall.
        d["windows"][0]["claims"].pop()
        with self.assertRaisesRegex(p3.P3SourceError,"P3_SOURCE_CUE_NOT_DISPOSITIONED"):
            p3.verify(ROOT,replacement=d)

    def test_shifted_cue_anchor_rejected(self):
        d=p3.read(ROOT,p3.LEDGER)
        d["windows"][0]["first_cue"]+=1
        with self.assertRaisesRegex(p3.P3SourceError,"P3_SOURCE_WINDOW"):
            p3.verify(ROOT,replacement=d)

    def test_risky_official_link_cannot_fake_regulatory_corroboration(self):
        d=p3.read(ROOT,p3.LEDGER)
        match=next(c for w in d["windows"] for c in w["claims"]
                   if c["meaning_class"]=="REGULATORY_SUPPORTED_SCOPED")
        match["official_context_source_ids"]=[]
        with self.assertRaisesRegex(p3.P3SourceError,"P3_BAD_OFFICIAL_SCOPE_LINK"):
            p3.verify(ROOT,replacement=d)

    def test_bad_source_host_rejected(self):
        d=p3.read(ROOT,p3.LEDGER)
        d["source_catalog"]["NTS_PENSION_1500"]["url"]="https://evil.example/forged"
        with self.assertRaisesRegex(p3.P3SourceError,"P3_UNTRUSTED_OFFICIAL"):
            p3.verify(ROOT,replacement=d)

    def test_false_original_archive_zip_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            fake=Path(folder)/"private.zip"
            fake.write_bytes(b"not original")
            with self.assertRaisesRegex(p3.P3SourceError,"P3_ORIGINAL_SOURCE_ARCHIVE"):
                p3.verify(ROOT,source_zip=fake)


if __name__=="__main__": unittest.main()
