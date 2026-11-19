"""Synthetic E3 disagreement adjudication security regressions; NOT independent gold."""
import copy, json, os, sqlite3, tempfile, unittest
from pathlib import Path
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import EngineChatSession, COMMIT, _digest
from v183_e3_two_turn_audit import E3TwoTurnAudit,ANSWER_SCHEMA as SECOND_ANSWER
from v184_e3_adjudication import E3Adjudication,ANSWER_SCHEMA as ADJ_ANSWER


def source():
    return ('1\n00:00:01,000 --> 00:00:01,600\nETF는 장점이 있습니다.\n\n'
            '2\n00:00:02,000 --> 00:00:02,600\n하지만 조건에 따라 손실이 있을 수 있습니다.\n\n'
            '3\n00:00:03,000 --> 00:00:03,600\n감사합니다.\n\n'
            '4\n00:00:04,000 --> 00:00:04,600\n끝입니다.').encode()


class TestAdjudication(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.raw=source()
        self.owner=root/'owner.sqlite'
        self.second=root/'second.sqlite'
        self.adj=root/'adjudication.sqlite'
        self.eng=EngineChatSession(self.owner,self.raw,'AbCdEf12345',
           owner_source_sha256=sha256(self.raw),window_size=4,expected_window_count=1)
        q=self.eng.prepare(limit=4,source_first_only=True)
        answer=[]
        for cue in q['target_cues']:
            answer.append({'cue_index':cue['cue_index'],'source_text_sha256':cue['source_text_sha256'],
              'disposition':'NON_RESEARCH' if cue['cue_index']!=1 else 'ASSERTION',
              'analysis':'이 발화는 앞뒤 연결이 있으므로 단독 주장 여부를 별도로 검증해야 합니다.',
              'speaker_role':'HOST','limitations_checked':True,
              'claims':([{'proposition':'ETF는 장점이 있다고 발언한다.','kind':'OPINION',
                     'quote':'ETF는 장점이 있습니다.','context_cue_indices':[1],
                     'conditions':[],'exceptions':[],'numeric_tokens':[],
                     'high_risk':False,'needs_official_source':False}]
                       if cue['cue_index']==1 else [])})
        self.eng.submit(q,{'schema':COMMIT,'challenge_sha256':q['challenge_sha256'],
                           'review_executor':'CHATGPT_IN_CHAT','responses':answer})
        self.head=self.eng.progress()['checkpoint_head_sha256']
        self.audit=E3TwoTurnAudit(self.eng,self.second,expected_owner_head=self.head,create=True)
        q=self.audit.prepare(limit=3)
        x=[]
        for c in q['target_cues']:
            disp='OPEN' if c['cue_index']==2 else 'NON_RESEARCH'
            x.append({'cue_index':c['cue_index'],'source_text_sha256':c['source_text_sha256'],
                      'disposition':disp,'speaker_role':'HOST','claims':[],
                      'analysis':'원문만으로 독립적 투자 사실이 되는지 추가 확인하고 보수적으로 처리합니다.',
                      'limitations_checked':True})
        self.audit.submit(q,{'schema':SECOND_ANSWER,'challenge_sha256':q['challenge_sha256'],
                             'review_executor':'CHATGPT_IN_CHAT','responses':x})
        self.reviewer=E3Adjudication(self.audit,self.adj,create=True)

    def response(self,p,category='CONFIRMED_SECOND_PASS_OMISSION',wrong=False):
        answers=[]
        for i in p['cue_indices']:
            txt=self.eng.source.cues[i-1].text
            cat=category if i==1 else 'UNRESOLVED_NEEDS_REVIEW'
            act='REVIEW_SECOND_PASS' if cat=='CONFIRMED_SECOND_PASS_OMISSION' else 'KEEP_OPEN_WITH_EVIDENCE_TASK'
            answers.append({'cue_index':i,'source_text_sha256':sha256(txt.encode()),
                            'source_quote':'없는 원문입니다' if wrong else txt,
                            'related_cue_indices':[i],
                            'category':cat,'qualifier_origin':'UNVERIFIED',
                            'semantic_rationale':'원문과 두 차례 검토의 범위를 분리해 살펴보았으나 E3 독립 정답으로 승인하지 않고 재검토 대상으로 관리합니다.',
                            'next_action':act,'independent_gold_certified':False,
                            'v123_e4_approved':False,'e5_authorized':False})
        return {'schema':ADJ_ANSWER,'challenge_sha256':p['challenge_sha256'],
                'review_executor':'CHATGPT_IN_CHAT','answers':answers}

    def test_packet_has_first_and_second_with_original_context(self):
        p=self.reviewer.prepare(limit=2)
        self.assertEqual(p['cue_indices'],[1,2])
        self.assertEqual(p['pair'][0]['first_pass']['disposition'],'ASSERTION')
        self.assertEqual(p['pair'][0]['second_pass']['disposition'],'NON_RESEARCH')
        self.assertTrue(p['blind_review_already_completed'])
        self.assertFalse(p['quality_certified'])

    def test_append_only_reopen_and_status(self):
        p=self.reviewer.prepare(limit=2)
        result=self.reviewer.submit(p,self.response(p))
        self.assertFalse(result['e3_quality_certified'])
        other=E3Adjudication(self.audit,self.adj,create=False)
        status=other.status()
        self.assertEqual(status['adjudicated_cues'],2)
        self.assertEqual(status['adjudication_events'],1)
        self.assertEqual(status['pending_adjudication_cues'],[])
        self.assertFalse(status['independent_gold_certified'])
        self.assertEqual(self.eng.progress()['checkpoint_head_sha256'],self.head)

    def test_forged_packet_self_hash_rejected(self):
        p=self.reviewer.prepare(limit=1)
        forged=copy.deepcopy(p)
        forged['surrounding_source'][0]['text']='절대 안전합니다'
        forged['challenge_sha256']=_digest({k:v for k,v in forged.items() if k!='challenge_sha256'})
        with self.assertRaisesRegex(InvalidInput,'STALE_OR_FORGED_PACKET'):
            self.reviewer.submit(forged,self.response(forged))
        self.assertEqual(self.reviewer.status()['adjudicated_cues'],0)

    def test_quote_forgery_rejected(self):
        p=self.reviewer.prepare(limit=1)
        with self.assertRaisesRegex(InvalidInput,'SOURCE_OR_SEMANTIC_GUARD'):
            self.reviewer.submit(p,self.response(p,wrong=True))
        self.assertEqual(self.reviewer.status()['adjudicated_cues'],0)

    def test_duplicate_packet_rejected(self):
        p=self.reviewer.prepare(limit=1)
        self.reviewer.submit(p,self.response(p))
        with self.assertRaisesRegex(InvalidInput,'SELECTION_INVALID|STALE_OR_FORGED_PACKET'):
            self.reviewer.submit(p,self.response(p))

    def test_stored_judgment_tamper_detected(self):
        p=self.reviewer.prepare(limit=1)
        self.reviewer.submit(p,self.response(p))
        with sqlite3.connect(self.adj) as db:
            db.execute("UPDATE judgments SET record='{}'")
        with self.assertRaisesRegex(InvalidInput,'ADJUDICATION_RECORD_TAMPER'):
            self.reviewer.status()

    def test_adjudication_is_not_separate_independent_gold(self):
        p=self.reviewer.prepare(limit=1)
        ans=self.response(p)
        ans['answers'][0]['independent_gold_certified']=True
        with self.assertRaisesRegex(InvalidInput,'SOURCE_OR_SEMANTIC_GUARD'):
            self.reviewer.submit(p,ans)
        self.assertEqual(self.reviewer.status()['adjudicated_cues'],0)

    def test_private_db_permissions(self):
        os.chmod(self.adj,0o644)
        with self.assertRaisesRegex(InvalidInput,'PRIVATE_DB_PERMISSIONS'):
            E3Adjudication(self.audit,self.adj,create=False)

    def test_second_pass_appending_does_not_invalidate_original_adjudication(self):
        p=self.reviewer.prepare(limit=1)
        self.reviewer.submit(p,self.response(p))
        # Adjudication depends on source pairs for the reviewed cues, not the
        # entire second-stage head, allowing safe continuation of full census.
        self.assertEqual(self.reviewer.status()['adjudicated_cues'],1)
        self.assertEqual(self.reviewer.status()['pending_adjudication_cues'],[2])
        prior_head=self.audit.status()['second_review_audit_head_sha256']
        q=self.audit.prepare(limit=1)
        self.assertEqual(q['cue_indices'],[4])
        answer={'schema':SECOND_ANSWER,'challenge_sha256':q['challenge_sha256'],
                'review_executor':'CHATGPT_IN_CHAT','responses':[
                    {'cue_index':4,'source_text_sha256':q['target_cues'][0]['source_text_sha256'],
                     'disposition':'NON_RESEARCH','speaker_role':'HOST','claims':[],
                     'analysis':'마지막 인사 말이므로 별도의 금융 사실로 분석하지 않습니다.',
                     'limitations_checked':True}]}
        self.audit.submit(q,answer)
        self.assertNotEqual(self.audit.status()['second_review_audit_head_sha256'],prior_head)
        self.assertEqual(self.reviewer.status()['adjudicated_cues'],1)
        self.assertEqual(self.reviewer.status()['pending_adjudication_cues'],[2])


if __name__=='__main__':unittest.main()