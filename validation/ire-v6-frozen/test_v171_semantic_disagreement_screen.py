"""Synthetic source triage; flags are not truth labels."""
import copy
import unittest
from v166_e4_full_video_readiness import digest,h
from test_v166_e4_full_video_readiness import fixture
from v171_semantic_disagreement_screen import screen_full_video

class V171SourceFirstTriageTests(unittest.TestCase):
    def setUp(self):
        self.raw,self.cues,self.segments=fixture()
        self.a=self.segments[0]['exchange']['atoms'][0]
        self.v=self.segments[0]['review']['atom_verdicts'][0]
        self.a.update(kind='FACT',proposition='화자의 개인적 의견과 숫자 주장이 섞인 문장')
        self.v['atom_sha256']=digest(self.a)
        self.b=self.segments[1]['exchange']['atoms'][0]
        self.b.update(kind='OPINION',proposition='의견')
        self.segments[1]['review']['atom_verdicts'][0]['atom_sha256']=digest(self.b)
    def run_audit(self):
        return screen_full_video(self.raw,self.cues,self.segments,
                                 expected_source_sha256=h(self.raw))
    def test_01_flags_fact_with_explicit_opinion_not_approve(self):
        r=self.run_audit()
        self.assertEqual(r['fact_atom_count'],1)
        self.assertEqual(r['flagged_for_meaning_review'],1)
        self.assertEqual(r['high_priority'],1)
        self.assertEqual(r['items'][0]['claim_id'],'C00001')
        self.assertFalse(r['native_v123_status_changed'])
        self.assertIsNone(r['true_error_count'])
    def test_02_nonfact_opinion_not_misclassified(self):
        self.a['kind']='OPINION';self.v['atom_sha256']=digest(self.a)
        self.assertEqual(self.run_audit()['flagged_for_meaning_review'],0)
    def test_03_forged_original_owner_bytes_not_trusted(self):
        with self.assertRaisesRegex(ValueError,'OWNER_SOURCE_PIN_MISMATCH'):
            screen_full_video(self.raw,self.cues,self.segments,
                              expected_source_sha256='0'*64)
    def test_04_new_atom_hash_drift_blocked(self):
        self.a['proposition']='다른 표현'
        with self.assertRaisesRegex(ValueError,'ATOM_DIGEST_DRIFT'):self.run_audit()
    def test_05_cue_text_drift_blocked(self):
        self.cues[1]='조작된 원문'
        with self.assertRaisesRegex(ValueError,'CUE_MAP_NOT_RAW_SOURCE_TEXT'):self.run_audit()
    def test_06_same_atom_twice_invalid(self):
        other=copy.deepcopy(self.a)
        self.segments[1]['exchange']['atoms'].append(other)
        self.segments[1]['review']['atom_verdicts'].append(copy.deepcopy(self.v))
        with self.assertRaisesRegex(ValueError,'CLAIM_CENSUS_OR_DUPLICATE'):self.run_audit()
    def test_07_insufficient_source_tail_blocked(self):
        self.segments.pop()
        with self.assertRaisesRegex(ValueError,'TRAILING_SOURCE_GAP'):self.run_audit()

if __name__=='__main__':unittest.main()