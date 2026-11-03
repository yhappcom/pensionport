"""V5 encrypted snapshot transport: real-run optional and synthetic CI tests."""
from __future__ import annotations
import json
from pathlib import Path
import secrets
import tempfile
import unittest

from ire.v5.engine import ResearchRun, RunError, sha256
from ire.v5.portable import export_encrypted, import_encrypted, reopen_private_store


class SyntheticPortabilityTests(unittest.TestCase):
    """Always runs on CI; no historical private original SRT dependency."""
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.srt=(b"1\n00:00:00,000 --> 00:00:01,000\nPension amount differs.\n\n"
                  b"2\n00:00:01,000 --> 00:00:02,000\nPrivate pension eligibility matters.\n")
        self.plan={"schema":"IRE_V5_SOURCE_PLAN_V1","video_id":"sz5N9WJS310",
             "source_sha256":sha256(self.srt),"source_cues":2,
             "planner_version":"V5_TEST_NO_V3_IMPORT",
             "prior_baseline_git_blob_sha":"b"*40,
             "active_window_ids":["W00001"],
             "windows":[{"window_id":"W00001","primary_cue_ids":[1,2],
                 "primary_text_sha256":sha256(
                     b"Pension amount differs. Private pension eligibility matters.")}]}
        self.store=self.root/"original"
        self.run=ResearchRun(self.srt,self.plan,self.store)
        pkt=self.run.packet("W00001")
        self.run.append("MODEL_ANALYSIS",{
            "schema":"IRE_V5_MODEL_WINDOW_V1","window_id":"W00001",
            "packet_sha256":pkt["packet_sha256"],
            "claimed_author":"CURRENT_CHATGPT_CONVERSATION",
            "independent_human_verified":False,
            "claims":[{"claim_id":"V5C0001",
                "proposition":"Pension eligibility depends on individual situation.",
                "kind":"OPINION","requires_external_verification":False,
                "fact_verified":False,"advisory_approved":False,
                "source_refs":[{"cue_index":1,"quote":"Pension amount differs."},
                               {"cue_index":2,"quote":"Private pension eligibility matters."}]}],
            "cue_dispositions":[{"cue_index":i,"status":"LINKED",
                "claim_ids":["V5C0001"],"reason":None} for i in (1,2)]})
        self.run.append("EVIDENCE_REVIEW",{
            "schema":"IRE_V5_EVIDENCE_CASE_V1","claim_id":"V5C0001",
            "status":"NOT_REQUIRED_WITH_REASON",
            "investigation_summary":"Educational scenario only, not a specific tax rule.",
            "open_reason":"Personal financial situation has not been independently established.",
            "financial_truth_approved":False})
        self.run.append("PRIOR_RELATION_REVIEW",{
            "schema":"IRE_V5_PRIOR_RELATION_V1","claim_id":"V5C0001",
            "prior_baseline_git_blob_sha":"b"*40,
            "prior_claim_ids":[],"status":"NO_RELEVANT_PRIOR_WITH_SEARCH",
            "review_notes":"Read prior principles; no exact semantic match was established.",
            "search_terms":["pension","personal eligibility"],
            "automerge":False,"financial_truth_approved":False})
        self.run.close()
        self.secret=secrets.token_urlsafe(32)
        self.archive=self.root/"receipt.v5enc"
        self.restored=self.root/"restore"

    def test_encrypted_replay_is_full_fidelity(self):
        original=self.run.status()
        export=export_encrypted(self.run,self.secret,self.archive)
        result=import_encrypted(self.archive,self.secret,self.restored)
        self.assertTrue(export["encrypted"])
        self.assertFalse(export["secret_saved_in_archive"])
        self.assertEqual(result["receipt_count"],4)
        self.assertEqual(result["event_chain_head_sha256"],
                         original["event_chain_head_sha256"])
        self.assertTrue(result["verified_by_real_v5_replay"])
        self.assertEqual(reopen_private_store(self.restored).status(),original)
        self.assertEqual(reopen_private_store(self.restored).next_task()["phase"],"DONE")
        self.assertTrue((self.restored/"private_source.srt").exists())
        self.assertEqual((self.restored/"private_source.srt").stat().st_mode & 0o077,0)

    def test_wrong_secret_and_no_plaintext(self):
        export_encrypted(self.run,self.secret,self.archive)
        encrypted=self.archive.read_bytes()
        self.assertNotIn(b"source_srt_base64",encrypted)
        self.assertNotIn(self.srt[:30],encrypted)
        with self.assertRaisesRegex(RunError,"ARCHIVE_PASSWORD_OR_INTEGRITY_FAILED"):
            import_encrypted(self.archive,"wrong secret password",self.restored)
        self.assertFalse(self.restored.exists())

    def test_tamper_rejected_without_partial_restore(self):
        export_encrypted(self.run,self.secret,self.archive)
        blob=bytearray(self.archive.read_bytes());blob[-8]^=1
        self.archive.write_bytes(blob)
        with self.assertRaisesRegex(RunError,"ARCHIVE_PASSWORD_OR_INTEGRITY_FAILED"):
            import_encrypted(self.archive,self.secret,self.restored)
        self.assertFalse(self.restored.exists())

    def test_never_overwrite_existing_archive_or_store(self):
        export_encrypted(self.run,self.secret,self.archive)
        with self.assertRaisesRegex(RunError,"ARCHIVE_WOULD_OVERWRITE"):
            export_encrypted(self.run,self.secret,self.archive)
        import_encrypted(self.archive,self.secret,self.restored)
        with self.assertRaisesRegex(RunError,"RESTORE_DESTINATION_MUST_BE_NEW"):
            import_encrypted(self.archive,self.secret,self.restored)


class PrivateSourcePilotOptionalTests(unittest.TestCase):
    """Only runs if a separately mounted 26-event original-source pilot exists."""
    def test_original_26_receipts_replay_after_encrypted_transport(self):
        source=Path("/mnt/data/ire_v5/private/source.srt")
        manifest=Path("/mnt/data/ire_v5/private/source_plan.json")
        run_dir=Path("/mnt/data/ire_v5/private/live_v3")
        if not source.exists() or not manifest.exists() or not (run_dir/"run_lock.json").exists():
            self.skipTest("Private #1 original-source pilot is intentionally absent in CI.")
        run=ResearchRun(source.read_bytes(),json.loads(manifest.read_text()),run_dir)
        before=run.status()
        self.assertEqual(before["receipt_count"],26)
        self.assertEqual(before["submitted_windows"],3)
        with tempfile.TemporaryDirectory() as temp:
            archive=Path(temp)/"real.v5enc"
            other=Path(temp)/"new"
            password=secrets.token_urlsafe(32)
            export_encrypted(run,password,archive)
            outcome=import_encrypted(archive,password,other)
            self.assertEqual(outcome["event_chain_head_sha256"],
                             before["event_chain_head_sha256"])
            self.assertEqual(reopen_private_store(other).status(),before)


if __name__=="__main__":
    unittest.main()
