"""V237 source-bound child review task contract: no artificial E3/E4 approval."""
from __future__ import annotations
import copy
import unittest
from ire.v6.codec import ZERO_SHA,json_digest
from ire.v6.errors import InvalidInput
import test_v234_e1_cross_child_context_custody as v234_fixture
from v234_e1_cross_child_context_custody import build_lossless_context_escrow
from v237_e1_parent_child_review_contract import (build_child_review_tasks,
                                                   verify_child_review_tasks)


class TestV237RealContract(unittest.TestCase):
    def setUp(self):
        fx=v234_fixture.TestV234CrossChildCustody('test_01_two_scopes_three_local_atoms_no_cross')
        fx.setUp()
        self.fx=fx
        self.addCleanup(fx.doCleanups)
        self.args=fx._with_cross()
        self.escrow=build_lossless_context_escrow(**self.args)
        self.args.update(cross_context_escrow=self.escrow,
                         externally_pinned_escrow_sha256=json_digest(self.escrow))

    def tasks(self):
        return build_child_review_tasks(**self.args)

    def test_01_review_jobs_expose_cross_scope_source_not_suppress(self):
        x=self.tasks()
        self.assertEqual((x['child_count'],x['parent_atom_count'],
            x['cross_segment_atom_count'],x['external_cue_reference_edges']), (2,3,1,1))
        self.assertEqual(sum(len(t['atom_review_tasks']) for t in x['child_tasks']),3)
        self.assertEqual(sum(len(t['source_cues']) for t in x['child_tasks']),8)
        self.assertFalse(x['e4_authorized'])
        self.assertEqual(x['e3_formal_child_approvals'],0)
        task=x['child_tasks'][0]['atom_review_tasks'][0]
        self.assertTrue(task['requires_cross_child_semantic_review'])
        self.assertEqual(task['source_context_references'][-1]['source_child_id'],'B0002')
        self.assertIn('CONDITION',task['source_context_references'][-1]['roles'])

    def test_02_source_digest_and_all_rows_exactly_replayed(self):
        x=self.tasks()
        got=verify_child_review_tasks(review_tasks=x,
            externally_pinned_review_tasks_sha256=json_digest(x),**self.args)
        self.assertEqual(got['external_cue_reference_edges'],1)

    def test_03_parent_atom_proposition_change_rejected_even_if_task_rehashed(self):
        x=self.tasks()
        x['child_tasks'][0]['atom_review_tasks'][0]['parent_proposition']='FORGED TEXT'
        with self.assertRaisesRegex(InvalidInput,'REVIEW_TASK_SOURCE_CONTENT_OR_ROLE_MUTATION'):
            verify_child_review_tasks(review_tasks=x,
                externally_pinned_review_tasks_sha256=json_digest(x),**self.args)

    def test_04_external_quote_mutation_rejected(self):
        x=self.tasks()
        x['child_tasks'][0]['atom_review_tasks'][0]['source_context_references'][-1]['quote']='FORGED OUTSIDE CUE'
        with self.assertRaisesRegex(InvalidInput,'REVIEW_TASK_SOURCE_CONTENT_OR_ROLE_MUTATION'):
            verify_child_review_tasks(review_tasks=x,
                externally_pinned_review_tasks_sha256=json_digest(x),**self.args)

    def test_05_missing_child_atom_rejected(self):
        x=self.tasks()
        x['child_tasks'][0]['atom_review_tasks'].pop(0)
        with self.assertRaisesRegex(InvalidInput,'REVIEW_TASK_SOURCE_CONTENT_OR_ROLE_MUTATION'):
            verify_child_review_tasks(review_tasks=x,
                externally_pinned_review_tasks_sha256=json_digest(x),**self.args)

    def test_06_claimed_chat_approval_rejected(self):
        x=self.tasks()
        x['child_tasks'][0]['child_v123_approved']=True
        with self.assertRaisesRegex(InvalidInput,'REVIEW_TASK_SOURCE_CONTENT_OR_ROLE_MUTATION'):
            verify_child_review_tasks(review_tasks=x,
                externally_pinned_review_tasks_sha256=json_digest(x),**self.args)

    def test_07_invalid_foreign_parent_plan_pinned(self):
        args=dict(self.args,externally_pinned_parent_plan_sha256='f'*64)
        with self.assertRaisesRegex(InvalidInput,'EXTERNAL_SOURCE_EXCHANGE_OR_PARENT_PIN_DRIFT'):
            build_child_review_tasks(**args)

    def test_08_invalid_parent_atom_digest_pinned(self):
        args=dict(self.args,externally_pinned_exchange_digest='f'*64)
        with self.assertRaisesRegex(InvalidInput,'EXTERNAL_SOURCE_EXCHANGE_OR_PARENT_PIN_DRIFT'):
            build_child_review_tasks(**args)

    def test_09_child_source_quote_replaced(self):
        x=self.tasks();x['child_tasks'][1]['source_cues'][0]['quote']='FAKE'
        with self.assertRaisesRegex(InvalidInput,'REVIEW_TASK_SOURCE_CONTENT_OR_ROLE_MUTATION'):
            verify_child_review_tasks(review_tasks=x,
                externally_pinned_review_tasks_sha256=json_digest(x),**self.args)

    def test_10_no_cross_still_never_self_certifies_approval(self):
        args=self.fx.args()
        escrow=build_lossless_context_escrow(**args)
        x=build_child_review_tasks(**args,cross_context_escrow=escrow,
            externally_pinned_escrow_sha256=json_digest(escrow))
        self.assertEqual(x['cross_segment_atom_count'],0)
        self.assertEqual(x['e3_formal_child_approvals'],0)
        self.assertEqual(x['e5_published'],0)

if __name__=='__main__':unittest.main()