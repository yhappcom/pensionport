"""Fresh adversarial source-entailment and two-file persistence regressions.

Only invented, synthetic financial examples are used. No private subtitles.
"""
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ire.source import sha256
from ire.chat_bridge import ConversationResearchSession
from ire.v3_orchestrator import ChatBatchQueue
from ire.v3_semantic_audit import window_semantic_audit
from ire.v3_numeric import _read_measure
from ire.v3_evidence import (save_scope_evidence_pair, apply_v3_scope_evidence,
                             audit_v3_scope)
from test_engine import VID, empty_frame
import test_v3_evidence as fixtures
import copy


def synthetic_packet(line: str, proposition: str):
    packet = {
        "video_id": VID, "window_id": "W00001",
        "primary_cues": [{"cue_index": 1, "start_ms": 0,
                          "end_ms": 2500, "text": line}],
        "left_context_cues": [], "right_context_cues": []
    }
    answer = {"claims": [{
        "proposition": proposition,
        "claim_types": ["PRODUCT"],
        "frame": empty_frame(),
        "source_refs": [{"cue_index": 1, "quote": line}],
    }], "cue_dispositions": [{
        "cue_index": 1, "status": "LINKED", "reason": None,
    }]}
    return packet, answer


class SourceEntailmentHardeningTests(unittest.TestCase):
    def audit(self, line, proposition):
        packet, answer = synthetic_packet(line, proposition)
        return window_semantic_audit(packet, answer)

    def test_does_not_infer_monthly_payout_from_amount_only(self):
        audit = self.audit("개인연금에서 25만원을 더 받습니다.",
                           "개인연금에서 매월 25만원을 더 받는다.")
        self.assertIn("UNSUPPORTED_MONTHLY_SOURCE_UNIT",
                      [x["code"] for x in audit["critical"]])

    def test_does_not_substitute_pension_savings_for_generic_pension(self):
        audit = self.audit("개인연금에 투자하는 방법을 생각합니다.",
                           "연금저축에 투자하는 방법을 생각한다.")
        self.assertIn("UNSUPPORTED_SPECIFIC_PRODUCT_연금저축",
                      [x["code"] for x in audit["critical"]])

    def test_cited_monthly_payout_is_not_blocked(self):
        audit = self.audit("매월 개인연금에서 25만원을 더 받습니다.",
                           "개인연금에서 월 25만원을 더 받는다.")
        self.assertEqual(audit["critical"], [])

    def test_short_caption_monthly_amount_is_not_rejected(self):
        audit=self.audit("월 26까지 나옵니다.",
                         "월 26만 원까지 나올 수 있다는 사례를 설명한다.")
        self.assertEqual(audit["critical"],[])

    def test_prior_case_payment_reference_requires_review_not_data_loss(self):
        audit=self.audit("25만 원을 맞추기 위해서는 높은 수익률이 필요합니다.",
                         "앞선 월 25만 원을 맞추려면 높은 수익률이 필요하다.")
        self.assertEqual(audit["critical"],[])
        self.assertIn("UNSUPPORTED_MONTHLY_SOURCE_UNIT",
                      [x["code"] for x in audit["warnings"]])

    def test_speech_recognition_pension_typo_is_reviewable(self):
        audit=self.audit("연금제축에 1800만원을 넣는다면", 
                         "연금저축에 1800만원을 넣는다면")
        self.assertEqual(audit["critical"],[])

    def test_korean_alias_for_irp_is_accepted(self):
        audit = self.audit("개인형퇴직연금은 예금 상품을 담을 수 있다.",
                           "IRP는 예금 상품을 담을 수 있다.")
        self.assertEqual(audit["critical"], [])

    def test_uncited_annual_rate_is_flagged(self):
        audit = self.audit("수익률은 5%라고 합니다.",
                           "연간 수익률이 5%라고 합니다.")
        self.assertIn("UNSUPPORTED_ANNUAL_SOURCE_UNIT",
                      [x["code"] for x in audit["warnings"]])

    def test_citation_not_neighbor_halo_is_the_evidence(self):
        packet, answer = synthetic_packet("개인연금에서 25만원을 더 받습니다.",
                                          "매월 25만원을 더 받는다.")
        packet["left_context_cues"] = [{"cue_index": 0, "text": "매월 지급합니다."}]
        audit = window_semantic_audit(packet, answer)
        self.assertIn("UNSUPPORTED_MONTHLY_SOURCE_UNIT",
                      [x["code"] for x in audit["warnings"]])
        self.assertFalse(audit["critical"])

    def test_adversarial_source_entailment_blocks_checkpoint_write(self):
        with tempfile.TemporaryDirectory() as root:
            text = "개인연금에서 25만원을 더 받습니다."
            raw = ("1\n00:00:00,000 --> 00:00:02,000\n"+text+"\n").encode()
            session = ConversationResearchSession(
                raw, VID, sha256(raw), str(Path(root)/"private"))
            packet = session.next_packet()
            _, answer = synthetic_packet(text, "연금저축에서 매월 25만원을 더 받는다.")
            answer.update({
                "schema": "IRE_CHAT_WINDOW_ANSWER_V1",
                "session_id": packet["session_id"],
                "window_id": packet["window_id"],
                "packet_sha256": packet["packet_sha256"]})
            self.assertEqual({"UNSUPPORTED_MONTHLY_SOURCE_UNIT",
                              "UNSUPPORTED_SPECIFIC_PRODUCT_연금저축"},
                             {e["code"] for e in window_semantic_audit(packet,answer)["critical"]})
            original_path=Path(root)/"original.srt"
            original_path.write_bytes(raw)
            queue=ChatBatchQueue({
                "schema":"IRE_V2_CHAT_BATCH_V1",
                "research_as_of":"2026-11-02",
                "videos":[{
                    "video_id":VID,
                    "original_srt_path":str(original_path),
                    "source_sha256":sha256(raw),
                    "private_chat_sessions_path":str(Path(root)/"private")
                }]
            })
            work=queue.next_work(max_packets=1,max_chars=18000)
            self.assertEqual(work["packets"][0]["packet"]["packet_sha256"],
                             packet["packet_sha256"])
            attempt={
                "schema":"IRE_V3_CHAT_SUBMISSION_V1",
                "batch_sha256":work["batch_sha256"],
                "max_packets":work["max_packets"],
                "max_chars":work["max_chars"],
                "answers":[{"video_id":VID,"submission":answer}],
            }
            with self.assertRaisesRegex(ValueError,
                                        "V3_HIGH_SIGNAL_SEMANTIC_OMISSION_BLOCKED"):
                queue.accept(attempt)
            self.assertEqual(queue.status()["accepted_windows"],0)
            self.assertEqual(list(session.answers.glob("*.json")),[])


class NumberCitationHardeningTests(unittest.TestCase):
    @staticmethod
    def row(value, unit, literal):
        return {"value": str(value), "unit": unit,
                "source_literal": literal}

    def test_amount_cannot_be_substring_of_larger_amount(self):
        with self.assertRaisesRegex(ValueError,"V3_CALC_SOURCE_LITERAL_NOT_CITED"):
            _read_measure(self.row(100, "만원", "100만원"), "1100만원 납부", {"만원"})

    def test_wrong_korean_money_unit_rejected(self):
        with self.assertRaisesRegex(ValueError,"V3_CALC_SOURCE_UNIT_NOT_TRACEABLE"):
            _read_measure(self.row(100, "원", "100만원"), "100만원", {"원"})

    def test_percent_must_be_adjacent_to_cited_number(self):
        with self.assertRaisesRegex(ValueError,"V3_CALC_LITERAL_VALUE_NOT_TRACEABLE"):
            _read_measure(self.row(100, "%", "100만원에서 5%"),
                          "100만원에서 5%", {"%"})

    def test_spaced_money_unit_still_traceable(self):
        self.assertEqual(
            _read_measure(self.row(100, "만원", "100만 원"), "100만 원", {"만원"}),
            (__import__("decimal").Decimal(100),"만원"))

    def test_partial_decimal_amount_cannot_be_cited(self):
        with self.assertRaisesRegex(ValueError,"V3_CALC_SOURCE_LITERAL_NOT_CITED"):
            _read_measure(self.row("0.3","%","0.3%"), "10.3%", {"%"})


class ReceiptRollbackTests(unittest.TestCase):
    # Reuse synthetic fixtures without inheriting and repeating 13 test cases.
    def setUp(self):
        self.fixture=fixtures.V3ScopedEvidenceTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def test_failed_ledger_save_leaves_no_orphan_scope_receipt(self):
        f=self.fixture
        updated, receipt = apply_v3_scope_evidence(
            f.ledger, f.knowledge, f.document, f.review())
        folder = f.root / "two_file_roll_back"
        with patch("ire.v3_evidence.save_private_evidence",
                   side_effect=OSError("synthetic disk failure")):
            with self.assertRaisesRegex(OSError,"synthetic disk failure"):
                save_scope_evidence_pair(updated, f.knowledge,
                                         receipt, str(folder))
        self.assertEqual(list(folder.glob("*.json")), [])

    def test_0_point_3_percent_is_not_10_point_3_percent(self):
        f=self.fixture
        review=f.review()
        review["global_claim_id"]=f.numeric_claim
        review["scope"]=fixtures.scope_template(
            conditions="UNRESOLVED", effective="UNRESOLVED", numbers="MATCH")
        review["effective_from"]=None
        review["scope_anchors"]={
            "jurisdiction":[],"effective_date":[],"conditions":[],
            "exceptions":[],"numbers":["연간 수수료 10.3%는 예시입니다."]
        }
        page=fixtures.official_doc(fixtures.TEXT.replace(
            "연간 수수료 0.3%는 예시입니다.",
            "연간 수수료 10.3%는 예시입니다."))
        review["document_sha256"]=page["raw_sha256"]
        review["document_text_sha256"]=page["visible_text_sha256"]
        review["source_quote"]="연간 수수료 10.3%는 예시입니다."
        with self.assertRaisesRegex(
                ValueError,"V3_SCOPE_NUMBER_NOT_IN_EXACT_DOCUMENT_ANCHOR"):
            audit_v3_scope(f.knowledge,page,review)

    def test_both_immutable_files_written_after_successful_retry(self):
        f=self.fixture
        updated, receipt = apply_v3_scope_evidence(
            f.ledger, f.knowledge, f.document, f.review())
        folder = f.root / "two_file_success"
        ledger_path, receipt_path = save_scope_evidence_pair(
            updated, f.knowledge, receipt, str(folder))
        self.assertTrue(Path(ledger_path).is_file())
        self.assertTrue(Path(receipt_path).is_file())
        self.assertEqual(len(list(folder.glob("*.json"))),2)
        with self.assertRaises(FileExistsError):
            save_scope_evidence_pair(updated, f.knowledge, receipt, str(folder))
        self.assertEqual(len(list(folder.glob("*.json"))),2)


if __name__ == "__main__":
    unittest.main()