"""V187 synthetic E3 scope inheritance attacks; NOT investment gold."""
import copy
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import EngineChatSession, COMMIT, _digest
from v186_e3_qualifier_provenance import E3QualifierProvenance,ANSWER_SCHEMA
from v187_e3_parent_scope_bridge import E3ParentScopeBridge, ANSWER


def fixture():
    cues=['가상의 ETF 예시 화면을 보겠습니다.',
          '이 ETF는 같은 화면의 제품입니다.',
          'NAV는 10,000원입니다.']
    return '\n\n'.join(f'{i}\n00:00:0{i},000 --> 00:00:0{i},800\n{t}'
                      for i,t in enumerate(cues,1)).encode('utf8')


class TestSourceScopeContinuity(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raw=fixture()
        self.owner_db=Path(self.tmp.name)/'owner.sqlite'
        self.qualifier_db=Path(self.tmp.name)/'qual.sqlite'
        self.scope_db=Path(self.tmp.name)/'scope.sqlite'
        self.engine=EngineChatSession(self.owner_db,self.raw,'AbCdEf12345',
            owner_source_sha256=sha256(self.raw),window_size=3,expected_window_count=1)
        pkt=self.engine.prepare(source_first_only=True,limit=3)
        responses=[]
        for t in pkt['target_cues']:
            cue=t['cue_index'];claims=[]
            if cue==3:
                claims=[{'proposition':'가상 ETF의 NAV가 10,000원이라고 설명한다.',
                    'kind':'FACT','quote':'NAV는 10,000원입니다.',
                    'context_cue_indices':[3],
                    'conditions':['앞서 소개된 가상 예시 ETF 화면을 전제로'],
                    'exceptions':['실제 상장 ETF의 현재 공시 NAV가 아님'],
                    'numeric_tokens':['10,000'],'high_risk':True,
                    'needs_official_source':True}]
            responses.append({'cue_index':cue,'source_text_sha256':t['source_text_sha256'],
                'disposition':'ASSERTION' if claims else 'NON_RESEARCH',
                'speaker_role':'HOST',
                'analysis':'이 자막의 실제 예시와 출처를 분리하고 실물 사실로는 승인하지 않습니다.',
                'limitations_checked':True,'claims':claims})
        self.engine.submit(pkt,{'schema':COMMIT,'challenge_sha256':pkt['challenge_sha256'],
            'review_executor':'CHATGPT_IN_CHAT','responses':responses})
        self.owner_head=self.engine.progress()['checkpoint_head_sha256']
        self.qual=E3QualifierProvenance(self.engine,self.qualifier_db,
            expected_owner_head=self.owner_head,create=True)
        qpkt=self.qual.prepare(limit=2)
        answers=[]
        for t in qpkt['targets']:
            conditions=t['field']=='conditions'
            answers.append({'term_id':t['term_id'],'term_sha256':t['term_sha256'],
              'origin':'UNRESOLVED' if conditions else 'REVIEWER_ADDED',
              'source_quote':None,'source_cue_indices':[],
              'semantic_rationale':('원문 세 번째 자막에는 가격만 있고 첫 번째 자막의 가상 ETF 예시 전제를 원자의 국소 문맥으로 연결하지 않아 출처를 보류합니다.'
                                    if conditions else
                                    '실제 상장 상품의 공시가 아니라는 금지문은 세 번째 자막에 직접 발화되지 않았으므로 검토자의 주의사항에 해당합니다.'),
              'e3_certified':False,'v123_approved':False,
              'e4_approved':False,'e5_published':False})
        self.qual.submit(qpkt,{'schema':ANSWER_SCHEMA,
            'challenge_sha256':qpkt['challenge_sha256'],
            'review_executor':'CHATGPT_IN_CHAT','responses':answers})
        self.qual_head=self.qual.status()['journal_head_sha256']
        self.bridge=E3ParentScopeBridge(self.engine,self.qual,self.scope_db,
            expected_owner_head=self.owner_head,
            expected_qualifier_head=self.qual_head,create=True)
        self.term_id='0003:01:conditions:01'

    def packet(self):
        return self.bridge.prepare(term_ids=[self.term_id],
            parent_cue_index=1,bridging_cue_index=2)

    def answer(self,pkt):
        return {'schema':ANSWER,'challenge_sha256':pkt['challenge_sha256'],
          'review_executor':'CHATGPT_IN_CHAT','responses':[
            {'term_id':self.term_id,
             'term_sha256':self.qual.terms[self.term_id]['term_sha256'],
             'scope_type':'HYPOTHETICAL_EXAMPLE',
             'parent_cue_index':1,
             'parent_source_quote':'가상의 ETF 예시 화면을 보겠습니다.',
             'bridging_cue_index':2,
             'bridging_source_quote':'이 ETF는 같은 화면의 제품입니다.',
             'target_claim_quote':'NAV는 10,000원입니다.',
             'semantic_scope_rationale':(
                 '첫째 자막의 가상 ETF라는 선언 뒤 둘째 자막의 이 ETF는 이라는 지시어로 '
                 '같은 화면 대상을 계속 가리키며, 셋째 자막 NAV 10,000원은 그 예시의 값이다. '
                 '실물 시장가격으로 사용하지 않고 상위 가상 전제를 소스 자막에 고정한다.'),
             'source_scope_provisional':True,'e3_certified':False,
             'v123_approved':False,'e4_approved':False,'e5_published':False}]}

    def test_a_original_context_missing_and_provisional_scope_repairs_stage(self):
        prior,stage0=self.engine.compile_native_v6_stage(qualifier_provenance=self.qual)
        self.assertEqual(prior['atoms'][0]['context_cue_indices'],[3])
        self.assertEqual(prior['atoms'][0]['condition_cue_indices'],[])
        pkt=self.packet()
        self.bridge.submit(pkt,self.answer(pkt))
        after,summary=self.engine.compile_native_v6_stage(
            qualifier_provenance=self.qual,cross_cue_scope_bridge=self.bridge)
        self.assertEqual(after['atoms'][0]['context_cue_indices'],[1,3])
        self.assertEqual(after['atoms'][0]['condition_cue_indices'],[1])
        self.assertEqual(after['atoms'][0]['exception_cue_indices'],[])
        self.assertEqual(summary['semantic_projection_gate']['v187_source_parent_scope_bridge'][
          'inherited_source_explicit_condition_terms'],1)
        self.assertFalse(summary['semantic_projection_gate']['v123_e4_approval_permitted'])
        self.assertFalse(summary['final_approval'])
        self.assertEqual(self.engine.progress()['checkpoint_head_sha256'],self.owner_head)

    def test_b_forged_source_quote_rejected(self):
        pkt=self.packet();ans=self.answer(pkt)
        ans['responses'][0]['parent_source_quote']='가상의 코스피 20% 수익률'
        with self.assertRaisesRegex(InvalidInput,'SOURCE_SCOPE_NOT_PROVEN'):
            self.bridge.submit(pkt,ans)
        self.assertEqual(self.bridge.status()['linked_term_count'],0)

    def test_c_wrong_bridge_quote_rejected(self):
        pkt=self.packet();ans=self.answer(pkt)
        ans['responses'][0]['bridging_source_quote']='ETF 가격은 확정'
        with self.assertRaisesRegex(InvalidInput,'SOURCE_SCOPE_NOT_PROVEN'):
            self.bridge.submit(pkt,ans)

    def test_d_replay_duplicate_rejected_and_immutable(self):
        pkt=self.packet();ans=self.answer(pkt)
        result=self.bridge.submit(pkt,ans)
        with self.assertRaises(InvalidInput):self.bridge.submit(pkt,ans)
        reopened=E3ParentScopeBridge(self.engine,self.qual,self.scope_db,
            expected_owner_head=self.owner_head,expected_qualifier_head=self.qual_head)
        self.assertEqual(reopened.status()['journal_head_sha256'],result['head_sha256'])

    def test_e_wrong_scope_target_rejected(self):
        with self.assertRaises(InvalidInput):
            self.bridge.prepare(term_ids=['0003:01:exceptions:01'],
                parent_cue_index=1,bridging_cue_index=2)

    def test_f_self_hash_forged_packet_rejected(self):
        pkt=self.packet();pkt['parent_original_text']='가짜 원본 자막'
        pkt['challenge_sha256']=_digest({k:v for k,v in pkt.items() if k!='challenge_sha256'})
        with self.assertRaisesRegex(InvalidInput,'PACKET_NOT_ENGINE_ISSUED'):
            self.bridge.submit(pkt,self.answer(pkt))

    def test_g_parent_not_before_child_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'PACKET_SCOPE_POSITION'):
            self.bridge.prepare(term_ids=[self.term_id],
                parent_cue_index=3,bridging_cue_index=2)

    def test_h_forbid_approval_forgery(self):
        pkt=self.packet();ans=self.answer(pkt)
        ans['responses'][0]['e4_approved']=True
        with self.assertRaisesRegex(InvalidInput,'RESPONSE_SCHEMA_OR_APPROVAL'):
            self.bridge.submit(pkt,ans)

    def test_i_journal_row_tamper_detected(self):
        pkt=self.packet();self.bridge.submit(pkt,self.answer(pkt))
        with sqlite3.connect(self.scope_db) as db:
            db.execute("UPDATE accepted_links SET record='{}' WHERE term_id=?",(self.term_id,))
        with self.assertRaises(InvalidInput):self.bridge.status()

    def test_j_scope_db_private_guard(self):
        pkt=self.packet();self.bridge.submit(pkt,self.answer(pkt))
        os.chmod(self.scope_db,0o644)
        with self.assertRaisesRegex(InvalidInput,'EXISTING_SCOPE_JOURNAL_MUST_RESUME_PRIVATELY'):
            E3ParentScopeBridge(self.engine,self.qual,self.scope_db,
                expected_owner_head=self.owner_head,expected_qualifier_head=self.qual_head)

    def test_k_no_qualifier_provenance_fails_closed(self):
        pkt=self.packet();self.bridge.submit(pkt,self.answer(pkt))
        with self.assertRaisesRegex(InvalidInput,'CROSS_CUE_SCOPE_BRIDGE_NOT_PINNED'):
            self.engine.compile_native_v6_stage(cross_cue_scope_bridge=self.bridge)

    def test_l_wrong_qualifier_head_pin_rejected(self):
        with self.assertRaises(InvalidInput):
            E3ParentScopeBridge(self.engine,self.qual,self.scope_db,
                expected_owner_head=self.owner_head,expected_qualifier_head='f'*64)

if __name__=='__main__':unittest.main()