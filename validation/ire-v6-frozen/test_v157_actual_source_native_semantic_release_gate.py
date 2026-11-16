"""V157 public regression tests: private owner original is not embedded."""
from __future__ import annotations
import copy,json,unittest
from pathlib import Path
from v157_actual_source_native_semantic_release_gate import (
    V157EvidenceInvalid,audit_v157_sha_only,
    can_publish_research_or_personal_advice,
)

HERE=Path(__file__).parent


class V157NativeHostReceiptTests(unittest.TestCase):
    def setUp(self):
        self.r=json.loads((HERE/"V157_ACTUAL_V6_CHAT_FIELD_HOST_SHA_ONLY.json").read_text(encoding="utf8"))

    def test_01_native_13_284_and_meaning_hold(self):
        x=audit_v157_sha_only(self.r)
        self.assertEqual(x["native_host_events"],13)
        self.assertEqual(x["candidate_atoms"],284)
        self.assertEqual(x["chat_revised_field_changes"],24)
        self.assertEqual(x["unresolved_cues"],13)
        self.assertFalse(x["p0e_go"])

    def test_02_falsely_approve_v123(self):
        x=copy.deepcopy(self.r);x["latest_real_v123_final_pass"]=13
        with self.assertRaisesRegex(V157EvidenceInvalid,"FALSE_COMPLETION"):
            audit_v157_sha_only(x)

    def test_03_falsely_publish_v128(self):
        x=copy.deepcopy(self.r);x["latest_real_v128_knowledge_published"]=284
        with self.assertRaisesRegex(V157EvidenceInvalid,"FALSE_COMPLETION"):
            audit_v157_sha_only(x)

    def test_04_falsely_certify_finance(self):
        x=copy.deepcopy(self.r);x["finance_ground_truth_certified"]=True
        with self.assertRaisesRegex(V157EvidenceInvalid,"FALSE_FINANCE_APPROVAL"):
            audit_v157_sha_only(x)

    def test_05_falsely_certify_gold_precision(self):
        x=copy.deepcopy(self.r);x["precision_95_recall_98_certified"]=True
        with self.assertRaisesRegex(V157EvidenceInvalid,"FALSE_FINANCE_APPROVAL"):
            audit_v157_sha_only(x)

    def test_06_falsely_certify_zero_high_risk_fn(self):
        x=copy.deepcopy(self.r);x["high_risk_FN_zero_certified"]=True
        with self.assertRaisesRegex(V157EvidenceInvalid,"FALSE_FINANCE_APPROVAL"):
            audit_v157_sha_only(x)

    def test_07_source_sha_tamper_rejected(self):
        x=copy.deepcopy(self.r);x["source_sha256"]="0"*64
        with self.assertRaisesRegex(V157EvidenceInvalid,"OWNER_SOURCE_SHA"):
            audit_v157_sha_only(x)

    def test_08_event_digest_scope_missing_rejected(self):
        x=copy.deepcopy(self.r);x["host_event_sha256_by_scope"].pop("B0013")
        with self.assertRaisesRegex(V157EvidenceInvalid,"SOURCE_SCOPE_CENSUS"):
            audit_v157_sha_only(x)

    def test_09_duplicate_event_hash_rejected(self):
        x=copy.deepcopy(self.r)
        x["host_event_sha256_by_scope"]["B0002"]=x["host_event_sha256_by_scope"]["B0001"]
        with self.assertRaisesRegex(V157EvidenceInvalid,"NATIVE_EVENT_DIGEST_CENSUS"):
            audit_v157_sha_only(x)

    def test_10_host_does_not_auto_approve_advice(self):
        x=can_publish_research_or_personal_advice(self.r)
        self.assertTrue(x["native_host_commit_confirmed"])
        self.assertFalse(x["research_candidate_export_allowed"])
        self.assertFalse(x["v128_atomic_parent_knowledge_publish_allowed"])
        self.assertFalse(x["personal_advice_approved"])

    def test_11_false_0_unresolved_cues_rejected(self):
        x=copy.deepcopy(self.r);x["source_cue_unresolved_after_review"]=0
        with self.assertRaisesRegex(V157EvidenceInvalid,"FALSE_COMPLETION"):
            audit_v157_sha_only(x)

    def test_12_false_all_speakers_known_rejected(self):
        x=copy.deepcopy(self.r);x["speaker_unknown_atoms_after_edit"]=0
        with self.assertRaisesRegex(V157EvidenceInvalid,"FALSE_COMPLETION"):
            audit_v157_sha_only(x)


if __name__=="__main__":
    unittest.main()
