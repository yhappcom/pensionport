"""V216 E2 residual-risk gate regression; synthetic cues only."""
from __future__ import annotations

import copy
import json
import unittest

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v216_e2_private_residual_evidence_guard import (
    audit_private_unapproved_evidence_risks,
)


class TestV216ResidualEvidence(unittest.TestCase):
    @staticmethod
    def raw(value):
        return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")

    def setUp(self):
        strings = [
            "차트를 보면 차이가 크게 벌어집니다.",
            "추적 차이가 낮을수록 좋습니다.",
            "장기 보유 비용도 함께 비교하세요.",
        ]
        self.exchange = {
            "source_sha256": "a" * 64,
            "atoms": [
                {"claim_id": "C00001", "speaker": "UNKNOWN",
                 "stance": "UNRESOLVED", "source_refs": [
                     {"cue_index": 1, "quote": "차트를 보면"}],
                 "context_cue_indices": [1]},
                {"claim_id": "C00002", "speaker": "UNKNOWN",
                 "stance": "UNRESOLVED", "source_refs": [
                     {"cue_index": 2, "quote": "낮을수록"}],
                 "context_cue_indices": [2, 3]},
            ],
            "cue_dispositions": [{
                "cue_index": i, "cue_text_sha256": sha256(s.encode()),
                "claim_ids": [["C00001"], ["C00002"], []][i-1],
            } for i, s in enumerate(strings, 1)],
        }
        self.coverage = {
            "source_sha256": "a" * 64,
            "new_native_v6_exchange_sha256": sha256(self.raw(self.exchange)),
            "full_original_cue_count": 3,
            "original_audio_and_screen_not_available": True,
            "independent_gold_certified": False,
            "e2_final_pass": False,
            "cues": [{
                "cue_index": i,
                "cue_text_sha256": sha256(s.encode()),
                "original_text": s,
                "native_unapproved_primary_claim_ids":
                    [["C00001"], ["C00002"], []][i-1],
                "native_unapproved_context_claim_ids":
                    [["C00001"], ["C00002"], ["C00002"]][i-1],
                "needs_original_audio_or_screen": (i == 1),
            } for i, s in enumerate(strings, 1)],
        }

    def run_guard(self, ex=None, cv=None, exbytes=None, cvbytes=None,
                  exp_ex_sha=None, exp_cv_sha=None):
        ex = self.exchange if ex is None else ex
        cv = self.coverage if cv is None else cv
        exbytes = self.raw(ex) if exbytes is None else exbytes
        cvbytes = self.raw(cv) if cvbytes is None else cvbytes
        return audit_private_unapproved_evidence_risks(
            ex, exbytes, cv, cvbytes,
            expected_exchange_sha256=(
                sha256(self.raw(self.exchange)) if exp_ex_sha is None
                else exp_ex_sha),
            expected_coverage_sha256=(
                sha256(cvbytes) if exp_cv_sha is None else exp_cv_sha),
        )

    def test_01_visual_anchor_stays_hold_after_parent_quarantine(self):
        r = self.run_guard()
        self.assertEqual(r["flagged_primary_atom_ids"], ["C00001"])
        self.assertEqual(r["flagged_context_atom_ids"], ["C00001"])
        self.assertEqual(r["source_flags_need_audio_or_screen_cue_count"], 1)
        self.assertEqual(r["candidate_count"], 2)
        self.assertFalse(r["e2_final_pass"])
        self.assertFalse(r["knowledge_published"])
        self.assertNotIn("차트를", str(r))

    def test_02_generic_text_claim_not_marked_visual(self):
        r = self.run_guard()
        self.assertNotIn("C00002", r["flagged_primary_atom_ids"])

    def test_03_change_native_bytes_rejected(self):
        with self.assertRaisesRegex(InvalidInput,
                                    "NATIVE_ORIGINAL_BYTES_OR_HASH_CHANGED"):
            self.run_guard(exbytes=self.raw(self.exchange) + b" ")

    def test_04_false_original_cue_hash_rejected(self):
        d = copy.deepcopy(self.coverage)
        d["cues"][0]["original_text"] = "주가가 반대로 움직입니다."
        with self.assertRaisesRegex(InvalidInput,
                                    "CUE_POSITION_OR_TEXT_HASH_CHANGED"):
            self.run_guard(cv=d)

    def test_05_orphan_claim_in_cue_rejected(self):
        d = copy.deepcopy(self.coverage)
        d["cues"][1]["native_unapproved_primary_claim_ids"] = []
        with self.assertRaisesRegex(InvalidInput,
                                    "CUE_NATIVE_PRIMARY_OR_RISK_FLAGS"):
            self.run_guard(cv=d)

    def test_06_unspoken_anchor_quote_rejected(self):
        d = copy.deepcopy(self.exchange)
        d["atoms"][0]["source_refs"][0]["quote"] = "수익 99% 보장"
        cv = copy.deepcopy(self.coverage)
        cv["new_native_v6_exchange_sha256"] = sha256(self.raw(d))
        with self.assertRaisesRegex(InvalidInput,
                                    "PRIMARY_SOURCE_QUOTE_UNGROUNDED"):
            self.run_guard(ex=d, cv=cv, exp_ex_sha=sha256(self.raw(d)))

    def test_07_gold_approval_forgery_rejected(self):
        for field in ("independent_gold_certified", "e2_final_pass"):
            d = copy.deepcopy(self.coverage)
            d[field] = True
            with self.assertRaisesRegex(InvalidInput,
                                        "UNJUSTIFIED_EXTERNAL_GOLD_OR_AUDIO_APPROVAL"):
                self.run_guard(cv=d)

    def test_08_audio_speaker_forgery_rejected(self):
        d = copy.deepcopy(self.exchange)
        d["atoms"][0]["speaker"] = "NARRATOR"
        cv = copy.deepcopy(self.coverage)
        cv["new_native_v6_exchange_sha256"] = sha256(self.raw(d))
        with self.assertRaisesRegex(InvalidInput,
                                    "NATIVE_ATOM_UNAPPROVED_AND_STRUCTURAL"):
            self.run_guard(ex=d, cv=cv, exp_ex_sha=sha256(self.raw(d)))

    def test_09_missing_context_row_rejected(self):
        d = copy.deepcopy(self.coverage)
        d["cues"][2]["native_unapproved_context_claim_ids"] = []
        with self.assertRaisesRegex(InvalidInput,
                                    "CONTEXT_CLAIM_DISPOSITION_DRIFT"):
            self.run_guard(cv=d)

    def test_10_malformed_flag_rejected_without_typeerror(self):
        d = copy.deepcopy(self.coverage)
        d["cues"][0]["needs_original_audio_or_screen"] = []
        with self.assertRaisesRegex(InvalidInput,
                                    "CUE_NATIVE_PRIMARY_OR_RISK_FLAGS"):
            self.run_guard(cv=d)

    def test_11_replay_deterministic_without_approval(self):
        self.assertEqual(self.run_guard(), self.run_guard())
        self.assertFalse(self.run_guard()["automatic_semantic_merge"])

    def test_12_text_only_reanchor_changes_custody_and_stays_hold(self):
        ex = copy.deepcopy(self.exchange)
        cv = copy.deepcopy(self.coverage)
        ex["atoms"][0]["source_refs"] = [{
            "cue_index": 2, "quote": "추적 차이가 낮을수록"}]
        ex["atoms"][0]["context_cue_indices"] = [2]
        ex["cue_dispositions"][0]["claim_ids"] = []
        ex["cue_dispositions"][1]["claim_ids"] = ["C00001", "C00002"]
        cv["cues"][0]["native_unapproved_primary_claim_ids"] = []
        cv["cues"][0]["native_unapproved_context_claim_ids"] = []
        cv["cues"][1]["native_unapproved_primary_claim_ids"] = [
            "C00001", "C00002"]
        cv["cues"][1]["native_unapproved_context_claim_ids"] = [
            "C00001", "C00002"]
        cv["new_native_v6_exchange_sha256"] = sha256(self.raw(ex))
        result = self.run_guard(ex=ex, cv=cv,
                                exp_ex_sha=sha256(self.raw(ex)))
        self.assertEqual(result["flagged_primary_atom_ids"], [])
        self.assertFalse(result["independent_gold_measured"])
        self.assertFalse(result["e2_final_pass"])


    def test_13_nonlist_disposition_claim_ids_fail_closed(self):
        d = copy.deepcopy(self.exchange)
        d["cue_dispositions"][0]["claim_ids"] = 777
        cv = copy.deepcopy(self.coverage)
        cv["new_native_v6_exchange_sha256"] = sha256(self.raw(d))
        with self.assertRaisesRegex(InvalidInput,
                                    "CUE_NATIVE_PRIMARY_OR_RISK_FLAGS"):
            self.run_guard(ex=d, cv=cv, exp_ex_sha=sha256(self.raw(d)))

    def test_14_nested_disposition_claim_ids_fail_closed(self):
        d = copy.deepcopy(self.exchange)
        d["cue_dispositions"][0]["claim_ids"] = [["C00001"]]
        cv = copy.deepcopy(self.coverage)
        cv["new_native_v6_exchange_sha256"] = sha256(self.raw(d))
        with self.assertRaisesRegex(InvalidInput,
                                    "CUE_NATIVE_PRIMARY_OR_RISK_FLAGS"):
            self.run_guard(ex=d, cv=cv, exp_ex_sha=sha256(self.raw(d)))


if __name__ == "__main__":
    unittest.main()
