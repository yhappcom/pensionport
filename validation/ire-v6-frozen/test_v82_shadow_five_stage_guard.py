"""V82 public-safe synthetic negative tests: five separate lineage gates.

No private SRT, ChatGPT source notes, owner financial information or
independent gold labels are used to populate these test fixtures.
"""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
import unittest, warnings
from v77_private_v33_replay import Cue,sha
from v78_shadow_source_custody import SCHEMA as S78
from v79_shadow_delta_guard import SCHEMA as S79
from v80_shadow_triplet_guard import SCHEMA as S80,load_pinned_private_rows
from v81_shadow_quad_guard import SCHEMA as S81
from v82_shadow_five_stage_guard import (SCHEMA as S82,validate_five,key,V81_RECORD)

class FiveStageShadowTests(unittest.TestCase):
    def setUp(self):
        self.vid='SYNTHETIC01'
        self.cues={self.vid:[Cue(i,i*500,(i+1)*500,'합성 계좌 원문 금액 위험 문맥 '+str(i)) for i in range(1,31)]}
        self.registry={self.vid:{'W00001':[]}}
        self.rows=[]
        for n,idx in enumerate(([1,2],[6,7],[11,12],[16,17],[21,22]),1):
            excerpt=' | '.join(self.cues[self.vid][i-1].text for i in idx)
            cid='C'+str(n).zfill(5)
            self.registry[self.vid]['W00001'].append({'claim_id':cid,'cue_indices':list(idx),
                'source_text_sha256':sha(excerpt.encode('utf8')),'numeric_tokens':0})
            halo=[{'cue_index':i,'start_ms':self.cues[self.vid][i-1].start_ms,
                   'end_ms':self.cues[self.vid][i-1].end_ms,'text_private':self.cues[self.vid][i-1].text}
                   for i in range(max(1,idx[0]-2),min(30,idx[-1]+2)+1)]
            self.rows.append({
                'schema':(S78,S79,S80,S81,S82)[n-1],
                'video_no':1,'video_id':self.vid,'window_id':'W00001','claim_id':cid,
                'cue_indices':list(idx),
                'start_ms':self.cues[self.vid][idx[0]-1].start_ms,
                'end_ms':self.cues[self.vid][idx[-1]-1].end_ms,
                'source_excerpt_private':excerpt,'source_excerpt_sha256':sha(excerpt.encode('utf8')),
                'neighbor_cues_private':halo,
                'speaker_units':[{'act':'NUMERIC_HYPOTHETICAL','interpretation':'합성 예시의 세금은 실제 금융사실이 아닙니다.'}],
                'reviewer_guard':'합성 금융 위험은 독립 사실 또는 개인정보 자문으로 승인하지 않으며 원문을 보존합니다.',
                'source_status':'SHADOW_UNRECONCILED_V75',
                'semantic_method':'CHAT_CONTEXT_INTERPRETATION_NOT_GOLD',
                'fact_approved':False,'independent_gold':False,'personal_action_approved':False,
                'v75_membership_verified':False,'official_parent_merged':False,
            })

    def check(self,rs=None,counts=(1,1,1,1,1)):
        rows=deepcopy(self.rows if rs is None else rs)
        return validate_five(self.cues,self.registry,*[[r] for r in rows],
                             counts=counts,enforce_video_counts=False)

    def mutate(self,stage,field,value):
        rs=deepcopy(self.rows);rs[stage][field]=value;return rs

    def rejects(self,stage,field,value,expected):
        with self.assertRaisesRegex(ValueError,expected):
            self.check(self.mutate(stage,field,value))

    def test_positive_five_unique(self):
        x=self.check();self.assertEqual(x['five_stage_unique_parent_reviews'],5)
    def test_positive_interpretation_count(self):
        x=self.check();self.assertEqual(x['five_stage_meaning_or_nonclaim_units'],5)
    def test_five_stage_collision_zero(self):self.assertEqual(self.check()['five_stage_source_parent_collisions'],0)
    def test_pending_887_not_decremented(self):self.assertEqual(self.check()['v75_total_pending_unchanged'],887)
    def test_zero_official_parent_increment(self):self.assertEqual(self.check()['official_v75_parent_count_increment'],0)
    def test_v75_membership_unknown(self):self.assertFalse(self.check()['v75_original_404_parent_membership_verified'])
    def test_no_independent_gold(self):self.assertFalse(self.check()['independent_gold'])
    def test_no_financial_truth_certification(self):self.assertFalse(self.check()['financial_fact_truth_certified'])
    def test_no_personal_advice(self):self.assertFalse(self.check()['personal_advice_approved'])
    def test_no_p0_go(self):self.assertFalse(self.check()['p0_go'])
    def test_no_raw_source_exposed_in_public(self):self.assertNotIn('합성 계좌',str(self.check()))
    def test_sha_only_five_stage_digest(self):self.assertEqual(len(self.check()['five_stage_source_review_sha256']),64)
    def test_missing_stage_count(self):
        with self.assertRaisesRegex(ValueError,'COUNTS_REQUIRED'):
            self.check(counts=(1,1,1,1))
    def test_new_empty_rejected(self):
        with self.assertRaisesRegex(ValueError,'NEW_PARENT_COUNT_DRIFT'):
            validate_five(self.cues,self.registry,*[[r] for r in self.rows[:4]],[],
                          counts=(1,1,1,1,1),enforce_video_counts=False)
    def test_new_wrong_schema(self):self.rejects(4,'schema',S81,'NEW_SCHEMA_DRIFT')
    def test_duplicate_with_v78(self):
        x=deepcopy(self.rows);x[4]=deepcopy(x[0]);x[4]['schema']=S82
        with self.assertRaisesRegex(ValueError,'CROSS_GENERATION_SOURCE_ID_COLLISION'):self.check(x)
    def test_duplicate_with_v79(self):
        x=deepcopy(self.rows);x[4]=deepcopy(x[1]);x[4]['schema']=S82
        with self.assertRaisesRegex(ValueError,'CROSS_GENERATION_SOURCE_ID_COLLISION'):self.check(x)
    def test_duplicate_with_v80(self):
        x=deepcopy(self.rows);x[4]=deepcopy(x[2]);x[4]['schema']=S82
        with self.assertRaisesRegex(ValueError,'CROSS_GENERATION_SOURCE_ID_COLLISION'):self.check(x)
    def test_duplicate_with_v81(self):
        x=deepcopy(self.rows);x[4]=deepcopy(x[3]);x[4]['schema']=S82
        with self.assertRaisesRegex(ValueError,'CROSS_GENERATION_SOURCE_ID_COLLISION'):self.check(x)
    def test_false_v78_gold(self):self.rejects(0,'independent_gold',True,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL')
    def test_false_v79_fact_approval(self):self.rejects(1,'fact_approved',True,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL')
    def test_false_v80_membership(self):self.rejects(2,'v75_membership_verified',True,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL')
    def test_false_v81_merge(self):self.rejects(3,'official_parent_merged',True,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL')
    def test_false_v82_membership(self):self.rejects(4,'v75_membership_verified',True,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL')
    def test_false_v82_gold(self):self.rejects(4,'independent_gold',True,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL')
    def test_false_v82_personal_advice(self):self.rejects(4,'personal_action_approved',True,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL')
    def test_false_v82_official_merge(self):self.rejects(4,'official_parent_merged',True,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL')
    def test_false_new_fact_approval(self):self.rejects(4,'fact_approved',True,'FALSE_FACT_OR_MEMBERSHIP_APPROVAL')
    def test_false_new_status(self):self.rejects(4,'source_status','OFFICIALLY_COMPLETE','FALSE_COMPLETION_STATUS')
    def test_false_new_method(self):self.rejects(4,'semantic_method','EXTERNAL_BLIND_GOLD','FALSE_SEMANTIC_GOLD')
    def test_foreign_candidate(self):self.rejects(4,'claim_id','C99999','FOREIGN_ORIGINAL_PARENT')
    def test_wrong_video_number(self):self.rejects(4,'video_no',2,'VIDEO_OWNERSHIP_MISMATCH')
    def test_wrong_cue_indices(self):self.rejects(4,'cue_indices',[22],'ORIGINAL_CUE_INDEX_DRIFT')
    def test_wrong_source_text(self):self.rejects(4,'source_excerpt_private','변조 본문','SOURCE_EXCERPT_OR_DIGEST_DRIFT')
    def test_wrong_source_sha(self):self.rejects(4,'source_excerpt_sha256','f'*64,'SOURCE_EXCERPT_OR_DIGEST_DRIFT')
    def test_wrong_start_time(self):self.rejects(4,'start_ms',0,'TIME_FRAME_DRIFT')
    def test_wrong_end_time(self):self.rejects(4,'end_ms',0,'TIME_FRAME_DRIFT')
    def test_empty_speaker_units(self):self.rejects(4,'speaker_units',[],'SPEAKER_UNITS_REQUIRED')
    def test_false_factual_speaker_act(self):
        self.rejects(4,'speaker_units',[{'act':'FACT_PROVEN','interpretation':'합성 원문을 금융 정답으로 승인합니다.'}],'SPEAKER_UNIT_INVALID')
    def test_missing_reviewer_guard(self):self.rejects(4,'reviewer_guard','','REVIEWER_GUARD_REQUIRED')
    def test_tampered_halo(self):
        h=deepcopy(self.rows[4]['neighbor_cues_private']);h[-1]['text_private']='변조'
        self.rejects(4,'neighbor_cues_private',h,'NEIGHBOR_OR_TIME_DRIFT')
    def test_record_has_pinned_source_key(self):self.assertEqual(key(self.rows[4]),('SYNTHETIC01','W00001','C00005'))
    def test_pinned_bundle_rejects_bad_archive_sha(self):
        with TemporaryDirectory() as t:
            p=Path(t)/'archive.zip'
            with ZipFile(p,'w') as z:z.writestr(V81_RECORD,b'[]')
            with self.assertRaisesRegex(ValueError,'PRIOR_BUNDLE_BYTES_CHANGED'):
                load_pinned_private_rows(p,'f'*64,V81_RECORD,sha(b'[]'))
    def test_pinned_bundle_rejects_missing_record(self):
        with TemporaryDirectory() as t:
            p=Path(t)/'archive.zip'
            with ZipFile(p,'w') as z:z.writestr('wrong.json',b'[]')
            with self.assertRaisesRegex(ValueError,'PRIOR_BUNDLE_DUPLICATE_OR_MISSING_RECORD'):
                load_pinned_private_rows(p,sha(p.read_bytes()),V81_RECORD,sha(b'[]'))
    def test_pinned_bundle_rejects_wrong_record_sha(self):
        with TemporaryDirectory() as t:
            p=Path(t)/'archive.zip'
            with ZipFile(p,'w') as z:z.writestr(V81_RECORD,b'[]')
            with self.assertRaisesRegex(ValueError,'PRIOR_RECORD_HASH_MISMATCH'):
                load_pinned_private_rows(p,sha(p.read_bytes()),V81_RECORD,'f'*64)
    def test_pinned_bundle_rejects_path_escape(self):
        with TemporaryDirectory() as t:
            p=Path(t)/'archive.zip'
            with ZipFile(p,'w') as z:z.writestr(V81_RECORD,b'[]');z.writestr('../outside',b'bad')
            with self.assertRaisesRegex(ValueError,'PRIOR_BUNDLE_UNSAFE_PATH'):
                load_pinned_private_rows(p,sha(p.read_bytes()),V81_RECORD,sha(b'[]'))

if __name__=='__main__':unittest.main()