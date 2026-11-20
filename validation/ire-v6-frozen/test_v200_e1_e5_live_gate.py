"""V200 native E1-E5 readiness tests (synthetic source only, never owner gold)."""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import EngineChatSession, COMMIT
from v200_e1_e5_live_gate import evaluate_live, SCHEMA


def original():
    return (
        "1\n00:00:01,000 --> 00:00:01,900\n"
        "이 상품은 조건에 따라 손실이 발생할 수 있습니다.\n\n"
        "2\n00:00:02,000 --> 00:00:02,900\n"
        "이체 수수료는 상품과 회사에 따라 다릅니다."
    ).encode("utf-8")


class TestV200LiveReadiness(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raw = original()
        self.db = Path(self.tmp.name) / "owner.sqlite"
        self.engine = EngineChatSession(
            self.db, self.raw, "AbCdEf12345",
            owner_source_sha256=sha256(self.raw),
            window_size=2, expected_window_count=1
        )

    def commit(self, *, with_claims):
        challenge = self.engine.prepare(limit=2, source_first_only=True)
        rows = []
        for cue in challenge["target_cues"]:
            idx = cue["cue_index"]
            claims = []
            if with_claims:
                claims = [{
                    "proposition": ("이 상품은 조건에 따라 손실이 발생할 수 있다고 설명한다."
                                    if idx == 1 else
                                    "이체 수수료는 상품과 회사에 따라 다르다고 설명한다."),
                    "kind": "FACT",
                    "quote": ("이 상품은 조건에 따라 손실이 발생할 수 있습니다."
                              if idx == 1 else
                              "이체 수수료는 상품과 회사에 따라 다릅니다."),
                    "context_cue_indices": [idx],
                    "conditions": ["특정 회사 및 상품 조건"] if idx == 2 else ["일부 조건"],
                    "exceptions": ["원금 보장으로 단정할 수 없음"] if idx == 1 else [],
                    "numeric_tokens": [],
                    "high_risk": True, "needs_official_source": True,
                }]
            rows.append({
                "cue_index": idx, "source_text_sha256": cue["source_text_sha256"],
                "disposition": "ASSERTION" if with_claims else "NON_RESEARCH",
                "analysis": "원문을 확인한 미승인 검토 결과이며 실제 금융 사실에 대한 증명은 아닙니다.",
                "speaker_role": "HOST", "limitations_checked": True,
                "claims": claims,
            })
        self.engine.submit(challenge, {
            "schema": COMMIT, "challenge_sha256": challenge["challenge_sha256"],
            "review_executor": "CHATGPT_IN_CHAT", "responses": rows,
        })

    def test_01_e1_first_pass_incomplete_on_new_live_journal(self):
        report = evaluate_live(self.engine)
        self.assertEqual(report["schema"], SCHEMA)
        self.assertEqual(report["e1"]["source_first_pass"], "INCOMPLETE")
        self.assertIn("E1_ORIGINAL_CUE_REVIEW_INCOMPLETE", report["blockers"])
        self.assertEqual(report["e4"]["status"], "NOT_RUN")
        self.assertEqual(report["e5"]["knowledge_published"], 0)

    def test_02_source_census_complete_is_not_e3_or_e4(self):
        self.commit(with_claims=False)
        report = evaluate_live(self.engine)
        self.assertEqual(report["e1"]["source_first_pass"], "COMPLETE")
        self.assertEqual(report["e1"]["cue_reviewed"], 2)
        self.assertIn("E2_NO_APPROVABLE_ATOMS", report["blockers"])
        self.assertFalse(report["all_stages_passed"])
        self.assertFalse(report["ready_for_financial_advice"])

    def test_03_unmapped_conditions_and_role_cannot_be_hidden(self):
        self.commit(with_claims=True)
        report = evaluate_live(self.engine)
        self.assertEqual(report["e2"]["staged_atoms"], 2)
        self.assertEqual(report["e2"]["unmapped_condition_terms"], 2)
        self.assertEqual(report["e2"]["unmapped_exception_terms"], 1)
        self.assertEqual(report["e2"]["unresolved_stance_atoms"], 2)
        self.assertEqual(report["e2"]["unknown_speaker_atoms"], 2)
        self.assertIn("E2_SOURCE_CONDITIONS_EXCEPTIONS_UNMAPPED", report["blockers"])
        self.assertIsNone(report["e3"]["precision"])

    def test_04_no_forged_dict_as_verified_engine(self):
        with self.assertRaisesRegex(InvalidInput, "REAL_V176_SESSION_REQUIRED"):
            evaluate_live({
                "source_first_review_complete": True,
                "e3_approved": True,
                "v123_approved": True,
                "e5_published": True,
            })

    def test_05_e3_requires_actual_pinned_e3_object_not_user_dict(self):
        self.commit(with_claims=True)
        with self.assertRaisesRegex(InvalidInput, "PINNED_E3_OBJECT_REQUIRED"):
            evaluate_live(self.engine, v199={
                "reviewed": 6, "e3_approved": True,
                "financial_fact_verified": True,
            })

    def test_06_checkpoint_reopen_determinism(self):
        self.commit(with_claims=True)
        original_result = evaluate_live(self.engine)
        reopened = EngineChatSession(
            self.db, self.raw, "AbCdEf12345",
            owner_source_sha256=sha256(self.raw),
            window_size=2, expected_window_count=1
        )
        self.assertEqual(original_result, evaluate_live(reopened))
        self.assertEqual(original_result["owner_head_sha256"],
                         reopened.progress()["checkpoint_head_sha256"])


if __name__ == "__main__":
    unittest.main()
