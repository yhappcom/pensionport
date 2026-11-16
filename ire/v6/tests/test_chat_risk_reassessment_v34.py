"""V34 synthetic custody regression tests; no private originals, no blind gold."""
from __future__ import annotations
import copy
import unittest
from unittest.mock import patch
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import verify_source
from ire.v6.semantic_risk import audit_semantic_risks
from ire.v6.tests.test_source_and_proof import make_manifest
from ire.v6.tests.test_stage_repair import atom,exchange
from ire.v6.chat_risk_reassessment_v34 import (
    audit_40_original_contrast_docket_v34,
    audit_two_open_original_claim_reassessments_v34,
    audit_chat_firstpass_atomic_window_v34)


def synthesized_source(n):
    text=[]
    for _ in range(8):
        text.extend(['특정 투자 대안을 논의합니다.', '조금 더 설명합니다.',
         '하지만 그 결과가 달라질 수 있습니다.', '이해할 필요가 있습니다.',
         '해당 주제의 설명을 마칩니다.', '다음 대화로 이어집니다.'])
    def stamp(t):return f'00:00:{t//1000:02d},{t%1000:03d}'
    raw='\n\n'.join(f'{i+1}\n{stamp(i*100)} --> {stamp(i*100+80)}\n{v}'
                          for i,v in enumerate(text)).encode('utf8')
    manifest=make_manifest(raw,cut=6)
    manifest['video_id']=f'SimV34{n:05d}'
    src=verify_source(raw,manifest,expected_source_sha256=sha256(raw),
                 expected_manifest_sha256=json_digest(manifest))
    atoms=[]
    for k in range(8):
        a=k*6+1; b=k*6+3
        atoms.append(atom(src,f'C{k*2+1:05d}',[a],[a],
                  '특정 투자 대안을 논의한다고 설명한다.',stance='UNRESOLVED'))
        atoms.append(atom(src,f'C{k*2+2:05d}',[b],[b],
                  '하지만 투자결과가 달라질 수 있다는 경고다.',stance='UNRESOLVED'))
    ex=exchange(src,atoms)
    return src,ex


class Original40ChatRiskDocketTests(unittest.TestCase):
    def setUp(self):
        self.sources={};self.exchanges={};self.rows=[]
        for n in range(5):
            src,ex=synthesized_source(n)
            self.sources[src.video_id]=src;self.exchanges[src.video_id]=ex
            risk=audit_semantic_risks(src,ex)
            self.assertEqual(risk['review_case_count'],8)
            for case in risk['review_cases']:
                idx=case['cue_index']
                carrier=next(a for a in ex['atoms'] if a['claim_id']!=case['claim_id']
                   and idx in [r['cue_index'] for r in a['source_refs']])
                context=list(range(max(1,idx-2),min(len(src.cues),idx+3)+1))
                self.rows.append({'video_id':src.video_id,'case_sha256':case['case_sha256'],
                  'case_cue_index':idx,'case_cue_sha256':sha256(src.cues[idx-1].text.encode()),
                  'draft_claim_id':case['claim_id'],
                  'draft_claim_frame_sha256':json_digest(next(a for a in ex['atoms'] if a['claim_id']==case['claim_id'])),
                  'contrast_carrier_claim_id':carrier['claim_id'],
                  'carrier_claim_frame_sha256':json_digest(carrier),
                  'context_cue_indices':context,
                  'context_cue_sha256':[sha256(src.cues[i-1].text.encode()) for i in context],
                  'classification':'CROSS_CUE_DISCOURSE_ONLY',
                  'chat_reason':'뒤에 이어지는 대조 표현은 원래 원자 주장 단독 인용에서 빠진 후속 문맥이다.',
                  'reviewer':'CHATGPT_CURRENT_TURN','as_of':'2026-11-10'})

    def audit(self,**kwargs):
        default=dict(sources=self.sources,exchanges=self.exchanges,
                     review_rows=self.rows,as_of='2026-11-10')
        default.update(kwargs)
        return audit_40_original_contrast_docket_v34(**default)

    def test_all_synthetic_40_source_bound_without_certification(self):
        r=self.audit()
        self.assertEqual(r['reviewed_alerts'],40)
        self.assertEqual(r['discourse_only_heuristic_alerts'],40)
        self.assertEqual(r['financial_or_asr_semantic_review_still_open'],0)
        self.assertFalse(r['full_video_semantic_accuracy_certified'])
        self.assertFalse(r['p0_go'])

    def test_explicit_unresolved_cases_do_not_disappear(self):
        bad=copy.deepcopy(self.rows)
        bad[0]['classification']='FINANCIAL_TAX_OR_LEGAL_SCOPE_OPEN'
        r=self.audit(review_rows=bad)
        self.assertEqual(r['financial_or_asr_semantic_review_still_open'],1)
        self.assertEqual(r['discourse_only_heuristic_alerts'],39)
        self.assertTrue(r['original_raw_heuristic_flags_kept'])

    def test_missing_case_fails(self):
        with self.assertRaisesRegex(InvalidInput,'V34_ORIGINAL_40_CASE_CENSUS_REQUIRED'):
            self.audit(review_rows=self.rows[:-1])

    def test_duplicate_case_fails(self):
        bad=copy.deepcopy(self.rows)
        bad[-1]=bad[0]
        with self.assertRaisesRegex(InvalidInput,'V34_RISK_CASE_MISSING_DUPLICATE_OR_FOREIGN'):
            self.audit(review_rows=bad)

    def test_changed_original_cue_sha_fails(self):
        bad=copy.deepcopy(self.rows)
        bad[0]['case_cue_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'V34_RISK_ORIGINAL_CUE_OR_CONTEXT_CHANGED'):
            self.audit(review_rows=bad)

    def test_changed_context_neighbor_hash_fails(self):
        bad=copy.deepcopy(self.rows)
        bad[0]['context_cue_sha256'][0]='0'*64
        with self.assertRaisesRegex(InvalidInput,'V34_RISK_ORIGINAL_CUE_OR_CONTEXT_CHANGED'):
            self.audit(review_rows=bad)

    def test_cannot_point_to_same_claim_as_contrast(self):
        bad=copy.deepcopy(self.rows)
        bad[0]['contrast_carrier_claim_id']=bad[0]['draft_claim_id']
        with self.assertRaisesRegex(InvalidInput,'V34_RISK_CONTRAST_CARRIER_NOT_SOURCE_PINNED'):
            self.audit(review_rows=bad)

    def test_false_external_reviewer_rejected(self):
        bad=copy.deepcopy(self.rows)
        bad[0]['reviewer']='INDEPENDENT_EXPERT'
        with self.assertRaisesRegex(InvalidInput,'V34_HOST_RISK_MEANING_REVIEW_INVALID'):
            self.audit(review_rows=bad)

    def test_unregistered_risk_class_rejected(self):
        bad=copy.deepcopy(self.rows)
        bad[0]['classification']='HUMAN_GOLD_COMPLETE'
        with self.assertRaisesRegex(InvalidInput,'V34_HOST_RISK_MEANING_REVIEW_INVALID'):
            self.audit(review_rows=bad)

    def test_atom_rewrite_is_not_silently_rebound(self):
        bad=copy.deepcopy(self.exchanges)
        key=next(iter(bad))
        bad[key]['atoms'][0]['proposition']='전혀 다른 의견을 주장한다고 수정하였다.'
        with self.assertRaisesRegex(InvalidInput,'V34_RISK_DRAFT_ATOM_HASH_CHANGED'):
            self.audit(exchanges=bad)


class ConditionalTwoOpenProofTests(unittest.TestCase):
    def setUp(self):
        src,ex=synthesized_source(0)
        self.sources={src.video_id:src};self.exchanges={src.video_id:ex}
        self.master=[{'claim_id':f'GOMHEE-C{i:02d}','claim':f'합성 투자 지식 {i}'} for i in range(1,117)]
        self.old=[{'review_id':'V3-IRP_ONE_MAN_WITHDRAWAL_START','video_id':src.video_id,
                 'source_cue_indices':[1], 'source_cue_sha256':[sha256(src.cues[0].text.encode())],
                 'knowledge_relation':{'master_claim_id':'GOMHEE-C31'}},
                  {'review_id':'V5-EMPLOYER_SUPPLIER_STOCK_ADVOCACY','video_id':src.video_id,
                 'source_cue_indices':[3], 'source_cue_sha256':[sha256(src.cues[2].text.encode())],
                 'knowledge_relation':{'master_claim_id':'GOMHEE-C09'}}]
        self.rows=[]
        sample_urls=[
            [('https://consumer.kiwoom.com/wm/rtp/pst/ij010/irpJoinMainView','FINANCIAL_INSTITUTION_POLICY','2026-11-10'),
             ('https://file.truefriend.com/Storage/kiwi/w8875/08174030IRPGuide2024.pdf','HISTORICAL_FINANCIAL_INSTITUTION_PDF','2024-07-18')],
            [('https://law.go.kr/LSW/lsLinkCommonInfo.do?lsJoLnkSeq=1032434111','STATUTE_CURRENT','2026-10-02'),
             ('https://www.investor.gov/introduction-investing','REGULATOR_FINANCIAL_EDUCATION','2026-11-10')]]
        for old,edges in zip(self.old,sample_urls):
            mid=old['knowledge_relation']['master_claim_id']
            self.rows.append({'review_id':old['review_id'],'video_id':old['video_id'],
                'original_v33_review_sha256':json_digest(old),
                'source_cue_sha256':old['source_cue_sha256'],
                'decision': ('PROVIDER_AND_CONTRIBUTION_TYPE_CONDITIONAL' if mid.endswith('31')
                  else 'PUBLIC_INFORMATION_AND_DIVERSIFICATION_BOUNDARY'),
                'new_meaning':'과거 원문은 투자 전략이 모든 가입자에게 항상 동일하다고 주장하는 것처럼 보이나, 실제 적용 조건을 분리하여 개별 상황에 맞는 조건부 교육적 설명만 남긴다.',
                'source_scope_reason':'공식 법령과 금융사 운영 정책의 내용 및 적용 시점이 구체적으로 다르므로 개인 자격과 사업자 종류에 관한 확정을 보류하고 단정적 투자를 승인하지 않는다.',
                'prior_master_claim_id':mid,
                'prior_master_row_sha256':json_digest(next(m for m in self.master if m['claim_id']==mid)),
                'official_evidence':[{'url':u,'source_type':t,
                     'published_or_effective_date':date,'retrieved_on':'2026-11-10',
                     'scope_note':'출처의 발행 시점과 적용 대상에 대한 설명은 사업자 계좌와 개인 사실관계를 일반적으로 확정하지 않고 자료 자체의 한계가 있다.',
                     'issuer_body_verified':False} for u,t,date in edges],
                'current_account_or_individual_applicability_verified':False,
                'investment_recommendation_approved':False,
                'reviewer':'CHATGPT_CURRENT_TURN','as_of':'2026-11-10'})

    def audit(self,**changes):
        kw=dict(sources=self.sources,exchanges=self.exchanges,
            original_reviews=self.old,master116=self.master,reassessments=self.rows,
            as_of='2026-11-10')
        kw.update(changes)
        with patch('ire.v6.chat_risk_reassessment_v34.audit_source_bound_chat_reviews_v33',
                   return_value={'host_open_items':2,'receipt_sha256':'a'*64}):
            return audit_two_open_original_claim_reassessments_v34(**kw)

    def test_only_conditional_classification_not_personal(self):
        r=self.audit()
        self.assertEqual(r['conditional_scope_reclassified_count'],2)
        self.assertEqual(r['unverified_current_individual_or_provider_cases'],2)
        self.assertFalse(r['master116_or_p4_auto_merge'])
        self.assertFalse(r['p0_go'])

    def test_cannot_make_personal_account_approval(self):
        rows=copy.deepcopy(self.rows)
        rows[0]['current_account_or_individual_applicability_verified']=True
        with self.assertRaisesRegex(InvalidInput,'V34_CONDITIONAL_EDUCATIONAL_CLAIM_NOT_SUPPORTED'):
            self.audit(reassessments=rows)

    def test_preserve_old_review_hash(self):
        rows=copy.deepcopy(self.rows)
        rows[0]['original_v33_review_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'V34_ORIGINAL_OPEN_REVIEW_HASH_DRIFT'):
            self.audit(reassessments=rows)

    def test_master116_tamper_rejected(self):
        rows=copy.deepcopy(self.rows)
        rows[0]['prior_master_row_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'V34_MASTER116_TARGET_REWRITE_OR_FORGERY'):
            self.audit(reassessments=rows)

    def test_no_current_statute_on_employer_case_rejected(self):
        rows=copy.deepcopy(self.rows)
        rows[1]['official_evidence'][0]['source_type']='FINANCIAL_INSTITUTION_POLICY'
        with self.assertRaisesRegex(InvalidInput,'V34_EMPLOYER_SECURITY_LAW_MISSING'):
            self.audit(reassessments=rows)

    def test_historical_provider_pdf_must_not_be_current_label(self):
        rows=copy.deepcopy(self.rows)
        rows[0]['official_evidence'][1]['source_type']='STATUTE_CURRENT'
        with self.assertRaisesRegex(InvalidInput,'V34_PROVIDER_CONTRAST_MISSING_HISTORICAL_LIMITATION'):
            self.audit(reassessments=rows)

    def test_evidence_future_dating_rejected(self):
        rows=copy.deepcopy(self.rows)
        rows[0]['official_evidence'][0]['published_or_effective_date']='2027-01-01'
        with self.assertRaisesRegex(InvalidInput,'V34_EVIDENCE_NOT_AUTHENTICATED_OR_DATE_WRONG'):
            self.audit(reassessments=rows)

    def test_false_external_reviewer_cannot_overwrite(self):
        rows=copy.deepcopy(self.rows)
        rows[0]['reviewer']='HUMAN_EXPERT'
        with self.assertRaisesRegex(InvalidInput,'V34_CONDITIONAL_EDUCATIONAL_CLAIM_NOT_SUPPORTED'):
            self.audit(reassessments=rows)


class FirstpassRealSourceSplitContractTests(unittest.TestCase):
    def setUp(self):
        from ire.v6.tests.test_source_and_proof import make_srt
        lines=['퇴직급여의 지급시기를 고릅니다.',
               '연금 계좌와 새 퇴직급여 수령을 구별합니다.',
               '새 계좌가 필요한지 질문합니다.',
               '만',
               '사업자의 계약 규정에 따라 다릅니다.',
               '현재 계좌 규칙은 별도로 확인해야 합니다.']
        raw=make_srt(lines,timestamps=[1000,2000,3000,4000,5000,6000])
        m=make_manifest(raw,cut=3)
        self.full=verify_source(raw,m,expected_source_sha256=sha256(raw),
                                expected_manifest_sha256=json_digest(m))
        part={**m,'scope':{'mode':'PARTIAL','first_cue':1,'last_cue':6}}
        self.partial=verify_source(raw,part,expected_source_sha256=sha256(raw),
                                expected_manifest_sha256=json_digest(part))
        old=[atom(self.full,'C00001',[1,2,3],[1,2,3],
                   'IRP 수령에 관한 여러 발화를 묶은 과거 미분할 문장이다.',stance='UNRESOLVED'),
             atom(self.full,'C00002',[5,6],[5,6],
                   '금융기관 계약별 차이가 있다는 긴 과거 설명이다.',stance='UNRESOLVED')]
        self.before=exchange(self.full,old)
        new=[atom(self.partial,f'C9000{i}',[j],[j],
                   '자막 원문의 부분 문장 내용을 분리해 설명한다.',stance='UNRESOLVED')
             for i,j in enumerate([1,2,3,5,6],1)]
        # The one-character ASR fragment cannot be quoted by V6, but stays
        # in the immediately related candidate's original context.
        new[2]['context_cue_indices']=[3,4]
        self.after=exchange(self.partial,new)
        self.links=[]
        before_cues={d['cue_index']:d['claim_ids'] for d in self.before['cue_dispositions']}
        for a in new:
            self.links.append({'claim_id':a['claim_id'],
              'old_provisional_ids':before_cues[a['source_refs'][0]['cue_index']],
              'new_claim_frame_sha256':json_digest(a),
              'chat_scope_note':'원문을 추적할 수 있는 좁은 발화 단위로만 나누었고 그 의미나 법률 효과는 확정하지 않았다.',
              'reviewer':'CHATGPT_CURRENT_TURN'})

    def audit(self,**kw):
        x=dict(full_source=self.full,full_draft_exchange=self.before,
               scoped_source=self.partial,scoped_chat_exchange=self.after,
               source_to_draft_links=self.links)
        x.update(kw)
        return audit_chat_firstpass_atomic_window_v34(**x)

    def test_source_first_split_preserves_old_anchor_without_gold(self):
        r=self.audit()
        self.assertEqual(r['former_v33_utterance_count'],2)
        self.assertEqual(r['new_host_firstpass_candidate_count'],5)
        self.assertEqual(r['new_source_cues_with_host_frames'],5)
        self.assertEqual(r['other_single_character_original_cues_context_only'],1)
        self.assertFalse(r['original_full_video_research_completed'])
        self.assertFalse(r['p0_go'])

    def test_old_cue_cannot_disappear_during_split(self):
        bad=exchange(self.partial,self.after['atoms'][:-1])
        with self.assertRaisesRegex(InvalidInput,'V34_SPLIT_OLD_CUE_ANCHORS_NOT_PRESERVED'):
            self.audit(scoped_chat_exchange=bad,source_to_draft_links=self.links[:-1])

    def test_parent_source_mapping_forgery_rejected(self):
        bad=copy.deepcopy(self.links)
        bad[0]['old_provisional_ids']=['C99999']
        with self.assertRaisesRegex(InvalidInput,'V34_SPLIT_SOURCE_PROVISIONAL_PARENT_DRIFT'):
            self.audit(source_to_draft_links=bad)

    def test_unreviewed_rewritten_chat_claim_sha_rejected(self):
        bad=copy.deepcopy(self.after)
        bad['atoms'][0]['proposition']='원래 발화와 다른 미래 성과를 확정한다는 주장이다.'
        with self.assertRaisesRegex(InvalidInput,'V34_SPLIT_SOURCE_PROVISIONAL_PARENT_DRIFT'):
            self.audit(scoped_chat_exchange=bad)

    def test_fake_independent_reviewer_cannot_grant_gold(self):
        bad=copy.deepcopy(self.links)
        bad[0]['reviewer']='INDEPENDENT_BLIND_HUMAN'
        with self.assertRaisesRegex(InvalidInput,'V34_SPLIT_SOURCE_PROVISIONAL_PARENT_DRIFT'):
            self.audit(source_to_draft_links=bad)

    def test_wrong_original_source_hash_rejected(self):
        bad=copy.deepcopy(self.after)
        bad['source_sha256']='0'*64
        with self.assertRaises(InvalidInput):
            self.audit(scoped_chat_exchange=bad)

    def test_one_character_as_original_quote_forbidden(self):
        bad=copy.deepcopy(self.after)
        bad['atoms'][2]['source_refs']=[{'cue_index':4,'quote':'만'}]
        with self.assertRaisesRegex(InvalidInput,'HOST_ATOM_QUOTE_NOT_IN_ORIGINAL'):
            self.audit(scoped_chat_exchange=bad)


if __name__=='__main__': unittest.main()
