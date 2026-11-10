"""V36 synthetic-only adversarial tests, never external gold or owner-original."""
from __future__ import annotations
import copy
import unittest
from unittest.mock import patch
from ire.v6 import chat_scope_disposition_v36 as m
from ire.v6.source import Cue
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput


class V36ChatScopeDispositionsTest(unittest.TestCase):
    def setUp(self):
        # Source-free synthetic boundary with SAME public case SHA IDs, but no
        # user-private original speech in CI. Local private ZIP replay is separate.
        indexes={vid:set() for vid in m.VIDEO_HASHES}
        for vid,idx in m._CONTEXT:
            indexes[vid].add(idx)
        src={}
        pins={}
        for vid,ids in indexes.items():
            end=max(m._CONTEXT[(vid,n)][1] for n in ids)
            rows=[Cue(i, i*1000,(i+1)*1000,'synthetic-context-placeholder') for i in range(1,end+1)]
            for idx in ids:
                kind=m._CONTEXT[(vid,idx)][2]
                rows[idx-1]=Cue(idx,idx*1000,(idx+1)*1000,
                                ' '.join(m._MARKERS[kind])+' 합성 위험·조건 원문 대조입니다.')
                pins[(vid,idx)]=sha256(rows[idx-1].text.encode())
            src[vid]=tuple(rows)
        self.sources=src;self.pins=pins
        self.parents=[];self.reviews=[]
        for case,t in m.TARGETS.items():
            vid,idx=t['video_id'],t['hinge_cue'];kind=m._CONTEXT[(vid,idx)][2]
            start,end,_=m._CONTEXT[(vid,idx)]
            context=' '.join(src[vid][i-1].text for i in range(start,end+1))
            child=m._CHILD_PINS[(vid,idx)]
            self.parents.append({'original_case_sha256':case,'video_id':vid,
                'source_hinge_cue_index':idx,
                'child_candidate_digest':child,
                'master_claim_id':t['master_claim_id'],
                'master_row_sha256':t['master_row_sha256'],
                'financial_fact_truth_certified':False,
                'combined_source_and_prior_review_status':(
                    'ORIGINAL_ASR_OR_FINANCIAL_SCOPE_STILL_OPEN' if kind in m._SCOPE_KINDS
                    else 'PRIOR_RELATION_REVIEW_REQUIRED')})
            relations={
              'TAX_POLICY_INVESTING_POSTURE':'TOPICALLY_DISTINCT_NO_EQUIVALENCE',
              'PERSONAL_STOCK_COUNT_PREFERENCE':'PERSONAL_PREFERENCE_NOT_ASSET_ALLOCATION_RULE',
              'IRP_ONE_MAN_WON_EARLY_START':'PROVIDER_CASE_NOT_DECUMULATION_EQUIVALENCE',
              'LOSS_POSITION_HOLD_EXPERIENCE':'CONDITIONAL_BEHAVIORAL_RELATION_NOT_EQUIVALENT',
            }
            urls=['https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6434'] if 'PENSION' in kind or 'WITHDRAWAL' in kind else (
              ['https://blog.kbsec.com/finance/cma'] if kind=='CMA_HISTORICAL_RATE' else [])
            self.reviews.append({'video_id':vid,'case_sha256':case,'hinge_cue':idx,
               'cue_sha256':pins[(vid,idx)],'context_first':start,'context_last':end,
               'context_sha256':sha256(context.encode()),
               'parent_child_digest':child,'master_claim_id':t['master_claim_id'],
               'master_row_sha256':t['master_row_sha256'],
               'meaning_kind':kind,
               'disposition':'SCOPED_HISTORICAL_EDUCATION_ONLY' if kind in m._SCOPE_KINDS
                             else 'DISTINCT_PRIOR_RELATION_REVIEWED_CHAT_ONLY',
               'prior_relation':'TOPICALLY_RELATED_NOT_MASTER_EQUIVALENCE' if kind in m._SCOPE_KINDS
                               else relations[kind],
               'reason':'본 합성자료는 앞뒤 맥락을 확인한 것으로 가정하지만 실제 녹음이나 개인 거래의 사실을 검증하지 않았고 수익 및 과세 적용을 인증하지 않는다.',
               'current_rule_urls':urls,'last_checked':'2026-11-11',
               'independent_audio_checked':False,'current_broker_contract_verified':False,
               'financial_fact_certified':False,'master_auto_merge':False,
               'personal_tax_or_trade_approval':False})

    def audit(self,**overrides):
        values={'sources':self.sources,'parent_rows':self.parents,'host_rows':self.reviews,
                'current_as_of':'2026-11-11','parent_receipt_sha256':m.V35_RECEIPT_SHA,
                'master116_rows_digest':m.MASTER116_ROOT_SHA}
        values.update(overrides)
        with patch.object(m,'_CUE_PINS',self.pins):
            return m.audit_chat_disposition_v36(**values)

    def test_thirteen_scope_classifications_not_truth_certification(self):
        r=self.audit()
        self.assertEqual(r['host_scope_decisions_recorded'],13)
        self.assertEqual(r['semantic_scope_dispositions_remaining_unreviewed'],0)
        self.assertEqual(r['source_audio_or_current_product_terms_still_unverified'],8)
        self.assertFalse(r['p0_go'])
        self.assertFalse(r['independent_gold_precision_recall_measured'])

    def test_no_proposition_or_raw_transcript_in_public_receipt(self):
        r=self.audit()
        self.assertTrue(all('reason' not in x and 'quote' not in x for x in r['reviewed_cases']))
        self.assertTrue(all('host_reason_sha256' in x for x in r['reviewed_cases']))

    def test_missing_last_host_case_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'V36_EXACT_THIRTEEN_REQUIRED'):
            self.audit(host_rows=self.reviews[:-1])

    def test_missing_prior_case_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'V36_EXACT_THIRTEEN_REQUIRED'):
            self.audit(parent_rows=self.parents[:-1])

    def test_duplicate_case_rejected(self):
        rows=copy.deepcopy(self.reviews);rows[1]=rows[0]
        with self.assertRaisesRegex(InvalidInput,'V36_REVIEW_DUPLICATE_OR_UNKNOWN_CASE'):
            self.audit(host_rows=rows)

    def test_tampered_parent_case_identity_rejected(self):
        rows=copy.deepcopy(self.parents);rows[0]['master_row_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'V36_PARENT_V35_CASE_HASH_LINEAGE_DRIFT'):
            self.audit(parent_rows=rows)

    def test_tampered_child_hash_rejected(self):
        rows=copy.deepcopy(self.reviews);rows[0]['parent_child_digest']='f'*64
        with self.assertRaisesRegex(InvalidInput,'V36_ORIGINAL_OR_PRIOR_MEANING_LINEAGE_DRIFT'):
            self.audit(host_rows=rows)

    def test_context_cue_quote_tampered_rejected(self):
        src=copy.deepcopy(self.sources)
        vid,idx=self.reviews[0]['video_id'],self.reviews[0]['hinge_cue']
        rows=list(src[vid]);rows[idx-1]=Cue(idx,0,1000,'forged original quote');src[vid]=tuple(rows)
        with self.assertRaisesRegex(InvalidInput,'V36_ORIGINAL_CUE_SHA_DRIFT'):
            self.audit(sources=src)

    def test_context_window_drift_rejected(self):
        rows=copy.deepcopy(self.reviews);rows[0]['context_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'V36_BOUNDING_CONTEXT_HASH_DRIFT'):
            self.audit(host_rows=rows)

    def test_wrong_current_date_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'V36_ASOF_OR_PARENT_OR_MASTER_PIN_DRIFT'):
            self.audit(current_as_of='2026-11-10')

    def test_wrong_parent_receipt_digest_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'V36_ASOF_OR_PARENT_OR_MASTER_PIN_DRIFT'):
            self.audit(parent_receipt_sha256='0'*64)

    def test_fake_external_audio_verification_rejected(self):
        rows=copy.deepcopy(self.reviews);rows[0]['independent_audio_checked']=True
        with self.assertRaisesRegex(InvalidInput,'V36_UNSUPPORTED_FACT_OR_INDEPENDENCE_APPROVAL'):
            self.audit(host_rows=rows)

    def test_fake_current_broker_product_validation_rejected(self):
        rows=copy.deepcopy(self.reviews);rows[0]['current_broker_contract_verified']=True
        with self.assertRaisesRegex(InvalidInput,'V36_UNSUPPORTED_FACT_OR_INDEPENDENCE_APPROVAL'):
            self.audit(host_rows=rows)

    def test_forced_master_equivalence_rejected(self):
        rows=copy.deepcopy(self.reviews)
        row=next(x for x in rows if x['meaning_kind']=='PERSONAL_STOCK_COUNT_PREFERENCE')
        row['prior_relation']='EXACT_EQUAL_MASTER116_APPROVED'
        with self.assertRaisesRegex(InvalidInput,'V36_PRIOR_NON_EQUIVALENCE_NOT_ESTABLISHED'):
            self.audit(host_rows=rows)

    def test_unsupported_automated_master_merge_rejected(self):
        rows=copy.deepcopy(self.reviews);rows[0]['master_auto_merge']=True
        with self.assertRaisesRegex(InvalidInput,'V36_UNSUPPORTED_FACT_OR_INDEPENDENCE_APPROVAL'):
            self.audit(host_rows=rows)

    def test_missing_primary_tax_evidence_rejected(self):
        rows=copy.deepcopy(self.reviews)
        row=next(x for x in rows if x['meaning_kind']=='PENSION_TAX_OPTION')
        row['current_rule_urls']=[]
        with self.assertRaisesRegex(InvalidInput,'V36_TAX_REGULATION_PRIMARY_EVIDENCE_REQUIRED'):
            self.audit(host_rows=rows)

    def test_cma_historic_yield_requires_institutional_product_scope(self):
        rows=copy.deepcopy(self.reviews)
        row=next(x for x in rows if x['meaning_kind']=='CMA_HISTORICAL_RATE')
        row['current_rule_urls']=[]
        with self.assertRaisesRegex(InvalidInput,'V36_CMA_PRODUCT_PRIMARY_TYPE_EVIDENCE_REQUIRED'):
            self.audit(host_rows=rows)

    def test_forged_lookalike_primary_evidence_domain_rejected(self):
        rows=copy.deepcopy(self.reviews)
        row=next(x for x in rows if x['meaning_kind']=='PENSION_TAX_OPTION')
        row['current_rule_urls']=['https://www.nts.go.kr.evil.invalid/pretend-law']
        with self.assertRaisesRegex(InvalidInput,'V36_PRIMARY_EVIDENCE_URL_SCOPE_INVALID'):
            self.audit(host_rows=rows)

    def test_fabricated_parent_child_sha_is_not_accepted(self):
        parents=copy.deepcopy(self.parents);parents[0]['child_candidate_digest']='1'*64
        reviews=copy.deepcopy(self.reviews);reviews[0]['parent_child_digest']='1'*64
        with self.assertRaisesRegex(InvalidInput,'V36_PARENT_V35_CASE_HASH_LINEAGE_DRIFT'):
            self.audit(parent_rows=parents,host_rows=reviews)

    def test_forged_financial_certification_rejected(self):
        rows=copy.deepcopy(self.reviews);rows[0]['financial_fact_certified']=True
        with self.assertRaisesRegex(InvalidInput,'V36_UNSUPPORTED_FACT_OR_INDEPENDENCE_APPROVAL'):
            self.audit(host_rows=rows)


if __name__=='__main__':
    unittest.main()
