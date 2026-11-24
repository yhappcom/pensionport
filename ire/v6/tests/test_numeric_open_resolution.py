"""Numeric OPEN amendment preserves historical events and fails closed."""
import copy, unittest
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import Cue, VerifiedSource
from ire.v6.semantic_source_graph import compile_graph, source_grid, _rows_digest
from ire.v6.obligation_ledger import genesis, append, replay
from ire.v6.tests.test_shared_qualifier_review import SharedQualifierTests as Fixture

class NumericOpenResolutionTests(unittest.TestCase):
    def setUp(self):
        f=Fixture();f.setUp()
        text='월 50만 원을 납입한다'
        self.s=VerifiedSource('AbCdEf12345','a'*64,'b'*64,'c'*64,(Cue(1,100,190,text),),1,1,(('W00001',1,1),))
        node=copy.deepcopy(f.packet['nodes'][0]);span=[1,2,7]
        node.update(predicate=text,direct=[[1,0,len(text)]],qualifiers=[],modality='UNRESOLVED',numbers=[{'parts':[span],'function':'AMOUNT','reason':'Explicit synthetic amount.'}])
        self.packet={'schema':'IRE_V3_SEMANTIC_GRAPH_PACKET_V1','grid_sha256':json_digest(source_grid(self.s)),'nodes':[node],'residual':[]}
        g=compile_graph(self.s,self.packet);self.old=[{'obligation':{'type':'NUMBER','position_status':'EXACT_UNIQUE','positions':[span],'raw':{'token':text[2:7]}}}];key=json_digest(self.old[0])
        edge={'node_id':'A00001','edge_index':1,'edge_sha256':json_digest(g['nodes']['A00001']['numbers'][0])}
        self.c=[{'old_obligation_sha256':key,'candidate_group_nodes':['A00001'],'candidate_edges':[edge],'qualifier_separation':None}]
        self.pins=dict(expected_old_digest=_rows_digest(self.old),expected_candidate_digest=_rows_digest(self.c),expected_packet_sha=g['packet_sha256']);self.args=(self.s,self.packet,self.old,self.c)
        self.prior={'old_sha256':key,'decision':'OPEN','role':'UNKNOWN','edge':None,'evidence':[{'span':span,'text_sha256':sha256(text[2:7].encode())}],'reason':'Previously unresolved synthetic amount.','review_note':None}
        self.row={**self.prior,'decision':'CARRY_SOURCE_EDGE','role':'AMOUNT','edge':edge,'reason':'Explicit original amount and coordinate.'}
        self.events,self.head=append(*self.args,[],'SINGLE',[self.prior],expected_head=genesis(self.s,**self.pins),**self.pins)
    def test_successor_preserves_original(self):
        e,h=append(*self.args,self.events,'RESOLVE_NUMERIC_OPEN',[self.row],expected_head=self.head,**self.pins)
        self.assertEqual(e[:-1],self.events);self.assertEqual(e[0]['rows'][0]['decision'],'OPEN')
        result=replay(*self.args,e,expected_head=h,**self.pins)
        self.assertEqual(result['effective_counts'],{'CARRY_SOURCE_EDGE':1});self.assertEqual(result['reviewed'],1);self.assertFalse(result['ready_for_e3']);self.assertFalse(result['publication_authorized'])
        with self.assertRaises(InvalidInput):append(*self.args,e,'RESOLVE_NUMERIC_OPEN',[self.row],expected_head=h,**self.pins)
    def test_wrong_source_evidence(self):
        bad=copy.deepcopy(self.row);bad['evidence'][0]['text_sha256']='0'*64
        with self.assertRaises(InvalidInput):append(*self.args,self.events,'RESOLVE_NUMERIC_OPEN',[bad],expected_head=self.head,**self.pins)
    def test_open_to_open(self):
        with self.assertRaises(InvalidInput):append(*self.args,self.events,'RESOLVE_NUMERIC_OPEN',[self.prior],expected_head=self.head,**self.pins)
    def test_qualifier_not_eligible(self):
        f=Fixture();f.setUp();args=(f.s,f.packet,f.old,f.c)
        e,h=append(*args,[],'SINGLE',f.prior,expected_head=genesis(f.s,**f.pins),**f.pins)
        with self.assertRaises(InvalidInput):append(*args,e,'RESOLVE_NUMERIC_OPEN',f.prior,expected_head=h,**f.pins)
