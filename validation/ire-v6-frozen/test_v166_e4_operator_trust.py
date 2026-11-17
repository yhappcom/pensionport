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

class V166E4OperatorCertifiedE2ReadIntegration(unittest.TestCase):
    def setUp(self):
        from test_v166_e4_certified_source_retrieval import (
            V166E4CertifiedE2ContextRealSqliteTests)
        self.pilot=V166E4CertifiedE2ContextRealSqliteTests(
            "test_01_certified_source_quote_separate_chat_caution_not_legacy_proposition")
        self.pilot.setUp()
        self.addCleanup(self.pilot.doCleanups)
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        path=Path(self.tmp.name)/"owner-private"
        path.mkdir(mode=0o700)
        self.key=path/"owner.key"
        self.pin=path/"latest.pin"
        self.key.write_bytes(os.urandom(48))
        self.key.chmod(0o600)
        self.op=E4OperatorTrust(
            self.pilot.fx.knowledge.path,key_path=str(self.key),
            latest_pin_path=str(self.pin))
        self.pilot.fx.knowledge=self.op.open_for_new_parent()

    def publish(self):
        pin,ids=self.pilot._approved_pin_and_ids()
        self.op.commit_signed_parent_pin(
            self.pilot.fx.knowledge,pin,expected_previous_pin=None)
        return pin,ids

    def test_13_real_sqlite_e2_source_separated_operational_read(self):
        pin,ids=self.publish()
        d=self.op.certified_research_context(
            "투자 수익 가정과 조건 검토",
            source=self.pilot.e2.source,
            exchange=self.pilot.e2.exchange,
            ledger=self.pilot.e2.ledger,
            selected_knowledge_ids=ids)
        self.assertEqual(d["e4_operator_schema"],
                         "IRE_V166_E4_SEPARATE_OPERATOR_TRUST_STORE_V1")
        self.assertEqual(d["e4_external_owner_pin_sha256"],pin)
        self.assertTrue(d["operator_external_latest_pin_verified"])
        self.assertEqual(d["count"],1)
        self.assertNotIn("proposition",d["claims"][0])
        self.assertFalse(d["personal_investment_advice_approved"])

    def test_14_operator_read_without_pin_before_commit_denied(self):
        pin,ids=self.pilot._approved_pin_and_ids()
        with self.assertRaises(QualityNotProven):
            self.op.certified_research_context(
                "수익",source=self.pilot.e2.source,
                exchange=self.pilot.e2.exchange,
                ledger=self.pilot.e2.ledger,
                selected_knowledge_ids=ids)

    def test_15_operator_read_refuses_wrong_e2_reviewer_hash(self):
        import copy
        pin,ids=self.publish()
        bad=copy.deepcopy(self.pilot.e2.ledger)
        bad["rows"][0]["reviewer_note_sha256"]="f"*64
        with self.assertRaises(InvalidInput):
            self.op.certified_research_context(
                "수익",source=self.pilot.e2.source,
                exchange=self.pilot.e2.exchange,
                ledger=bad,selected_knowledge_ids=ids)


class V166E4OperatorOneTurnParentTests(unittest.TestCase):
    def setUp(self):
        from test_v166_e4_primary_approval_gate import (
            V166E4E3V128RealSQLiteIntegration)
        self.pilot=V166E4E3V128RealSQLiteIntegration(
            "test_14_both_valid_synthetic_children_do_publish_research_only")
        self.pilot.setUp()
        self.addCleanup(self.pilot.doCleanups)
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)/"private-operator"
        root.mkdir(mode=0o700)
        key=root/"operator.key"
        key.write_bytes(os.urandom(48))
        key.chmod(0o600)
        self.pin=root/"latest.pin"
        self.operator=E4OperatorTrust(
            self.pilot.fx.knowledge.path,
            key_path=str(key),latest_pin_path=str(self.pin))

    def run_parent(self):
        from unittest.mock import patch
        from test_v166_e4_primary_approval_gate import BODY
        from v166_e4_operator_trust import run_e4_with_external_owner_pin
        fx=self.pilot.fx
        with patch("v166_e4_primary_approval_gate._fetch_approved_primary_https",
                   return_value=BODY):
            return run_e4_with_external_owner_pin(
                self.operator,fx.checkpoint,
                review_or_load_child=fx.child,
                review_seams=fx.seams,
                review_parent=fx.parent_review,
                primary_manifest_for_child=lambda sid,case:self.pilot.manifests.get(sid),
                expected_knowledge_head="0"*64,
                now_as_of="2026-11-17")

    def test_16_one_turn_e4_publishes_only_after_private_external_pin_durable(self):
        r=self.run_parent()
        self.assertEqual(r["schema"],"IRE_V166_E4_OPERATOR_PARENT_RELEASE_V1")
        self.assertEqual(r["status"],"E4_PARENT_RESEARCH_CANDIDATES_PUBLISHED")
        self.assertTrue(r["external_owner_pin_committed"])
        self.assertEqual(r["certified_child_scope_count"],2)
        self.assertEqual(self.operator.read_latest_pin(),
                         r["operator_latest_pin_sha256"])
        self.assertFalse(r["formal_financial_law_certified"])
        self.assertFalse(r["personal_advice_approved"])

    def test_17_unverified_second_child_does_not_commit_pin_or_knowledge(self):
        del self.pilot.manifests[self.pilot.fx.checkpoint.child_ids[1]]
        r=self.run_parent()
        self.assertEqual(r["status"],"E4_HOLD_UNVERIFIED_CHILD")
        self.assertFalse(r["external_owner_pin_committed"])
        self.assertFalse(self.pin.exists())
        self.assertEqual(self.pilot.fx._counts().get("knowledge",0),0)

    def test_18_missing_external_pin_after_parent_commit_cannot_be_trusted(self):
        r=self.run_parent()
        self.pin.unlink()
        self.assertTrue(r["all_video_knowledge_published"])
        with self.assertRaises(QualityNotProven):
            self.operator.open_verified_read()


if __name__=="__main__":
    unittest.main()
