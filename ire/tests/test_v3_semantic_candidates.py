"""Blind-to-existing-study lexical/paraphrase retrieval regression fixtures.

All examples are independently written illustrative test sentences, not a
human gold standard or measured Recall@K on the original videos.
"""
from __future__ import annotations

import unittest

from ire.v3_semantic_candidates import (
    financial_concepts, semantic_candidate_score, advisory_concept_overlap)
from ire.knowledge import _overlap_score, _cross_video_candidates

def atom(text, product=None, event=None, video_sha="a"*64,
         identifier="K"+"a"*24, modality="ASSERTION"):
    return {
        "global_claim_id": identifier,
        "source_sha256": video_sha,
        "proposition": text,
        "frame": {
            "subject": None, "product": product,
            "financial_event": event, "action": None, "object": None,
            "jurisdiction": "KR", "effective_date": None,
            "conditions": [], "exceptions": [], "measurements": [],
            "modality": modality,
        }
    }


class ControlledMeaningRetrievalTests(unittest.TestCase):
    def test_gold_tax_paraphrases_are_retrieved_as_pending(self):
        old = atom("KRX 금시장 매매차익에는 비과세가 적용된다는 설명",
                   video_sha="a"*64, identifier="K"+"a"*24)
        new = atom("금 현물 거래에서 생긴 거래 이익에 세금이 붙지 않는다는 주장",
                   video_sha="b"*64, identifier="K"+"b"*24)
        shared = financial_concepts(old["proposition"]) & financial_concepts(
            new["proposition"])
        self.assertIn("KRX_GOLD", shared)
        self.assertIn("TAX_EXEMPT", shared)
        self.assertGreaterEqual(semantic_candidate_score(old,new),0.5)
        self.assertGreaterEqual(_overlap_score(old,new),0.5)
        candidates = _cross_video_candidates([new], [old])
        self.assertEqual(len(candidates),1)
        self.assertEqual(candidates[0]["review_status"],
                         "PENDING_SEPARATE_ADJUDICATION")

    def test_retirement_account_and_benefit_paraphrase(self):
        a = atom("IRP에서 퇴직금을 연금으로 지급받는 설명")
        b = atom("개인형퇴직연금 계좌에서 퇴직급여를 수령할 때의 처리")
        self.assertGreaterEqual(semantic_candidate_score(a,b),0.54)

    def test_one_shared_financial_noun_is_not_equivalence(self):
        a = atom("ETF 상품의 거래 시간")
        b = atom("상장지수펀드의 분배금 지급일")
        self.assertEqual(semantic_candidate_score(a,b),0)
        c = atom("국민연금을 연기하면 증액되는 사례")
        d = atom("연금저축펀드의 인출 절차")
        self.assertEqual(semantic_candidate_score(c,d),0)
        self.assertEqual(semantic_candidate_score(
            atom("ISA 계좌 개설"),atom("IRP 세액공제")),0)

    def test_advisory_question_expands_financial_phrasing_only(self):
        question = "거래소 금시장 매매차익의 비과세 여부를 검토"
        claim = atom("금 현물 거래로 발생한 거래 이익에는 세금이 붙지 않는다")
        self.assertGreaterEqual(advisory_concept_overlap(question,claim),2)
        self.assertEqual(advisory_concept_overlap(
            "국민연금 수령 연기를 검토", atom("ETF 자동 매수 주문")),0)

    def test_candidate_not_truth_when_modality_disagrees(self):
        left=atom("KRX 금시장 매매차익은 비과세 대상이다",
                  identifier="K"+"a"*24)
        right=atom("금 현물 거래 이익에 세금이 붙지 않는 것은 아니다",
                   video_sha="b"*64, identifier="K"+"b"*24,
                   modality="NEGATION")
        candidates=_cross_video_candidates([right],[left])
        self.assertEqual(len(candidates),1)
        self.assertEqual(candidates[0]["candidate_type"],
                         "POSSIBLE_NEGATION_CONFLICT")
        self.assertEqual(candidates[0]["review_status"],
                         "PENDING_SEPARATE_ADJUDICATION")


if __name__=="__main__":
    unittest.main()
