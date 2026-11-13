"""Synthetic V79 provenance and no-false-GO tests, no owner source text."""
import json
import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
from v77_private_v33_replay import Cue,sha
from v78_shadow_source_custody import SCHEMA as V78_SCHEMA
from v79_shadow_delta_guard import SCHEMA,validate_delta,read_v78_anchor,V78_RECORD_FILENAME

class V79Tests(unittest.TestCase):
    def setUp(self):
        self.vid='Synthetic01'
        self.cues={self.vid:[Cue(i,i*100,(i+1)*100,f'샘플 발언 {i} 가정과 유의사항') for i in range(1,9)]}
        self.reg={self.vid:{'W00001':[]}}
        self.rows=[]
        for j,grp in enumerate(([1,2],[4,5]),1):
            excerpt=' | '.join(self.cues[self.vid][i-1].text for i in grp)
            cid=f'C{j:05d}'
            self.reg[self.vid]['W00001'].append({'claim_id':cid,'cue_indices':grp,'source_text_sha256':sha(excerpt.encode()),'numeric_tokens':0})
            first,last=max(1,grp[0]-2),min(8,grp[-1]+2)
            self.rows.append({'schema':V78_SCHEMA if j==1 else SCHEMA,'video_no':1,'video_id':self.vid,
                'window_id':'W00001','claim_id':cid,'cue_indices':grp,
                'start_ms':self.cues[self.vid][grp[0]-1].start_ms,'end_ms':self.cues[self.vid][grp[-1]-1].end_ms,
                'source_excerpt_private':excerpt,'source_excerpt_sha256':sha(excerpt.encode()),
                'neighbor_cues_private':[{'cue_index':i,'start_ms':self.cues[self.vid][i-1].start_ms,
                                          'end_ms':self.cues[self.vid][i-1].end_ms,'text_private':self.cues[self.vid][i-1].text}
                                         for i in range(first,last+1)],
                'speaker_units':[{'act':'HYPOTHETICAL','interpretation':'가정적 금융상품 사례를 교육적으로 설명한다.'}],
                'reviewer_guard':'원금이나 수익률의 보장 또는 금융 진실 승인으로 해석할 수 없다.',
                'source_status':'SHADOW_UNRECONCILED_V75','semantic_method':'CHAT_CONTEXT_INTERPRETATION_NOT_GOLD',
                'fact_approved':False,'independent_gold':False,'personal_action_approved':False,
                'v75_membership_verified':False,'official_parent_merged':False})

    def check(self,p=None,n=None):
        return validate_delta(self.cues,self.reg,[self.rows[0]] if p is None else p,
                              [self.rows[1]] if n is None else n,prev_count=1,new_count=1,enforce_four_per_video=False)
    def test_valid_two_distinct_shadow_parents(self):
        o=self.check();self.assertEqual(o['v78_v79_joint_distinct_source_parents'],2)
        self.assertEqual(o['v78_v79_overlap'],0);self.assertEqual(o['v75_official_parent_count_increment'],0)
        self.assertNotIn('샘플 발언',str(o))
    def test_no_official_pending_reduction(self):
        self.assertEqual(self.check()['v75_total_remaining_unchanged'],887)
        self.assertFalse(self.check()['p0_go'])
    def test_cross_version_duplicate_rejected(self):
        r=deepcopy(self.rows[0]);r['schema']=SCHEMA
        with self.assertRaisesRegex(ValueError,'DUPLICATE_V78_V79_PARENT_SOURCE_KEY'):self.check(n=[r])
    def test_new_schema_must_be_v79(self):
        r=deepcopy(self.rows[1]);r['schema']=V78_SCHEMA
        with self.assertRaisesRegex(ValueError,'V79_NEW_SHADOW_SCHEMA_REQUIRED'):self.check(n=[r])
    def test_duplicate_current_rejected(self):
        with self.assertRaisesRegex(ValueError,'DUPLICATE_SHADOW_PARENT'):
            validate_delta(self.cues,self.reg,[self.rows[0]],[self.rows[1],self.rows[1]],prev_count=1,new_count=2,enforce_four_per_video=False)
    def test_previous_source_tamper_rejected(self):
        r=deepcopy(self.rows[0]);r['source_excerpt_private']='다른 발언'
        with self.assertRaisesRegex(ValueError,'SOURCE_EXCERPT_OR_DIGEST_DRIFT'):self.check(p=[r])
    def test_new_source_tamper_rejected(self):
        r=deepcopy(self.rows[1]);r['source_excerpt_private']='다른 발언'
        with self.assertRaisesRegex(ValueError,'SOURCE_EXCERPT_OR_DIGEST_DRIFT'):self.check(n=[r])
    def test_new_time_tamper_rejected(self):
        r=deepcopy(self.rows[1]);r['end_ms']+=10
        with self.assertRaisesRegex(ValueError,'TIME_FRAME_DRIFT'):self.check(n=[r])
    def test_new_neighbor_tamper_rejected(self):
        r=deepcopy(self.rows[1]);r['neighbor_cues_private'][0]['text_private']='조작'
        with self.assertRaisesRegex(ValueError,'NEIGHBOR_OR_TIME_DRIFT'):self.check(n=[r])
    def test_previous_false_gold_rejected(self):
        r=deepcopy(self.rows[0]);r['independent_gold']=True
        with self.assertRaisesRegex(ValueError,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL'):self.check(p=[r])
    def test_new_false_gold_rejected(self):
        r=deepcopy(self.rows[1]);r['independent_gold']=True
        with self.assertRaisesRegex(ValueError,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL'):self.check(n=[r])
    def test_new_false_v75_membership_rejected(self):
        r=deepcopy(self.rows[1]);r['v75_membership_verified']=True
        with self.assertRaisesRegex(ValueError,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL'):self.check(n=[r])
    def test_new_false_personal_advice_rejected(self):
        r=deepcopy(self.rows[1]);r['personal_action_approved']=True
        with self.assertRaisesRegex(ValueError,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL'):self.check(n=[r])
    def test_new_false_official_merge_rejected(self):
        r=deepcopy(self.rows[1]);r['official_parent_merged']=True
        with self.assertRaisesRegex(ValueError,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL'):self.check(n=[r])
    def test_new_no_reviewer_guard_rejected(self):
        r=deepcopy(self.rows[1]);r['reviewer_guard']='ok'
        with self.assertRaisesRegex(ValueError,'REVIEWER_GUARD_REQUIRED'):self.check(n=[r])
    def test_new_no_semantic_interpretation_rejected(self):
        r=deepcopy(self.rows[1]);r['speaker_units']=[]
        with self.assertRaisesRegex(ValueError,'SPEAKER_UNITS_REQUIRED'):self.check(n=[r])
    def test_new_unverified_act_rejected(self):
        r=deepcopy(self.rows[1]);r['speaker_units'][0]['act']='CERTIFIED_FACT'
        with self.assertRaisesRegex(ValueError,'SPEAKER_UNIT_INVALID'):self.check(n=[r])
    def test_new_false_completed_status_rejected(self):
        r=deepcopy(self.rows[1]);r['source_status']='OFFICIAL_COMPLETE'
        with self.assertRaisesRegex(ValueError,'FALSE_COMPLETION_STATUS'):self.check(n=[r])
    def test_old_archive_integrity_check(self):
        with TemporaryDirectory() as d:
            f=Path(d)/'old.zip'
            content=json.dumps([self.rows[0]],ensure_ascii=False).encode()
            with ZipFile(f,'w') as z:z.writestr(V78_RECORD_FILENAME,content)
            out=read_v78_anchor(f,expected_zip_sha=sha(f.read_bytes()),expected_records_sha=sha(content))
            self.assertEqual(len(out),1)
            with self.assertRaisesRegex(ValueError,'V78_PREVIOUS_BUNDLE_SHA_MISMATCH'):
                read_v78_anchor(f,expected_zip_sha='0'*64,expected_records_sha=sha(content))
    def test_old_archive_record_integrity_rejected(self):
        with TemporaryDirectory() as d:
            f=Path(d)/'old.zip'
            with ZipFile(f,'w') as z:z.writestr(V78_RECORD_FILENAME,b'[]')
            with self.assertRaisesRegex(ValueError,'V78_PREVIOUS_RECORD_SHA_MISMATCH'):
                read_v78_anchor(f,expected_zip_sha=sha(f.read_bytes()),expected_records_sha='0'*64)

if __name__=='__main__':unittest.main()