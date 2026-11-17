"""V159 public SHA-only negative tests, no original owner research content."""
from __future__ import annotations
import copy,json,unittest
from pathlib import Path
from v159_source_first_v123_release_guard import (
 V159EvidenceNotReady,audit_v159_public_source_first,
 research_release_or_personal_advice_allowed,
)
ROOT=Path(__file__).parent


class V159SourceFirstEvidenceGuardTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads((ROOT/"V159_V123_286_SOURCE_FIRST_PARTIAL_SHA_ONLY.json").read_text())

    def test_01_actual_private_source_first_partial_HOLD(self):
        status=audit_v159_public_source_first(self.data)
        self.assertEqual(status["provisional_atom_count"],286)
        self.assertEqual(status["ChatGPT_source_first_atoms_individually_adjudicated"],81)
        self.assertEqual(status["candidate_row_accepted_educational_not_finally_released"],18)
        self.assertEqual(status["candidate_rows_still_open"],268)
        self.assertEqual(status["V123_final_scope_PASSES"],0)
        self.assertEqual(status["V128_approved_parent_knowledge_publications"],0)
        self.assertFalse(status["P0E_GO"])

    def test_02_recovered_atoms_cannot_disappear(self):
        x=copy.deepcopy(self.data);x["new_candidate_atoms"]=284
        with self.assertRaises(V159EvidenceNotReady):audit_v159_public_source_first(x)

    def test_03_not_all_cues_have_new_chat_source_first_verdict(self):
        x=copy.deepcopy(self.data);x["source_cues_not_yet_source_first_checked"]=0
        with self.assertRaises(V159EvidenceNotReady):audit_v159_public_source_first(x)

    def test_04_no_fake_13_scope_v123_approval(self):
        x=copy.deepcopy(self.data);x["V123_13_scope_final_approved"]=13
        with self.assertRaises(V159EvidenceNotReady):audit_v159_public_source_first(x)

    def test_05_18_partial_rows_not_final_13_scope_approvals(self):
        release=research_release_or_personal_advice_allowed(self.data)
        self.assertTrue(release["v6_native_host_structurally_ready"])
        self.assertFalse(release["full_video_V123_research_release_approved"])
        self.assertFalse(release["V128_atomic_knowledge_publish_allowed"])
        self.assertFalse(release["personalized_advice_approved"])

    def test_06_no_fake_v128_knowledge_publication(self):
        x=copy.deepcopy(self.data);x["V128_parent_publications"]=286
        with self.assertRaises(V159EvidenceNotReady):audit_v159_public_source_first(x)

    def test_07_false_precision_95_certificate_rejected(self):
        x=copy.deepcopy(self.data);x["precision_95_certified"]=True
        with self.assertRaises(V159EvidenceNotReady):audit_v159_public_source_first(x)

    def test_08_false_recall_98_certificate_rejected(self):
        x=copy.deepcopy(self.data);x["recall_98_certified"]=True
        with self.assertRaises(V159EvidenceNotReady):audit_v159_public_source_first(x)

    def test_09_false_zero_high_risk_FN_certificate_rejected(self):
        x=copy.deepcopy(self.data);x["high_risk_false_negatives_zero_certified"]=True
        with self.assertRaises(V159EvidenceNotReady):audit_v159_public_source_first(x)

    def test_10_source_sha_tamper_rejected(self):
        x=copy.deepcopy(self.data);x["original_source_sha256"]="f"*64
        with self.assertRaises(V159EvidenceNotReady):audit_v159_public_source_first(x)

    def test_11_event_sha_duplicate_rejected(self):
        x=copy.deepcopy(self.data)
        x["host_event_sha256_by_scope"]["B0013"]=x["host_event_sha256_by_scope"]["B0012"]
        with self.assertRaises(V159EvidenceNotReady):audit_v159_public_source_first(x)

    def test_12_private_packet_sha_missing_rejected(self):
        x=copy.deepcopy(self.data);x["owner_private_packet_sha256"]="bad"
        with self.assertRaises(V159EvidenceNotReady):audit_v159_public_source_first(x)

    def test_13_unchallenged_current_financial_suitability_rejected(self):
        x=copy.deepcopy(self.data);x["current_primary_law_and_personal_suitability_certified"]=True
        with self.assertRaises(V159EvidenceNotReady):audit_v159_public_source_first(x)

    def test_14_audited_and_unreviewed_atom_counts_must_match(self):
        x=copy.deepcopy(self.data);x["V123_atom_rows_open"]=0
        with self.assertRaises(V159EvidenceNotReady):audit_v159_public_source_first(x)

    def test_15_audio_unverified_source_count_must_be_preserved(self):
        x=copy.deepcopy(self.data);x["original_audio_or_primary_source_unverified_cues"]=0
        with self.assertRaises(V159EvidenceNotReady):audit_v159_public_source_first(x)


if __name__=="__main__":
    unittest.main()
