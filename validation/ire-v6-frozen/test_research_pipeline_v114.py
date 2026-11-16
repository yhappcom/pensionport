import copy
import hashlib
import os
import sqlite3
import tempfile
import unittest

from ire.v6.research_pipeline_v114 import (
    V114ResearchJournal, UnsafeResearchStage, ZERO,
    audit_source_unit_crosswalk, audit_official_fact_docket,
)

A='a'*64
B='b'*64
C='c'*64
D='d'*64


def stage_payloads():
    return [
        dict(source_cues=3,source_windows=1,source_sha256=A,
             owner_private_replay_digest_sha256=B,unaccounted_source_cues=0,
             structure_wall_ns=1000),
        dict(parents=1,semantic_units=2,classified_cues=2,unassigned_cues=1,
             open_units=1,meaning_review_approved=False,
             semantic_artifact_sha256=C,structure_wall_ns=1200),
        dict(financial_fact_candidates=1,official_reference_count=1,
             official_reference_metadata_sha256=C,official_primary_snapshot_verified=False,
             current_law_scope_checked=True,unresolved_evidence_units=1,
             financial_fact_approved=0,personal_tax_approved=False,
             finance_artifact_sha256=D,structure_wall_ns=2300),
        dict(source_parse_wall_ns=1000,semantic_structure_wall_ns=1200,
             finance_structure_wall_ns=2300,p1_preview_wall_ns=1500,
             model_semantic_wall_ns=None,official_search_wall_ns=None,
             open_resolution_wall_ns=None,independent_adjudication_wall_ns=None,
             observed_artifact_sha256=C),
        dict(candidate_relations=0,historical_overlap_positions=1,
             historical_reconciliation_complete=False,
             v75_identity_recovered=False,knowledge_merge_count=0,
             knowledge_preview_sha256=D,structure_wall_ns=1500),
    ]


def private_fixture():
    text='연금 예시 발화'
    sha=hashlib.sha256(text.encode()).hexdigest()
    source={'source_archive_sha256':A,'owner_private_cues':[
        dict(video_id='VIDEO01',window_id='W00001',cue_index=1,
             start_ms=100,end_ms=200,text_private=text,cue_sha256=sha),
        dict(video_id='VIDEO01',window_id='W00001',cue_index=2,
             start_ms=201,end_ms=300,text_private='중간 구간',
             cue_sha256=hashlib.sha256('중간 구간'.encode()).hexdigest()),
    ]}
    unit_sha=hashlib.sha256(sha.encode('utf-8')).hexdigest()
    unit=dict(unit_id='V110_P01_U01',role='FACT_CANDIDATE',
              source_cue_indices=[1],source_cues_digest_sha256=unit_sha,
              independent_gold=False,approved_financial_fact=False,
              personal_advice_approved=False)
    ledger=dict(source_archive_sha256=A,parents=[
        dict(video_id='VIDEO01',draft_parent_id='C00001',window_id='W00001',
             source_cue_indices=[1],units=[unit])],
        unassigned_cues=[dict(video_id='VIDEO01',cue_index=2,
                              cue_sha256=source['owner_private_cues'][1]['cue_sha256'],
                              claim_absence_certified=False)])
    overlay=dict(original_owner_source_sha256=A,rows=[
        dict(unit_id='V110_P01_U01',video_id='VIDEO01',window_id='W00001',
             draft_parent_id='C00001',unit_role='FACT_CANDIDATE',
             source_cue_indices=[1],source_cues_digest_sha256=unit_sha,
             shadow_status='OPEN_AUDIO',finance_semantic_certified=False,
             independent_gold=False,p0_go=False,personal_advice_approved=False)])
    return source,ledger,overlay


class RealSourceCrosswalkContract(unittest.TestCase):
    def test_all_source_cues_accounted_without_gold(self):
        s,l,o=private_fixture()
        r=audit_source_unit_crosswalk(s,l,o)
        self.assertEqual((r['source_cues'],r['classified_cues'],r['unassigned_cues'],r['semantic_units'],r['open_units']),
                         (2,1,1,1,1))
        self.assertFalse(r['p0_go'])
    def test_original_cue_bytes_tampered(self):
        s,l,o=private_fixture();s['owner_private_cues'][0]['text_private']='변조'
        with self.assertRaises(UnsafeResearchStage):audit_source_unit_crosswalk(s,l,o)
    def test_overlay_unit_identity_changed(self):
        s,l,o=private_fixture();o['rows'][0]['source_cues_digest_sha256']=C
        with self.assertRaises(UnsafeResearchStage):audit_source_unit_crosswalk(s,l,o)
    def test_missing_cue_not_silently_removed(self):
        s,l,o=private_fixture();l['unassigned_cues']=[]
        with self.assertRaises(UnsafeResearchStage):audit_source_unit_crosswalk(s,l,o)
    def test_gap_not_approved_claim_absence(self):
        s,l,o=private_fixture();l['unassigned_cues'][0]['claim_absence_certified']=True
        with self.assertRaises(UnsafeResearchStage):audit_source_unit_crosswalk(s,l,o)
    def test_false_finance_claim_approval(self):
        s,l,o=private_fixture();l['parents'][0]['units'][0]['approved_financial_fact']=True
        with self.assertRaises(UnsafeResearchStage):audit_source_unit_crosswalk(s,l,o)
    def test_duplicate_parent_cue(self):
        s,l,o=private_fixture();l['parents'].append(copy.deepcopy(l['parents'][0]));l['parents'][1]['draft_parent_id']='C00002'
        with self.assertRaises(UnsafeResearchStage):audit_source_unit_crosswalk(s,l,o)
    def test_missing_shadow_status(self):
        s,l,o=private_fixture();o['rows'][0]['shadow_status']='CLOSED_CERTIFIED'
        with self.assertRaises(UnsafeResearchStage):audit_source_unit_crosswalk(s,l,o)


class OfficialDocketGate(unittest.TestCase):
    def setUp(self):
        self.ledger=private_fixture()[1]
        self.docket=[dict(unit_id='V110_P01_U01',status='GENERAL_RULE_COUNTEREVIDENCE_OPEN',
                     source_evidence_urls=['https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888'],
                     evidence_checked_date='2026-11-14',official_body_sha256=None,
                     personal_applicability_verified=False,financial_fact_approved=False)]
    def test_public_official_pointer_still_not_approved(self):
        r=audit_official_fact_docket(self.ledger,self.docket,checked_date='2026-11-14')
        self.assertEqual((r['fact_candidates'],r['official_reference_count'],r['financial_fact_approved']),
                         (1,1,0))
    def test_official_url_spoofed(self):
        self.docket[0]['source_evidence_urls']=['https://nts.go.kr.evil.example/a']
        with self.assertRaises(UnsafeResearchStage):
            audit_official_fact_docket(self.ledger,self.docket,checked_date='2026-11-14')
    def test_phishing_userinfo_rejected(self):
        self.docket[0]['source_evidence_urls']=['https://login@www.nts.go.kr/nts/a']
        with self.assertRaises(UnsafeResearchStage):
            audit_official_fact_docket(self.ledger,self.docket,checked_date='2026-11-14')
    def test_date_stale(self):
        self.docket[0]['evidence_checked_date']='2026-11-13'
        with self.assertRaises(UnsafeResearchStage):
            audit_official_fact_docket(self.ledger,self.docket,checked_date='2026-11-14')
    def test_missing_fact_denied(self):
        with self.assertRaises(UnsafeResearchStage):
            audit_official_fact_docket(self.ledger,[],checked_date='2026-11-14')
    def test_fake_personal_applicability(self):
        self.docket[0]['personal_applicability_verified']=True
        with self.assertRaises(UnsafeResearchStage):
            audit_official_fact_docket(self.ledger,self.docket,checked_date='2026-11-14')


class CheckpointJournal(unittest.TestCase):
    def setUp(self):
        self.dir=tempfile.TemporaryDirectory()
        self.path=os.path.join(self.dir.name,'research.sqlite')
        self.j=V114ResearchJournal(self.path)
    def tearDown(self):self.dir.cleanup()
    def stage(self,i,*,project='video7',run=None,payload=None,head=None):
        p=payload if payload is not None else stage_payloads()[i]
        h=head if head is not None else self.j.snapshot(project)['head_sha256']
        return self.j.submit(project_id=project,run_id=run or f'run-{i}',
                             expected_head=h,stage=('SOURCE','SEMANTIC','FINANCE','METRICS','KNOWLEDGE')[i],payload=p)
    def test_all_five_stages_readonly(self):
        for i in range(5):self.stage(i)
        r=V114ResearchJournal(self.path).snapshot('video7')
        self.assertEqual((r['stage'],r['completed_stages'],r['ready_for_next']),('KNOWLEDGE',5,None))
        self.assertFalse(r['p0_go']);self.assertFalse(r['research_complete'])
    def test_restart_next_stage(self):
        self.stage(0)
        j=V114ResearchJournal(self.path)
        self.assertEqual(j.snapshot('video7')['ready_for_next'],'SEMANTIC')
        self.stage(1)
        self.assertEqual(j.snapshot('video7')['completed_stages'],2)
    def test_idempotent_run(self):
        old_head=ZERO
        r=self.stage(0,head=old_head)
        dup=self.stage(0,head=old_head)
        self.assertEqual(r['new_head_sha256'],dup['new_head_sha256'])
        self.assertTrue(dup['idempotent'])
        self.assertEqual(self.j.snapshot('video7')['completed_stages'],1)
    def test_conflicting_replay(self):
        self.stage(0,head=ZERO)
        wrong=stage_payloads()[0];wrong['source_cues']=4
        with self.assertRaises(UnsafeResearchStage):self.stage(0,head=ZERO,payload=wrong)
    def test_stale_head_detected(self):
        self.stage(0)
        with self.assertRaises(UnsafeResearchStage):self.stage(1,head=ZERO)
    def test_stage_order(self):
        with self.assertRaises(UnsafeResearchStage):self.stage(2)
    def test_semantic_cue_census(self):
        self.stage(0)
        p=stage_payloads()[1];p['unassigned_cues']=0
        with self.assertRaises(UnsafeResearchStage):self.stage(1,payload=p)
    def test_open_financial_case_not_auto_closed(self):
        self.stage(0);self.stage(1)
        p=stage_payloads()[2];p['unresolved_evidence_units']=0
        with self.assertRaises(UnsafeResearchStage):self.stage(2,payload=p)
    def test_law_approval_not_inferred(self):
        self.stage(0);self.stage(1)
        p=stage_payloads()[2];p['financial_fact_approved']=1
        with self.assertRaises(UnsafeResearchStage):self.stage(2,payload=p)
    def test_private_text_never_accepted(self):
        p=stage_payloads()[0];p['original_srt']='financial private transcript'
        with self.assertRaises(UnsafeResearchStage):self.stage(0,payload=p)
    def test_false_v75_dedup_not_promoted(self):
        for i in range(4):self.stage(i)
        p=stage_payloads()[4];p['historical_reconciliation_complete']=True
        with self.assertRaises(UnsafeResearchStage):self.stage(4,payload=p)
    def test_model_time_can_remain_unmeasured(self):
        for i in range(4):self.stage(i)
        self.assertFalse(self.j.snapshot('video7')['independent_gold'])
    def test_tampered_checkpoint_detected(self):
        self.stage(0)
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE events SET payload_json='{}' WHERE stage='SOURCE'")
        with self.assertRaises(UnsafeResearchStage):self.j.snapshot('video7')


if __name__=='__main__':unittest.main()
