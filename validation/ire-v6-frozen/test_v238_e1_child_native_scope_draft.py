"""V238 strict partial source, complete-local claims only; parent sidecar intact."""
from __future__ import annotations
import copy,unittest
from ire.v6.codec import json_digest
from ire.v6.errors import InvalidInput
from ire.v6.atomic_exchange import audit_host_atomic_exchange
from v234_e1_cross_child_context_custody import build_lossless_context_escrow
from v237_e1_parent_child_review_contract import build_child_review_tasks
from v238_e1_child_native_scope_draft import build_partial_native_drafts,verify_partial_native_drafts
import test_v234_e1_cross_child_context_custody as v234_fixture

class TestV238NativeChildDraft(unittest.TestCase):
    def setUp(self):
        fx=v234_fixture.TestV234CrossChildCustody('test_01_two_scopes_three_local_atoms_no_cross')
        fx.setUp();self.fx=fx;self.addCleanup(fx.doCleanups)
        self.args=fx._with_cross()
        escrow=build_lossless_context_escrow(**self.args)
        self.args.update(cross_context_escrow=escrow,
                         externally_pinned_escrow_sha256=json_digest(escrow))
        self.tasks=build_child_review_tasks(**self.args)
        self.kw=dict(origin=self.args['origin'],checkpoint=self.args['checkpoint'],
                     review_tasks=self.tasks,
                     externally_pinned_review_tasks_sha256=json_digest(self.tasks),
                     **{k:v for k,v in self.args.items() if k not in ('origin','checkpoint')})

    def draft(self): return build_partial_native_drafts(**self.kw)

    def test_01_all_cues_and_parent_atoms_retained_without_fake_approval(self):
        d=self.draft()
        self.assertEqual(d['local_complete_parent_atom_count'],2)
        self.assertEqual(d['cross_parent_atom_count'],1)
        self.assertEqual(d['child_count'],2)
        self.assertEqual(d['actual_child_host_receipts'],0)
        self.assertFalse(d['e4_authorized'])
        self.assertTrue(all(x['real_child_v6_host_committed'] is False for x in d['child_drafts']))
        self.assertEqual(sum(len(x['native_draft_exchange']['cue_dispositions']) for x in d['child_drafts']),8)

    def test_02_original_cross_atom_not_silently_accepted_as_child(self):
        d=self.draft();a=d['child_drafts'][0]
        self.assertEqual(a['cross_atom_ids_kept_in_parent_sidecar'],['C00001'])
        self.assertNotIn('C00001',[x['claim_id'] for x in a['native_draft_exchange']['atoms']])
        self.assertEqual(a['original_parent_cue_became_unresolved'],[1])
        self.assertEqual(a['native_draft_exchange']['cue_dispositions'][0]['disposition'],'UNRESOLVED')

    def test_03_local_child_atom_replays_under_partial_source(self):
        d=self.draft();self.assertEqual(d['child_drafts'][1]['native_child_draft_audit']['proposed_atomic_claims'],1)

    def test_04_all_child_drafts_rebuilt_exactly(self):
        d=self.draft()
        a=verify_partial_native_drafts(draft=d,externally_pinned_draft_sha256=json_digest(d),**self.kw)
        self.assertEqual(a['cross_atoms_waiting_for_semantics'],1)

    def test_05_child_proposition_rewrite_fails_even_with_new_digest(self):
        d=self.draft()
        d['child_drafts'][0]['native_draft_exchange']['atoms'][0]['proposition']='FAKE'
        with self.assertRaisesRegex(InvalidInput,'CHILD_DRAFT_SOURCE_OR_QUARANTINE_MUTATED'):
            verify_partial_native_drafts(draft=d,externally_pinned_draft_sha256=json_digest(d),**self.kw)

    def test_06_child_open_source_disposition_rewrite_rejected(self):
        d=self.draft();d['child_drafts'][0]['original_parent_cue_became_unresolved']=[]
        with self.assertRaisesRegex(InvalidInput,'CHILD_DRAFT_SOURCE_OR_QUARANTINE_MUTATED'):
            verify_partial_native_drafts(draft=d,externally_pinned_draft_sha256=json_digest(d),**self.kw)

    def test_07_parent_task_shrinkage_cannot_be_repinned(self):
        bad=copy.deepcopy(self.kw)
        bad['review_tasks']['child_tasks'][0]['atom_review_tasks']=[]
        bad['externally_pinned_review_tasks_sha256']=json_digest(bad['review_tasks'])
        with self.assertRaisesRegex(InvalidInput,'REVIEW_TASK_SOURCE_CONTENT_OR_ROLE_MUTATION'):
            build_partial_native_drafts(**bad)

    def test_08_wrong_independent_task_digest_is_fail_closed(self):
        bad=dict(self.kw,externally_pinned_review_tasks_sha256='f'*64)
        with self.assertRaisesRegex(InvalidInput,'REVIEW_TASKS_DIGEST_MISMATCH'):
            build_partial_native_drafts(**bad)

if __name__=='__main__':unittest.main()