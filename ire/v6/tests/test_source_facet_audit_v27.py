"""V27 synthetic negative controls, not independent gold or private SRT replay."""
from __future__ import annotations
import copy
import unittest
from unittest.mock import patch

from ire.v6.errors import InvalidInput
from ire.v6.source_facet_audit_v27 import (
    audit_source_facet_residuals, evaluate_current_question_v27)


class V27SourceFacetTests(unittest.TestCase):
    def setUp(self):
        # Lazy import prevents test discovery inflating historical counts.
        from ire.v6.tests.test_source_census_tax_guard_v26 import SourceCensusTaxGuardV26Tests
        from ire.v6.tests.test_stage_repair import fixture,atom,exchange
        self.old=SourceCensusTaxGuardV26Tests(
            'test_full_selected_and_off_topic_census_then_real_v24_pipeline')
        self.old.setUp()
        self.fixture=fixture; self.atom=atom; self.exchange=exchange
        self.args=self.old._args()

    def audit(self,**replacements):
        d={**self.args,**replacements}
        return audit_source_facet_residuals(
            d['source'],d['exchange'],d['question'],
            d['selected_claim_ids'],d['candidate_dispositions'],
            current_as_of=d['current_as_of'])

    def test_baseline_pass_source_bound_multi_subject_and_offtopic_candidate(self):
        a=self.audit()
        self.assertEqual(a['all_original_scoped_cues'],3)
        self.assertEqual(a['already_extracted_candidates'],3)
        self.assertEqual(a['selected_candidates'],2)
        self.assertEqual(a['same_facet_unselected_candidates'],0)
        self.assertFalse(a['p0_go'])

    def test_real_v26_v5_path_preserved_with_source_facet_gate(self):
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer',
                   side_effect=self.old.v24._p3) as p3:
            r=evaluate_current_question_v27(**self.args)
        p3.assert_called_once()
        self.assertEqual(r['schema'],'IRE_V6_V27_SOURCE_FACET_AUDITED_DECISION')
        self.assertIn('법정 중도인출 사유',r['answer_text'])
        self.assertFalse(r['p0_go'])
        self.assertFalse(r['source_semantic_recall_independently_verified'])

    def test_unselected_same_faceted_atom_wrongly_marked_offtopic_is_blocked(self):
        src=self.fixture([
            'IRP 중도 인출이 모두 불가능하다고 말합니다.',
            '국내 ETF 매매차익에는 15.4% 세금이 있다고 말합니다.',
            'IRP 중도 인출에는 일부 예외가 가능하다고 설명합니다.'])
        atoms=[
            self.atom(src,'C00001',[1],[1],
                      'IRP 중도인출은 모두 불가능하다.',stance='UNRESOLVED'),
            self.atom(src,'C00002',[2],[2],
                      'ETF 매매차익은 15.4% 과세된다.',stance='UNRESOLVED'),
            self.atom(src,'C00003',[3],[3],
                      'IRP 중도인출에는 예외가 있다.',stance='UNRESOLVED')]
        ex=self.exchange(src,atoms)
        dispositions=self.old._census(self.args['question'],ex,['C00001','C00002'])
        with self.assertRaisesRegex(InvalidInput,'UNSELECTED_SAME_FACET'):
            self.audit(source=src,exchange=ex,
                       candidate_dispositions=dispositions)

    def test_mismatched_source_cue_can_no_longer_be_marked_no_atom(self):
        src=self.fixture(['IRP 중도 인출은 언제든 안 됩니다.',
                          'ETF 매매차익은 모두 과세됩니다.'])
        ex=self.exchange(src,[
            self.atom(src,'C00001',[1],[1],
                      'IRP 중도인출이 불가능하다고 단정한다.',stance='UNRESOLVED')])
        disp=self.old._census('IRP 중도인출은 가능한가요?',ex,['C00001'])
        with self.assertRaisesRegex(InvalidInput,'UNEXTRACTED'):
            self.audit(source=src,exchange=ex,question='IRP 중도인출은 가능한가요?',
                       selected_claim_ids=['C00001'],
                       candidate_dispositions=disp)

    def test_unresolved_original_cue_blocks_before_v5(self):
        a=copy.deepcopy(self.args)
        a['exchange']['cue_dispositions'][2]['disposition']='UNRESOLVED'
        a['exchange']['cue_dispositions'][2]['claim_ids']=[]
        a['exchange']['atoms']=a['exchange']['atoms'][:2]
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer') as p3:
            with self.assertRaises(InvalidInput):
                evaluate_current_question_v27(**a)
        p3.assert_not_called()

    def test_missing_source_quote_no_longer_reaches_v5(self):
        a=copy.deepcopy(self.args)
        a['exchange']['atoms'][0]['source_refs'][0]['quote']='FORGED'
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer') as p3:
            with self.assertRaisesRegex(InvalidInput,'QUOTE_NOT_IN_ORIGINAL'):
                evaluate_current_question_v27(**a)
        p3.assert_not_called()

    def test_incomplete_candidate_dispositions_rejected(self):
        d=self.args['candidate_dispositions'][:-1]
        with self.assertRaisesRegex(InvalidInput,'MISSING_CANDIDATE'):
            self.audit(candidate_dispositions=d)

    def test_offtopic_candidate_without_shared_facet_allowed(self):
        r=self.audit()
        self.assertEqual(r['already_extracted_candidates']-r['selected_candidates'],1)
        self.assertFalse(r['independent_human_gold_verified'])

    def test_forged_offtopic_label_against_same_facet_rejected(self):
        src=self.fixture(['IRP 중도인출은 절대 안 됩니다.',
                          'IRP 중도인출 예외 사유를 확인해야 합니다.'])
        ex=self.exchange(src,[
            self.atom(src,'C00001',[1],[1],
                      'IRP 중도인출은 절대 안 된다.',stance='UNRESOLVED'),
            self.atom(src,'C00002',[2],[2],
                      'IRP 중도인출에는 법정 예외가 있다.',stance='UNRESOLVED')])
        question='IRP 중도인출이 전혀 불가능한가요?'
        d=self.old._census(question,ex,['C00001'])
        with self.assertRaisesRegex(InvalidInput,'UNSELECTED_SAME_FACET'):
            self.audit(source=src,exchange=ex,question=question,
                       selected_claim_ids=['C00001'],
                       candidate_dispositions=d)

    def test_answer_requires_stable_question_hash(self):
        a=copy.deepcopy(self.args)
        a['candidate_dispositions'][0]['question_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'SOURCE_OR_DATE_NOT_VERIFIED'):
            self.audit(**a)

    def test_numeric_source_token_cannot_be_silently_edited(self):
        a=copy.deepcopy(self.args)
        a['exchange']['cue_dispositions'][1]['numeric_tokens']=[]
        with self.assertRaisesRegex(InvalidInput,'NUMERIC_CENSUS_MISMATCH'):
            self.audit(**a)

    def test_source_review_never_certifies_release(self):
        a=self.audit()
        self.assertFalse(a['all_real_original_atoms_extracted'])
        self.assertTrue(a['same_chat_semantic_truth_only'])
        self.assertFalse(a['personal_financial_advice_approved'])


if __name__=='__main__':
    unittest.main()
