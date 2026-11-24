"""Prospective lexical boundary policy: no historical packet rewrite."""
import copy, unittest
from ire.v6.semantic_source_graph import (numeric_token_ranges,numeric_binding,compile_graph,source_grid,
                                         LEGACY_PACKET,BOUNDARY_PACKET,score_graphs)
from ire.v6.source import Cue, VerifiedSource
from ire.v6.codec import json_digest
from ire.v6.errors import InvalidInput


def source(*texts):
    return VerifiedSource('AbCdEf12345','a'*64,'b'*64,'c'*64,
        tuple(Cue(i,i*100,i*100+90,t) for i,t in enumerate(texts,1)),1,len(texts),(('W00001',1,len(texts)),))

class BoundaryV2Tests(unittest.TestCase):
    def test_known_word_continuations(self):
        for t in ('300 만들기','300만들기','300만큼'):
            old,_=numeric_token_ranges(t);new,w=numeric_token_ranges(t,boundary_policy=True)
            self.assertEqual([t[a:b] for a,b in new],['300']); self.assertEqual(len(w),1)
            self.assertNotEqual(old,new)
    def test_preserves_valid_units(self):
        for t in ('100만 원을','3억이','2천만 원','1억 2천','5.5%만큼','10월에','-3.5%','300만 원 만들기'):
            self.assertEqual(numeric_token_ranges(t),numeric_token_ranges(t,boundary_policy=True),t)
    def test_wrong_magnitude_rejected_bare_not_invented(self):
        s=source('월 300 만들기')
        self.assertEqual(numeric_binding(s,[[1,2,7]])['literal'],'300 만')
        with self.assertRaisesRegex(InvalidInput,'NUMBER_BOUNDARY'):
            numeric_binding(s,[[1,2,7]],boundary_policy=True)
        self.assertEqual(numeric_binding(s,[[1,2,5]],boundary_policy=True)['literal'],'300')
    def test_cross_cue_amount_and_false_magnitude(self):
        s=source('100만','원')
        self.assertEqual(numeric_binding(s,[[1,0,4],[2,0,1]],boundary_policy=True)['literal'],'100만 원')
        s=source('300','만들기')
        with self.assertRaises(InvalidInput):numeric_binding(s,[[1,0,3],[2,0,1]],boundary_policy=True)
        self.assertEqual(numeric_binding(s,[[1,0,3]],boundary_policy=True)['literal'],'300')
    def test_warning_retained_in_graph_even_nonclaim(self):
        s=source('월 300 만들기','투자 의견입니다')
        node=dict(predicate='투자 의견입니다',atomicity_reason='하나의 의견입니다',kind='OPINION',utterance_act='EVALUATION',
          speaker=dict(participant_id='UNKNOWN',status='UNRESOLVED',evidence=[],reason='화자 식별 불명확'),
          attribution='DIRECT',attributed_participant=None,polarity='AFFIRMED',modality='ASSERTED',correction=False,as_of=None,
          direct=[[2,0,len(s.cues[1].text)]],context=[],qualifiers=[],numbers=[],risk='NORMAL',risk_reason='개인 의견에 불과함')
        p=dict(schema=LEGACY_PACKET,grid_sha256=json_digest(source_grid(s)),nodes=[node],
               residual=[dict(span=[1,0,len(s.cues[0].text)],status='NONCLAIM',reason='소제목으로 처리한 표현')])
        g=compile_graph(s,p);self.assertNotIn('numeric_boundary_warnings',g)
        q=copy.deepcopy(p);q['schema']=BOUNDARY_PACKET;h=compile_graph(s,q)
        self.assertEqual(h['census'],g['census']);self.assertEqual(len(h['numeric_boundary_warnings']),1)
        self.assertFalse(h['publication_authorized']);self.assertNotEqual(h['packet_sha256'],g['packet_sha256'])
        with self.assertRaisesRegex(InvalidInput,'NUMERIC_POLICY_MISMATCH'):score_graphs(s,p,q,{})
    def test_no_partial_numeric_coordinates(self):
        for t in ('1, 4, 7, 10월','6.6는 6내는'):
            ranges,_=numeric_token_ranges(t,boundary_policy=True)
            self.assertEqual([t[a:b] for a,b in ranges],['1','4','7','10월'] if t.startswith('1') else ['6.6','6'])
