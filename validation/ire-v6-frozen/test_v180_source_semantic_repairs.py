"""V180 synthetic transition tests. These DO NOT invoke ChatGPT or certify recall.

Actual owner-source ChatGPT decisions stay private in the user's checkpoint;
CI asserts only fail-closed append-only source/response contracts.
"""
from __future__ import annotations
import copy,hashlib,json,sqlite3,tempfile,unittest
from pathlib import Path
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import EngineChatSession,COMMIT,REVISION,_digest
from v180_source_residual_gate import prepare_source_risk_recheck,assess_chat_risk_responses


def fixture():
    lines=['안녕하세요.',
           '이건 인덱스 펀드라고 부릅니다.',
           '다섯 가지 기준을 배워 보겠습니다.',
           'ETF는 주식시장에 상장되어 거래됩니다.',
           '매매 거래가 이루어집니다.',
           '기초지수를 잘 추종한다고 설명합니다.',
           '투자할 때 위험을 주의해야 합니다.',
           '하지만 주식이 부족할 수 있습니다.']
    return '\n\n'.join(f'{i}\n00:00:{i:02d},000 --> 00:00:{i:02d},500\n{s}'
                       for i,s in enumerate(lines,1)).encode('utf8')


def bare_claim(quote, proposition, *, kind='FACT', high=False, official=False, idx=4):
    return {'proposition':proposition,'kind':kind,'quote':quote,
            'context_cue_indices':[idx],'conditions':[], 'exceptions':[],
            'numeric_tokens':[], 'high_risk':high,'needs_official_source':official}


def first_reply(q):
    out=[]
    for c in q['target_cues']:
        i=c['cue_index'];kind='NON_RESEARCH';claims=[]
        if i==3:
            kind='ASSERTION'; claims=[bare_claim('기준을 배워 보겠습니다.',
                '오늘은 여러 가지를 배울 예정이라고 안내한다.',kind='ANECDOTE',idx=i)]
        elif i==4:
            kind='ASSERTION';claims=[bare_claim('ETF는 주식시장에 상장되어 거래됩니다.',
                'ETF는 주식시장에 상장되어 거래된다고 말한다.',high=True,official=True,idx=i)]
        elif i==7:
            kind='ASSERTION';claims=[bare_claim('투자할 때 위험을 주의해야 합니다.',
                '투자할 때 주의가 필요하다고 권고한다.',kind='RECOMMENDATION',high=True,idx=i)]
        out.append({'cue_index':i,'source_text_sha256':c['source_text_sha256'],
                    'disposition':kind,'speaker_role':'HOST','claims':claims,
                    'analysis':'원문 발화에 표시된 주제와 문맥을 확인하되 금융사실 승인이나 개인 자문은 하지 않는다.',
                    'limitations_checked':True})
    return {'schema':COMMIT,'challenge_sha256':q['challenge_sha256'],
            'review_executor':'CHATGPT_IN_CHAT','responses':out}


def revision_reply(q, *, cue, cls, prop=None, quote=None):
    t=q['target_cues'][0]
    claim=[]
    if cls=='ASSERTION':
        claim=[bare_claim(quote or '이건 인덱스 펀드라고 부릅니다.',
                          prop or '화자는 인덱스 펀드라는 명칭을 설명한다.',
                          idx=cue)]
    return {'schema':REVISION,'challenge_sha256':q['challenge_sha256'],
       'review_executor':'CHATGPT_IN_CHAT','responses':[
        {'cue_index':cue,'source_text_sha256':t['source_text_sha256'],
         'disposition':cls,'analysis':'인접한 원문 발화와 원래 연구 후보의 차이를 대조한 뒤 독립 주장 여부를 다시 판정하였다.',
         'speaker_role':'HOST','claims':claim,'limitations_checked':True,
         'prior_review_event_sha256':t['prior_review_event_sha256'],
         'new_context_cue_indices':[max(1,cue-1),cue],
         'change_reason':'새로운 원문 문맥 검토에 따라 이전 과잉 추출 또는 누락된 자막 의미를 수정한다. 원래 기록은 덮어쓰지 않고 보존한다.'}]
    }


class ActualEngineTransitionOnly(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.db=Path(temp.name)/'private.sqlite';self.raw=fixture()
        self.e=EngineChatSession(self.db,self.raw,'AbCdEf12345',
                         owner_source_sha256=sha256(self.raw),window_size=4,
                         expected_window_count=2)
        while self.e.progress()['cue_remaining']:
            q=self.e.prepare(limit=4,context_radius=4,source_first_only=True)
            self.e.submit(q,first_reply(q))

    def test_01_known_lexical_gap_not_flagged_but_reviewable(self):
        q= self.e.prepare_nonresearch_semantic_gap_revisit(2,
          source_quote='이건 인덱스 펀드라고 부릅니다.',
          gap_hypothesis='앞선 ETF 설명에서 용어의 별칭을 제시했으나 기존 원자 구조에 독립 명칭 개념이 들어 있지 않아 누락 검토가 필요하다.')
        self.assertEqual(q['type'],'REVISIT_NONRESEARCH_SEMANTIC_GAP')
        self.assertTrue(q['response_requirements']['no_automatic_approval'])
        receipt=self.e.submit_context_revisit(q,revision_reply(q,cue=2,cls='ASSERTION'))
        self.assertFalse(receipt['e4_approved'])
        x,s=self.e.compile_native_v6_stage()
        self.assertEqual(s['native_v6_audit']['proposed_atomic_claims'],3)
        self.assertFalse(s['native_v6_audit']['research_complete'])
        with sqlite3.connect(self.db) as c:
            self.assertEqual(c.execute('SELECT disposition FROM cue_reviews WHERE cue_index=2').fetchone()[0],'NON_RESEARCH')
            self.assertEqual(c.execute('SELECT COUNT(*) FROM cue_revisions').fetchone()[0],1)

    def test_02_no_gap_without_verbatim_quote(self):
        with self.assertRaisesRegex(InvalidInput,'SEMANTIC_GAP_SOURCE_REQUIRED'):
            self.e.prepare_nonresearch_semantic_gap_revisit(2,
              source_quote='가짜 상품입니다.',
              gap_hypothesis='원래 자료에 없는 문구를 인용하여 사실로 만들어서는 안 되므로 출처 대조로 차단해야 한다.')

    def test_03_short_hypothesis_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'SEMANTIC_GAP_SOURCE_REQUIRED'):
            self.e.prepare_nonresearch_semantic_gap_revisit(2,
              source_quote='인덱스 펀드',gap_hypothesis='누락')

    def test_04_no_atom_response_not_silent_consume_gap(self):
        q=self.e.prepare_nonresearch_semantic_gap_revisit(2,
         source_quote='인덱스 펀드',gap_hypothesis='출처 인용과 선행 문맥을 충분히 검토해 해당 발화의 독립된 개념 설명 여부를 추가로 확인해야 한다.')
        with self.assertRaisesRegex(InvalidInput,'GAP_REPAIR_REQUIRES_EXPLICIT_ASSERTION'):
            self.e.submit_context_revisit(q,revision_reply(q,cue=2,cls='NON_RESEARCH'))
        with sqlite3.connect(self.db) as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM cue_revisions').fetchone()[0],0)

    def test_05_tampered_challenge_fails_against_native_reissue(self):
        q=self.e.prepare_nonresearch_semantic_gap_revisit(2,
          source_quote='인덱스 펀드',gap_hypothesis='신규 영상 자막에서 독립된 용어 명칭 주장이라는 가설이 존재하므로 원문 직접 인용으로 누락을 감사한다.')
        forged=copy.deepcopy(q)
        forged['gap_hypothesis']='원본에 있는 척하는 잘못된 검토 지시 문구인데 길이만 충분히 길게 작성되었다.'
        forged['challenge_sha256']=_digest({k:v for k,v in forged.items() if k!='challenge_sha256'})
        # Self-hashing a new hypothesis does not authenticate model identity.
        # Actual security check: original cue quote/text cannot be forged.
        forged=copy.deepcopy(q);forged['target_cues'][0]['text']='UNTRUSTED INSERT'
        forged['challenge_sha256']=_digest({k:v for k,v in forged.items() if k!='challenge_sha256'})
        a=revision_reply(forged,cue=2,cls='ASSERTION')
        with self.assertRaisesRegex(InvalidInput,'CONTEXT_NOT_ENGINE_ISSUED'):
            self.e.submit_context_revisit(forged,a)

    def test_06_stale_head_and_replay_rejected(self):
        q=self.e.prepare_nonresearch_semantic_gap_revisit(2,
          source_quote='인덱스 펀드',gap_hypothesis='선행 자막에는 없는 개념 설명이 연결된 새 명제로 존재하므로 실제 원문에 근거하여 추가 검토가 필요하다.')
        r=revision_reply(q,cue=2,cls='ASSERTION')
        self.e.submit_context_revisit(q,r)
        with self.assertRaisesRegex(InvalidInput,'CONTEXT_HEAD_STALE|SEMANTIC_GAP_REQUIRES_UNREVISED'):
            self.e.submit_context_revisit(q,r)
        with self.assertRaisesRegex(InvalidInput,'SEMANTIC_GAP_REQUIRES_UNREVISED'):
            self.e.prepare_nonresearch_semantic_gap_revisit(2,
              source_quote='인덱스 펀드',gap_hypothesis='이전에 승인하지 않은 개념 설명의 원자 후보는 중복 심사와 승인을 시도해서는 안 된다.')

    def test_07_high_risk_original_cannot_be_erased(self):
        with self.assertRaisesRegex(InvalidInput,'OVEREXTRACT_HIGH_RISK'):
            self.e.prepare_overextracted_atom_revisit(4,
              source_quote='ETF는 주식시장에 상장되어 거래됩니다.',
              removal_rationale='금융 사실성과 고위험 여부를 추가 검토하지 않고 원본의 중요한 후보를 삭제하거나 숨겨서는 안 된다.')

    def test_08_overextracted_anecdote_can_be_safely_declassified(self):
        q=self.e.prepare_overextracted_atom_revisit(3,
           source_quote='기준을 배워 보겠습니다.',
           removal_rationale='앞선 후보는 금융 사실이나 운용 조건이 아니라 강의의 진행 일정을 소개한 담화적 발화이므로 지식 원자로 삼지 않는다.')
        s=self.e.compile_native_v6_stage()[1]
        self.assertEqual(s['native_v6_audit']['unresolved_cues'],1)
        r=self.e.submit_context_revisit(q,revision_reply(q,cue=3,cls='NON_RESEARCH'))
        after=self.e.compile_native_v6_stage()[1]
        self.assertEqual(after['native_v6_audit']['unresolved_cues'],0)
        self.assertEqual(after['native_v6_audit']['proposed_atomic_claims'],2)
        self.assertFalse(r['e5_published'])
        with sqlite3.connect(self.db) as c:
            self.assertEqual(c.execute('SELECT disposition FROM cue_reviews WHERE cue_index=3').fetchone()[0],'ASSERTION')

    def test_09_overextract_cannot_replace_with_unsupported_or_factual_atom(self):
        q=self.e.prepare_overextracted_atom_revisit(3,
           source_quote='기준을 배워 보겠습니다.',
           removal_rationale='연구 내용이 아니라 발언자의 발표 예정 사항을 기록한 진행 문장으로서 독립 금융 사실이 아니므로 제거를 검토한다.')
        a=revision_reply(q,cue=3,cls='ASSERTION')
        with self.assertRaisesRegex(InvalidInput,'OVEREXTRACT_REQUIRES_VERIFIED_NO_ATOM'):
            self.e.submit_context_revisit(q,a)

    def test_10_semantic_gap_cannot_target_existing_assertion_or_open(self):
        with self.assertRaisesRegex(InvalidInput,'SEMANTIC_GAP_REQUIRES_UNREVISED'):
            self.e.prepare_nonresearch_semantic_gap_revisit(4,
              source_quote='ETF는 주식시장에 상장되어 거래됩니다.',
              gap_hypothesis='이미 독립된 후보로 판단되어 있는 원자는 추가 의미 재검토 대상이 아니라 기존 원자 수정 경로로 처리해야 한다.')

    def test_11_identity_false_authority_metadata_is_not_accepted(self):
        q=self.e.prepare_nonresearch_semantic_gap_revisit(2,
          source_quote='인덱스 펀드',gap_hypothesis='용어 설명에 대한 새 투자 지식 후보를 추가하고 싶으나 이를 실제 승인된 금융 사실로 취급하면 안 되므로 별도 판정이 필요하다.')
        response=revision_reply(q,cue=2,cls='ASSERTION')
        response['e4_approved']=True
        with self.assertRaisesRegex(InvalidInput,'CONTEXT_RESPONSE_SCHEMA'):
            self.e.submit_context_revisit(q,response)

    def test_12_original_journal_and_source_are_immutable(self):
        original=self.db.read_bytes()
        q=self.e.prepare_nonresearch_semantic_gap_revisit(2,
          source_quote='인덱스 펀드',gap_hypothesis='분류기가 찾지 못했던 별도 명칭 설명에 대한 독립 후보를 만들어 원문 대조만 수행할 수 있도록 해야 한다.')
        forged=revision_reply(q,cue=2,cls='ASSERTION',quote='원문에 없는 주장')
        with self.assertRaisesRegex(InvalidInput,'CONTEXT_CLAIM_QUOTE_OR_NUMBER_NOT_IN_SOURCE'):
            self.e.submit_context_revisit(q,forged)
        self.assertEqual(self.e.progress()['cue_reviewed'],8)
        with sqlite3.connect(self.db) as c:self.assertEqual(c.execute('SELECT COUNT(*) FROM cue_revisions').fetchone()[0],0)
        with self.assertRaisesRegex(InvalidInput,'PINNED_OWNER_SRT_CHANGED'):
            EngineChatSession(self.db,self.raw.replace(b'ETF',b'ETN'),
                              'AbCdEf12345',owner_source_sha256=sha256(self.raw),window_size=4)


class RiskReviewDocket(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        self.raw=fixture();self.e=EngineChatSession(Path(t.name)/'s.sqlite',self.raw,
          'AbCdEf12345',owner_source_sha256=sha256(self.raw),window_size=4)
        while self.e.progress()['cue_remaining']:
            q=self.e.prepare(limit=4,source_first_only=True)
            self.e.submit(q,first_reply(q))
        self.q=prepare_source_risk_recheck(self.e)
        self.tasks={x['cue_index']:x for x in self.q['items']}

    def reply(self,i,decision='SOURCE_ONLY_DISCOURSE',parent=None):
        q=self.tasks[i];return {'cue_index':i,'source_cue_sha256':q['source_cue_sha256'],
            'source_quote':q['source_text'],'decision':decision,
            'linked_parent_claim_ids':parent or [],
            'meaning_reason':'이 문장은 전체 문맥상 다음 발화의 설명을 연결하는 부분에 해당하며 독립된 금융사실이나 수익 보장에 관한 결론을 만들지 않는다.',
            'conditions_and_exceptions_checked':True,
            'independent_gold_certified':False,'finance_truth_certified':False,
            'model_identity_cryptographically_attested':False,
            'e4_or_e5_authorized':False}

    def test_13_census_matches_frozen_v6_even_if_no_reviews(self):
        report=assess_chat_risk_responses(self.e,self.q,[])
        self.assertEqual(report['risk_cue_count'],len(self.tasks))
        self.assertEqual(report['unreviewed_risk_cues'],len(self.tasks))
        self.assertFalse(report['e4_approved'])

    def test_14_cannot_claim_parent_without_source_context(self):
        task=next(iter(self.tasks))
        bad=self.reply(task,'CONTEXT_ONLY_PROPOSAL',[])
        with self.assertRaises(InvalidInput):
            assess_chat_risk_responses(self.e,self.q,[bad])

    def test_15_false_model_identity_or_e4_is_rejected(self):
        i=next(iter(self.tasks))
        a=self.reply(i)
        a['e4_or_e5_authorized']=True
        with self.assertRaisesRegex(InvalidInput,'SOURCE_SEMANTIC_OR_AUTHORITY_REQUIRED'):
            assess_chat_risk_responses(self.e,self.q,[a])

    def test_16_duplicate_reviewer_cue_not_counted(self):
        i=next(iter(self.tasks))
        r=self.reply(i)
        with self.assertRaisesRegex(InvalidInput,'RESPONSE_LIST|UNKNOWN_OR_DUPLICATE'):
            assess_chat_risk_responses(self.e,self.q,[r,r])

    def test_17_stale_journal_does_not_certify_prior_review(self):
        old=self.q
        q=self.e.prepare_nonresearch_semantic_gap_revisit(2,
          source_quote='인덱스 펀드',gap_hypothesis='처음에는 누락된 원자 후보였으나 후속 세션의 의미 판단으로 원장이 바뀌었기 때문에 과거의 위험 검토 결과는 무효다.')
        self.e.submit_context_revisit(q,revision_reply(q,cue=2,cls='ASSERTION'))
        with self.assertRaisesRegex(InvalidInput,'STALE_OR_FORGED_CHALLENGE'):
            assess_chat_risk_responses(self.e,old,[])

    def test_18_forged_source_quote_rejected(self):
        i=next(iter(self.tasks))
        a=self.reply(i)
        a['source_quote']='거짓 인용 금지'
        with self.assertRaisesRegex(InvalidInput,'SOURCE_SEMANTIC_OR_AUTHORITY_REQUIRED'):
            assess_chat_risk_responses(self.e,self.q,[a])


if __name__=='__main__':unittest.main()