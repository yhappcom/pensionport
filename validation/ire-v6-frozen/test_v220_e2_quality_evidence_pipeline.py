"""Public code-only V220 regressions: NO owner SRT, historical SQLite or fabricated gold."""
from __future__ import annotations
import copy
import unittest
from hashlib import sha256
from ire.v6.errors import InvalidInput
from v220_e2_quality_evidence_pipeline import (
    diagnose_e2_proof_gaps, assess_claim_precision_recall, audit_media_claim_quarantine,
)

SOURCE_SHA='a'*64

def source_hash(s):return sha256(s.encode('utf8')).hexdigest()


def fixture():
    source=['ETF는 펀드입니다.', '하지만 예외가 있습니다.', '그래프를 보면 차이가 있습니다.', '감사합니다.']
    classes=['PRIMARY_UNAPPROVED','CONTEXT_UNAPPROVED_NEEDS_CLAIM_OMISSION_REVIEW',
             'MEDIA_DEPENDENT_UNMAPPED_QUARANTINE','DISCOURSE_OR_NONCLAIM_PROVISIONAL']
    rows=[]
    for i,(s,c) in enumerate(zip(source,classes),1):
        rows.append({'cue_index':i,'source_quote':s,'classification':c,
            'independent_omission_review_complete':False,
            'original_audio_or_screen_review_required':i==3})
    native={'source_sha256':SOURCE_SHA,'atoms':[
        {'claim_id':'C00001','kind':'FACT','speaker':'UNKNOWN','stance':'UNRESOLVED',
         'source_refs':[{'cue_index':1,'quote':source[0]}],
         'context_cue_indices':[1,2],
         'condition_cue_indices':[],'exception_cue_indices':[]}]}
    census={'original_source_sha256':SOURCE_SHA,'rows':rows}
    finance={'source_sha256':SOURCE_SHA,'atoms':[
        {'claim_id':'C00001','risk_tags':['MATERIAL_FACT_RISK'],
         'financial_truth_certified':False,'claim_approved':False}]}
    receipt={'schema':'IRE_V219_E2_INTEGRATED_REAL_SOURCE_AND_UNAPPROVED_CLAIM_CUSTODY_V1',
         'original_source_sha256':SOURCE_SHA,'original_cues_verified':4,
         'native_unapproved_atoms':1,'e2_final_pass':False,'financial_facts_approved':False,
         'knowledge_published':False,'historical_v176_owner_sqlite_recovered':False,
         'separate_blind_independent_gold_measured':False,
         'historical_v182_source_open_cases_unresolved':1,
         'source_risk_tagged_native_atoms':1,
         'cues_flagged_audio_or_video_or_screen':1,
         'all_cue_review_state_counts':dict(zip(classes,[1]*4))}
    media={'schema':'IRE_V220_E2_UNAPPROVED_MEDIA_SPEECH_DOCKET_V1',
        'source_sha256':SOURCE_SHA,'unapproved_speech_claims':[{
        'id':'M001','claim_status':'UNAPPROVED_SPEECH_ONLY_VISUAL_HOLD',
        'text_only_proposition_unverified':'화자의 차트 발언이 있다는 미승인 주장입니다.',
        'source_refs':[{'cue_index':3,'quote':source[2],
                        'source_text_sha256':source_hash(source[2])}],
        'financial_fact_approved':False,'speaker_verified':False,
        'e2_pass':False,'native_claim_id':None}]}
    gold={'schema':'IRE_V220_SOURCE_ONLY_GOLD_DRAFT_V1',
          'source_sha256':SOURCE_SHA,
          'claims':[{'gold_id':'G001','cue_indices':[1],
                     'high_risk':True,'kind':'FACT'}]}
    pairs={'source_sha256':SOURCE_SHA,'pairs':[
        {'gold_id':'G001','claim_id':'C00001','verdict':'EQUIVALENT'}]}
    return receipt,census,finance,native,media,gold,pairs


class V220E2EvidenceQualityTests(unittest.TestCase):
    def setUp(self):
        (self.receipt,self.census,self.finance,self.native,self.media,self.gold,self.pairs)=fixture()

    def diagnose(self):
        return diagnose_e2_proof_gaps(self.receipt,self.census,self.finance,self.native)

    def measure(self):
        return assess_claim_precision_recall(self.gold,self.native,self.pairs,
                                               expected_source_sha256=SOURCE_SHA)

    def check_media(self):
        return audit_media_claim_quarantine(self.census,self.media,
                                             expected_source_sha256=SOURCE_SHA)

    def test_01_realistic_blocker_census_separates_independent_and_owner(self):
        result=self.diagnose()
        self.assertFalse(result['e2_final_pass'])
        self.assertTrue(result['historical_owner_required_for_legacy_knowledge_merge'])
        self.assertFalse(result['historical_owner_required_for_new_video_gold_measurement'])
        self.assertEqual(result['media_cue_indices'],[3])
        self.assertEqual(result['unverified_speaker_atoms'],1)

    def test_02_code_only_ci_never_becomes_semantic_pass(self):
        result=self.diagnose()
        self.assertEqual(result['e2_semantic_quality_status'],'HOLD_EVIDENCE_MISSING')
        self.assertFalse(result['valid_independent_precision_recall_measured'])
        self.assertFalse(result['e3_e4_e5_authorized'])

    def test_03_fake_receipt_pass_rejected(self):
        self.receipt['e2_final_pass']=True
        with self.assertRaisesRegex(InvalidInput,'FALSE_FINAL_APPROVAL'):self.diagnose()

    def test_04_missing_financial_risk_item_rejected(self):
        self.finance['atoms']=[]
        with self.assertRaisesRegex(InvalidInput,'SOURCE_COUNTS_DRIFT'):self.diagnose()

    def test_05_source_tamper_rejected(self):
        self.finance['source_sha256']='f'*64
        with self.assertRaisesRegex(InvalidInput,'SOURCE_SHA_MISMATCH'):self.diagnose()

    def test_06_bad_cue_index_rejected(self):
        self.census['rows'][2]['cue_index']=19
        with self.assertRaisesRegex(InvalidInput,'INCOMPLETE_CUE_CUSTODY'):self.diagnose()

    def test_07_unaudited_speaker_promotion_rejected(self):
        self.native['atoms'][0]['speaker']='LECTURER'
        with self.assertRaisesRegex(InvalidInput,'UNTRUSTED_SPEAKER_PROMOTION'):self.diagnose()

    def test_08_risk_count_drift_rejected(self):
        self.receipt['source_risk_tagged_native_atoms']=0
        with self.assertRaisesRegex(InvalidInput,'RISK_COUNT_DRIFT'):self.diagnose()

    def test_09_positive_100_percent_measurement_is_NOT_certification(self):
        metric=self.measure()
        self.assertEqual((metric['precision_pct'],metric['recall_pct']),(100.0,100.0))
        self.assertTrue(metric['numerical_thresholds_met_on_supplied_annotations'])
        self.assertFalse(metric['independent_gold_provenance_certified'])
        self.assertFalse(metric['e2_final_pass'])

    def test_10_missing_high_risk_is_failure(self):
        self.gold['claims'].append({'gold_id':'G002','cue_indices':[3],
                                     'high_risk':True,'kind':'FACT'})
        metric=self.measure()
        self.assertEqual(metric['recall_pct'],50.0)
        self.assertEqual(metric['missed_high_risk_gold_ids'],['G002'])
        self.assertFalse(metric['numerical_thresholds_met_on_supplied_annotations'])

    def test_11_partial_equivalence_is_never_tp(self):
        self.pairs['pairs'][0]['verdict']='PARTIAL'
        metric=self.measure()
        self.assertEqual((metric['true_positives'],metric['false_positives'],
                          metric['false_negatives']),(0,1,1))

    def test_12_duplicated_equivalence_is_blocked(self):
        self.pairs['pairs'].append(copy.deepcopy(self.pairs['pairs'][0]))
        with self.assertRaisesRegex(InvalidInput,'ADJUDICATION_INVALID_OR_DUPLICATED'):self.measure()

    def test_13_unanchored_equivalence_is_blocked(self):
        self.gold['claims'][0]['cue_indices']=[4]
        with self.assertRaisesRegex(InvalidInput,'DUPLICATE_OR_UNSOURCED_EQUIVALENCE'):self.measure()

    def test_14_malformed_gold_id_is_blocked(self):
        self.gold['claims'][0]['gold_id']=[]
        with self.assertRaisesRegex(InvalidInput,'INVALID_GOLD_ITEM'):self.measure()

    def test_15_empty_gold_is_blocked(self):
        self.gold['claims']=[]
        with self.assertRaisesRegex(InvalidInput,'GOLD_EMPTY_OR_TOO_LARGE'):self.measure()

    def test_16_self_attested_independence_not_trusted(self):
        self.gold['independent_gold_certified']=True
        self.pairs['approved_by_authority']=True
        self.assertFalse(self.measure()['independent_gold_provenance_certified'])

    def test_17_different_gold_source_fails(self):
        self.gold['source_sha256']='b'*64
        with self.assertRaisesRegex(InvalidInput,'GOLD_SOURCE_MISMATCH'):self.measure()

    def test_18_media_claim_quarantine_all_source_refs(self):
        r=self.check_media()
        self.assertEqual(r['original_media_unmapped_cues'],1)
        self.assertEqual(r['media_claim_candidates_retained'],1)
        self.assertFalse(r['e2_final_pass'])

    def test_19_drop_media_claim_fails(self):
        self.media['unapproved_speech_claims'][0]['source_refs']=[]
        with self.assertRaisesRegex(InvalidInput,'MEDIA_FALSE_CERTIFICATION'):self.check_media()

    def test_20_fake_financial_media_approval_fails(self):
        self.media['unapproved_speech_claims'][0]['financial_fact_approved']=True
        with self.assertRaisesRegex(InvalidInput,'MEDIA_FALSE_CERTIFICATION'):self.check_media()

    def test_21_media_cue_quote_altered_fails(self):
        self.media['unapproved_speech_claims'][0]['source_refs'][0]['quote']='원금보장'
        with self.assertRaisesRegex(InvalidInput,'MEDIA_QUOTE_OR_CUE_DUPLICATE_OR_SHA'):self.check_media()

    def test_22_media_original_source_sha_fails(self):
        self.media['source_sha256']='f'*64
        with self.assertRaisesRegex(InvalidInput,'MEDIA_PACKET_SOURCE_INVALID'):self.check_media()

    def test_23_duplicate_media_cue_mapping_fails(self):
        self.media['unapproved_speech_claims'].append(copy.deepcopy(self.media['unapproved_speech_claims'][0]))
        self.media['unapproved_speech_claims'][1]['id']='M002'
        with self.assertRaisesRegex(InvalidInput,'MEDIA_QUOTE_OR_CUE_DUPLICATE'):self.check_media()

    def test_24_gold_wrong_type_is_handled_not_runfail(self):
        self.pairs['pairs'][0]['claim_id']=[]
        with self.assertRaisesRegex(InvalidInput,'ADJUDICATION_INVALID_OR_DUPLICATED'):self.measure()

    def test_25_malformed_census_rows_is_invalidinput(self):
        self.census['rows']=[None]*4
        with self.assertRaisesRegex(InvalidInput,'INCOMPLETE_CUE_CUSTODY'):self.diagnose()


if __name__=='__main__':unittest.main()