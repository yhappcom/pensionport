"""Synthetic parent screening protocol checks; no financial E3 gold label."""
import copy,unittest
from types import SimpleNamespace
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import _digest
from v189_e3_parent_alignment_screen import (validate_answer,ANSWER_SCHEMA,PACKET_SCHEMA)

class TestParentScreen(unittest.TestCase):
    def setUp(self):
        self.cues=[SimpleNamespace(text='시장가격과 NAV는 서로 다른 계산 방식입니다.'),
                   SimpleNamespace(text='거래소에서 ETF가 실시간으로 거래됩니다.'),
                   SimpleNamespace(text='원금은 보장되지 않을 수 있습니다.')]
        self.pair={'first_anchor':1,'second_anchor':2,
                   'first_claim_ordinal':1,'second_claim_ordinal':1}
        self.packet={'schema':PACKET_SCHEMA,'source_sha256':'a'*64,
                     'first_head':'b'*64,'second_head':'c'*64,
                     'adjudication_head':'d'*64,'max_cue_shift':8,
                     'cases':[{'cue_index':1,'cue_text':self.cues[0].text,
                               'candidate_count':1,'candidate_pairs':[{'ref':self.pair}]},
                              {'cue_index':2,'cue_text':self.cues[1].text,
                               'candidate_count':2,'candidate_pairs':[{'ref':self.pair},{'ref':self.pair}]},
                              {'cue_index':3,'cue_text':self.cues[2].text,
                               'candidate_count':0,'candidate_pairs':[]}],
                     'source_quote_must_be_from_original':True,'independent_gold':False,
                     'e3_certified':False,'e4_approved':False,'e5_published':False,
                     'structural_triage_counts':{'UNIQUE':1,'AMBIGUOUS':1,'UNMATCHED':1}}
        self.packet['packet_sha256']=_digest(self.packet)
    def ans(self):
        tags=['OVERLAPPING_DISTINCT_FACTS','MULTIPLE_CANDIDATES_UNRESOLVED',
              'NO_CANDIDATE_UNRESOLVED']
        return {'schema':ANSWER_SCHEMA,'packet_sha256':self.packet['packet_sha256'],
                'review_executor':'CHATGPT_IN_CHAT',
                'reviews':[{'cue_index':i,'assessment':tags[i-1],
                            'source_quote':self.cues[i-1].text,'source_quote_cue_index':i,
                            'pair_ref':copy.deepcopy(self.pair) if i==1 else None,
                            'semantic_rationale':'해당 원본 자막과 양쪽 주장을 함께 대조했지만 완전한 동치 인증은 할 수 없습니다. 검토자는 주장 범위와 별도 가격의 의미를 구별하여 향후 원문 재판정 대상으로 보존합니다.',
                            'semantic_equivalence_certified':False,'independent_gold_certified':False,
                            'e3_certified':False,'e4_approved':False,'e5_published':False}
                           for i in range(1,4)]}
    def test_01_valid_source_ref_while_hold(self):
        p=validate_answer(self.packet,self.ans(),self.cues)
        self.assertEqual(p['review_count'],3)
        self.assertFalse(p['semantic_equivalence_certified'])
    def test_02_forged_source_quote(self):
        a=self.ans();a['reviews'][0]['source_quote']='원금 100% 보장'
        with self.assertRaisesRegex(InvalidInput,'SOURCE_QUOTE_UNVERIFIED'):
            validate_answer(self.packet,a,self.cues)
    def test_03_approval_forgery(self):
        a=self.ans();a['reviews'][0]['e3_certified']=True
        with self.assertRaisesRegex(InvalidInput,'RESPONSE_SCHEMA_OR_AUTHORITY'):
            validate_answer(self.packet,a,self.cues)
    def test_04_wrong_parent_ref(self):
        a=self.ans();a['reviews'][0]['pair_ref']['first_anchor']=3
        with self.assertRaisesRegex(InvalidInput,'UNIQUE_MATCH_REFERENCE_INVALID'):
            validate_answer(self.packet,a,self.cues)
    def test_05_ambiguous_cannot_autolink(self):
        a=self.ans();a['reviews'][1]['assessment']='PROVISIONAL_SAME_PARENT'
        a['reviews'][1]['pair_ref']=self.pair
        with self.assertRaisesRegex(InvalidInput,'MULTIPLE_MATCH_NOT_RESOLVED'):
            validate_answer(self.packet,a,self.cues)
    def test_06_unmatched_cannot_link(self):
        a=self.ans();a['reviews'][2]['assessment']='PROVISIONAL_SAME_PARENT'
        a['reviews'][2]['pair_ref']=self.pair
        with self.assertRaisesRegex(InvalidInput,'NO_MATCH_CANNOT_PROVE_EQUIVALENCE'):
            validate_answer(self.packet,a,self.cues)
    def test_07_wrong_cue_order(self):
        a=self.ans();a['reviews'][0],a['reviews'][1]=a['reviews'][1],a['reviews'][0]
        with self.assertRaisesRegex(InvalidInput,'RESPONSE_SCHEMA_OR_AUTHORITY'):
            validate_answer(self.packet,a,self.cues)
    def test_08_wrong_answer_pin(self):
        a=self.ans();a['packet_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'ANSWER_COUNT_OR_PIN'):
            validate_answer(self.packet,a,self.cues)
    def test_09_packet_data_modified(self):
        x=copy.deepcopy(self.packet);x['cases'][0]['cue_text']='다른 원본으로 바꾸기'
        with self.assertRaisesRegex(InvalidInput,'PACKET_SELF_HASH'):
            validate_answer(x,self.ans(),self.cues)
    def test_10_cannot_claim_golden_reviewer(self):
        a=self.ans();a['reviews'][0]['independent_gold_certified']=True
        with self.assertRaisesRegex(InvalidInput,'RESPONSE_SCHEMA_OR_AUTHORITY'):
            validate_answer(self.packet,a,self.cues)

if __name__=='__main__':unittest.main()