"""Synthetic arithmetic/source-binding tests; no financial truth assertions."""
import copy
import unittest
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import Cue, VerifiedSource
from ire.v6.semantic_source_graph import source_grid, compile_graph
from ire.v6.calculation_lineage import _value, verify_calculations


class CalculationLineageTests(unittest.TestCase):
    def setUp(self):
        texts = ['연간 120만 원', '월 10만 원']
        self.s = VerifiedSource('AbCdEf12345','a'*64,'b'*64,'c'*64,
            tuple(Cue(i,i*100,i*100+90,t) for i,t in enumerate(texts,1)),1,2,(('W00001',1,2),))
        self.packet = {'schema':'IRE_V3_SEMANTIC_GRAPH_PACKET_V1',
            'grid_sha256':json_digest(source_grid(self.s)), 'residual':[], 'nodes':[{
            'predicate':'연 금액을 월 금액으로 환산한다.', 'atomicity_reason':'One arithmetic example.',
            'kind':'MATH','utterance_act':'CALCULATION','speaker':{'participant_id':'UNKNOWN',
            'status':'UNRESOLVED','evidence':[],'reason':'No authenticated speaker.'},
            'attribution':'DIRECT','attributed_participant':None,'polarity':'AFFIRMED',
            'modality':'HYPOTHETICAL','correction':False,'as_of':None,
            'direct':[[i,0,len(t)] for i,t in enumerate(texts,1)],'context':[], 'qualifiers':[],
            'numbers':[{'parts':[[1,3,len(texts[0])]],'function':'AMOUNT','reason':'Annual amount.'},
                       {'parts':[[2,2,len(texts[1])]],'function':'AMOUNT','reason':'Monthly amount.'}],
            'risk':'HIGH','risk_reason':'Amount verification required.'}]}
        g = compile_graph(self.s,self.packet); self.pin=g['packet_sha256']
        refs=[{'node_id':'A00001','edge_index':i,'edge_sha256':json_digest(e)}
            for i,e in enumerate(g['nodes']['A00001']['numbers'],1)]
        self.rows=[{'id':'annual','operation':'ANNUAL_TO_MONTHLY','inputs':refs[:1],'reported':refs[1],
            'scope_evidence':[{'span':[i,0,len(t)],'text_sha256':sha256(t.encode())} for i,t in enumerate(texts,1)],
            'reason':'Annual amount divided into twelve months.'}]
    def run_calc(self, rows=None):
        return verify_calculations(self.s,self.packet,self.rows if rows is None else rows,expected_packet_sha256=self.pin)
    def test_annual_conversion(self):
        r=self.run_calc(); self.assertEqual(r['results'][0]['status'],'ARITHMETIC_MATCH')
        self.assertEqual(r['results'][0]['derived_krw_numerator'],'100000')
        self.assertFalse(r['financial_approval']);self.assertFalse(r['publication_authorized'])
    def test_no_implicit_units(self):
        for v in ('200','16.5','100만','6900'):
            self.assertEqual(_value(v),('UNRESOLVED',None))
        self.assertEqual(_value('1천만 원'),('KRW',10000000))
        self.assertEqual(_value('10%')[1]*10,1)
    def test_missing_operand_scope(self):
        r=copy.deepcopy(self.rows);r[0]['scope_evidence'].pop()
        with self.assertRaisesRegex(InvalidInput,'CALC_MISSING_OPERAND_SCOPE'):self.run_calc(r)
    def test_duplicate_operand(self):
        r=copy.deepcopy(self.rows);r[0]['reported']=r[0]['inputs'][0]
        with self.assertRaisesRegex(InvalidInput,'CALC_DUPLICATE_EDGE'):self.run_calc(r)
    def test_wrong_edge_pin(self):
        r=copy.deepcopy(self.rows);r[0]['reported']['edge_sha256']='f'*64
        with self.assertRaisesRegex(InvalidInput,'CALC_EDGE_PIN'):self.run_calc(r)
