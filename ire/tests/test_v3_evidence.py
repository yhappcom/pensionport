"""V3 evidence scope/date/numeric anchor guards — synthetic documents only."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from ire.evidence import independently_fetch_candidate
from ire.knowledge import empty_knowledge, ingest_new_video
from ire.v2_evidence import empty_evidence_ledger, validate_evidence_ledger
from ire.v3_evidence import (
    audit_v3_scope, apply_v3_scope_evidence, save_v3_scope_receipt)
from test_engine import VID, synthetic_srt
from test_knowledge import make_report

URL = "https://www.bok.or.kr/portal/v3-scope-synthetic-fixture"
TEXT = (
    "시험용 가상 자료입니다. 실제 금융기관 공시가 아닙니다. "
    "2026년 1월 1일부터 적용한다는 가상의 조건을 설명합니다. "
    "가상의 상품 A는 계약 조건에 따라 매년 비용이 달라질 수 있습니다. "
    "단, 연간 수수료 0.3%는 예시입니다. "
    "이 가상 규칙의 법적 효력은 확인되지 않았습니다."
)


def official_doc(body=TEXT):
    def reader(url):
        return body.encode("utf-8"), "text/plain; charset=utf-8", url
    return independently_fetch_candidate(
        URL, read_fn=reader, fetched_at="2026-11-02T00:00:00Z")


def scope_template(conditions="MATCH", effective="MATCH",
                   numbers="NOT_SPECIFIED"):
    return {
        "jurisdiction": "UNRESOLVED",
        "effective_date": effective,
        "conditions": conditions,
        "exceptions": "UNRESOLVED",
        "numbers": numbers,
    }


class V3ScopedEvidenceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        raw, _ = synthetic_srt()
        report = make_report(raw, VID, self.root / "source")
        self.knowledge = ingest_new_video(empty_knowledge(), raw, report)
        self.ledger = empty_evidence_ledger(self.knowledge)
        self.document = official_doc()
        self.claim = self.knowledge["claims"][0]["global_claim_id"]
        self.numeric_claim = self.knowledge["claims"][1]["global_claim_id"]

    def review(self):
        return {
            "schema": "IRE_CHAT_EVIDENCE_REVIEW_V3",
            "global_claim_id": self.claim,
            "document_url": self.document["canonical_url"],
            "document_sha256": self.document["raw_sha256"],
            "document_text_sha256": self.document["visible_text_sha256"],
            "source_quote": "가상의 상품 A는 계약 조건에 따라 매년 비용이 달라질 수 있습니다.",
            "verdict": "CONDITIONALLY_SUPPORTS",
            "scope": scope_template(),
            "scope_anchors": {
                "jurisdiction": [],
                "effective_date": ["2026년 1월 1일부터 적용한다는 가상의 조건을 설명합니다."],
                "conditions": ["가상의 상품 A는 계약 조건에 따라 매년 비용이 달라질 수 있습니다."],
                "exceptions": [],
                "numbers": [],
            },
            "effective_from": "2026-01-01",
            "effective_until": None,
            "chat_reviewer_mode": "CURRENT_CHATGPT_CONVERSATION",
        }

    def test_scope_anchors_create_unapproved_receipt_and_v2_event(self):
        record, receipt = apply_v3_scope_evidence(
            self.ledger, self.knowledge, self.document, self.review())
        validate_evidence_ledger(record, self.knowledge)
        self.assertEqual(len(record["assessments"]), 1)
        self.assertEqual(record["assessments"][0]["finance_truth_approved"], False)
        self.assertFalse(receipt["scope_semantic_truth_verified"])
        self.assertFalse(receipt["statutory_effect_verified"])
        self.assertEqual(receipt["approved_financial_facts"], 0)
        self.assertFalse(receipt["actual_network_fetch"])
        path = Path(save_v3_scope_receipt(receipt, str(self.root/"receipts")))
        self.assertTrue(path.exists())
        self.assertEqual(path.stat().st_mode & 0o077, 0)
        loaded = json.loads(path.read_text())
        self.assertEqual(loaded["receipt_sha256"], receipt["receipt_sha256"])
        with self.assertRaises(FileExistsError):
            save_v3_scope_receipt(receipt, str(self.root/"receipts"))

    def test_unquoted_positive_scope_refused(self):
        review = self.review()
        review["scope_anchors"]["conditions"] = []
        with self.assertRaisesRegex(ValueError, "V3_SCOPE_POSITIVE_WITHOUT_ANCHOR"):
            audit_v3_scope(self.knowledge, self.document, review)

    def test_forged_scope_anchor_refused(self):
        review = self.review()
        review["scope_anchors"]["conditions"] = [
            "해당 상품의 모든 투자자는 연 9%의 수익을 보장받습니다"]
        with self.assertRaisesRegex(ValueError, "V3_SCOPE_ANCHOR_NOT_IN_DOCUMENT"):
            audit_v3_scope(self.knowledge, self.document, review)

    def test_scope_unresolved_cannot_claim_positive_anchor(self):
        review = self.review()
        review["scope"]["conditions"] = "UNRESOLVED"
        with self.assertRaisesRegex(ValueError,
                                    "V3_SCOPE_UNRESOLVED_HAS_UNJUSTIFIED_ANCHOR"):
            audit_v3_scope(self.knowledge, self.document, review)

    def test_date_scope_must_match_document_boundary(self):
        review = self.review()
        review["effective_from"] = "2025-01-01"
        with self.assertRaisesRegex(ValueError,
                                    "V3_SCOPE_EFFECTIVE_BOUNDARY_NOT_IN_DOCUMENT"):
            audit_v3_scope(self.knowledge, self.document, review)

    def test_unknown_effective_date_cannot_be_declared_exact(self):
        review = self.review()
        review["scope"]["effective_date"] = "UNRESOLVED"
        review["scope_anchors"]["effective_date"] = []
        with self.assertRaisesRegex(ValueError, "V3_SCOPE_UNANCHORED_EFFECTIVE_RANGE"):
            audit_v3_scope(self.knowledge, self.document, review)

    def test_numeric_anchor_must_reproduce_claim_measurement(self):
        review = self.review()
        review["global_claim_id"] = self.numeric_claim
        review["source_quote"] = "연간 수수료 0.3%는 예시입니다."
        review["scope"] = scope_template(
            conditions="UNRESOLVED", effective="UNRESOLVED",
            numbers="MATCH")
        review["scope_anchors"] = {
            "jurisdiction": [], "effective_date": [],
            "conditions": [], "exceptions": [],
            "numbers": ["연간 수수료 0.3%는 예시입니다."]
        }
        review["effective_from"] = None
        audit = audit_v3_scope(self.knowledge, self.document, review)
        self.assertEqual(audit["scope_proposals"]["numbers"], "MATCH")
        bad = copy.deepcopy(review)
        bad["scope_anchors"]["numbers"] = ["연간 수수료 0.9%는 예시입니다."]
        alternate = official_doc(
            TEXT.replace("연간 수수료 0.3%는 예시입니다.",
                         "연간 수수료 0.9%는 예시입니다."))
        bad["document_sha256"] = alternate["raw_sha256"]
        bad["document_text_sha256"] = alternate["visible_text_sha256"]
        bad["source_quote"] = "연간 수수료 0.9%는 예시입니다."
        with self.assertRaisesRegex(
                ValueError, "V3_SCOPE_NUMBER_NOT_IN_EXACT_DOCUMENT_ANCHOR"):
            audit_v3_scope(self.knowledge, alternate, bad)

    def test_document_visible_hash_tampering_rejected(self):
        doc = copy.deepcopy(self.document)
        doc["visible_text"] += " 변경"
        with self.assertRaisesRegex(ValueError, "V3_SCOPE_DOCUMENT_PROVENANCE_INVALID"):
            audit_v3_scope(self.knowledge, doc, self.review())

    def test_false_claim_jurisdiction_is_blocked(self):
        review = self.review()
        review["scope"]["jurisdiction"] = "MATCH"
        review["scope_anchors"]["jurisdiction"] = [
            "가상의 상품 A는 계약 조건에 따라 매년 비용이 달라질 수 있습니다."]
        with self.assertRaisesRegex(ValueError,
                                    "V3_SCOPE_NO_CLAIM_JURISDICTION"):
            audit_v3_scope(self.knowledge, self.document, review)

    def test_without_exception_in_claim_cannot_assert_scope_match(self):
        review = self.review()
        review["scope"]["exceptions"] = "MATCH"
        review["scope_anchors"]["exceptions"] = [
            "이 가상 규칙의 법적 효력은 확인되지 않았습니다."]
        with self.assertRaisesRegex(ValueError, "V3_SCOPE_NO_CLAIM_EXCEPTIONS"):
            audit_v3_scope(self.knowledge, self.document, review)

    def test_unregistered_claim_is_rejected(self):
        review = self.review()
        review["global_claim_id"] = "K" + "f"*24
        with self.assertRaisesRegex(ValueError, "V3_SCOPE_UNREGISTERED_CLAIM"):
            audit_v3_scope(self.knowledge, self.document, review)

    def test_injected_source_is_explicitly_not_real_independent_official(self):
        _, receipt = apply_v3_scope_evidence(
            self.ledger, self.knowledge, self.document, self.review())
        self.assertFalse(receipt["actual_network_fetch"])
        self.assertFalse(receipt["independent_human_review"])
        self.assertEqual(receipt["approved_financial_facts"], 0)


if __name__ == "__main__":
    unittest.main()
