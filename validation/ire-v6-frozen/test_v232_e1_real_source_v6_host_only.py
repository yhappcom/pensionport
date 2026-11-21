"""V232 real-host seam regression with SYNTHETIC source, never owner evidence.

The private 250-cue ETF real-source staging is run OFFLINE and kept out of
GitHub. This CI fixture tests the exact production handoff, including V231
source-note proof, protected 116+29 Git bytes, all pending atom relations and
real SQLite persistence. It cannot establish financial semantic quality.
"""
from __future__ import annotations

import copy
import sqlite3
import tempfile
import unittest
from pathlib import Path

import test_v202_e1_v176_native_positive_path as v202_fixture
import test_v231_e1_v228_private_turn2_custody_bridge as v231_fixture

from ire.v6 import TransactionStore
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v231_e1_v228_private_turn2_custody_bridge import (
    stage_after_verified_private_turn2,
)


class TestV232NativeRealSqliteAfterTurn2Proof(unittest.TestCase):
    def setUp(self):
        note = v231_fixture.TestV231Turn2ReviewCustody(
            "test_01_synthetic_internal_second_turn_and_quarantine_valid")
        note.setUp()
        self.addCleanup(note.doCleanups)
        self.note = note
        prior_fx = v202_fixture.TestV202SameInputE1Route(
            "test_01_preseeded_native_v166_cannot_impersonate_v176_verdict")
        prior_fx.setUp()
        self.addCleanup(prior_fx.doCleanups)
        self.prior = copy.deepcopy(
            prior_fx.fx.fx.packets[0]["case"]["prior_knowledge"])
        self.prior["relations"] = [{
            "claim_id": a["claim_id"],
            "candidate_source_sha256": note.origin["source_sha256"],
            "target_kind": "NONE",
            "target_id": None,
            "target_content_sha256": None,
            "relationship": "NOVEL_PENDING",
            "rationale": "SYNTHETIC relation unapproved and unreconciled",
            "independent_semantic_review_verified": False,
            "personalized_action_approved": False,
        } for a in note.origin["exchange"]["atoms"]]
        self.root = tempfile.TemporaryDirectory()
        self.addCleanup(self.root.cleanup)
        self.folder = Path(self.root.name)

    def args(self, *, native_store, prior=None, note=None, escrow=None):
        v = self.note
        return dict(
            origin=v.origin, second_receipt=v.receipt,
            private_source_note=v.synthetic_note if note is None else note,
            prequarantine=v.escrow if escrow is None else escrow,
            externally_pinned_receipt_sha256=
                v.pins["externally_pinned_receipt_sha256"],
            externally_pinned_source_note_sha256=
                v.pins["externally_pinned_source_note_sha256"],
            externally_pinned_prequarantine_sha256=
                v.pins["externally_pinned_prequarantine_sha256"],
            native_store=native_store,
            scope_id="v232_synthetic_original_e1_host",
            run_id="v232_synthetic_source_native_host_only",
            externally_pinned_inventory_sha256=v.origin["inventory_sha256"],
            prior_knowledge=self.prior if prior is None else prior,
            explicit_private_host_stage=True,
        )

    def test_01_full_v231_to_actual_v6_sqlite_commit_is_unapproved(self):
        folder = self.folder/"private"
        folder.mkdir(mode=0o700)
        store = TransactionStore(folder/"native.db")
        out = stage_after_verified_private_turn2(
            **self.args(native_store=store))
        snap = store.snapshot("v232_synthetic_original_e1_host")
        reopened = TransactionStore(folder/"native.db").snapshot(
            "v232_synthetic_original_e1_host")
        self.assertEqual(snap["ledger_head_sha256"],
                         out["new_v6_host_event_sha256"])
        self.assertEqual(reopened["ledger_head_sha256"],
                         out["new_v6_host_event_sha256"])
        self.assertTrue(out["v231_source_review_custody_verified"])
        self.assertFalse(out["e1_full_approval_store_path_proven"])
        self.assertFalse(out["e3_final_approved"])
        self.assertFalse(out["e4_authorized"])
        self.assertEqual(out["e5_published"], 0)
        self.assertEqual(snap["progress"]["model_windows_recorded"], 1)
        self.assertEqual(snap["progress"][
            "unverified_current_revision_review_proposals"], 1)
        with sqlite3.connect(folder/"native.db") as db:
            tables = {x[0] for x in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertTrue({"events","scopes"}.issubset(tables))
            self.assertNotIn("knowledge", tables)
            self.assertNotIn("parent_publications",tables)

    def test_02_no_private_prior_relation_cannot_create_scope(self):
        folder = self.folder/"private"; folder.mkdir(mode=0o700)
        store = TransactionStore(folder/"native.db")
        knowledge = copy.deepcopy(self.prior)
        knowledge["relations"].pop()
        with self.assertRaisesRegex(InvalidInput,
                                    "PRIOR_EVERY_HOST_ATOM_REQUIRES_RELATION"):
            stage_after_verified_private_turn2(
                **self.args(native_store=store, prior=knowledge))
        with self.assertRaisesRegex(InvalidInput,"SCOPE_UNKNOWN"):
            store.snapshot("v232_synthetic_original_e1_host")

    def test_03_claimed_gold_or_approval_cannot_be_staged(self):
        folder = self.folder/"private"; folder.mkdir(mode=0o700)
        store = TransactionStore(folder/"native.db")
        bad = copy.deepcopy(self.note.synthetic_note)
        bad["e3_formal_approved"] = True
        with self.assertRaisesRegex(InvalidInput,"PRIVATE_NOTE_BYTE_PIN"):
            stage_after_verified_private_turn2(
                **self.args(native_store=store,note=bad))
        with self.assertRaisesRegex(InvalidInput,"SCOPE_UNKNOWN"):
            store.snapshot("v232_synthetic_original_e1_host")

    def test_04_legacy_protected_blob_substitution_precedes_host_write(self):
        folder = self.folder/"private"; folder.mkdir(mode=0o700)
        store = TransactionStore(folder/"native.db")
        knowledge = copy.deepcopy(self.prior)
        knowledge["master116_bytes"] += b"\nUNAUTHORIZED\n"
        with self.assertRaisesRegex(InvalidInput,
                                    "MASTER116_PROTECTED_GIT_BLOB_DRIFT"):
            stage_after_verified_private_turn2(
                **self.args(native_store=store, prior=knowledge))
        with self.assertRaisesRegex(InvalidInput,"SCOPE_UNKNOWN"):
            store.snapshot("v232_synthetic_original_e1_host")


if __name__ == "__main__":
    unittest.main()
