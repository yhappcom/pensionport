"""Synthetic adversarial current-law review: TODAY rather than filming/upload day."""
import copy
import unittest

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from ire.v6.current_law_reassessment import (
    audit_current_law_reassessment,prepare_private_current_law_chat_packet)
from ire.v6.tests.test_stage_repair import fixture,atom,exchange


class CurrentLawReassessmentTests(unittest.TestCase):
    def setUp(self):
        self.source=fixture([
            'IRP는 중도 인출이 전혀 불가능합니다.',
            '국내 ETF 매매수익은 모두 15.4% 세금을 냅니다.',
            '투자에서는 위험을 분산하세요.'])
        self.ex=exchange(self.source,[
            atom(self.source,'C00001',[1],[1],
                 'IRP 중도인출이 어떠한 경우에도 불가능하다고 단정한다.',
                 stance='AFFIRMED'),
            atom(self.source,'C00002',[2],[2],
                 '모든 국내 ETF의 매매차익은 15.4% 과세된다고 단정한다.',
                 stance='AFFIRMED'),
            atom(self.source,'C00003',[3],[3],
                 '투자에는 분산이 필요하다는 개인적 견해다.',
                 stance='AFFIRMED')])
        self.asof='2026-11-10'
        self.evidence=[self._evidence('IRP_CURRENT','2026-03-24',
            'https://law.go.kr/lsLinkCommonInfo.do?chrClsCd=010202&lspttninfSeq=71031',
            '개인형퇴직연금제도의 중도인출에 관한 제18조 제2항은 법정 사유를 규정한다.'),
            self._evidence('ETF_KRX_TAX','2026-01-01',
            'https://regulation.krx.co.kr/contents/RGL/03/03060105/RGL03060105.jsp',
            '국내주식형 ETF의 매매차익과 기타 ETF의 보유기간 과세는 구분해서 다루어야 한다.')]
        self.decisions=[
            self._decision('C00001','CURRENT_RULE_CONTRADICTS_SOURCE',['IRP_CURRENT'],
                'IRP에서 법정 사유로 인출이 허용되는 예외가 있어 절대 불가라는 명제에 반례가 존재한다.'),
            self._decision('C00002','CURRENT_RULE_SCOPE_MISSING',['ETF_KRX_TAX'],
                '국내 주식형과 기타 ETF 매매차익의 과세 차이를 무시한 과잉 일반화이다.',
                ['ETF 종류','납세계좌 유형']),
            self._decision('C00003','NOT_A_REGULATORY_CLAIM',[],
                '이 문장은 투자 다각화에 관한 일반적 의견으로 법정 금융 규정의 단언이 아니다.')]

    def _evidence(self,rid,start,url,text):
        return {'rule_id':rid,'source_url':url,'effective_from':start,
            'effective_to':None,'retrieved_on':'2026-11-10','excerpt':text,
            'excerpt_sha256':sha256(text.encode()),'document_body_sha256':None,
            'scope_note':'채팅이 공식기관의 일반 적용 범위만 확인했으며 개인 적용 및 별도 시행일은 추가 확인 필요함'}

    def _decision(self,cid,klass,rids,reason,missing=None):
        a=next(x for x in self.ex['atoms'] if x['claim_id']==cid)
        return {'claim_id':cid,'proposition_sha256':sha256(a['proposition'].encode()),
                'classification':klass,'rule_ids':rids,'reason':reason,
                'missing_conditions':sorted(missing or []),
                'reviewer':'CHATGPT_CURRENT_TURN','reviewed_as_of':self.asof}

    def _audit(self,*,evidence=None,decisions=None,asof=None,ex=None):
        return audit_current_law_reassessment(self.source,ex or self.ex,
            current_as_of=asof or self.asof,
            primary_evidence=self.evidence if evidence is None else evidence,
            chat_decisions=self.decisions if decisions is None else decisions)

    def test_current_law_after_video_publication_is_valid_for_current_advice(self):
        r=self._audit()
        self.assertEqual(r['mode'],'CURRENT_ADVISORY_ASOF_NOT_HISTORICAL_SPEECH')
        self.assertEqual(r['current_as_of'],'2026-11-10')
        self.assertEqual(r['chat_reviewed_claims'],3)
        self.assertEqual(r['open_chat_review_claims'],0)
        self.assertTrue(r['video_publication_date_not_used_as_current_law_gate'])
        self.assertFalse(r['approved_advisory_knowledge'])
        self.assertFalse(r['individual_tax_or_pension_application_approved'])
        self.assertFalse(r['p0_go'])
        self.assertEqual(r['claim_review'][0]['classification'],'CURRENT_RULE_CONTRADICTS_SOURCE')
        self.assertEqual(r['claim_review'][1]['classification'],'CURRENT_RULE_SCOPE_MISSING')

    def test_missing_chat_reviews_are_queued_not_auto_certified(self):
        r=self._audit(decisions=self.decisions[:1])
        self.assertEqual(r['chat_reviewed_claims'],1)
        self.assertEqual(r['open_chat_review_claims'],2)
        self.assertEqual(r['outstanding_claim_ids'],['C00002','C00003'])
        self.assertFalse(r['independent_semantic_precision_recall_measured'])

    def test_expired_law_may_not_justify_current_ruling(self):
        e=copy.deepcopy(self.evidence);e[0]['effective_to']='2026-10-01'
        with self.assertRaisesRegex(InvalidInput,'REFERENCED_RULE_NOT_CURRENT'):
            self._audit(evidence=e)
        d=copy.deepcopy(self.decisions);d[0]['classification']='CURRENT_FACT_OR_APPLICABILITY_UNKNOWN'
        r=self._audit(evidence=e,decisions=d)
        self.assertEqual(r['official_references']['IRP_CURRENT']['status'],'EXPIRED_NOT_CURRENT')

    def test_future_law_may_not_justify_current_ruling(self):
        e=copy.deepcopy(self.evidence);e[0]['effective_from']='2027-01-01'
        with self.assertRaisesRegex(InvalidInput,'REFERENCED_RULE_NOT_CURRENT'):
            self._audit(evidence=e)

    def test_stale_primary_page_cannot_support_certified_current_status(self):
        e=copy.deepcopy(self.evidence);e[0]['retrieved_on']='2026-09-01'
        with self.assertRaisesRegex(InvalidInput,'REFERENCED_RULE_NOT_CURRENT'):
            self._audit(evidence=e)

    def test_untrusted_source_cannot_pose_as_authoritative(self):
        for url in ['http://law.go.kr/article','https://law.go.kr.evil.test/article',
                    'https://evil.test/article','https://law.go.kr@evil.test/article']:
            e=copy.deepcopy(self.evidence);e[0]['source_url']=url
            with self.subTest(url=url),self.assertRaises(InvalidInput):
                self._audit(evidence=e)

    def test_forged_official_excerpt_hash_rejected(self):
        e=copy.deepcopy(self.evidence);e[0]['excerpt_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'EXCERPT_SHA_MISMATCH'):
            self._audit(evidence=e)

    def test_reject_silent_video_proposition_change(self):
        d=copy.deepcopy(self.decisions);d[0]['proposition_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'SOURCE_PROPOSITION_DRIFT'):
            self._audit(decisions=d)

    def test_unjustified_chats_and_duplicate_rules_rejected(self):
        d=copy.deepcopy(self.decisions);d[0]['rule_ids']=[]
        with self.assertRaisesRegex(InvalidInput,'REGULATORY_JUDGMENT_NO_RULE'):
            self._audit(decisions=d)
        d=copy.deepcopy(self.decisions);d[0]['rule_ids']=['IRP_CURRENT','IRP_CURRENT']
        with self.assertRaises(InvalidInput):self._audit(decisions=d)

    def test_general_consistency_must_require_conditions(self):
        d=copy.deepcopy(self.decisions)
        d[0]['classification']='CURRENT_GENERAL_RULE_CONSISTENT_CONDITIONAL'
        with self.assertRaisesRegex(InvalidInput,'UNCONDITIONAL_LEGAL_APPROVAL_FORBIDDEN'):
            self._audit(decisions=d)
        d[0]['missing_conditions']=['가입자 조건']
        self.assertEqual(self._audit(decisions=d)['chat_reviewed_claims'],3)

    def test_private_packet_exposes_source_to_chat_only_not_public(self):
        p=prepare_private_current_law_chat_packet(self.source,self.ex,
            current_as_of=self.asof,primary_evidence=self.evidence,max_claims=2)
        self.assertEqual(p['remaining_claim_count'],1)
        self.assertEqual(len(p['original_claims']),2)
        self.assertEqual(len(p['official_law_evidence']),2)
        self.assertTrue(p['private_not_for_public_storage'])
        self.assertFalse(p['independent_gold'])
        self.assertIn('IRP',p['original_claims'][0]['original_cues'][0]['quote'])

    def test_chronological_prereg_is_not_altered(self):
        r=self._audit()
        self.assertFalse(r['general_rule_chat_comparison_only'] is False)
        self.assertFalse(r['independent_semantic_precision_recall_measured'])
        self.assertTrue(r['official_primary_bytes_identity_not_independently_verified'])
        self.assertFalse(r['p0_go'])

    def test_non_regulatory_claim_cannot_disguise_a_legal_ruling(self):
        d=copy.deepcopy(self.decisions);d[0]['classification']='NOT_A_REGULATORY_CLAIM'
        with self.assertRaises(InvalidInput):self._audit(decisions=d)

    def test_explicit_tax_fact_cannot_be_hidden_as_nonregulatory(self):
        d=copy.deepcopy(self.decisions)
        d[1]['classification']='NOT_A_REGULATORY_CLAIM'
        d[1]['rule_ids']=[]
        d[1]['missing_conditions']=[]
        with self.assertRaisesRegex(InvalidInput,'LEGAL_FACT_FALSE_NONREGULATORY'):
            self._audit(decisions=d)

    def test_invalid_asof_bad_date(self):
        with self.assertRaises(InvalidInput):self._audit(asof='2026-11-31')
        with self.assertRaises(InvalidInput):self._audit(asof='2026/11/10')

    def test_reviewer_identity_is_not_external_human(self):
        d=copy.deepcopy(self.decisions);d[0]['reviewer']='INDEPENDENT_HUMAN'
        with self.assertRaises(InvalidInput):self._audit(decisions=d)


if __name__=='__main__': unittest.main()
