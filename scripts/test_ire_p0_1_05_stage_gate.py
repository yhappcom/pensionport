"""P105 E1 final structure assessment must never promote real ETF GO."""
from __future__ import annotations
import copy
import unittest
from scripts.ire_p0_1_05_stage_gate import (
    ROOT,RECEIPT,STATE,LEDGER,P101,P102,P103,P104,load,verify)


class P105StageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.clean_receipt=load(ROOT,RECEIPT)
        cls.clean_state=load(ROOT,STATE)
        cls.clean_ledger=load(ROOT,LEDGER)
        cls.clean_inputs={
            "p101":load(ROOT,P101),"p102":load(ROOT,P102),
            "p103":load(ROOT,P103),"p104":load(ROOT,P104)}

    def setUp(self):
        self.r=copy.deepcopy(self.clean_receipt)
        self.s=copy.deepcopy(self.clean_state)
        self.l=copy.deepcopy(self.clean_ledger)
        self.i=copy.deepcopy(self.clean_inputs)

    def check(self):
        return verify(ROOT,receipt=self.r,state=self.s,
                      ledger=self.l,inputs=self.i)

    def bad(self,code):
        errors=self.check()
        self.assertTrue(any(code in e for e in errors),errors)

    def test_01_exact_e1_stage_pass_and_real_etf_hold(self):
        self.assertEqual([],self.check())

    def test_02_e2_must_be_only_new_ready(self):
        self.s["items"][13]["status"]="READY"
        self.bad("E1_FIVE_PASS_E2_ONLY_NEXT")

    def test_03_not_all_five_e1_items_can_be_passed_by_fiat(self):
        self.s["items"][10]["status"]="HOLD"
        self.bad("E1_FIVE_PASS_E2_ONLY_NEXT")

    def test_04_no_etf_turn2_can_be_fabricated(self):
        self.l["reference_cohort"]["actual_user_etf_turn2_final_verdict_proven"]=True
        self.bad("ETF_ACTUAL_APPROVAL_PREMATURE")

    def test_05_stage_e1_cannot_be_released_for_real_etf(self):
        self.l["stages"]["E1"]["official_stage_release"]="PASS"
        self.bad("STAGE_SOFTWARE_AND_REAL_RELEASE_CONFLATED")

    def test_06_semantics_accurate_gold_cannot_be_claimed(self):
        self.r["actual_etf_semantic_gold_verified"]=True
        self.bad("NEXT_E2_ENTRY_OR_HOLD_SCOPE_MISSTATED")

    def test_07_source_sha_altering_denied(self):
        self.i["p102"]["source_srt_sha256"]="0"*64
        self.bad("P102_REAL_SOURCE_ONLY_NOT_SEMANTICS")

    def test_08_cross_child_condition_45_cannot_disappear(self):
        self.i["p103"]["b0013_c00057"][
            "foreign_inherited_condition_source_cues"]=[46,47]
        self.bad("P103_CROSS_CONDITIONS_NOT_FULLY_RETAINED")

    def test_09_49_edge_cannot_be_claimed_as_final_e3(self):
        self.i["p103"]["formal_etf_e3_approved_children"]=13
        self.bad("P103_CROSS_CONDITIONS_NOT_FULLY_RETAINED")

    def test_10_unsealed_crash_cannot_be_relabelled_auto_recovered(self):
        self.i["p104"]["post_commit_pre_e4_seal_crash"][
            "automatic_physical_rollback_guaranteed"]=True
        self.bad("UNSEALED_CRASH_RISK_LAUNDERED_AS_AUTOMATIC_RECOVERY")

    def test_11_partial_second_child_store_cannot_pass(self):
        self.i["p104"]["failure_zero_partial"]["missing_secondary_child_official_evidence"][
            "knowledge"]=1
        self.bad("P104_PARTIAL_WRITE_OR_REPLAY")

    def test_12_duplicate_parent_publication_denied(self):
        self.i["p104"]["idempotent_replay_with_prior_externally_retained_owner_pin"][
            "additional_parent_publications"]=1
        self.bad("P104_PARTIAL_WRITE_OR_REPLAY")

    def test_13_missing_manual_two_turn_provenance_denied(self):
        self.i["p101"]["manual_turns_not_platform_authenticated"]=False
        self.bad("P101_SINGLE_API_OR_TURN_PROVENANCE")

    def test_14_e4_or_e5_real_approved_impossible_from_ci(self):
        self.r["actual_etf_approvals"]["E5_parent_publications"]=1
        self.bad("FALSE_INVESTMENT_ADVICE_OR_E5_PUBLICATION")

    def test_15_cannot_accept_only_five_of_six_ci_jobs(self):
        self.r["last_precloseout_ci"]["successful_jobs"]=5
        self.bad("UNVERIFIED_BASELINE_CI")

    def test_16_closeout_ci_never_self_certified(self):
        self.r["post_commit_ci_auto_self_certified"]=True
        self.bad("CLOSEOUT_CI_SELF_ATTESTATION")

    def test_17_protected_main_still_pinned(self):
        self.r["main_sha_unchanged"]="0"*40
        self.bad("NEXT_E2_ENTRY_OR_HOLD_SCOPE_MISSTATED")

    def test_18_historical_p104_proof_has_no_independent_owner_pin_custody(self):
        self.i["p104"]["operational_constraints"][
            "owner_external_pin_custody_not_self_certified"]=False
        self.bad("UNSEALED_CRASH_RISK_LAUNDERED_AS_AUTOMATIC_RECOVERY")


if __name__=="__main__":
    unittest.main()
