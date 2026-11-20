"""Synthetic preregistration security tests; NOT independent investment gold."""
from __future__ import annotations
import tempfile,unittest,os,copy,json
from pathlib import Path
from types import SimpleNamespace
from ire.v6.errors import InvalidInput
from v192_e3_frozen_reference import (
    prepare_reference,seal_reference,verify_reference,score_without_gold)

class TestV192FrozenReference(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        self.path=Path(t.name)/'private_reference.json'
        self.cues=[SimpleNamespace(text='상품마다 금리 지급 방식이 다를 수 있습니다.'),
                   SimpleNamespace(text='연 2%라는 수치는 여기서 설명을 위한 예시입니다.'),
                   SimpleNamespace(text='금리 조건은 투자 전에 꼭 확인해야 합니다.')]
        self.raw=('\n\n'.join(
            f'{i}\n00:00:{i:02d},000 --> 00:00:{i:02d},900\n{c.text}'
            for i,c in enumerate(self.cues,1))).encode('utf-8')
        self.record={'claim_id':'REF001','kind':'FACT',
          'proposition':'상품마다 금리 지급 방식이 다를 수 있다고 발언한다.',
          'quote_cue':1,'quote':'금리 지급 방식이 다를 수 있습니다.',
          'evidence_cues':[1], 'source_spoken_conditions':[],
          'source_spoken_exceptions':[], 'independent_truth_confirmed':False,
          'high_risk':True,'requires_external_evidence':True}
    def generate(self,record=None):
        return prepare_reference(source_bytes=self.raw,source_cues=self.cues,
          video_id='AbCdEf12345',entries=[record or self.record],
          evaluation_scope={'start_cue':1,'end_cue':3})
    def test_01_source_only_internal_reference_not_gold(self):
        r=self.generate();self.assertFalse(r['independent_gold_certified'])
        self.assertFalse(r['e3_certified'])
        self.assertIsNone(score_without_gold(r)['certified_precision'])
    def test_02_refuse_gold_scoring_of_predictions(self):
        r=self.generate()
        with self.assertRaisesRegex(InvalidInput,'UNADJUDICATED_PREDICTIONS'):
            score_without_gold(r,predictions=[self.record])
    def test_03_freeze_and_verify_digest(self):
        r=self.generate();meta=seal_reference(self.path,r)
        saved=verify_reference(self.path,expected_reference_sha256=meta['reference_sha256'],
               expected_source_sha256=meta['source_sha256'])
        self.assertEqual(saved,r)
        self.assertIsNone(meta['recall'])
    def test_04_never_overwrite_frozen_reference(self):
        r=self.generate();seal_reference(self.path,r)
        with self.assertRaisesRegex(InvalidInput,'NO_OVERWRITE_OR_RESET'):
            seal_reference(self.path,r)
    def test_05_reject_added_fake_speaker_qualifier(self):
        bad=copy.deepcopy(self.record)
        bad['source_spoken_conditions']=[{'cue_index':1,'quote':'원금보장 100%'}]
        with self.assertRaisesRegex(InvalidInput,'SPOKEN_QUALIFIER_UNGROUNDED'):
            self.generate(bad)
    def test_06_reject_quote_from_wrong_source(self):
        bad=copy.deepcopy(self.record);bad['quote']='모든 사람의 원금을 보장합니다.'
        with self.assertRaisesRegex(InvalidInput,'CLAIM_REF_OR_SOURCE_CUE_INVALID'):
            self.generate(bad)
    def test_07_reject_truth_forgery(self):
        bad=copy.deepcopy(self.record);bad['independent_truth_confirmed']=True
        with self.assertRaisesRegex(InvalidInput,'CLAIM_REF_OR_SOURCE_CUE_INVALID'):
            self.generate(bad)
    def test_08_reject_reference_digest_tamper(self):
        r=self.generate();meta=seal_reference(self.path,r)
        self.path.write_text('{}');os.chmod(self.path,0o600)
        with self.assertRaisesRegex(InvalidInput,'REFERENCE_DIGEST_CHANGED'):
            verify_reference(self.path,expected_reference_sha256=meta['reference_sha256'],
                             expected_source_sha256=meta['source_sha256'])
    def test_09_private_permission_required(self):
        r=self.generate();meta=seal_reference(self.path,r);os.chmod(self.path,0o644)
        with self.assertRaisesRegex(InvalidInput,'PRIVATE_REFERENCE_PERMISSION'):
            verify_reference(self.path,expected_reference_sha256=meta['reference_sha256'],
                             expected_source_sha256=meta['source_sha256'])
    def test_10_source_shift_detected(self):
        r=self.generate();meta=seal_reference(self.path,r)
        with self.assertRaisesRegex(InvalidInput,'REFERENCE_DATA_OR_AUTHORITY_CHANGED'):
            verify_reference(self.path,expected_reference_sha256=meta['reference_sha256'],
                             expected_source_sha256='0'*64)
    def test_11_cue_span_must_not_be_external(self):
        bad=copy.deepcopy(self.record);bad['evidence_cues']=[1,4]
        with self.assertRaisesRegex(InvalidInput,'CLAIM_REF_OR_SOURCE_CUE_INVALID'):
            self.generate(bad)
    def test_12_fake_source_cues_under_valid_raw_sha_rejected(self):
        falsified=copy.deepcopy(self.cues)
        falsified[2].text='영상에 전혀 없는 자료입니다.'
        with self.assertRaisesRegex(InvalidInput,'ORIGINAL_SRT_CUE_MISMATCH'):
            prepare_reference(source_bytes=self.raw,source_cues=falsified,
              video_id='AbCdEf12345',entries=[self.record],
              evaluation_scope={'start_cue':1,'end_cue':3})
    def test_13_reference_seal_cannot_invent_external_reviewer(self):
        r=self.generate();r['external_reviewer_independence_verified']=True
        with self.assertRaisesRegex(InvalidInput,'MUST_BE_UNAPPROVED_SOURCE_REFERENCE'):
            seal_reference(self.path,r)
    def test_14_fake_reference_authority_rejected(self):
        r=self.generate();r['independent_gold_certified']=True
        with self.assertRaisesRegex(InvalidInput,'MUST_BE_UNAPPROVED_SOURCE_REFERENCE'):
            seal_reference(self.path,r)

if __name__=='__main__':unittest.main()