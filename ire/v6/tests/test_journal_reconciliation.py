"""Journal reconciliation transition and source-bound payload contracts."""
import copy, unittest
from ire.v6.codec import json_digest
from ire.v6.errors import InvalidInput
from ire.v6.semantic_graph_journal import GraphJournal, _allowed
from ire.v6.semantic_reconciliation import reconciliation_plan
from ire.v6.tests.test_qualifier_gap_review import QualifierGapReviewTests as Fixture


class JournalReconciliationTests(unittest.TestCase):
    def setUp(self):
        t=Fixture();t.setUp();_,r=t.check()
        pins=dict(expected_head=t.head,expected_gap_receipt_sha256=json_digest(r),**t.pins)
        plan=reconciliation_plan(t.f.s,t.packet,t.f.old,t.c,[],t.rows,t.scopes,**pins)
        self.payload=dict(packet=t.packet,old=t.f.old,candidates=t.c,events=[],rows=t.rows,scopes=t.scopes,pins=pins,plan=plan,plan_sha256=json_digest(plan))
        self.j=object.__new__(GraphJournal);self.j.source=t.f.s

    def test_order(self):
        chain=['REGISTER','FIRST','SECOND','SCORE','DISPUTES','REVISION','RECONCILIATION']
        for a,b in zip([None]+chain,chain):self.assertTrue(_allowed(a,b))
        self.assertTrue(_allowed('REGISTER','LEGACY_RECONCILIATION'))
        for a,b in [('REGISTER','RECONCILIATION'),('FIRST','LEGACY_RECONCILIATION'),('LEGACY_RECONCILIATION','FIRST'),('RECONCILIATION','FIRST')]:
            self.assertFalse(_allowed(a,b))

    def test_native_revision_binding(self):
        p={'revision':{'final_packet_sha256':self.payload['pins']['expected_packet_sha']}}
        self.j._apply(p,'RECONCILIATION',self.payload)
        self.assertFalse(p['reconciliation']['legacy_development']);self.assertFalse(p['reconciliation']['ready_for_e3'])
        with self.assertRaisesRegex(InvalidInput,'RECONCILIATION_REVISION_DRIFT'):
            self.j._apply({'revision':{'final_packet_sha256':'0'*64}},'RECONCILIATION',self.payload)

    def test_legacy_development_only(self):
        with self.assertRaisesRegex(InvalidInput,'LEGACY_DEVELOPMENT_ONLY'):
            self.j._apply({'plan':{'purpose':'HOLDOUT'}},'LEGACY_RECONCILIATION',self.payload)
        p={'plan':{'purpose':'DEVELOPMENT'}};self.j._apply(p,'LEGACY_RECONCILIATION',self.payload)
        self.assertTrue(p['reconciliation']['legacy_development']);self.assertFalse(p['reconciliation']['publication_authorized'])

    def test_mutation_rejected(self):
        bad=copy.deepcopy(self.payload);bad['plan']['scope_items'][0]['role']='REVIEW_NOTE'
        with self.assertRaises(InvalidInput):self.j._apply({'plan':{'purpose':'DEVELOPMENT'}},'LEGACY_RECONCILIATION',bad)
