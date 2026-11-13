"""V78 source-meaning custody negative controls using synthetic text only."""
from __future__ import annotations
from copy import deepcopy
import unittest
from v77_private_v33_replay import Cue,sha
from v78_shadow_source_custody import SCHEMA,validate_rows


class V78Tests(unittest.TestCase):
    def setUp(self):
        self.vid = 'Synthetic01'
        self.cues = {self.vid: [
            Cue(1,100,800,'한 가지 가정을 합니다.'),
            Cue(2,801,1600,'상품에 수익이 생길 수도 있습니다.'),
            Cue(3,1601,2300,'조건을 확인해야 합니다.'),
        ]}
        excerpt=' | '.join(c.text for c in self.cues[self.vid][0:2])
        self.reg={self.vid:{'W00001':[
            {'claim_id':'C00001','cue_indices':[1,2],
             'source_text_sha256':sha(excerpt.encode('utf-8')),'numeric_tokens':0}]}}
        self.row={
            'schema':SCHEMA,'video_no':1,'video_id':self.vid,'window_id':'W00001','claim_id':'C00001',
            'cue_indices':[1,2], 'start_ms':100,'end_ms':1600,
            'source_excerpt_private':excerpt,'source_excerpt_sha256':sha(excerpt.encode('utf-8')),
            'neighbor_cues_private':[
                {'cue_index':i,'start_ms':c.start_ms,'end_ms':c.end_ms,'text_private':c.text}
                for i,c in enumerate(self.cues[self.vid],1)],
            'speaker_units':[{'act':'HYPOTHETICAL','interpretation':'이 발언은 금융 수익이 발생할 수 있다는 가정이다.'}],
            'reviewer_guard':'특정 상품의 금융 사실 인증 또는 수익 보장은 불가하다.',
            'source_status':'SHADOW_UNRECONCILED_V75',
            'semantic_method':'CHAT_CONTEXT_INTERPRETATION_NOT_GOLD',
            'fact_approved':False,'independent_gold':False,'personal_action_approved':False,
            'v75_membership_verified':False,'official_parent_merged':False,
        }

    def check(self,rows):
        return validate_rows(self.cues,self.reg,rows,expected_count=len(rows),enforce_four_per_video=False)

    def test_valid_synthetic_one(self):
        result=self.check([self.row]);self.assertEqual(result['shadow_parents'],1)
        self.assertEqual(result['shadow_speaker_or_nonclaim_interpretations'],1)
        self.assertFalse(result['v75_298_queue_membership_verified'])
        self.assertNotIn('상품에 수익',str(result))

    def test_duplicate_parent_rejected(self):
        with self.assertRaisesRegex(ValueError,'DUPLICATE_SHADOW_PARENT'):
            self.check([self.row,deepcopy(self.row)])

    def test_quote_tamper_rejected(self):
        r=deepcopy(self.row);r['source_excerpt_private']='원금 보장입니다.'
        with self.assertRaisesRegex(ValueError,'SOURCE_EXCERPT_OR_DIGEST_DRIFT'):self.check([r])

    def test_source_sha_tamper_rejected(self):
        r=deepcopy(self.row);r['source_excerpt_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'SOURCE_EXCERPT_OR_DIGEST_DRIFT'):self.check([r])

    def test_source_index_tamper_rejected(self):
        r=deepcopy(self.row);r['cue_indices']=[2,3]
        with self.assertRaisesRegex(ValueError,'ORIGINAL_CUE_INDEX_DRIFT'):self.check([r])

    def test_wrong_time_rejected(self):
        r=deepcopy(self.row);r['end_ms']=1500
        with self.assertRaisesRegex(ValueError,'TIME_FRAME_DRIFT'):self.check([r])

    def test_missing_neighbor_rejected(self):
        r=deepcopy(self.row);r['neighbor_cues_private'].pop()
        with self.assertRaisesRegex(ValueError,'NEIGHBOR_OR_TIME_DRIFT'):self.check([r])

    def test_neighbor_tamper_rejected(self):
        r=deepcopy(self.row);r['neighbor_cues_private'][2]['text_private']='참입니다.'
        with self.assertRaisesRegex(ValueError,'NEIGHBOR_OR_TIME_DRIFT'):self.check([r])

    def test_false_independent_gold_rejected(self):
        r=deepcopy(self.row);r['independent_gold']=True
        with self.assertRaisesRegex(ValueError,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL'):self.check([r])

    def test_false_v75_membership_rejected(self):
        r=deepcopy(self.row);r['v75_membership_verified']=True
        with self.assertRaisesRegex(ValueError,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL'):self.check([r])

    def test_false_official_merge_rejected(self):
        r=deepcopy(self.row);r['official_parent_merged']=True
        with self.assertRaisesRegex(ValueError,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL'):self.check([r])

    def test_false_advice_approval_rejected(self):
        r=deepcopy(self.row);r['personal_action_approved']=True
        with self.assertRaisesRegex(ValueError,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL'):self.check([r])

    def test_unsupported_act_rejected(self):
        r=deepcopy(self.row);r['speaker_units'][0]['act']='CERTIFIED_FACT'
        with self.assertRaisesRegex(ValueError,'SPEAKER_UNIT_INVALID'):self.check([r])

    def test_missing_guard_rejected(self):
        r=deepcopy(self.row);r['reviewer_guard']='OK'
        with self.assertRaisesRegex(ValueError,'REVIEWER_GUARD_REQUIRED'):self.check([r])

    def test_missing_speaker_units_rejected(self):
        r=deepcopy(self.row);r['speaker_units']=[]
        with self.assertRaisesRegex(ValueError,'SPEAKER_UNITS_REQUIRED'):self.check([r])

    def test_unknown_source_parent_rejected(self):
        r=deepcopy(self.row);r['claim_id']='C00002'
        with self.assertRaisesRegex(ValueError,'FOREIGN_ORIGINAL_PARENT'):self.check([r])

    def test_fake_completed_status_rejected(self):
        r=deepcopy(self.row);r['source_status']='COMPLETED'
        with self.assertRaisesRegex(ValueError,'FALSE_COMPLETION_STATUS'):self.check([r])

    def test_spurious_extra_field_rejected(self):
        r=deepcopy(self.row);r['extra']='sneaky'
        with self.assertRaisesRegex(ValueError,'ROW_SCHEMA_MISMATCH'):self.check([r])

    def test_false_meaning_gold_method_rejected(self):
        r=deepcopy(self.row);r['semantic_method']='INDEPENDENT_TRUTH'
        with self.assertRaisesRegex(ValueError,'FALSE_SEMANTIC_GOLD'):self.check([r])

    def test_wrong_video_number_rejected(self):
        r=deepcopy(self.row);r['video_no']=5
        with self.assertRaisesRegex(ValueError,'VIDEO_OWNERSHIP_MISMATCH'):self.check([r])


if __name__=='__main__':unittest.main()