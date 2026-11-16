"""Synthetic-only V83 tests; never use owner/private source on GitHub CI."""
import unittest
from copy import deepcopy
from v77_private_v33_replay import Cue,sha
from v83_source_gap_context_guard import (
  auxiliary_expected, validate_source_gap_custody,PRIORITY_ALERTS,
  REVIEWED,UNTRIAGED,SCHEMA,STATUS,FALSE_FLAGS)

class SyntheticGapCustody(unittest.TestCase):
    def setUp(self):
        self.vid='SYNTHETIC_ONLY'
        self.video=[(9,self.vid,6,'synthetic-no-archive')]
        raw=['첫 발언 예시','그런데 질문','?', '다음 발언','예', '끝 발언']
        self.cues={self.vid:[Cue(i+1,i*1000,i*1000+999,t) for i,t in enumerate(raw)]}
        self.reg={self.vid:{'W00001':[
          {'claim_id':'C00001','cue_indices':[1,2],'source_text_sha256':sha('첫 발언 예시 | 그런데 질문'.encode())},
          {'claim_id':'C00002','cue_indices':[4],'source_text_sha256':sha('다음 발언'.encode())},
          {'claim_id':'C00003','cue_indices':[6],'source_text_sha256':sha('끝 발언'.encode())}]}}
        self.alerts={(9,3):'QUESTION_FORCE_FRAGMENT'}
        self.rows=auxiliary_expected(self.cues,self.reg,self.video)
        assert len(self.rows)==2
        for row in self.rows:
            if row['cue_index']==3:
                row.update(context_status=REVIEWED,risk_type=self.alerts[(9,3)],
                           context_interpretation_private='이 대목은 의문형으로 끝난다.',
                           reviewer_caution_private='질문을 확정 권고로 분류하면 안 된다.')

    def check(self,rows=None,alerts=None):
        return validate_source_gap_custody(self.cues,self.reg,self.video,
            self.rows if rows is None else rows, expected_count=2,
            alerts=self.alerts if alerts is None else alerts,expected_prior_parents=2)

    def assert_invalid(self,mutation,code=None):
        rows=deepcopy(self.rows)
        mutation(rows)
        with self.assertRaisesRegex(ValueError,('V83_'+code) if code else 'V83_'):
            self.check(rows)

    def test_01_basic_two_gaps_and_policy_is_fail_closed(self):
        x=self.check();self.assertEqual(x['auxiliary_context_links_verified'],2)
        self.assertFalse(x['p0_go']);self.assertFalse(x['independent_gold'])
        self.assertEqual(x['new_v33_candidates_approved'],0)
    def test_02_one_critical_unreviewed_context(self):
        x=self.check();self.assertEqual(x['high_priority_contextual_alerts'],1)
        self.assertEqual(x['other_gaps_unadjudicated_as_standalone_claims'],1)
    def test_03_cue_gap_is_never_automatic_financial_fact(self):
        x=self.check();self.assertFalse(x['atomic_claim_recall_certified'])
        self.assertEqual(x['financial_facts_approved'],0)
        self.assertEqual(x['v75_total_pending_unchanged'],887)
    def test_04_non_gap_candidate_as_gap_rejected(self):
        self.assert_invalid(lambda a:a[0].update(cue_index=1),'NON_GAP_OR_FOREIGN_CUE')
    def test_05_missing_gap_rejected(self):
        self.assert_invalid(lambda a:a.pop(),'GAP_COUNT_OR_TYPE_DRIFT')
    def test_06_duplicate_gap_rejected(self):
        self.assert_invalid(lambda a:a.append(deepcopy(a[0])),'GAP_COUNT_OR_TYPE_DRIFT')
    def test_07_wrong_video_id_rejected(self):
        self.assert_invalid(lambda a:a[0].update(video_id='WRONG_VIDEO'),'NON_GAP_OR_FOREIGN_CUE')
    def test_08_wrong_video_no_rejected(self):
        self.assert_invalid(lambda a:a[0].update(video_no=10))
    def test_09_source_cue_text_mutation_rejected(self):
        self.assert_invalid(lambda a:a[0].update(cue_text_private='다른 질문'))
    def test_10_source_cue_sha_forgery_rejected(self):
        self.assert_invalid(lambda a:a[0].update(cue_text_sha256='0'*64))
    def test_11_source_time_mutation_rejected(self):
        self.assert_invalid(lambda a:a[0].update(start_ms=99))
    def test_12_end_time_mutation_rejected(self):
        self.assert_invalid(lambda a:a[1].update(end_ms=999999))
    def test_13_neighbor_cue_text_forgery_rejected(self):
        self.assert_invalid(lambda a:a[0]['adjacent_cues_private'][0].update(text_private='변조'))
    def test_14_neighbor_timestamp_forgery_rejected(self):
        self.assert_invalid(lambda a:a[0]['adjacent_cues_private'][0].update(start_ms=42))
    def test_15_left_anchor_claim_swap_rejected(self):
        self.assert_invalid(lambda a:a[0]['left_existing_candidate'].update(claim_id='C99999'))
    def test_16_right_anchor_claim_swap_rejected(self):
        self.assert_invalid(lambda a:a[0]['right_existing_candidate'].update(claim_id='C99999'))
    def test_17_source_status_upgrade_rejected(self):
        self.assert_invalid(lambda a:a[0].update(source_status='APPROVED'))
    def test_18_false_fact_approval_rejected(self):
        self.assert_invalid(lambda a:a[0].update(fact_approved=True),'FALSE_FINANCIAL_OR_GOLD_PROMOTION')
    def test_19_false_gold_approval_rejected(self):
        self.assert_invalid(lambda a:a[0].update(independent_gold=True),'FALSE_FINANCIAL_OR_GOLD_PROMOTION')
    def test_20_false_v75_member_rejected(self):
        self.assert_invalid(lambda a:a[0].update(v75_membership_verified=True),'FALSE_FINANCIAL_OR_GOLD_PROMOTION')
    def test_21_false_personal_advice_rejected(self):
        self.assert_invalid(lambda a:a[0].update(personal_action_approved=True),'FALSE_FINANCIAL_OR_GOLD_PROMOTION')
    def test_22_mislabeled_priority_rejected(self):
        self.assert_invalid(lambda a:a[0].update(risk_type='NUMERIC_FACT'))
    def test_23_priority_disguised_as_unreviewed_rejected(self):
        self.assert_invalid(lambda a:a[0].update(context_status=UNTRIAGED))
    def test_24_missing_manual_interpretation_rejected(self):
        self.assert_invalid(lambda a:a[0].update(context_interpretation_private=None))
    def test_25_missing_manual_caution_rejected(self):
        self.assert_invalid(lambda a:a[0].update(reviewer_caution_private=''))
    def test_26_unreviewed_gap_cannot_falsely_gain_interpretation(self):
        self.assert_invalid(lambda a:a[1].update(context_interpretation_private='자동 사실 승인입니다.'))
    def test_27_unreviewed_gap_cannot_gain_risk_label(self):
        self.assert_invalid(lambda a:a[1].update(risk_type='TRUE'))
    def test_28_alert_census_change_rejected(self):
        with self.assertRaisesRegex(ValueError,'V83_'):
            self.check(alerts={(9,3):'QUESTION_FORCE_FRAGMENT',(9,5):'FALSE_PRIORITY'})
    def test_29_duplicate_candidate_source_cue_rejected(self):
        other=deepcopy(self.reg)
        other[self.vid]['W00001'][1]['cue_indices']=[2,4]
        with self.assertRaisesRegex(ValueError,'V83_CANDIDATE_CUE_OVERLAP'):
            validate_source_gap_custody(self.cues,other,self.video,self.rows,expected_count=2,alerts=self.alerts)
    def test_30_missing_original_candidate_rejected(self):
        other=deepcopy(self.reg)
        other[self.vid]['W00001'][1]['cue_indices']=[4,5]
        with self.assertRaisesRegex(ValueError,'V83_'):
            validate_source_gap_custody(self.cues,other,self.video,self.rows,expected_count=2,alerts=self.alerts)
    def test_31_unaltered_replay_digest_deterministic(self):
        self.assertEqual(self.check()['source_gap_auxiliary_custody_sha256'],self.check(deepcopy(self.rows))['source_gap_auxiliary_custody_sha256'])
    def test_32_semantic_text_change_is_hash_audited_not_truth_graded(self):
        rows=deepcopy(self.rows);rows[0]['context_interpretation_private']='이것은 다른 주관적 해석이다.'
        new=self.check(rows);original=self.check()
        self.assertNotEqual(new['priority_alert_manifest_sha256'],original['priority_alert_manifest_sha256'])
        self.assertFalse(new['independent_gold'])
    def test_33_negative_count_invalid(self):
        with self.assertRaisesRegex(ValueError,'V83_GAP_COUNT_OR_TYPE_DRIFT'):
            validate_source_gap_custody(self.cues,self.reg,self.video,self.rows,expected_count=3,alerts=self.alerts)
    def test_34_original_candidate_identity_untouched(self):
        self.assertEqual(len(self.reg[self.vid]['W00001']),3)
        self.check();self.assertEqual(len(self.reg[self.vid]['W00001']),3)

if __name__=='__main__':unittest.main()