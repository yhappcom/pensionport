"""Synthetic audit of complete financial numerical spans and source cue linkage.

This contains no private ETF subtitle, owner claim or financial approval.
"""
from __future__ import annotations
import unittest
from ire.v6.numeric_provenance import audit_numeric_reference_boundaries

class Cue:
    def __init__(self,text):self.text=text

def atom(token,source=1,cid='C00001'):
    return {'claim_id':cid,'numeric_references':[{'cue_index':source,'token':token}]}

class NumericUnitProvenanceTests(unittest.TestCase):
    def audit(self,text,token):return audit_numeric_reference_boundaries([Cue(text)],[atom(token)])
    def reject(self,text,token,reason):
        ret=self.audit(text,token)
        self.assertIn(reason,{x['reason'] for x in ret},ret)

    def test_01_full_exact_won_and_comma(self):self.assertEqual([],self.audit('NAV 17,728원입니다.','17,728원'))
    def test_02_partial_won(self):self.reject('17,728원입니다','17,728','NUMERIC_TOKEN_MISSING_ATTACHED_UNIT')
    def test_03_partial_krw_magnitude(self):self.reject('415억입니다','415','NUMERIC_TOKEN_MISSING_ATTACHED_UNIT')
    def test_04_fragment_numeric_hundred(self):self.reject('1천000개가 넘음','000','NUMERIC_TOKEN_MISSING_PREFIX')
    def test_05_fragment_numeric_unit(self):self.reject('1천000개가 넘음','1','NUMERIC_TOKEN_MISSING_ATTACHED_UNIT')
    def test_06_full_korean_mixed_count(self):self.assertEqual([],self.audit('1천000개가 넘음','1천000개'))
    def test_07_truncated_share_count(self):self.reject('123,477주고요','123,477','NUMERIC_TOKEN_MISSING_ATTACHED_UNIT')
    def test_08_full_share_count(self):self.assertEqual([],self.audit('123,477주고요','123,477주'))
    def test_09_truncated_roman_mass_label(self):self.reject('몸무이 40km인','40','NUMERIC_TOKEN_MISSING_ATTACHED_UNIT')
    def test_10_verbatim_unphysical_unit_is_preserved(self):self.assertEqual([],self.audit('몸무이 40km인','40km'))
    def test_11_fraction_no_unit_left_undecided(self):self.assertEqual([],self.audit('0.001과 0.002를','0.001'))
    def test_12_second_fraction_no_unit_left_undecided(self):self.assertEqual([],self.audit('0.001과 0.002를','0.002'))
    def test_13_ordinal_asr_must_be_semantically_reviewed(self):self.assertEqual([],self.audit('5차입니다.','5'))
    def test_14_korean_particle_does_not_prove_duplicate(self):self.assertEqual([],self.audit('2을 비교하는','2'))
    def test_15_complete_percent(self):self.assertEqual([],self.audit('연 0.45%입니다.','0.45%'))
    def test_16_percent_must_not_be_dropped(self):self.reject('연 0.45%입니다.','0.45','NUMERIC_TOKEN_MISSING_ATTACHED_UNIT')
    def test_17_time_period_kept(self):self.assertEqual([],self.audit('1년 동안 20%','1년'))
    def test_18_missing_token(self):self.reject('18% 수익률','20%','NOT_VERBATIM_IN_ORIGINAL')
    def test_19_missing_cue(self):
        flags=audit_numeric_reference_boundaries([Cue('20%')],[atom('20%',source=2)])
        self.assertEqual(flags[0]['reason'],'INVALID_CUE_OR_EMPTY_TOKEN')
    def test_20_empty_token(self):self.reject('20%','', 'INVALID_CUE_OR_EMPTY_TOKEN')
    def test_21_bad_numeric_reference_type(self):
        flags=audit_numeric_reference_boundaries([Cue('100')],[{'claim_id':'C','numeric_references':[{'cue_index':1,'token':['100']}]}])
        self.assertEqual(flags[0]['reason'],'INVALID_NUMERIC_REFERENCE')
    def test_22_bad_numeric_ref_list(self):
        flags=audit_numeric_reference_boundaries([Cue('100')],[{'claim_id':'C','numeric_references':{}}])
        self.assertEqual(flags[0]['reason'],'NUMERIC_REFS_NOT_ARRAY')
    def test_23_bool_cue_index_invalid(self):
        flags=audit_numeric_reference_boundaries([Cue('100')],[{'claim_id':'C','numeric_references':[{'cue_index':True,'token':'100'}]}])
        self.assertEqual(flags[0]['reason'],'INVALID_NUMERIC_REFERENCE')
    def test_24_different_atoms_do_not_launder_each_other(self):
        atoms=[atom('415',cid='C1'),atom('415억',cid='C2')]
        flags=audit_numeric_reference_boundaries([Cue('415억')],atoms)
        self.assertEqual(len(flags),1);self.assertEqual(flags[0]['claim_id'],'C1')
    def test_25_repeated_token_with_complete_occurrence(self):
        self.assertEqual([],self.audit('40km는 사례이고 40이라고도 말한다','40'))
    def test_26_reference_partial_decimal_rejected(self):self.reject('0.001% 와','0.001','NUMERIC_TOKEN_MISSING_ATTACHED_UNIT')
    def test_27_raw_claim_does_not_auto_generate_numeric_truth(self):
        self.assertEqual([],audit_numeric_reference_boundaries([Cue('ETF는 유익하다')],[{'claim_id':'C','numeric_references':[]}]))
    def test_full_unit_followed_by_particle(self):
        for text,token in [('300만 원만 납입','300만 원'),('45만원만 출금','45만원'),
                           ('수익률 8%만 적용','8%'),('2년만 유지','2년'),
                           ('20주만 매수','20주'),('5억 원만 사용','5억 원')]:
            with self.subTest(text=text):
                self.assertEqual([],self.audit(text,token))

    def test_spaced_or_extended_unit_is_not_optional(self):
        for text,token in [('300만 원만 납입','300만'),('45만 원만 출금','45'),
                           ('8 퍼센트포인트만 변경','8'),('12 개월만 유지','12')]:
            with self.subTest(text=text):
                self.reject(text,token,'NUMERIC_TOKEN_MISSING_ATTACHED_UNIT')

    def test_28_no_original_srt_leakage_in_module(self):
        import inspect,ire.v6.numeric_provenance as m
        src=inspect.getsource(m)
        self.assertNotIn('LVE7XN_esTc',src)
        self.assertNotIn('P205_PRIVATE',src)

if __name__=='__main__':unittest.main()
