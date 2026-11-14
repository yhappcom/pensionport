"""ChatGPT-host general educational fallback and original-wording IRP bridge."""
from __future__ import annotations
import copy
import unittest
from pathlib import Path
from unittest.mock import patch
from ire.v6.codec import sha256,json_digest
from ire.v6.errors import InvalidInput
from ire.v6.chat_general_answer_v32 import (
 evaluate_chat_general_question_v32,evaluate_chat_irp_paraphrase_v32)

class V32GeneralEducationalTests(unittest.TestCase):
 def setUp(self):
  from ire.v6.tests.test_stage_repair import fixture,atom,exchange
  self.src=fixture(['감정적으로 팔면 시장 회복 기회를 놓칠 수도 있습니다.',
                    '투자 손실 후 다른 종목에 전부 옮기는 행동을 경계합니다.'])
  self.a=atom(self.src,'C00001',[1,2],[1,2],
               '주식 손실과 감정에 따른 성급한 갈아타기를 경계한다.',stance='UNRESOLVED')
  self.ex=exchange(self.src,[self.a]);self.asof='2026-11-10'
  self.q='손실 후 무턱대고 다른 종목으로 갈아타는 행동을 어떻게 생각하나요?'
  self.answer=('해당 영상 구간은 투자 손실 이후 감정에 휩쓸려 투자 대상을 바꾸는 행동을 경계합니다. '
               '매도 여부를 판단할 때는 손실 감정과 자산의 비용, 위험, 투자기간을 구분하는 것이 유용합니다. '
               '이는 특정 종목에 관한 매수나 매도 지시가 아니며 실제 선택은 투자자 상황에 따라 달라집니다.')
  self.meaning=[{'claim_id':'C00001','claim_frame_sha256':json_digest(self.a),
    'source_cue_sha256':[sha256(c.text.encode()) for c in self.src.cues],
    'source_kind':self.a['kind'],'source_stance':self.a['stance'],
    'source_speaker':self.a['speaker'],
    'reviewed_condition_cue_indices':[],'reviewed_exception_cue_indices':[],
    'numeric_scope_checked':True,'meaning_verdict':'SUPPORTED_WITH_CONTEXT',
    'reason':'손실 후 감정에 휩쓸린 투자의 위험성을 설명하는 일반 교육 명제이다.',
    'reviewer':'CHATGPT_CURRENT_TURN','reviewed_as_of':self.asof}]
  self.evidence=[{'rule_id':'SYNTHETIC_OFFICIAL_REFERENCE',
   'source_url':'https://www.law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1030452785',
   'effective_from':'2026-03-24','effective_to':None,'retrieved_on':self.asof,
   'excerpt':'합성 시험에서는 실제 법률 주장과 무관한 일반 투자교육 항목만 점검합니다.',
   'document_body_sha256':None,
   'scope_note':'실제 공식문서 인증을 주장하지 않는 독립 검증이 아닌 합성 코드 시험입니다.'}]
  self.evidence[0]['excerpt_sha256']=sha256(self.evidence[0]['excerpt'].encode())
  self.regs=[{'claim_id':'C00001','proposition_sha256':sha256(self.a['proposition'].encode()),
    'classification':'NOT_A_REGULATORY_CLAIM','rule_ids':[],
    'reason':'투자 심리와 의사결정 위험에 관한 의견이므로 개별 금융규정 단정이 아니다.',
    'missing_conditions':[],'reviewer':'CHATGPT_CURRENT_TURN',
    'reviewed_as_of':self.asof}]
  self.prior=[{'claim_id':'C00001','claim_frame_sha256':json_digest(self.a),
    'relation':'NO_MATCH_FOUND_CHAT_ONLY','master_claim_id':None,
    'master_atom_sha256':None,'reason':'관련 금융교육 원장에 정확한 대응 주장은 확인되지 않았다고 명시하였다.',
    'reviewer':'CHATGPT_CURRENT_TURN','reviewed_as_of':self.asof}]
  self.census=[{'claim_id':'C00001','question_sha256':sha256(self.q.encode()),
    'proposition_sha256':sha256(self.a['proposition'].encode()),
    'disposition':'SELECTED_RELEVANT','reviewer':'CHATGPT_CURRENT_TURN',
    'reviewed_as_of':self.asof,'context_checked':True,
    'reason':'금융 원문에서 감정에 따른 매도 행동을 검토한 주장과 질문이 관련되어 있다.'}]
  self.review={'schema':'IRE_V6_V32_CHAT_HOST_EDUCATIONAL_ANSWER_REVIEW',
    'question_sha256':sha256(self.q.encode()),
    'answer_sha256':sha256(self.answer.encode()),
    'source_sha256':self.src.source_sha256,
    'current_as_of':self.asof,'selected_claim_ids':['C00001'],
    'claim_frame_digests':[json_digest(self.a)],
    'claim_source_ref_digests':[json_digest(self.a['source_refs'])],
    'general_education_facet':'GENERAL_INVESTMENT_BEHAVIOR',
    'answer_scope':'GENERAL_EDUCATION_ONLY',
    'no_trade_instruction':True,'uncertainty_disclosed':True,
    'reviewer':'CHATGPT_CURRENT_TURN',
    'reason':'원문에서 검토한 일반 투자심리 위험만 서술하고 손익을 확정하거나 매매를 지시하지 않는다.'}

 def call(self,**d):
  args={'question':self.q,'source':self.src,'exchange':self.ex,'current_as_of':self.asof,
    'primary_evidence':self.evidence,'regulatory_decisions':self.regs,'meaning_reviews':self.meaning,
    'prior_knowledge_reviews':self.prior,'selected_claim_ids':['C00001'],
    'candidate_dispositions':self.census,'host_answer_text':self.answer,
    'host_answer_review':self.review}
  args.update(d)
  return evaluate_chat_general_question_v32(**args)

 def test_actual_chat_authored_general_educational_answer_path(self):
  r=self.call()
  self.assertEqual(r['answer_text'],self.answer)
  self.assertFalse(r['public_hash_only_receipt']['actual_legacy_v5_called'])
  self.assertTrue(r['operational_education_only'])
  self.assertFalse(r['p0_go'])

 def test_answer_text_not_leaked_to_public_receipt(self):
  r=self.call()
  self.assertNotIn(self.answer,str(r['public_hash_only_receipt']))
  self.assertEqual(r['public_hash_only_receipt']['host_answer_sha256'],sha256(self.answer.encode()))

 def test_unreviewed_prior_relation_refuses_generic_output(self):
  bad=copy.deepcopy(self.prior);bad[0]['relation']='POSSIBLE_RELATION_PENDING'
  with self.assertRaisesRegex(InvalidInput,'V32_CITED_ATOM_NOT_CHAT_REVIEWED'):
   self.call(prior_knowledge_reviews=bad)

 def test_missing_host_meaning_refuses_generic_output(self):
  with self.assertRaisesRegex(InvalidInput,'V32_CITED_ATOM_NOT_CHAT_REVIEWED'):
   self.call(meaning_reviews=[])

 def test_false_answer_digest_refused(self):
  bad=copy.deepcopy(self.review);bad['answer_sha256']='0'*64
  with self.assertRaisesRegex(InvalidInput,'V32_ANSWER_SHA_SOURCE_OR_SCOPE_MISMATCH'):
   self.call(host_answer_review=bad)

 def test_wrong_source_frame_sha_refused(self):
  bad=copy.deepcopy(self.review);bad['claim_frame_digests']=['0'*64]
  with self.assertRaisesRegex(InvalidInput,'V32_ANSWER_SHA_SOURCE_OR_SCOPE_MISMATCH'):
   self.call(host_answer_review=bad)

 def test_wrong_citation_exact_quotes_refused(self):
  bad=copy.deepcopy(self.review);bad['claim_source_ref_digests']=['0'*64]
  with self.assertRaisesRegex(InvalidInput,'V32_ANSWER_SHA_SOURCE_OR_SCOPE_MISMATCH'):
   self.call(host_answer_review=bad)

 def test_question_not_general_finance_is_refused(self):
  with self.assertRaisesRegex(InvalidInput,'V32_ONLY_SUPPORTED_GENERAL_EDUCATION_QUESTION'):
   self.call(question='IRP 중도인출은 가능한가요?')

 def test_direct_sell_command_refused_before_host_answer(self):
  with self.assertRaisesRegex(InvalidInput,'V32_ONLY_SUPPORTED_GENERAL_EDUCATION_QUESTION'):
   self.call(question='지금 보유 종목 모두 매도해줘')

 def test_guaranteed_return_answer_refused(self):
  with self.assertRaisesRegex(InvalidInput,'V32_UNSAFE_OR_INCOMPLETE_HOST_ANSWER'):
   self.call(host_answer_text='투자 수익 보장입니다.'+self.answer)

 def test_invented_numeric_return_refused(self):
  with self.assertRaisesRegex(InvalidInput,'V32_NUMERIC_UNSUPPORTED_IN_GENERIC_EDUCATION'):
   self.call(host_answer_text=self.answer+' 앞으로 투자수익은 13%입니다.')

 def test_uncertainty_flag_absence_refused(self):
  bad=copy.deepcopy(self.review);bad['uncertainty_disclosed']=False
  with self.assertRaisesRegex(InvalidInput,'V32_ANSWER_SHA_SOURCE_OR_SCOPE_MISMATCH'):
   self.call(host_answer_review=bad)

 def test_wrong_host_reviewer_identity_refused(self):
  bad=copy.deepcopy(self.review);bad['reviewer']='INDEPENDENT_HUMAN'
  with self.assertRaisesRegex(InvalidInput,'V32_ANSWER_SHA_SOURCE_OR_SCOPE_MISMATCH'):
   self.call(host_answer_review=bad)

 def test_v5_not_claimed_by_general_route(self):
  r=self.call();self.assertFalse(r['public_hash_only_receipt']['actual_legacy_v5_called'])

 def test_irp_normalization_rejects_wrong_subject(self):
  with self.assertRaisesRegex(InvalidInput,'V32_IRP_PARAPHRASE_SCOPE_INVALID'):
   evaluate_chat_irp_paraphrase_v32(Path('.'),'퇴직금을 받을 때 새 계좌가 필요하나요?',
     host_paraphrase_review={},source=self.src,exchange=self.ex,current_as_of=self.asof,
     primary_evidence=[],regulatory_decisions=self.regs,meaning_reviews=self.meaning,
     prior_knowledge_reviews=self.prior,selected_claim_ids=['C00001'],relevance_decisions=[],candidate_dispositions=[])

 def test_irp_bridge_does_not_accept_unrelated_paraphrase(self):
  with self.assertRaisesRegex(InvalidInput,'V32_NO_SAFE_PARAPHRASE_NORMALIZATION_AVAILABLE'):
   evaluate_chat_irp_paraphrase_v32(Path('.'),'IRP를 해지하면 어떤가요?',
     host_paraphrase_review={},source=self.src,exchange=self.ex,current_as_of=self.asof,
     primary_evidence=[],regulatory_decisions=self.regs,meaning_reviews=self.meaning,
     prior_knowledge_reviews=self.prior,selected_claim_ids=['C00001'],relevance_decisions=[],candidate_dispositions=[])

 def test_chat_approved_bridge_requires_complete_sha_receipt(self):
  with self.assertRaisesRegex(InvalidInput,'V32_IRP_PARAPHRASE_REVIEW_MISSING_OR_DRIFTED'):
   evaluate_chat_irp_paraphrase_v32(Path('.'),'퇴직금을 받을 때 IRP는 어떻게 하나요?',
     host_paraphrase_review={'reviewer':'CHATGPT_CURRENT_TURN'},
     source=self.src,exchange=self.ex,current_as_of=self.asof,
     primary_evidence=[],regulatory_decisions=self.regs,meaning_reviews=self.meaning,
     prior_knowledge_reviews=self.prior,selected_claim_ids=['C00001'],relevance_decisions=[],candidate_dispositions=[])

if __name__=='__main__': unittest.main()
