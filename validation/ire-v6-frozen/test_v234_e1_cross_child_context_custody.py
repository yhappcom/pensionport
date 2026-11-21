"""V234 regression: synthetic 2-child cross-scope atom with no approval."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from ire.v6.codec import ZERO_SHA, canonical, json_digest, sha256
from ire.v6.errors import InvalidInput, QualityNotProven
from ire.v6.atomic_exchange import audit_host_atomic_exchange
from v176_chat_engine_loop import make_original_plan
from v1271_parent_resume_checkpoint import PrivateFullVideoCheckpoint
from v230_e1_v228_source_native_handoff import SCHEMA as V230_SCHEMA
from test_v227_e2_source_semantic_reconciliation import synthetic
from v234_e1_cross_child_context_custody import (
    build_lossless_context_escrow, verify_escrow_bytes,
    require_complete_real_child_release)


class TestV234CrossChildCustody(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.private = self.root / 'private'
        self.private.mkdir(mode=0o700)
        docs,*_ = synthetic()
        self.source,self.manifest = make_original_plan(
            docs['srt'],'SYNTHET0001',
            expected_source_sha256=sha256(docs['srt']),window_size=4)
        exchange = json.loads(docs['native'])
        exchange['manifest_sha256'] = self.source.manifest_sha256
        for atom in exchange['atoms']:
            atom['owner_window_id'] = self.source.owner(
                atom['source_refs'][0]['cue_index'])
        audit_host_atomic_exchange(self.source,exchange)
        inv = {'schema':'IRE_V6_OWNER_INVENTORY_V1','entries':[{
            'video_id': self.source.video_id,
            'source_sha256': self.source.source_sha256,
            'manifest_sha256': self.source.manifest_sha256,
            'cue_census_sha256': self.source.cue_census_sha256,
        }]}
        inv_bytes=canonical(inv)
        self.origin={
            'schema':V230_SCHEMA,'source':self.source,
            'source_raw':docs['srt'],'manifest':self.manifest,
            'exchange':exchange,'inventory_bytes':inv_bytes,
            'inventory_sha256':sha256(inv_bytes),
            'source_sha256':self.source.source_sha256,
            'native_exchange_digest':json_digest(exchange),
            'unapproved_atoms':3,
        }
        self.ck = PrivateFullVideoCheckpoint(
            self.private/'test.db',raw=docs['srt'],
            parent_manifest=self.manifest,parent_inventory=inv_bytes,
            expected_parent_inventory_sha256=sha256(inv_bytes),max_cues=4)
        self.assertEqual(len(self.ck.child_ids),2)

    def args(self):
        return dict(origin=self.origin,checkpoint=self.ck,
                    externally_pinned_parent_plan_sha256=self.ck.plan_pin,
                    externally_pinned_checkpoint_head_sha256=ZERO_SHA,
                    externally_pinned_source_sha256=self.origin['source_sha256'],
                    externally_pinned_exchange_digest=self.origin['native_exchange_digest'])

    def test_01_two_scopes_three_local_atoms_no_cross(self):
        receipt=build_lossless_context_escrow(**self.args())
        self.assertEqual(receipt['full_atom_count'],3)
        self.assertEqual(receipt['cross_segment_atom_count'],0)
        self.assertEqual(len(receipt['all_local_atom_ids']),3)
        self.assertFalse(receipt['v123_final_approval'])

    def _with_cross(self):
        origin=copy.deepcopy(self.origin)
        a=origin['exchange']['atoms'][0]
        a['context_cue_indices']=[1,2,5]
        a['condition_cue_indices']=[5]
        origin['native_exchange_digest']=json_digest(origin['exchange'])
        audit_host_atomic_exchange(origin['source'],origin['exchange'])
        return dict(self.args(),origin=origin,
                    externally_pinned_exchange_digest=origin['native_exchange_digest'])

    def test_02_cross_child_context_and_qualifier_preserved(self):
        args=self._with_cross()
        x=build_lossless_context_escrow(**args)
        self.assertEqual(x['cross_segment_atom_count'],1)
        self.assertEqual(x['cross_segment_qualifier_atom_count'],1)
        self.assertEqual(x['full_atom_count'],3)
        row=x['cross_segment_atom_rows'][0]
        self.assertEqual(row['claim_id'],'C00001')
        self.assertEqual(row['referenced_segment_ids'],['B0001','B0002'])
        self.assertEqual(row['cross_segment_cues'][-1]['cue_index'],5)
        self.assertIn('CONDITION',row['cross_segment_cues'][-1]['reference_roles'])
        self.assertFalse(row['meaning_approved'])

    def test_03_replay_private_source_content_and_sha(self):
        args=self._with_cross()
        x=build_lossless_context_escrow(**args)
        got=verify_escrow_bytes(**args,escrow=x,
                                externally_pinned_escrow_sha256=json_digest(x))
        self.assertEqual(got['cross_segment_atom_count'],1)
        self.assertFalse(got['e3_final_approved'])

    def test_04_quoted_cross_source_tamper_even_with_repin_is_blocked(self):
        args=self._with_cross()
        x=build_lossless_context_escrow(**args)
        x['cross_segment_atom_rows'][0]['cross_segment_cues'][-1]['cue_text']='SYNTHETIC FALSE CONTEXT'
        with self.assertRaisesRegex(InvalidInput,
                                    'CROSS_SCOPE_CUE_OR_ATOM_CONTEXT_SUBSTITUTED'):
            verify_escrow_bytes(**args,escrow=x,
                                externally_pinned_escrow_sha256=json_digest(x))

    def test_05_equal_atom_count_with_proposition_substitution_is_blocked(self):
        args=self._with_cross()
        x=build_lossless_context_escrow(**args)
        altered=copy.deepcopy(args['origin'])
        altered['exchange']['atoms'][0]['proposition']+=' 바꾼 의미'
        with self.assertRaisesRegex(InvalidInput,
                                    'EXTERNAL_SOURCE_EXCHANGE_OR_PARENT_PIN_DRIFT'):
            verify_escrow_bytes(**dict(args,origin=altered),escrow=x,
                                externally_pinned_escrow_sha256=json_digest(x))

    def test_06_wrong_external_parent_plan_pin_is_blocked(self):
        args=self._with_cross()
        with self.assertRaisesRegex(InvalidInput,
                                    'EXTERNAL_SOURCE_EXCHANGE_OR_PARENT_PIN_DRIFT'):
            build_lossless_context_escrow(**dict(args,
                externally_pinned_parent_plan_sha256='f'*64))

    def test_07_wrong_external_checkpoint_head_is_blocked(self):
        args=self._with_cross()
        with self.assertRaisesRegex(QualityNotProven,
                                    'EXTERNAL_CHECKPOINT_HEAD_DRIFT'):
            build_lossless_context_escrow(**dict(args,
                externally_pinned_checkpoint_head_sha256='f'*64))

    def test_08_raw_origin_source_change_is_blocked(self):
        args=self._with_cross()
        changed=copy.deepcopy(args['origin'])
        changed['source_raw']+=b'ALTERED'
        with self.assertRaisesRegex(InvalidInput,
                                    'EXTERNAL_SOURCE_EXCHANGE_OR_PARENT_PIN_DRIFT'):
            build_lossless_context_escrow(**dict(args,origin=changed))

    def test_09_unapproved_cross_child_cannot_release(self):
        args=self._with_cross()
        x=build_lossless_context_escrow(**args)
        with self.assertRaisesRegex(QualityNotProven,
                                    'OPEN_CROSS_SCOPE_ATOMS_OR_UNVERIFIED'):
            require_complete_real_child_release(
                escrow=x,checkpoint=self.ck,
                externally_pinned_checkpoint_head_sha256=ZERO_SHA)

    def test_10_no_cross_also_cannot_fake_2turn_or_v123(self):
        x=build_lossless_context_escrow(**self.args())
        with self.assertRaisesRegex(QualityNotProven,
                                    'OPEN_CROSS_SCOPE_ATOMS_OR_UNVERIFIED'):
            require_complete_real_child_release(
                escrow=x,checkpoint=self.ck,
                externally_pinned_checkpoint_head_sha256=ZERO_SHA)

    def test_11_removed_cross_ref_with_unreconciled_digest_detected(self):
        args=self._with_cross()
        x=build_lossless_context_escrow(**args)
        x['cross_segment_atom_rows']=[]
        with self.assertRaisesRegex(InvalidInput,
                                    'CROSS_SCOPE_CUE_OR_ATOM_CONTEXT_SUBSTITUTED'):
            verify_escrow_bytes(**args,escrow=x,
                                externally_pinned_escrow_sha256=json_digest(x))


if __name__=='__main__':
    unittest.main()