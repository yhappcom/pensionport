"""Synthetic only. No in-chat model identity or issuer origin attested."""
import copy
import unittest

from v166_e4_full_video_readiness import digest, h
from v167_chat_research_loop import prepare_open_docket, execute_chat_review_round


def fixture():
    cues = {1: '은퇴 후에는 연 4천만원이 필요합니다.',
            2: '시장수익률 5퍼센트라는 가정을 설명합니다.',
            3: '원금손실 위험은 모든 경우에 동일한가요?',
            4: '감사 인사입니다.'}
    raw = '\n\n'.join(f'{i}\n00:00:{i:02d},000 --> 00:00:{i:02d},500\n{t}'
                      for i,t in cues.items()).encode('utf-8')
    source = h(raw)
    segs = []
    for j in range(2):
        first = 2*j+1
        plan = {'source_sha256': source, 'cue_count': 4,
                'scope': {'first_cue': first, 'last_cue': first+1}}
        atoms = [{'claim_id':f'C{i:05d}', 'kind':'FACT' if i == 1 else 'QUESTION',
                  'context_cue_indices':[i],
                  'source_refs':[{'cue_index':i, 'quote':cues[i]}],
                  'condition_cue_indices':[], 'exception_cue_indices':[],
                  'numeric_references':[]} for i in (first, first+1)]
        statuses = ('OPEN','ACCEPT_FOR_RESEARCH') if j == 0 else ('OPEN','EXCLUDE_FROM_RESEARCH')
        verdicts = [{'claim_id': a['claim_id'],'atom_sha256':digest(a),
                     'status': s, 'high_risk': j == 0 and i == 0 and s == 'OPEN'}
                    for i,(a,s) in enumerate(zip(atoms,statuses))]
        event,bundle = digest(['e',j]), digest(['b',j])
        review = {'source_sha256':source, 'manifest_sha256':digest(plan),
                  'host_event_sha256':event,'host_bundle_sha256':bundle,
                  'source_cues':[{'cue_index':i,'status':'REVIEWED',
                                  'cue_text_sha256':h(cues[i].encode())}
                                 for i in (first,first+1)],
                  'atom_verdicts':verdicts,
                  'unresolved_high_risk_omissions':1,
                  'disagreements_adjudicated':False}
        segs.append({'segment_id':f'B{j+1:04d}', 'plan':plan,
                     'exchange':{'source_sha256':source,
                                 'manifest_sha256':digest(plan),'atoms':atoms},
                     'review':review, 'host':{'event_sha256':event,
                                              'bundle_sha256':bundle,
                                              'atomic_batch_committed':True}})
    return raw,cues,segs


def evidence(_):
    return [{'url':'https://example.com/books/a','body': b'A published research extract with plausible quoted material.',
             'excerpt':'published research extract', 'source_label':'Publisher',
             'retrieved_as_of':'2026-11-18'}]


def reviewer(req, decision='CANDIDATE_NEEDS_NATIVE_REVIEW'):
    return {'claim_id':req['task']['claim_id'],
            'atom_sha256':req['task']['atom_sha256'],
            'request_sha256':req['request_sha256'],
            'decision':decision,
            'reason':'원문의 조건·수치와 제출된 자료를 비교하였으나 공인 발행인 근거 및 최종 승인 검증이 남았습니다.',
            'conditions_checked':True, 'exceptions_checked':True,
            'numbers_and_period_checked':True, 'counterarguments_checked':True,
            'chat_reviewer_identity_attested':False,
            'financial_fact_certified':False,'personal_advice_approved':False}


class V167SourcePinnedLoopTests(unittest.TestCase):
    def setUp(self):
        self.raw,self.cues,self.segments = fixture()
        self.docket = prepare_open_docket(self.raw,self.cues,self.segments,
                expected_source_sha256=h(self.raw), as_of='2026-11-18')

    def test_01_all_source_and_high_risk_first(self):
        self.assertEqual(self.docket['original_atom_count'],4)
        self.assertEqual(self.docket['original_open_count'],2)
        self.assertEqual(self.docket['original_high_risk_open_count'],1)
        self.assertEqual([x['claim_id'] for x in self.docket['items']],['C00001','C00003'])
        self.assertFalse(self.docket['e4_approved'])

    def test_02_chat_proposals_always_unreleased(self):
        orig=copy.deepcopy(self.segments)
        receipt=execute_chat_review_round(self.docket,evidence_retriever=evidence,
                                          chat_reviewer=reviewer)
        self.assertEqual(receipt['candidate_proposals'],2)
        self.assertEqual(receipt['unprocessed_open_count'],0)
        self.assertFalse(receipt['knowledge_publication_authorized'])
        self.assertFalse(receipt['e5_authorized'])
        self.assertTrue(all(not x['applied_to_native_v123'] for x in receipt['proposals']))
        self.assertTrue(all(not e['provenance_authenticated'] for x in receipt['proposals']
                            for e in x['source_evidence']))
        self.assertEqual(orig,self.segments)

    def test_03_limit_keeps_remaining_open(self):
        r=execute_chat_review_round(self.docket,evidence_retriever=evidence,
            chat_reviewer=lambda q:reviewer(q,'KEEP_OPEN'), limit=1)
        self.assertEqual(r['proposals_created'],1)
        self.assertEqual(r['unprocessed_open_count'],1)
        self.assertEqual(r['candidate_proposals'],0)

    def test_04_approval_without_source_blocked(self):
        with self.assertRaisesRegex(ValueError,'CANDIDATE_WITHOUT_SOURCE'):
            execute_chat_review_round(self.docket,evidence_retriever=lambda _:[],
                                     chat_reviewer=reviewer)

    def test_05_spoofed_claim_or_evidence_hash_blocked(self):
        def evil(req):
            v=reviewer(req);v['request_sha256']='0'*64
            return v
        with self.assertRaisesRegex(ValueError,'CHAT_DECISION_PIN_MISMATCH'):
            execute_chat_review_round(self.docket,evidence_retriever=evidence,
                                     chat_reviewer=evil)

    def test_06_forged_origin_claim_blocked(self):
        def evil(req):
            v=reviewer(req);v['chat_reviewer_identity_attested']=True
            return v
        with self.assertRaisesRegex(ValueError,'CHAT_SEMANTIC_OR_AUTHORITY_NOT_SAFE'):
            execute_chat_review_round(self.docket,evidence_retriever=evidence,
                                     chat_reviewer=evil)

    def test_07_changed_docket_digest_blocked(self):
        self.docket['items'][0]['source_context'][0]['text']='다른 말'
        with self.assertRaisesRegex(ValueError,'DOCKET_DRIFT'):
            execute_chat_review_round(self.docket,evidence_retriever=evidence,
                                     chat_reviewer=reviewer)

    def test_08_original_owner_bytes_blocked(self):
        with self.assertRaisesRegex(ValueError,'OWNER_SOURCE_PIN_MISMATCH'):
            prepare_open_docket(self.raw,self.cues,self.segments,
                                expected_source_sha256='0'*64,
                                as_of='2026-11-18')

    def test_09_evidence_quote_must_be_in_bytes(self):
        def fake(_):
            v=evidence(None)
            v[0]['excerpt']='Invented quote not in publisher body'
            return v
        with self.assertRaisesRegex(ValueError,'EVIDENCE_QUOTE_NOT_IN_BYTES'):
            execute_chat_review_round(self.docket,evidence_retriever=fake,
                                     chat_reviewer=reviewer)

    def test_10_no_host_callback_no_automatic_model(self):
        with self.assertRaisesRegex(ValueError,'CHAT_HOST_CALLBACK_REQUIRED'):
            execute_chat_review_round(self.docket,evidence_retriever=evidence,
                                     chat_reviewer=None)

    def test_11_unchecked_conditions_blocked(self):
        def evil(req):
            v=reviewer(req);v['exceptions_checked']=False
            return v
        with self.assertRaisesRegex(ValueError,'CHAT_SEMANTIC_OR_AUTHORITY_NOT_SAFE'):
            execute_chat_review_round(self.docket,evidence_retriever=evidence,
                                     chat_reviewer=evil)

    def test_12_candidate_not_equivalent_to_native_release(self):
        a=execute_chat_review_round(self.docket,evidence_retriever=evidence,
                                    chat_reviewer=reviewer)
        self.assertEqual(a['proposals_created'],2)
        self.assertEqual(self.docket['original_open_count'],2)
        self.assertTrue(a['native_v123_replay_required'])
        self.assertTrue(a['formal_e4_primary_and_scope_review_required'])

if __name__=='__main__':unittest.main()