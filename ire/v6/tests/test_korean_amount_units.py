"""V19 synthetic financial amount controls: full Korean magnitude tokens."""
import copy
import unittest
from ire.v6.atomic_exchange import NUMBER, audit_host_atomic_exchange
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import verify_source
from ire.v6.tests.test_source_and_proof import make_srt, make_manifest

class KoreanAmountUnitRegressionTests(unittest.TestCase):
    def test_complex_tokens_are_atomic(self):
        examples = {
            '2천만 원': ['2천만 원'],
            '2억 4천만 원': ['2억 4천만 원'],
            '18만9,000원씩': ['18만9,000원'],
            '2,268만 원': ['2,268만 원'],
            '1억6천만원': ['1억6천만원'],
            '3천5백만 원': ['3천5백만 원'],
            '300만 원': ['300만 원'],
            '300만원': ['300만원'],
            '1조 2억 3천만 원': ['1조 2억 3천만 원'],
            '30년 / 3.3% / 5개월': ['30년','3.3%','5개월'],
            '5.5%를 적용': ['5.5%'],
            '10 20원': ['10','20원'],
            '2026년 11월 10일': ['2026년','11월','10일'],
        }
        for src, tokens in examples.items():
            with self.subTest(src=src):
                self.assertEqual(NUMBER.findall(src),tokens)
    def _fixture(self, text, claimed):
        raw=make_srt([text, '다음 설명을 확인합니다.'])
        plan=make_manifest(raw,cut=2)
        src=verify_source(raw,plan,expected_source_sha256=sha256(raw),
                          expected_manifest_sha256=json_digest(plan))
        atom={'claim_id':'C00001','owner_window_id':src.owner(1),
              'proposition':claimed,'kind':'FACT','stance':'AFFIRMED',
              'speaker':'NARRATOR','source_refs':[{'cue_index':1,'quote':src.cues[0].text}],
              'context_cue_indices':[1],'condition_cue_indices':[],
              'exception_cue_indices':[],
              'numeric_references':[{'cue_index':1,'token':t} for t in NUMBER.findall(text)],
              'as_of':None}
        e={'schema':'IRE_V6_HOST_ATOMIC_EXCHANGE_V1','video_id':src.video_id,
           'source_sha256':src.source_sha256,'manifest_sha256':src.manifest_sha256,
           'atoms':[atom],'cue_dispositions':[
               {'cue_index':i,'cue_text_sha256':sha256(c.text.encode()),
                'disposition':'CANDIDATES' if i==1 else 'NO_ATOM',
                'claim_ids':['C00001'] if i==1 else [],
                'numeric_tokens':NUMBER.findall(c.text),
                'note':'' if i==1 else '금액 이외의 안내 문장'}
               for i,c in enumerate(src.cues,1)]}
        return src,e
    def test_equivalent_whitespace_remains_valid(self):
        for original,proposal in [
            ('300만 원','300만원'),('2억 4천만 원','2억4천만원'),
            ('18만9,000원','18만 9,000원')]:
            with self.subTest(original=original):
                s,e=self._fixture('금액은 '+original+'입니다.','금액은 '+proposal+'입니다.')
                self.assertEqual(audit_host_atomic_exchange(s,e)['proposed_atomic_claims'],1)
    def test_change_any_magnitude_or_digit_must_fail(self):
        for original,forgery in [
            ('2천만 원','2만 원'),('2억 4천만 원','2억 5천만 원'),
            ('18만9,000원','18만9,001원'),('2,268만 원','2,269만 원'),
            ('1억원','1만원'),('30년','30개월')]:
            with self.subTest(original=original,forgery=forgery):
                s,e=self._fixture('금액은 '+original+'입니다.','금액은 '+forgery+'입니다.')
                with self.assertRaisesRegex(InvalidInput,'HOST_ATOM_PROPOSITION_NUMBER_UNGROUNDED'):
                    audit_host_atomic_exchange(s,e)
    def test_source_numeric_census_cannot_be_old_split_tokens(self):
        src,e=self._fixture('18만9,000원 2천만 원을 더합니다.',
                            '18만9,000원 2천만 원을 더합니다.')
        self.assertEqual(e['cue_dispositions'][0]['numeric_tokens'],['18만9,000원','2천만 원'])
        e['cue_dispositions'][0]['numeric_tokens']=['18','9,000원','2']
        with self.assertRaisesRegex(InvalidInput,'HOST_ATOMIC_NUMERIC_CENSUS_MISMATCH'):
            audit_host_atomic_exchange(src,e)
    def test_no_false_independent_gold(self):
        src,e=self._fixture('금액 2억 4천만 원','금액 2억4천만원')
        r=audit_host_atomic_exchange(src,e)
        self.assertFalse(r['semantic_claims_independently_verified'])
        self.assertFalse(r['p0_go'])

if __name__=='__main__': unittest.main()
