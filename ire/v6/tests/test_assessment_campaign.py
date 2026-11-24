"""Synthetic campaign routing/authority regression; not real gold."""
import copy,unittest
from unittest.mock import patch
from ire.v6.assessment_plan import (CAMPAIGN_SCHEMA,THRESHOLDS,register_campaign,
                                   validate_campaign)
from ire.v6.assessment_campaign import assess_campaign
from ire.v6.codec import json_digest,sha256
from ire.v6.errors import InvalidInput


class AssessmentCampaignTests(unittest.TestCase):
    def setUp(self):
        from ire.v6.tests.test_p205_gold_release import P205GoldReleaseTests
        fx=P205GoldReleaseTests();fx.setUp()
        self.fx=fx
        self.plan={"schema":CAMPAIGN_SCHEMA,"campaign_id":"new_holdout_001",
                   "engine_commit_sha":"a"*40,"purpose":"HOLDOUT",
                   "registered_at":"2026-11-21T00:00:00+00:00",
                   "source":{"video_id":"AbCdEf12345","cue_count":4,
                             "original_srt_sha256":sha256(fx.source)},
                   "predictions":{"frozen_native_sha256":sha256(fx.native),"atom_count":2},
                   "assessment":{"thresholds":copy.deepcopy(THRESHOLDS)},
                   "source_only_packet_sha256":fx.registry["source_only_packet_sha256"]}

    def run_eval(self,**kw):
        args={"gold":self.fx.gold,"alignment":self.fx.alignment}
        args.update(kw)
        return assess_campaign(self.plan,self.fx.source,self.fx.native,**args)

    def test_missing_gold_is_l1_not_accuracy(self):
        r=self.run_eval(gold=None,alignment=None)
        self.assertEqual(r["evidence_level"],"L1")
        self.assertIsNone(r["tp"])
        self.assertFalse(r["ready_for_p0_2_06"])

    def test_perfect_internal_score_is_l2_not_independent(self):
        r=self.run_eval()
        self.assertEqual((r["evidence_level"],r["tp"],r["fp"],r["fn"]),("L2",2,0,0))
        self.assertTrue(r["diagnostic_thresholds_met"])
        self.assertFalse(r["independent_metrics_available"])
        self.assertFalse(r["ready_for_p0_2_06"])

    def test_thresholds_not_relaxed(self):
        self.plan["assessment"]["thresholds"]["atomic_precision_min_bp"]=9000
        with self.assertRaises(InvalidInput):self.run_eval()

    def test_known_development_video_cannot_be_holdout(self):
        self.plan["source"]["video_id"]="LVE7XN_esTc"
        with self.assertRaises(InvalidInput):validate_campaign(self.plan)

    def test_append_only_registration_and_no_reused_holdout(self):
        prior=register_campaign([],self.plan)
        saved=copy.deepcopy(prior)
        another=copy.deepcopy(self.plan);another["campaign_id"]="other_campaign_002"
        with self.assertRaises(InvalidInput):register_campaign(prior,another)
        another["purpose"]="DEVELOPMENT"
        result=register_campaign(prior,another)
        self.assertEqual(prior,saved)
        self.assertEqual(result[0],prior[0])
        self.assertEqual(result[1]["previous_entry_sha256"],json_digest(prior[0]))
        corrupted=copy.deepcopy(prior);corrupted[0]["plan"]["engine_commit_sha"]="b"*40
        with self.assertRaises(InvalidInput):register_campaign(corrupted,another)

    def test_caller_signed_keys_cannot_enrol_campaign(self):
        fx=self.fx;fx.registry["plan_sha256"]=json_digest(self.plan)
        evidence={k:getattr(fx,k) for k in ("registry","consensus","alignment_receipt")}
        evidence["reviewer_submissions"]=fx.reviews
        r=self.run_eval(production_evidence=evidence)
        self.assertEqual(r["evidence_level"],"L2")
        self.assertFalse(r["ready_for_p0_2_06"])

    def test_synthetic_pinned_campaign_uses_existing_l4_gate(self):
        fx=self.fx;fx.registry["plan_sha256"]=json_digest(self.plan)
        evidence={k:getattr(fx,k) for k in ("registry","consensus","alignment_receipt")}
        evidence["reviewer_submissions"]=fx.reviews
        pin={self.plan["campaign_id"]:{"plan_sha256":json_digest(self.plan),
                                       "registry_sha256":json_digest(fx.registry)}}
        with patch("ire.v6.assessment_plan.PINNED_CAMPAIGNS",pin):
            r=self.run_eval(production_evidence=evidence)
            self.assertEqual(r["evidence_level"],"L4")
            self.assertTrue(r["ready_for_p0_2_06"])
            self.assertFalse(r["research_publication_authorized"])
            self.plan["engine_commit_sha"]="b"*40
            self.assertFalse(self.run_eval(production_evidence=evidence)["ready_for_p0_2_06"])

    def manual(self):
        fx=self.fx
        transcripts=[b"synthetic transcript one",b"synthetic transcript two"]
        submissions=[]
        for row,transcript in zip(fx.reviews,transcripts):
            body=row["body"]
            submissions.append({k:body[k] for k in ("role","session_id","began_at",
                                                     "submitted_at","draft_gold")})
            submissions[-1].update(packet_sha256=self.plan["source_only_packet_sha256"],
                    transcript_sha256=sha256(transcript),predictions_reported_exposed=False)
        c=copy.deepcopy(fx.consensus["body"])
        c["reviewer_submission_sha256"]={x["role"]:json_digest(x) for x in submissions}
        lock={k:v for k,v in fx.alignment_receipt["body"].items() if k!="schema"}
        return {"submissions":submissions,"consensus":c,"alignment_lock":lock},transcripts

    def test_manual_two_review_exports_are_l3_not_l4(self):
        e,t=self.manual()
        r=self.run_eval(manual_evidence=e,transcripts=t)
        self.assertEqual(r["evidence_level"],"L3")
        self.assertFalse(r["independent_gold_verified"])
        self.assertFalse(r["ready_for_p0_2_06"])

    def test_manual_same_session_and_transcript_drift_rejected(self):
        e,t=self.manual()
        e["submissions"][1]["session_id"]=e["submissions"][0]["session_id"]
        with self.assertRaises(InvalidInput):self.run_eval(manual_evidence=e,transcripts=t)
        e,t=self.manual()
        with self.assertRaises(InvalidInput):self.run_eval(manual_evidence=e,transcripts=[t[0],b"tampered"])

    def test_closeout_replays_l4_instead_of_accepting_a_grade(self):
        from ire.v6.assessment_closeout import propose_closeout
        fx=self.fx;fx.registry["plan_sha256"]=json_digest(self.plan)
        evidence={k:getattr(fx,k) for k in ("registry","consensus","alignment_receipt")}
        evidence["reviewer_submissions"]=fx.reviews
        def run():
            return propose_closeout(self.plan,fx.source,fx.native,gold=fx.gold,
                      alignment=fx.alignment,production_evidence=evidence)
        with self.assertRaises(InvalidInput):run()
        pin={self.plan["campaign_id"]:{"plan_sha256":json_digest(self.plan),
                                       "registry_sha256":json_digest(fx.registry)}}
        with patch("ire.v6.assessment_plan.PINNED_CAMPAIGNS",pin):
            result=run()
            self.assertEqual((result["tp"],result["fp"],result["fn"]),(2,0,0))
            self.assertFalse(result["research_publication_authorized"])
            self.assertEqual(result["gold_sha256"],json_digest(fx.gold))
