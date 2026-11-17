"""V166 E1 source-only to frozen native V123 quarantine adapter.

All sample SRT and claim texts are synthetic. Passing does not certify owner
video #1 or reduce the pending external original evidence count.
"""
from __future__ import annotations

import copy
import unittest

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from test_v164_typed_v123 import TypedReviewSyntheticTests
from v166_source_only_to_v123_quarantine import (
    compile_b0001_source_only_to_native_review,
)

NOTE = (
    "ChatGPT 원문 맥락 확인: 이 다섯 건은 실제로 발화된 질문, "
    "제안, 조건부 가설과 독서 의견으로만 보존합니다. "
    "금융사실이나 전략 효과, 개인투자 권유가 아니므로 연구 지식에는 포함하지 않습니다."
)


class V166TypedToNativeQuarantineTests(unittest.TestCase):
    def setUp(self):
        fx = TypedReviewSyntheticTests("test_01_all_five_synthetic_source_speech_rows_attested")
        fx.setUp()
        self.fx = fx
        self.source = fx.source
        self.exchange = {"atoms": list(fx.atoms.values())}
        atom_rows = []
        for row in fx.legacy.values():
            item = copy.deepcopy(row)
            item.update({
                "official_body_sha256": None,
                "official_effective_as_of": None,
                "financial_scope_checked": False,
                "speaker_stance_checked": True,
                "conditions_exceptions_checked": True,
                "numeric_period_checked": True,
                "counterexample_checked": True,
                "private_review_note_sha256": sha256(b"synthetic reviewer note"),
            })
            atom_rows.append(item)
        self.review = {
            "source_sha256": self.source.source_sha256,
            "manifest_sha256": self.source.manifest_sha256,
            "review_executor": "CHATGPT_IN_CHAT",
            "source_cues": [{"cue_index":i, "status":"REVIEWED"} for i in range(1,121)],
            "atom_verdicts": atom_rows,
            "quarantine": {
                "schema":"IRE_V123_SOURCE_PINNED_QUARANTINE_V1",
                "source_sha256":self.source.source_sha256,
                "manifest_sha256":self.source.manifest_sha256,
                "review_executor":"CHATGPT_IN_CHAT",
                "cue_rows":[],
                "atom_rows":[{
                    "claim_id":"C00012",
                    "atom_sha256":fx.legacy["C00012"]["atom_sha256"],
                    "reason_code":"NON_RESEARCH_CONTENT",
                    "private_review_note_sha256":sha256(b"synthetic old exclusion"),
                    "context_dependencies_checked":True
                }],
                "audio_unverified_cue_indices":[],
                "private_chat_quarantine_review_sha256":sha256(b"synthetic prior chat quarantine"),
            },
            "unresolved_high_risk_omissions":12,
            "disagreements_adjudicated":False,
            "source_first_pass_completed":True,
            "counterexample_pass_completed":True,
            "as_of":"2026-11-17",
        }

    def transform(self, *, source=None, exchange=None, review=None, rows=None, note=NOTE):
        return compile_b0001_source_only_to_native_review(
            source or self.source, exchange or self.exchange,
            review or self.review, rows if rows is not None else self.fx.rows,
            final_chat_quarantine_note=note)

    def test_01_five_source_only_quarantined_without_finance_fact_promotion(self):
        before = copy.deepcopy(self.review)
        got = self.transform()
        final = got["compiled_chat_review"]
        change = {x["claim_id"]:x for x in final["atom_verdicts"]}
        self.assertEqual(got["source_only_quarantined_ids"],
            ["C00001","C00003","C00277","C00285","C00293"])
        self.assertEqual(len(final["quarantine"]["atom_rows"]), 6)
        self.assertEqual(sum(x["status"]=="EXCLUDE_FROM_RESEARCH" for x in change.values()),6)
        self.assertEqual(sum(x["status"]=="OPEN" for x in change.values()),3)
        self.assertEqual(final["unresolved_high_risk_omissions"],12)
        self.assertFalse(final["disagreements_adjudicated"])
        self.assertFalse(got["release_authorized_by_compiler"])
        self.assertFalse(got["financial_factual_truth_certified"])
        self.assertEqual(self.review,before)

    def test_02_three_objective_facts_stay_unverified_and_open(self):
        got = self.transform()
        a = {r["claim_id"]:r for r in got["compiled_chat_review"]["atom_verdicts"]}
        self.assertTrue(all(a[cid]["status"]=="OPEN" for cid in
                            ("C00002","C00009","C00010")))

    def test_03_false_quote_rejected(self):
        rows = copy.deepcopy(self.fx.rows)
        rows[0]["verbatim_anchor"] = "원문에 없는 말"
        with self.assertRaises(InvalidInput):
            self.transform(rows=rows)

    def test_04_missing_original_exclusion_ledger_rejected(self):
        r = copy.deepcopy(self.review)
        del r["quarantine"]
        with self.assertRaises(InvalidInput):
            self.transform(review=r)

    def test_05_wrong_typed_row_count_rejected(self):
        with self.assertRaises(InvalidInput):
            self.transform(rows=self.fx.rows[:4])

    def test_06_unauthorized_factual_exclusion_rejected(self):
        r = copy.deepcopy(self.review)
        item = next(x for x in r["atom_verdicts"] if x["claim_id"]=="C00009")
        item["status"] = "EXCLUDE_FROM_RESEARCH"
        with self.assertRaises(InvalidInput):
            self.transform(review=r)

    def test_07_final_quarantine_note_required(self):
        with self.assertRaises(InvalidInput):
            self.transform(note="automatic PASS")


if __name__ == "__main__":
    unittest.main()
