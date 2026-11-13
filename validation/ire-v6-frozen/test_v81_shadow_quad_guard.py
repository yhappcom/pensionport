"""Public-safe V81 4-stage source custody synthetic tests. No private SRT."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
import unittest,warnings
from v77_private_v33_replay import Cue,sha
from v78_shadow_source_custody import SCHEMA as S78
from v79_shadow_delta_guard import SCHEMA as S79
from v80_shadow_triplet_guard import SCHEMA as S80,load_pinned_private_rows
from v81_shadow_quad_guard import V80_RECORD
from v81_shadow_quad_guard import SCHEMA as S81,validate_quad

class QuadTests(unittest.TestCase):
    def setUp(self):
        vid='SYNTHETIC01'
        self.vid=vid
        self.cues={vid:[Cue(i,i*500,(i+1)*500, f'합성 금융 문맥 발화 {i}: 질문과 조건이 있는 자료') for i in range(1,21)]}
        self.reg={vid:{'W00001':[]}}
        self.rows=[]
        for i,indices in enumerate(([1,2],[5,6],[9,10],[13,14]),1):
            text=' | '.join(self.cues[vid][q-1].text for q in indices)
            cid=f'C{i:05d}';s=sha(text.encode('utf-8'))
            self.reg[vid]['W00001'].append({'claim_id':cid,'cue_indices':list(indices),'source_text_sha256':s,'numeric_tokens':0})
            halo=[{'cue_index':q,'start_ms':self.cues[vid][q-1].start_ms,'end_ms':self.cues[vid][q-1].end_ms,'text_private':self.cues[vid][q-1].text}
                  for q in range(max(1,indices[0]-2),min(20,indices[-1]+2)+1)]
            self.rows.append({'schema':[S78,S79,S80,S81][i-1],
                'video_no':1,'video_id':vid,'window_id':'W00001','claim_id':cid,'cue_indices':list(indices),
                'start_ms':self.cues[vid][indices[0]-1].start_ms,'end_ms':self.cues[vid][indices[-1]-1].end_ms,
                'source_excerpt_private':text,'source_excerpt_sha256':s,'neighbor_cues_private':halo,
                'speaker_units':[{'act':'HYPOTHETICAL','interpretation':'합성 예시는 실제 금융사실이 아닙니다.'}],
                'reviewer_guard':'계좌별 상품별 위험을 충분히 확인할 때까지 금융사실 또는 개인자문을 승인하지 않습니다.',
                'source_status':'SHADOW_UNRECONCILED_V75','semantic_method':'CHAT_CONTEXT_INTERPRETATION_NOT_GOLD',
                'fact_approved':False,'independent_gold':False,'personal_action_approved':False,
                'v75_membership_verified':False,'official_parent_merged':False})

    def check(self,rows=None):
        xs=[deepcopy(r) for r in (self.rows if rows is None else rows)]
        return validate_quad(self.cues,self.reg,*[[x] for x in xs],counts=(1,1,1,1),enforce_video_counts=False)

    def mutate(self,step,field,value):
        xs=deepcopy(self.rows)
        xs[step][field]=value
        return xs

    def rejects(self,step,field,value,code):
        with self.assertRaisesRegex(ValueError,code):self.check(self.mutate(step,field,value))

    def test_valid_four_records(self):
        x=self.check();self.assertEqual(x['four_stage_source_parents_unique'],4)
        self.assertEqual(x['four_stage_semantic_or_nonclaim_units'],4)
    def test_no_approval_and_887_pending(self):
        x=self.check();self.assertFalse(x['p0_go']);self.assertFalse(x['personal_advice_approved']);self.assertFalse(x['independent_gold']);self.assertEqual(x['v75_total_pending_unchanged'],887)
    def test_no_private_text_leak_to_receipt(self):self.assertNotIn('합성 금융 문맥 발화',str(self.check()))
    def test_identity_sha_present(self):self.assertEqual(len(self.check()['four_stage_source_review_sha256']),64)
    def test_overlap_with_v78(self):
        xs=deepcopy(self.rows);xs[3]=deepcopy(xs[0]);xs[3]['schema']=S81
        with self.assertRaisesRegex(ValueError,'CROSS_GENERATION_SOURCE_ID_COLLISION'):self.check(xs)
    def test_overlap_with_v79(self):
        xs=deepcopy(self.rows);xs[3]=deepcopy(xs[1]);xs[3]['schema']=S81
        with self.assertRaisesRegex(ValueError,'CROSS_GENERATION_SOURCE_ID_COLLISION'):self.check(xs)
    def test_overlap_with_v80(self):
        xs=deepcopy(self.rows);xs[3]=deepcopy(xs[2]);xs[3]['schema']=S81
        with self.assertRaisesRegex(ValueError,'CROSS_GENERATION_SOURCE_ID_COLLISION'):self.check(xs)
    def test_old_v78_v79_overlap(self):
        xs=deepcopy(self.rows);xs[1]=deepcopy(xs[0]);xs[1]['schema']=S79
        with self.assertRaisesRegex(ValueError,'DUPLICATE_V78_V79_PARENT_SOURCE_KEY'):self.check(xs)
    def test_old_v78_v80_overlap(self):
        xs=deepcopy(self.rows);xs[2]=deepcopy(xs[0]);xs[2]['schema']=S80
        with self.assertRaisesRegex(ValueError,'CROSS_VERSION_DUPLICATE_PARENT'):self.check(xs)
    def test_old_v79_v80_overlap(self):
        xs=deepcopy(self.rows);xs[2]=deepcopy(xs[1]);xs[2]['schema']=S80
        with self.assertRaisesRegex(ValueError,'CROSS_VERSION_DUPLICATE_PARENT'):self.check(xs)
    def test_wrong_four_generation_count(self):
        with self.assertRaisesRegex(ValueError,'EXACT_FOUR_GENERATION_COUNTS_REQUIRED'):
            validate_quad(self.cues,self.reg,*[[r] for r in self.rows],counts=(1,1,1),enforce_video_counts=False)
    def test_new_empty_rejected(self):
        with self.assertRaisesRegex(ValueError,'NEW_PARENT_CENSUS_DRIFT'):
            validate_quad(self.cues,self.reg,*[[r] for r in self.rows[:3]],[],counts=(1,1,1,1),enforce_video_counts=False)
    def test_wrong_new_record_count(self):
        with self.assertRaisesRegex(ValueError,'NEW_PARENT_CENSUS_DRIFT'):
            validate_quad(self.cues,self.reg,*[[r] for r in self.rows[:3]],[self.rows[3]]*2,counts=(1,1,1,1),enforce_video_counts=False)
    def test_schema_forgery(self):self.rejects(3,'schema',S80,'NEW_SCHEMA_DRIFT')
    def test_foreign_source_parent(self):self.rejects(3,'claim_id','C99999','FOREIGN_ORIGINAL_PARENT')
    def test_source_video_number(self):self.rejects(3,'video_no',2,'VIDEO_OWNERSHIP_MISMATCH')
    def test_source_text_forgery(self):self.rejects(3,'source_excerpt_private','조작된 자막','SOURCE_EXCERPT_OR_DIGEST_DRIFT')
    def test_source_sha_forgery(self):self.rejects(3,'source_excerpt_sha256','f'*64,'SOURCE_EXCERPT_OR_DIGEST_DRIFT')
    def test_cue_indices_forgery(self):self.rejects(3,'cue_indices',[14],'ORIGINAL_CUE_INDEX_DRIFT')
    def test_start_time_forgery(self):self.rejects(3,'start_ms',0,'TIME_FRAME_DRIFT')
    def test_end_time_forgery(self):self.rejects(3,'end_ms',999999,'TIME_FRAME_DRIFT')
    def test_neighbor_context_forgery(self):
        bad=deepcopy(self.rows[3]['neighbor_cues_private']);bad[0]['text_private']='가짜';self.rejects(3,'neighbor_cues_private',bad,'NEIGHBOR_OR_TIME_DRIFT')
    def test_empty_speaker_units(self):self.rejects(3,'speaker_units',[],'SPEAKER_UNITS_REQUIRED')
    def test_fake_gold_act(self):self.rejects(3,'speaker_units',[{'act':'FACT_PROVEN','interpretation':'사실을 실제로 승인합니다.'}],'SPEAKER_UNIT_INVALID')
    def test_empty_guard(self):self.rejects(3,'reviewer_guard','','REVIEWER_GUARD_REQUIRED')
    def test_false_finance_fact_approval(self):self.rejects(3,'fact_approved',True,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL')
    def test_false_gold_approval(self):self.rejects(3,'independent_gold',True,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL')
    def test_false_personal_advice(self):self.rejects(3,'personal_action_approved',True,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL')
    def test_false_v75_membership(self):self.rejects(3,'v75_membership_verified',True,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL')
    def test_false_official_merge(self):self.rejects(3,'official_parent_merged',True,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL')
    def test_false_old_v78_gold(self):self.rejects(0,'independent_gold',True,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL')
    def test_false_old_v79_gold(self):self.rejects(1,'independent_gold',True,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL')
    def test_false_old_v80_gold(self):self.rejects(2,'independent_gold',True,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL')
    def test_false_completed_status(self):self.rejects(3,'source_status','COMPLETE','FALSE_COMPLETION_STATUS')
    def test_false_semantic_method(self):self.rejects(3,'semantic_method','EXTERNAL_BLIND_GOLD','FALSE_SEMANTIC_GOLD')
    def test_false_prior_v78_completion(self):self.rejects(0,'source_status','OFFICIALLY_COMPLETE','FALSE_COMPLETION_STATUS')
    def test_old_sha_invalid(self):
        with TemporaryDirectory() as t:
            p=Path(t)/'bundle.zip'
            with ZipFile(p,'w') as z:z.writestr(V80_RECORD,b'[]')
            with self.assertRaisesRegex(ValueError,'PRIOR_BUNDLE_BYTES_CHANGED'):
                load_pinned_private_rows(p,'f'*64,V80_RECORD,sha(b'[]'))
    def test_old_record_hash_invalid(self):
        with TemporaryDirectory() as t:
            p=Path(t)/'bundle.zip'
            with ZipFile(p,'w') as z:z.writestr(V80_RECORD,b'[]')
            with self.assertRaisesRegex(ValueError,'PRIOR_RECORD_HASH_MISMATCH'):
                load_pinned_private_rows(p,sha(p.read_bytes()),V80_RECORD,'f'*64)
    def test_prior_zip_traversal(self):
        with TemporaryDirectory() as t:
            p=Path(t)/'bundle.zip'
            with ZipFile(p,'w') as z:z.writestr(V80_RECORD,b'[]');z.writestr('../unsafe.bin',b'')
            with self.assertRaisesRegex(ValueError,'PRIOR_BUNDLE_UNSAFE_PATH'):
                load_pinned_private_rows(p,sha(p.read_bytes()),V80_RECORD,sha(b'[]'))
    def test_prior_zip_duplicate(self):
        with TemporaryDirectory() as t:
            p=Path(t)/'bundle.zip'
            with warnings.catch_warnings():
                warnings.simplefilter('ignore',UserWarning)
                with ZipFile(p,'w') as z:z.writestr(V80_RECORD,b'[]');z.writestr(V80_RECORD,b'[]')
            with self.assertRaisesRegex(ValueError,'PRIOR_BUNDLE_DUPLICATE_OR_MISSING_RECORD'):
                load_pinned_private_rows(p,sha(p.read_bytes()),V80_RECORD,sha(b'[]'))

if __name__=='__main__':unittest.main()