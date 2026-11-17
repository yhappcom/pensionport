"""E4 simulated operator vault: exact V128/V126 SQLite, no real keys.

All secrets are generated within isolated CI temp directories, never GitHub.
No live B0001 knowledge is published or personally advised.
"""
from __future__ import annotations

import json
import os
import sqlite3
import stat
import tempfile
import unittest
from pathlib import Path

from ire.v6.errors import InvalidInput, QualityNotProven
from test_v166_e4_primary_approval_gate import V166E4E3V128RealSQLiteIntegration
from v166_e4_operator_trust import E4OperatorTrust

class V166E4OperatorTrustFileTests(unittest.TestCase):
    def setUp(self):
        self.fx=V166E4E3V128RealSQLiteIntegration(
            "test_14_both_valid_synthetic_children_do_publish_research_only")
        self.fx.setUp()
        self.addCleanup(self.fx.doCleanups)
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        vault=Path(self.tmp.name)/"operator-vault"
        vault.mkdir(mode=0o700)
        self.key=vault/"e4.key"
        self.pin=vault/"latest.e4.pin"
        self.key.write_bytes(os.urandom(48))
        self.key.chmod(0o600)
        self.path=self.fx.fx.knowledge.path
        self.op=E4OperatorTrust(
            self.path,key_path=str(self.key),latest_pin_path=str(self.pin))
        self.store=self.op.open_for_new_parent()
        self.fx.fx.knowledge=self.store

    def _publish(self):
        result=self.fx.run_guarded()
        self.assertEqual(result["status"],"E4_PARENT_RESEARCH_CANDIDATES_PUBLISHED")
        pin=result["e4_external_owner_pin_sha256"]
        return pin

    def _pin(self):
        pin=self._publish()
        receipt=self.op.commit_signed_parent_pin(
            self.store,pin,expected_previous_pin=None)
        self.assertEqual(receipt["status"],"E4_OPERATOR_OWNER_PIN_COMMITTED")
        return pin

    def test_01_actual_sqlite_parent_and_secure_external_pin_read(self):
        pin=self._pin()
        stored,got,receipt=self.op.open_verified_read()
        self.assertEqual(pin,got)
        self.assertEqual(receipt["parent_count"],1)
        self.assertEqual(receipt["knowledge_count"],3)
        self.assertEqual(stat.S_IMODE(self.pin.stat().st_mode),0o600)
        self.assertFalse(receipt["personal_investment_advice_approved"])
        self.assertEqual(stored.path,self.path)

    def test_02_only_sqlite_seal_without_external_latest_pin_does_not_trust(self):
        self._publish()
        with self.assertRaises(QualityNotProven):
            self.op.open_verified_read()

    def test_03_same_db_legacy_row_mutation_invalidates_external_approval(self):
        self._pin()
        with sqlite3.connect(str(self.path)) as db:
            db.execute("UPDATE knowledge SET entry_json='{}' "
                       "WHERE knowledge_id=(SELECT knowledge_id FROM knowledge LIMIT 1)")
        with self.assertRaises(QualityNotProven):
            self.op.open_verified_read()

    def test_04_owner_pin_wrong_value_fails_closed(self):
        self._pin()
        self.pin.write_text("0"*64+"\n",encoding="ascii")
        self.pin.chmod(0o600)
        with self.assertRaises(QualityNotProven):
            self.op.open_verified_read()

    def test_05_wrong_secret_does_not_verify_valid_owner_pin(self):
        self._pin()
        self.key.write_bytes(os.urandom(48))
        self.key.chmod(0o600)
        another=E4OperatorTrust(
            self.path,key_path=str(self.key),latest_pin_path=str(self.pin))
        with self.assertRaises(QualityNotProven):
            another.open_verified_read()

    def test_06_second_cas_without_matching_prior_pin_refused(self):
        pin=self._pin()
        with self.assertRaisesRegex(QualityNotProven,"PIN_COMPARE_AND_SWAP_CONFLICT"):
            self.op.commit_signed_parent_pin(
                self.store,pin,expected_previous_pin=None)

    def test_07_key_world_readable_rejected(self):
        self.key.chmod(0o644)
        with self.assertRaisesRegex(InvalidInput,"OWNER_FILE_NOT_PRIVATE_0600"):
            E4OperatorTrust(
                self.path,key_path=str(self.key),latest_pin_path=str(self.pin))

    def test_08_key_symlink_to_same_bytes_rejected(self):
        link=self.key.parent/"key-symlink"
        link.symlink_to(self.key)
        with self.assertRaises(InvalidInput):
            E4OperatorTrust(
                self.path,key_path=str(link),latest_pin_path=str(self.pin))

    def test_09_pin_path_in_same_db_directory_rejected(self):
        with self.assertRaisesRegex(InvalidInput,"OUTSIDE_DATABASE_DIRECTORY"):
            E4OperatorTrust(
                self.path,key_path=str(self.key),
                latest_pin_path=str(self.path.parent/"owner.pin"))

    def test_10_private_operator_directory_required(self):
        self.key.parent.chmod(0o755)
        with self.assertRaisesRegex(InvalidInput,"PRIVATE_OPERATOR_DIR_OWNER"):
            E4OperatorTrust(
                self.path,key_path=str(self.key),latest_pin_path=str(self.pin))

    def test_11_source_db_file_without_approved_root_not_retro_certified(self):
        with self.assertRaises(QualityNotProven):
            self.op.open_verified_read()

    def test_12_commit_forged_pin_without_matching_hmac_refused(self):
        pin=self._publish()
        with self.assertRaises(QualityNotProven):
            self.op.commit_signed_parent_pin(
                self.store,"a"*64,expected_previous_pin=None)
        self.assertFalse(self.pin.exists())
        self.op.commit_signed_parent_pin(
            self.store,pin,expected_previous_pin=None)

if __name__=="__main__":
    unittest.main()
