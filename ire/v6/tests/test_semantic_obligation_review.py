"""Synthetic tests of the explicit review sidecar; not semantic truth."""
import copy,unittest
from types import SimpleNamespace
from ire.v6.codec import json_digest,sha256
from ire.v6.errors import InvalidInput
from ire.v6.semantic_source_graph import _rows_digest
from ire.v6.semantic_obligation_review import review_batch

class ObligationReviewTests(unittest.TestCase):
    def setUp(self):
        self.src=SimpleNamespace(source_sha256='a'*64,cues=[SimpleNamespace(text='100원'),SimpleNamespace(text='별도 문맥')])
        v={'parts':[[1,0,4]],'literal':'100원','cross_cue':False}
        self.g={'grid':{'source_sha256':'a'*64},'packet_sha256':'b'*64,'nodes':{'A00001':{'direct':[[1,0,4]],'numbers':[v],'qualifiers':[]}}}
        self.old=[{'obligation':{'type':'NUMBER','position_status':'EXACT_UNIQUE','positions':[[1,0,4]],'raw':{'token':'100원'}}},
                  {'obligation':{'type':'CONDITION','position_status':'SEMANTIC_ONLY_NO_EXPLICIT_COORDINATE','positions':[],'raw':'후속 제도 검토'}}]
        self.edge={'node_id':'A00001','edge_index':1,'edge_sha256':json_digest(v)}
        self.c=[{'old_obligation_sha256':json_digest(self.old[0]),'candidate_group_nodes':['A00001'],'candidate_edges':[self.edge],'qualifier_separation':None},
                {'old_obligation_sha256':json_digest(self.old[1]),'candidate_group_nodes':['A00001'],'candidate_edges':[],'qualifier_separation':'REVIEW_NOTE'}]
        ev=[{'span':[1,0,4],'text_sha256':sha256('100원'.encode())}]
        self.rows=[{'old_sha256':json_digest(self.old[0]),'decision':'CARRY_SOURCE_EDGE','role':'AMOUNT','edge':self.edge,'evidence':ev,'reason':'Explicit source amount review.','review_note':None},
                   {'old_sha256':json_digest(self.old[1]),'decision':'REVIEWER_NOTE','role':'REVIEW_NOTE','edge':None,'evidence':ev,'reason':'Separate downstream reviewer caution.','review_note':'후속 제도 검토'}]
        self.pins={'expected_old_digest':_rows_digest(self.old),'expected_candidate_digest':_rows_digest(self.c),'expected_packet_sha':'b'*64}
    def run_review(self,rows):return review_batch(self.src,self.g,self.old,self.c,rows,**self.pins)
    def test_explicit_two_decisions_and_partial(self):
        result=self.run_review(self.rows)
        self.assertEqual(result['reviewed'],2);self.assertEqual(result['remaining_unreviewed'],0)
        self.assertFalse(result['publication_authorized']);self.assertFalse(result['claim_semantic_equivalence_certified'])
        self.assertEqual(self.run_review(self.rows[:1])['remaining_unreviewed'],1)
    def test_duplicate_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'OLD_ID'):self.run_review(self.rows+[self.rows[0]])
    def test_context_not_financial_number(self):
        r=copy.deepcopy(self.rows);r[0].update(decision='CONTEXT_ONLY',role='CONTEXT')
        self.assertEqual(self.run_review(r)['decisions']['CONTEXT_ONLY'],1)
    def test_note_as_source_rejected(self):
        r=copy.deepcopy(self.rows);r[1].update(decision='CARRY_SOURCE_EDGE',role='CONDITION')
        with self.assertRaises(InvalidInput):self.run_review(r)
    def test_note_unrelated_evidence_rejected(self):
        r=copy.deepcopy(self.rows);r[1]['evidence']=[{'span':[2,0,2],'text_sha256':sha256('별도'.encode())}]
        with self.assertRaisesRegex(InvalidInput,'NOTE_UNRELATED_EVIDENCE'):self.run_review(r)
    def test_changed_parent_pin(self):
        self.pins['expected_old_digest']='f'*64
        with self.assertRaisesRegex(InvalidInput,'PARENT_PIN'):self.run_review(self.rows)
    def test_cross_cue_rebind_cannot_be_declared_for_single_span(self):
        r=copy.deepcopy(self.rows);r[0]['decision']='REBIND_SOURCE_FRAGMENT'
        with self.assertRaisesRegex(InvalidInput,'NOT_CROSS_CUE_FRAGMENT'):self.run_review(r)
