"""Synthetic shared-scope contracts; no financial truth or release."""
import copy, unittest
from ire.v6.codec import json_digest,sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import Cue,VerifiedSource
from ire.v6.semantic_source_graph import compile_graph,source_grid,_rows_digest
from ire.v6.semantic_obligation_review import review_batch
from ire.v6.shared_qualifier_review import review_shared_qualifiers
from ire.v6.semantic_graph_journal import revision,_edges

class SharedQualifierTests(unittest.TestCase):
    def setUp(self):
        texts=['조건을 충족하면','첫 번째 결과이다','다른 결과이다']
        cues=tuple(Cue(i,i*100,i*100+90,t) for i,t in enumerate(texts,1))
        self.s=VerifiedSource('AbCdEf12345','a'*64,'b'*64,'c'*64,cues,1,3,(('W00001',1,3),))
        span=lambda i:[i,0,len(texts[i-1])]
        self.span=span
        q={'type':'CONDITION','span':span(1),'reason':'Explicit synthetic common condition.'}
        node={'predicate':'첫 번째 결과이다','atomicity_reason':'One synthetic predicate.',
              'kind':'FACT','utterance_act':'ASSERTION','speaker':{'participant_id':'UNKNOWN','status':'UNRESOLVED','evidence':[],'reason':'No speaker authentication.'},
              'attribution':'DIRECT','attributed_participant':None,'polarity':'AFFIRMED','modality':'CONDITIONAL',
              'correction':False,'as_of':None,'direct':[span(2)],'context':[],'qualifiers':[q],
              'numbers':[],'risk':'HIGH','risk_reason':'Synthetic high-risk claim.'}
        other={**copy.deepcopy(node),'predicate':'다른 결과이다','direct':[span(3)]}
        self.packet={'schema':'IRE_V3_SEMANTIC_GRAPH_PACKET_V1','grid_sha256':json_digest(source_grid(self.s)),
                     'nodes':[node,other],'residual':[]}
        self.g=compile_graph(self.s,self.packet)
        self.old=[{'obligation':{'type':'CONDITION','position_status':'CUE_ONLY','positions':[span(1)],'raw':1}}]
        self.key=json_digest(self.old[0]);self.edges=[{'node_id':k,'edge_index':1,'edge_sha256':json_digest(q)} for k in self.g['nodes']]
        self.c=[{'old_obligation_sha256':self.key,'candidate_group_nodes':list(self.g['nodes']),'candidate_edges':self.edges,'qualifier_separation':None}]
        self.ev=lambda i:{'span':span(i),'text_sha256':sha256(texts[i-1].encode())}
        self.prior=[{'old_sha256':self.key,'decision':'OPEN','role':'UNKNOWN','edge':None,'evidence':[self.ev(1)],'reason':'Previously unresolved common condition.','review_note':None}]
        self.pins={'expected_old_digest':_rows_digest(self.old),'expected_candidate_digest':_rows_digest(self.c),'expected_packet_sha':self.g['packet_sha256']}
        self.receipt=review_batch(self.s,self.g,self.old,self.c,self.prior,**self.pins)
        self.rows=[{'old_sha256':self.key,'prior_row_sha256':json_digest(self.prior[0]),'reason':'Review each consequent independently.',
                    'targets':[{'edge':e,'decision':'APPLY','reason':'Common condition limits this consequent.','condition_evidence':self.ev(1),'predicate_evidence':self.ev(i)} for i,e in enumerate(self.edges,2)]}]
    def check(self,rows=None):
        return review_shared_qualifiers(self.s,self.packet,self.old,self.c,self.prior,self.receipt,
            self.rows if rows is None else rows,expected_prior_receipt_sha256=json_digest(self.receipt),**self.pins)
    def test_two_successors_and_original_open_preserved(self):
        r=self.check();self.assertEqual(r['applied_edges'],2);self.assertEqual(r['new_obligations'],0)
        self.assertEqual(self.prior[0]['decision'],'OPEN');self.assertFalse(r['publication_authorized'])
    def test_missing_target_rejected(self):
        r=copy.deepcopy(self.rows);r[0]['targets'].pop()
        with self.assertRaisesRegex(InvalidInput,'SHARED_TARGET_CENSUS'):self.check(r)
    def test_condition_is_not_consequent(self):
        r=copy.deepcopy(self.rows);r[0]['targets'][0]['predicate_evidence']=self.ev(1)
        with self.assertRaisesRegex(InvalidInput,'SHARED_PREDICATE_EVIDENCE'):self.check(r)
    def test_explicit_open_not_approved(self):
        r=copy.deepcopy(self.rows);r[0]['targets'][1]['decision']='OPEN'
        self.assertEqual(self.check(r)['open_obligations'],1)
    def test_native_split_carries_both(self):
        p=copy.deepcopy(self.packet);p['nodes'][0]['predicate']='두 가지 결과를 설명한다';p['nodes'][0]['direct']=[self.span(2),self.span(3)];p['nodes'].pop()
        a=compile_graph(self.s,p);b=self.g;d=next(iter(_edges(a['nodes']['A00001'])))
        f=[{'old_ids':['A00001'],'new_ids':list(b['nodes']),'operation':'SPLIT','reason':'Separate the two synthetic predicates.','losses':[],
            'carries':[{'old_id':'A00001','edge_sha256':d,'new_id':k,'reason':'Explicit common condition carry.'} for k in b['nodes']]}]
        g=[{'old_ids':[k],'new_ids':[k],'operation':'KEEP','reason':'Same synthetic predicate.','losses':[],
            'carries':[{'old_id':k,'edge_sha256':d,'new_id':k,'reason':'Keep original condition binding.'}]} for k in b['nodes']]
        self.assertFalse(revision(self.s,a,b,self.packet,f,g)['publication_authorized'])
        lost=copy.deepcopy(f);lost[0]['carries'].pop()
        with self.assertRaisesRegex(InvalidInput,'SHARED_QUALIFIER_TARGET_UNREVIEWED'):revision(self.s,a,b,self.packet,lost,g)
        lost[0]['shared_qualifier_exclusions']=[f[0]['carries'][1]]
        r=revision(self.s,a,b,self.packet,lost,g);self.assertTrue(any(x['disposition']=='SHARED_QUALIFIER_EXCLUSION_REQUIRES_E3' for x in r['first_lineage']['escrow']))
