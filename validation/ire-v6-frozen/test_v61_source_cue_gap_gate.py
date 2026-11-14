"""Synthetic-only V61 gap custody tests; no original owner speech."""
import copy
import importlib.util
import unittest
from pathlib import Path

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from ire.v6.host_semantic_custody_v39 import _v33_draft_registry
from ire.v6.source import parse_srt

_path = Path(__file__).with_name("v61_source_cue_gap_gate.py")
_spec = importlib.util.spec_from_file_location("v61_source_cue_gap_gate", _path)
_gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_gate)
audit_cue_coverage_v61 = _gate.audit_cue_coverage_v61


class TestV61CueCoverage(unittest.TestCase):
    def setUp(self):
        self.vid = "FAKEVID111A"
        self.raw = (
            "1\n00:00:00,000 --> 00:00:01,000\n"
            "분산투자는 손실 위험을 줄일 수도 있습니다.\n\n"
            "2\n00:00:01,000 --> 00:00:01,500\n"
            "네.\n\n"
            "3\n00:00:01,500 --> 00:00:02,000\n"
            "금리 변화에 따라 채권 가격은 떨어질 수도 있습니다.\n"
        ).encode("utf-8")
        cues = parse_srt(self.raw)
        self.source = {self.vid: self.raw}
        self.pins = [{
            "video_id": self.vid, "original_srt_sha256": sha256(self.raw),
            "cue_count": len(cues),
        }]
        registry = _v33_draft_registry(cues)
        assigned = {
            i for proposals in registry.values() for row in proposals
            for i in row["cue_indices"]
        }
        self.gaps = [i for i in range(1, len(cues) + 1) if i not in assigned]
        self.reviews = [{
            "video_id": self.vid, "cue_index": i,
            "original_cue_text_sha256": sha256(cues[i - 1].text.encode("utf-8")),
            "status": "BACKCHANNEL_CONTEXT",
            "neighbor_cue_indices": [i - 1 if i > 1 else i + 1],
            "context_reason": "가상의 짧은 확인 응답이며 독립적 금융 주장은 아님",
            "source_audio_verified": False, "independent_gold": False,
        } for i in self.gaps]

    def test_success_is_only_structural(self):
        actual = audit_cue_coverage_v61(self.source, self.pins, self.reviews)
        self.assertEqual(actual["totals"]["source_cues"], 3)
        self.assertEqual(actual["totals"]["cues_not_referenced_by_v33"],
                         len(self.gaps))
        self.assertFalse(actual["cue_gap_review_proves_no_missing_atomic_claims"])
        self.assertFalse(actual["p0_go"])

    def reject(self, *, source=None, pins=None, reviews=None):
        with self.assertRaises(InvalidInput):
            audit_cue_coverage_v61(
                source if source is not None else self.source,
                pins if pins is not None else self.pins,
                reviews if reviews is not None else self.reviews,
            )

    def test_negative_controls_fail_closed(self):
        if not self.reviews:
            self.skipTest("No source omission in synthetic sample")
        self.reject(reviews=[])
        self.reject(reviews=self.reviews + self.reviews)
        row = copy.deepcopy(self.reviews)
        row[0]["original_cue_text_sha256"] = "0" * 64
        self.reject(reviews=row)
        row = copy.deepcopy(self.reviews)
        row[0]["source_audio_verified"] = True
        self.reject(reviews=row)
        row = copy.deepcopy(self.reviews)
        row[0]["independent_gold"] = True
        self.reject(reviews=row)
        row = copy.deepcopy(self.reviews)
        row[0]["neighbor_cue_indices"] = [999]
        self.reject(reviews=row)
        row = copy.deepcopy(self.reviews)
        row[0]["context_reason"] = "x"
        self.reject(reviews=row)
        row = copy.deepcopy(self.reviews)
        row[0]["status"] = "APPROVED_ATOMIC_TRUTH"
        self.reject(reviews=row)
        pins = copy.deepcopy(self.pins)
        pins[0]["original_srt_sha256"] = "f" * 64
        self.reject(pins=pins)
        pins = copy.deepcopy(self.pins)
        pins[0]["cue_count"] = 300
        self.reject(pins=pins)
        self.reject(source={self.vid: b"source changed"})


if __name__ == "__main__":
    unittest.main()
