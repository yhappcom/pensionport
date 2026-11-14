"""Public synthetic guard tests, never contain owner-private SRT or real claims."""
from __future__ import annotations
import copy, json, tempfile, unittest
from pathlib import Path

from v115_full_video_bridge import (audit_private_review, assert_public_replay_receipt,
                                    resume_prepared_five_stage_run, sha, digest,
                                    UnsafeResearchStage)
from ire.v6.research_pipeline_v114 import V114ResearchJournal, ZERO

FIXTURE_PATH=Path(__file__).parent/'V115_ACTUAL_152CUE_REAL_SOURCE_FIVE_STAGE_SHA_ONLY.json'
if not FIXTURE_PATH.exists():
    FIXTURE_PATH=Path(__file__).parent/'public'/'V115_ACTUAL_152CUE_REAL_SOURCE_FIVE_STAGE_SHA_ONLY.json'

def fake():
    txt=['회사 주식 ETF', '분배 정책이 서로', '다를 수 있습니다.',
         '여기는 조건 설명', '앞의 내용을 확인', '이상입니다.']
    cues=[];blocks=[]
    for i,t in enumerate(txt,1):
        blocks.append(f'{i}\n00:00:{i:02},000 --> 00:00:{i+1:02},000\n{t}')
        cues.append({'cue_index':i,'sha256':sha(t)})
    raw=('\n\n'.join(blocks)+'\n').encode()
    def atom(num,start,end,role,group):
        arr=list(range(start,end+1)); hashes=[cues[i-1]['sha256'] for i in arr]
        return {'unit_id':f'TEST_A{num:03d}','cue_indices':arr,'cue_sha256':hashes,
                'source_span_digest':sha(''.join(hashes)),
                'owner_private_paraphrase':f'{num}번 검문용 의미',
                'speaker_stance':'AFFIRMED' if group else 'CONTEXT_ONLY',
                'risk_level':'LOW' if group else 'CONTEXT_ONLY','official_check_group':group,
                'reviewer_conditions':{}, 'origin':'SINGLE_CHAT_REVIEW_OF_REAL_ORIGINAL_SRT',
                'speaker_audio_confirmed':False,'independent_gold':False,
                'financial_fact_approved':False,'knowledge_merge_approved':False}
    whole=sha(' '.join(txt))
    ledger={'source_sha256':sha(raw),'source_original_zip_sha256':'f'*64,
            'source_video_id':'7RRWNL0V6As','source_cues':6,'source_windows':1,
            'source_cue_hashes':cues,
            'parents':[{'parent_id':'TEST_P001','first_cue':1,'last_cue':6,
                        'cue_indices':list(range(1,7)),'speech_act':'EXPLANATION',
                        'speaker':'NARRATOR_PRESUMED_NOT_AUDIO_VERIFIED',
                        'source_text_sha256':whole,
                        'source_meaning_claims_verified_independently':False}],
            'atom_proposals':[atom(1,1,3,'FACT','KRX_DISTRIBUTION'),
                              atom(2,4,6,'CONTEXT',None)],
            'original_audio_verified':False,'original_video_screen_verified':False,
            'independent_gold':False,'semantics_complete_certified':False,
            'p0_go':False,'precision':None,'recall':None}
    docket=[{'unit_id':'TEST_A001','source_cue_indices':[1,2,3],
             'official_reference_urls':['https://regulation.krx.co.kr/contents/fake'],
             'checked_date':'2026-11-14','status':'GENERAL_SCOPE_OPEN',
             'must_verify_product_screens':False,'official_body_content_hash_verified':False,
             'personal_applicability_verified':False,'approved':False}]
    return raw,ledger,docket

def payloads():
    s='a'*64
    return {
      'SOURCE':{'source_cues':6,'source_windows':1,'source_sha256':s,
                'owner_private_replay_digest_sha256':s,'unaccounted_source_cues':0,
                'structure_wall_ns':123},
      'SEMANTIC':{'parents':1,'semantic_units':2,'classified_cues':6,
                  'unassigned_cues':0,'open_units':1,'meaning_review_approved':False,
                  'semantic_artifact_sha256':s,'structure_wall_ns':3},
      'FINANCE':{'financial_fact_candidates':1,'official_reference_count':1,
                 'official_reference_metadata_sha256':s,'official_primary_snapshot_verified':False,
                 'current_law_scope_checked':True,'unresolved_evidence_units':1,
                 'financial_fact_approved':0,'personal_tax_approved':False,
                 'finance_artifact_sha256':s,'structure_wall_ns':42},
      'METRICS':{'source_parse_wall_ns':123,'semantic_structure_wall_ns':3,
                 'finance_structure_wall_ns':42,'p1_preview_wall_ns':0,
                 'model_semantic_wall_ns':None,'official_search_wall_ns':None,
                 'open_resolution_wall_ns':None,'independent_adjudication_wall_ns':None,
                 'observed_artifact_sha256':s},
      'KNOWLEDGE':{'candidate_relations':0,'historical_overlap_positions':0,
                   'historical_reconciliation_complete':False,'v75_identity_recovered':False,
                   'knowledge_merge_count':0,'knowledge_preview_sha256':s,
                   'structure_wall_ns':0},
    }

class OriginalCensusGuard(unittest.TestCase):
    def check(self,raw,ledger,docket):
        return audit_private_review(raw_srt=raw,ledger=ledger,docket=docket,
                expected_srt_sha256=sha(raw),expected_zip_sha256='f'*64,
                private_zip_sha256='f'*64)
    def test_actual_review_fixture(self):
        a,b,c=fake();out=self.check(a,b,c)
        self.assertEqual((out['original_cues'],out['all_source_cues_accounted'],
                          out['pending_finance_docket_rows']),(6,6,1))
        self.assertFalse(out['p0_go'])
    def test_source_sha_mutation_rejected(self):
        a,b,c=fake();b['source_sha256']='a'*64
        with self.assertRaises(UnsafeResearchStage):self.check(a,b,c)
    def test_source_zip_pin_mutation_rejected(self):
        a,b,c=fake();b['source_original_zip_sha256']='0'*64
        with self.assertRaises(UnsafeResearchStage):self.check(a,b,c)
    def test_parent_cue_gap_rejected(self):
        a,b,c=fake();b['parents'][0]['cue_indices']=[1,2,3,5,6]
        with self.assertRaises(UnsafeResearchStage):self.check(a,b,c)
    def test_parent_mismatched_original_content_rejected(self):
        a,b,c=fake();b['parents'][0]['source_text_sha256']='a'*64
        with self.assertRaises(UnsafeResearchStage):self.check(a,b,c)
    def test_doubled_parent_rejected(self):
        a,b,c=fake();b['parents'].append(copy.deepcopy(b['parents'][0]))
        with self.assertRaises(UnsafeResearchStage):self.check(a,b,c)
    def test_unit_source_cue_hash_rejected(self):
        a,b,c=fake();b['atom_proposals'][0]['cue_sha256'][0]='c'*64
        with self.assertRaises(UnsafeResearchStage):self.check(a,b,c)
    def test_unit_source_span_sha_rejected(self):
        a,b,c=fake();b['atom_proposals'][0]['source_span_digest']='c'*64
        with self.assertRaises(UnsafeResearchStage):self.check(a,b,c)
    def test_unit_source_gap_rejected(self):
        a,b,c=fake();b['atom_proposals'].pop()
        with self.assertRaises(UnsafeResearchStage):self.check(a,b,c)
    def test_unit_fictitious_independent_gold_rejected(self):
        a,b,c=fake();b['atom_proposals'][0]['independent_gold']=True
        with self.assertRaises(UnsafeResearchStage):self.check(a,b,c)
    def test_unverified_audio_cannot_be_approved(self):
        a,b,c=fake();b['atom_proposals'][0]['speaker_audio_confirmed']=True
        with self.assertRaises(UnsafeResearchStage):self.check(a,b,c)
    def test_independent_accuracy_not_inferred(self):
        a,b,c=fake();b['precision']=0.99
        with self.assertRaises(UnsafeResearchStage):self.check(a,b,c)
    def test_false_finance_approval_rejected(self):
        a,b,c=fake();c[0]['approved']=True
        with self.assertRaises(UnsafeResearchStage):self.check(a,b,c)
    def test_forged_docket_cue_rebinding_rejected(self):
        a,b,c=fake();c[0]['source_cue_indices']=[1,2]
        with self.assertRaises(UnsafeResearchStage):self.check(a,b,c)
    def test_docket_missing_rejected(self):
        a,b,c=fake()
        with self.assertRaises(UnsafeResearchStage):self.check(a,b,[])
    def test_phishing_official_url_rejected(self):
        a,b,c=fake();c[0]['official_reference_urls']=['https://regulation.krx.co.kr.evil.invalid/']
        with self.assertRaises(UnsafeResearchStage):self.check(a,b,c)
    def test_reference_date_stale_rejected(self):
        a,b,c=fake();c[0]['checked_date']='2025-11-14'
        with self.assertRaises(UnsafeResearchStage):self.check(a,b,c)
    def test_not_automatic_gold_without_evidence(self):
        a,b,c=fake();b['semantics_complete_certified']=True
        with self.assertRaises(UnsafeResearchStage):self.check(a,b,c)

class ResumablePreparedDriver(unittest.TestCase):
    def test_empty_db_five_stage_sequential(self):
        with tempfile.TemporaryDirectory() as t:
            r=resume_prepared_five_stage_run(str(Path(t)/'v115.sqlite'),'V115_TEST',payloads())
            self.assertEqual(r['newly_recorded_stages'],5)
            self.assertFalse(r['model_inference_automated'])
            again=resume_prepared_five_stage_run(str(Path(t)/'v115.sqlite'),'V115_TEST',payloads())
            self.assertEqual(again['newly_recorded_stages'],0)
            self.assertEqual(r['head_sha256'],again['head_sha256'])
    def test_resume_from_interrupted_semantic(self):
        with tempfile.TemporaryDirectory() as t:
            file=str(Path(t)/'p.sqlite');j=V114ResearchJournal(file);p=payloads();h=ZERO
            for step in ('SOURCE','SEMANTIC'):
                h=j.submit(project_id='V115_TEST',run_id='V115_TEST_'+step,
                           expected_head=h,stage=step,payload=p[step])['new_head_sha256']
            out=resume_prepared_five_stage_run(file,'V115_TEST',p)
            self.assertEqual(out['newly_recorded_stages'],3)
            self.assertTrue(out['restarted_from_snapshot'])
    def test_tamper_previously_committed_stage_detected(self):
        with tempfile.TemporaryDirectory() as t:
            file=str(Path(t)/'p.sqlite');p=payloads();resume_prepared_five_stage_run(file,'V115_TEST',p)
            p2=copy.deepcopy(p);p2['SEMANTIC']['semantic_units']=3
            with self.assertRaises(UnsafeResearchStage):
                resume_prepared_five_stage_run(file,'V115_TEST',p2)
    def test_cannot_skipping_finance_stage(self):
        with tempfile.TemporaryDirectory() as t:
            p=payloads();p.pop('FINANCE')
            with self.assertRaises(UnsafeResearchStage):
                resume_prepared_five_stage_run(str(Path(t)/'p.sqlite'),'V115_TEST',p)
    def test_financial_claims_cannot_auto_approve(self):
        with tempfile.TemporaryDirectory() as t:
            p=payloads();p['FINANCE']['financial_fact_approved']=1
            with self.assertRaises(UnsafeResearchStage):
                resume_prepared_five_stage_run(str(Path(t)/'p.sqlite'),'V115_TEST',p)
    def test_v75_unfound_forces_open(self):
        with tempfile.TemporaryDirectory() as t:
            p=payloads();p['KNOWLEDGE']['v75_identity_recovered']=True
            with self.assertRaises(UnsafeResearchStage):
                resume_prepared_five_stage_run(str(Path(t)/'p.sqlite'),'V115_TEST',p)
    def test_private_prose_cannot_enter_public_checkpoint(self):
        with tempfile.TemporaryDirectory() as t:
            p=payloads();p['SEMANTIC']['private_claim_prose']='do not store'
            with self.assertRaises(UnsafeResearchStage):
                resume_prepared_five_stage_run(str(Path(t)/'p.sqlite'),'V115_TEST',p)

class PublicReceiptTest(unittest.TestCase):
    def test_real_pilot_receipt_frozen(self):
        x=json.loads(FIXTURE_PATH.read_text(encoding='utf-8'))
        self.assertTrue(assert_public_replay_receipt(x)['public_cue_review_pilot_receipt_consistent'])
    def test_fake_p0_go_receipt_rejected(self):
        x=json.loads(FIXTURE_PATH.read_text(encoding='utf-8'));x['p0_go']=True
        with self.assertRaises(UnsafeResearchStage):assert_public_replay_receipt(x)
    def test_fake_model_latency_rejected(self):
        x=json.loads(FIXTURE_PATH.read_text(encoding='utf-8'));x['model_semantic_wall_ns']=1
        with self.assertRaises(UnsafeResearchStage):assert_public_replay_receipt(x)

if __name__=='__main__':unittest.main()
