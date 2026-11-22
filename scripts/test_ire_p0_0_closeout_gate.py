"""P0-0-07 stage closeout must not silently cross to financial research GO."""
from __future__ import annotations
import copy
import unittest
from scripts.ire_p0_0_closeout_gate import ROOT,RECEIPT,STATE,LEDGER,load,verify

class P007CloseoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt=load(ROOT/RECEIPT)
        cls.state=load(ROOT/STATE)
        cls.ledger=load(ROOT/LEDGER)
    def setUp(self):
        self.r=copy.deepcopy(self.receipt)
        self.s=copy.deepcopy(self.state)
        self.l=copy.deepcopy(self.ledger)
    def bad(self,code):
        issues=verify(ROOT,receipt=self.r,state=self.s,ledger=self.l)
        self.assertTrue(any(code in x for x in issues),issues)
    def test_actual_stage_closeout_is_consistent(self):
        self.assertEqual([],verify(ROOT))
    def test_p007_stays_closed_when_next_e1_item_is_holding(self):
        self.assertEqual(self.s["items"][7]["status"], "HOLD")
        self.assertEqual([], verify(ROOT))

    def test_bad_ci_sha_cannot_pass(self):
        self.r["source_exact_head_ci"]["sha"]="0"*40
        self.bad("P007_EVIDENCE_RUN_OR_SHA_WRONG")
    def test_ci_success_not_self_certifiable(self):
        self.r["new_closeout_sha_ci_validation"]="NO_NEW_CI_NEEDED"
        self.bad("P007_UNJUSTIFIED_SELF_CI_PASS")
    def test_cannot_skip_required_seventh_task(self):
        self.s["items"][6]["status"]="HOLD"
        self.bad("P007_CHECKLIST_SEQUENCE_FALSE_GO")
    def test_unapproved_next_stage_cannot_be_opened(self):
        self.s["items"][8]["status"]="READY"
        self.bad("P007_CHECKLIST_SEQUENCE_FALSE_GO")
    def test_legacy_archives_not_treated_as_restored(self):
        self.r["evidence_digests"]["unrestored_historical_encrypted_archives"]=0
        self.bad("P007_STAGE_EVIDENCE_COUNTS")
    def test_cannot_invent_e3_approvals(self):
        self.r["financial_scope"]["actual_etf_formal_v123_child_approvals"]=13
        self.bad("P007_FINANCIAL_RELEASE_FALSE_GO")
    def test_cannot_invent_e5_publication(self):
        self.r["financial_scope"]["actual_e5_parent_publications"]=1
        self.bad("P007_FINANCIAL_RELEASE_FALSE_GO")
    def test_no_main_move_or_extra_branch_claim(self):
        self.r["unchanged_main_sha"]="0"*40
        self.bad("P007_BRANCH_MAIN_UNCHANGED_REQUIRED")
    def test_canonical_next_task_cursor_cannot_be_changed(self):
        self.l["development_gate"]["this_item"]="P0-1-02"
        self.bad("P007_CANONICAL_LEDGER_INVALID")
    def test_duplicate_canonical_approval_is_forbidden(self):
        self.l["reference_cohort"]["actual_e5_publications"]=1
        self.bad("P007_CANONICAL_LEDGER_INVALID")

if __name__=="__main__":
    unittest.main()
