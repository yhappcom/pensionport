"""Source-first semantic challenge docket, synthetic transcript only."""
from __future__ import annotations
import copy
import unittest

from ire.v6.atomic_exchange import NUMBER, audit_host_atomic_exchange
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from ire.v6.semantic_frontier import source_first_semantic_frontier
from ire.v6.source import verify_source
from ire.v6.tests.test_atomic_exchange import HostAtomExchangeTests
from ire.v6.tests.test_source_and_proof import VIDEO, make_manifest, make_srt


class SemanticFrontierTests(unittest.TestCase):
    def setUp(self):
        base=HostAtomExchangeTests("test_all_cues_number_context_and_stance_bound_but_not_semantic_gold")
        base.setUp()
        self.addCleanup(base.doCleanups)
        self.fx=base

    def test_qualifier_nearby_is_not_silently_dropped(self):
        r=source_first_semantic_frontier(self.fx.source,self.fx.exchange)
        by=r["review_cases_by_kind"]
        self.assertGreater(by["NEARBY_QUALIFIER_EXCLUDED_FROM_CONTEXT"],0)
        self.assertGreater(by["QUALIFIER_OR_CORRECTION_CUE"],0)
        self.assertFalse(r["semantic_exhaustiveness_verified"])
        self.assertFalse(r["p0_go"])
        self.assertEqual(r["scoped_original_cues"],4)

    def test_synthetic_source_text_is_never_returned(self):
        r=source_first_semantic_frontier(self.fx.source,self.fx.exchange)
        import json
        encoded=json.dumps(r,ensure_ascii=False)
        self.assertNotIn("연금저축의 예상 수익",encoded)
        self.assertNotIn("하지만 실제로는",encoded)
        self.assertNotIn("세금 조건은",encoded)

    def test_source_model_mismatch_remains_hard_rejection(self):
        e=copy.deepcopy(self.fx.exchange)
        e["cue_dispositions"].pop()
        with self.assertRaises(InvalidInput):
            source_first_semantic_frontier(self.fx.source,e)

    def test_model_self_label_as_approved_is_rejected(self):
        e=copy.deepcopy(self.fx.exchange)
        e["atoms"][0]["semantic_truth_certified"]=True
        with self.assertRaises(InvalidInput):
            source_first_semantic_frontier(self.fx.source,e)

    def test_numeric_cue_mismatch_is_not_masked_by_review_docket(self):
        e=copy.deepcopy(self.fx.exchange)
        e["cue_dispositions"][0]["numeric_tokens"]=[]
        with self.assertRaises(InvalidInput):
            source_first_semantic_frontier(self.fx.source,e)

    def test_no_atom_risky_cue_is_explicit_review(self):
        e=copy.deepcopy(self.fx.exchange)
        e["cue_dispositions"][0].update(
            disposition="NO_ATOM",claim_ids=[],note="모델 판단으로 후보 없음")
        e["atoms"].pop(0)
        r=source_first_semantic_frontier(self.fx.source,e)
        self.assertGreater(r["review_cases_by_kind"]["FINANCIAL_NO_ATOM"],0)
        self.assertFalse(r["independent_gold_recall_measured"])

    def test_unknown_speaker_and_missing_date_trigger_review(self):
        e=copy.deepcopy(self.fx.exchange)
        e["atoms"][0]["speaker"]="UNKNOWN"
        r=source_first_semantic_frontier(self.fx.source,e)
        self.assertGreater(r["review_cases_by_kind"]["SPEAKER_OR_STANCE_AMBIGUITY"],0)
        self.assertGreater(r["review_cases_by_kind"]["FINANCIAL_FACT_DATE_SCOPE_UNKNOWN"],0)

    def test_multiple_source_anchors_adjacent_to_same_qualifier_deduplicated(self):
        e=copy.deepcopy(self.fx.exchange)
        # C00001 spans original cues 1 and 2; cue 3 qualifier is then
        # adjacent to both 1 and 2 but outside its declared context.
        e["atoms"][0]["source_refs"].append(
            {"cue_index":2,"quote":self.fx.source.cues[1].text})
        e["atoms"][0]["context_cue_indices"]=[1,2]
        e["atoms"][0]["stance"]="CORRECTED"
        e["cue_dispositions"][1]["claim_ids"].insert(0,"C00001")
        r=source_first_semantic_frontier(self.fx.source,e)
        matching=[x for x in r["review_cases"]
                  if x["kind"]=="NEARBY_QUALIFIER_EXCLUDED_FROM_CONTEXT"
                  and x["claim_id"]=="C00001" and x["cue_index"]==3]
        self.assertEqual(len(matching),1)

    def test_repeatability_and_source_identity(self):
        r=source_first_semantic_frontier(self.fx.source,self.fx.exchange)
        r2=source_first_semantic_frontier(self.fx.source,self.fx.exchange)
        self.assertEqual(r,r2)
        self.assertRegex(r["review_case_census_sha256"],r"^[0-9a-f]{64}$")
        self.assertEqual(len(r["review_cases"]),r["review_case_count"])
        self.assertEqual(len({x["case_id"] for x in r["review_cases"]}),
                         r["review_case_count"])

    def test_compound_single_candidate_creates_case(self):
        raw=make_srt(["연금과 ISA를 같이 고려하고 또한 투자 위험도 검토합니다."])
        m=make_manifest(raw,cut=1)
        src=verify_source(raw,m,expected_source_sha256=sha256(raw),
                          expected_manifest_sha256=json_digest(m))
        from ire.v6.atomic_exchange import NUMBER
        text=src.cues[0].text
        e={"schema":"IRE_V6_HOST_ATOMIC_EXCHANGE_V1",
           "video_id":VIDEO,"source_sha256":src.source_sha256,
           "manifest_sha256":src.manifest_sha256,
           "cue_dispositions":[{"cue_index":1,
             "cue_text_sha256":sha256(text.encode()),
             "disposition":"CANDIDATES","claim_ids":["C00001"],
             "numeric_tokens":NUMBER.findall(text),"note":""}],
           "atoms":[{"claim_id":"C00001","owner_window_id":src.owner(1),
             "proposition":"ISA와 연금을 함께 고려합니다.","kind":"OPINION",
             "stance":"AFFIRMED","speaker":"NARRATOR",
             "source_refs":[{"cue_index":1,"quote":text}],
             "context_cue_indices":[1],"condition_cue_indices":[],
             "exception_cue_indices":[],"numeric_references":[],"as_of":None}]}
        result=source_first_semantic_frontier(src,e)
        self.assertEqual(result["review_cases_by_kind"][
            "COMPOUND_CUE_SINGLE_OR_NO_CANDIDATE"],1)


if __name__=="__main__":
    unittest.main()
