"""V158 SHA-only negative controls. All original private SRT stays off Actions."""
from __future__ import annotations
import copy,json,unittest
from pathlib import Path
from v158_source_meaning_release_gate import (
    V158ReleaseEvidenceError,audit_v158_public_receipt,research_release_allowed,
)
HERE=Path(__file__).parent

class V158PublicHostAccuracyGuardTests(unittest.TestCase):
    def setUp(self):
        self.r=json.loads((HERE/"V158_REAL_CHATGPT_STANCE_129_SOURCE_HOST_SHA_ONLY.json").read_text())

    def test_01_actual_host_pins_and_no_fake_research_approval(self):
        p=audit_v158_public_receipt(self.r)
        self.assertEqual(p["real_native_v6_event_heads"],13)
        self.assertEqual(p["explicit_chat_source_first_changes"],129)
        self.assertEqual(p["remaining_unresolved_stances"],77)
        self.assertEqual(p["V123_final_pass_scopes"],0)
        self.assertFalse(p["p0e_go"])

    def test_02_host_commit_not_finance_quality_certification(self):
        p=research_release_allowed(self.r)
        self.assertTrue(p["native_v6_structural_ledger_ready"])
        self.assertFalse(p["V123_release_approved"])
        self.assertFalse(p["V128_knowledge_publish_allowed"])
        self.assertFalse(p["personalized_advice_authorized"])

    def test_03_false_v123_approval_rejected(self):
        x=copy.deepcopy(self.r);x["actual_v123_chat_pass_scopes"]=13
        with self.assertRaises(V158ReleaseEvidenceError):audit_v158_public_receipt(x)

    def test_04_false_v128_commit_rejected(self):
        x=copy.deepcopy(self.r);x["actual_v128_parent_publication_count"]=284
        with self.assertRaises(V158ReleaseEvidenceError):audit_v158_public_receipt(x)

    def test_05_false_95_percent_precision_rejected(self):
        x=copy.deepcopy(self.r);x["current_precision_95_certified"]=True
        with self.assertRaises(V158ReleaseEvidenceError):audit_v158_public_receipt(x)

    def test_06_false_98_percent_recall_rejected(self):
        x=copy.deepcopy(self.r);x["current_recall_98_certified"]=True
        with self.assertRaises(V158ReleaseEvidenceError):audit_v158_public_receipt(x)

    def test_07_zero_high_risk_fn_claim_rejected(self):
        x=copy.deepcopy(self.r);x["zero_high_risk_FN_certified"]=True
        with self.assertRaises(V158ReleaseEvidenceError):audit_v158_public_receipt(x)

    def test_08_wrong_source_sha_rejected(self):
        x=copy.deepcopy(self.r);x["original_source_sha256"]="0"*64
        with self.assertRaises(V158ReleaseEvidenceError):audit_v158_public_receipt(x)

    def test_09_duplicate_host_event_head_rejected(self):
        x=copy.deepcopy(self.r)
        x["host_event_sha256_by_scope"]["B0013"]=x["host_event_sha256_by_scope"]["B0012"]
        with self.assertRaises(V158ReleaseEvidenceError):audit_v158_public_receipt(x)

    def test_10_missing_scope_head_rejected(self):
        x=copy.deepcopy(self.r);del x["host_event_sha256_by_scope"]["B0001"]
        with self.assertRaises(V158ReleaseEvidenceError):audit_v158_public_receipt(x)

    def test_11_wrong_stance_reduction_rejected(self):
        x=copy.deepcopy(self.r);x["unresolved_stances_after_patch"]=76
        with self.assertRaises(V158ReleaseEvidenceError):audit_v158_public_receipt(x)

    def test_12_audio_cue_not_cleared_by_fiat(self):
        x=copy.deepcopy(self.r);x["unresolved_original_audio_cues"]=0
        with self.assertRaises(V158ReleaseEvidenceError):audit_v158_public_receipt(x)
