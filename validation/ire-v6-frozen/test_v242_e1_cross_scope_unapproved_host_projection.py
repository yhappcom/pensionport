"""V242 *synthetic* V6 native host regression; genuine ETF is offline only."""
from __future__ import annotations

import copy
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ire.v6 import TransactionStore
from ire.v6.codec import json_digest
from ire.v6.errors import InvalidInput, LedgerCorrupted
from v242_e1_cross_scope_unapproved_host_projection import (
    build_pending_cross_child_host_case,stage_pending_cross_child_host_only,
)
import test_v241_e1_unapproved_child_host_writer as fixture


class TestV242LocalAnchorWithInheritedCondition(unittest.TestCase):
    def setUp(self):
        self.fx=fixture.TestV241UnapprovedRealNativeWriter(
            'test_01_two_scopes_can_preflight_local_atoms_without_approval')
        self.fx.setUp();self.addCleanup(self.fx.doCleanups)
        origin=copy.deepcopy(self.fx.origin)
        atom=next(x for x in origin['exchange']['atoms'] if x['claim_id']=='C00003')
        atom['context_cue_indices']=[4,5,6]
        atom['condition_cue_indices']=[4]
        from ire.v6.codec import json_digest
        origin['native_exchange_digest']=json_digest(origin['exchange'])
        self.fx._setup_origin(origin)
        self.kw=copy.deepcopy(self.fx.kw)
        self.kw['child_id']='B0002'
        self.folder=Path(tempfile.mkdtemp(prefix='v242-e1-'))
        self.addCleanup(lambda: __import__('shutil').rmtree(self.folder))
        # private store parent; permissions guaranteed before V6 init
        self.folder.chmod(0o700)

    def build(self, args=None):
        with patch('v242_e1_cross_scope_unapproved_host_projection.verify_real_turn2_private_custody',
                   return_value={'status':'SYNTHETIC_TURN2_STUB_NOT_REAL'}):
            return build_pending_cross_child_host_case(**(self.kw if args is None else args))

    def stage(self,case,*,store=None,pin=None,params=None,allowed=True):
        if store is None:store=TransactionStore(self.folder/'test.db')
        with patch('v242_e1_cross_scope_unapproved_host_projection.verify_real_turn2_private_custody',
                   return_value={'status':'SYNTHETIC_TURN2_STUB_NOT_REAL'}):
            return stage_pending_cross_child_host_only(
                case=case, original_build_kwargs=self.kw if params is None else params,
                native_store=store, run_id='v242_test_cross_pending',
                externally_pinned_parent_binding_sha256=(
                    case['v242_pending_parent_binding_sha256'] if pin is None else pin),
                explicit_unapproved_host_stage=allowed)

    def test_01_empty_local_child_recovered_without_parent_atom_change(self):
        c=self.build()
        self.assertEqual(c['segment_id'],'B0002')
        self.assertEqual(c['original_local_atoms_staged'],0)
        self.assertEqual(c['original_cross_atoms_awaiting_meaning'],1)
        original=next(a for a in self.kw['origin']['exchange']['atoms']
                      if a['claim_id']=='C00003')
        self.assertEqual(c['v242_pending_parent_binding']['parent_atom'], original)
        self.assertEqual(c['v242_pending_parent_binding']['dropped_only_in_native_local_view'],[4])
        self.assertEqual(c['exchange']['atoms'][0]['context_cue_indices'],[5,6])
        self.assertFalse(c['e3_formal_approved'])

    def test_02_actual_synthetic_native_sqlite_commit_and_idempotent_replay(self):
        c=self.build()
        one=self.stage(c)
        two=self.stage(c)
        self.assertEqual(one['native_host_receipt_event_sha256'],two['native_host_receipt_event_sha256'])
        self.assertEqual(one['native_host_event_count'],6)
        self.assertFalse(one['parent_external_semantics_resolved'])
        snap=TransactionStore(self.folder/'test.db').snapshot(one['scope_id'])
        self.assertEqual(snap['sequence'],6)
        self.assertEqual(snap['progress']['verified_proofs'],0)
        self.assertFalse(snap['progress']['financial_facts_approved'])
        with sqlite3.connect(self.folder/'test.db') as db:
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            self.assertNotIn('knowledge',{r[0] for r in db.execute('SELECT name FROM sqlite_master')})

    def test_03_parent_condition_quote_mutation_fails_closed(self):
        bad=copy.deepcopy(self.kw)
        cross=bad['cross_context_escrow']['cross_segment_atom_rows'][0]
        cross['cross_segment_cues'][0]['cue_text']='INVENTED'
        bad['externally_pinned_escrow_sha256']=json_digest(bad['cross_context_escrow'])
        with self.assertRaisesRegex(InvalidInput,'CROSS_SCOPE_CUE_OR_ATOM_CONTEXT_SUBSTITUTED'):
            self.build(bad)

    def test_04_lost_parent_condition_becomes_invalid_not_false_no_atom(self):
        bad=copy.deepcopy(self.kw)
        a=next(a for a in bad['origin']['exchange']['atoms'] if a['claim_id']=='C00003')
        a['context_cue_indices']=[5,6]
        a['condition_cue_indices']=[]
        with self.assertRaises(InvalidInput):self.build(bad)

    def test_05_fake_final_approval_rejected_before_host_write(self):
        c=self.build()
        c['e3_formal_approved']=True
        store=TransactionStore(self.folder/'reject.db')
        with self.assertRaisesRegex(InvalidInput,'CASE_CHANGED_SINCE_SOURCE_FIRST_REVIEW'):
            self.stage(c,store=store)
        with self.assertRaisesRegex(InvalidInput,'SCOPE_UNKNOWN'):
            store.snapshot('v242_'+c['v242_pending_parent_binding_sha256'])

    def test_06_external_parent_pin_changed_before_any_scope(self):
        c=self.build();s=TransactionStore(self.folder/'reject.db')
        with self.assertRaisesRegex(InvalidInput,'OUTSIDE_PARENT_CONDITION_PIN_MISMATCH'):
            self.stage(c,store=s,pin='f'*64)
        with self.assertRaisesRegex(InvalidInput,'SCOPE_UNKNOWN'):
            s.snapshot('v242_'+c['v242_pending_parent_binding_sha256'])

    def test_07_no_explicit_staging_permission_no_event(self):
        c=self.build();s=TransactionStore(self.folder/'reject.db')
        with self.assertRaisesRegex(InvalidInput,'EXPLICIT_NATIVE_UNAPPROVED_STAGING_REQUIRED'):
            self.stage(c,store=s,allowed=False)
        with self.assertRaisesRegex(InvalidInput,'SCOPE_UNKNOWN'):
            s.snapshot('v242_'+c['v242_pending_parent_binding_sha256'])

    def test_08_turn2_cue_quote_mutation_rejected(self):
        bad=copy.deepcopy(self.kw)
        bad['second_receipt']['turn2_review']['source_only_review_rows'][4]['quote']='ALTERED'
        with self.assertRaisesRegex(InvalidInput,'CHILD_SOURCE_FIRST_REVIEW_DRIFT'):
            self.build(bad)

    def test_09_native_event_tamper_detected(self):
        c=self.build();r=self.stage(c)
        db=self.folder/'test.db'
        with sqlite3.connect(db) as con:
            con.execute('UPDATE events SET event_json=? WHERE sequence=4',('fake data',))
            con.commit()
        with self.assertRaises(LedgerCorrupted):
            TransactionStore(db).snapshot(r['scope_id'])

    def test_10_native_projection_never_eligible_for_formal_v123_e4(self):
        c=self.build();r=self.stage(c)
        self.assertTrue(c['v242_forbidden_as_v123_formal_child_atom'])
        self.assertFalse(c['v242_parent_semantic_qualifier_discharged'])
        self.assertFalse(r['e3_formal_child_approved'])
        self.assertFalse(r['e4_authorized'])
        self.assertEqual(r['e5_published'],0)


if __name__=='__main__':unittest.main()