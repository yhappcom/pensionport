"""V118 isolated synthetic regression only; never embeds owner-private SRT."""
import copy, hashlib, json, os, sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v118_41_open_primary_scope_and_blind_gate import (
 audit_open_41, blind_packet, compare_against_synthetic_gold,
 sha,digest,OpenEvidenceFailure
)

ROOT=Path(__file__).resolve().parent
ATOMS=[f'A{i:03d}' for i in range(2,47) if i not in (7,26,33,38)]
assert len(ATOMS)==41
COUNTER={'A003','A012','A017','A021','A022','A028','A042','A044'}
SYNTHETIC_AIDS=['KRX_CURRENT_ETF_LISTING','KRX_HISTORICAL_RULE','KCMI_2026_RESEARCH',
                 'FSC_NXT_2025','LAW_246_2026_CURRENT','LAW_192_2026_CURRENT',
                 'LAW_EXEC_223_2026','KRX_PRICE_TRACK','KRX_RISK','KRX_ETF_BOND',
                 'NABO_TAX_POINTER','ISSUER_TAX_POINTER']
URLS={
 'KRX_CURRENT_ETF_LISTING':('EXCHANGE_PRIMARY_WEB','https://listing.krx.co.kr/rule','LIVE_PAGE_READ'),
 'KRX_HISTORICAL_RULE':('EXCHANGE_OLD_REVISION','https://law.krx.co.kr/archive','INDEXED_2022_ONLY'),
 'KCMI_2026_RESEARCH':('INDEPENDENT_RESEARCH_SECONDARY','https://www.kcmi.re.kr/p','DIRECT_INDEXED'),
 'FSC_NXT_2025':('GOV_REGULATOR_PRIMARY_WEB','https://www.fsc.go.kr/release','LIVE_PAGE_READ'),
 'LAW_246_2026_CURRENT':('LEGISLATIVE_PRIMARY_WEB','https://www.law.go.kr/246','INDEXED_CURRENT_CLAUSE'),
 'LAW_192_2026_CURRENT':('LEGISLATIVE_PRIMARY_WEB','https://www.law.go.kr/192','INDEXED_CURRENT_CLAUSE'),
 'LAW_EXEC_223_2026':('LEGISLATIVE_PRIMARY_WEB','https://law.go.kr/223','INDEXED_2026_CLAUSE'),
 'KRX_PRICE_TRACK':('EXCHANGE_PRIMARY_WEB','https://www.krx.co.kr/nav','INDEXED_PAGE'),
 'KRX_RISK':('EXCHANGE_PRIMARY_WEB','https://open.krx.co.kr/risk','INDEXED_PAGE'),
 'KRX_ETF_BOND':('EXCHANGE_PRODUCT_DISCLOSURE','https://kind.krx.co.kr/bond','INDEXED_PRODUCT_DOCUMENT'),
 'NABO_TAX_POINTER':('FISCAL_SECONDARY','https://korea.nabo.go.kr/tax','NO_PRODUCT_BINDING'),
 'ISSUER_TAX_POINTER':('ISSUER_PRODUCT_DISCLOSURE','https://m.samsungfund.com/bond','NO_PRODUCT_BINDING')
}

def fixture():
    atoms=[];old=[];triage=[]
    for i,aid in enumerate(ATOMS,1):
        risk='CRITICAL' if aid in COUNTER else 'HIGH' if i%7==0 else 'LOW'
        prop=f'SYNTHETIC ONLY review source statement number {i}.'
        a={'atom_id':aid,'cue_indices':[i],'source_span_sha256':sha(f'span{i}'),
           'proposition_private':prop,'risk':risk,'evidence_key':'KRX'}
        atoms.append(a)
        old.append({'atom_id':aid,'cue_indices':[i],
           'evidence_status':'OPEN_PRIMARY_BODY_AND_APPLICABILITY'})
        refs=['KRX_CURRENT_ETF_LISTING']
        if aid in ('A003','A004'): refs=['FSC_NXT_2025']
        if aid in ('A034','A035','A036','A042'):refs=['LAW_246_2026_CURRENT']
        if aid=='A012':refs=['KRX_CURRENT_ETF_LISTING','KRX_PRICE_TRACK']
        if aid=='A028':refs=['KCMI_2026_RESEARCH']
        if aid=='A032':refs=['NABO_TAX_POINTER','ISSUER_TAX_POINTER']
        triage.append({'atom_id':aid,'source_cue_indices':[i],
         'source_span_sha256':a['source_span_sha256'],
         'proposition_digest_sha256':sha(prop),'risk':risk,
         'review_class':'COUNTEREVIDENCE_OR_OVERGENERALIZATION' if aid in COUNTER else
                 'PRODUCT_ACCOUNT_TAX_SCOPE_MISSING' if aid=='A032' else
                 'QUALIFICATION_REQUIRED',
         'authority_keys':refs,
         'reviewer_reason_private':f'Synthetic check with source clause and exception, id={aid}',
         'source_date_as_of':'2026-11-15',
         'original_docket_status':'OPEN_PRIMARY_BODY_AND_APPLICABILITY',
         'primary_body_frozen_exact_bytes':False,'independent_source_adjudicated':False,
         'current_rule_version_fully_verified':False,'financial_fact_approved':False,
         'personal_application_approved':False,'final_status':'OPEN_NOT_FOR_PERSONAL_ADVICE'})
    graph={'video_id':'Yb_5prWaqhk','atoms':atoms}
    registry=[{'id':k,'url':v[1],'issuer_class':v[0],'retrieval':v[2],
      'scope_summary':f'SYNTHETIC scope note representing a {k} reference.',
      'issuer_http_body_sha256':None,'legal_version_fully_verified':False,
      'finance_approved':False,'checked_as_of':'2026-11-15'} for k,v in URLS.items()]
    ledger={'schema':'V118_PRIVATE_41_OPEN_ATOM_OFFICIAL_SCOPE_TRIAGE_V1',
    'video_id':'Yb_5prWaqhk','as_of':'2026-11-15',
    'v117_graph_sha256':digest(graph),'v117_docket_sha256':digest(old),
    'authority_register':registry,'rows':triage,'independent_gold':False,
    'all_finance_facts_approved':False,'primary_full_http_body_sha_verified':False,
    'formal_closed_items':0,'pending_items':41,'personal_advice_authorized':False}
    return graph,old,ledger

class V118SyntheticGate(unittest.TestCase):
    def setUp(self):self.graph,self.original,self.ledger=fixture()
    def audit(self):return audit_open_41(graph=self.graph,original_docket=self.original,ledger=self.ledger)
    def reject(self,code=None):
        with self.assertRaises(OpenEvidenceFailure) as cm:self.audit()
        if code:self.assertIn(code,str(cm.exception))
    def test_01_baseline(self):
        x=self.audit();self.assertEqual((x['source_41_reviewed'],x['financial_remaining_open']), (41,41));self.assertEqual(x['formal_finance_approvals'],0)
    def test_02_no_gold(self):self.assertIsNone(self.audit()['precision'])
    def test_03_no_model_time(self):self.assertIsNone(self.audit()['model_review_wall_ns'])
    def test_04_no_go(self):self.assertFalse(self.audit()['p0_go'])
    def test_05_no_personal_advice(self):self.assertFalse(self.audit()['ready_for_personal_advice'])
    def test_06_bad_schema(self):self.ledger['schema']='V117';self.reject('SCHEMA')
    def test_07_false_independent_gold(self):self.ledger['independent_gold']=True;self.reject('FALSE_GO')
    def test_08_false_fact_approval(self):self.ledger['all_finance_facts_approved']=True;self.reject('FALSE_GO')
    def test_09_false_primary_http_pin(self):self.ledger['primary_full_http_body_sha_verified']=True;self.reject('FALSE_GO')
    def test_10_false_closed(self):self.ledger['formal_closed_items']=41;self.reject('FALSE_GO')
    def test_11_false_pending_count(self):self.ledger['pending_items']=0;self.reject('FALSE_GO')
    def test_12_false_personal_advice(self):self.ledger['personal_advice_authorized']=True;self.reject('FALSE_GO')
    def test_13_wrong_video(self):self.ledger['video_id']='ABCDEFGHIJK';self.reject('VIDEO_SCOPE')
    def test_14_wrong_date(self):self.ledger['as_of']='2025-11-15';self.reject('AS_OF_DATE')
    def test_15_forged_graph(self):self.graph['atoms'][0]['proposition_private']='HACK';self.reject('SOURCE_LEDGER_DIGEST')
    def test_16_forged_docket(self):self.original[0]['cue_indices']=[6];self.reject('SOURCE_LEDGER_DIGEST')
    def test_17_wrong_source_cue(self):self.ledger['rows'][0]['source_cue_indices']=[100];self.reject('TRIAGE_SOURCE')
    def test_18_wrong_source_digest(self):self.ledger['rows'][0]['source_span_sha256']='0'*64;self.reject('TRIAGE_SOURCE')
    def test_19_wrong_proposition_digest(self):self.ledger['rows'][0]['proposition_digest_sha256']='0'*64;self.reject('TRIAGE_SOURCE')
    def test_20_forged_risk(self):self.ledger['rows'][0]['risk']='LOW' if self.ledger['rows'][0]['risk']=='HIGH' else 'HIGH';self.reject('TRIAGE_SOURCE')
    def test_21_missing_case(self):self.ledger['rows'].pop();self.reject('REVIEW_41')
    def test_22_duplicate_case(self):self.ledger['rows'][1]=copy.deepcopy(self.ledger['rows'][0]);self.reject('TRIAGE_DUPLICATE')
    def test_23_unknown_case(self):self.ledger['rows'][1]['atom_id']='A900';self.reject('TRIAGE_DUPLICATE')
    def test_24_counterevidence_hidden(self):next(x for x in self.ledger['rows'] if x['atom_id']=='A017')['review_class']='GENERAL_SUPPORT_PENDING_LEGAL_FINAL';self.reject('HIGH_RISK_COUNTEREVIDENCE_SILENCED')
    def test_25_tax_becomes_approved(self):next(x for x in self.ledger['rows'] if x['atom_id']=='A032')['financial_fact_approved']=True;self.reject('UNSUPPORTED_FINANCE_APPROVAL')
    def test_26_tax_false_scope(self):next(x for x in self.ledger['rows'] if x['atom_id']=='A032')['review_class']='QUALIFICATION_REQUIRED';self.reject('TAX_SCOPE_FABRICATED')
    def test_27_tax_unlink_product(self):next(x for x in self.ledger['rows'] if x['atom_id']=='A032')['authority_keys']=['NABO_TAX_POINTER'];self.reject('TAX_SCOPE_FABRICATED')
    def test_28_krx_50_legal_missing(self):next(x for x in self.ledger['rows'] if x['atom_id']=='A018')['authority_keys']=['LAW_EXEC_223_2026'];self.reject('KRX_50_BOTH_AND_HALFYEAR_LOST')
    def test_29_custodian_act_missing(self):next(x for x in self.ledger['rows'] if x['atom_id']=='A036')['authority_keys']=['KRX_RISK'];self.reject('CUSTODIAN_LAW_MISSING')
    def test_30_ats_missing(self):next(x for x in self.ledger['rows'] if x['atom_id']=='A004')['authority_keys']=['KRX_RISK'];self.reject('ATS_STOCK_MARKET_SPLIT_MISSING')
    def test_31_nav_gap_missing(self):next(x for x in self.ledger['rows'] if x['atom_id']=='A012')['authority_keys']=['KRX_CURRENT_ETF_LISTING'];self.reject('PRICE_GAP_VS_TRACKING_LOST')
    def test_32_trade_vs_redemption_missing(self):next(x for x in self.ledger['rows'] if x['atom_id']=='A028')['authority_keys']=['KRX_RISK'];self.reject('REDEMPTION_VS_MARKET_SALE_LOST')
    def test_33_false_body_sha(self):self.ledger['authority_register'][0]['issuer_http_body_sha256']='1'*64;self.reject('UNPINNED_PRIMARY_FALSE_GO')
    def test_34_historical_rule_becomes_current(self):next(x for x in self.ledger['authority_register'] if x['id']=='KRX_HISTORICAL_RULE')['retrieval']='LIVE_PAGE_READ';self.reject('OLD_KRX_MISCLASSIFIED_CURRENT')
    def test_35_tax_pretends_binding(self):next(x for x in self.ledger['authority_register'] if x['id']=='NABO_TAX_POINTER')['retrieval']='LIVE_PAGE_READ';self.reject('TAX_PERSONAL_FALSE_SCOPE')
    def test_36_fake_site(self):self.ledger['authority_register'][0]['url']='https://listing.krx.co.kr.attacker.com/rule';self.reject('URL_NOT_ISSUER')
    def test_37_plain_http(self):self.ledger['authority_register'][0]['url']='http://listing.krx.co.kr/rule';self.reject('URL_HTTPS')
    def test_38_userinfo(self):self.ledger['authority_register'][0]['url']='https://bad@listing.krx.co.kr/rule';self.reject('URL_HTTPS')
    def test_39_port(self):self.ledger['authority_register'][0]['url']='https://listing.krx.co.kr:443/rule';self.reject('URL_HTTPS')
    def test_40_fragment(self):self.ledger['authority_register'][0]['url']='https://listing.krx.co.kr/rule#bad';self.reject('URL_HTTPS')
    def test_41_duplicate_registry(self):self.ledger['authority_register'][1]['id']=self.ledger['authority_register'][0]['id'];self.reject('REGISTRY_DUPLICATE')
    def test_42_weaker_authorities(self):self.ledger['authority_register']=self.ledger['authority_register'][:4];self.reject('INSUFFICIENT_FAMILY_EVIDENCE')
    def test_43_unverified_issuer(self):self.ledger['authority_register'][0]['finance_approved']=True;self.reject('UNPINNED_PRIMARY_FALSE_GO')
    def test_44_unknown_retrieval(self):self.ledger['authority_register'][0]['retrieval']='ALWAYS_VERIFIED';self.reject('REGISTRY_SOURCE_SCOPE')
    def test_45_blank_reason(self):self.ledger['rows'][0]['reviewer_reason_private']='bad';self.reject('TRIAGE_EXPLANATION_REQUIRED')
    def test_46_unknown_class(self):self.ledger['rows'][0]['review_class']='APPROVED';self.reject('TRIAGE_EXPLANATION_REQUIRED')
    def test_47_fake_date_row(self):self.ledger['rows'][0]['source_date_as_of']='2024-10-01';self.reject('ORIGINAL_OPEN_DRIFT')
    def test_48_fake_final_status(self):self.ledger['rows'][0]['final_status']='FINANCIAL_APPROVED';self.reject('UNSUPPORTED_FINANCE_APPROVAL')
    def test_49_duplicate_ref(self):self.ledger['rows'][0]['authority_keys']=['KRX_CURRENT_ETF_LISTING']*2;self.reject('ISSUER_KEY_MISSING')
    def test_50_unknown_ref(self):self.ledger['rows'][0]['authority_keys']=['LEGAL_LIE'];self.reject('ISSUER_KEY_MISSING')
    def test_51_bad_registry_field(self):self.ledger['authority_register'][0]['evil_code']='yes';self.reject('REGISTRY_FIELDS')
    def test_52_bad_row_field(self):self.ledger['rows'][0]['gold_tamper']=1;self.reject('TRIAGE_ROW_FIELDS')
    def test_53_bad_ledger_field(self):self.ledger['approve_anything']=True;self.reject('LEDGER_SCHEMA')
    def test_54_no_fake_benchmark_precision(self):
        x=compare_against_synthetic_gold(gold={1,2,3},predicted={2,3,4});self.assertEqual((x['tp'],x['fp'],x['fn']),(2,1,1));self.assertAlmostEqual(x['precision'],2/3);self.assertAlmostEqual(x['recall'],2/3)
    def test_55_empty_synthetic_gold_rejected(self):
        with self.assertRaises(OpenEvidenceFailure):compare_against_synthetic_gold(gold=set(),predicted=set())
    def test_56_nonset_synthetic_gold_rejected(self):
        with self.assertRaises(OpenEvidenceFailure):compare_against_synthetic_gold(gold=[1,2],predicted={1,2})

class V118PublicReceipt(unittest.TestCase):
    def setUp(self):
        p=ROOT/'V118_PUBLIC_SHA_ONLY.json'
        self.assertTrue(p.exists(),'Mandatory public receipt must be checked by CI, never skipped')
        self.data=json.loads(p.read_text())
    def test_57_v117_custody(self):self.assertEqual(self.data['original_cues'],173)
    def test_58_41_census(self):self.assertEqual(self.data['financial_docket_cases_reviewed'],41)
    def test_59_false_approvals(self):self.assertEqual(self.data['financial_fact_approvals'],0)
    def test_60_no_gold_score(self):self.assertIsNone(self.data['independent_precision'])
    def test_61_all_open(self):self.assertEqual(self.data['remaining_formal_finance_open'],41)
    def test_62_full_no_go(self):self.assertFalse(self.data['p0_go'])
    def test_63_8_counterexamples(self):self.assertEqual(self.data['review_class_counts']['COUNTEREVIDENCE_OR_OVERGENERALIZATION'],8)
    def test_64_separate_legal_body(self):self.assertFalse(self.data['official_full_http_body_sha_verified'])

if __name__=='__main__':unittest.main()
