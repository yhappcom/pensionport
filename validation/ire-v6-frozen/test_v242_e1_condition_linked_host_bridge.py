"""V242 synthetic adversarial tests. Genuine ETF proof runs OFFLINE only.

Only the V231 separate-turn authenticity check is stubbed for synthetic cues;
source, atom exchange, prior 145 raw bytes and V6 SQLite host are REAL code.
"""
from __future__ import annotations

from copy import deepcopy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ire.v6 import TransactionStore
from ire.v6.codec import json_digest
from ire.v6.errors import InvalidInput, QualityNotProven
from v242_e1_condition_linked_host_bridge import (
    build_condition_linked_provisional_case, stage_verified_condition_linked_host)
from v241_e1_unapproved_child_host_writer import build_unapproved_child_host_case
import test_v241_e1_unapproved_child_host_writer as fx


class TestV242ParentQualifierProvisionalChild(unittest.TestCase):
    def setUp(self):
        f=fx.TestV241UnapprovedRealNativeWriter(
            'test_01_two_scopes_can_preflight_local_atoms_without_approval')
        f.setUp(); self.addCleanup(f.doCleanups)
        self.f=f
        origin=deepcopy(f.origin)
        atom=next(a for a in origin['exchange']['atoms'] if a['claim_id']=='C00003')
        # Synthetic B0002: local cue 5 + source quote cue 6; external cue 4
        # is an indispensable source condition. The parent atom is unchanged.
        atom['context_cue_indices']=[4,5,6]
        atom['condition_cue_indices']=[4,5]
        from ire.v6.codec import json_digest
        origin['native_exchange_digest']=json_digest(origin['exchange'])
        f._setup_origin(origin)
        self.kw=dict(f.kw,child_id='B0002',claim_id='C00003')
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def prepare(self,kw=None):
        with patch('v242_e1_condition_linked_host_bridge.verify_real_turn2_private_custody',
                   return_value={'status':'SYNTHETIC_STUB_NOT_HOST_SIGNATURE'}):
            return build_condition_linked_provisional_case(**(kw or self.kw))

    def stage(self,kw=None,**extra):
        kw=kw or self.kw
        p=self.prepare(kw)
        path=self.root/'child.db'
        store=TransactionStore(path)
        with patch('v242_e1_condition_linked_host_bridge.verify_real_turn2_private_custody',
                   return_value={'status':'SYNTHETIC_STUB_NOT_HOST_SIGNATURE'}):
            return stage_verified_condition_linked_host(
                **kw,native_store=store,
                scope_id='v242_fixture_only_B0002',
                run_id='v242_fixture_staging_only',
                externally_operator_pinned_inventory_sha256=p['case']['operator_inventory_digest_sha256'],
                externally_pinned_provenance_sha256=json_digest(p['provenance']),
                **extra),store

    def test_01_root_cause_old_v241_rejects_empty_scope(self):
        with patch('v241_e1_unapproved_child_host_writer.verify_real_turn2_private_custody',
                   return_value={'status':'SYNTHETIC_STUB'}):
            with self.assertRaisesRegex(QualityNotProven,'EMPTY_CHILD_LOCAL_ATOMS'):
                build_unapproved_child_host_case(child_id='B0002',**self.f.kw)

    def test_02_local_projection_and_parent_condition_exactly_reconstruct(self):
        p=self.prepare();local=p['case']['exchange']['atoms'][0];link=p['provenance']
        self.assertEqual(local['context_cue_indices'],[5,6])
        self.assertEqual(local['condition_cue_indices'],[5])
        self.assertEqual([x['cue_index'] for x in link['original_external_condition_cues']],[4])
        self.assertTrue(link['reconstructs_full_original_atom'])
        self.assertTrue(link['requires_e3_parent_condition_review'])
        self.assertFalse(link['e3_final_approved'])
        self.assertFalse(link['child_local_semantics_certified'])
        self.assertFalse(link['parent_qualifier_semantics_certified'])

    def test_03_original_v6_sqlite_staging_reopens_without_any_approval(self):
        out,store=self.stage(explicit_provisional_host_stage=True)
        self.assertEqual(out['status'],'STRUCTURAL_PROVISIONAL_CHILD_HOST_COMMITTED')
        self.assertEqual(out['external_condition_cues_preserved'],1)
        self.assertEqual(out['e5_published'],0)
        snap=TransactionStore(store.path).snapshot('v242_fixture_only_B0002')
        self.assertEqual(snap['ledger_head_sha256'],out['host_event_sha256'])
        self.assertFalse(snap['progress']['research_report_closed'])
        self.assertEqual(snap['progress']['verified_proofs'],0)

    def test_04_explicit_permission_required_before_any_scope_write(self):
        with self.assertRaisesRegex(InvalidInput,'EXPLICIT_PROVISIONAL'):
            self.stage()
        store=TransactionStore(self.root/'child.db')
        with self.assertRaisesRegex(InvalidInput,'SCOPE_UNKNOWN'):
            store.snapshot('v242_fixture_only_B0002')

    def test_05_external_qualifier_pin_mismatch_fails_before_scope(self):
        p=self.prepare();bad='0'*64
        if bad==json_digest(p['provenance']):bad='f'*64
        with patch('v242_e1_condition_linked_host_bridge.verify_real_turn2_private_custody',
                   return_value={}):
            with self.assertRaisesRegex(InvalidInput,'PARENT_QUALIFIER_ESCROW_PIN_MISMATCH'):
                stage_verified_condition_linked_host(**self.kw,
                    native_store=TransactionStore(self.root/'child.db'),
                    scope_id='v242_fixture_only_B0002',run_id='v242_fixture_staging_only',
                    externally_operator_pinned_inventory_sha256=p['case']['operator_inventory_digest_sha256'],
                    externally_pinned_provenance_sha256=bad,
                    explicit_provisional_host_stage=True)
        with self.assertRaisesRegex(InvalidInput,'SCOPE_UNKNOWN'):
            TransactionStore(self.root/'child.db').snapshot('v242_fixture_only_B0002')

    def test_06_parent_condition_cue_no_longer_qualifier_fails(self):
        altered=deepcopy(self.kw)
        atom=next(a for a in altered['origin']['exchange']['atoms'] if a['claim_id']=='C00003')
        atom['condition_cue_indices']=[5]
        altered['origin']['native_exchange_digest']=json_digest(altered['origin']['exchange'])
        altered['externally_pinned_exchange_digest']=altered['origin']['native_exchange_digest']
        # Repack all derived child evidence (so SHA pin update cannot disguise a missing qualifier)
        self.f._setup_origin(altered['origin'])
        altered=dict(self.f.kw,child_id='B0002',claim_id='C00003')
        with self.assertRaisesRegex(InvalidInput,'CROSS_PRIMARY_NUMERIC_EXCEPTION_OR_NONQUALIFIER_BLOCKED'):
            self.prepare(altered)

    def test_07_false_final_v123_approval_rejected(self):
        altered=deepcopy(self.kw)
        altered['review_tasks']['child_tasks'][1]['atom_review_tasks'][0]['formal_v123_verdict']='APPROVED'
        altered['externally_pinned_review_tasks_sha256']=json_digest(altered['review_tasks'])
        with self.assertRaisesRegex(InvalidInput,'REVIEW_TASK_SOURCE_CONTENT_OR_ROLE_MUTATION'):
            self.prepare(altered)

    def test_08_source_quote_changed_even_with_new_pin_rejected(self):
        altered=deepcopy(self.kw)
        altered['review_tasks']['child_tasks'][1]['atom_review_tasks'][0]['source_context_references'][0]['quote']='FAKE QUOTE'
        altered['externally_pinned_review_tasks_sha256']=json_digest(altered['review_tasks'])
        with self.assertRaisesRegex(InvalidInput,'REVIEW_TASK_SOURCE_CONTENT_OR_ROLE_MUTATION'):
            self.prepare(altered)

    def test_09_parent_original_source_changed_rejected(self):
        altered=deepcopy(self.kw)
        altered['origin']['source_raw']+=b'NEWLY_MUTATED_SOURCE_BYTES'
        with self.assertRaisesRegex(InvalidInput,'EXTERNAL_SOURCE_EXCHANGE_OR_PARENT_PIN_DRIFT'):
            self.prepare(altered)

    def test_10_provisional_projection_without_local_condition_rejected(self):
        altered=deepcopy(self.kw)
        atom=next(a for a in altered['origin']['exchange']['atoms'] if a['claim_id']=='C00003')
        atom['condition_cue_indices']=[4]
        altered['origin']['native_exchange_digest']=json_digest(altered['origin']['exchange'])
        self.f._setup_origin(altered['origin'])
        altered=dict(self.f.kw,child_id='B0002',claim_id='C00003')
        with self.assertRaisesRegex(InvalidInput,'CROSS_PRIMARY_NUMERIC_EXCEPTION_OR_NONQUALIFIER_BLOCKED'):
            self.prepare(altered)


if __name__ == '__main__':
    unittest.main()