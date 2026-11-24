"""Synthetic public operational release boundary tests."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from scripts import ire_p205_operational_release as op


def fixture():
    sources=[];trials=[]
    for i,domain in enumerate(sorted(op.DOMAINS),1):
        src={"domain":domain,"video_id":f"AbCdEf1234{i}","source_sha256":str(i)*64,
             "selection_sha256":str(i+3)*64,"exposure_screen_sha256":str(i+6)*64}
        sources.append(src)
        trials.append({"schema":"IRE_P205_INTERNAL_OPERATIONAL_TRIAL_V1","policy_id":op.POLICY_ID,
            "campaign_id":f"synthetic_{i}","engine_commit_sha":"a"*40,
            "cohort_sha256":"0"*64,"domain":domain,"video_id":src["video_id"],
            "source_sha256":src["source_sha256"],"selection_sha256":src["selection_sha256"],
            "plan_sha256":"a"*64,"prediction_sha256":"b"*64,"reference_sha256":"c"*64,
            "alignment_sha256":"d"*64,"review_sha256":"e"*64,
            "manifest_sha256":"f"*64,"inventory_sha256":"a"*64,
            "prediction_frozen_at":"2026-11-24T02:00:00+00:00",
            "source_cues":100,"reviewed_cues":100,"prediction_atoms":100,"reference_atoms":98,
            "tp":97,"fp":3,"fn":1,"high_risk_reference_atoms":20,"high_risk_fn":0,
            "numeric_boundary_warnings":0,"critical_pair_mismatches":0,
            "internal_thresholds_met":True,"evidence_level":"L2","independent_gold_verified":False,
            "independent_precision":None,"independent_recall":None,"independent_high_risk_fn":None,
            "host_turn_authentication_verified":False,"research_publication_authorized":False,
            "personalized_advice_authorized":False,"status":"INTERNAL_TRIAL_THRESHOLDS_MET"})
    cohort={"schema":"IRE_P205_OPERATIONAL_COHORT_V1","policy_id":op.POLICY_ID,
            "engine_commit_sha":"a"*40,"registered_at":"2026-11-24T01:00:00+00:00","sources":sources}
    return ({"schema":"IRE_P205_OPERATIONAL_CLOSEOUT_V1","policy_id":op.POLICY_ID,
             "cohort_sha256":"0"*64,"trials":trials,
             "ci":{"run_id":1,"head_sha":"a"*40,"successful_jobs":6,"conclusion":"success"}},cohort)

class OperationalReleaseTests(unittest.TestCase):
    def setUp(self):self.r,self.c=fixture()
    def errs(self):return op.validate_closeout(self.r,self.c,"0"*64)

    def test_positive_shape_only(self):self.assertEqual([],self.errs())
    def test_per_video_not_average(self):
        self.r["trials"][0].update(tp=90,fp=10,fn=8)
        self.assertIn("P205_OPERATIONAL_PER_VIDEO_THRESHOLDS",self.errs())
    def test_high_risk_nonvacuous(self):
        self.r["trials"][0]["high_risk_reference_atoms"]=0
        self.assertTrue(self.errs())
    def test_l4_claim_and_personal_approval_rejected(self):
        self.r["trials"][0]["independent_precision"]=1
        self.assertIn("P205_OPERATIONAL_NO_INDEPENDENCE_OR_RELEASE_LAUNDERING",self.errs())
        self.r["trials"][0]["personalized_advice_authorized"]=True
        self.assertTrue(self.errs())
    def test_cohort_registered_before_prediction(self):
        self.c["registered_at"]="2026-11-24T03:00:00+00:00"
        self.assertIn("P205_OPERATIONAL_COHORT_BEFORE_PREDICTION",self.errs())
    def test_duplicate_and_exposed_sources_rejected(self):
        self.c["sources"][0]["video_id"]="LVE7XN_esTc"
        self.assertTrue(self.errs())
    def test_different_engine_ci_rejected(self):
        self.r["ci"]["head_sha"]="b"*40
        self.assertIn("P205_OPERATIONAL_ENGINE_CI",self.errs())
    def test_current_real_hold(self):self.assertEqual([],op.verify_current())
    def test_unpinned_perfect_metrics_cannot_advance(self):
        state=op._load(op.ROOT,op.STATE)
        state["items"][16]["status"]="PASS"
        with patch.object(op,"PREREGISTERED_COHORT_SHA256",None):
            self.assertIn("P205_OPERATIONAL_REAL_CLOSEOUT_NOT_ENROLLED",op.verify_current(state=state))
    def test_forged_operational_pass_in_ledger_rejected(self):
        ledger=op._load(op.ROOT,op.LEDGER)
        ledger["stages"]["E2"]["operational_assessment"]["status"]="PASS_INTERNAL_ONLY"
        self.assertIn("P205_OPERATIONAL_LEDGER_FALSE_PASS",op.verify_current(ledger=ledger))
    def test_actual_policy_routes_live_to_operational_not_l4(self):
        from scripts import ire_p205_live_release as old
        with patch.object(old,"verify_legacy_independent_transition",side_effect=AssertionError("L4 invoked")):
            self.assertEqual([],old.verify_current())


class CommonRubricReleaseTests(unittest.TestCase):
    def test_old_cohort_cannot_be_released_even_with_perfect_metrics(self):
        r,c=fixture()
        self.assertIn("P205_OPERATIONAL_FAILED_COHORT_CANNOT_RELEASE",
                      op.validate_common_closeout(r,c,op.FAILED_COHORT_SHA256))

    def test_common_contract_and_failed_source(self):
        from ire.v6.common_atomic_review import RUBRIC_SHA256
        r,c=fixture();c["rubric_sha256"]=RUBRIC_SHA256
        self.assertIn("P205_OPERATIONAL_COMMON_REPLAY_REQUIRED",op.validate_common_closeout(r,c,"0"*64))
        for t in r["trials"]:
            t.update(schema="IRE_P205_INTERNAL_OPERATIONAL_TRIAL_V2",
                     common_typed_review_replayed=True,rubric_sha256=RUBRIC_SHA256,
                     first_packet_sha256="1"*64,second_packet_sha256="2"*64,
                     rubric_lock_sha256="3"*64,critical_unmatched_atoms=0)
        self.assertEqual([],op.validate_common_closeout(r,c,"0"*64))
        c["sources"][0]["video_id"]=op.FAILED_VIDEO_ID
        self.assertIn("P205_OPERATIONAL_FAILED_SOURCE_REUSE",op.validate_common_closeout(r,c,"0"*64))
