"""Synthetic source-scope patch contracts, not meaning/financial truth."""
import copy, unittest
from ire.v6.codec import json_digest
from ire.v6.errors import InvalidInput
from ire.v6.semantic_source_graph import compile_graph, _rows_digest
from ire.v6.obligation_ledger import genesis
from ire.v6.qualifier_gap_review import draft_qualifier_gaps
from ire.v6.tests import test_shared_qualifier_review as fixture


class QualifierGapReviewTests(unittest.TestCase):
    def setUp(self):
        f=fixture.SharedQualifierTests(); f.setUp(); self.f=f
        self.packet=copy.deepcopy(f.packet)
        for n in self.packet['nodes']:
            n['qualifiers']=[]; n['context']=[f.span(1)]; n['modality']='UNRESOLVED'
        self.g=compile_graph(f.s,self.packet)
        self.c=copy.deepcopy(f.c); self.c[0]['candidate_edges']=[]
        self.pins={'expected_old_digest':_rows_digest(f.old),'expected_candidate_digest':_rows_digest(self.c),
                   'expected_packet_sha':self.g['packet_sha256']}
        self.head=genesis(f.s,**self.pins)
        self.rows=[{'old_sha256':f.key,'decision':'SCOPE_DRAFT','scope_id':'Q001','evidence':[f.ev(1)],
                    'reason':'Explicit original condition review.'}]
        self.scopes=[{'scope_id':'Q001','node_id':'A00001','type':'CONDITION','role':'SOURCE_CONDITION',
                      'parts':[f.ev(1)],'consequent':f.ev(2),'reason':'Common scope is proposed for this consequent.'}]
    def check(self,rows=None,scopes=None):
        return draft_qualifier_gaps(self.f.s,self.packet,self.f.old,self.c,[],
            self.rows if rows is None else rows,self.scopes if scopes is None else scopes,
            expected_head=self.head,**self.pins)
    def test_patch_is_separate_and_provisional(self):
        p,r=self.check();self.assertEqual(r['new_qualifier_edges'],1)
        self.assertEqual(self.packet['nodes'][0]['qualifiers'],[])
        self.assertEqual(p['nodes'][0]['qualifiers'][0]['span'],self.f.span(1))
        self.assertFalse(r['ready_for_e3']);self.assertFalse(r['publication_authorized'])
    def test_scope_not_consequent(self):
        q=copy.deepcopy(self.scopes);q[0]['consequent']=self.f.ev(1)
        with self.assertRaisesRegex(InvalidInput,'GAP_CONSEQUENT'):self.check(scopes=q)
    def test_unaccounted_source(self):
        q=copy.deepcopy(self.scopes);q[0]['parts'].append(self.f.ev(3))
        with self.assertRaisesRegex(InvalidInput,'GAP_UNACCOUNTED_SCOPE_PART'):self.check(scopes=q)
    def test_duplicate_row(self):
        with self.assertRaisesRegex(InvalidInput,'GAP_OLD_ID'):self.check(rows=self.rows*2)
    def test_open_does_not_insert_qualifier(self):
        r=copy.deepcopy(self.rows);r[0].update(decision='OPEN',scope_id=None)
        p,s=self.check(rows=r,scopes=[]);self.assertEqual(self.packet,p);self.assertEqual(s['new_qualifier_edges'],0)
