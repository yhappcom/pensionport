"""Public synthetic-only V116 adversarial tests; no private subtitles."""
from __future__ import annotations
import copy,json,tempfile,unittest
from pathlib import Path
from ire.v6.research_pipeline_v114 import V114ResearchJournal, ZERO
from v115_full_video_bridge import sha,resume_prepared_five_stage_run
from test_v115_full_video_bridge import fake,payloads
from v116_semantic_finance_integration import (
    UnsafeResearchStage,digest,verify_original_challenges,
    audit_current_regulatory_evidence,audit_readonly_prior_preview,
    guard_public_v116_receipt,_validate_official_url,
    measure_bounded_review_steps)

HERE=Path(__file__).parent
PUBLIC=HERE/'V116_ACTUAL_PRIVATE_152CUE_SEMANTIC_FINANCE_P1_SHA_ONLY.json'
if not PUBLIC.exists():PUBLIC=HERE/'public'/'V116_ACTUAL_PRIVATE_152CUE_SEMANTIC_FINANCE_P1_SHA_ONLY.json'


def synth():
    raw,base,docket=fake()
    h=base['source_cue_hashes']
    part=lambda num,typ,indices,origin:dict(
        part_id='V116_C001_P%02d'%num,kind=typ,cue_indices=indices,
        cue_sha256=[h[i-1]['sha256'] for i in indices],
        meaning_private='synthetic meaning segment is provisional',
        origin=origin,approval_state='HOST_PROPOSED_OPEN',
        current_law_scope_confirmed=False)
    ch={'schema':'V116_OWNER_SEMANTIC_SPLIT_AND_CONTEXT_CHALLENGES_V1',
       'video_id':base['source_video_id'],'original_srt_sha256':sha(raw),
       'source_v115_atom_digest_sha256':digest(base['atom_proposals']),
       'independent_gold':False,'all_claims_certified':False,'p0_go':False,
       'cases':[{'case_id':'V116_C001','review_kind':'COMPOUND_ATOM',
          'source_cue_indices':list(range(1,7)),
          'source_cue_sha256':[z['sha256'] for z in h],
          'baseline_unit_ids':['TEST_A001','TEST_A002'],
          'provisional_parts':[
            part(1,'SPEAKER_ASSERTION',[1,2,3],'SRT_SPEAKER_PROPOSAL'),
            part(2,'REVIEWER_APPLICABILITY_LIMIT',[4,5,6],
                 'CHAT_REVIEWER_QUALIFICATION')],
          'risk':'HIGH','review_status':'INTERNAL_ANALYSIS_OPEN',
          'source_context_reason':'Synthetic source phrase spans source cues and reviewer limitation.',
          'source_resolution':'OPEN_NOT_INDEPENDENT_GOLD',
          'human_blind_independent':False,'financial_truth_approved':False,
          'has_per_cue_original_replay':True}]}
    def pointer(ident,kind,url,state,indexdate):
        return {'source_id':ident,'kind':kind,'url':url,'observed_date':'2026-11-14',
                'index_date':indexdate,'evidence_state':state,'raw_source_body_sha256':None}
    reg={'schema':'V116_INDEXED_LAW_PLUS_ISSUER_POINTERS_NO_RAW_BODY_V1',
       'as_of':'2026-11-14','law_article_id':'소득세법 시행령 제26조의2',
       'legal_effective_date':'2026-10-01','tax_change_applies_from':'2025-07-01',
       'old_claim_universal_tr_elimination':False,
       'domestic_equity_tr_exception_exists':True,
       'live_law_site_status':'MAINTENANCE_HTML_ON_2026_11_14',
       'original_law_html_sha256':None,'official_body_bytes_verified':False,
       'independent_finance_gold':False,'financial_facts_approved':0,
       'personal_advice_approved':False,
       'asof_source_pointers':[
        pointer('LAW2026','CURRENT_STATUTE','https://www.law.go.kr/lsLawLinkInfo.do?lsJoLnkSeq=1001063330','GOVERNMENT_INDEXED_LAW_LIVE_BODY_UNAVAILABLE','2026-10-01'),
        pointer('PLUS2025','ISSUER_NOTICE','https://www.plusetf.co.kr/customer/notice/detail?n=29585','ISSUER_NOTICE_SEARCH_INDEX_ONLY','2025-06-24'),
        pointer('RISE2025','ISSUER_NOTICE','https://www.riseetf.co.kr/cust/notice/123?page=1','ISSUER_NOTICE_SEARCH_INDEX_ONLY','2025-06-23')],
       'per_challenge_outcomes':[{'case_id':'V116_C001',
         'related_v115_unit_ids':['TEST_A001','TEST_A002'],
         'evidence_source_ids':['LAW2026','PLUS2025'],
         'evidence_state':'GOVERNMENT_INDEXED_LAW_LIVE_BODY_UNAVAILABLE',
         'scope_open':True,'original_audio_or_visual_open':False,
         'verified_financial_claim':False,'reviewer_status':'OPEN_NOT_FOR_ADVICE',
         'as_of':'2026-11-14'}]}
    prior={'schema':'V116_P1_READONLY_TOPIC_RELATION_PREVIEW_V1',
       'source_video_id':base['source_video_id'],
       'master116_git_blob_sha1':'ab5af7eea02e65d5e36174546a2a94f4cc642d92',
       'p4_22_git_blob_sha1':'bfb446ffb1dd40caa1ed03088d088c9a1ba7490f',
       'historical_v75_identity_recovered':False,'full_history_dedup_completed':False,
       'master_or_p4_modified':False,'knowledge_merges':0,
       'candidate_relations':[{'challenge_case_id':'V116_C001',
          'source_unit_id':'TEST_A001','prior_namespace':'MASTER116',
          'prior_id':'GOMHEE-C17','relation':'TOPIC_RELATED_PENDING',
          'reason_private':'synthetic source to prior topic relation only',
          'independently_verified_equivalence':False,'ready_for_merge':False}]}
    return raw,base,docket,ch,reg,prior


class V116ChallengeSecurity(unittest.TestCase):
    def audit(self,bundle):
        raw,base,docket,ch,reg,prior=bundle
        return verify_original_challenges(srt_raw=raw,base_ledger=base,
          base_docket=docket,challenges=ch,expected_srt_sha256=sha(raw),
          owner_zip_sha256='f'*64)
    def mut(self,fn):
        b=copy.deepcopy(synth());fn(b)
        with self.assertRaises(UnsafeResearchStage):self.audit(b)
    def test_baseline(self):
        a=self.audit(synth());self.assertEqual((a['baseline_source_cues'],
          a['challenge_cases'],a['provisional_atomic_facets']),(6,1,2))
    def test_baseline_mutation(self):self.mut(lambda b:b[3].update(source_v115_atom_digest_sha256='0'*64))
    def test_source_sha_mutation(self):self.mut(lambda b:b[3]['cases'][0]['source_cue_sha256'].__setitem__(0,'a'*64))
    def test_blank_source_status(self):self.mut(lambda b:b[3]['cases'][0].update(source_resolution='APPROVED'))
    def test_independent_gold_forge(self):self.mut(lambda b:b[3].update(independent_gold=True))
    def test_full_claims_forge(self):self.mut(lambda b:b[3].update(all_claims_certified=True))
    def test_add_private_field(self):self.mut(lambda b:b[3]['cases'][0].update(private_user_account='oops'))
    def test_duplicate_case(self):self.mut(lambda b:b[3]['cases'].append(copy.deepcopy(b[3]['cases'][0])))
    def test_duplicate_part(self):self.mut(lambda b:b[3]['cases'][0]['provisional_parts'].append(copy.deepcopy(b[3]['cases'][0]['provisional_parts'][0])))
    def test_undocumented_cue(self):self.mut(lambda b:b[3]['cases'][0]['provisional_parts'][0].update(cue_indices=[1,3]))
    def test_malicious_new_cue(self):self.mut(lambda b:b[3]['cases'][0].update(source_cue_indices=[1,2,3,4,5,7]))
    def test_parent_unit_misbind(self):self.mut(lambda b:b[3]['cases'][0].update(baseline_unit_ids=['TEST_A001']))
    def test_reviewer_masquerades_speaker(self):self.mut(lambda b:b[3]['cases'][0]['provisional_parts'][1].update(origin='SRT_SPEAKER_PROPOSAL'))
    def test_fake_law_scope_confirmed(self):self.mut(lambda b:b[3]['cases'][0]['provisional_parts'][1].update(current_law_scope_confirmed=True))
    def test_law_requires_counterevidence(self):
        b=synth();b[3]['cases'][0]['review_kind']='CURRENT_LAW_EXCEPTION'
        with self.assertRaises(UnsafeResearchStage):self.audit(b)
    def test_law_split_valid_when_corrected(self):
        b=synth();b[3]['cases'][0]['review_kind']='CURRENT_LAW_EXCEPTION'
        b[3]['cases'][0]['provisional_parts'][1]['kind']='REVIEWER_EXCEPTION'
        self.assertEqual(self.audit(b)['challenge_cases'],1)
    def test_missing_reviewer_correction(self):self.mut(lambda b:b[3]['cases'][0]['provisional_parts'][1].update(kind='SPEAKER_QUALIFIER',origin='SRT_SPEAKER_PROPOSAL'))
    def test_screen_case_not_closed(self):self.mut(lambda b:b[3]['cases'][0].update(review_kind='SCREEN_SOURCE_REQUIRED'))


class V116FinanceSecurity(unittest.TestCase):
    def audit(self,b):
        return audit_current_regulatory_evidence(challenge_doc=b[3],
          official_record=b[4],baseline_finance_docket=[copy.deepcopy(b[2][0]) for _ in range(26)])
    def mut(self,fn):
        b=copy.deepcopy(synth());fn(b)
        with self.assertRaises(UnsafeResearchStage):self.audit(b)
    def test_baseline(self):
        a=self.audit(synth());self.assertEqual(a['reviewed_source_pointer_count'],3)
        self.assertFalse(a['law_original_html_pinned'])
    def test_live_html_sha_forge(self):self.mut(lambda b:b[4].update(original_law_html_sha256='b'*64))
    def test_law_html_verified_forge(self):self.mut(lambda b:b[4].update(official_body_bytes_verified=True))
    def test_false_tax_exception_removed(self):self.mut(lambda b:b[4].update(domestic_equity_tr_exception_exists=False))
    def test_law_effective_date_changed(self):self.mut(lambda b:b[4].update(legal_effective_date='2025-07-01'))
    def test_claim_finance_approved(self):self.mut(lambda b:b[4].update(financial_facts_approved=1))
    def test_finance_independent_gold_forged(self):self.mut(lambda b:b[4].update(independent_finance_gold=True))
    def test_user_private_advice_forged(self):self.mut(lambda b:b[4].update(personal_advice_approved=True))
    def test_missing_case_evidence(self):self.mut(lambda b:b[4].update(per_challenge_outcomes=[]))
    def test_rebind_case(self):self.mut(lambda b:b[4]['per_challenge_outcomes'][0].update(related_v115_unit_ids=['TEST_A002']))
    def test_case_approved(self):self.mut(lambda b:b[4]['per_challenge_outcomes'][0].update(verified_financial_claim=True))
    def test_issuer_url_spoofed(self):self.mut(lambda b:b[4]['asof_source_pointers'][1].update(url='https://plusetf.co.kr.phishing.example/'))
    def test_invalid_port(self):self.mut(lambda b:b[4]['asof_source_pointers'][0].update(url='https://www.law.go.kr:invalid/'))
    def test_must_keep_original_site_unavailable(self):self.mut(lambda b:b[4].update(live_law_site_status='LIVE_BODY_VERIFIED'))
    def test_law_challenge_requires_two_types(self):
        b=synth();b[3]['cases'][0]['review_kind']='CURRENT_LAW_EXCEPTION'
        b[4]['per_challenge_outcomes'][0]['evidence_source_ids']=['LAW2026']
        with self.assertRaises(UnsafeResearchStage):self.audit(b)
    def test_visual_case_remains_open(self):
        b=synth();b[3]['cases'][0]['review_kind']='SCREEN_SOURCE_REQUIRED'
        with self.assertRaises(UnsafeResearchStage):self.audit(b)


class V116PriorSecurity(unittest.TestCase):
    def audit(self,b):return audit_readonly_prior_preview(challenge_doc=b[3],prior_review=b[5])
    def mut(self,fn):
        b=copy.deepcopy(synth());fn(b)
        with self.assertRaises(UnsafeResearchStage):self.audit(b)
    def test_baseline(self):self.assertEqual(self.audit(synth())['candidate_relations'],1)
    def test_unknown_master_id_rejected(self):self.mut(lambda b:b[5]['candidate_relations'][0].update(prior_id='GOMHEE-C88'))
    def test_false_v75_recovered(self):self.mut(lambda b:b[5].update(historical_v75_identity_recovered=True))
    def test_false_full_dedup(self):self.mut(lambda b:b[5].update(full_history_dedup_completed=True))
    def test_fake_merges(self):self.mut(lambda b:b[5].update(knowledge_merges=1))
    def test_forged_master_blob(self):self.mut(lambda b:b[5].update(master116_git_blob_sha1='a'*40))
    def test_fake_equivalence(self):self.mut(lambda b:b[5]['candidate_relations'][0].update(independently_verified_equivalence=True))
    def test_nonexistent_source(self):self.mut(lambda b:b[5]['candidate_relations'][0].update(source_unit_id='TEST_A999'))
    def test_duplicate_relation(self):self.mut(lambda b:b[5]['candidate_relations'].append(copy.deepcopy(b[5]['candidate_relations'][0])))


class V116PublicReceiptSecurity(unittest.TestCase):
    def read(self):return json.loads(PUBLIC.read_text(encoding='utf-8'))
    def test_frozen_public_receipt(self):self.assertTrue(guard_public_v116_receipt(self.read())['real_source_challenge_receipt_consistent'])
    def test_false_recall(self):
        x=self.read();x['recall']=0.93
        with self.assertRaises(UnsafeResearchStage):guard_public_v116_receipt(x)
    def test_fake_model_time(self):
        x=self.read();x['measured_local_stage_wall_ns']['chat_model_semantic_inference_ns']=123
        with self.assertRaises(UnsafeResearchStage):guard_public_v116_receipt(x)
    def test_wrong_challenge_count(self):
        x=self.read();x['challenge_cases']=17
        with self.assertRaises(UnsafeResearchStage):guard_public_v116_receipt(x)
    def test_false_law_html_pin(self):
        x=self.read();x['official_original_html_pinned']=True
        with self.assertRaises(UnsafeResearchStage):guard_public_v116_receipt(x)


class V116PreparedCheckpointSecurity(unittest.TestCase):
    def test_prepared_five_stages_run_once_and_replay(self):
        p=payloads()
        with tempfile.TemporaryDirectory() as d:
            fn=str(Path(d)/'z.sqlite')
            a=resume_prepared_five_stage_run(fn,'V116_SYNTH',p)
            b=resume_prepared_five_stage_run(fn,'V116_SYNTH',p)
            self.assertEqual(a['newly_recorded_stages'],5)
            self.assertEqual(b['newly_recorded_stages'],0)
            self.assertEqual(a['head_sha256'],b['head_sha256'])
    def test_interrupted_after_two_stages_resumes(self):
        p=payloads()
        with tempfile.TemporaryDirectory() as d:
            fn=str(Path(d)/'z.sqlite');j=V114ResearchJournal(fn);h=ZERO
            for step in ('SOURCE','SEMANTIC'):
                h=j.submit(project_id='V116_SYNTH',run_id='V116_SYNTH_'+step,
                      expected_head=h,stage=step,payload=p[step])['new_head_sha256']
            r=resume_prepared_five_stage_run(fn,'V116_SYNTH',p)
            self.assertEqual(r['newly_recorded_stages'],3)

if __name__=='__main__':unittest.main()
