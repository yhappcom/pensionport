"""Current E2 sequential-stage verdict is a HOLD until real source/gold."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent
STATE=ROOT/"V202_E1_E5_CURRENT_ROUTE_SEQUENCE_STATUS.json"
E2_REPORT=ROOT/"V206_E2_FULL_SOURCE_SEMANTIC_CENSUS_IMPLEMENTED_REAL_GOLD_HOLD_20261120.md"


class TestV206E2StageGate(unittest.TestCase):
    def setUp(self):
        self.status=json.loads(STATE.read_text(encoding="utf-8"))

    def test_01_e1_historical_pass_not_e2_quality_pass(self):
        self.assertEqual(self.status["sequence"][0]["status"],"PASS")
        self.assertTrue(self.status["current_e1_verdict"].startswith("PASS_V203_"))
        self.assertEqual(self.status["current_step"],
                         "E2_V2152_REAL_ETF250_NATIVE66_3_VISUAL_HOLD_2145_PAIR_SCREEN_34_CHAT_GOLD_HOLD")
        self.assertTrue(self.status["current_e2_verdict"].startswith("HOLD_"))

    def test_02_real_source_and_gold_not_falsely_certified(self):
        e=self.status["e2_evidence"]
        self.assertTrue(e["original_full_cue_census_implemented"])
        self.assertTrue(e["private_sqlite_hashchain_resume_and_idempotency_tested"])
        self.assertTrue(e["real_owner_srt_bytes_available_in_current_runtime"])
        self.assertFalse(e["real_13_segment_e2_review_completed"])
        self.assertFalse(e["independent_real_semantic_gold_certified"])
        self.assertFalse(e["native_fact_correction_and_relations_transferred"])
        self.assertEqual(e["knowledge_published"],0)

    def test_03_e3_e4_e5_stay_not_run_no_premature_release(self):
        self.assertEqual(self.status["sequence"][1]["status"],
                         "IN_PROGRESS_HOLD_REAL_SEMANTIC_GOLD_HISTORIC_OWNER_AND_SPEAKER")
        self.assertEqual([x["status"] for x in self.status["sequence"][2:]],
                         ["NOT_RUN_CURRENT_ROUTE"]*3)
        self.assertTrue(E2_REPORT.is_file())
        txt=E2_REPORT.read_text(encoding="utf-8")
        self.assertIn("104/104",txt)
        self.assertIn("HOLD_REAL_SOURCE_AND_INDEPENDENT_GOLD",txt)


    def test_04_v208_repairs_persist_but_e2_semantics_not_certified(self):
        e=self.status["e2_evidence"]
        self.assertTrue(e["v208_private_source_review_repair_chain_tested"])
        self.assertTrue(e["v208_source_review_before_repair_enforced"])
        self.assertTrue(e["v208_private_restart_idempotent_replay_tested"])
        self.assertTrue(e["v208_malformed_hash_rejected_without_runtime_exception"])
        self.assertTrue(e["v208_cross_census_temporal_history_check_tested"])
        self.assertTrue(e["v208_real_srt_private_resume_not_tested"])
        self.assertGreaterEqual(e["ci_total_tests"],281)
        self.assertGreaterEqual(e["ci_current_e2_tests"],210)
        self.assertEqual(e["ci_existing_e2_and_e1_regression"],71)
        self.assertTrue((ROOT/"V208_E2_PRIVATE_SOURCE_REPAIR_CHAIN_AND_CONTINUATION_HOLD_20261120.md").is_file())
        self.assertFalse(e["independent_real_semantic_gold_certified"])
        self.assertFalse(e["e2_semantic_accuracy_approved"])


    def test_05_verified_real_srt_changes_source_access_not_independent_gold(self):
        e=self.status["e2_evidence"]
        self.assertTrue(e["real_owner_srt_bytes_loaded_in_chat_private_runtime"])
        self.assertFalse(e["real_owner_srt_bytes_available_in_github_ci"])
        self.assertEqual(e["real_etf_video_id"],"LVE7XN_esTc")
        self.assertEqual(e["real_etf_cues_verified"],250)
        self.assertEqual(e["real_etf_candidate_draft_count"],57)
        self.assertEqual(e["real_etf_candidate_flagged_count"],47)
        self.assertTrue(e["real_etf_250_cues_accounted_by_span_or_nonclaim"])
        self.assertTrue(e["real_etf_private_draft_saved_in_user_library"])
        self.assertFalse(e["real_etf_live_v176_owner_sqlite_accessible"])
        self.assertFalse(e["real_etf_v179_61_provisional_claims_semantically_reconciled"])
        self.assertFalse(e["independent_real_semantic_gold_certified"])
        self.assertFalse(e["e2_semantic_accuracy_approved"])
        self.assertTrue((ROOT/"V210_E2_REAL_ETF_250_CUES_SOURCE_FIRST_57_DRAFT_HOLD_20261120.md").is_file())

    def test_06_v211_real_source_risk_and_crosscue_context_not_gold(self):
        e=self.status["e2_evidence"]
        self.assertTrue(e["v211_private_source_risk_docket_created"])
        self.assertEqual(e["v211_original_cues_rechecked"],250)
        self.assertEqual(e["v211_new_risk_review_items"],61)
        self.assertEqual(e["v211_risk_priority"],
                         {"high":44,"medium":14,"low":3})
        self.assertTrue(e["v2111_private_crosscue_relations_created"])
        self.assertEqual(e["v2111_private_crosscue_relation_count"],32)
        self.assertTrue(e["v211_code_custody_synthetic_tested"])
        self.assertTrue(e["v2111_code_custody_synthetic_tested"])
        self.assertFalse(e["v179_prior_unresolved_24_individual_cue_ids_recovered"])
        self.assertFalse(e["v179_prior_suspicious_68_individual_cue_ids_recovered"])
        self.assertFalse(e["v211_same_as_v179_61_native_atoms_certified"])
        self.assertFalse(e["v211_relation_semantic_truth_approved"])
        self.assertFalse(e["v211_private_source_data_uploaded_to_github"])
        self.assertFalse(e["independent_real_semantic_gold_certified"])
        self.assertFalse(e["e2_semantic_accuracy_approved"])
        self.assertTrue((ROOT/"V211_E2_REAL_ETF_250CUE_61_RISK_32_CROSSCUE_HOLD_20261120.md").is_file())


    def test_07_v212_real_v182_17_open_and_five_missed_risks_never_e2_go(self):
        e=self.status["e2_evidence"]
        self.assertEqual(e["v212_real_v182_effective_open_cue_count"],17)
        self.assertEqual(e["v212_v182_open_evidence_classes"],{
            "asr_audio":9,"video_screen":5,"historical_statistics":1,
            "fact_scope_overgeneralization":2})
        self.assertEqual(e["v212_prior_v211_risk_cues_intersect"],12)
        self.assertEqual(e["v212_newly_discovered_v211_missed_open_count"],5)
        self.assertEqual(e["v212_newly_discovered_v211_missed_open_cue_ids"],
                         [126,149,153,160,232])
        self.assertTrue(e["v212_private_original_crosswalk_saved_to_library"])
        self.assertTrue(e["v212_actual_original_source_250cue_hash_audit_pass"])
        self.assertTrue(e["v212_v182_historical_open_different_from_v179_24"])
        self.assertFalse(e["v212_v179_24_open_reconciled"])
        self.assertFalse(e["v212_v179_68_noatom_reconciled"])
        self.assertFalse(e["v212_real_v176_historical_owner_recovered"])
        self.assertFalse(e["v212_independent_gold_available"])
        self.assertFalse(e["e2_semantic_accuracy_approved"])
        self.assertTrue(e["v212_krx_concept_scope_explored_not_e4_certified"])
        self.assertTrue((ROOT/"V212_E2_REAL_V182_17_OPEN_5_SOURCE_RISK_GAPS_HOLD_20261120.md").is_file())


    def test_08_v213_native_qualifier_fix_pass_is_not_actual_e2_semantic_pass(self):
        e=self.status["e2_evidence"]
        self.assertTrue(e["v213_native_v176_to_frozen_v6_qualifier_bridge_tested"])
        self.assertTrue(e["v213_native_v6_condition_and_exception_cue_indices_mapped_synthetic"])
        self.assertTrue(e["v213_source_context_and_reviewer_cautions_excluded_from_native_qualifiers"])
        self.assertTrue(e["v213_owner_original_journal_unchanged_in_tests"])
        self.assertTrue(e["v213_private_append_only_source_qualifier_custody_tested"])
        self.assertTrue(e["v213_invalid_schema_types_fail_closed_without_typeerror"])
        self.assertFalse(e["v213_verified_all_original_etf_250_native_qualifiers"])
        self.assertFalse(e["v213_real_v176_owner_checkpoint_reloaded"])
        self.assertFalse(e["v213_all_speaker_stance_resolved"])
        self.assertFalse(e["v213_e2_independent_semantic_gold_passed"])
        self.assertFalse(e["v213_e2_approved"])
        # V213 is a historical minimum; V214+ may append new tests.
        # Do not make a previous stage regression depend on future totals.
        self.assertGreaterEqual(e["ci_current_e2_tests"],185)
        self.assertTrue((ROOT/"V213_E2_NATIVE_SOURCE_QUALIFIER_BRIDGE_REAL_V182_DEFECT_REPAIRED_20261120.md").is_file())


    def test_09_v214_exact_private_real_source_native_pass_is_not_gold(self):
        e=self.status["e2_evidence"]
        self.assertTrue(e["v214_exact_frozen_native_v6_private_real_srt_executed"])
        self.assertEqual(e["v214_real_srt_original_cues_checked"],250)
        self.assertEqual(e["v214_real_srt_plan_windows"],13)
        self.assertEqual(e["v214_real_v210_unapproved_candidates"],57)
        self.assertEqual(e["v214_real_native_unapproved_atoms_audited"],55)
        self.assertEqual(e["v214_real_native_blocked_unspoken_derived_claims"],2)
        self.assertEqual(e["v214_real_native_blocked_ids"],
                         ["E2REAL-036","E2REAL-050"])
        self.assertEqual(e["v214_real_native_cues_unresolved"],195)
        self.assertEqual(e["v214_real_native_source_explicit_condition_cue_links"],15)
        self.assertEqual(e["v214_real_native_source_explicit_exception_cue_links"],2)
        self.assertFalse(e["v214_real_native_speaker_and_stance_finalized"])
        self.assertFalse(e["v214_real_v176_historical_owner_sqlite_recovered"])
        self.assertFalse(e["v214_real_gold_independent_reference_available"])
        self.assertFalse(e["v214_real_precision_recall_measured"])
        self.assertTrue(e["v214_real_8_overlap_pairs_reviewed"])
        self.assertTrue(e["v214_real_1588_nonoverlap_pairs_not_independently_adjudicated"])
        self.assertEqual(e["v214_v182_open_cue_count_rechecked"],17)
        self.assertEqual(e["v214_v182_open_native_candidate_cues"],4)
        self.assertEqual(e["v214_v182_open_native_unresolved_cues"],13)
        self.assertTrue(e["v214_v182_all_cases_still_open"])
        self.assertFalse(e["v214_real_private_srt_uploaded_to_github"])
        self.assertTrue(e["v214_real_v210_decimal_runfail_fixed_by_byte_sha"])
        self.assertEqual(e["v214_code_only_native_validator_actions_artifact_id"],
                         14640087173)
        self.assertFalse(e["e2_semantic_accuracy_approved"])
        self.assertTrue((ROOT/"V214_E2_REAL_250_EXACT_FROZEN_NATIVE_V6_55_SOURCE_ATTESTED_17_HOLD_20261120.md").is_file())


    def test_10_v2152_reconciled_66_native_and_independent_semantic_gold_hold(self):
        e=self.status["e2_evidence"]
        self.assertEqual(e["v2152_actual_real_original_cues_verified"],250)
        self.assertEqual(e["v2152_previous_native_unapproved_atoms"],55)
        self.assertEqual(e["v2152_new_source_anchored_children"],16)
        self.assertEqual(e["v2152_replaced_multi_atom_parents"],2)
        self.assertEqual(e["v2152_video_only_quarantine_count"],3)
        self.assertEqual(e["v2152_video_only_quarantine_ids"],
                         ["E2REAL-037","E2REAL-054","E2REAL-055"])
        self.assertTrue(e["v2151_initial_67_native_draft_superseded_but_preserved"])
        self.assertEqual(e["v2152_native_v6_unapproved_atoms"],66)
        self.assertEqual(e["v2152_native_primary_cues_unresolved"],187)
        self.assertEqual(e["v2152_all_native_pairs_lexically_screened"],2145)
        self.assertEqual(e["v2152_pairs_similarity_above_or_equal_0_2"],13)
        self.assertEqual(e["v2152_pairs_chat_semantically_reviewed"],34)
        self.assertEqual(e["v2152_pairs_not_manually_semantically_reviewed"],2111)
        self.assertEqual(e["v2152_pairwise_partial_equivalence_remain_open"],2)
        self.assertEqual(e["v2152_duplicate_atoms_automatically_merged"],0)
        self.assertEqual(e["v2152_speaker_stance_textual_hypotheses"],66)
        self.assertFalse(e["v2152_audio_diarization_verified"])
        self.assertFalse(e["v2152_native_speaker_stance_finalized"])
        self.assertEqual(e["v2152_v182_open_total"],17)
        self.assertEqual(e["v2152_v182_open_native_primary"],2)
        self.assertEqual(e["v2152_v182_open_unresolved"],15)
        self.assertFalse(e["v2152_v179_24_open_individually_resolved"])
        self.assertFalse(e["v2152_v179_68_noatom_individually_resolved"])
        self.assertFalse(e["v2152_historical_v176_owner_sqlite_replayed"])
        self.assertFalse(e["v2152_independent_gold_certified"])
        self.assertFalse(e["v2152_precision_measured"])
        self.assertFalse(e["v2152_recall_measured"])
        self.assertFalse(e["v2152_high_risk_zero_misses_certified"])
        self.assertTrue(e["v2152_source_original_bytes_sha_guard_tested"])
        self.assertTrue(e["v2152_all_visual_cautions_gate_tested"])
        self.assertTrue(e["v2152_pairwise_sharding_cap_prevents_quadratic_runfail"])
        self.assertFalse(e["v2152_real_private_source_data_uploaded_to_github"])
        self.assertEqual(e["ci_current_e2_tests"],238)
        self.assertEqual(e["ci_total_tests"],309)
        self.assertTrue((ROOT/"V215_E2_REAL_250_66_NATIVE_ATOMS_2145_PAIRS_34_REVIEWED_AND_GOLD_HOLD_20261121.md").is_file())


if __name__=="__main__":
    unittest.main()
