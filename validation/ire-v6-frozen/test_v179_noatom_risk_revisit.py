"""Synthetic V179 original-V176 regression: risky NO_ATOM -> real chat revision.

The Python engine never calls ChatGPT. The tests use explicitly provided
synthetic reviewer responses to exercise only transport, fail-closed and native
V6 structural checks. Original owner SRT is never uploaded to GitHub.
"""
from __future__ import annotations
import copy, hashlib, sqlite3, tempfile, unittest
from pathlib import Path
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import EngineChatSession, COMMIT, REVISION, _digest


def raw_srt():
    t=['안녕하세요.',
       'ETF는 주식시장에 상장되어 거래됩니다.',
       '거래량이 낮은 ETF는 유동성이 부족할 수 있습니다.',
       '여기까지 설명하겠습니다.']
    return '\n\n'.join(f'{j}\n00:00:{j:02d},000 --> 00:00:{j:02d},500\n{x}'
                     for j,x in enumerate(t,1)).encode('utf-8')


def first_answer(q):
    rows=[]
    for t in q['target_cues']:
        idx=t['cue_index']
        claim=[]
        if idx==3:
            claim=[{'proposition':'화자는 거래량이 낮은 ETF는 유동성이 부족할 수 있다고 진술한다.',
                    'kind':'HYPOTHETICAL','quote':'거래량이 낮은 ETF는 유동성이',
                    'context_cue_indices':[2,3],
                    'conditions':['거래량이 낮은 경우'],
                    'exceptions':['거래량만으로 호가 깊이와 LP 유동성을 확정하지 않는다.'],
                    'numeric_tokens':[],'high_risk':True,
                    'needs_official_source':True}]
        rows.append({'cue_index':idx,'source_text_sha256':t['source_text_sha256'],
                     'disposition':'ASSERTION' if idx==3 else 'NON_RESEARCH',
                     'speaker_role':'HOST','claims':claim,'limitations_checked':True,
                     'analysis':'원문 인접 발화를 비교했으나 별도 금융 사실 승인은 수행하지 않았습니다.'})
    return {'schema':COMMIT,'challenge_sha256':q['challenge_sha256'],
            'review_executor':'CHATGPT_IN_CHAT','responses':rows}


def risk_answer(q, *, disposition='ASSERTION', forged=False):
    t=q['target_cues'][0]
    new_claim={'proposition':'화자는 ETF가 주식시장에 상장되어 거래된다고 진술한다.',
               'kind':'FACT','quote':'ETF는 주식시장에 상장되어 거래됩니다.',
               'context_cue_indices':[2,3],
               'conditions':['거래소 영업일에 해당 ETF 거래가 가능한 경우'],
               'exceptions':['ETF 기초자산이 반드시 주식인 것은 아니다.'],
               'numeric_tokens':[],'high_risk':True,'needs_official_source':True}
    row={'cue_index':t['cue_index'],'source_text_sha256':t['source_text_sha256'],
         'disposition':disposition,'speaker_role':'HOST',
         'analysis':'원문과 후속 문맥을 다시 검토했으며 별개 금융시장 구조 주장을 확인했지만 승인하지 않았습니다.',
         'claims':[new_claim] if disposition=='ASSERTION' else [],
         'limitations_checked':True,
         'prior_review_event_sha256':t['prior_review_event_sha256'],
         'new_context_cue_indices':[1,2,3],
         'change_reason':'앞선 NON_RESEARCH 발화에는 기초시장 구조에 관한 독립적인 추가 주장이 있으므로 원문을 인용해 분리합니다.'}
    if forged:row['claims'][0]['quote']='SOURCE NOT FOUND'
    return {'schema':REVISION,'challenge_sha256':q['challenge_sha256'],
            'review_executor':'CHATGPT_IN_CHAT','responses':[row]}


class SourceRiskRevisit(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        self.db=Path(t.name)/'private.sqlite';self.raw=raw_srt()
        self.engine=EngineChatSession(self.db,self.raw,'AbCdEf12345',
                 owner_source_sha256=sha256(self.raw),window_size=3,expected_window_count=2)
        while self.engine.progress()['cue_remaining']:
            q=self.engine.prepare(limit=3,context_radius=4,source_first_only=True)
            self.engine.submit(q,first_answer(q))
    def challenge(self):return self.engine.prepare_nonresearch_risk_revisit(2,context_radius=4)

    def test_01_real_recheck_explicit_response_and_frozen_native_v6(self):
        first=self.engine.compile_native_v6_stage()[1]['native_v6_audit']
        self.assertEqual(first['proposed_atomic_claims'],1)
        result=self.engine.submit_context_revisit(self.challenge(),risk_answer(self.challenge()))
        self.assertEqual(result['status'],'CHAT_CONTEXT_REVISIT_COMMITTED_UNRELEASED')
        native=self.engine.compile_native_v6_stage()[1]['native_v6_audit']
        self.assertEqual(native['proposed_atomic_claims'],2)
        self.assertTrue(native['all_numeric_cue_tokens_reconciled'])
        self.assertFalse(native['research_complete'])
        self.assertFalse(result['e4_approved'])
        with sqlite3.connect(self.db) as con:
            old=con.execute('SELECT disposition FROM cue_reviews WHERE cue_index=2').fetchone()[0]
            self.assertEqual(old,'NON_RESEARCH')
            self.assertEqual(con.execute('SELECT COUNT(*) FROM cue_revisions').fetchone()[0],1)

    def test_02_unflagged_greeting_cannot_be_revisited(self):
        with self.assertRaisesRegex(InvalidInput,'SUSPECT_UNREVISED_CUE'):
            self.engine.prepare_nonresearch_risk_revisit(1,context_radius=4)

    def test_03_challenge_self_hash_forgery_cannot_change_target(self):
        q=self.challenge(); forged=copy.deepcopy(q)
        forged['target_cues'][0]['text']='modified evidence'
        forged['challenge_sha256']=_digest({k:v for k,v in forged.items()
                                             if k!='challenge_sha256'})
        with self.assertRaises(InvalidInput):
            self.engine.submit_context_revisit(forged,risk_answer(forged))
        self.assertEqual(self.engine.progress()['cue_reviewed'],4)
        with sqlite3.connect(self.db) as con:
            self.assertEqual(con.execute('SELECT COUNT(*) FROM cue_revisions').fetchone()[0],0)

    def test_04_false_quote_rejected_without_write(self):
        q=self.challenge()
        with self.assertRaisesRegex(InvalidInput,'CONTEXT_CLAIM_QUOTE_OR_NUMBER_NOT_IN_SOURCE'):
            self.engine.submit_context_revisit(q,risk_answer(q,forged=True))
        with sqlite3.connect(self.db) as con:
            self.assertEqual(con.execute('SELECT COUNT(*) FROM cue_revisions').fetchone()[0],0)

    def test_05_reopen_rebuilds_original_and_revision_chain(self):
        q=self.challenge();r=self.engine.submit_context_revisit(q,risk_answer(q))
        restarted=EngineChatSession(self.db,self.raw,'AbCdEf12345',
                    owner_source_sha256=sha256(self.raw),window_size=3,expected_window_count=2)
        self.assertEqual(restarted.progress()['checkpoint_head_sha256'],r['checkpoint_head_sha256'])
        self.assertEqual(restarted.compile_native_v6_stage()[1]['native_v6_audit']['proposed_atomic_claims'],2)
        with self.assertRaisesRegex(InvalidInput,'SUSPECT_UNREVISED_CUE'):
            restarted.prepare_nonresearch_risk_revisit(2,context_radius=4)

    def test_06_cannot_replay_same_model_response_as_second_approval(self):
        q=self.challenge();self.engine.submit_context_revisit(q,risk_answer(q))
        with self.assertRaises(InvalidInput):
            self.engine.submit_context_revisit(q,risk_answer(q))
        self.assertFalse(self.engine.progress()['e4_pass_claimed'])

    def test_07_can_reaffirm_no_independent_atom_explicitly(self):
        q=self.challenge();r=self.engine.submit_context_revisit(q,risk_answer(q,disposition='NON_RESEARCH'))
        self.assertFalse(r['e4_approved'])
        self.assertEqual(self.engine.compile_native_v6_stage()[1]['native_v6_audit']['proposed_atomic_claims'],1)

    def test_08_changed_original_source_rejected(self):
        new=self.raw.replace(b'ETF',b'ETN')
        with self.assertRaisesRegex(InvalidInput,'PINNED_OWNER_SRT_CHANGED'):
            EngineChatSession(self.db,new,'AbCdEf12345',
                              owner_source_sha256=sha256(self.raw),window_size=3)


if __name__=='__main__': unittest.main()