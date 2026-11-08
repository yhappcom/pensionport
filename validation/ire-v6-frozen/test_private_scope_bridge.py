"""Hash-bridge from ChatGPT PRIVATE real-SRT execution to reproducible GitHub-only anchors.

This test never sees SRT text; it verifies private run's public HASH REPORT references
against GitHub's real canonical master116 and first-party archived official bytes.
The report is not independent evidence that the private replay ran correctly.
"""
import hashlib
import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = Path(__file__).with_name("REAL_PRIVATE_SCOPE_E2E_ATTESTATION_V1.json")

class PrivateRealSourceHashBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_real_source_identity_but_no_private_payload(self):
        e=self.data
        self.assertEqual(e["original_srt_sha256"],
                         "2de4b318c75c96421f446a462ecaeacef2a931fbda5bd4c7b35236dcb3fe9a0f")
        self.assertEqual(e["full_video_cue_count"],1195)
        self.assertEqual(e["full_video_historical_windows"],67)
        self.assertTrue(e["source_media_private"])
        self.assertTrue(e["all_private_source_content_retained_outside_github"])
        self.assertNotIn("source_refs",EVIDENCE.read_text(encoding="utf-8"))
        self.assertNotIn("srt_transcript",EVIDENCE.read_text(encoding="utf-8"))

    def test_first_party_actual_bytes_sha256_against_archived_repo(self):
        e=self.data
        raw=Path(e["official_public_law_path"]).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),e["official_original_sha256"])
        self.assertEqual(e["official_visible_effective_from"],"2026-10-01")
        self.assertFalse(e["official_fact_approved"])

    def test_all_116_protected_claims_from_original_repository(self):
        e=self.data
        output=subprocess.check_output(["git","hash-object",e["master116_original_path"]],text=True).strip()
        self.assertEqual(output,e["master116_git_blob_sha"])
        rows=[json.loads(s) for s in Path(e["master116_original_path"]).read_text(encoding="utf-8").splitlines() if s.strip()]
        self.assertEqual(len(rows),116)
        self.assertEqual(len({x["claim_id"] for x in rows}),116)
        self.assertTrue(any(x["claim_id"]==e["legacy_candidate_relation_id"] for x in rows))
        self.assertFalse(any("sz5N9WJS310" in x["supporting_videos"] for x in rows))
        self.assertEqual(e["baseline_approved_direct_source_links"],0)
        self.assertEqual(e["legacy_candidate_relation_kind"],"OPEN")
        self.assertFalse(e["external_independent_prior_relation_verified"])

    def test_four_windows_six_real_atomic_candidates_and_five_attacks(self):
        r=self.data["private_real_replay"]
        self.assertEqual(r["windows_structurally_modelled"],4)
        self.assertEqual(r["actual_source_atom_count"],6)
        self.assertEqual(r["source_question_roles_preserved"],3)
        self.assertEqual(r["verified_current_structural_proofs"],4)
        self.assertEqual(r["malicious_finance_input_classes_rejected"],5)
        self.assertEqual(r["outcome"],"TERMINAL_BLOCKED")
        self.assertFalse(r["independent_finance_entailment_verified"])

    def test_one_complete_real_historical_window_has_only_outside_blockers(self):
        r=self.data["historical_single_window_full_chain"]
        self.assertEqual(r["original_window_id"],"W00037")
        self.assertEqual((r["first_cue"],r["last_cue"]),(638,655))
        self.assertEqual(r["model_scope"],"PARTIAL")
        self.assertEqual(r["fully_modelled_source_window_count"],1)
        self.assertEqual(r["unmodelled_rest_of_full_video_windows"],66)
        self.assertTrue(all(r[k] for k in (
            "proof_replayed","finance_candidate_replayed",
            "source_in_current_window_complete","master116_relation_replayed",
            "official_original_law_bytes_replayed",
            "current_ledger_audit_reloaded_after_restart")))
        self.assertEqual(r["missing_model_or_proof_or_finance_candidate_blockers"],0)
        self.assertEqual(set(r["remaining_blockers"]),{
            "FINANCIAL_ENTAILMENT_NOT_VERIFIED",
            "GOLD_REVIEWER_INDEPENDENCE_NOT_VERIFIED",
            "INDEPENDENT_GOLDSET_MEASUREMENT_NOT_CURRENT",
            "OWNER_IDENTITY_NOT_INDEPENDENTLY_VERIFIED"})
        self.assertEqual(r["outcome"],"TERMINAL_BLOCKED")
        self.assertFalse(r["engine_p0_go"])

    def test_chatgpt_private_reports_hash_pinned_but_not_github_reexecuted(self):
        for key in ("private_real_replay","historical_single_window_full_chain"):
            doc=self.data[key]
            self.assertRegex(doc["chat_private_report_sha256"],r"^[0-9a-f]{64}$")
            self.assertRegex(doc["private_sqlite_receipt_event_sha256"],r"^[0-9a-f]{64}$")
        self.assertTrue(self.data["github_ci_verifies_only_hash_references_and_provenance_not_private_srt_replay"])
        self.assertFalse(self.data["engine_quality_certified"])
        self.assertFalse(self.data["p0_go"])
        self.assertEqual(self.data["independent_precision_recall"],"UNMEASURABLE")

if __name__=="__main__":
    unittest.main()
