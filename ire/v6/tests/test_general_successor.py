"""Synthetic general successor contracts; not semantic correctness."""
import copy, unittest
from ire.v6.codec import json_digest
from ire.v6.errors import InvalidInput
from ire.v6.semantic_graph_journal import _allowed, _edges, successor_revision, GraphJournal
from ire.v6.semantic_source_graph import compile_graph, BOUNDARY_PACKET
from ire.v6.semantic_reconciliation import reconciliation_plan
from ire.v6.tests import test_qualifier_gap_review as fixture

class GeneralSuccessorTests(unittest.TestCase):
    def setUp(self):
        t=fixture.QualifierGapReviewTests();t.setUp();self.s=t.f.s
        draft,r=t.check();self.parent=compile_graph(self.s,draft)
        self.plan=reconciliation_plan(self.s,t.packet,t.f.old,t.c,[],t.rows,t.scopes,
            expected_head=t.head,expected_gap_receipt_sha256=json_digest(r),**t.pins)
        self.packet=copy.deepcopy(draft);self.packet['schema']=BOUNDARY_PACKET
        self.packet['nodes'][0]['predicate']='두 결과에 대한 합성 검증 사례'
        self.packet['nodes'][0]['direct']=[t.f.span(2),t.f.span(3)];self.packet['nodes'].pop()
        self.lineage=[dict(old_ids=['A00001','A00002'],new_ids=['A00001'],operation='MERGE',reason='Synthetic merge for structural regression only.',losses=[],carries=[dict(old_id=n,edge_sha256=h,new_id='A00001',reason='Original synthetic qualifier carry.') for n,v in self.parent['nodes'].items() for h in _edges(v)])]
    def run_revision(self,packet=None,lineage=None,edges=None):
        return successor_revision(self.s,self.parent,self.plan,self.packet if packet is None else packet,self.lineage if lineage is None else lineage,[] if edges is None else edges)
    def test_merge_keeps_pending_scope(self):
        r=self.run_revision();self.assertEqual(r['lineage']['operations'],{'MERGE':1});self.assertEqual(r['scope_drafts'],1);self.assertFalse(r['ready_for_e3'])
    def test_unaccounted_edge_fails(self):
        p=copy.deepcopy(self.packet);p['nodes'][0]['qualifiers'].append(dict(type='EXCEPTION',span=p['nodes'][0]['direct'][0],reason='Synthetic newly proposed edge.'))
        with self.assertRaisesRegex(InvalidInput,'SUCCESSOR_NEW_EDGE_CENSUS'):self.run_revision(packet=p)
        f=compile_graph(self.s,p);old=set(_edges(self.parent['nodes']['A00001']));new=set(_edges(f['nodes']['A00001']))-old
        self.assertEqual(self.run_revision(packet=p,edges=[dict(node_id='A00001',edge_sha256=h,reason='Synthetic review required.') for h in new])['new_edge_count'],1)
    def test_transition_restrictions(self):
        self.assertTrue(_allowed('RECONCILIATION','SUCCESSOR'));self.assertTrue(_allowed('LEGACY_RECONCILIATION','SUCCESSOR'))
        for stage in (None,'REGISTER','FIRST','SECOND','REVISION','SUCCESSOR'):self.assertFalse(_allowed(stage,'SUCCESSOR'))
    def test_native_successor_application_receipt_checked(self):
        j=object.__new__(GraphJournal);j.source=self.s;p={'reconciliation_parent':self.parent,'reconciliation_plan':self.plan}
        r=self.run_revision();v=dict(packet=self.packet,lineage=self.lineage,new_edges=[],receipt=r)
        j._apply(p,'SUCCESSOR',v);self.assertEqual(p['successor'],r)
        bad=copy.deepcopy(v);bad['receipt']['publication_authorized']=True
        with self.assertRaisesRegex(InvalidInput,'SUCCESSOR_DRIFT'):j._apply(p,'SUCCESSOR',bad)
