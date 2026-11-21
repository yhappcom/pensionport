"""V233 E1 regression: genuine V127 child PLAN, NEVER fake financial approval.

The live 250-cue ETF is privately exercised outside GitHub. Here the same
production bridge runs on a V228-shaped synthetic 8-cue source/real V6 store.
"""
from __future__ import annotations

import copy
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from ire.v6 import TransactionStore
from ire.v6.codec import ZERO_SHA
from ire.v6.errors import InvalidInput, QualityNotProven, LedgerCorrupted
import test_v202_e1_v176_native_positive_path as v202_fixture
import test_v231_e1_v228_private_turn2_custody_bridge as v231_fixture
from v231_e1_v228_private_turn2_custody_bridge import stage_after_verified_private_turn2
from v233_e1_v228_actual_parent_checkpoint_preflight import (
    open_new_real_v1271_checkpoint, require_actual_e1_full_release_ready,
    verify_v232_source_native_host,
)


class TestV233NativeV127Handoff(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Source is test fixture; never the private owner ETF.
        pass

    def setUp(self):
        case = v231_fixture.TestV231Turn2ReviewCustody(
            'test_01_synthetic_internal_second_turn_and_quarantine_valid')
        case.setUp()
        self.addCleanup(case.doCleanups)
        self.case = case
        legacy = v202_fixture.TestV202SameInputE1Route(
            'test_01_preseeded_native_v166_cannot_impersonate_v176_verdict')
        legacy.setUp()
        self.addCleanup(legacy.doCleanups)
        knowledge = copy.deepcopy(legacy.fx.fx.packets[0]['case']['prior_knowledge'])
        knowledge['relations'] = [dict(
            claim_id=a['claim_id'],
            candidate_source_sha256=case.origin['source_sha256'],
            target_kind='NONE', target_id=None,
            target_content_sha256=None, relationship='NOVEL_PENDING',
            rationale='SYNTHETIC candidate relation remains unapproved',
            independent_semantic_review_verified=False,
            personalized_action_approved=False,
        ) for a in case.origin['exchange']['atoms']]
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.priv = self.root/'private'
        self.priv.mkdir(mode=0o700)
        self.store = TransactionStore(self.priv/'host.db')
        out = stage_after_verified_private_turn2(
            origin=case.origin, second_receipt=case.receipt,
            private_source_note=case.synthetic_note,
            prequarantine=case.escrow,
            externally_pinned_receipt_sha256=
                case.pins['externally_pinned_receipt_sha256'],
            externally_pinned_source_note_sha256=
                case.pins['externally_pinned_source_note_sha256'],
            externally_pinned_prequarantine_sha256=
                case.pins['externally_pinned_prequarantine_sha256'],
            native_store=self.store, scope_id='v233_synthetic_source_scope',
            run_id='v233_synthetic_unapproved',
            externally_pinned_inventory_sha256=case.origin['inventory_sha256'],
            prior_knowledge=knowledge, explicit_private_host_stage=True,
        )
        self.snapshot = self.store.snapshot('v233_synthetic_source_scope')
        self.assertEqual(self.snapshot['ledger_head_sha256'],
                         out['new_v6_host_event_sha256'])
        self.path = self.priv/'new_owner_v127.db'
        self.args = dict(
            origin=case.origin, native_store=self.store,
            scope_id='v233_synthetic_source_scope',
            expected_host_head_sha256=out['new_v6_host_event_sha256'],
            expected_event_count=self.snapshot['sequence'],
            second_receipt=case.receipt,
            private_source_note=case.synthetic_note,
            prequarantine=case.escrow,
            **case.pins, checkpoint_path=self.path,
            expected_checkpoint_head_sha256=ZERO_SHA,
            max_cues=20,
        )

    def test_01_real_v6_event_to_real_v127_checkpoint_no_false_approval(self):
        out = open_new_real_v1271_checkpoint(**self.args)
        self.assertTrue(out['checkpoint_created_now'])
        self.assertEqual(out['source_cues'],8)
        self.assertEqual(out['unapproved_atoms'],3)
        self.assertEqual(out['v1271_expected_children'],1)
        self.assertEqual(out['v1271_children_missing'],1)
        self.assertEqual(out['v1271_children_passed'],0)
        self.assertFalse(out['v123_chat_final_released'])
        self.assertFalse(out['v126_knowledge_published'])
        self.assertEqual(out['e5_published'],0)
        self.assertEqual(self.path.stat().st_mode & 0o777,0o600)

    def test_02_restart_reuses_pinned_plan_without_new_approval(self):
        first = open_new_real_v1271_checkpoint(**self.args)
        second = open_new_real_v1271_checkpoint(**self.args)
        self.assertFalse(second['checkpoint_created_now'])
        self.assertEqual(first['parent_plan_sha256'],second['parent_plan_sha256'])
        self.assertEqual(second['v1271_checkpoint_head_sha256'],ZERO_SHA)
        self.assertEqual(second['v1271_children_missing'],1)
        self.assertFalse(second['v128_parent_assembly_allowed'])

    def test_03_wrong_host_head_rejected_before_creating_checkpoint(self):
        args = dict(self.args,expected_host_head_sha256='f'*64)
        with self.assertRaisesRegex(InvalidInput,
                                    'EXTERNAL_HOST_HEAD_OR_SEQUENCE_CHANGED'):
            open_new_real_v1271_checkpoint(**args)
        self.assertFalse(self.path.exists())

    def test_04_wrong_host_count_rejected_before_checkpoint(self):
        with self.assertRaisesRegex(InvalidInput,
                                    'EXTERNAL_HOST_HEAD_OR_SEQUENCE_CHANGED'):
            open_new_real_v1271_checkpoint(**dict(self.args,
                expected_event_count=self.snapshot['sequence']+1))
        self.assertFalse(self.path.exists())

    def test_05_fake_E3_receipt_must_not_open_checkpoint(self):
        wrong = copy.deepcopy(self.case.receipt)
        wrong['e3_formal_approved']=True
        with self.assertRaisesRegex(InvalidInput, 'SECOND_RECEIPT_BYTE_PIN'):
            open_new_real_v1271_checkpoint(**dict(self.args,
                second_receipt=wrong))
        self.assertFalse(self.path.exists())

    def test_06_unapproved_checkpoint_cannot_release_parent(self):
        out = open_new_real_v1271_checkpoint(**self.args)
        with self.assertRaisesRegex(QualityNotProven,
                                    'ACTUAL_E2_E3_VERDICTS'):
            require_actual_e1_full_release_ready(checkpoint_receipt=out)

    def test_07_wrong_checkpoint_head_on_restart_rejected(self):
        open_new_real_v1271_checkpoint(**self.args)
        with self.assertRaisesRegex(QualityNotProven,
                                    'EXTERNAL_CHECKPOINT_HEAD_DRIFT'):
            open_new_real_v1271_checkpoint(**dict(self.args,
                expected_checkpoint_head_sha256='f'*64))

    def test_08_insecure_existing_checkpoint_rejected(self):
        self.path.write_bytes(b'insecure-placeholder')
        os.chmod(self.path,0o644)
        with self.assertRaisesRegex(InvalidInput,
                                    'PRIVATE_CHECKPOINT_FILE_MODE'):
            open_new_real_v1271_checkpoint(**self.args)

    def test_09_new_checkpoint_nonzero_head_rejected_before_creation(self):
        with self.assertRaisesRegex(InvalidInput,
                                    'NEW_CHECKPOINT_REQUIRES_ZERO_HEAD'):
            open_new_real_v1271_checkpoint(**dict(self.args,
                expected_checkpoint_head_sha256='f'*64))
        self.assertFalse(self.path.exists())

    def test_10_sqlite_event_row_tamper_detected_on_replay(self):
        with sqlite3.connect(self.store.path) as con:
            con.execute('UPDATE events SET event_json=? WHERE sequence=2',
                        ('{"changed":"synthetic"}',))
        with self.assertRaises(LedgerCorrupted):
            open_new_real_v1271_checkpoint(**self.args)
        self.assertFalse(self.path.exists())

    def test_11_wrong_v6_owner_pin_not_a_valid_parent(self):
        changed = copy.deepcopy(self.args['origin'])
        changed['inventory_sha256']='a'*64
        with self.assertRaisesRegex(InvalidInput,
                                    'V6_HOST_OWNER_INVENTORY_NOT_PINNED'):
            open_new_real_v1271_checkpoint(**dict(self.args,origin=changed))
        self.assertFalse(self.path.exists())


if __name__=='__main__':
    unittest.main()