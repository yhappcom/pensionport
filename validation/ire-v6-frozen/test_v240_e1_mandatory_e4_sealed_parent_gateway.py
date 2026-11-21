"""V240 mandatory E4 gate dispatch and no-leak; E4 itself tested elsewhere.

Mock V239 here is an isolation STUB, never genuine host ChatGPT evidence.
"""
from __future__ import annotations
import copy,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from ire.v6.codec import ZERO_SHA,json_digest
from ire.v6.errors import InvalidInput
from v126_chat_approved_knowledge_store import PrivateKnowledgeStore
from v166_e4_sealed_knowledge import E4SealedKnowledgeStore
from v234_e1_cross_child_context_custody import build_lossless_context_escrow
from v237_e1_parent_child_review_contract import build_child_review_tasks
from v238_e1_child_native_scope_draft import build_partial_native_drafts
from v240_e1_mandatory_e4_sealed_parent_gateway import run_mandatory_e4_source_native_parent
import test_v234_e1_cross_child_context_custody as fixture

class TestV240E4Only(unittest.TestCase):
    def setUp(self):
        fx=fixture.TestV234CrossChildCustody('test_01_two_scopes_three_local_atoms_no_cross')
        fx.setUp();self.addCleanup(fx.doCleanups)
        self.fx=fx
        self.a=fx._with_cross()
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.db=Path(self.tmp.name)/'e4.db'
        self.store=E4SealedKnowledgeStore(self.db,external_signing_key=b'synthetic-test-only-not-a-real-owner-key-'+b'x'*32)
        self._assign(self.a)

    def _assign(self,a):
        self.a=a;e=build_lossless_context_escrow(**a)
        source=dict(a,cross_context_escrow=e,externally_pinned_escrow_sha256=json_digest(e))
        self.tasks=build_child_review_tasks(**source)
        drafts=build_partial_native_drafts(origin=a['origin'],checkpoint=a['checkpoint'],
            review_tasks=self.tasks,externally_pinned_review_tasks_sha256=json_digest(self.tasks),
            **{k:v for k,v in source.items() if k not in ('origin','checkpoint')})
        self.kw=dict(origin=a['origin'],checkpoint=a['checkpoint'],review_tasks=self.tasks,
            child_native_draft=drafts,pending_review_intake={},second_receipt={},
            private_source_note={},prequarantine={},cross_context_escrow=e,
            externally_pinned_review_tasks_sha256=json_digest(self.tasks),
            externally_pinned_child_draft_sha256=json_digest(drafts),
            externally_pinned_intake_sha256='a'*64,
            externally_pinned_receipt_sha256='b'*64,
            externally_pinned_source_note_sha256='c'*64,
            externally_pinned_prequarantine_sha256='d'*64,
            externally_pinned_escrow_sha256=json_digest(e),
            externally_pinned_parent_plan_sha256=a['externally_pinned_parent_plan_sha256'],
            externally_pinned_checkpoint_head_sha256=a['externally_pinned_checkpoint_head_sha256'],
            externally_pinned_source_sha256=a['externally_pinned_source_sha256'],
            externally_pinned_exchange_digest=a['externally_pinned_exchange_digest'],
            knowledge_store=self.store,expected_knowledge_head_sha256=ZERO_SHA)

    def _run(self,**overrides):
        args=dict(self.kw,**overrides)
        with patch('v240_e1_mandatory_e4_sealed_parent_gateway.verify_pending_child_review_intake',
                   return_value={'child_count':2,'atom_review_count':3,
                                 'cross_atom_review_count':1}) as auth:
            result=run_mandatory_e4_source_native_parent(**args)
            self.assertTrue(auth.called)
            return result

    def test_01_real_cross_scope_review_intake_does_not_write(self):
        x=self._run()
        self.assertEqual(x['status'],'HOLD_OPEN_CROSS_SCOPE_REATOMIZATION_BEFORE_E4')
        self.assertFalse(x['knowledge_changed'])
        self.assertEqual(x['e5_published'],0)
        self.assertEqual(self.store.audit(externally_pinned_head=ZERO_SHA)['active_claims'],0)
        self.assertFalse(Path(str(self.db)+'.e4seal.json').exists())

    def test_02_plain_private_store_cannot_substitute_for_e4(self):
        db=Path(self.tmp.name)/'legacy.db';legacy=PrivateKnowledgeStore(db)
        with self.assertRaisesRegex(InvalidInput,'E4_SEALED_STORE_REQUIRED'):
            run_mandatory_e4_source_native_parent(**dict(self.kw,knowledge_store=legacy))

    def test_03_full_fake_callbacks_still_cannot_skip_cross_scope_hold(self):
        def unexpected(*args,**kwargs):self.fail('E4 must not see pending real cross atoms')
        dummy={x:unexpected for x in ('review_or_load_child','review_seams','review_parent',
            'primary_manifest_for_child','typed_inventory_for_child','typed_manifest_for_child')}
        x=self._run(**dict(dummy,now_as_of='2026-11-21'))
        self.assertEqual(x['e5_published'],0)

    def test_04_repaired_synthetic_no_cross_missing_e4_contract_holds(self):
        self._assign(self.fx.args())
        x=self._run()
        self.assertEqual(x['status'],'HOLD_V123_FINAL_REVIEWS_AND_E4_OFFICIAL_EVIDENCE_NOT_SUPPLIED')

    def test_05_no_cross_full_official_callbacks_delegate_only_to_frozen_e4(self):
        self._assign(self.fx.args())
        def f(*_):return None
        callbacks={k:f for k in ('review_or_load_child','review_seams','review_parent',
            'primary_manifest_for_child','typed_inventory_for_child','typed_manifest_for_child')}
        with patch('v240_e1_mandatory_e4_sealed_parent_gateway.run_e4_guarded_parent',
                   return_value={'schema':'IRE_V166_E4_PARENT_APPROVAL_V1',
                                 'all_video_knowledge_published':False,'status':'E4_HOLD_UNVERIFIED_CHILD'}) as e4:
            x=self._run(**dict(callbacks,now_as_of='2026-11-21'))
            self.assertEqual(x['status'],'E4_HOLD_OFFICIAL_PRIMARY_OR_CHAT_REVIEW')
            self.assertEqual(e4.call_count,1)
            self.assertIs(e4.call_args[0][1],self.store)
        self.assertEqual(self.store.audit(externally_pinned_head=ZERO_SHA)['active_claims'],0)

    def test_06_cross_source_tamper_blocks_before_e4(self):
        args=copy.deepcopy({k:v for k,v in self.kw.items() if k!='knowledge_store'})
        args['knowledge_store']=self.store
        args['review_tasks']['child_tasks'][0]['atom_review_tasks'][0]['source_context_references'][-1]['quote']='FAKE'
        args['externally_pinned_review_tasks_sha256']=json_digest(args['review_tasks'])
        with self.assertRaisesRegex(InvalidInput,'REVIEW_TASK_SOURCE_CONTENT_OR_ROLE_MUTATION'):
            self._run(**args)

    def test_07_wrong_prior_knowledge_head_blocks(self):
        with self.assertRaisesRegex(Exception,'EXTERNAL|HEAD|DRIFT|MISMATCH'):
            self._run(expected_knowledge_head_sha256='f'*64)

if __name__=='__main__':unittest.main()