"""P204 SHA-only public controls; true V6 RED/GREEN exercises run in V6 prepush."""
import copy
import unittest
from scripts.ire_p0_2_04_adversarial_gate import (
    ROOT,P204,P203,STATE,LEDGER,load,verify,
)
class P204AdversarialReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline=tuple(load(ROOT,p) for p in (P204,STATE,LEDGER,P203))
    def setUp(self):
        self.r,self.s,self.l,self.prior=copy.deepcopy(self.baseline)
    def errors(self):
        return verify(ROOT,receipt=self.r,state=self.s,ledger=self.l,p203=self.prior)
    def bad(self,label):
        result=self.errors()
        self.assertTrue(any(label in x for x in result),result)
    def test_01_original_red_green_contract(self):self.assertEqual([],self.errors())
    def test_02_wrong_issue_number(self):
        self.r["issue_numbers"]=[48,51];self.bad("ISSUE_ID")
    def test_03_red_not_reproduced(self):
        self.r["red_negative_tests_failed_as_expected"]=0;self.bad("RED_GREEN")
    def test_04_fake_green_sha(self):
        self.r["candidate_green_sha"]="0"*40;self.bad("RED_GREEN")
    def test_05_missing_cross_cue_fixture(self):
        self.r["cross_cue_rebuttal_synthetic_tests"]=4;self.bad("TEN_NEW")
    def test_06_missing_legacy_fixture(self):
        self.r["legacy_v2_synthetic_tests"]=4;self.bad("TEN_NEW")
    def test_07_high_risk_omission_false_close(self):
        self.r["issue48_unmodelled_high_risk_tax_assertion_can_close_research"]=True
        self.bad("ISSUE48")
    def test_08_model_nonfact_self_laundering(self):
        self.r["issue48_nonfact_self_label_independent_role_certified"]=True
        self.bad("ISSUE48")
    def test_09_assert_atomic_recall_from_cue_coverage(self):
        self.r["issue48_source_first_atomic_exhaustiveness_certified"]=True
        self.bad("ISSUE48")
    def test_10_claim_cross_cue_negation_accepted(self):
        self.r["issue50_cross_cue_rebuttal_and_disclaimer_rejected"]=False
        self.bad("ISSUE50_NEGATION")
    def test_11_claim_cross_window_exception_accepted(self):
        self.r["issue50_cross_window_stance_risk_rejected"]=False
        self.bad("ISSUE50_NEGATION")
    def test_12_fake_duplicate_rule_after_review(self):
        self.r["issue50_interleaved_duplicate_rule_rejected"]=False
        self.bad("ISSUE50_NEGATION")
    def test_13_relevant_model_revision_does_not_invalidate(self):
        self.r["issue50_model_revision_invalidates_rule"]=False
        self.bad("ISSUE50_NEGATION")
    def test_14_unsupported_full_semantic_entailment(self):
        self.r["issue50_scope_stance_semantics_fully_certified"]=True
        self.bad("NO_FALSE_SEMANTIC")
    def test_15_historical_v2_completion_promoted(self):
        self.r["issue50_legacy_v2_historic_research_complete_declassified_no_go"]=False
        self.bad("V2_HISTORIC")
    def test_16_historical_owner_db_migration_faked(self):
        self.r["issue50_real_owner_v2_database_import_or_migration_approved"]=True
        self.bad("V2_HISTORIC")
    def test_17_official_law_date_unbounded(self):
        self.r["issue50_as_of_future_version_unsilenced"]=True
        self.bad("OFFICIAL_TEMPORAL")
    def test_18_private_original_claimed_in_this_stage(self):
        self.r["real_owner_etf_source_replay_this_stage"]=True
        self.bad("FALSE_NEW_PRIVATE")
    def test_19_synthetic_gold_forgery(self):
        self.r["independent_semantic_recall"]=0.99
        self.bad("FALSE_FINANCIAL")
    def test_20_e3_13_fake_approvals(self):
        self.r["real_etf_e3_v123_approvals"]=13
        self.bad("FALSE_FINANCIAL")
    def test_21_e5_fake_knowledge_publication(self):
        self.r["real_etf_e5_publications"]=1
        self.bad("FALSE_FINANCIAL")
    def test_22_skip_p205_while_p204_ready(self):
        self.s["items"][17]["status"]="READY"
        self.bad("FULL_60_TASK")
    def test_23_wrong_live_cursor(self):
        self.l["development_gate"]["this_item"]="P0-2-06"
        self.bad("ACTIVE_STAGE_CURSOR")
    def test_24_loss_of_p203_source_hash(self):
        self.prior["p203_private_source_semantic_json_sha256"]="0"*64
        self.bad("P203_OWNER_SOURCE")
    def test_25_wrong_next_phase(self):
        self.r["subsequent_after_closeout"]="P0-2-06"
        self.bad("NEXT_STEP")
if __name__=="__main__":unittest.main()
