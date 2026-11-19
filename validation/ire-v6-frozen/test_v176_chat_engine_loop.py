"""V176 synthetic adversarial tests; not original owner or independent gold."""
import copy, json, os, sqlite3, tempfile, unittest
from pathlib import Path
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import EngineChatSession, COMMIT, REVISION, EVIDENCE


def fixture():
    snippets=['반갑습니다.', '가정에서 투자한 돈이 10% 오른다고 말합니다.',
              '이것은 정말 안전한가요?', '다만 손실 가능성이 있습니다.',
              '다음 편도 보세요.']
    s=[]
    for i,t in enumerate(snippets,1):
        s.append(f'{i}\n00:00:{i:02d},000 --> 00:00:{i:02d},500\n{t}')
    return '\n\n'.join(s).encode('utf8')


def respond(challenge, *, add_claim=False):
    if challenge['type']=='SEARCH_ORIGINAL_PRIMARY_EVIDENCE':
        return {'schema':EVIDENCE,'review_executor':'CHATGPT_IN_CHAT',
                'challenge_sha256':challenge['challenge_sha256'],
                'responses':[{'cue_index':r['cue_index'],
                    'claim_index':r['claim_index'],
                    'claim_sha256':r['claim_sha256'],
                    'evidence_state':'NOT_FOUND_KEEP_OPEN',
                    'official_source_url':None,'source_excerpt':None,
                    'effective_as_of':None,'original_body_sha256':None,
                    'context_and_counterexamples':'공식 발행기관의 원문 근거가 제공되지 않아 이 투자 주장에 대한 재무 사실의 진위를 확정할 수 없습니다.',
                    'final_financial_truth_certified':False}
                    for r in challenge['claim_evidence_tasks']]}
    if challenge['type']=='RESOLVE_CONTEXT_CUES':
        results=[]
        for t in challenge['target_cues']:
            results.append({'cue_index':t['cue_index'],
                'source_text_sha256':t['source_text_sha256'],
                'disposition':'OPEN','speaker_role':'UNKNOWN','claims':[],
                'analysis':'상세 문맥을 재확인했으나 근거가 더 필요하여 이 발화를 승인할 수 없습니다.',
                'limitations_checked':True,
                'prior_review_event_sha256':t['prior_review_event_sha256'],
                'new_context_cue_indices':[3,4],
                'change_reason':'전후 자막을 함께 검토했지만 객관적인 근거가 아직 제공되지 않았습니다.'})
        return {'schema':REVISION, 'challenge_sha256':challenge['challenge_sha256'],
                'review_executor':'CHATGPT_IN_CHAT', 'responses':results}
    output=[]
    for row in challenge['target_cues']:
        i=row['cue_index']
        claim=[]
        if i==2 and add_claim:
            disp='ASSERTION'
            claim=[{'proposition':'투자한 금액이 10% 오른다고 설명한다.',
                    'kind':'HYPOTHETICAL', 'quote':'투자한 돈이 10% 오른다고',
                    'context_cue_indices':[2], 'conditions':[], 'exceptions':[],
                    'numeric_tokens':['10%'], 'high_risk':True,
                    'needs_official_source':True}]
        elif i==3:disp='QUESTION'
        elif i==4:disp='OPEN'
        else:disp='NON_RESEARCH'
        output.append({'cue_index':i, 'source_text_sha256':row['source_text_sha256'],
                       'disposition':disp, 'speaker_role':'UNKNOWN',
                       'analysis':'주변 문맥과 발화 목적을 확인했으나 자동 투자 사실 승인은 수행하지 않음',
                       'limitations_checked':disp!='OPEN','claims':claim})
    return {'schema':COMMIT, 'challenge_sha256':challenge['challenge_sha256'],
            'review_executor':'CHATGPT_IN_CHAT','responses':output}


class TestCollaborativeEngine(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.raw=fixture();self.db=Path(self.tmp.name)/'private'/'owner.sqlite'
        self.session=EngineChatSession(self.db,self.raw,'AbCdEf12345',
          owner_source_sha256=sha256(self.raw),window_size=3,expected_window_count=2)

    def test_01_frozen_v6_source_before_any_chat_and_real_review_exchange(self):
        p=self.session.progress()
        self.assertEqual(p['cue_total'],5)
        self.assertEqual(p['cue_reviewed'],0)
        c=self.session.prepare(limit=2)
        self.assertEqual([r['cue_index'] for r in c['target_cues']],[1,2])
        receipt=self.session.submit(c,respond(c,add_claim=True))
        self.assertEqual(receipt['status'],'CHAT_SOURCE_REVIEW_COMMITTED_UNRELEASED')
        staged,audit=self.session.compile_native_v6_stage()
        self.assertEqual(len(staged['atoms']),1)
        self.assertEqual(staged['atoms'][0]['kind'],'HYPOTHETICAL')
        self.assertEqual(audit['native_v6_audit']['original_scoped_cues_enumerated'],5)
        self.assertEqual(audit['pending_original_cues'],3)
        self.assertFalse(audit['e4_invoked'])

    def test_02_full_one_callback_host_cycle_still_never_e4_approves(self):
        r=self.session.run_host_cycle(lambda c:respond(c,add_claim=True),
                                      max_batches=6,batch_size=2)
        self.assertEqual(r['calls_completed'],5)
        self.assertTrue(r['all_source_cues_reviewed'])
        self.assertEqual(r['remaining_original_cues'],0)
        self.assertFalse(r['e4_approved'])
        self.assertFalse(r['e5_published'])
        p=self.session.progress()
        self.assertEqual(p['unresolved_open_cues'],1)
        original,evidence=self.session.compile_native_v6_stage()
        self.assertEqual(evidence['native_v6_audit']['proposed_atomic_claims'],1)
        self.assertEqual(evidence['pending_original_cues'],1)
        self.assertEqual(self.session.prepare()['type'],'E4_HOLD_UNRESOLVED_SOURCE')

    def test_03_restart_pins_source_and_preserves_cursor(self):
        c=self.session.prepare(limit=2)
        self.session.submit(c,respond(c,add_claim=True))
        reopened=EngineChatSession(self.db,self.raw,'AbCdEf12345',
             owner_source_sha256=sha256(self.raw),window_size=3,expected_window_count=2)
        self.assertEqual(reopened.progress()['cue_reviewed'],2)
        self.assertEqual(reopened.prepare(limit=2)['target_cues'][0]['cue_index'],3)
        with self.assertRaises(InvalidInput):
            EngineChatSession(self.db,self.raw,'AbCdEf12345',
                owner_source_sha256=sha256(self.raw),window_size=2)

    def test_04_stale_or_conflicting_turn_and_idempotence(self):
        c=self.session.prepare(limit=2)
        v=respond(c,add_claim=True)
        first=self.session.submit(c,v)
        self.assertEqual(self.session.submit(c,v)['status'],'IDEMPOTENT_CHAT_REVIEW_REPLAY')
        self.assertEqual(self.session.progress()['checkpoint_head_sha256'],first['checkpoint_head_sha256'])
        edit=copy.deepcopy(v);edit['responses'][0]['analysis']+=' 변경'
        with self.assertRaisesRegex(InvalidInput,'STALE_OR_CONFLICTING'):
            self.session.submit(c,edit)

    def test_05_changed_quote_and_fabricated_number_rejected(self):
        c=self.session.prepare(limit=3)
        v=respond(c,add_claim=True)
        v['responses'][1]['claims'][0]['quote']='원본에 존재하지 않는 거짓 인용'
        with self.assertRaisesRegex(InvalidInput,'ATOM_NOT_GROUNDED'):
            self.session.submit(c,v)
        v=respond(c,add_claim=True)
        v['responses'][1]['claims'][0]['numeric_tokens']=['999%']
        with self.assertRaisesRegex(InvalidInput,'ATOM_NUMBER_NOT_IN_CUE'):
            self.session.submit(c,v)
        self.assertEqual(self.session.progress()['cue_reviewed'],0)

    def test_06_fake_engine_challenge_cannot_self_sign(self):
        c=self.session.prepare(limit=2)
        bad=copy.deepcopy(c)
        bad['surrounding_context'].pop()
        from v176_chat_engine_loop import _digest
        bad['challenge_sha256']=_digest({k:v for k,v in bad.items() if k!='challenge_sha256'})
        v=respond(bad,add_claim=True)
        with self.assertRaisesRegex(InvalidInput,'CHALLENGE_NOT_ENGINE_ISSUED'):
            self.session.submit(bad,v)

    def test_07_duplicate_missing_and_out_of_order_target_prohibited(self):
        c=self.session.prepare(limit=3)
        r=respond(c,add_claim=True)
        r['responses']=r['responses'][:2]
        with self.assertRaisesRegex(InvalidInput,'INCOMPLETE'):
            self.session.submit(c,r)
        r=respond(c,add_claim=True)
        r['responses'][0],r['responses'][1]=r['responses'][1],r['responses'][0]
        with self.assertRaisesRegex(InvalidInput,'REVIEW_NOT_SOURCE_BOUND'):
            self.session.submit(c,r)
        self.assertEqual(self.session.progress()['cue_reviewed'],0)

    def test_08_private_event_and_review_census_tamper_detected(self):
        c=self.session.prepare(limit=3)
        self.session.submit(c,respond(c,add_claim=True))
        with sqlite3.connect(self.db) as con:
            con.execute('UPDATE cue_reviews SET disposition=? WHERE cue_index=?',('ASSERTION',1))
        with self.assertRaisesRegex(InvalidInput,'REVIEW_ROW_DRIFT'):
            self.session.progress()

    def test_09_source_mutation_and_missing_chat_host_fail(self):
        altered=self.raw.replace(b'\xeb\xb0\x98\xea\xb0\x91',b'\xec\x88\x98\xeb\x8b\x89')
        with self.assertRaises(InvalidInput):
            EngineChatSession(Path(self.tmp.name)/'different.db',altered,
               'AbCdEf12345',owner_source_sha256=sha256(self.raw))
        with self.assertRaisesRegex(InvalidInput,'NO_CHAT_HOST_CONNECTED'):
            self.session.run_host_cycle(None)

    def test_10_host_error_no_partial_commit_or_false_completion(self):
        def bad_chat(_):raise RuntimeError('Host not responding')
        with self.assertRaises(RuntimeError):
            self.session.run_host_cycle(bad_chat,max_batches=1)
        self.assertEqual(self.session.progress()['cue_reviewed'],0)
        self.assertFalse(self.session.work_summary()['research_finished'])

    def test_11_reviewed_open_not_silently_promoted_to_pass(self):
        self.session.run_host_cycle(lambda c:respond(c,add_claim=True),
                                    max_batches=6,batch_size=2)
        p=self.session.progress()
        self.assertEqual(p['cue_remaining'],0)
        self.assertEqual(p['unresolved_open_cues'],1)
        self.assertFalse(p['v123_pass_claimed'])
        self.assertFalse(p['e4_pass_claimed'])

    def test_12_unmappable_anecdote_remains_unresolved(self):
        c=self.session.prepare(limit=3)
        r=respond(c,add_claim=True)
        r['responses'][1]['claims'][0]['kind']='ANECDOTE'
        self.session.submit(c,r)
        _,meta=self.session.compile_native_v6_stage()
        self.assertEqual(meta['unsupported_claim_cues'],[2])
        self.assertEqual(meta['native_v6_audit']['proposed_atomic_claims'],0)
        self.assertFalse(meta['final_approval'])

    def test_13_real_context_revisit_preserves_original_and_updates_status(self):
        first=self.session.run_host_cycle(lambda c:respond(c,add_claim=True),
                                          max_batches=4,batch_size=2)
        self.assertEqual(first['remaining_original_cues'],0)
        task=self.session.prepare(limit=2)
        self.assertEqual(task['type'],'RESOLVE_CONTEXT_CUES')
        answer=respond(task)
        answer['responses'][0]['disposition']='NON_RESEARCH'
        answer['responses'][0]['analysis']='확장 문맥을 검토하니 단순 서술 연결부이며 별도의 투자 주장은 포함하지 않습니다.'
        ret=self.session.submit_context_revisit(task,answer)
        self.assertEqual(ret['status'],'CHAT_CONTEXT_REVISIT_COMMITTED_UNRELEASED')
        self.assertEqual(self.session.progress()['unresolved_open_cues'],0)
        with sqlite3.connect(self.db) as con:
            initial=con.execute('SELECT disposition FROM cue_reviews WHERE cue_index=4').fetchone()[0]
            revisions=con.execute('SELECT COUNT(*) FROM cue_revisions').fetchone()[0]
        self.assertEqual(initial,'OPEN')
        self.assertEqual(revisions,1)
        self.assertFalse(self.session.compile_native_v6_stage()[1]['e4_invoked'])

    def test_14_context_revisit_requires_real_original_and_previous_hash(self):
        self.session.run_host_cycle(lambda c:respond(c,add_claim=True),
                                    max_batches=4,batch_size=2)
        task=self.session.prepare(limit=2)
        answer=respond(task)
        answer['responses'][0]['prior_review_event_sha256']='1'*64
        with self.assertRaisesRegex(InvalidInput,'CONTEXT_REVISION_NOT_GROUNDED'):
            self.session.submit_context_revisit(task,answer)
        self.assertEqual(self.session.progress()['unresolved_open_cues'],1)

    def test_15_engine_requests_evidence_after_first_scope_and_does_not_approve(self):
        first=self.session.run_host_cycle(lambda c:respond(c,add_claim=True),
                                          max_batches=2,batch_size=2)
        task=self.session.prepare(limit=2)
        self.assertEqual(task['type'],'SEARCH_ORIGINAL_PRIMARY_EVIDENCE')
        self.assertEqual(task['claim_evidence_tasks'][0]['cue_index'],2)
        receipt=self.session.submit_evidence_proposals(task,respond(task))
        self.assertFalse(receipt['native_primary_bytes_verified'])
        self.assertEqual(self.session.progress()['source_evidence_proposals_recorded'],1)
        self.assertEqual(self.session.prepare(limit=2)['type'],'CLASSIFY_SOURCE_CUES')
        self.assertFalse(self.session.progress()['e4_pass_claimed'])

    def test_16_fake_official_evidence_cannot_be_authority(self):
        self.session.run_host_cycle(lambda c:respond(c,add_claim=True),
                                    max_batches=2,batch_size=2)
        task=self.session.prepare(limit=2)
        answer=respond(task)
        answer['responses'][0]['final_financial_truth_certified']=True
        with self.assertRaisesRegex(InvalidInput,'OFFICIAL_EVIDENCE_NOT_GROUNDED'):
            self.session.submit_evidence_proposals(task,answer)
        answer=respond(task)
        answer['responses'][0]['official_source_url']='https://example.com/fake'
        with self.assertRaisesRegex(InvalidInput,'MISSING_SOURCE_FAKED'):
            self.session.submit_evidence_proposals(task,answer)
        self.assertEqual(self.session.progress()['source_evidence_proposals_recorded'],0)

    def test_17_real_engine_holds_when_source_review_complete_but_open_remains(self):
        cycle=self.session.run_host_cycle(lambda c:respond(c,add_claim=True),
                                          max_batches=9,batch_size=2)
        self.assertTrue(cycle['all_source_cues_reviewed'])
        self.assertFalse(cycle['e4_approved'])
        marker=self.session.prepare(limit=2)
        self.assertEqual(marker['type'],'E4_HOLD_UNRESOLVED_SOURCE')
        self.assertEqual(marker['unresolved_cue_indices'],[4])
        self.assertFalse(marker['e5_authorized'])
        self.assertEqual(self.session.work_summary()['next_required_step'],
                         'E4_HOLD_UNRESOLVED_SOURCE')

if __name__=='__main__':unittest.main()