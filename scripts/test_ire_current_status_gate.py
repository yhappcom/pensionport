"""Negative/positive tests for scope-safe E1-E5 canonical status. Not a financial fact audit."""
from __future__ import annotations

import copy
import unittest

from scripts.ire_current_status_gate import ROOT, LEDGER, load, validate


class CanonicalStatusGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.good = load(ROOT / LEDGER)

    def setUp(self):
        self.ledger = copy.deepcopy(self.good)

    def bad(self, code: str):
        errors = validate(self.ledger, root=None)
        self.assertTrue(any(code in error for error in errors), errors)

    def test_unmodified_ledger_and_live_pinned_evidence(self):
        self.assertEqual([], validate(self.ledger, root=ROOT))

    def test_all_five_stages_are_individually_scoped(self):
        self.assertEqual(["E1", "E2", "E3", "E4", "E5"], list(self.ledger["stages"]))
        self.assertEqual([], validate(self.ledger, root=None))

    def test_e1_synthetic_must_not_promote_to_real(self):
        self.ledger["stages"]["E1"]["end_to_end_real_owner_approval_route"]["status"] = "PASS"
        self.bad("E1_E2E5_REAL_FALSE_GO")

    def test_e1_actual_child_provisional_cannot_disappear(self):
        self.ledger["reference_cohort"]["parent_external_qualifier_provisional_child_hosts"] = 0
        self.bad("ETF_B0013_PROVISIONAL_LOST")

    def test_e1_missing_cross_parent_qualifier_rejected(self):
        self.ledger["reference_cohort"]["cross_parent_qualifier_edges"] = 0
        self.bad("ETF_QUALIFIER_EDGES_LOST")

    def test_etf_source_cue_count_not_legacy_count(self):
        self.ledger["reference_cohort"]["cue_count"] = 1481
        self.bad("ETF_CUE_COUNT_MISREPRESENTED")

    def test_etf_registered_candidate_atoms_not_certified(self):
        self.ledger["reference_cohort"]["provisional_atom_candidates"] = 116
        self.bad("ETF_ATOM_CANDIDATES_MISREPRESENTED")

    def test_real_etf_formal_approval_must_not_be_invented(self):
        self.ledger["reference_cohort"]["actual_formal_v123_child_approvals"] = 13
        self.bad("ETFTURN_FINAL_APPROVAL_OR_PUBLICATION_FALSE_GO")

    def test_real_etf_e5_publication_must_not_be_invented(self):
        self.ledger["stages"]["E5"]["actual_etf_parent_publications"] = 1
        self.bad("E5_FALSE_PUBLICATION")

    def test_independent_accuracy_must_be_null(self):
        self.ledger["stages"]["E2"]["independently_certified_recall"] = 0.98
        self.bad("UNKNOWN_ACCURACY_REPLACED_WITH_NUMBER")

    def test_etf_accuracy_not_copied_from_other_original(self):
        self.ledger["accuracy_and_context"]["etf_source_first_gold"]["precision"] = 0.8
        self.bad("ETF_ACCURACY_FAKE_NUMBER")

    def test_unrelated_historical_cma_turn2_not_etf_proof(self):
        self.ledger["reference_cohort"]["actual_user_etf_turn2_final_verdict_proven"] = True
        self.bad("ETFTURN2_FALSELY_CLAIMED")

    def test_roster_shorts_cannot_be_added_twice(self):
        self.ledger["video_denominators"]["canonical_roster"]["total"] = 879
        self.bad("ROSTER_COUNTS_INCONSISTENT")

    def test_legacy_video_rows_not_roster_e5(self):
        self.ledger["video_denominators"]["certified_e5_research_published_videos_total"] = 157
        self.bad("UNKNOWN_ALL_ROSTER_APPROVAL_COUNT_FILLED")

    def test_legacy_claims_not_e5_publications(self):
        self.ledger["video_denominators"]["legacy_records"]["denominator_kind"] = "E5_APPROVED"
        self.bad("LEGACY_RECORD_AS_E5")

    def test_advisory_personalized_auto_approval_blocked(self):
        self.ledger["advisory"]["personalized_recommendation_authorized"] = True
        self.bad("ADVISORY_SCOPE_FALSE_GO")

    def test_v149_internal_not_an_independent_gold(self):
        self.ledger["accuracy_and_context"]["historical_v149_internal_other_original"]["independently_certified"] = True
        self.bad("OTHER_SCOPE_P_R_LAUNDERED")

    def test_source_provenance_cannot_claim_private_replay(self):
        self.ledger["reference_cohort"]["original_private_srt_bytes_verified_in_this_turn"] = True
        self.bad("PRIVATE_SRT_REPLAY_FALSELY_CLAIMED")

    def test_evidence_key_missing(self):
        self.ledger["stages"]["E3"]["evidence_keys"] = ["missing.json"]
        self.bad("UNRESOLVED_STAGE_EVIDENCE")

    def test_sourced_evidence_git_blob_mutation_caught(self):
        path = "data/inventory_control.json"
        self.ledger["evidence_sources"][path]["git_blob_sha"] = "0" * 40
        self.bad_with_root("EVIDENCE_BLOB_CHANGED")

    def bad_with_root(self, code: str):
        errors = validate(self.ledger, root=ROOT)
        self.assertTrue(any(code in error for error in errors), errors)

    def test_e4_owner_authorization_must_not_be_invented(self):
        self.ledger["stages"]["E4"]["actual_etf_owner_seal_verified"] = True
        self.bad("E4_FALSE_SEAL")

    def test_corpus_release_forbidden_without_e2_e5(self):
        self.ledger["accuracy_and_context"]["current_complete_research_engine_go"] = True
        self.bad("RELEASE_GATE_FALSE_GO")

    def test_full_ci_run_id_must_remain_actual_verified_run(self):
        self.ledger["development_gate"]["implementation_ci"]["run_id"] = 1
        self.bad("P0_0_04_CI_PROVENANCE_INVALID")

    def test_full_ci_skipped_cases_cannot_be_erased(self):
        self.ledger["development_gate"]["implementation_ci"]["strict_core_tests"]["v5_skipped"] = 0
        self.bad("CI_COUNTER_OR_SKIP_DRIFT")

    def test_software_ci_cannot_be_financial_e5_approval(self):
        self.ledger["stages"]["E5"]["actual_etf_parent_publications"] = 1
        self.bad("E5_FALSE_PUBLICATION")

    def test_handoff_42_unmerged_prs_not_41(self):
        self.ledger["development_gate"]["legacy_transfer"]["formerly_open_now_closed_unmerged_pr_count"] = 41
        self.bad("P005_HANDOFF_CENSUS_DRIFT")

    def test_handoff_no_fake_historical_adopt(self):
        self.ledger["development_gate"]["legacy_transfer"]["path_decisions"]["ADOPT"] = 1
        self.bad("P005_FALSE_CODE_ADOPTION_OR_GOLD")

    def test_public_b64_cannot_be_laundered_as_encrypted(self):
        self.ledger["development_gate"]["security_archive_audit"]["public_b64_confidentiality_certified"] = True
        self.bad("P006_FALSE_SECURITY_RECOVERY_OR_PUBLICATION_GO")

    def test_owner_key_recovery_cannot_be_invented(self):
        self.ledger["development_gate"]["security_archive_audit"]["actual_36_archive_key_recovery_verified"] = True
        self.bad("P006_FALSE_SECURITY_RECOVERY_OR_PUBLICATION_GO")

    def test_private_exposure_zero_unmeasured_must_remain_false(self):
        self.ledger["development_gate"]["security_archive_audit"]["private_content_nonexposure_certified"] = True
        self.bad("P006_FALSE_SECURITY_RECOVERY_OR_PUBLICATION_GO")

    def test_archive_count_cannot_be_silently_reduced(self):
        self.ledger["development_gate"]["security_archive_audit"]["public_reversible_b64"] = 0
        self.bad("P006_SECURITY_CENSUS_OR_HOLD_INVALID")

    def test_unresolved_public_security_issue_cannot_disappear(self):
        self.ledger["historical_public_material_audit_findings"] = [x for x in self.ledger["historical_public_material_audit_findings"] if x["id"] != "P006-R01"]
        self.bad("P006_HISTORICAL_FINDINGS_MISSING")

    def test_security_release_cannot_unblock_next_item(self):
        self.ledger["development_gate"]["security_archive_audit"]["successor_P0_0_07_blocked"] = True
        self.bad("P006_FALSE_SECURITY_RECOVERY_OR_PUBLICATION_GO")

    def test_p007_next_staged_item_cannot_be_advanced(self):
        self.ledger["development_gate"]["pending_next_item"] = "P0-2-06"
        self.bad("P006_FALSE_SECURITY_RECOVERY_OR_PUBLICATION_GO")

    def test_p007_release_receipt_must_not_claim_real_e5(self):
        self.ledger["development_gate"]["p0_0_closeout"]["real_e5_published_parents"] = 1
        self.bad("P007_STAGE_CLOSEOUT_SCOPE_OR_CURSOR_INVALID")

    def test_p007_end_of_stage_cannot_omit_final_sha_ci_requirement(self):
        self.ledger["development_gate"]["p0_0_closeout"]["closing_sha_postpush_ci_required"] = False
        self.bad("P007_STAGE_CLOSEOUT_SCOPE_OR_CURSOR_INVALID")

    def test_p007_receipt_exists_and_scoped_to_nonfinancial_ci(self):
        closeout = self.ledger["development_gate"]["p0_0_closeout"]
        self.assertEqual(closeout["next_allowed_item"], "P0-1-01")
        self.assertEqual([], validate(self.ledger, root=ROOT))

    def test_open_blockers_cannot_be_silenced(self):
        self.ledger["open_blockers"] = []
        self.bad("OPEN_BLOCKERS_DROPPED")


if __name__ == "__main__":
    unittest.main()
