"""V235 source-native E1 gateway test: authenticated structure, no fake approvals."""
from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from ire.v6.codec import ZERO_SHA,json_digest
from ire.v6.errors import InvalidInput
from v126_chat_approved_knowledge_store import PrivateKnowledgeStore
from v1271_parent_resume_checkpoint import PrivateFullVideoCheckpoint
from v233_e1_v228_actual_parent_checkpoint_preflight import open_new_real_v1271_checkpoint
from v234_e1_cross_child_context_custody import build_lossless_context_escrow
from v235_e1_real_parent_release_gateway import run_verified_source_native_parent_gateway
import test_v233_e1_v228_actual_parent_checkpoint_preflight as v233_fixture


class TestV235VerifiedE1Gateway(unittest.TestCase):
    def setUp(self):
        fx=v233_fixture.TestV233NativeV127Handoff(
            'test_01_real_v6_event_to_real_v127_checkpoint_no_false_approval')
        fx.setUp()
        self.addCleanup(fx.doCleanups)
        self.fx=fx
        open_new_real_v1271_checkpoint(**fx.args)
        self.ck=PrivateFullVideoCheckpoint(
            fx.path,raw=fx.case.origin['source_raw'],
            parent_manifest=fx.case.origin['manifest'],
            parent_inventory=fx.case.origin['inventory_bytes'],
            expected_parent_inventory_sha256=fx.case.origin['inventory_sha256'],
            max_cues=20)
        self.knowledge=PrivateKnowledgeStore(fx.priv/'knowledge.db')
        self.escrow=build_lossless_context_escrow(
            origin=fx.case.origin,checkpoint=self.ck,
            externally_pinned_parent_plan_sha256=self.ck.plan_pin,
            externally_pinned_checkpoint_head_sha256=ZERO_SHA,
            externally_pinned_source_sha256=fx.case.origin['source_sha256'],
            externally_pinned_exchange_digest=fx.case.origin['native_exchange_digest'])
        self.args={
            'origin':fx.case.origin,'native_store':fx.store,
            'scope_id':fx.args['scope_id'],
            'expected_host_head_sha256':fx.args['expected_host_head_sha256'],
            'expected_event_count':fx.args['expected_event_count'],
            'second_receipt':fx.case.receipt,
            'private_source_note':fx.case.synthetic_note,
            'prequarantine':fx.case.escrow,
            **fx.case.pins,
            'checkpoint':self.ck,
            'externally_pinned_parent_plan_sha256':self.ck.plan_pin,
            'externally_pinned_checkpoint_head_sha256':ZERO_SHA,
            'externally_pinned_source_sha256':fx.case.origin['source_sha256'],
            'externally_pinned_exchange_digest':fx.case.origin['native_exchange_digest'],
            'cross_context_escrow':self.escrow,
            'externally_pinned_escrow_sha256':json_digest(self.escrow),
            'knowledge_store':self.knowledge,
            'expected_knowledge_head_sha256':ZERO_SHA,
        }

    def test_01_synthetic_valid_source_missing_chat_reviews_stays_hold(self):
        out=run_verified_source_native_parent_gateway(**self.args)
        self.assertEqual(out['status'],
            'HOLD_REAL_CHATGPT_CHILD_SEAM_AND_PARENT_REVIEW_NOT_SUPPLIED')
        self.assertEqual(out['cross_segment_atoms_pending'],0)
        self.assertEqual(out['e5_published'],0)
        self.assertEqual(out['knowledge_before'],out['knowledge_after'])
        self.assertEqual(self.knowledge.audit()['active_claims'],0)

    def test_02_synthetic_valid_source_does_reach_actual_v128_child_boundary(self):
        # Callback is intentionally bad: V166/V123 refuses forged approval.
        called=[]
        def child(segment_id,manifest,stage,original_raw):
            called.append(segment_id)
            return {'fake':'approval'}
        with self.assertRaisesRegex(InvalidInput,
                                    'V166_E3_DECISION_CHILD_CALLBACK_REQUIRED'):
            run_verified_source_native_parent_gateway(**dict(
                self.args,review_or_load_child=child,
                review_seams=lambda *a: [],review_parent=lambda *a: {}))
        self.assertEqual(called,['B0001'])
        self.assertEqual(self.knowledge.audit()['active_claims'],0)
        self.assertEqual(self.ck.progress()['checkpoint_head_sha256'],ZERO_SHA)

    def test_03_tampered_host_head_rejected_before_child_or_knowledge(self):
        with self.assertRaisesRegex(InvalidInput,
                                    'EXTERNAL_HOST_HEAD_OR_SEQUENCE_CHANGED'):
            run_verified_source_native_parent_gateway(**dict(
                self.args,expected_host_head_sha256='a'*64))
        self.assertEqual(self.knowledge.audit()['active_claims'],0)

    def test_04_changed_cross_context_receipt_with_repin_is_rejected(self):
        wrong=copy.deepcopy(self.escrow)
        wrong['source_cue_count']+=1
        with self.assertRaisesRegex(InvalidInput,
                                    'CROSS_SCOPE_CUE_OR_ATOM_CONTEXT_SUBSTITUTED'):
            run_verified_source_native_parent_gateway(**dict(
                self.args,cross_context_escrow=wrong,
                externally_pinned_escrow_sha256=json_digest(wrong)))
        self.assertEqual(self.knowledge.audit()['active_claims'],0)

    def test_05_no_foreign_knowledge_head_before_review(self):
        with self.assertRaisesRegex(Exception, 'EXTERNAL_HEAD_CHECKPOINT_DRIFT'):
            run_verified_source_native_parent_gateway(**dict(
                self.args,expected_knowledge_head_sha256='f'*64))
        self.assertEqual(self.knowledge.audit()['active_claims'],0)

    def test_06_missing_verified_turn2_source_pin_fails(self):
        altered=copy.deepcopy(self.fx.case.receipt)
        altered['turn2_manual_message_ref']='user:UNATTESTED-FORGED'
        with self.assertRaisesRegex(InvalidInput,'SECOND_RECEIPT_BYTE_PIN'):
            run_verified_source_native_parent_gateway(**dict(
                self.args,second_receipt=altered))
        self.assertEqual(self.knowledge.audit()['active_claims'],0)


if __name__=='__main__':
    unittest.main()