"""Synthetic risk correction and exact source numeric census; not blind gold."""
from __future__ import annotations

import copy
import unittest
from ire.v6.codec import sha256,json_digest
from ire.v6.errors import InvalidInput
from ire.v6.semantic_risk import audit_semantic_risks
from ire.v6.source_quality_audit_v30 import audit_private_source_repairs_v30


class V30SourceQualityRepairTests(unittest.TestCase):
    def setUp(self):
        from ire.v6.tests.test_stage_repair import fixture,atom,exchange
        self.src=fixture([
            '40대 직장인입니다.',
            '연금저축에 600을 납입했고 공제액은 0입니다.',
            '그럼에도 계속 납입하는 게 맞을까요?',
            '급할 때 300을 인출하여 만약의 사항에 대비합니다.',
        ])
        self.a=atom(self.src,'C00001',[2,3],[2,3],
                    '납입액과 세액공제 질문을 설명한다.',stance='QUOTED')
        self.b=atom(self.src,'C00002',[4],[4],
                    '급할 때 인출해서 비상 상황에 대비한다.',stance='UNRESOLVED')
        self.before=exchange(self.src,[self.a,self.b])
        self.after=copy.deepcopy(self.before)
        self.after['atoms'][0]['exception_cue_indices']=[3]
        self.after['atoms'][1]['condition_cue_indices']=[4]
        self.after['atoms'][1]['stance']='CONDITIONAL'
        self.new=atom(self.src,'C00003',[1],[1],
                      '40대 직장인이다.',stance='QUOTED')
        self.after=exchange(self.src,[*self.after['atoms'],self.new])
        risk=audit_semantic_risks(self.src,self.before)
        self.assertEqual(risk['review_case_count'],2)
        self.assertEqual(audit_semantic_risks(self.src,self.after)['review_case_count'],0)
        self.decisions=[{
            'case_sha256':case['case_sha256'],
            'source_cue_sha256':sha256(self.src.cues[case['cue_index']-1].text.encode()),
            'decision':'REMODELED_EXCEPTION' if case['reason']=='UNMAPPED_EXCEPTION_IN_MODEL_CONTEXT'
                       else 'REMODELED_CONDITION',
            'linked_claim_id':case['claim_id'],
            'reason':'원문에 존재하는 양보 또는 조건절을 해당 원자 주장 프레임에 직접 추가해 검토했다.'
        } for case in risk['review_cases']]

    def evaluate(self,after=None,decisions=None,changed=None,added=None,pin_after=False):
        chosen=self.after if after is None else after
        pinned=chosen if pin_after else self.after
        return audit_private_source_repairs_v30(
            self.src,self.before,self.after if after is None else after,
            self.decisions if decisions is None else decisions,
            reviewed_changed_claim_ids=['C00001','C00002'] if changed is None else changed,
            approved_new_claim_ids=['C00003'] if added is None else added,
            approved_revised_atom_sha256={a['claim_id']:json_digest(a)
                for a in pinned['atoms'] if a['claim_id'] in
                ('C00001','C00002','C00003')})

    def test_two_alerts_structurally_remodeled_no_gold(self):
        r=self.evaluate()
        self.assertEqual(r['original_semantic_risk_count'],2)
        self.assertEqual(r['revised_semantic_risk_count'],0)
        self.assertEqual(r['unreviewed_semantic_cases'],0)
        self.assertFalse(r['independent_human_gold_provided'])
        self.assertFalse(r['p0_go'])

    def test_all_four_synthetic_source_numeric_occurrences_mapped(self):
        r=self.evaluate()
        self.assertEqual(r['source_numeric_token_count'],4)
        self.assertEqual(r['source_numeric_tokens_with_atom_anchor'],4)
        self.assertEqual(r['source_cues_linked_to_candidate'],4)

    def test_numeric_missing_from_candidate_even_with_cue_link_blocked(self):
        bad=copy.deepcopy(self.after)
        bad['atoms'][1]['numeric_references']=[]
        with self.assertRaisesRegex(InvalidInput,'V30_ORIGINAL_NUMERIC_TOKEN_RECALL_GAP'):
            self.evaluate(after=bad,pin_after=True)

    def test_unanchored_age_context_not_hidden_by_financial_keyword_check(self):
        from ire.v6.tests.test_stage_repair import exchange
        bad=exchange(self.src,self.after['atoms'][:2])
        with self.assertRaisesRegex(InvalidInput,'V30_UNANCHORED_CUE'):
            self.evaluate(after=bad,added=[],pin_after=True)

    def test_unknown_new_claim_cannot_be_silently_added(self):
        with self.assertRaisesRegex(InvalidInput,'V30_UNREVIEWED_CANDIDATE_CHANGE'):
            self.evaluate(added=[])

    def test_missing_changed_claim_from_review_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'V30_UNREVIEWED_CANDIDATE_CHANGE'):
            self.evaluate(changed=['C00002'])

    def test_unsorted_changed_review_ids_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'V30_REPAIR_REVIEW_LIST_INVALID'):
            self.evaluate(changed=['C00002','C00001'])

    def test_unreviewed_same_id_rewrite_rejected(self):
        bad=copy.deepcopy(self.after)
        bad['atoms'][1]['proposition']='급할 때 인출할 수 있다고 단정한다.'
        with self.assertRaisesRegex(InvalidInput,'V30_UNREVIEWED_CANDIDATE_CHANGE'):
            self.evaluate(after=bad)

    def test_open_semantic_risk_not_considered_closed(self):
        bad=copy.deepcopy(self.after)
        bad['atoms'][1]['condition_cue_indices']=[]
        bad['atoms'][1]['stance']='UNRESOLVED'
        with self.assertRaises(InvalidInput):
            self.evaluate(after=bad)

    def test_forged_review_cue_sha_rejected(self):
        bad=copy.deepcopy(self.decisions)
        bad[0]['source_cue_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'CHAT_RISK_CUE_OR_RATIONALE_UNTRUSTED'):
            self.evaluate(decisions=bad)

    def test_duplicate_risk_decision_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'CHAT_RISK_UNKNOWN_OR_DUPLICATE_CASE'):
            self.evaluate(decisions=[self.decisions[0],self.decisions[0]])

    def test_quote_forgery_fails_before_risk_adjudication(self):
        bad=copy.deepcopy(self.after)
        bad['atoms'][0]['source_refs'][0]['quote']='FORGED NONORIGINAL'
        with self.assertRaisesRegex(InvalidInput,'HOST_ATOM_QUOTE_NOT_IN_ORIGINAL'):
            self.evaluate(after=bad)

    def test_reviewed_scope_not_certified_semantic_truth(self):
        r=self.evaluate()
        for field in ('independently_correct_numeric_units_or_scope',
                      'full_atomic_claim_recall_certified',
                      'blind_semantic_precision_recall_measured',
                      'approved_knowledge_ingestion'):
            self.assertIs(r[field],False)


if __name__=='__main__':
    unittest.main()
