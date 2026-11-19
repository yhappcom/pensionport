"""V182 synthetic semantic projection guard; not owner-original financial gold."""
import json,sqlite3,tempfile,unittest
from pathlib import Path
from ire.v6.codec import sha256
from v176_chat_engine_loop import EngineChatSession,COMMIT
def source():
    return ('1\n00:00:01,000 --> 00:00:01,900\n'
            'ETF는 상황에 따라 투자 손실이 발생할 수 있습니다.\n\n'
            '2\n00:00:02,000 --> 00:00:02,900\n'
            '여기서 예시는 끝입니다.').encode('utf8')
class TestNativeSemanticProjectionGate(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raw=source()
        self.db=Path(self.tmp.name)/'owner.sqlite'
        self.eng=EngineChatSession(self.db,self.raw,'AbCdEf12345',
            owner_source_sha256=sha256(self.raw),window_size=2,expected_window_count=1)
    def commit(self,with_claim):
        challenge=self.eng.prepare(limit=2,source_first_only=True)
        answers=[]
        for t in challenge['target_cues']:
            claim=[]
            if with_claim and t['cue_index']==1:
                claim=[{'proposition':'ETF 투자 상황에 따라 손실이 발생할 수 있다고 설명한다.',
                        'kind':'FACT','quote':'ETF는 상황에 따라 투자 손실이 발생할 수 있습니다.',
                        'context_cue_indices':[1],
                        'conditions':['손실 가능성이 있는 경우에만'],
                        'exceptions':['원금 보장과 동일하게 취급해서는 안 됨'],
                        'numeric_tokens':[],'high_risk':True,'needs_official_source':True}]
            answers.append({'cue_index':t['cue_index'],'source_text_sha256':t['source_text_sha256'],
                'disposition':'ASSERTION' if claim else 'NON_RESEARCH',
                'speaker_role':'HOST','analysis':'실제 자막을 인용한 미승인 예비 원자이며 금융 사실을 자동 승인하지 않았습니다.',
                'limitations_checked':True,'claims':claim})
        self.assertFalse(self.eng.submit(challenge,{'schema':COMMIT,
            'challenge_sha256':challenge['challenge_sha256'],
            'review_executor':'CHATGPT_IN_CHAT','responses':answers})['e4_approved'])
    def test_conditional_text_not_silently_dropped(self):
        self.commit(True)
        exchange,summary=self.eng.compile_native_v6_stage()
        self.assertEqual(exchange['atoms'][0]['condition_cue_indices'],[])
        self.assertEqual(exchange['atoms'][0]['exception_cue_indices'],[])
        gate=summary['semantic_projection_gate']
        self.assertEqual((gate['staged_atoms'],gate['unprojected_claims'],
            gate['unprojected_condition_terms'],gate['unprojected_exception_terms']),(1,1,1,1))
        self.assertEqual(gate['unresolved_stance_atoms'],1)
        self.assertEqual(gate['unknown_speaker_atoms'],1)
        self.assertFalse(gate['v123_e4_approval_permitted'])
        self.assertFalse(gate['full_semantic_projection_verified'])
        with sqlite3.connect(self.db) as db:
            old=json.loads(db.execute('SELECT record FROM cue_reviews WHERE cue_index=1').fetchone()[0])
        self.assertEqual(len(old['claims'][0]['conditions']),1)
        self.assertEqual(len(old['claims'][0]['exceptions']),1)
        self.assertNotIn('원금 보장',json.dumps(gate,ensure_ascii=False))
    def test_reopen_reproduces_same_loss_gate(self):
        self.commit(True)
        old=self.eng.progress()['checkpoint_head_sha256']
        reopened=EngineChatSession(self.db,self.raw,'AbCdEf12345',
            owner_source_sha256=sha256(self.raw),window_size=2,expected_window_count=1)
        self.assertEqual(reopened.progress()['checkpoint_head_sha256'],old)
        self.assertEqual(reopened.compile_native_v6_stage()[1]['semantic_projection_gate']['unprojected_claims'],1)
    def test_no_claim_still_not_e4_approved(self):
        self.commit(False)
        _,stage=self.eng.compile_native_v6_stage()
        self.assertEqual(stage['semantic_projection_gate']['staged_atoms'],0)
        self.assertFalse(stage['semantic_projection_gate']['v123_e4_approval_permitted'])
        self.assertFalse(stage['final_approval'])
if __name__=='__main__':unittest.main()
