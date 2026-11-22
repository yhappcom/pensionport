"""P0-0-05 positive and hostile mutations: no historical code or PR may self-approve."""
from __future__ import annotations

import copy
import unittest

from scripts.ire_legacy_transfer_gate import ROOT, PATH_CENSUS, REGISTER, load, verify


class LegacyTransferGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = load(ROOT, REGISTER)
        cls.source_paths = load(ROOT, PATH_CENSUS)

    def setUp(self):
        self.data = copy.deepcopy(self.source)
        self.paths = copy.deepcopy(self.source_paths)

    def fail_for(self, marker: str, root=None):
        errors = verify(self.data,self.paths,root)
        self.assertTrue(any(marker in error for error in errors), errors)

    def test_01_original_all_11_branches_and_1103_candidates_and_42_prs(self):
        self.assertEqual([], verify(self.data, self.paths, ROOT))
        self.assertEqual(11, len(self.data["branches"]))
        self.assertEqual(1103, len(self.paths["records"]))
        self.assertEqual(42, len(self.data["pull_requests"]))
        self.assertEqual({48,50}, {x["number"] for x in self.data["issues"]})

    def test_02_11_branches_are_distinct_and_code_adoption_is_zero(self):
        self.assertEqual([], verify(self.data,self.paths,root=None))
        self.assertEqual(0,self.data["decision_counts"]["ADOPT"])

    def test_03_missing_one_maximal_branch_refused(self):
        self.data["branches"].pop()
        self.fail_for("P005_MISSING_MAXIMAL_BRANCH")

    def test_04_missing_one_candidate_rejected(self):
        self.paths["records"].pop()
        self.fail_for("P005_ALL_PATHS_REQUIRED")

    def test_05_fabricated_adopt_with_valid_source_sha_rejected(self):
        self.paths["records"][0]["decision"]="ADOPT"
        self.paths["records"][0]["approved_for_current_runtime"]=True
        self.fail_for("P005_FALSE_RUNTIME_ADOPT_OR_FINANCE_APPROVAL")

    def test_06_real_e5_truth_cannot_be_pretended(self):
        self.paths["records"][0]["released_financial_fact"]=True
        self.fail_for("P005_FALSE_RUNTIME_ADOPT_OR_FINANCE_APPROVAL")

    def test_07_unapproved_branch_hold_cannot_be_converted_to_pass(self):
        self.data["branches"][0]["portfolio_decision"]="ADOPT"
        self.fail_for("P005_BRANCH_FALSE_GO")

    def test_08_missing_branch_followup_fails(self):
        self.data["branches"][3]["planned_action"]=""
        self.fail_for("P005_BRANCH_NEXT_ACTION_MISSING")

    def test_09_unverified_branch_head_sha_rejected_by_source(self):
        self.data["branches"][4]["source_head_sha"]="0"*40
        self.fail_for("P005_BRANCH_HEAD_DRIFT",ROOT)

    def test_10_catalog_blob_cannot_change(self):
        self.data["referenced_sources"]["docs/BRANCH_DIVERGENT_BLOB_CATALOG_20261122.tsv"]="0"*40
        self.fail_for("P005_FROZEN_UPSTREAM_BLOB_DRIFT",ROOT)

    def test_11_one_source_path_blob_mutated_without_catalog(self):
        self.paths["records"][350]["original_blob_sha"]="0"*40
        self.fail_for("P005_CANDIDATE_CHANGED",ROOT)

    def test_12_legacy_test_miscount_fails(self):
        self.data["decision_counts"]["TEST_ONLY"]+=1
        self.fail_for("P005_DECISION_COUNT_MISMATCH")

    def test_13_pr_one_missing_cannot_be_silent(self):
        self.data["pull_requests"].pop()
        self.fail_for("P005_MISSING_PR")

    def test_14_pr_49_head_swap_detected(self):
        row=next(x for x in self.data["pull_requests"] if x["number"]==49)
        row["original_head_sha"]="a"*40
        self.fail_for("P005_PR_ORIGINAL_HEAD_OR_CLOSEOUT_CHANGED",ROOT)

    def test_15_pr_50_style_fake_e3_approval_blocked(self):
        self.data["pull_requests"][10]["real_E3_approved"]=True
        self.fail_for("P005_PR_FALSE_APPROVAL")

    def test_16_pr_unmerged_cannot_become_main_merge(self):
        self.data["pull_requests"][0]["live_merged_at"]="2026-11-22T00:00:00Z"
        self.fail_for("P005_PR_FALSE_APPROVAL")

    def test_17_no_double_counting_all_74_live_prs_as_42(self):
        self.data["verified_github"]["pr_total_closed_live"]=42
        self.fail_for("P005_PR_LIVE_SCOPE_LAUNDERED")

    def test_18_issue_48_must_remain_open(self):
        self.data["issues"][0]["live_state"]="closed"
        self.fail_for("P005_ISSUE_FALSE_CLOSED")

    def test_19_issue_50_must_remain_open(self):
        self.data["issues"][1]["next_release_allowed"]=True
        self.fail_for("P005_ISSUE_FALSE_CLOSED")

    def test_20_issue_50_six_defects_cannot_be_dropped(self):
        self.data["issues"][1]["risks"]=self.data["issues"][1]["risks"][:2]
        self.fail_for("P005_ISSUE_RISK_CENSUS_GAP")

    def test_21_code_fix_does_not_convert_issues_to_final_approval(self):
        self.data["issues"][0]["risks"][0]["status"]="PASS"
        self.fail_for("P005_ISSUE_RISK_CENSUS_GAP")

    def test_22_missing_open_defect_docket_blocks(self):
        self.data["globally_unresolved"]=[]
        self.fail_for("P005_OPEN_RISKS_SILENCED")

    def test_23_invalid_issue_number_not_silently_accepted(self):
        self.data["issues"][0]["number"]=47
        self.fail_for("P005_ISSUE_48_50_REQUIRED")

    def test_24_original_transfer_pr_set_must_match(self):
        self.data["pull_requests"][2]["number"]=77
        self.fail_for("P005_PR_LIST_NOT_IDENTICAL",ROOT)


if __name__=="__main__":
    unittest.main()
