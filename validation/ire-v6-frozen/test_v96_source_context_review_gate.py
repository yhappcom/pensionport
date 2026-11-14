"""V96 synthetic adversarial tests. No owner source, no gold or real review prose."""
from __future__ import annotations
import unittest,copy
from dataclasses import dataclass
from v96_source_context_review_gate import (verify_batch,cue_evidence,digest,sha,
 STATUS,FALSE_FIELDS,SOURCE_VIDEO_IDS)
@dataclass
class Cue:
    index:int
    start_ms:int
    end_ms:int
    text:str
class TestsV96(unittest.TestCase):
    def setUp(self):
        self.archive_sha='a'*64
        self.cues={}
        self.registry={}
        self.queue={}
        self.prior={}
        self.rows=[]
        self.counter={'QUALIFIER_REVIEW':6}
        for v in sorted(SOURCE_VIDEO_IDS):
            cues=[Cue(i,i*100,i*100+60,f'가상 계좌 {i}번째 자막의 이야기입니다') for i in range(1,13)]
            self.cues[v]=cues
            parent_text=' | '.join(cues[i-1].text for i in [2,3,4])
            self.registry[v]={'W00001':[{'claim_id':'C00001','cue_indices':[2,3,4],
                        'source_text_sha256':sha(parent_text)}]}
            self.queue[v]=[{'cue_index':3,'kind':'QUALIFIER_REVIEW','cue_sha256':sha(cues[2].text)}]
            self.prior[v]=set()
            row={'video_id':v,'cue_index':3,'kind':'QUALIFIER_REVIEW','cue_sha256':sha(cues[2].text),
                 'source_archive_sha256':self.archive_sha,'window_id':'W00001',
                 'start_ms':cues[2].start_ms,'end_ms':cues[2].end_ms,
                 'source_text_private':cues[2].text,'context_cues_private':cue_evidence(cues,3),
                 'context_sha256':digest(cue_evidence(cues,3)),
                 'parent_claim_id':'C00001','parent_cue_indices':[2,3,4],
                 'parent_sha256':sha(parent_text), 'status':STATUS,
                 'semantic_kind':'HYPOTHESIS',
                 'speaker_meaning_private':'가상 계좌에 관한 조건부 가정을 분리하여 검토합니다.',
                 'scope_caution_private':'합성 자막의 금융내용은 어떤 실제 투자자에게도 적용하지 않습니다.',
                 'provisional_subclaims':[], **{field:False for field in FALSE_FIELDS}}
            self.rows.append(row)
        self.expected={(r['video_id'],r['cue_index'],r['kind']) for r in self.rows}
        self.rows[0]['provisional_subclaims']=[
            {'source_cue_indices':[2,3],'provisional_meaning_private':'합성 자막의 첫 가정 항목을 분리합니다.','fact_approved':False},
            {'source_cue_indices':[4],'provisional_meaning_private':'합성 자막의 둘째 가정 항목을 분리합니다.','fact_approved':False}]
    def check(self,**changes):
        data=dict(rows=self.rows,cues_by_video=self.cues,registry_by_video=self.registry,
                  full_queue_by_video=self.queue,prior_cues_by_video=self.prior,
                  expected_keys=self.expected,expected_source_sha=self.archive_sha,
                  expected_public_risk_counts=self.counter)
        data.update(changes)
        return verify_batch(**data)
    def rejected(self,rows=None,**kwargs):
        with self.assertRaises(ValueError):self.check(rows=rows if rows is not None else self.rows,**kwargs)
    def rowscopy(self):return copy.deepcopy(self.rows)
    def test_valid_six_video_fixture_does_not_certify(self):
        r=self.check();self.assertEqual(r['new_reviewed_risk_cues'],6)
        self.assertEqual(r['draft_parent_partition_proposals'],1)
        self.assertFalse(r['p0_go']);self.assertFalse(r['independent_gold']);self.assertEqual(r['unreviewed_risk_signals'],0)
    def test_missing_case(self):self.rejected(rows=self.rows[:-1])
    def test_duplicate_case(self):
        x=self.rowscopy();x[-1]=x[0];self.rejected(rows=x)
    def test_bad_expected_source(self):self.rejected(expected_source_sha='x')
    def test_source_archive_spoof(self):
        x=self.rowscopy();x[0]['source_archive_sha256']='b'*64;self.rejected(rows=x)
    def test_cue_text_spoof(self):
        x=self.rowscopy();x[0]['source_text_private']='fake';self.rejected(rows=x)
    def test_cue_hash_spoof(self):
        x=self.rowscopy();x[0]['cue_sha256']='0'*64;self.rejected(rows=x)
    def test_cue_time_spoof(self):
        x=self.rowscopy();x[0]['start_ms']+=1;self.rejected(rows=x)
    def test_context_cue_text_spoof(self):
        x=self.rowscopy();x[0]['context_cues_private'][0]['text_private']='fake';self.rejected(rows=x)
    def test_context_hash_spoof(self):
        x=self.rowscopy();x[0]['context_sha256']='0'*64;self.rejected(rows=x)
    def test_wrong_claim_parent(self):
        x=self.rowscopy();x[0]['parent_claim_id']='C99999';self.rejected(rows=x)
    def test_wrong_parent_indices(self):
        x=self.rowscopy();x[0]['parent_cue_indices']=[3,4];self.rejected(rows=x)
    def test_wrong_parent_source_hash(self):
        x=self.rowscopy();x[0]['parent_sha256']='0'*64;self.rejected(rows=x)
    def test_wrong_window(self):
        x=self.rowscopy();x[0]['window_id']='W00002';self.rejected(rows=x)
    def test_fake_financial_fact_approval(self):
        x=self.rowscopy();x[0]['fact_approved']=True;self.rejected(rows=x)
    def test_fake_gold(self):
        x=self.rowscopy();x[0]['independent_gold']=True;self.rejected(rows=x)
    def test_fake_p0_go(self):
        x=self.rowscopy();x[0]['p0_go']=True;self.rejected(rows=x)
    def test_fake_historical_lineage_merge(self):
        x=self.rowscopy();x[0]['v75_lineage_certified']=True;self.rejected(rows=x)
    def test_false_precision_recall(self):
        x=self.rowscopy();x[0]['precision_recall_certified']=True;self.rejected(rows=x)
    def test_fake_audio_verified(self):
        x=self.rowscopy();x[0]['audio_verified']=True;self.rejected(rows=x)
    def test_missing_speaker_meaning(self):
        x=self.rowscopy();x[0]['speaker_meaning_private']='err';self.rejected(rows=x)
    def test_missing_caution(self):
        x=self.rowscopy();x[0]['scope_caution_private']='err';self.rejected(rows=x)
    def test_invalid_semantic_kind(self):
        x=self.rowscopy();x[0]['semantic_kind']='GOLD_FACT';self.rejected(rows=x)
    def test_subclaim_missing_cue(self):
        x=self.rowscopy();x[0]['provisional_subclaims'][0]['source_cue_indices']=[2];self.rejected(rows=x)
    def test_subclaim_source_outside_parent(self):
        x=self.rowscopy();x[0]['provisional_subclaims'][0]['source_cue_indices']=[2,5];self.rejected(rows=x)
    def test_subclaim_fact_false_go(self):
        x=self.rowscopy();x[0]['provisional_subclaims'][0]['fact_approved']=True;self.rejected(rows=x)
    def test_duplicate_subclaim_cue(self):
        x=self.rowscopy();x[0]['provisional_subclaims'][0]['source_cue_indices']=[2,2,3];self.rejected(rows=x)
    def test_wrong_review_status(self):
        x=self.rowscopy();x[0]['status']='RESEARCH_APPROVED';self.rejected(rows=x)
    def test_prior_source_overlap(self):
        p=copy.deepcopy(self.prior);p[self.rows[0]['video_id']].add(3);self.rejected(prior_cues_by_video=p)
    def test_queued_hash_spoof(self):
        q=copy.deepcopy(self.queue);q[self.rows[0]['video_id']][0]['cue_sha256']='0'*64;self.rejected(full_queue_by_video=q)
    def test_wrong_queue_census(self):self.rejected(expected_public_risk_counts={'QUALIFIER_REVIEW':7})
    def test_missing_video(self):
        c=copy.deepcopy(self.cues);c.pop(next(iter(c)));self.rejected(cues_by_video=c)
if __name__=='__main__':unittest.main()