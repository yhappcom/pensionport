"""V31 synthetic host-evidence boundary tests. No human-blind gold or private SRT."""
from __future__ import annotations

import copy
import unittest
from pathlib import Path
from unittest.mock import patch

from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from ire.v6.chat_led_evidence_v31 import (
    prepare_private_chat_packet_v31, audit_chat_evidence_v31,
    evaluate_chat_question_v31,
)


class ChatLedEvidenceV31Tests(unittest.TestCase):
    def setUp(self):
        # Import earlier TestCase only inside setUp to avoid double test discovery.
        from ire.v6.tests.test_current_law_reassessment import CurrentLawReassessmentTests
        from ire.v6.tests.test_stage_repair import exchange
        old=CurrentLawReassessmentTests(
            'test_current_law_after_video_publication_is_valid_for_current_advice')
        old.setUp()
        self.src=old.source
        atoms=copy.deepcopy(old.ex['atoms'])
        # Original negative claim is attributed as unverified, NOT model truth.
        atoms[0]['stance']='UNRESOLVED'
        self.ex=exchange(self.src,atoms)
        self.asof=old.asof
        self.evidence=old.evidence
        self.decisions=old.decisions
        self.q='IRP 중도인출은 전혀 불가능하고, ETF 매매차익은 모두 15.4% 과세되나요?'
        self.selected=['C00001','C00002']
        self.meaning=[]
        self.prior=[]
        meanings={
            'C00001':'SOURCE_INCORRECT_CURRENT',
            'C00002':'SOURCE_SCOPE_OVERSTATED',
            'C00003':'SUPPORTED_WITH_CONTEXT',
        }
        for atom in self.ex['atoms']:
            cid=atom['claim_id']
            self.meaning.append({
                'claim_id':cid,'claim_frame_sha256':json_digest(atom),
                'source_cue_sha256':[sha256(self.src.cues[r['cue_index']-1].text.encode())
                                     for r in atom['source_refs']],
                'source_kind':atom['kind'],
                'source_stance':atom['stance'],
                'source_speaker':atom['speaker'],
                'reviewed_condition_cue_indices':atom['condition_cue_indices'],
                'reviewed_exception_cue_indices':atom['exception_cue_indices'],
                'numeric_scope_checked':True,
                'meaning_verdict':meanings[cid],
                'reason':'현재 질문의 원문 단정과 적용 범위, 법적 예외 및 숫자의 출처를 확인하였다.',
                'reviewer':'CHATGPT_CURRENT_TURN',
                'reviewed_as_of':self.asof,
            })
            self.prior.append({
                'claim_id':cid,'claim_frame_sha256':json_digest(atom),
                'relation':'NO_MATCH_FOUND_CHAT_ONLY',
                'master_claim_id':None,'master_atom_sha256':None,
                'reason':'기존 지식 원장과 직접 일치하는 증거가 확정되지 않은 채팅 판단으로만 남긴다.',
                'reviewer':'CHATGPT_CURRENT_TURN','reviewed_as_of':self.asof,
            })
        self.relevance=[{
            'claim_id':cid,
            'question_sha256':sha256(self.q.encode()),
            'proposition_sha256':sha256(atom['proposition'].encode()),
            'relation':'COUNTERPOINT',
            'facet':'IRP_WITHDRAWAL' if cid=='C00001' else 'ETF_TAX',
            'reviewer':'CHATGPT_CURRENT_TURN',
            'reviewed_as_of':self.asof,
            'source_attribution_checked':True,
            'stance_checked':True,
            'conditions_and_exceptions_checked':True,
            'numeric_scope_checked':True,
            'reason':'원문의 전후 문맥과 해당 금융 질문의 논점·예외·범위를 검토한 근거다.',
        } for atom in self.ex['atoms'] if atom['claim_id'] in self.selected]
        self.census=[{
            'claim_id':a['claim_id'],
            'question_sha256':sha256(self.q.encode()),
            'proposition_sha256':sha256(a['proposition'].encode()),
            'disposition':'SELECTED_RELEVANT' if a['claim_id'] in self.selected
                          else 'REVIEWED_OFF_TOPIC',
            'reviewer':'CHATGPT_CURRENT_TURN','reviewed_as_of':self.asof,
            'context_checked':True,
            'reason':'채팅에서 질문 범위와 원문 문맥을 대조해 검토했으며 독립 검증은 아니다.'
        } for a in self.ex['atoms']]

    def audit(self,**change):
        kw=dict(source=self.src,exchange=self.ex,current_as_of=self.asof,
                primary_evidence=self.evidence,regulatory_decisions=self.decisions,
                meaning_reviews=self.meaning,prior_knowledge_reviews=self.prior)
        kw.update(change)
        return audit_chat_evidence_v31(**kw)

    def answer(self,**change):
        kw=dict(root=Path('/synthetic-root-no-private-zip'),question=self.q,
                source=self.src,exchange=self.ex,current_as_of=self.asof,
                primary_evidence=self.evidence,regulatory_decisions=self.decisions,
                meaning_reviews=self.meaning,prior_knowledge_reviews=self.prior,
                selected_claim_ids=self.selected,relevance_decisions=self.relevance,
                candidate_dispositions=self.census)
        kw.update(change)
        return evaluate_chat_question_v31(**kw)

    def test_all_three_host_reviews_operational_not_independent_certification(self):
        r=self.audit()
        self.assertEqual(r['candidate_claim_count'],3)
        self.assertEqual(r['chat_reviewed_education_or_correction_count'],3)
        self.assertTrue(r['operational_research_ready'])
        self.assertFalse(r['independent_human_accuracy_certified'])
        self.assertFalse(r['automatic_master_116_knowledge_merge'])
        self.assertFalse(r['p0_go'])

    def test_regulatory_source_corrections_not_direct_original_fact_reuse(self):
        rows={r['claim_id']:r for r in self.audit()['claim_review_rows']}
        self.assertTrue(rows['C00001']['corrective_education_only'])
        self.assertTrue(rows['C00002']['corrective_education_only'])
        self.assertFalse(rows['C00001']['direct_fact_reuse_allowed'])
        self.assertTrue(rows['C00003']['direct_fact_reuse_allowed'])

    def test_raw_source_or_official_excerpt_never_in_public_audit_receipt(self):
        x=str(self.audit())
        self.assertNotIn('IRP는 중도 인출이 전혀 불가능합니다',x)
        self.assertNotIn(self.evidence[0]['excerpt'],x)
        self.assertNotIn(self.q,x)

    def test_private_packet_contains_source_and_marked_private(self):
        p=prepare_private_chat_packet_v31(
            self.src,self.ex,current_as_of=self.asof,primary_evidence=self.evidence,
            start_index=0,max_claims=2)
        self.assertEqual(len(p['original_claims']),2)
        self.assertEqual(p['next_start_index'],2)
        self.assertTrue(p['private_not_for_github'])
        self.assertIn('IRP',p['original_claims'][0]['original_cues'][0]['quote'])
        self.assertEqual(p['known_official_evidence'][0]['current_rule_status'],
                         'EFFECTIVE_ON_CURRENT_ASOF_CHAT_PRIMARY_EXCERPT_ONLY')
        self.assertFalse(p['p0_go'])

    def test_private_packet_paginates_last_source_atom(self):
        p=prepare_private_chat_packet_v31(
            self.src,self.ex,current_as_of=self.asof,
            start_index=2,max_claims=2)
        self.assertEqual(p['next_start_index'],None)
        self.assertEqual(p['original_candidate_count'],3)
        self.assertEqual(p['known_official_evidence'],[])

    def test_invalid_private_packet_bounds_rejected(self):
        for start,size in [(-1,2),(0,0),(3,1),(0,26),(True,1)]:
            with self.subTest(start=start,size=size),self.assertRaisesRegex(
                    InvalidInput,'V31_PRIVATE_PACKET_SLICE_INVALID'):
                prepare_private_chat_packet_v31(
                    self.src,self.ex,current_as_of=self.asof,
                    start_index=start,max_claims=size)

    def test_missing_meaning_review_returns_explicit_pending(self):
        r=self.audit(meaning_reviews=self.meaning[:-1])
        self.assertFalse(r['operational_research_ready'])
        self.assertEqual(r['pending_candidate_ids'],['C00003'])
        self.assertFalse(r['p0_go'])

    def test_missing_current_rule_review_returns_pending(self):
        r=self.audit(regulatory_decisions=self.decisions[:1])
        self.assertEqual(r['pending_candidate_ids'],['C00002','C00003'])
        self.assertFalse(r['operational_research_ready'])

    def test_missing_prior_relation_review_prevents_complete_research(self):
        r=self.audit(prior_knowledge_reviews=self.prior[:1])
        self.assertFalse(r['operational_research_ready'])
        self.assertFalse(r['automatic_master_116_knowledge_merge'])

    def test_silent_atom_frame_modification_rejected(self):
        bad=copy.deepcopy(self.ex)
        bad['atoms'][0]['proposition']='IRP 중도인출에는 반드시 모든 법률 예외가 있다.'
        from ire.v6.tests.test_stage_repair import exchange
        bad=exchange(self.src,bad['atoms'])
        with self.assertRaises(InvalidInput):
            self.audit(exchange=bad)

    def test_changed_reviewer_identity_rejected(self):
        bad=copy.deepcopy(self.meaning)
        bad[0]['reviewer']='UNVERIFIED_HUMAN_EXPERT'
        with self.assertRaisesRegex(InvalidInput,'V31_HOST_REVIEW_HASH_DATE_OR_RATIONALE_DRIFT'):
            self.audit(meaning_reviews=bad)

    def test_changed_review_claim_digest_rejected(self):
        bad=copy.deepcopy(self.meaning)
        bad[0]['claim_frame_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'V31_HOST_REVIEW_HASH_DATE_OR_RATIONALE_DRIFT'):
            self.audit(meaning_reviews=bad)

    def test_changed_original_cue_hash_rejected(self):
        bad=copy.deepcopy(self.meaning)
        bad[0]['source_cue_sha256']=['0'*64]
        with self.assertRaisesRegex(InvalidInput,'V31_MEANING_SOURCE_CONTEXT_OR_NUMERIC_DRIFT'):
            self.audit(meaning_reviews=bad)

    def test_changed_source_attributed_speaker_rejected(self):
        bad=copy.deepcopy(self.meaning)
        bad[0]['source_speaker']='QUESTIONER'
        with self.assertRaisesRegex(InvalidInput,'V31_MEANING_SOURCE_CONTEXT_OR_NUMERIC_DRIFT'):
            self.audit(meaning_reviews=bad)

    def test_unsigned_master_prior_relation_cannot_claim_verified_relation(self):
        bad=copy.deepcopy(self.prior)
        bad[0]['relation']='SUPPORTS_PRIOR_CHAT_ONLY'
        with self.assertRaisesRegex(InvalidInput,'V31_PRIOR_KNOWLEDGE_ANCHOR_REQUIRED'):
            self.audit(prior_knowledge_reviews=bad)

    def test_chat_labeled_prior_knowledge_anchor_does_not_auto_merge(self):
        bad=copy.deepcopy(self.prior)
        bad[0]['relation']='REFINES_PRIOR_CHAT_ONLY'
        bad[0]['master_claim_id']='MASTER_000001'
        bad[0]['master_atom_sha256']='a'*64
        r=self.audit(prior_knowledge_reviews=bad)
        self.assertFalse(r['automatic_master_116_knowledge_merge'])
        self.assertTrue(r['operational_research_ready'])

    def test_law_scope_mismatch_host_review_rejected(self):
        bad=copy.deepcopy(self.meaning)
        bad[0]['meaning_verdict']='SUPPORTED_WITH_CONTEXT'
        with self.assertRaisesRegex(InvalidInput,'V31_CURRENT_LAW_HOST_MEANING_CONTRADICTION'):
            self.audit(meaning_reviews=bad)

    def test_legal_scope_missing_cannot_be_called_supported(self):
        bad=copy.deepcopy(self.meaning)
        bad[1]['meaning_verdict']='SUPPORTED_WITH_CONTEXT'
        with self.assertRaisesRegex(InvalidInput,'V31_SOURCE_SCOPE_MISSING_MEANING_NOT_ACKNOWLEDGED'):
            self.audit(meaning_reviews=bad)

    def test_unknown_financial_rule_stays_open_even_with_host_meaning(self):
        bad=copy.deepcopy(self.decisions)
        bad[0]['classification']='CURRENT_FACT_OR_APPLICABILITY_UNKNOWN'
        r=self.audit(regulatory_decisions=bad)
        self.assertIn('C00001',r['pending_candidate_ids'])
        self.assertFalse(r['operational_research_ready'])

    def test_invalid_official_excerpt_hash_rejected(self):
        bad=copy.deepcopy(self.evidence)
        bad[0]['excerpt_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'CURRENT_LAW_EXCERPT_SHA_MISMATCH'):
            self.audit(primary_evidence=bad)

    def test_expired_current_rule_rejected(self):
        bad=copy.deepcopy(self.evidence)
        bad[0]['effective_to']='2026-10-01'
        with self.assertRaisesRegex(InvalidInput,'CURRENT_CHAT_REFERENCED_RULE_NOT_CURRENT'):
            self.audit(primary_evidence=bad)

    def test_mislabeled_quoted_question_as_fact_rejected(self):
        bad=copy.deepcopy(self.ex)
        bad['atoms'][2]['kind']='QUESTION'
        from ire.v6.tests.test_stage_repair import exchange
        bad=exchange(self.src,bad['atoms'])
        revised=copy.deepcopy(self.meaning)
        revised[2]['claim_frame_sha256']=json_digest(bad['atoms'][2])
        revised[2]['source_kind']='QUESTION'
        with self.assertRaisesRegex(InvalidInput,'V31_QUESTION_CANNOT_BECOME_FACT'):
            self.audit(exchange=bad,meaning_reviews=revised)

    def test_numeric_scope_review_false_marks_pending(self):
        bad=copy.deepcopy(self.meaning)
        bad[1]['numeric_scope_checked']=False
        r=self.audit(meaning_reviews=bad)
        self.assertIn('C00002',r['pending_candidate_ids'])

    def test_actual_v27_v5_route_called_once_after_host_gate_with_synthetic_mock(self):
        from ire.v6.tests.test_advisory_decision_utility import CurrentDecisionUtilityTests
        old=CurrentDecisionUtilityTests(
            'test_actual_style_irp_and_etf_question_leads_with_decision')
        old.setUp()
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer',
                   side_effect=old._p3) as p3:
            r=self.answer()
        p3.assert_called_once()
        self.assertIn('answer_text',r)
        self.assertEqual(r['schema'],'IRE_V6_V31_CHAT_LED_FINANCE_EDUCATIONAL_ANSWER')
        self.assertTrue(r['operational_education_only'])
        self.assertFalse(r['independent_financial_accuracy_certified'])
        self.assertFalse(r['v31_hash_only_answer_receipt']['p0_go'])

    def test_missing_selected_review_blocks_before_v5(self):
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer') as p3:
            with self.assertRaisesRegex(InvalidInput,'V31_SELECTED_CHAT_EVIDENCE_NOT_RESOLVED'):
                self.answer(meaning_reviews=self.meaning[1:])
        p3.assert_not_called()

    def test_question_is_action_command_refused_before_v5(self):
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer') as p3:
            with self.assertRaisesRegex(InvalidInput,'V31_PERSONAL_FINANCIAL_EXECUTION_NOT_SUPPORTED'):
                self.answer(question='IRP 자산 지금 모두 매도해줘')
        p3.assert_not_called()

    def test_missing_candidate_disposition_refused_before_v5(self):
        with patch('ire.v6.current_advisory_bridge._v5_p3_answer') as p3:
            with self.assertRaisesRegex(InvalidInput,'V26_CENSUS_MISSING_CANDIDATE'):
                self.answer(candidate_dispositions=self.census[:-1])
        p3.assert_not_called()

    def test_current_chat_reviews_cannot_certify_independent_gold(self):
        r=self.audit()
        for key in ('independent_human_accuracy_certified',
                    'independent_gold_precision_recall_measured',
                    'automatic_master_116_knowledge_merge',
                    'user_specific_tax_or_order_approved','p0_go'):
            self.assertFalse(r[key])


if __name__=='__main__':
    unittest.main()
