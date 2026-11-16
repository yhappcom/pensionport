"""V153 public negative controls. Private original is never included in CI."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from v153_source_first_owner_recheck import (
    V153SourceReviewError, audit_public_sha_only,
    private_owner_source_recheck,
)

PUBLIC = Path(__file__).with_name("V153_SOURCE_FIRST_SEMANTIC_202_SHA_ONLY.json")


class V153SourceFirstTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(PUBLIC.read_text(encoding="utf-8"))

    def test_01_actual_manifest_still_hold(self):
        result = audit_public_sha_only(self.data)
        self.assertEqual(result["source_first_chat_pending_claim_notes"], 202)
        self.assertEqual(result["private_unresolved_cue_recheck"], 108)
        self.assertEqual(result["v123_scopes_approved"], 0)
        self.assertEqual(result["v128_published"], 0)
        self.assertFalse(result["gold_precision_or_recall_measured"])
        self.assertFalse(result["p0e_go"])

    def test_02_fake_full_gold_is_blocked(self):
        x=copy.deepcopy(self.data)
        x["full_atomic_precision_recall_certified"]=True
        with self.assertRaisesRegex(V153SourceReviewError,"FALSE_APPROVAL"):
            audit_public_sha_only(x)

    def test_03_fake_no_high_risk_FN_is_blocked(self):
        x=copy.deepcopy(self.data)
        x["high_risk_false_negative_zero_certified"]=True
        with self.assertRaisesRegex(V153SourceReviewError,"FALSE_APPROVAL"):
            audit_public_sha_only(x)

    def test_04_fake_v123_final_is_blocked(self):
        x=copy.deepcopy(self.data)
        x["v123_chat_final_approved_scopes"]=13
        with self.assertRaisesRegex(V153SourceReviewError,"FALSE_COUNT"):
            audit_public_sha_only(x)

    def test_05_fake_v128_publishing_is_blocked(self):
        x=copy.deepcopy(self.data)
        x["v128_parent_published"]=276
        with self.assertRaisesRegex(V153SourceReviewError,"FALSE_COUNT"):
            audit_public_sha_only(x)

    def test_06_relabel_unresolved_108_is_blocked(self):
        x=copy.deepcopy(self.data)
        x["remaining_unresolved_cue_V6_dispositions"]=0
        with self.assertRaisesRegex(V153SourceReviewError,"FALSE_COUNT"):
            audit_public_sha_only(x)

    def test_07_wrong_original_source_rejected(self):
        x=copy.deepcopy(self.data)
        x["original_source_sha256"]="0"*64
        with self.assertRaisesRegex(V153SourceReviewError,"SOURCE"):
            audit_public_sha_only(x)

    def test_08_truncated_private_sha_rejected(self):
        x=copy.deepcopy(self.data)
        x["private_160_notes_sha256"]="fff"
        with self.assertRaisesRegex(V153SourceReviewError,"PRIVATE_DIGEST"):
            audit_public_sha_only(x)

    def test_09_raw_owner_srt_required_not_fabricated(self):
        with self.assertRaisesRegex(V153SourceReviewError,
                                    "REAL_RAW_SRT_HASH_REQUIRED"):
            private_owner_source_recheck(self.data, b"1\n00:00:00,000 --> 00:00:00,300\nsynthetic\n",
                {},{}, {}, [], [], [])

    def test_10_cannot_claim_personal_advice_completed(self):
        x=copy.deepcopy(self.data)
        x["approved_video_knowledge_based_advice_tested"]=True
        with self.assertRaisesRegex(V153SourceReviewError,"FALSE_APPROVAL"):
            audit_public_sha_only(x)


if __name__ == "__main__":
    unittest.main()
