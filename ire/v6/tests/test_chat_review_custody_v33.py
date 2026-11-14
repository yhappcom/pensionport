"""V33 synthetic official/legal and master116 hash custody tests only."""
import copy,unittest
from ire.v6.codec import sha256,json_digest
from ire.v6.errors import InvalidInput
from ire.v6.source import verify_source
from ire.v6.tests.test_source_and_proof import make_srt,make_manifest
from ire.v6.provisional_full_source_v33 import draft_full_original_utterance_exchange_v33
from ire.v6.chat_review_custody_v33 import audit_source_bound_chat_reviews_v33

class V33HostReviewCustodyTests(unittest.TestCase):
    def setUp(self):
        raw=make_srt(['IRP의 인출 조건은 무엇일까요?','법정 예외가 있는지 검토합니다.',
                      '연금저축은 50만 원을 납입합니다.','세액 공제 조건은 다릅니다.'])
        m=make_manifest(raw,cut=2)
        self.src=verify_source(raw,m,expected_source_sha256=sha256(raw),expected_manifest_sha256=json_digest(m))
        self.ex,_=draft_full_original_utterance_exchange_v33(self.src)
        self.masters=[{'claim_id':f'GOMHEE-C{i:03d}','claim':f'합성 학습 문장 {i}'} for i in range(1,117)]
        self.vid=self.src.video_id
        ids=[1,2]
        self.review={
            'review_id':'SYNTHETIC_R01','video_id':self.vid,'source_cue_indices':ids,
            'source_cue_sha256':[sha256(self.src.cues[i-1].text.encode()) for i in ids],
            'draft_candidate_ids':sorted({cid for d in self.ex['cue_dispositions']
                                         if d['cue_index'] in ids for cid in d['claim_ids']}),
            'reviewed_claim':'IRP 중도인출에는 특정한 법정 사유가 존재한다는 검토사항이다.',
            'review_reason':'합성 원문과 현행 법령의 예외 관련 요건을 분리했으며 실제 개인계좌 자격은 전혀 확인되지 않았다.',
            'speaker_role':'HOST_INTERPRETATION',
            'meaning_verdict':'CURRENT_LAW_CONDITIONAL_EDUCATION','risk_level':'HIGH',
            'official_evidence':[{'source_url':'https://www.law.go.kr/LSW/test',
                   'retrieved_on':'2026-11-10','rule_effective_on':'2026-03-24',
                   'scope_note':'합성 법률 원문 예외에 해당하는지 개인 사정을 따로 검토해야 한다.',
                   'document_sha256_authenticated':False}],
            'knowledge_relation':{'relation':'REFINES_PRIOR_CHAT_REVIEW',
                   'master_claim_id':'GOMHEE-C001','master_claim_sha256':json_digest(self.masters[0]),
                   'reason':'대조된 합성 기존 지식의 핵심을 보완하지만 자동 병합은 승인하지 않는다.'},
            'reviewer':'CHATGPT_CURRENT_TURN','current_as_of':'2026-11-10'}

    def audit(self,**changes):
        params={'sources':{self.vid:self.src},'draft_exchanges':{self.vid:self.ex},
                'reviews':[self.review],'master_116':self.masters,'current_as_of':'2026-11-10'}
        params.update(changes)
        return audit_source_bound_chat_reviews_v33(**params)

    def altered(self,modify):
        x=copy.deepcopy(self.review);modify(x)
        return self.audit(reviews=[x])

    def test_actual_original_hash_and_master_relationship_structure(self):
        r=self.audit()
        self.assertEqual(r['host_review_claim_count'],1)
        self.assertTrue(r['master_116_identity_reproduced'])
        self.assertFalse(r['master116_or_p4_auto_merge'])
        self.assertFalse(r['independent_gold_precision_recall_measured'])
        self.assertFalse(r['p0_go'])

    def test_no_text_leak_in_public_hash_receipt(self):
        s=str(self.audit())
        self.assertNotIn(self.review['reviewed_claim'],s)
        self.assertNotIn(self.review['review_reason'],s)

    def test_forged_original_cue_hash_refused(self):
        with self.assertRaisesRegex(InvalidInput,'V33_REVIEW_ORIGINAL_CUE_SHA_TAMPER'):
            self.altered(lambda x:x['source_cue_sha256'].__setitem__(0,'0'*64))

    def test_forged_draft_candidate_mapping_refused(self):
        with self.assertRaisesRegex(InvalidInput,'V33_REVIEW_DRAFT_SOURCE_CANDIDATE_LINK_MISMATCH'):
            self.altered(lambda x:x.__setitem__('draft_candidate_ids',[]))

    def test_wrong_master_hash_refused(self):
        with self.assertRaisesRegex(InvalidInput,'V33_MASTER116_ROW_HASH_MISMATCH'):
            self.altered(lambda x:x['knowledge_relation'].__setitem__('master_claim_sha256','0'*64))

    def test_unknown_master_claim_refused(self):
        with self.assertRaises(InvalidInput):
            self.altered(lambda x:x['knowledge_relation'].__setitem__('master_claim_id','GOMHEE-C999'))

    def test_current_law_claim_requires_citation(self):
        with self.assertRaisesRegex(InvalidInput,'V33_CURRENT_LAW_REQUIRES_OFFICIAL_EVIDENCE'):
            self.altered(lambda x:x.__setitem__('official_evidence',[]))

    def test_nonofficial_injected_source_url_refused(self):
        with self.assertRaisesRegex(InvalidInput,'V33_OFFICIAL_EVIDENCE_NOT_CURRENT_OR_AUTHENTICATED'):
            self.altered(lambda x:x['official_evidence'][0].__setitem__('source_url','https://malicious.example/claim'))

    def test_future_law_effectivity_refused(self):
        with self.assertRaisesRegex(InvalidInput,'V33_OFFICIAL_EVIDENCE_NOT_CURRENT_OR_AUTHENTICATED'):
            self.altered(lambda x:x['official_evidence'][0].__setitem__('rule_effective_on','2027-01-01'))

    def test_publisher_body_not_falsely_attested(self):
        with self.assertRaisesRegex(InvalidInput,'V33_OFFICIAL_EVIDENCE_NOT_CURRENT_OR_AUTHENTICATED'):
            self.altered(lambda x:x['official_evidence'][0].__setitem__('document_sha256_authenticated',True))

    def test_forged_independent_reviewer_refused(self):
        with self.assertRaisesRegex(InvalidInput,'V33_HOST_REVIEW_MEANING_METADATA_INVALID'):
            self.altered(lambda x:x.__setitem__('reviewer','UNVERIFIED_EXPERT'))

    def test_duplicate_review_refused(self):
        with self.assertRaisesRegex(InvalidInput,'V33_HOST_REVIEW_DUPLICATE_OR_FOREIGN_ID'):
            self.audit(reviews=[self.review,self.review])

    def test_unknown_conclusion_refused(self):
        with self.assertRaisesRegex(InvalidInput,'V33_HOST_REVIEW_MEANING_METADATA_INVALID'):
            self.altered(lambda x:x.__setitem__('meaning_verdict','INDEPENDENT_P0_GO'))

    def test_possible_conflict_stays_open_and_never_auto_merges(self):
        r=self.altered(lambda x:x['knowledge_relation'].__setitem__('relation','POSSIBLE_CONFLICT_REQUIRES_REVIEW'))
        self.assertEqual(r['host_open_items'],1)
        self.assertFalse(r['master116_or_p4_auto_merge'])

if __name__=='__main__':unittest.main()
