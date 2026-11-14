"""Synthetic adversarial checks; no private source or original user transcript."""
import copy
import hashlib
import json
import pathlib
import sys
import unittest
from unittest.mock import patch

try:
    from . import v120_chat_internal_score_guard as g
except ImportError:
    import v120_chat_internal_score_guard as g

HERE=pathlib.Path(__file__).resolve().parent

def demo():
    src='\n\n'.join(f'{i}\n00:00:00,000 --> 00:00:01,000\nSYNTH-{i}' for i in range(1,174)).encode()
    predict=b'FAKE-PREDICTION-RAW-NOT_OWNER'
    def cuehash(ids):return g.digest(' | '.join(f'SYNTH-{x}' for x in ids).encode())
    A=[{'id':f'A{i:03}', 'cue_indices':[i], 'source_text_sha256':cuehash([i])}
       for i in range(1,59)]
    B=[{'id':f'R{i:03}','cue_indices':[i], 'source_text_sha256':cuehash([i]),
        'risk':'HIGH' if i<=14 or 36<=i<=44 else 'LOW'} for i in range(1,60)]
    pre={'schema':'V120_PRECOMMITTED_ASSET_DIGESTS_V1','video_id':'Yb_5prWaqhk',
         'source_sha256':g.digest(src),'engine_predictions_pre_reveal_sha256':g.digest(predict),
         'first_pass_A_sha256':'0'*64,'A_cue_parent_census':173,
         'blindness':'PARTIAL_PREVIOUS_TOPIC_EXPOSURE'}
    a={'schema':'V120_CHAT_SOURCE_FIRST_PASS_A_PARTIAL_PRIOR_TOPIC_EXPOSURE_V1','video_id':'Yb_5prWaqhk',
       'original_cue_count':173,'prior_exposure_status':'PRIOR_SUMMARY_TOPICS_SEEN_NOT_STRICTLY_BLIND',
       'reference_gold_certified':False,
       'source_segments':[{'range':[1,173]}],'first_pass_claims':A,
       'context_cues_without_direct_claim':list(range(59,174))}
    ar=json.dumps(a,sort_keys=True).encode();pre['first_pass_A_sha256']=g.digest(ar)
    b={'schema':'V120_CHAT_COUNTEREXAMPLE_PASS_B_AND_ADJUDICATED_REFERENCE_V1','video_id':'Yb_5prWaqhk',
       'A_frozen_sha256':pre['first_pass_A_sha256'],
       'engine_predictions_pre_reveal_sha256':pre['engine_predictions_pre_reveal_sha256'],
       'same_chat_review_not_externally_independent':True,'external_gold':False,
       'official_financial_fact_approved':0,'source_audio_verified':False,'video_screen_verified':False,
       'A_claim_count':58,'chat_reference_claim_count':59,'B_revision_count':20,
       'revisions':[{'id':i} for i in range(20)],'reference_claims':B}
    bb=json.dumps(b,sort_keys=True).encode()
    matches=[{'prediction_id':f'P{i:03}','reference_id':f'R{i:03}','verdict':'TP'} for i in range(1,36)]
    other=[{'prediction_id':f'P{i:03}','reference_id':None,'verdict':'FP'} for i in range(36,47)]
    misses=[{'reference_id':f'R{i:03}','risk':r['risk']} for i,r in enumerate(B,1) if i>35]
    s={'schema':'V120_CHAT_INTERNAL_REFERENCE_ONE_TO_ONE_CROSSCHECK_NOT_EXTERNAL_GOLD_V1',
       'video_id':'Yb_5prWaqhk','B_sha256':g.digest(bb),
       'prior_prediction_sha256':pre['engine_predictions_pre_reveal_sha256'],
       'A_sha256':pre['first_pass_A_sha256'],'independent_gold':False,'p0_go':False,
       'external_certified_precision':None,'external_certified_recall':None,
       'evaluation_type':'CHAT_INTERNAL_REFERENCE_SCORE_PROVISIONAL',
       'limitations':['REFERENCE_DUPLICATE_R045_R046_POTENTIAL_OVERSPLIT',
       'REFERENCE_AUTHORED_BY_SAME_MODEL_IN_SAME_TURN',
       'FALSE_POSITIVE_HERE_MEANS_NOT_ONE_TO_ONE_NOT_FACTUALLY_FALSE'],
       'counts':{'predicted_atoms':46,'chat_reference_candidates':59,'tp':35,'fp':11,'fn':24,
                 'high_critical_reference_candidates':23,'high_critical_tp':14,'high_critical_fn':9,
                 'A_claims':58,'B_adjudication_revision_records':20},
       'chat_internal_precision':35/46,'chat_internal_recall':35/59,
       'chat_internal_high_risk_recall':14/23,
       'predicted_atom_verdicts':matches+other,'unmatched_chat_reference':misses}
    return pre,a,b,s,src,predict,ar,bb

class TestSyntheticChatScore(unittest.TestCase):
    def setUp(self):
        self.fixture=list(copy.deepcopy(demo()))
        self.expected_pin=g.digest(self.fixture[4])
        self.patcher=patch.object(g,'EXPECTED_OWNER_SOURCE_SHA256',self.expected_pin)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def call(self):return g.audit(*self.fixture)
    def reject(self, mut):
        mut(self.fixture)
        with self.assertRaises((g.UnsafeScore,KeyError,TypeError)):
            self.call()

    def test_01_valid_synthetic_counts(self):
        z=self.call();self.assertEqual((z['tp'],z['fp'],z['fn']),(35,11,24))
    def test_02_private_source_mutation(self):
        self.reject(lambda v:v.__setitem__(4,v[4]+b'BAD'))
    def test_03_baseline_mutation(self):
        self.reject(lambda v:v.__setitem__(5,v[5]+b'BAD'))
    def test_04_A_bytes_tamper(self):
        self.reject(lambda v:v.__setitem__(6,v[6]+b'BAD'))
    def test_05_B_bytes_tamper(self):
        self.reject(lambda v:v.__setitem__(7,v[7]+b'BAD'))
    def test_06_no_fake_external_score(self):
        self.reject(lambda v:v[3].__setitem__('external_certified_recall',0.9))
    def test_07_no_fake_independent_gold(self):
        self.reject(lambda v:v[3].__setitem__('independent_gold',True))
    def test_08_no_fake_p0_go(self):
        self.reject(lambda v:v[3].__setitem__('p0_go',True))
    def test_09_no_fake_source_blind(self):
        self.reject(lambda v:v[0].__setitem__('blindness','FULLY_BLIND'))
    def test_10_no_fake_chat_independence(self):
        self.reject(lambda v:v[2].__setitem__('same_chat_review_not_externally_independent',False))
    def test_11_no_fake_finance_approval(self):
        self.reject(lambda v:v[2].__setitem__('official_financial_fact_approved',1))
    def test_12_no_fake_audio(self):
        self.reject(lambda v:v[2].__setitem__('source_audio_verified',True))
    def test_13_no_fake_video(self):
        self.reject(lambda v:v[2].__setitem__('video_screen_verified',True))
    def test_14_no_dropped_A_claim(self):
        self.reject(lambda v:v[1]['first_pass_claims'].pop())
    def test_15_no_dropped_B_reference(self):
        self.reject(lambda v:v[2]['reference_claims'].pop())
    def test_16_no_fake_tp_count(self):
        self.reject(lambda v:v[3]['counts'].__setitem__('tp',36))
    def test_17_no_wrong_precision(self):
        self.reject(lambda v:v[3].__setitem__('chat_internal_precision',.99))
    def test_18_no_wrong_recall(self):
        self.reject(lambda v:v[3].__setitem__('chat_internal_recall',.99))
    def test_19_no_wrong_high_risk_recall(self):
        self.reject(lambda v:v[3].__setitem__('chat_internal_high_risk_recall',.99))
    def test_20_no_double_match(self):
        self.reject(lambda v:v[3]['predicted_atom_verdicts'][1].__setitem__('reference_id','R001'))
    def test_21_no_unknown_ref(self):
        self.reject(lambda v:v[3]['predicted_atom_verdicts'][1].__setitem__('reference_id','R999'))
    def test_22_no_wrong_FN_list(self):
        self.reject(lambda v:v[3]['unmatched_chat_reference'][0].__setitem__('reference_id','R001'))
    def test_23_no_duplicate_prediction(self):
        self.reject(lambda v:v[3]['predicted_atom_verdicts'][1].__setitem__('prediction_id','P001'))
    def test_24_high_FN_must_balance(self):
        self.reject(lambda v:v[3]['counts'].__setitem__('high_critical_fn',10))
    def test_25_A_ref_source_digest(self):
        self.reject(lambda v:v[1]['first_pass_claims'][0].__setitem__('source_text_sha256','f'*64))
    def test_26_B_ref_source_digest(self):
        self.reject(lambda v:v[2]['reference_claims'][0].__setitem__('source_text_sha256','f'*64))
    def test_27_missing_source_cue(self):
        self.reject(lambda v:v[1]['first_pass_claims'][0].__setitem__('cue_indices',[190]))
    def test_28_source_segment_gap(self):
        self.reject(lambda v:v[1]['source_segments'][0].__setitem__('range',[2,173]))
    def test_29_missing_context_cue(self):
        self.reject(lambda v:v[1]['context_cues_without_direct_claim'].pop())
    def test_30_provisional_label_only(self):
        self.reject(lambda v:v[3].__setitem__('evaluation_type','EXTERNALLY_CERTIFIED'))
    def test_31_source_segment_different_id(self):
        self.reject(lambda v:v[0].__setitem__('video_id','OTHER_SOURCE'))
    def test_32_ref_duplicate_id(self):
        self.reject(lambda v:v[2]['reference_claims'][1].__setitem__('id','R001'))
    def test_33_no_forged_reviewer_reference(self):
        self.reject(lambda v:v[1].__setitem__('reference_gold_certified',True))
    def test_34_missing_duplicate_reference_disclaimer(self):
        self.reject(lambda v:v[3]['limitations'].remove('REFERENCE_DUPLICATE_R045_R046_POTENTIAL_OVERSPLIT'))
    def test_35_internal_scores_not_0_0(self):
        z=self.call();self.assertAlmostEqual(z['recall_provisional'],35/59)

class PublicReceiptTests(unittest.TestCase):
    def test_36_public_receipt_metadata(self):
        p=HERE/'V120_PUBLIC_SHA_ONLY.json'
        if not p.exists():self.skipTest('local test fixture present only with public receipt')
        v=json.loads(p.read_text(encoding='utf-8'))
        self.assertEqual(v['schema'],'V120_PUBLIC_INTERNAL_SCORE_GUARD_RECEIPT_V1')
        self.assertEqual((v['previous_predictions'],v['chat_reference_candidates']),(46,59))
        self.assertEqual((v['tp'],v['fp'],v['fn']),(35,11,24))
        self.assertTrue(v['prior_topic_exposure'])
        self.assertFalse(v['external_independent_gold'])
        self.assertFalse(v['p0_go'])
    def test_37_public_only_receipt_no_personal_text(self):
        p=HERE/'V120_PUBLIC_SHA_ONLY.json'
        if not p.exists():self.skipTest('local test fixture present only with public receipt')
        v=json.loads(p.read_text(encoding='utf-8'))
        self.assertFalse(any('proposition' in key or 'private' in key or 'script' in key for key in v))
    def test_38_public_accuracy_is_provisional(self):
        p=HERE/'V120_PUBLIC_SHA_ONLY.json'
        if not p.exists():self.skipTest('local test fixture present only with public receipt')
        v=json.loads(p.read_text(encoding='utf-8'))
        self.assertTrue(v['actual_chat_internal_reference_score_provisional'])
        self.assertFalse(v['official_source_http_body_sha256_pinned'])
        self.assertIsNone(v['model_internal_inference_seconds'])

if __name__=='__main__':unittest.main()
