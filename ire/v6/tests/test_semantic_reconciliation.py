"""Synthetic reconciliation contract tests; real replay is kept separately."""
import copy, unittest
from ire.v6.codec import json_digest
from ire.v6.errors import InvalidInput
from ire.v6.qualifier_gap_review import draft_qualifier_gaps
from ire.v6.semantic_reconciliation import reconciliation_plan, verify_reconciliation_plan
from ire.v6.tests.test_qualifier_gap_review import QualifierGapReviewTests


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        t=QualifierGapReviewTests(); t.setUp(); self.t=t
        _,r=t.check()
        self.args=(t.f.s,t.packet,t.f.old,t.c,[],t.rows,t.scopes)
        self.kw=dict(expected_head=t.head,expected_gap_receipt_sha256=json_digest(r),**t.pins)

    def test_typed_scope_preserved(self):
        p=reconciliation_plan(*self.args,**self.kw)
        q=p['scope_items'][0]; s=self.t.scopes[0]
        self.assertEqual(q['antecedent'],s['parts']);self.assertEqual(q['consequent'],s['consequent'])
        self.assertEqual(q['role'],s['role']);self.assertEqual(q['obligation_ids'],[self.t.f.key])
        self.assertFalse(p['ready_for_e3']);self.assertFalse(p['financial_approval'])

    def test_mutations_rejected(self):
        p=reconciliation_plan(*self.args,**self.kw); h=json_digest(p)
        for change in ('role','consequent','obligation_ids'):
            with self.subTest(change=change):
                q=copy.deepcopy(p);q['scope_items'][0][change]=None
                with self.assertRaises(InvalidInput):verify_reconciliation_plan(q,*self.args,expected_plan_sha256=h,**self.kw)
        self.assertEqual(verify_reconciliation_plan(p,*self.args,expected_plan_sha256=h,**self.kw),h)

    def test_open_preserved(self):
        t=self.t;r=copy.deepcopy(t.rows);r[0].update(decision='OPEN',scope_id=None)
        a=(t.f.s,t.packet,t.f.old,t.c,[],r,[])
        _,receipt=draft_qualifier_gaps(*a,expected_head=t.head,**t.pins)
        p=reconciliation_plan(*a,expected_head=t.head,expected_gap_receipt_sha256=json_digest(receipt),**t.pins)
        self.assertEqual(p['open_items'][0]['old_sha256'],t.f.key)
        self.assertEqual(p['evidence_tasks'][0]['obligation_ids'],[t.f.key]);self.assertEqual(p['scope_items'],[])

    def test_gap_pin_rejected(self):
        with self.assertRaises(InvalidInput):reconciliation_plan(*self.args,**{**self.kw,'expected_gap_receipt_sha256':'0'*64})
