"""V35 37/40 source-scoped synthetic regression, NOT independent semantic gold."""
from __future__ import annotations

import copy
import unittest

from ire.v6.codec import json_digest,sha256
from ire.v6.errors import InvalidInput
from ire.v6.tests.test_stage_repair import atom, exchange
from ire.v6.chat_risk_resolution_v35 import (
    audit_source_first_remaining_37_v35,RESOLVED,OPEN)


class V35RiskResolutionTests(unittest.TestCase):
    def setUp(self):
        from ire.v6.tests.test_chat_risk_reassessment_v34 import Original40ChatRiskDocketTests
        old=Original40ChatRiskDocketTests('test_all_synthetic_40_source_bound_without_certification')
        old.setUp()
        self.sources=old.sources
        self.before=old.exchanges
        self.rows=copy.deepcopy(old.rows)
        # Exactly 3 discourse-only and 37 previously open alerts.
        for i,row in enumerate(self.rows):
            if i>=3:
                row['classification']='INVESTMENT_CONDITION_OR_FORECAST_OPEN'
        self.master=[{'claim_id':f'GOMHEE-C{i:02d}',
                      'claim':f'합성 전용 기준 지식 {i}'} for i in range(1,117)]
        self.replays=[];self.decisions=[]
        for case_no,row in enumerate(self.rows[3:],1):
            src=self.sources[row['video_id']]
            idx=row['case_cue_index']
            # Unique across 37 scopes, two children, anchored to original cue.
            cl1=f'C{70000+2*case_no:05d}'
            cl2=f'C{70001+2*case_no:05d}'
            new=[atom(src,cl1,[idx-1],[idx-1,idx],
                      '해당 투자 의견의 전제를 설명한다.',stance='UNRESOLVED'),
                 atom(src,cl2,[idx],[idx,idx+1],
                      '하지만 투자 결과가 달라질 수 있다는 반론이다.',stance='UNRESOLVED')]
            ex=exchange(src,new)
            for r in ex['cue_dispositions']:
                if r['disposition']=='NO_ATOM':
                    r['disposition']='UNRESOLVED'
            self.replays.append({'video_id':src.video_id,'hinge_cue':idx,
                                 'source':src,'exchange':ex,
                                 'case_sha256_list':[row['case_sha256']]})
            m=self.master[12]
            self.decisions.append({
                'video_id':src.video_id,'case_sha256':row['case_sha256'],
                'hinge_cue_index':idx,
                'scoped_candidate_sha256':__import__('ire.v6.atomic_exchange',fromlist=['audit_host_atomic_exchange']).audit_host_atomic_exchange(src,ex)['atom_candidate_digest'],
                'original_draft_atom_sha256':row['draft_claim_frame_sha256'],
                'source_meaning_status':RESOLVED if case_no<=24 else OPEN,
                'bounded_semantic_explanation':'원문 발화의 대조와 조건을 분할하여 화자 의견으로만 분류한다. 금융상품의 현재 실현 수익이나 미래 손익은 이 표현만으로 확정할 수 없다.',
                'remaining_limit':'독립 검토와 현재 금융기관 계약 적용성, 음성 대조가 미완료이다.',
                'master_claim_id':m['claim_id'],
                'master_row_sha256':json_digest(m),
                'prior_knowledge_relation':'SUPPORTS_PRIOR_CHAT_ONLY' if case_no<=22 else 'POTENTIAL_PRIOR_LINK_OPEN',
                'official_evidence':[],
                'reviewer':'CHATGPT_CURRENT_TURN','as_of':'2026-11-10'})
        assert len(self.decisions)==37

    def audit(self,**changes):
        args={'sources':self.sources,'baseline_exchanges':self.before,
              'v34_rows':self.rows,'scoped_replays':self.replays,
              'host_case_reviews':self.decisions,'master116':self.master,
              'as_of':'2026-11-10',
              'expected_master116_rows_digest':json_digest(self.master)}
        args.update(changes)
        return audit_source_first_remaining_37_v35(**args)

    def test_original37_all_mapped_with_two_children_each(self):
        r=self.audit()
        self.assertEqual((r['reviewed_source_case_count'],r['new_provisional_child_claim_frames']), (37,74))
        self.assertEqual((r['chat_source_meaning_resolved_education_only'],r['risk_cases_retained_open_after_chat_review']),(24,13))
        self.assertFalse(r['p0_go'])
        self.assertFalse(r['all_130_original_windows_semantically_complete'])

    def test_missing_case_fails_closed(self):
        with self.assertRaisesRegex(InvalidInput,'V35_ALL37_CHAT_DECISIONS_REQUIRED'):
            self.audit(host_case_reviews=self.decisions[:-1])

    def test_duplicate_case_cannot_cover_missing_one(self):
        bad=copy.deepcopy(self.decisions)
        bad[-1]=bad[0]
        with self.assertRaisesRegex(InvalidInput,'V35_CHAT_CASE_MISSING_OR_DUPLICATE'):
            self.audit(host_case_reviews=bad)

    def test_changed_original_claim_identity_fails(self):
        bad=copy.deepcopy(self.decisions)
        bad[0]['original_draft_atom_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'V35_CHAT_CASE_OR_CHILD_LINEAGE_DRIFT'):
            self.audit(host_case_reviews=bad)

    def test_claim_child_frame_hash_tampering_fails(self):
        bad=copy.deepcopy(self.decisions)
        bad[0]['scoped_candidate_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'V35_CHAT_CASE_OR_CHILD_LINEAGE_DRIFT'):
            self.audit(host_case_reviews=bad)

    def test_source_cue_tamper_fails_before_assessing_meaning(self):
        bad=copy.deepcopy(self.replays)
        bad[0]['exchange']['atoms'][0]['source_refs'][0]['quote']='NOT ORIGINAL'
        with self.assertRaisesRegex(InvalidInput,'HOST_ATOM_QUOTE_NOT_IN_ORIGINAL'):
            self.audit(scoped_replays=bad)

    def test_old_risk_docket_cannot_be_rewritten(self):
        bad=copy.deepcopy(self.rows)
        bad[3]['case_cue_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'V34_RISK_ORIGINAL_CUE_OR_CONTEXT_CHANGED'):
            self.audit(v34_rows=bad)

    def test_unverified_asr_auto_resolved_is_rejected(self):
        bad=copy.deepcopy(self.rows)
        bad[3]['classification']='ASR_OR_SPEAKER_UNCERTAINTY_OPEN'
        with self.assertRaisesRegex(InvalidInput,'V35_UNVERIFIED_ASR_MUST_REMAIN_OPEN'):
            self.audit(v34_rows=bad)

    def test_legal_fact_claim_without_current_primary_evidence_rejected(self):
        bad=copy.deepcopy(self.rows)
        bad[3]['classification']='FINANCIAL_TAX_OR_LEGAL_SCOPE_OPEN'
        with self.assertRaisesRegex(InvalidInput,'V35_LEGAL_CURRENT_SCOPE_WITHOUT_PRIMARY_EVIDENCE'):
            self.audit(v34_rows=bad)

    def test_current_law_issuer_authentication_must_not_be_faked(self):
        bad=copy.deepcopy(self.decisions)
        bad[0]['official_evidence']=[{'url':'https://www.law.go.kr/lsInfoP.do?lsiSeq=284455',
            'retrieved_on':'2026-11-10',
            'scope':'이것은 합성 근거이고 개별 상황에 적용된 진짜 법률 인증은 하지 않는다.',
            'independent_issuer_body_verified':True}]
        with self.assertRaisesRegex(InvalidInput,'V35_PRIMARY_EVIDENCE_SCOPE_OR_PROVENANCE_INVALID'):
            self.audit(host_case_reviews=bad)

    def test_master_row_sha_tampering_fails(self):
        bad=copy.deepcopy(self.decisions)
        bad[0]['master_row_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'V35_PRIOR116_RELATION_NOT_SOURCE_BOUND'):
            self.audit(host_case_reviews=bad)

    def test_master116_row_set_drift_fails_before_claim_relations(self):
        bad=copy.deepcopy(self.master)
        bad[12]['claim']='합성 기준 지식 자체를 바꾼 공격'
        with self.assertRaisesRegex(InvalidInput,'V35_MASTER116_ROWS_PIN_MISMATCH'):
            self.audit(master116=bad)

    def test_wrong_ledger_expected_digest_fails(self):
        with self.assertRaisesRegex(InvalidInput,'V35_MASTER116_ROWS_PIN_MISMATCH'):
            self.audit(expected_master116_rows_digest='0'*64)

    def test_claim_reviewer_cannot_claim_external_expert_independence(self):
        bad=copy.deepcopy(self.decisions)
        bad[0]['reviewer']='INDEPENDENT_EXPERT'
        with self.assertRaisesRegex(InvalidInput,'V35_CHAT_MEANING_OR_STATUS_INVALID'):
            self.audit(host_case_reviews=bad)

    def test_invalid_case_reclassification_rejected(self):
        bad=copy.deepcopy(self.decisions)
        bad[0]['source_meaning_status']='INDEPENDENT_GOLD_GO'
        with self.assertRaisesRegex(InvalidInput,'V35_CHAT_MEANING_OR_STATUS_INVALID'):
            self.audit(host_case_reviews=bad)

    def test_wrong_scoped_video_sha_rejected(self):
        bad=copy.deepcopy(self.replays)
        bad[0]['video_id']='OUTSIDE_SOURCE'
        with self.assertRaisesRegex(InvalidInput,'V35_HINGE_VIDEO_OR_GROUP_DUPLICATE'):
            self.audit(scoped_replays=bad)

    def test_duplicate_child_atom_id_across_two_replays_rejected(self):
        bad=copy.deepcopy(self.replays)
        bad[1]['exchange']['atoms'][0]['claim_id']=bad[0]['exchange']['atoms'][0]['claim_id']
        for r in bad[1]['exchange']['cue_dispositions']:
            r['claim_ids']=[bad[0]['exchange']['atoms'][0]['claim_id'] if x==self.replays[1]['exchange']['atoms'][0]['claim_id'] else x for x in r['claim_ids']]
        with self.assertRaisesRegex(InvalidInput,'V35_DUPLICATE_CHILD_ID_ACROSS_SCOPED_REPLAYS'):
            self.audit(scoped_replays=bad)

    def test_no_semantic_certification_even_with_all_source_reviews(self):
        x=self.audit()
        self.assertFalse(x['independent_gold_precision_recall_measured'])
        self.assertFalse(x['official_issuer_document_body_independently_authenticated'])
        self.assertFalse(x['master116_auto_merge_approved'])
        self.assertFalse(x['personal_tax_or_trade_approved'])


if __name__=='__main__':
    unittest.main()
