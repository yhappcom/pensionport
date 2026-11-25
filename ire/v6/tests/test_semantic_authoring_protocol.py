"""Prospective shared authoring contract; synthetic, not semantic certification."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from ire.v6.codec import json_digest
from ire.v6.errors import InvalidInput
from ire.v6.gold_eval import MATCH_FIELDS
from ire.v6.semantic_authoring_protocol import PROTOCOL_SHA256, compile_authoring, occurrence_inventory
from ire.v6.semantic_graph_journal import GraphJournal, plan_for
from ire.v6.semantic_source_graph import source_grid, score_graphs
from ire.v6.tests.test_numeric_boundary_v2 import source


def full(s,i):return [i,0,len(s.cues[i-1].text)]

def packet(s,role='CONTRIBUTION_BASE',unit='원',parts=None,anchor=None):
    spans=[full(s,i) for i in range(1,len(s.cues)+1)]
    inventory=occurrence_inventory(s)
    p=inventory if parts is None else parts
    return dict(protocol_sha256=PROTOCOL_SHA256,grid_sha256=json_digest(source_grid(s)),
        segments=[dict(span=x,status='DIRECT',reason='Synthetic direct evidence.') for x in spans],
        atoms=[dict(node=dict(predicate='하나의 합성 원문 명제를 검토한다.',atomicity_reason='Synthetic one predicate.',
            utterance_act='ASSERTION',speaker=dict(participant_id='S00001',status='TEXT_INFERRED',evidence=[spans[0]],reason='Synthetic participant only.'),
            attribution='DIRECT',attributed_participant=None,polarity='AFFIRMED',correction=False,direct=spans,context=[],risk='HIGH',risk_reason='Synthetic high-risk scope.'),
            content_type='FACT',scenario='ACTUAL',certainty='ASSERTED',temporal=[],relations=[],
            quantities=[dict(parts=p,role=role,unit=unit,anchor=p if anchor is None else anchor,reason='Synthetic role assignment.')])],
        occurrences=[dict(span=x,disposition='IDENTIFIER' if role=='IDENTIFIER' else 'QUANTITY',owners=['A00001'],reason='Synthetic explicit occurrence.') for x in inventory])


def alignment(r1,r2,**axes):
    d=dict.fromkeys(MATCH_FIELDS,True);d.update(axes)
    return dict(first_packet_sha256=r1['graph_sha256'],second_packet_sha256=r2['graph_sha256'],
        speaker_aliases=[dict(first='S00001',second='S00001',reason='Synthetic alias only.',evidence=[[1,0,1]])],
        pairs=[dict(prediction_id='A00001',reference_id='A00001',axes=d,reasons=dict.fromkeys(MATCH_FIELDS,'Synthetic structural judgment.'))],
        unmatched_prediction_ids=[],unmatched_reference_ids=[],unmatched_reasons={})


class SharedAuthoringProtocolTests(unittest.TestCase):
    def setUp(self):
        self.s=source('매월 100만 원을 납입한다.')
        self.a=packet(self.s)

    def test_explicit_role_and_inventory(self):
        p,r=compile_authoring(self.s,self.a)
        self.assertEqual(p['nodes'][0]['numbers'][0]['function'],'AMOUNT')
        self.assertEqual(r['open_numeric_occurrences'],0)
        self.assertEqual(r['unbound_numeric_spans'],0)
        self.assertFalse(r['semantic_truth_certified'])
        for field in ('segments','occurrences'):
            b=copy.deepcopy(self.a);b[field].pop()
            with self.subTest(field=field),self.assertRaises(InvalidInput):compile_authoring(self.s,b)

    def test_quantity_unit_and_identifier(self):
        s=source('65세에 지급한다. 다른 금액은 원으로 표기한다.')
        age=packet(s,'AGE','세',anchor=[[1,0,3]])
        p,_=compile_authoring(s,age);self.assertEqual(p['nodes'][0]['numbers'][0]['function'],'OTHER')
        b=copy.deepcopy(age);b['atoms'][0]['quantities'][0].update(role='AMOUNT',unit='원',anchor=[full(s,1)])
        with self.assertRaisesRegex(InvalidInput,'UNIT_NOT_VERBATIM'):compile_authoring(s,b)
        b=copy.deepcopy(age);b['atoms'][0]['quantities'][0].update(role='IDENTIFIER',unit='');b['occurrences'][0]['disposition']='IDENTIFIER'
        with self.assertRaisesRegex(InvalidInput,'IDENTIFIER_CONTEXT'):compile_authoring(s,b)
        s=source('제도 401K를 설명한다.')
        a=packet(s,'IDENTIFIER','',anchor=[[1,3,7]])
        _,r=compile_authoring(s,a);self.assertEqual(r['unbound_numeric_spans'],0)

    def test_cross_cue_unit_and_shared_list(self):
        s=source('100만','원 납입한다.')
        a=packet(s,parts=[[1,0,4],[2,0,1]])
        p,r=compile_authoring(s,a);self.assertEqual(r['numeric_occurrences'],1);self.assertEqual(r['unbound_numeric_spans'],0)
        self.assertEqual(p['nodes'][0]['numbers'][0]['parts'],[[1,0,4],[2,0,1]])
        s=source('1, 4, 7, 10월에 지급한다.')
        a=packet(s,'PAYMENT_MONTH','월');a['atoms'][0]['quantities']=[dict(parts=[x],role='PAYMENT_MONTH',unit='월',anchor=[[1,0,12]],reason='Synthetic shared list suffix.') for x in occurrence_inventory(s)]
        _,r=compile_authoring(s,a);self.assertEqual(r['numeric_occurrences'],4);self.assertEqual(r['open_numeric_occurrences'],0)

    def test_multi_fragment_condition(self):
        s=source('원금이 있다면','수익률을 비교하고','조건에 맞는 선택을 한다.')
        a=packet(s);a['atoms'][0]['quantities']=[];a['atoms'][0]['node']['direct']=[full(s,3)]
        a['segments'][0]['status']=a['segments'][1]['status']='SUPPORT'
        a['atoms'][0]['relations']=[dict(type='CONDITION',premise=[full(s,1),full(s,2)],consequent=[full(s,3)],reason='Synthetic one grouped condition.')]
        p,r=compile_authoring(s,a);self.assertEqual(len(p['nodes'][0]['qualifiers']),2)
        b=copy.deepcopy(a);b['atoms'][0]['relations'][0]['consequent']=[full(s,2)]
        with self.assertRaisesRegex(InvalidInput,'CONSEQUENT_OWNER'):compile_authoring(s,b)

    def test_directive_and_speculation_fields(self):
        a=copy.deepcopy(self.a);a['atoms'][0]['certainty']='SPECULATIVE'
        with self.assertRaisesRegex(InvalidInput,'SPECULATION_NOT_FACT'):compile_authoring(self.s,a)
        a['atoms'][0]['content_type']='OPINION';p,_=compile_authoring(self.s,a);self.assertEqual(p['nodes'][0]['kind'],'OPINION');self.assertEqual(p['nodes'][0]['modality'],'UNRESOLVED')
        a['atoms'][0]['node']['utterance_act']='QUESTION'
        with self.assertRaisesRegex(InvalidInput,'DIRECTIVE_FIELDS'):compile_authoring(self.s,a)
        a['atoms'][0].update(content_type='NOT_APPLICABLE',certainty='NOT_APPLICABLE');p,_=compile_authoring(self.s,a);self.assertEqual(p['nodes'][0]['kind'],'QUESTION')

    def journal_case(self,role,open_occurrence=False):
        with tempfile.TemporaryDirectory() as d,patch('ire.v6.semantic_graph_journal.verify_source',return_value=self.s):
            file=Path(d)/'j.sqlite';pins=dict(source_sha=self.s.source_sha256,manifest_sha=self.s.manifest_sha256)
            j=GraphJournal(file,b'',{},create=True,**pins)
            plan=plan_for(self.s,campaign_id='synthetic-authoring',engine_commit='a'*40,registered_at='2026-11-25T08:00:00+09:00',purpose='DEVELOPMENT',protocol_sha256=PROTOCOL_SHA256)
            j.append('REGISTER',plan)
            p1,r1=compile_authoring(self.s,self.a)
            with self.assertRaisesRegex(InvalidInput,'V3_LINEAGE_TURN'):j.append('FIRST',dict(user_ref='synthetic first',observed_at='2026-11-25T08:01:00+09:00',packet=p1))
            bad=copy.deepcopy(r1);bad['publication_authorized']=True
            with self.assertRaisesRegex(InvalidInput,'AUTHORING_RECEIPT_DRIFT'):j.append('FIRST',dict(user_ref='synthetic first',observed_at='2026-11-25T08:01:00+09:00',authored=self.a,receipt=bad))
            j.append('FIRST',dict(user_ref='synthetic first',observed_at='2026-11-25T08:01:00+09:00',authored=self.a,receipt=r1))
            b=copy.deepcopy(self.a);b['atoms'][0]['quantities'][0]['role']=role;b['atoms'][0]['node']['risk_reason']='Synthetic second risk explanation.'
            if open_occurrence:b['occurrences'][0]['disposition']='OPEN'
            p2,r2=compile_authoring(self.s,b)
            v=dict(user_ref='synthetic second',observed_at='2026-11-25T08:02:00+09:00',authored=b,receipt=r2)
            with self.assertRaisesRegex(InvalidInput,'SAME_USER_REF'):j.append('SECOND',{**v,'user_ref':'synthetic first'})
            j.append('SECOND',v)
            a=alignment(r1,r2);sc=score_graphs(self.s,p1,p2,a);self.assertTrue(sc['thresholds_met_on_supplied_internal_graphs'])
            if role!='CONTRIBUTION_BASE':
                with self.assertRaisesRegex(InvalidInput,'CONTRADICTORY_MATCH_NUMERIC_ROLE_UNIT'):j.append('SCORE',dict(alignment=a,result=sc))
                a=alignment(r1,r2,numeric_value_and_unit=False);sc=score_graphs(self.s,p1,p2,a)
            h=j.append('SCORE',dict(alignment=a,result=sc));snap=j.snapshot()
            self.assertEqual(snap,GraphJournal(file,b'',{},expected_head=h,**pins).snapshot());self.assertEqual(snap['event_count'],4)
            self.assertFalse(snap['authoring']['authoring_comparison']['protocol_thresholds_met'])
            with self.assertRaisesRegex(InvalidInput,'AUTHORING_DIAGNOSTIC_ONLY'):j.append('DISPUTES',[])
            self.assertEqual(snap,j.snapshot());self.assertFalse(snap['publication_authorized'])

    def test_typed_role_mismatch_blocks_score(self):self.journal_case('TAX_AMOUNT')
    def test_open_occurrence_blocks_protocol_threshold(self):self.journal_case('CONTRIBUTION_BASE',True)
