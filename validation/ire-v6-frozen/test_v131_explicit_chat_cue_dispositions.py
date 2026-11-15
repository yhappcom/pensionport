"""Synthetic cue-level review negative controls; no real owner text in GitHub."""
from __future__ import annotations
import copy
import unittest
from ire.v6.source import verify_source, parse_srt
from ire.v6.codec import sha256, json_digest
from ire.v6.errors import QualityNotProven
from v131_explicit_chat_cue_dispositions import make_source_review_queue,audit_explicit_chat_dispositions

RAW=('1\n00:00:00,000 --> 00:00:01,000\n투자에는 손실 위험이 있습니다.\n\n'
     '2\n00:00:01,000 --> 00:00:02,000\n하지만 손실 후 회복을 보장할 수 없습니다.\n\n'
     '3\n00:00:02,000 --> 00:00:03,000\n질문을 시작하겠습니다.\n\n'
     '4\n00:00:03,000 --> 00:00:04,000\n그리고 장기 투자에도 손실이 날 수 있습니다.\n').encode()

def source():
    cues=parse_srt(RAW)
    plan={'schema':'IRE_V6_SOURCE_PLAN_V1','video_id':'Abcdefghijk',
          'source_sha256':sha256(RAW),'cue_count':4,
          'scope':{'mode':'FULL_VIDEO','first_cue':1,'last_cue':4},
          'windows':[{'window_id':'W00001','first_cue':1,'last_cue':4,
                      'text_sha256':sha256(' '.join(x.text for x in cues).encode())}]}
    return verify_source(RAW,plan,expected_source_sha256=sha256(RAW),expected_manifest_sha256=json_digest(plan))

def packet(s):
    def row(i,role,atomids,risk=True,note='ChatGPT original cue and exception context checked'):
        return {'cue_index':i,'cue_text_sha256':sha256(s.cues[i-1].text.encode()),
                'role':role,'atom_ids':atomids,'rationale':note,
                'risk_checked':risk,'review_state':'REVIEWED'}
    return {'schema':'IRE_V131_CHAT_EXPLICIT_CUE_DISPOSITIONS_V1',
            'source_sha256':s.source_sha256,'manifest_sha256':s.manifest_sha256,
            'reviewer':'CHATGPT_IN_CHAT','cue_rows':[
               row(1,'ASSERTION',['ATOM_0001']),
               row(2,'EXCEPTION',['ATOM_0001']),
               row(3,'QUESTION',[]),
               row(4,'ASSERTION',['ATOM_0002'])],
            'atoms':[{'atom_id':a,'proposition':p,'source_cues':indices,
                      'speech_act':'ASSERTION','context_constraints':[],
                      'chat_private_review_sha256':sha256(a.encode())}
             for a,p,indices in [('ATOM_0001','손실 가능성과 회복 비보장',[1,2]),
                                  ('ATOM_0002','장기 투자에도 손실 발생 가능',[4])]]}

class V131ExplicitCueReviewTests(unittest.TestCase):
    def setUp(self):
        self.src=source()
        self.packet=packet(self.src)
    def test_source_queue_never_auto_fills_reviews(self):
        q=make_source_review_queue(self.src)
        self.assertEqual(q['total_cues'],4)
        self.assertTrue(all(x['review_state']=='REVIEW_REQUIRED' for x in q['items']))
        self.assertFalse(q['v123_final_approved'])
        self.assertFalse(q['p0_go'])
    def test_all_explicit_cue_rows_still_not_v123_approved(self):
        d=audit_explicit_chat_dispositions(self.src,self.packet,required_high_risk_spans=[(1,2)])
        self.assertEqual(d['cue_rows_checked'],4)
        self.assertEqual(d['declared_atoms'],2)
        self.assertEqual(d['status'],'EXPLICIT_CUE_DISPOSITIONS_CHECKED_NOT_V123_APPROVED')
        self.assertFalse(d['knowledge_export_authorized'])
        self.assertFalse(d['independent_recall_verified'])
    def test_missing_one_source_cue_fails(self):
        p=copy.deepcopy(self.packet);p['cue_rows'].pop()
        with self.assertRaisesRegex(QualityNotProven,'CUE_CENSUS_INCOMPLETE'):
            audit_explicit_chat_dispositions(self.src,p)
    def test_shuffled_cue_or_forged_source_sha_fails(self):
        p=copy.deepcopy(self.packet);p['cue_rows'][1]['cue_index']=1
        with self.assertRaisesRegex(QualityNotProven,'CUE_INDEX_SHA'):
            audit_explicit_chat_dispositions(self.src,p)
        p=copy.deepcopy(self.packet);p['cue_rows'][0]['cue_text_sha256']='0'*64
        with self.assertRaisesRegex(QualityNotProven,'CUE_INDEX_SHA'):
            audit_explicit_chat_dispositions(self.src,p)
    def test_context_claim_without_atom_is_blocked(self):
        p=copy.deepcopy(self.packet);p['cue_rows'][1]['atom_ids']=[]
        with self.assertRaisesRegex(QualityNotProven,'SPEECH_ACT_ANCHOR'):
            audit_explicit_chat_dispositions(self.src,p)
    def test_rebuttal_continuation_requires_earlier_parent(self):
        p=copy.deepcopy(self.packet);p['atoms'][0]['source_cues']=[2];p['cue_rows'][0]['atom_ids']=[]
        p['cue_rows'][0]['role']='CONTEXT'
        with self.assertRaisesRegex(QualityNotProven,'CROSS_CUE_CONTEXT_PARENT_NOT_EARLIER'):
            audit_explicit_chat_dispositions(self.src,p)
    def test_high_risk_cue_not_reviewed_blocked(self):
        p=copy.deepcopy(self.packet);p['cue_rows'][1]['risk_checked']=False
        with self.assertRaisesRegex(QualityNotProven,'HIGH_RISK_SOURCE_CUE_NOT_ADJUDICATED'):
            audit_explicit_chat_dispositions(self.src,p)
    def test_explicit_open_prevents_release(self):
        p=copy.deepcopy(self.packet);p['cue_rows'][2]['role']='OPEN';p['cue_rows'][2]['review_state']='OPEN'
        d=audit_explicit_chat_dispositions(self.src,p)
        self.assertEqual(d['status'],'HOLD_OPEN_CUE_DISPOSITIONS')
        self.assertEqual(d['unresolved_open_cues'],1)
    def test_atom_wrong_cue_link_not_accepted(self):
        p=copy.deepcopy(self.packet);p['atoms'][0]['source_cues']=[1]
        with self.assertRaisesRegex(QualityNotProven,'ATOM_PARENT_OR_CONTINUATION_ANCHOR_DRIFT'):
            audit_explicit_chat_dispositions(self.src,p)
    def test_missing_chat_review_packet_never_passes(self):
        with self.assertRaisesRegex(QualityNotProven,'SOURCE_OR_CHAT_REVIEW_SCHEMA'):
            audit_explicit_chat_dispositions(self.src,{})

if __name__=='__main__': unittest.main()
