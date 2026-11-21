"""V239 mapping regression: V231 authenticator separately tested in V231 CI.

The mocked V231 verifier in this synthetic fixture ONLY isolates the mapping
stage; it does not constitute genuine ChatGPT identity or final approval.
"""
from __future__ import annotations
import copy,unittest
from unittest.mock import patch
from ire.v6.codec import json_digest
from ire.v6.errors import InvalidInput
import test_v234_e1_cross_child_context_custody as v234_fixture
from v234_e1_cross_child_context_custody import build_lossless_context_escrow
from v237_e1_parent_child_review_contract import build_child_review_tasks
from v239_e1_source_bound_second_turn_child_intake import build_pending_child_review_intake,verify_pending_child_review_intake

class TestV239SyntheticMappingOnly(unittest.TestCase):
    def setUp(self):
        fx=v234_fixture.TestV234CrossChildCustody('test_01_two_scopes_three_local_atoms_no_cross')
        fx.setUp();self.addCleanup(fx.doCleanups)
        a=fx._with_cross(); e=build_lossless_context_escrow(**a)
        a.update(cross_context_escrow=e,externally_pinned_escrow_sha256=json_digest(e))
        tasks=build_child_review_tasks(**a)
        self.args=dict(origin=a['origin'],review_tasks=tasks,checkpoint=a['checkpoint'],
            cross_context_escrow=e,externally_pinned_review_tasks_sha256=json_digest(tasks),
            second_receipt={'turn2_review':{'atom_adjudication_rows':[{
                'claim_id':atom['claim_id'],
                'disposition':'REQUIRES_SOURCE_MEANING_REPAIR' if atom['claim_id']=='C00001' else 'HOLD',
                'source_grounded_reason':'Synthetic unapproved source-side caveat',
                'e3_final_approved':False,'financial_fact_approved':False,
                'independent_gold_certified':False}
                for atom in a['origin']['exchange']['atoms']]}},
            private_source_note={},prequarantine={},
            externally_pinned_receipt_sha256='a'*64,
            externally_pinned_source_note_sha256='b'*64,
            externally_pinned_prequarantine_sha256='c'*64,
            **{k:v for k,v in a.items() if k not in ('origin','checkpoint','cross_context_escrow')})
    def build(self):
        with patch('v239_e1_source_bound_second_turn_child_intake.verify_real_turn2_private_custody',return_value={'status':'SYNTHETIC_STUB_DO_NOT_ATTEST'}):
            return build_pending_child_review_intake(**self.args)
    def test_01_real_child_task_bind_all_synthetic_second_turn_rows(self):
        d=self.build()
        self.assertEqual((d['child_count'],d['atom_review_count'],d['cross_atom_review_count']),(2,3,1))
        self.assertEqual((d['cross_atom_requires_repair'],d['cross_atom_hold_or_other']),(1,0))
        self.assertEqual(d['e3_formal_child_approvals'],0)
        self.assertFalse(d['host_turn_cryptographic_authentication'])
    def test_02_full_byte_replay_and_pin(self):
        d=self.build()
        with patch('v239_e1_source_bound_second_turn_child_intake.verify_real_turn2_private_custody',return_value={'status':'SYNTHETIC_STUB_DO_NOT_ATTEST'}):
            checked=verify_pending_child_review_intake(intake=d,externally_pinned_intake_sha256=json_digest(d),**self.args)
        self.assertEqual(checked['atom_review_count'],3)
    def test_03_missing_atom_is_rejected(self):
        a=copy.deepcopy(self.args);a['second_receipt']['turn2_review']['atom_adjudication_rows'].pop()
        with self.assertRaisesRegex(InvalidInput,'TURN2_ATOM_REVIEWS_INCOMPLETE'):
            with patch('v239_e1_source_bound_second_turn_child_intake.verify_real_turn2_private_custody',return_value={}):
                build_pending_child_review_intake(**a)
    def test_04_duplicate_atom_is_rejected(self):
        a=copy.deepcopy(self.args)
        rows=a['second_receipt']['turn2_review']['atom_adjudication_rows'];rows[2]=copy.deepcopy(rows[0])
        with self.assertRaisesRegex(InvalidInput,'TURN2_ATOM_REVIEWS_INCOMPLETE'):
            with patch('v239_e1_source_bound_second_turn_child_intake.verify_real_turn2_private_custody',return_value={}):
                build_pending_child_review_intake(**a)
    def test_05_fake_approved_atom_is_rejected(self):
        a=copy.deepcopy(self.args);a['second_receipt']['turn2_review']['atom_adjudication_rows'][0]['e3_final_approved']=True
        with self.assertRaisesRegex(InvalidInput,'SECOND_TURN_FALSE_AUTHORITY'):
            with patch('v239_e1_source_bound_second_turn_child_intake.verify_real_turn2_private_custody',return_value={}):
                build_pending_child_review_intake(**a)
    def test_06_outside_cue_quote_discrepancy_rejected(self):
        a=copy.deepcopy(self.args);a['review_tasks']['child_tasks'][0]['atom_review_tasks'][0]['source_context_references'][-1]['quote']='FAKE'
        a['externally_pinned_review_tasks_sha256']=json_digest(a['review_tasks'])
        with self.assertRaisesRegex(InvalidInput,'REVIEW_TASK_SOURCE_CONTENT_OR_ROLE_MUTATION'):
            with patch('v239_e1_source_bound_second_turn_child_intake.verify_real_turn2_private_custody',return_value={}):
                build_pending_child_review_intake(**a)
    def test_07_intake_approval_forgery_rejected(self):
        d=self.build();d['child_findings'][0]['real_v123_formal_child_approved']=True
        with self.assertRaisesRegex(InvalidInput,'SOURCE_OR_SECOND_TURN_REVIEW_INTAKE_MUTATED'):
            with patch('v239_e1_source_bound_second_turn_child_intake.verify_real_turn2_private_custody',return_value={}):
                verify_pending_child_review_intake(intake=d,externally_pinned_intake_sha256=json_digest(d),**self.args)

if __name__=='__main__':unittest.main()