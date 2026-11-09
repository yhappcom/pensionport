"""Synthetic source-first census controls; NEVER a blind-gold claim."""
import unittest

from ire.v6.claim_census import audit_source_first_residuals
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import verify_source
from ire.v6.tests.test_source_and_proof import make_srt, make_manifest, make_model


class SourceFirstCensusTests(unittest.TestCase):
    def setup_source(self):
        raw=make_srt(["연금에서 3% 수익이고 300만원을 받는다. 그리고 세금도 없다.",
                      "다만 과세 조건은 개인별로 달라진다.",
                      "단기 주식투자는 손실이 생긴다.",
                      "어느 상품이 맞는지 질문입니다."])
        plan=make_manifest(raw,cut=2)
        source=verify_source(raw,plan,
                             expected_source_sha256=sha256(raw),
                             expected_manifest_sha256=json_digest(plan))
        return source,raw,plan

    def test_four_cues_accounted_not_automatic_claim_recall(self):
        src,_,_=self.setup_source()
        first=make_model(owner="W00001",first=1,last=1,quote1=src.cues[0].text)
        second=make_model(owner="W00002",first=3,last=3,quote1=src.cues[2].text)
        result=audit_source_first_residuals(src,{"W00001":first,"W00002":second})
        self.assertEqual(result["scope_cue_count"],4)
        self.assertEqual(result["model_anchored_cue_count"],2)
        self.assertGreaterEqual(result["unanchored_financial_heuristic_cue_count"],1)
        self.assertGreaterEqual(result["qualifier_or_contradiction_cue_count"],1)
        self.assertGreaterEqual(result["multi_atom_heuristic_cue_count"],1)
        self.assertFalse(result["all_atomic_claims_exhausted"])
        self.assertFalse(result["research_complete"])
        self.assertEqual(result["status"],"SOURCE_FIRST_SEMANTIC_RESIDUAL_OPEN")

    def test_same_cue_many_propositions_not_equated_with_one_atom(self):
        src,_,_=self.setup_source()
        one=make_model(owner="W00001",first=1,last=1,quote1=src.cues[0].text)
        two=make_model(owner="W00002",first=3,last=3,quote1=src.cues[2].text)
        actual=audit_source_first_residuals(src,{"W00001":one,"W00002":two})
        self.assertFalse(actual["all_atomic_claims_exhausted"])
        self.assertGreaterEqual(actual["multi_atom_heuristic_cue_count"],1)

    def test_missing_modelled_window_fails_closed(self):
        src,_,_=self.setup_source()
        with self.assertRaisesRegex(InvalidInput,"SOURCE_FIRST_MODEL_SCOPE_INCOMPLETE"):
            audit_source_first_residuals(src,{"W00001":make_model(owner="W00001",
                first=1,last=1,quote1=src.cues[0].text)})

    def test_wrong_quote_and_outside_scope_rejected(self):
        src,_,_=self.setup_source()
        first=make_model(owner="W00001",first=1,last=1,quote1="fabricated claim")
        second=make_model(owner="W00002",first=3,last=3,quote1=src.cues[2].text)
        with self.assertRaisesRegex(InvalidInput,"SOURCE_FIRST_ANCHOR_NOT_IN_ORIGINAL"):
            audit_source_first_residuals(src,{"W00001":first,"W00002":second})
        first["claims"][0]["source_refs"][0]["cue_index"]=0
        with self.assertRaisesRegex(InvalidInput,"SOURCE_FIRST_ANCHOR_NOT_IN_ORIGINAL"):
            audit_source_first_residuals(src,{"W00001":first,"W00002":second})

    def test_reproducible_digest_and_source_change_changes_digest(self):
        src,_,_=self.setup_source()
        first=make_model(owner="W00001",first=1,last=1,quote1=src.cues[0].text)
        second=make_model(owner="W00002",first=3,last=3,quote1=src.cues[2].text)
        mapping={"W00001":first,"W00002":second}
        a=audit_source_first_residuals(src,mapping)
        b=audit_source_first_residuals(src,mapping)
        self.assertEqual(a["cue_census_sha256"],b["cue_census_sha256"])
        self.assertEqual(a["source_sha256"],b["source_sha256"])
        self.assertFalse(a["independent_recall_measured"])


if __name__=="__main__":
    unittest.main()
