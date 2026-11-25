"""Source-link review transitions: structural tests, not gold certification."""
import copy, unittest
from ire.v6.codec import json_digest
from ire.v6.errors import InvalidInput
from ire.v6.pending_semantic_review import pending_review
from ire.v6.semantic_graph_journal import _allowed
from ire.v6.tests import test_successor_amendment as fixture


class PendingSemanticReviewTests(unittest.TestCase):
    def setUp(self):
        f=fixture.SuccessorAmendmentTests();f.setUp();self.addCleanup(f.doCleanups)
        self.f=f;self.j=f.j
        c=self.j.pending_review_context();q=c['plan']['scope_items'][0]
        self.row=dict(kind='SCOPE',id=q['scope_id'],prior_sha256=q['review_sha256'],
            decision='SOURCE_LINK_REVIEWED',node_id=q['candidate_nodes'][0],role=q['role'],
            edge_index=None,edge_sha256=None,evidence=q['antecedent']+[q['consequent']],
            reason='Synthetic source condition review, not financial approval.')

    def payload(self,row):
        c=self.j.pending_review_context();rows=[copy.deepcopy(row)]
        receipt=pending_review(self.j.source,c['graph'],c['plan'],c['old'],rows,c['prior_rows'])
        return dict(rows=rows,receipt=receipt)

    def test_review_requires_successor(self):
        for phase in (None,'REGISTER','REVISION','RECONCILIATION','LEGACY_RECONCILIATION'):
            self.assertFalse(_allowed(phase,'PENDING_REVIEW'))
        self.assertTrue(_allowed('SUCCESSOR','PENDING_REVIEW'))

    def test_hold_can_be_reviewed_once_and_retry_idempotent(self):
        hold=dict(self.row,decision='HOLD',node_id=None,role='UNKNOWN',reason='Synthetic initial uncertainty remains open.')
        a=self.payload(hold);self.j.append('PENDING_REVIEW',a)
        self.assertEqual(self.j.snapshot()['pending_review']['remaining_scope_drafts'],1)
        b=self.payload(self.row);h=self.j.append('PENDING_REVIEW',b)
        self.assertEqual(self.j.append('PENDING_REVIEW',b),h)
        self.assertEqual(self.j.snapshot()['pending_review']['remaining_scope_drafts'],0)
        self.assertFalse(self.j.snapshot()['pending_review']['ready_for_e3'])
        with self.assertRaises(InvalidInput):self.payload(self.row)

    def test_wrong_evidence_or_role_fails(self):
        for field,val in [('role','QUESTION_PREMISE'),('prior_sha256','0'*64)]:
            with self.subTest(field=field),self.assertRaises(InvalidInput):self.payload(dict(self.row,**{field:val}))
        row=copy.deepcopy(self.row);row['evidence'].pop()
        with self.assertRaises(InvalidInput):self.payload(row)

    def test_new_graph_explicitly_invalidates_review(self):
        self.j.append('PENDING_REVIEW',self.payload(self.row));before=self.j.snapshot()
        amendment=self.f.proposal('새로운 합성 재검토 문장')
        with self.assertRaisesRegex(InvalidInput,'AMENDMENT_REVIEW_INVALIDATION'):
            self.j.append('SUCCESSOR_AMENDMENT',amendment)
        self.assertEqual(self.j.snapshot(),before)
        pin=json_digest(before['pending_review']);amendment['invalidated_review_sha256']=pin
        self.j.append('SUCCESSOR_AMENDMENT',amendment)
        after=self.j.snapshot();self.assertNotIn('pending_review',after)
        self.assertEqual(after['invalidated_reviews'],[pin])
        self.assertFalse(after['publication_authorized'])
