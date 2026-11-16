"""V149 gold measurement and official HTTPS-body validation negative controls."""
from __future__ import annotations
import copy,hashlib,unittest,tempfile
from pathlib import Path
from unittest.mock import patch
from v149_research_gold_gate import score,GoldEvidenceError
from v149_official_https_body import SPECS,audit_original_bytes,OfficialBodyError,try_live_fetch

SRC='a'*64

def sha(s):return hashlib.sha256(s.encode()).hexdigest()

class V149GoldAndOfficialTests(unittest.TestCase):
    def setUp(self):
        self.original=[{'cue_index':i,'text':t,'sha256':sha(t)} for i,t in enumerate(['투자 위험','고위험 조건','따라서 분산'],1)]
        self.gold={'schema':'IRE_V149_SOURCE_FIRST_GOLD_V1','source_sha256':SRC,'scope':[1,3],
            'review_independence':'SAME_CHAT_SOURCE_FIRST_NOT_EXTERNAL',
            'cue_dispositions':[{'cue_index':x['cue_index'],'cue_text_sha256':x['sha256'],'role':'ASSERTION','review_note':'source-only test'} for x in self.original],
            'atoms':[{'gold_id':'G1','proposition':'첫 투자 원칙은 조건부다','cue_indices':[1,2],'high_risk':True},
                     {'gold_id':'G2','proposition':'둘째 원칙은 분산이다','cue_indices':[3],'high_risk':True}]}
        self.pred={'schema':'IRE_V149_PRIOR_V6_PREDICTION_V1','source_sha256':SRC,'scope':[1,3],
            'atoms':[{'predicted_id':'C1','proposition':'첫째 조건부 투자 원칙','cue_indices':[1,2],'high_risk':True},
                     {'predicted_id':'C2','proposition':'둘째 분산 투자 원칙','cue_indices':[3],'high_risk':True}]}
        self.adj={'schema':'IRE_V149_EXACT_ATOMIC_ADJUDICATION_V1','source_sha256':SRC,'scope':[1,3],
            'exact_matches':[{'gold_id':'G1','predicted_id':'C1','proposition_and_conditions_equivalent':True,'chat_decision_sha256':sha('test blind match')},
                             {'gold_id':'G2','predicted_id':'C2','proposition_and_conditions_equivalent':True,'chat_decision_sha256':sha('test blind match two')}],
            'unmatched_gold_ids':[],'unmatched_prediction_ids':[],
            'review_executor':'CHATGPT_IN_CHAT','reviewer_fully_checked_scope':True}
    def run_score(self, gold=None,pred=None,adj=None,src=None):
        return score(gold or self.gold,pred or self.pred,adj or self.adj,original_cues=src or self.original,
                     expected_scope=(1,3),original_source_sha256=SRC,whole_video_cue_count=1481)
    def test_01_true_one_to_one_slice_does_not_certify_entire_video(self):
        out=self.run_score()
        self.assertEqual(out['tp_exact'],2);self.assertEqual(out['precision'],1);self.assertEqual(out['recall'],1)
        self.assertFalse(out['p0_e_pass']);self.assertFalse(out['independently_certified']);self.assertFalse(out['full_video_complete'])
    def test_02_merged_claim_counts_false_positive_and_false_negative(self):
        pred=copy.deepcopy(self.pred);pred['atoms']=[pred['atoms'][0]]
        adj=copy.deepcopy(self.adj);adj['exact_matches']=adj['exact_matches'][:1]
        adj['unmatched_gold_ids']=['G2'];adj['unmatched_prediction_ids']=[]
        out=self.run_score(pred=pred,adj=adj)
        self.assertEqual((out['tp_exact'],out['fn_unmatched'],out['high_risk_fn_unmatched']),(1,1,1))
    def test_03_wrong_source_sha_fails(self):
        g=copy.deepcopy(self.gold);g['source_sha256']='0'*64
        with self.assertRaisesRegex(GoldEvidenceError,'SOURCE_DRIFT'):self.run_score(gold=g)
    def test_04_missing_cue_gold_census_fails(self):
        g=copy.deepcopy(self.gold);g['cue_dispositions'].pop()
        with self.assertRaisesRegex(GoldEvidenceError,'GOLD_NOT_FULL_CUE_CENSUS'):self.run_score(gold=g)
    def test_05_one_to_many_fake_matches_not_tp(self):
        a=copy.deepcopy(self.adj);a['exact_matches'][1]['predicted_id']='C1'
        with self.assertRaisesRegex(GoldEvidenceError,'MATCH_NOT_ONE_TO_ONE'):self.run_score(adj=a)
    def test_06_partial_cannot_be_passed(self):
        a=copy.deepcopy(self.adj);a['exact_matches'][0]['proposition_and_conditions_equivalent']=False
        with self.assertRaisesRegex(GoldEvidenceError,'PARTIAL_CANNOT_BE_TP'):self.run_score(adj=a)
    def test_07_mislabeled_high_risk_is_rejected(self):
        g=copy.deepcopy(self.gold);g['atoms'][0]['high_risk']=None
        with self.assertRaisesRegex(GoldEvidenceError,'HIGH_RISK_CLASSIFICATION_MISSING'):self.run_score(gold=g)
    def test_08_original_cue_tamper_fails(self):
        source=copy.deepcopy(self.original);source[0]['text']='변조됨'
        with self.assertRaisesRegex(GoldEvidenceError,'OWNER_CUE_TAMPERED'):self.run_score(src=source)

    @staticmethod
    def legal_bytes(rule):
        s=SPECS[rule]
        d=s['effective'];yy,mm,dd=(int(x) for x in d.split('-'))
        return ('<html><head><title>공식 법률 시험 자료</title></head><body>'+
                s['law']+f' [시행 {yy}. {mm}. {dd}.] '+s['article']+' '.join(s['terms'])+
                ' 본 문서는 단지 원문 검사 테스트를 위한 인위적 본문입니다.</body></html>').encode()
    def test_09_test_html_literal_rehashed_does_not_certify_issuer(self):
        law='PENSION_59_3';url=SPECS[law]['url']
        out=audit_original_bytes(law,self.legal_bytes(law),requested_url=url,final_url=url,captured_on='2026-11-16',as_of='2026-11-16')
        self.assertTrue(out['original_http_bytes_locally_rehashed'])
        self.assertFalse(out['issuer_digitally_signed_body_verified']);self.assertFalse(out['tls_session_executed_by_this_function'])
        self.assertFalse(out['individual_account_or_tax_eligibility_verified']);self.assertFalse(out['p0_e_go'])
    def test_10_host_mismatch_blocked(self):
        law='ISA_91_18';url=SPECS[law]['url']
        with self.assertRaises(OfficialBodyError):audit_original_bytes(law,self.legal_bytes(law),requested_url=url,final_url='https://evil.example/steal',captured_on='2026-11-16',as_of='2026-11-16')
    def test_11_wrong_effective_date_blocked(self):
        law='ISA_91_18';url=SPECS[law]['url']
        raw=self.legal_bytes(law).replace(b'2026. 9. 18.',b'2027. 9. 18.')
        with self.assertRaisesRegex(OfficialBodyError,'EFFECTIVE_DATE_NOT_IN_ORIGINAL_BYTES'):
            audit_original_bytes(law,raw,requested_url=url,final_url=url,captured_on='2026-11-16',as_of='2026-11-16')
    def test_12_article_not_present_blocked(self):
        law='ISA_91_18';url=SPECS[law]['url']
        raw=self.legal_bytes(law).replace('제91조의18'.encode(),'제91조의19'.encode())
        with self.assertRaisesRegex(OfficialBodyError,'ARTICLE_OR_LITERAL_NOT_IN_BYTES'):
            audit_original_bytes(law,raw,requested_url=url,final_url=url,captured_on='2026-11-16',as_of='2026-11-16')
    def test_13_captured_after_asof_blocked(self):
        law='PENSION_59_3';url=SPECS[law]['url']
        with self.assertRaisesRegex(OfficialBodyError,'FUTURE_EFFECTIVE_OR_CAPTURE'):
            audit_original_bytes(law,self.legal_bytes(law),requested_url=url,final_url=url,captured_on='2026-12-01',as_of='2026-11-16')

    def test_14_synthetic_tls_fetch_preserves_exact_raw_body_for_rehash(self):
        class H:
            def get_content_type(self):return 'text/html'
        class R:
            status=200;headers=H()
            def __enter__(self):return self
            def __exit__(self,*a):return False
            def geturl(self):return SPECS['PENSION_59_3']['url']
            def read(self,n):return V149GoldAndOfficialTests.legal_bytes('PENSION_59_3')
        class Opener:
            def open(self,*a,**k):return R()
        with tempfile.TemporaryDirectory() as temp,patch('urllib.request.build_opener',return_value=Opener()):
            got=try_live_fetch('PENSION_59_3',as_of='2026-11-16',raw_store=Path(temp))
            self.assertTrue(got['original_raw_artifact_rehashed'])
            self.assertTrue(got['tls_session_executed_by_this_function'])
            self.assertEqual(hashlib.sha256((Path(temp)/got['original_raw_artifact_filename']).read_bytes()).hexdigest(),got['body_sha256'])
            self.assertFalse(got['issuer_digitally_signed_body_verified'])
            self.assertFalse(got['p0_e_go'])

    def test_15_blocked_https_fetch_never_falls_back_to_search_excerpt(self):
        class Blocked:
            def open(self,*a,**k):raise OSError('synthetic network denied')
        with tempfile.TemporaryDirectory() as temp,patch('urllib.request.build_opener',return_value=Blocked()):
            got=try_live_fetch('ISA_91_18',raw_store=Path(temp))
            self.assertEqual(got['status'],'OFFICIAL_RAW_SOURCE_UNAVAILABLE_HOLD')
            self.assertIsNone(got['body_sha256'])
            self.assertFalse(list(Path(temp).iterdir()))

if __name__=='__main__':unittest.main()
