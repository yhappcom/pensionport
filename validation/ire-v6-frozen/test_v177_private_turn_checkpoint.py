"""V177 two-process and adversarial checkpoint tests — synthetic captions ONLY.

Not a real ChatGPT model invocation, not actual V176 720-cue owner data, not
independent semantic accuracy proof or V123/E4 authorization.
"""
from __future__ import annotations

import json
import os
import sqlite3
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from ire.v6.codec import sha256
from test_v176_chat_engine_loop import fixture, respond
from v176_chat_engine_loop import EngineChatSession
from v177_private_turn_checkpoint import (
    export_private_two_turn_bundle, restore_private_two_turn_bundle,
)


class TestActualTwoProcessHandoff(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.raw = fixture()
        self.srt = self.root / "original.srt"
        self.srt.write_bytes(self.raw)
        os.chmod(self.srt, 0o600)
        self.db = self.root / "owner.sqlite"
        self.source_sha = sha256(self.raw)
        self.video = "AbCdEf12345"
        self.engine = EngineChatSession(self.db, self.raw, self.video,
            owner_source_sha256=self.source_sha,
            window_size=3, expected_window_count=2)
        first = self.engine.prepare(limit=3, source_first_only=True)
        self.engine.submit(first, respond(first, add_claim=True))
        self.p = self.engine.progress()
        self.assertEqual(self.p["cue_reviewed"], 3)
        self.bundle = self.root / "private-two-turn.zip"

    def create(self, **changes):
        args = dict(srt_path=self.srt, db_path=self.db,
                    video_id=self.video, source_sha256=self.source_sha,
                    expected_head_sha256=self.p["checkpoint_head_sha256"],
                    expected_reviewed=3, output_zip=self.bundle,
                    window_size=3, expected_windows=2, limit=2,
                    context_radius=2)
        args.update(changes)
        return export_private_two_turn_bundle(**args)

    def restore(self, **changes):
        args = dict(input_zip=self.bundle, output_dir=self.root / "restored",
                    expected_source_sha256=self.source_sha,
                    expected_head_sha256=self.p["checkpoint_head_sha256"],
                    expected_reviewed=3, expected_video_id=self.video)
        args.update(changes)
        return restore_private_two_turn_bundle(**args)

    def test_01_actual_new_python_interpreter_restores_and_commits_chat_response(self):
        receipt = self.create()
        self.assertEqual((receipt["next_cue_start"],receipt["next_cue_end"]),(4,5))
        self.assertFalse(receipt["e4_approved"])
        self.assertEqual(stat.S_IMODE(self.bundle.stat().st_mode),0o600)
        cli = Path(__file__).with_name("v177_private_turn_checkpoint.py")
        cmd = [sys.executable, str(cli), "restore", "--zip", str(self.bundle),
               "--out-dir", str(self.root / "restored"), "--sha", self.source_sha,
               "--video-id", self.video, "--head", self.p["checkpoint_head_sha256"],
               "--reviewed", "3"]
        process = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        self.assertEqual(process.returncode, 0, process.stderr)
        result = json.loads(process.stdout)
        self.assertEqual(result["next_cue_indices"], [4,5])
        self.assertFalse(result["model_review_performed_by_restore"])
        restored = self.root / "restored"
        new_engine = EngineChatSession(restored / "owner.sqlite",
            (restored / "original.srt").read_bytes(), self.video,
            owner_source_sha256=self.source_sha,
            window_size=3, expected_window_count=2)
        challenge=json.loads((restored / "next_challenge.json").read_text())
        answer=respond(challenge)  # SYNTHETIC reviewer, no hidden LLM.
        out=new_engine.submit(challenge,answer)
        self.assertEqual(out["cues_committed"],2)
        self.assertEqual(new_engine.progress()["cue_reviewed"],5)
        self.assertFalse(new_engine.progress()["e4_pass_claimed"])
        self.assertEqual(self.engine.progress()["cue_reviewed"],3)

    def test_02_missing_private_journal_fails_before_auto_creating_empty_state(self):
        absent = self.root / "lost-journal.sqlite"
        with self.assertRaisesRegex(ValueError,"EXISTING_JOURNAL_MISSING"):
            self.create(db_path=absent)
        self.assertFalse(absent.exists())
        self.assertFalse(self.bundle.exists())

    def test_03_old_wrong_head_rejected_before_any_zip(self):
        with self.assertRaisesRegex(ValueError,"JOURNAL_HEAD_MISMATCH_DO_NOT_RESET"):
            self.create(expected_head_sha256="0"*64)
        self.assertFalse(self.bundle.exists())

    def test_04_reviewed_count_mismatch_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"REVIEWED_COUNT_MISMATCH_DO_NOT_RESET"):
            self.create(expected_reviewed=720)
        self.assertFalse(self.bundle.exists())

    def test_05_wrong_owner_srt_bytes_cannot_export(self):
        self.srt.write_bytes(self.raw + b"\nforged")
        with self.assertRaisesRegex(ValueError,"ORIGINAL_OWNER_BYTES_WRONG"):
            self.create()
        self.assertFalse(self.bundle.exists())

    def test_06_source_and_head_external_pins_mandatory_on_restore(self):
        self.create()
        with self.assertRaisesRegex(ValueError,"EXTERNAL_OWNER_HEAD_PROGRESS_PIN_MISMATCH"):
            self.restore(expected_head_sha256="1"*64)
        self.assertFalse((self.root / "restored").exists())

    def test_07_reject_modified_original_inside_private_bundle(self):
        self.create()
        with zipfile.ZipFile(self.bundle) as z:
            content={i.filename:z.read(i.filename) for i in z.infolist()}
        content["owner.srt"] += b"altered"
        self.bundle.unlink()
        with zipfile.ZipFile(self.bundle,"w") as z:
            for n,b in content.items(): z.writestr(n,b)
        with self.assertRaisesRegex(ValueError,"ARCHIVE_INNER_BYTE_HASH_DRIFT"):
            self.restore()
        self.assertFalse((self.root / "restored").exists())

    def test_08_reject_path_traversal_or_extra_zip_entry(self):
        self.create()
        with zipfile.ZipFile(self.bundle) as z:
            content={i.filename:z.read(i.filename) for i in z.infolist()}
        self.bundle.unlink()
        with zipfile.ZipFile(self.bundle,"w") as z:
            for n,b in content.items(): z.writestr(n,b)
            z.writestr("../../invalid.srt", b"bad")
        with self.assertRaisesRegex(ValueError,"BUNDLE_ENTRIES_UNSAFE"):
            self.restore()

    def test_09_no_restore_overwrite_of_live_existing_journal(self):
        self.create()
        existing=self.root / "existing"
        existing.mkdir()
        existing_db=existing / "owner.sqlite"
        existing_db.write_bytes(b"OWNER_ACTIVE_DATA")
        with self.assertRaisesRegex(ValueError,"RESTORE_DESTINATION_MUST_BE_NEW"):
            self.restore(output_dir=existing)
        self.assertEqual(existing_db.read_bytes(),b"OWNER_ACTIVE_DATA")

    def test_10_unreadable_or_world_exposed_db_fails_export(self):
        os.chmod(self.db, 0o644)
        with self.assertRaisesRegex(ValueError,"INSECURE_DB_MODE"):
            self.create()
        self.assertFalse(self.bundle.exists())

    def test_11_restore_rejects_wrong_video_id(self):
        self.create()
        with self.assertRaisesRegex(ValueError,"EXTERNAL_OWNER_HEAD_PROGRESS_PIN_MISMATCH"):
            self.restore(expected_video_id="DIFFERENT_VIDEO")

    def test_12_corrupted_sqlite_rejected_not_reset(self):
        self.db.write_bytes(b"NOT_A_DATABASE")
        with self.assertRaisesRegex(ValueError,"SQLITE_NOT_VALID"):
            self.create()
        self.assertFalse(self.bundle.exists())

    def test_13_restore_cannot_be_used_twice_to_overwrite_existing_state(self):
        self.create()
        self.restore()
        with self.assertRaisesRegex(ValueError,"RESTORE_DESTINATION_MUST_BE_NEW"):
            self.restore()

    def test_14_original_journal_is_not_mutated_on_export_and_import(self):
        old_bytes = self.db.read_bytes()
        self.create()
        self.restore()
        self.assertEqual(self.db.read_bytes(),old_bytes)
        self.assertEqual(self.engine.progress()["checkpoint_head_sha256"],
                         self.p["checkpoint_head_sha256"])

    def test_15_reject_newly_started_empty_db_as_prior_720_progress(self):
        empty=self.root / "new.sqlite"
        EngineChatSession(empty,self.raw,self.video,
            owner_source_sha256=self.source_sha,window_size=3,
            expected_window_count=2)
        with self.assertRaisesRegex(ValueError,"JOURNAL_HEAD_MISMATCH_DO_NOT_RESET"):
            self.create(db_path=empty, expected_reviewed=720)
        self.assertFalse(self.bundle.exists())


class TestV176OperatorCliNeverSilentlyResets(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)
        self.raw=fixture()
        self.srt=self.path / "owner.srt"
        self.srt.write_bytes(self.raw)
        self.db=self.path / "private.sqlite"
        self.video="AbCdEf12345"
        self.sha=sha256(self.raw)
        self.cli=Path(__file__).with_name('v176_chat_engine_cli.py')

    def call(self,*opts,db=None,action='progress'):
        command=[sys.executable,str(self.cli),'--srt',str(self.srt),
             '--sha',self.sha,'--video-id',self.video,
             '--db',str(db or self.db),'--window-size','3',
             '--windows','2',*opts,action]
        return subprocess.run(command,capture_output=True,text=True,timeout=15)

    def test_16_operator_cli_cannot_silently_start_empty_on_resume(self):
        p=self.call()
        self.assertNotEqual(p.returncode,0)
        self.assertIn('V177_MISSING_EXISTING_JOURNAL_DO_NOT_RESET',p.stderr)
        self.assertFalse(self.db.exists())

    def test_17_explicit_new_session_is_the_only_new_db_path(self):
        p=self.call('--new-session',action='next-meaning')
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertTrue(self.db.is_file())
        self.assertEqual(stat.S_IMODE(self.db.stat().st_mode),0o600)
        self.assertEqual(json.loads(p.stdout)['target_cues'][0]['cue_index'],1)
        self.assertEqual(self.call().returncode,0)

    def test_18_new_session_flag_refuses_to_overwrite_existing(self):
        self.assertEqual(self.call('--new-session',action='next').returncode,0)
        p=self.call('--new-session',action='next')
        self.assertNotEqual(p.returncode,0)
        self.assertIn('V177_NEW_SESSION_REQUIRES_ABSENT_JOURNAL',p.stderr)

    def test_19_restore_external_head_check_and_wrong_head(self):
        self.assertEqual(self.call('--new-session',action='next-meaning').returncode,0)
        e=EngineChatSession(self.db,self.raw,self.video,
            owner_source_sha256=self.sha,window_size=3,expected_window_count=2)
        ch=e.prepare(limit=3,source_first_only=True)
        e.submit(ch,respond(ch))
        progress=e.progress()
        proper=self.call('--resume-head',progress['checkpoint_head_sha256'],
                         '--resume-reviewed','3')
        self.assertEqual(proper.returncode,0,proper.stderr)
        bad=self.call('--resume-head','0'*64,'--resume-reviewed','3')
        self.assertNotEqual(bad.returncode,0)
        self.assertIn('V177_RESUME_PIN_MISMATCH_DO_NOT_RESET',bad.stderr)
        self.assertEqual(e.progress()['cue_reviewed'],3)

    def test_20_partial_external_checkpoint_pins_fail_closed(self):
        self.assertEqual(self.call('--new-session',action='next').returncode,0)
        p=self.call('--resume-reviewed','3')
        self.assertNotEqual(p.returncode,0)
        self.assertIn('V177_RESUME_HEAD_AND_COUNT_MUST_BOTH_BE_GIVEN',p.stderr)



if __name__ == "__main__": unittest.main()