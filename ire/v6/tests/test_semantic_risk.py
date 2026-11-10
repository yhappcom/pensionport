"""P0-2 semantic risk triage tests: synthetic Korean original only."""
from __future__ import annotations
import copy
import json
import unittest

from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from ire.v6.semantic_risk import audit_semantic_risks
from ire.v6.source import verify_source
from ire.v6.atomic_exchange import NUMBER
from ire.v6.tests import test_atomic_exchange, test_source_and_proof


class SemanticRiskTests(unittest.TestCase):
    def setUp(self):
        fx=test_atomic_exchange.HostAtomExchangeTests(
            "test_all_cues_number_context_and_stance_bound_but_not_semantic_gold")
        fx.setUp()
        self.addCleanup(fx.doCleanups)
        self.fx=fx

    def test_real_original_cue_structure_and_risk_census(self):
        r=audit_semantic_risks(self.fx.source,self.fx.exchange)
        self.assertEqual(r["scoped_cue_count"],4)
        self.assertEqual(r["model_claim_count"],3)
        self.assertGreater(r["review_case_count"],0)
        self.assertEqual(sum(r["cases_by_reason"].values()),r["review_case_count"])
        self.assertFalse(r["p0_go"])
        self.assertFalse(r["semantic_entailment_independently_verified"])

    def test_review_cases_never_include_private_original_text(self):
        r=audit_semantic_risks(self.fx.source,self.fx.exchange)
        serialized=json.dumps(r,ensure_ascii=False)
        for item in self.fx.source.cues:
            self.assertNotIn(item.text,serialized)
        self.assertNotIn("proposition",serialized)

    def test_invalid_calendar_date_is_hard_blocked(self):
        e=copy.deepcopy(self.fx.exchange)
        e["atoms"][0]["as_of"]="2026-02-30"
        with self.assertRaisesRegex(InvalidInput,"INVALID_REAL_CALENDAR_DATE"):
            audit_semantic_risks(self.fx.source,e)

    def test_leap_day_is_valid_calendar_input(self):
        e=copy.deepcopy(self.fx.exchange)
        e["atoms"][0]["as_of"]="2024-02-29"
        self.assertEqual(audit_semantic_risks(self.fx.source,e)["model_claim_count"],3)

    def test_condition_withheld_from_model_is_flagged_not_approved(self):
        e=copy.deepcopy(self.fx.exchange)
        e["atoms"][2]["stance"]="CORRECTED"
        e["atoms"][2]["condition_cue_indices"]=[]
        r=audit_semantic_risks(self.fx.source,e)
        self.assertGreater(r["cases_by_reason"]["UNMAPPED_CONDITION_IN_MODEL_CONTEXT"],0)
        self.assertFalse(r["independent_human_review_complete"])

    def test_exception_withheld_is_flagged(self):
        r=audit_semantic_risks(self.fx.source,self.fx.exchange)
        self.assertGreater(r["cases_by_reason"]["UNMAPPED_EXCEPTION_IN_MODEL_CONTEXT"],0)

    def test_neighbor_correction_not_in_context_is_flagged(self):
        e=copy.deepcopy(self.fx.exchange)
        # Claim 1 includes cue 1 only; neighbor cue 2 is "하지만".
        # For this check use explicit correction language in a pinned source.
        src,e=self._single_cue_exchange("연금 10%라고 말했지만 잘못 설명했습니다.",
                                        proposition="연금 10%는 예상입니다.",
                                        stance="CORRECTED")
        self.assertGreater(audit_semantic_risks(src,e)["review_case_count"],0)

    def test_source_quote_mismatch_still_fails_closed(self):
        e=copy.deepcopy(self.fx.exchange)
        e["atoms"][0]["source_refs"][0]["quote"]="존재하지 않는 원문"
        with self.assertRaises(InvalidInput):
            audit_semantic_risks(self.fx.source,e)

    def test_determinism_and_provenance_identity(self):
        a=audit_semantic_risks(self.fx.source,self.fx.exchange)
        b=audit_semantic_risks(self.fx.source,self.fx.exchange)
        self.assertEqual(a,b)
        self.assertEqual(len(a["case_census_sha256"]),64)
        self.assertEqual(len(set(x["case_sha256"] for x in a["review_cases"])),
                         a["review_case_count"])

    def _single_cue_exchange(self,text,*,proposition,stance="CORRECTED"):
        raw=test_source_and_proof.make_srt([text])
        manifest=test_source_and_proof.make_manifest(raw,cut=1)
        source=verify_source(raw,manifest,expected_source_sha256=sha256(raw),
                             expected_manifest_sha256=json_digest(manifest))
        tokens=NUMBER.findall(text)
        prop_tokens=NUMBER.findall(proposition)
        if any(token not in tokens for token in prop_tokens):
            raise AssertionError("test proposition token not present in source")
        atom={"claim_id":"C00001","owner_window_id":"W00001",
            "proposition":proposition,"kind":"FACT","stance":stance,"speaker":"NARRATOR",
            "source_refs":[{"cue_index":1,"quote":text}],
            "context_cue_indices":[1],"condition_cue_indices":[],
            "exception_cue_indices":[],"numeric_references":[
              {"cue_index":1,"token":token} for token in prop_tokens],
            "as_of":None}
        exchange={"schema":"IRE_V6_HOST_ATOMIC_EXCHANGE_V1",
            "video_id":source.video_id,"source_sha256":source.source_sha256,
            "manifest_sha256":source.manifest_sha256,
            "cue_dispositions":[{"cue_index":1,"cue_text_sha256":sha256(text.encode()),
                 "disposition":"CANDIDATES","claim_ids":["C00001"],
                 "numeric_tokens":tokens,"note":""}],
            "atoms":[atom]}
        return source,exchange

    def test_annual_monthly_mismatch_is_explicit_review(self):
        src,e=self._single_cue_exchange("연 10% 수익률로 설명합니다.",
                                         proposition="월 10% 수익률로 설명합니다.")
        result=audit_semantic_risks(src,e)
        self.assertEqual(result["cases_by_reason"][
            "NUMERIC_ANNUAL_MONTHLY_SCOPE_REVIEW"],1)
        self.assertFalse(result["financial_law_as_of_verified"])

    def test_questioner_role_is_review_not_automatic_correction(self):
        src,e=self._single_cue_exchange("질문은 연금저축 10%입니다.",
                                         proposition="연금저축 10%라는 질문입니다.")
        self.assertEqual(audit_semantic_risks(src,e)["cases_by_reason"][
            "QUESTION_OR_QUOTATION_SPEAKER_REVIEW"],1)

    def test_negation_polarity_is_review_not_final_verdict(self):
        src,e=self._single_cue_exchange("연금 10%라는 말은 아닙니다.",
                                         proposition="연금 10%라는 말입니다.",
                                         stance="AFFIRMED")
        # Source qualifier is not in declared context => existing structural
        # auditor fails closed; never bypass it to force a semantic score.
        with self.assertRaises(InvalidInput):
            audit_semantic_risks(src,e)


if __name__=="__main__":
    unittest.main()
