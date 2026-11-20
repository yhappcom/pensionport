"""Synthetic E3 source-aware causal classification tests; not owner gold."""
import tempfile,unittest
from dataclasses import dataclass
from pathlib import Path
from ire.v6.errors import InvalidInput
from v185_e3_parent_qualifier_audit import analyze_source_journals
from v176_chat_engine_loop import ZERO

@dataclass
class Cue:
    text:str


def claim(kind,ctx,numeric=None,conditions=None,exceptions=None):
    return {'kind':kind,'context_cue_indices':ctx,'numeric_tokens':numeric or [],
            'conditions':conditions or [],'exceptions':exceptions or []}


def rows(n,claims=None):
    c=claims or {}
    return {i:(ZERO,{'claims':c.get(i,[]),'disposition':'ASSERTION' if i in c else 'NON_RESEARCH'})
            for i in range(1,n+1)}

class TestParentQualifierDiagnostics(unittest.TestCase):
    def setUp(self):
        self.cues=[Cue(x) for x in ['패시브 ETF는 지수를','따릅니다. 예외는 장중','이것은 거래량이 많고','매수가 쉬울 수 있습니다.','별도 발언입니다.']]
        self.first=rows(5,{1:[claim('FACT',[1,2],conditions=['예외는 장중'],exceptions=['원금보장 아님'])],
                           3:[claim('FACT',[3,4],numeric=['10%'])]})
        self.second=rows(5,{2:[claim('FACT',[1,2])],4:[claim('FACT',[3,4],numeric=['20%'])]})
    def run_audit(self,first=None,second=None):
        return analyze_source_journals(first or self.first,second or self.second,self.cues,
                                      pinned_first_head=ZERO,pinned_second_head=ZERO)
    def test_01_shift_not_automatically_semantic_agreement(self):
        x=self.run_audit()
        self.assertEqual(x['possible_cross_cue_parent_alignment_cues'],2)
        self.assertEqual(x['possible_cross_cue_parent_alignments'],2)
        self.assertFalse(x['e3_quality_certified'])
        self.assertTrue(all(not v['semantic_equivalence_proven'] for v in x['possible_parent_links']))
        self.assertEqual(x['cue_level_claim_presence_differences'],4)
    def test_02_numeric_mismatch_prevents_candidate_alignment(self):
        x=self.run_audit()
        self.assertTrue(all(item['first_anchor']==1 for item in x['possible_parent_links']))
        self.assertNotIn(3,{v['first_anchor'] for v in x['possible_parent_links']})
    def test_03_literal_qualifier_is_not_proven_source_spoken(self):
        x=self.run_audit()
        terms=x['first_qualifier_provenance']
        self.assertEqual(terms['total_terms'],2)
        self.assertEqual(terms['exact_original_substring_terms'],1)
        self.assertEqual(terms['not_literal_or_unanchored_terms'],1)
        self.assertEqual(terms['terms_proven_source_spoken'],0)
        self.assertFalse(x['source_spoken_and_reviewer_added_qualifiers_separated_in_native_v6'])
    def test_04_source_span_wrong_cannot_claim_alignment(self):
        self.second=rows(5,{5:[claim('FACT',[5])]})
        x=self.run_audit()
        self.assertEqual(x['possible_cross_cue_parent_alignments'],0)
    def test_05_kind_mismatch_not_equivalent(self):
        self.second=rows(5,{2:[claim('RECOMMENDATION',[1,2])]})
        self.assertEqual(self.run_audit()['possible_cross_cue_parent_alignments'],0)
    def test_06_opinion_recommendation_possible_only_not_certified(self):
        self.first=rows(5,{1:[claim('OPINION',[1,2])]})
        self.second=rows(5,{2:[claim('RECOMMENDATION',[1,2])]})
        x=self.run_audit()
        self.assertEqual(x['possible_cross_cue_parent_alignments'],2)
        self.assertFalse(x['possible_parent_links'][0]['same_kind'])
        self.assertFalse(x['e3_quality_certified'])
    def test_07_first_census_missing_rejected(self):
        first=dict(self.first);first.pop(5)
        with self.assertRaisesRegex(InvalidInput,'SOURCE_CENSUS_INCOMPLETE'):
            self.run_audit(first=first)
    def test_08_adjudication_requires_head_and_second_review(self):
        with self.assertRaisesRegex(InvalidInput,'ADJUDICATION_HEAD_NOT_PINNED'):
            analyze_source_journals(self.first,self.second,self.cues,
                pinned_first_head=ZERO,pinned_second_head=ZERO,adjudications={})
    def test_09_no_claim_still_no_approval(self):
        x=self.run_audit(first=rows(5),second=rows(5))
        for key in ['accuracy_precision_certified','accuracy_recall_certified',
                    'e3_quality_certified','e4_approved','e5_published']:
            self.assertFalse(x[key])
    def test_10_unverified_qualifiers_not_emitted_verbatim(self):
        x=self.run_audit()
        self.assertNotIn('원금보장 아님',str(x))
        self.assertFalse(x['all_reviewed_source_qualifiers_verified'])
    def test_11_limit_parameter_fails_closed(self):
        with self.assertRaisesRegex(InvalidInput,'MAX_CUE_SHIFT_RANGE'):
            analyze_source_journals(self.first,self.second,self.cues,
                                    pinned_first_head=ZERO,pinned_second_head=ZERO,max_cue_shift=20)
    def test_12_summary_counts_adjudication_causes(self):
        adjudications={1:('hash',{'category':'CLAIM_BOUNDARY_DISAGREEMENT'})}
        x=analyze_source_journals(self.first,self.second,self.cues,
            pinned_first_head=ZERO,pinned_second_head=ZERO,
            adjudications=adjudications,pinned_adjudication_head=ZERO)
        self.assertEqual(x['adjudicated_causes'],{'CLAIM_BOUNDARY_DISAGREEMENT':1})
        self.assertFalse(x['independent_gold_certified'])
if __name__=='__main__':unittest.main()