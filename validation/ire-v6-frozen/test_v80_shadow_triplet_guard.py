"""V80 3-stage custody synthetic regression: no real SRT or owner notes."""
import json,unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile,ZipInfo
from v77_private_v33_replay import Cue,sha
from v78_shadow_source_custody import SCHEMA as V78_SCHEMA
from v79_shadow_delta_guard import SCHEMA as V79_SCHEMA
from v80_shadow_triplet_guard import SCHEMA,validate_triplet,load_pinned_private_rows,V79_RECORD

class TripletTests(unittest.TestCase):
    def setUp(self):
        self.vid='SYNTHETIC01'
        self.cues={self.vid:[Cue(i,i*500,(i+1)*500,f'합성 테스트 발언 {i}: 금융상품 가정과 조건 확인') for i in range(1,13)]}
        self.reg={self.vid:{'W00001':[]}}
        self.rows=[]
        for i,ix in enumerate(([1,2],[5,6],[9,10]),1):
            cid=f'C{i:05d}'
            self.reg[self.vid]['W00001'].append({'claim_id':cid,'cue_indices':ix,'source_text_sha256':sha(' | '.join(self.cues[self.vid][j-1].text for j in ix).encode()),'numeric_tokens':0})
            s=' | '.join(self.cues[self.vid][j-1].text for j in ix)
            ns=[{'cue_index':j,'start_ms':self.cues[self.vid][j-1].start_ms,'end_ms':self.cues[self.vid][j-1].end_ms,'text_private':self.cues[self.vid][j-1].text} for j in range(max(1,ix[0]-2),min(12,ix[-1]+2)+1)]
            self.rows.append({'schema':[V78_SCHEMA,V79_SCHEMA,SCHEMA][i-1],
             'video_no':1,'video_id':self.vid,'window_id':'W00001','claim_id':cid,'cue_indices':ix,
             'start_ms':self.cues[self.vid][ix[0]-1].start_ms,'end_ms':self.cues[self.vid][ix[-1]-1].end_ms,
             'source_excerpt_private':s,'source_excerpt_sha256':sha(s.encode()),'neighbor_cues_private':ns,
             'speaker_units':[{'act':'HYPOTHETICAL','interpretation':'가정된 금융 내용은 실물 원장 증명이 아니다.'}],
             'reviewer_guard':'가정 수익과 계좌별 상품조건을 원금보장이나 개인 승인의 사실로 오인하지 않는다.',
             'source_status':'SHADOW_UNRECONCILED_V75','semantic_method':'CHAT_CONTEXT_INTERPRETATION_NOT_GOLD',
             'fact_approved':False,'independent_gold':False,'personal_action_approved':False,
             'v75_membership_verified':False,'official_parent_merged':False})

    def check(self,old78=None,old79=None,new80=None):
        return validate_triplet(self.cues,self.reg,
             [deepcopy(self.rows[0])] if old78 is None else old78,
             [deepcopy(self.rows[1])] if old79 is None else old79,
             [deepcopy(self.rows[2])] if new80 is None else new80,
             n78=1,n79=1,n80=1,enforce_video_counts=False)

    def changed(self,attr,value):
        r=deepcopy(self.rows[2]);r[attr]=value;return [r]

    def test_accept_all_three_distinct_source_ids(self):
        r=self.check();self.assertEqual(r['three_stage_distinct_source_parents'],3)
        self.assertEqual(r['three_stage_interpretations'],3)
    def test_no_approval_and_pending_unchanged(self):
        r=self.check();self.assertFalse(r['p0_go']);self.assertFalse(r['personal_advice_approved']);self.assertEqual(r['v75_total_pending_unchanged'],887)
    def test_receipt_contains_no_source_text(self):self.assertNotIn('합성 테스트 발언',str(self.check()))
    def test_v78_v80_parent_overlap_rejected(self):
        r=deepcopy(self.rows[0]);r['schema']=SCHEMA
        with self.assertRaisesRegex(ValueError,'CROSS_VERSION_DUPLICATE_PARENT'):self.check(new80=[r])
    def test_v79_v80_parent_overlap_rejected(self):
        r=deepcopy(self.rows[1]);r['schema']=SCHEMA
        with self.assertRaisesRegex(ValueError,'CROSS_VERSION_DUPLICATE_PARENT'):self.check(new80=[r])
    def test_old_v78_v79_parent_overlap_rejected(self):
        r=deepcopy(self.rows[0]);r['schema']=V79_SCHEMA
        with self.assertRaisesRegex(ValueError,'DUPLICATE_V78_V79_PARENT_SOURCE_KEY'):self.check(old79=[r])
    def test_current_duplicate_parent_rejected(self):
        with self.assertRaisesRegex(ValueError,'DUPLICATE_SHADOW_PARENT'):
            validate_triplet(self.cues,self.reg,[self.rows[0]],[self.rows[1]],[self.rows[2],self.rows[2]],n78=1,n79=1,n80=2,enforce_video_counts=False)
    def test_new_schema_rejected(self):
        with self.assertRaisesRegex(ValueError,'V80_SCHEMA_REQUIRED'):self.check(new80=self.changed('schema',V79_SCHEMA))
    def test_false_independent_gold_rejected(self):
        with self.assertRaisesRegex(ValueError,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL'):self.check(new80=self.changed('independent_gold',True))
    def test_false_fact_approved_rejected(self):
        with self.assertRaisesRegex(ValueError,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL'):self.check(new80=self.changed('fact_approved',True))
    def test_false_advice_rejected(self):
        with self.assertRaisesRegex(ValueError,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL'):self.check(new80=self.changed('personal_action_approved',True))
    def test_false_v75_membership_rejected(self):
        with self.assertRaisesRegex(ValueError,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL'):self.check(new80=self.changed('v75_membership_verified',True))
    def test_false_official_merge_rejected(self):
        with self.assertRaisesRegex(ValueError,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL'):self.check(new80=self.changed('official_parent_merged',True))
    def test_false_completed_status_rejected(self):
        with self.assertRaisesRegex(ValueError,'FALSE_COMPLETION_STATUS'):self.check(new80=self.changed('source_status','OFFICIAL_COMPLETE'))
    def test_false_semantic_gold_rejected(self):
        with self.assertRaisesRegex(ValueError,'FALSE_SEMANTIC_GOLD'):self.check(new80=self.changed('semantic_method','INDEPENDENT_BLIND_GOLD'))
    def test_source_excerpt_tamper_rejected(self):
        with self.assertRaisesRegex(ValueError,'SOURCE_EXCERPT_OR_DIGEST_DRIFT'):self.check(new80=self.changed('source_excerpt_private','위조 인용'))
    def test_source_hash_tamper_rejected(self):
        with self.assertRaisesRegex(ValueError,'SOURCE_EXCERPT_OR_DIGEST_DRIFT'):self.check(new80=self.changed('source_excerpt_sha256','0'*64))
    def test_source_time_tamper_rejected(self):
        with self.assertRaisesRegex(ValueError,'TIME_FRAME_DRIFT'):self.check(new80=self.changed('start_ms',1))
    def test_source_neighbor_tamper_rejected(self):
        bad=deepcopy(self.rows[2]);bad['neighbor_cues_private'][0]['text_private']='수정';
        with self.assertRaisesRegex(ValueError,'NEIGHBOR_OR_TIME_DRIFT'):self.check(new80=[bad])
    def test_wrong_cue_indices_rejected(self):
        with self.assertRaisesRegex(ValueError,'ORIGINAL_CUE_INDEX_DRIFT'):self.check(new80=self.changed('cue_indices',[9]))
    def test_invalid_parent_key_rejected(self):
        with self.assertRaisesRegex(ValueError,'FOREIGN_ORIGINAL_PARENT'):self.check(new80=self.changed('claim_id','C99999'))
    def test_empty_interpretation_rejected(self):
        with self.assertRaisesRegex(ValueError,'SPEAKER_UNITS_REQUIRED'):self.check(new80=self.changed('speaker_units',[]))
    def test_invalid_speech_act_rejected(self):
        with self.assertRaisesRegex(ValueError,'SPEAKER_UNIT_INVALID'):self.check(new80=self.changed('speaker_units',[{'act':'CERTIFIED_TRUTH','interpretation':'이건 유효한 발언인가? 확인해야 한다.'}]))
    def test_missing_reviewer_guard_rejected(self):
        with self.assertRaisesRegex(ValueError,'REVIEWER_GUARD_REQUIRED'):self.check(new80=self.changed('reviewer_guard','없음'))
    def test_previous_v79_false_gold_rejected(self):
        bad=deepcopy(self.rows[1]);bad['independent_gold']=True
        with self.assertRaisesRegex(ValueError,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL'):self.check(old79=[bad])
    def test_previous_v78_false_gold_rejected(self):
        bad=deepcopy(self.rows[0]);bad['independent_gold']=True
        with self.assertRaisesRegex(ValueError,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL'):self.check(old78=[bad])
    def test_prior_zip_sha_tamper_rejected(self):
        with TemporaryDirectory() as tmp:
            dest=Path(tmp)/'priv.zip'
            with ZipFile(dest,'w') as z:z.writestr(V79_RECORD,b'[]')
            with self.assertRaisesRegex(ValueError,'PRIOR_BUNDLE_BYTES_CHANGED'):
                load_pinned_private_rows(dest,'0'*64,V79_RECORD,sha(b'[]'))
    def test_prior_zip_record_sha_tamper_rejected(self):
        with TemporaryDirectory() as tmp:
            dest=Path(tmp)/'priv.zip'
            with ZipFile(dest,'w') as z:z.writestr(V79_RECORD,b'[]')
            with self.assertRaisesRegex(ValueError,'PRIOR_RECORD_HASH_MISMATCH'):
                load_pinned_private_rows(dest,sha(dest.read_bytes()),V79_RECORD,'0'*64)
    def test_prior_zip_unsafe_path_rejected(self):
        with TemporaryDirectory() as tmp:
            dest=Path(tmp)/'priv.zip'
            with ZipFile(dest,'w') as z:z.writestr(V79_RECORD,b'[]');z.writestr('../escape.json',b'a')
            with self.assertRaisesRegex(ValueError,'PRIOR_BUNDLE_UNSAFE_PATH'):
                load_pinned_private_rows(dest,sha(dest.read_bytes()),V79_RECORD,sha(b'[]'))
    def test_prior_zip_duplicate_record_rejected(self):
        with TemporaryDirectory() as tmp:
            dest=Path(tmp)/'priv.zip'
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',UserWarning)
                with ZipFile(dest,'w') as z:z.writestr(V79_RECORD,b'[]');z.writestr(V79_RECORD,b'[]')
            with self.assertRaisesRegex(ValueError,'PRIOR_BUNDLE_DUPLICATE_OR_MISSING_RECORD'):
                load_pinned_private_rows(dest,sha(dest.read_bytes()),V79_RECORD,sha(b'[]'))
if __name__=='__main__':unittest.main()