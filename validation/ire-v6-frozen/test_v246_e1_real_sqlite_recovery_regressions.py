"""P0-1-04: native V123→E4→V128→E5 SQLite fault / restart regression.

All content, official HTTPS responses and review decisions are synthetic;
the SQLite engine, sealed store, V123, E4, V128, source/checkpoint hashes
and all physical tables execute FOR REAL.

'zero partial parent publication' concerns no approved *subset* of a parent.
An abrupt crash after full SQLite commit but before external sidecar sealing
CAN leave a physically complete but UNSEALED parent. It is untrusted and must
remain blocked: this suite explicitly documents that recovery limitation.
"""
from __future__ import annotations

import copy
import sqlite3
import unittest
from pathlib import Path
from unittest.mock import patch

import test_v243_canonical_e1_e5_route as fixtures
from ire.v6.codec import ZERO_SHA
from ire.v6.errors import InvalidInput, QualityNotProven
from v166_e4_sealed_knowledge import E4SealedKnowledgeStore
from v126_chat_approved_knowledge_store import PrivateKnowledgeStore
import v128_atomic_parent_knowledge as atomic

KEY=b"SYNTHETIC_TEST_KEY_FOR_GUARDED_CI_"*2


class EndToEndPrivateSQLiteRecovery(unittest.TestCase):
    def setUp(self):
        self.h=fixtures.CanonicalRouteContractTests(
            "test_01_manual_turns_reach_actual_v123_e4_e5_without_forged_host_success")
        self.h.setUp()
        self.addCleanup(self.h.doCleanups)
        self.fx=self.h.f.fx
        self.db=self.fx.knowledge.path
        self.seal=Path(str(self.db)+".e4seal.json")

    def table_counts(self):
        with sqlite3.connect(str(self.db)) as con:
            names={row[0] for row in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            return {name:con.execute("SELECT COUNT(*) FROM "+name).fetchone()[0]
                    if name in names else 0
                    for name in ("events","knowledge","parent_publications")}

    def assert_empty(self):
        self.assertEqual(self.table_counts(),
                         {"events":0,"knowledge":0,"parent_publications":0})
        self.assertFalse(self.seal.exists())

    def run_route(self,**changes):
        with patch("v166_e4_primary_approval_gate._fetch_approved_primary_https",
                   return_value=fixtures.BODY):
            return self.h.run_route(**changes)

    def refresh_owner_checkpoint_head(self):
        head=self.fx.checkpoint.progress()["checkpoint_head_sha256"]
        self.h.head=head
        self.h.a["owner_head_sha256"]=head
        self.h.b["owner_head_sha256"]=head
        return head

    def reopen_with_owner_pin(self,pin):
        self.fx.knowledge=E4SealedKnowledgeStore(
            self.db,external_signing_key=KEY,prior_owner_pin=pin)

    def test_01_native_full_parent_commit_and_owner_seal(self):
        result=self.run_route()
        self.assertTrue(result["e5_new_parent_committed"])
        self.assertFalse(result["e5_idempotent_replay_no_new_sqlite_rows"])
        self.assertEqual(self.table_counts(),
                         {"events":3,"knowledge":3,"parent_publications":1})
        self.assertTrue(self.seal.exists())
        audited=self.fx.knowledge.verify_e4_certificate(
            externally_pinned_seal_sha256=result[
                "e4_external_pin_returned_not_yet_owner_custodied"])
        self.assertEqual((audited["knowledge_count"],audited["parent_count"]),(3,1))
        self.assertFalse(result["formal_financial_fact_approved"])
        self.assertFalse(result["personal_advice_approved"])

    def test_02_missing_second_user_command_writes_no_row(self):
        r=self.run_route(second_user_turn=None)
        self.assertFalse(r["e4_invoked"])
        self.assert_empty()

    def test_03_missing_second_child_official_primary_never_partially_publishes(self):
        missing=self.fx.checkpoint.child_ids[-1]
        del self.h.f.manifests[missing]
        result=self.run_route()
        self.assertEqual(result["status"],"HOLD_E4_PRIMARY_EVIDENCE")
        self.assertFalse(result["e5_invoked"])
        self.assert_empty()

    def test_04_financial_primary_redirect_rejected_before_knowledge(self):
        sid=self.fx.checkpoint.child_ids[-1]
        self.h.f.manifests[sid]["rows"][0]["official_url"]=(
            "https://www.nts.go.kr.attacker.invalid/fake")
        with self.assertRaises(InvalidInput):
            self.run_route()
        self.assert_empty()

    def test_05_v123_open_not_reclassified_as_approved(self):
        case=self.fx.packets[1]["case"]
        case["chat_review"]["atom_verdicts"][0]["status"]="OPEN"
        outcome=self.run_route()
        self.assertEqual(outcome["status"],"HOLD_E4_PRIMARY_EVIDENCE")
        self.assert_empty()

    def test_06_original_source_tamper_fails_before_sqlite(self):
        with self.assertRaises(QualityNotProven):
            self.run_route(original_source_raw=self.fx.checkpoint.raw+b"tamper")
        self.assert_empty()

    def test_07_interruption_after_all_child_checks_then_replay_with_new_owner_head(self):
        def interrupted(*_):
            raise RuntimeError("SYNTHETIC_AFTER_ALL_CHILD_CHECKPOINTS_BEFORE_PARENT")
        with self.assertRaisesRegex(RuntimeError,"SYNTHETIC_AFTER_ALL_CHILD"):
            self.run_route(review_seams=interrupted)
        self.assert_empty()
        self.assertEqual(self.fx.checkpoint.progress()["passed_child_scopes"],2)
        self.assertNotEqual(self.refresh_owner_checkpoint_head(),ZERO_SHA)
        result=self.run_route()
        self.assertTrue(result["e5_new_parent_committed"])
        self.assertEqual(self.table_counts()["parent_publications"],1)

    def test_08_identical_parent_replay_with_old_owner_pin_has_zero_new_rows(self):
        first=self.run_route()
        pin=first["e4_external_pin_returned_not_yet_owner_custodied"]
        baseline=self.fx.knowledge._logical_fingerprint()
        original_seal=self.seal.read_bytes()
        self.refresh_owner_checkpoint_head()
        self.reopen_with_owner_pin(pin)
        result=self.run_route(expected_knowledge_head=ZERO_SHA)
        self.assertEqual(result["status"],
                         "RESEARCH_CANDIDATE_PARENT_IDEMPOTENT_REPLAY_NO_NEW_WRITE")
        self.assertFalse(result["e5_new_parent_committed"])
        self.assertTrue(result["e5_idempotent_replay_no_new_sqlite_rows"])
        self.assertEqual(self.fx.knowledge._logical_fingerprint(),baseline)
        self.assertEqual(self.seal.read_bytes(),original_seal)
        self.assertEqual(result["e4_external_pin_returned_not_yet_owner_custodied"],pin)
        self.assertEqual(self.table_counts()["parent_publications"],1)

    def test_09_existing_parent_requires_actual_prior_owner_pin_for_replay(self):
        first=self.run_route()
        counts=self.table_counts()
        self.refresh_owner_checkpoint_head()
        self.reopen_with_owner_pin(None)
        with self.assertRaisesRegex(QualityNotProven,
                                     "PREVIOUS_EXTERNAL_OWNER_PIN_REQUIRED"):
            self.run_route(expected_knowledge_head=ZERO_SHA)
        self.assertEqual(self.table_counts(),counts)
        self.assertEqual(self.table_counts()["parent_publications"],1)

    def test_10_replay_tampered_child_review_cannot_change_pinned_seal(self):
        first=self.run_route()
        pin=first["e4_external_pin_returned_not_yet_owner_custodied"]
        baseline=self.fx.knowledge._logical_fingerprint()
        seal_bytes=self.seal.read_bytes()
        self.refresh_owner_checkpoint_head()
        self.reopen_with_owner_pin(pin)
        self.fx.packets[-1]["case"]["chat_review"]["atom_verdicts"][0]["status"]="OPEN"
        # V166 may classify a changed CHAT verdict as a real E4 HOLD
        # rather than raise. Neither response may alter the sealed store.
        result=self.run_route(expected_knowledge_head=ZERO_SHA)
        self.assertEqual(result["status"],"HOLD_E4_PRIMARY_EVIDENCE")
        self.assertFalse(result["e5_invoked"])
        self.assertEqual(self.fx.knowledge._logical_fingerprint(),baseline)
        self.assertEqual(self.seal.read_bytes(),seal_bytes)

    def test_11_exception_inside_parent_sqlite_transaction_rolls_back_all_rows(self):
        original=atomic._replay_parent_publications
        def fail_in_commit(con,head):
            if (con.in_transaction and
                con.execute("SELECT COUNT(*) FROM parent_publications").fetchone()[0]>0):
                raise RuntimeError("SYNTHETIC_FAILURE_INSIDE_DURABLE_PARENT_TX")
            return original(con,head)
        with patch("v128_atomic_parent_knowledge._replay_parent_publications",
                   side_effect=fail_in_commit):
            with self.assertRaisesRegex(RuntimeError,"SYNTHETIC_FAILURE_INSIDE"):
                self.run_route()
        self.assert_empty()

    def test_12_after_sqlite_commit_before_seal_is_not_certified_or_republished(self):
        with patch("v166_e4_sealed_knowledge.os.replace",
                   side_effect=OSError("SYNTHETIC_SEAL_CRASH")):
            with self.assertRaisesRegex(OSError,"SYNTHETIC_SEAL_CRASH"):
                self.run_route()
        # Real limitation: FULL 3-row parent physically committed but NOT
        # CERTIFIED. No orphaned *partial subset* or authorized E5 exists.
        self.assertEqual(self.table_counts(),
                         {"events":3,"knowledge":3,"parent_publications":1})
        self.assertFalse(self.seal.exists())
        with self.assertRaises(QualityNotProven):
            self.fx.knowledge.verify_e4_certificate(
                externally_pinned_seal_sha256="a"*64)
        self.refresh_owner_checkpoint_head()
        self.reopen_with_owner_pin(None)
        with self.assertRaisesRegex(QualityNotProven,
                                     "EXISTING_UNCERTIFIED_LEGACY_ROWS"):
            self.run_route(expected_knowledge_head=ZERO_SHA)
        self.assertEqual(self.table_counts()["parent_publications"],1)

    def test_16_orphan_crash_private_forensic_quarantine_enables_clean_owner_retry(self):
        import tempfile
        with patch("v166_e4_sealed_knowledge.os.replace",
                   side_effect=OSError("SYNTHETIC_AFTER_ALL_PARENT_ROWS")):
            with self.assertRaisesRegex(OSError,"SYNTHETIC_AFTER_ALL_PARENT_ROWS"):
                self.run_route()
        state=self.fx.knowledge._logical_fingerprint()
        self.assertEqual(state["parent_count"],1)
        self.assertFalse(self.seal.exists())
        with tempfile.TemporaryDirectory(prefix="p104_private_",
                                         dir=str(self.db.parent)) as private:
            receipt=self.fx.knowledge.quarantine_unsealed_parent(
                expected_unsealed_rows_sha256=state["canonical_sqlite_rows_sha256"],
                private_quarantine_dir=private)
            self.assertEqual(receipt["quarantine_parent_count"],1)
            forensic=Path(receipt["forensic_private_database_path"])
            self.assertTrue(forensic.is_file())
            archived=E4SealedKnowledgeStore(
                forensic,external_signing_key=KEY)
            self.assertEqual(archived._logical_fingerprint(),state)
            self.assert_empty()
            # The two child source-first verdicts were durably checkpointed
            # before the seal crash. Only their freshly pinned checkpoint
            # may be reused, and ALL children are replayed before E4 seals.
            self.refresh_owner_checkpoint_head()
            recovered=self.run_route()
            self.assertTrue(recovered["e5_new_parent_committed"])
            self.assertEqual(self.table_counts(),
                             {"events":3,"knowledge":3,"parent_publications":1})
            self.assertTrue(self.seal.exists())

    def test_17_orphan_quarantine_wrong_rows_pin_refuses_destructive_reset(self):
        import tempfile
        with patch("v166_e4_sealed_knowledge.os.replace",
                   side_effect=OSError("SYNTHETIC_BEFORE_EXTERNAL_SEAL")):
            with self.assertRaises(OSError):
                self.run_route()
        before=self.table_counts()
        with tempfile.TemporaryDirectory(prefix="p104_private_",
                                         dir=str(self.db.parent)) as private:
            with self.assertRaisesRegex(QualityNotProven,
                                        "FULL_UNSEALED_PARENT_OR_SOURCE"):
                self.fx.knowledge.quarantine_unsealed_parent(
                    expected_unsealed_rows_sha256="0"*64,
                    private_quarantine_dir=private)
        self.assertEqual(self.table_counts(),before)
        self.assertFalse(self.seal.exists())

    def test_18_already_sealed_parent_cannot_be_quarantined_or_deleted(self):
        import tempfile
        result=self.run_route()
        state=self.fx.knowledge._logical_fingerprint()
        with tempfile.TemporaryDirectory(prefix="p104_private_",
                                         dir=str(self.db.parent)) as private:
            with self.assertRaisesRegex(QualityNotProven,
                                        "SEALED_DATABASE_MUST_NOT_ENTER"):
                self.fx.knowledge.quarantine_unsealed_parent(
                    expected_unsealed_rows_sha256=state["canonical_sqlite_rows_sha256"],
                    private_quarantine_dir=private)
        self.assertEqual(self.table_counts()["parent_publications"],1)
        self.fx.knowledge.verify_e4_certificate(
            externally_pinned_seal_sha256=result[
                "e4_external_pin_returned_not_yet_owner_custodied"])

    def test_13_legacy_raw_sqlite_mutation_breaks_certified_readback(self):
        result=self.run_route()
        pin=result["e4_external_pin_returned_not_yet_owner_custodied"]
        with sqlite3.connect(str(self.db)) as con:
            con.execute("UPDATE knowledge SET entry_json='{}' WHERE "
                        "knowledge_id=(SELECT knowledge_id FROM knowledge LIMIT 1)")
        with self.assertRaises(QualityNotProven):
            self.fx.knowledge.verify_e4_certificate(
                externally_pinned_seal_sha256=pin)
        self.assertEqual(self.table_counts()["parent_publications"],1)

    def test_14_unresolved_cross_parent_is_private_review_hold_no_sqlite(self):
        overlay,kwargs=self.h._synthetic_typed_parent_stub(cross_atoms=1)
        with patch("v243_canonical_e1_e5_route.verify_typed_parent_review_overlay",
                   return_value={"status":"PARENT_TYPED_CHILD_INPUTS_SOURCE_VERIFIED_NOT_APPROVED"}):
            result=self.run_route(**kwargs)
        self.assertEqual(result["status"],
                         "HOLD_PARENT_CROSS_CHILD_SEMANTIC_REVIEW_REQUIRED")
        self.assertEqual(result["unapproved_cross_child_parent_atoms"],1)
        self.assertFalse(result["e4_invoked"])
        self.assertFalse(result["e5_invoked"])
        self.assert_empty()

    def test_15_second_child_not_chat_approved_has_zero_approved_partial_rows(self):
        # First native child can PASS checkpoint while second is held; no
        # durable E4 authorisation / child-only stored knowledge is allowed.
        self.fx.packets[-1]["case"]["chat_review"]["atom_verdicts"][0][
            "status"]="REJECT"
        outcome=self.run_route()
        self.assertFalse(outcome["e5_invoked"])
        self.assert_empty()


if __name__=="__main__":
    unittest.main()
