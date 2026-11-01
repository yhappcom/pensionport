"""Exact arithmetic tests on independently created synthetic SRT claims."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from ire.chat_bridge import ConversationResearchSession
from ire.knowledge import empty_knowledge, ingest_new_video
from ire.source import sha256
from ire.v3_numeric import check_cited_calculation
from test_engine import VID, empty_frame

SENTENCES = [
    "가상 검산: 100만원에서 16.5%를 공제하면 84.6만원이라고 주장합니다.",
    "가상 인출: 원금 200만원에서 매월 4만원씩 36개월 지출하면 56만원이 남습니다.",
    "가상 회수: 추가 비용 1800만원을 내고 매월 25만원을 받으면 6년이 걸립니다.",
    "가상 합계: 매달 450만원씩 36개월이면 16200만원이 됩니다.",
]


def build_synthetic_numeric_knowledge(root):
    blocks = []
    for i, line in enumerate(SENTENCES, 1):
        start = (i - 1)*2
        blocks.append(
            f"{i}\n00:00:{start:02d},000 --> "
            f"00:00:{start + 1:02d},500\n{line}")
    raw = ("\n\n".join(blocks) + "\n").encode("utf-8")
    digest = sha256(raw)
    session = ConversationResearchSession(raw, VID, digest,
                                          str(root / "private_sessions"))
    packet = session.next_packet()
    assert len(packet["primary_cues"]) == 4
    refs = [
        ["100만원", "16.5%", "84.6만원"],
        ["200만원", "4만원", "36개월", "56만원"],
        ["1800만원", "25만원", "6년"],
        ["450만원", "36개월", "16200만원"]
    ]
    claims = []
    for i, line in enumerate(SENTENCES, 1):
        measurements = [
            {"value_text": literal, "unit": "원" if "원" in literal else "%",
             "measure_kind": "synthetic cited value", "reference_cue": i}
            for literal in refs[i - 1]
        ]
        claims.append({
            "proposition": line,
            "claim_types": ["NUMERIC"],
            "frame": empty_frame(
                financial_event="가상 산술 예제",
                measurements=measurements,
                modality="HYPOTHESIS"),
            "source_refs": [{"cue_index": i, "quote": line}]
        })
    session.accept({
        "schema": "IRE_CHAT_WINDOW_ANSWER_V1",
        "session_id": packet["session_id"],
        "window_id": packet["window_id"],
        "packet_sha256": packet["packet_sha256"],
        "claims": claims,
        "cue_dispositions": [
            {"cue_index": i, "status": "LINKED", "reason": None}
            for i in range(1, 5)]
    })
    report = json.loads(Path(session.finalize()["private_report_path"]).read_text())
    knowledge = ingest_new_video(empty_knowledge(), raw, report)
    return knowledge, [x["global_claim_id"] for x in knowledge["claims"]]


def operand(value, unit, literal):
    return {"value": str(value), "unit": unit, "source_literal": literal}


class V3ExactArithmeticTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.kb, self.ids = build_synthetic_numeric_knowledge(Path(temp.name))

    def submit(self, index, operation, operands, reported):
        return {
            "schema": "IRE_V3_CITED_FINANCE_CALCULATION_V1",
            "global_claim_id": self.ids[index],
            "operation": operation,
            "operands": operands,
            "reported_result": reported,
        }

    def test_net_after_percent_detects_source_arithmetic_mismatch(self):
        report = check_cited_calculation(self.kb, self.submit(
            0, "NET_AFTER_PERCENT",
            {"gross": operand("100", "만원", "100만원"),
             "percent": operand("16.5", "%", "16.5%")},
            operand("84.6", "만원", "84.6만원")))
        self.assertEqual(report["computed_value"], "83.500")
        self.assertFalse(report["arithmetic_consistent"])
        self.assertEqual(report["difference_in_computed_unit"], "1.100")
        self.assertFalse(report["financial_truth_certified"])

    def test_withdrawal_remainder_is_mathematically_consistent(self):
        report = check_cited_calculation(self.kb, self.submit(
            1, "REMAINDER_AFTER_PERIODIC",
            {"principal": operand("200", "만원", "200만원"),
             "periodic": operand("4", "만원", "4만원"),
             "periods": operand("36", "개월", "36개월")},
            operand("56", "만원", "56만원")))
        self.assertTrue(report["arithmetic_consistent"])
        self.assertEqual(report["computed_value"], "56")

    def test_payback_calculation_computes_months_and_converts_years(self):
        report = check_cited_calculation(self.kb, self.submit(
            2, "PAYBACK_PERIOD",
            {"initial_cost": operand("1800", "만원", "1800만원"),
             "monthly_increase": operand("25", "만원", "25만원")},
            operand("6", "년", "6년")))
        self.assertTrue(report["arithmetic_consistent"])
        self.assertEqual(report["computed_value"], "72")

    def test_multiplying_periodic_amount_and_months(self):
        report = check_cited_calculation(self.kb, self.submit(
            3, "MULTIPLY_PERIODIC",
            {"periodic": operand("450", "만원", "450만원"),
             "periods": operand("36", "개월", "36개월")},
            operand("16200", "만원", "16200만원")))
        self.assertTrue(report["arithmetic_consistent"])
        self.assertEqual(report["computed_value"], "16200")

    def test_missing_source_literal_fails_closed(self):
        query = self.submit(
            0, "NET_AFTER_PERCENT",
            {"gross": operand("100", "만원", "1000만원"),
             "percent": operand("16.5", "%", "16.5%")}, None)
        with self.assertRaisesRegex(ValueError, "V3_CALC_SOURCE_LITERAL_NOT_CITED"):
            check_cited_calculation(self.kb, query)

    def test_wrong_numeric_value_not_passed_by_literal(self):
        query = self.submit(
            0, "NET_AFTER_PERCENT",
            {"gross": operand("1000", "만원", "100만원"),
             "percent": operand("16.5", "%", "16.5%")}, None)
        with self.assertRaisesRegex(ValueError, "V3_CALC_LITERAL_VALUE_NOT_TRACEABLE"):
            check_cited_calculation(self.kb, query)

    def test_wrong_currency_unit_refused(self):
        query = self.submit(
            0, "NET_AFTER_PERCENT",
            {"gross": operand("100", "억원", "100만원"),
             "percent": operand("16.5", "%", "16.5%")}, None)
        with self.assertRaisesRegex(ValueError, "V3_CALC_SOURCE_UNIT_NOT_TRACEABLE"):
            check_cited_calculation(self.kb, query)

    def test_wrong_period_count_refused(self):
        query = self.submit(
            1, "REMAINDER_AFTER_PERIODIC",
            {"principal": operand("200", "만원", "200만원"),
             "periodic": operand("4", "만원", "4만원"),
             "periods": operand("36.5", "개월", "36개월")}, None)
        with self.assertRaisesRegex(ValueError, "V3_CALC_LITERAL_VALUE_NOT_TRACEABLE"):
            check_cited_calculation(self.kb, query)

    def test_ungrounded_reported_result_refused(self):
        query = self.submit(
            1, "REMAINDER_AFTER_PERIODIC",
            {"principal": operand("200", "만원", "200만원"),
             "periodic": operand("4", "만원", "4만원"),
             "periods": operand("36", "개월", "36개월")},
            operand("999", "만원", "999만원"))
        with self.assertRaisesRegex(ValueError, "V3_CALC_SOURCE_LITERAL_NOT_CITED"):
            check_cited_calculation(self.kb, query)

    def test_optional_reported_result_leaves_factual_truth_unattested(self):
        report = check_cited_calculation(self.kb, self.submit(
            3, "MULTIPLY_PERIODIC",
            {"periodic": operand("450", "만원", "450만원"),
             "periods": operand("36", "개월", "36개월")}, None))
        self.assertIsNone(report["arithmetic_consistent"])
        self.assertFalse(report["tax_and_legal_assumptions_verified"])
        self.assertFalse(report["investment_recommendation_authorized"])


    def test_private_cli_saves_redacted_audit_without_exposing_amounts(self):
        import subprocess
        import sys
        from ire.knowledge import save_private_snapshot
        folder = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(folder))
        saved = save_private_snapshot(self.kb, str(folder / "knowledge"))
        payload = self.submit(
            0, "NET_AFTER_PERCENT",
            {"gross": operand("100", "만원", "100만원"),
             "percent": operand("16.5", "%", "16.5%")},
            operand("84.6", "만원", "84.6만원"))
        submission = folder / "calculation.json"
        submission.write_text(json.dumps(payload, ensure_ascii=False))
        cmd = [sys.executable, "-m", "ire.v3_numeric", "verify",
               "--private-knowledge-snapshot", saved,
               "--private-calculation", str(submission),
               "--private-audit-dir", str(folder / "numeric_audits")]
        proc = subprocess.run(cmd, text=True, capture_output=True)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        receipt = json.loads(proc.stdout)
        self.assertEqual(receipt["status"], "REVIEW_REQUIRED_DIFFERENCE")
        self.assertFalse(receipt["financial_truth_approved"])
        self.assertNotIn("84.6만원", proc.stdout)
        self.assertNotIn("16.5%", proc.stdout)
        private = Path(receipt["private_audit_path"])
        self.assertTrue(private.is_file())
        self.assertEqual(private.stat().st_mode & 0o077, 0)
        self.assertFalse(json.loads(private.read_text())[
            "financial_truth_certified"])
        again = subprocess.run(cmd, text=True, capture_output=True)
        self.assertEqual(again.returncode, 3)
        self.assertEqual(json.loads(again.stdout)["status"], "FAILED_CLOSED")



if __name__ == "__main__":
    unittest.main()
