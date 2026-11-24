"""Public synthetic transition cases, no real enrollment."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from scripts import ire_p205_live_release as live


def fixture():
    r={"schema":"IRE_P205_PRIVATE_ASSESSMENT_CLOSEOUT_V1",
       "campaign_id":"synthetic_holdout","plan_sha256":"1"*64,
       "registry_sha256":"2"*64,"engine_commit_sha":"a"*40,
       "source_sha256":"3"*64,"prediction_sha256":"4"*64,
       "gold_sha256":"5"*64,"alignment_sha256":"6"*64,
       "production_evidence_sha256":"7"*64,"source_cues":250,
       "prediction_atoms":100,"gold_atoms":98,"tp":97,"fp":3,"fn":1,
       "high_risk_fn":0,"evidence_level":"L4","independent_gold_verified":True,
       "research_publication_authorized":False}
    return {"schema":"IRE_P205_REVIEWED_PUBLIC_CLOSEOUT_V1","private_replay":r,
            "ci":{"run_id":1,"head_sha":"a"*40,"successful_jobs":6,"conclusion":"success"}}


class P205LiveTransitionTests(unittest.TestCase):
    def setUp(self):
        self.r=fixture()
        self.pins={"synthetic_holdout":{"plan_sha256":"1"*64,"registry_sha256":"2"*64}}

    def test_structurally_eligible_receipt(self):
        self.assertEqual([],live.validate_closeout(self.r,self.pins))

    def test_unenrolled_campaign_and_l3_rejected(self):
        self.assertTrue(live.validate_closeout(self.r,{}))
        self.r["private_replay"]["evidence_level"]="L3"
        self.assertTrue(live.validate_closeout(self.r,self.pins))

    def test_high_risk_fn_and_thresholds_are_not_relaxed(self):
        self.r["private_replay"]["high_risk_fn"]=1
        self.assertTrue(live.validate_closeout(self.r,self.pins))
        self.r["private_replay"].update(high_risk_fn=0,tp=95,fp=5,fn=3)
        self.assertTrue(live.validate_closeout(self.r,self.pins))

    def test_wrong_engine_ci(self):
        self.r["ci"]["head_sha"]="b"*40
        self.assertTrue(live.validate_closeout(self.r,self.pins))

    def test_actual_current_hold(self):
        state=live._load(live.ROOT,live.STATE)
        if state["items"][16]["status"]=="PASS":
            self.assertEqual([],live.verify_current())
        else:
            self.assertEqual([],live.verify_current())

    def test_unpinned_perfect_receipt_cannot_advance(self):
        s={"items":[{} for _ in range(60)]}
        s["items"][16]={"id":"P0-2-05","status":"PASS"}
        with patch.object(live,"APPROVED_CLOSEOUT_SHA256",None):
            self.assertIn("P205_LIVE_NO_REVIEWED_CLOSEOUT_ENROLLMENT",
                          live.verify_current(state=s,ledger={}))

    def test_pinned_receipt_must_bind_checklist_and_current_guards(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/live.CLOSEOUT_PATH
            path.parent.mkdir(parents=True)
            raw=json.dumps(self.r).encode();path.write_bytes(raw)
            s={"items":[{} for _ in range(60)]}
            s["items"][16]={"id":"P0-2-05","status":"PASS","evidence":[]}
            with patch.object(live,"APPROVED_CLOSEOUT_SHA256",live._sha(raw)), \
                 patch.object(live,"_campaign_pins",return_value=self.pins):
                self.assertIn("P205_LIVE_CHECKLIST_EVIDENCE_NOT_BOUND",
                              live.verify_current(root,state=s,ledger={}))
                s["items"][16]["evidence"]=[{"kind":"assessment","verdict":"PASS",
                    "ref":live.CLOSEOUT_PATH,"sha":live._git_blob(raw)}]
                with patch.object(live,"_load",return_value={}), \
                     patch.object(live,"validate_checklist",return_value=["SEQUENCE_BAD"]), \
                     patch.object(live,"validate_status",return_value=[]):
                    self.assertEqual(["SEQUENCE_BAD"],live.verify_current(root,state=s,ledger={}))
                    with patch.object(live,"validate_checklist",return_value=[]):
                        self.assertEqual([],live.verify_current(root,state=s,ledger={}))
                path.write_bytes(raw+b" ")
                self.assertIn("P205_LIVE_CLOSEOUT_DIGEST_DRIFT",
                              live.verify_current(root,state=s,ledger={}))
