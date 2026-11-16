"""Negative controls: fabricated 100% synthetic gold can never certify GO."""
import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from aggregate_blind_cohort import audit_cohort
from ire.v6.evaluation import _wilson95
from ire.v6.errors import InvalidInput

def ratio(n,d):
    return {"numerator":n,"denominator":d,
            "parts_per_million":(n*1000000+d//2)//d if d else None}

def fake(i, missed=0):
    by={}
    for cat in ("LEVERAGE","OTHER","PENSION","RETURN","TAX"):
        tp,fn = (4,missed) if cat=="PENSION" else ((3,0) if cat=="OTHER" else (0,0))
        by[cat]={"tp":tp,"fp":0,"fn":fn,"precision":ratio(tp,tp),
                 "recall":ratio(tp,tp+fn)}
    c={"tp":7,"fp":0,"fn":missed,"predictions":7,"gold":7+missed}
    h=lambda k:format(10*i+k,"064x")
    m={"schema":"IRE_V6_BLIND_ARITHMETIC_V1",
       "source_sha256":h(1),"plan_sha256":h(2),"gold_sha256":h(3),
       "predictions_sha256":h(4),"alignment_sha256":h(5),
       "counts":c,"by_category":by,
       "precision":ratio(7,7),"recall":ratio(7,7+missed),
       "high_risk_recall":ratio(4,4+missed),
       "precision_wilson_95":_wilson95(7,7),
       "recall_wilson_95":_wilson95(7,7+missed),
       "high_risk_recall_wilson_95":_wilson95(4,4+missed),
       "actual_reviewer_identity_verified":False,
       "actual_blindness_independently_verified":False,
       "gold_completeness_independently_verified":False,
       "semantic_accuracy_certified":False,"engine_quality_certified":False,
       "p0_go":False}
    return {"slot":f"S{i:02d}","measurement":m}

class CohortGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=json.loads(Path(__file__).with_name("BLIND_PREREGISTRATION_V1.json").read_text())

    def test_missing_gold_is_unmeasured(self):
        r=audit_cohort(self.p,[])
        self.assertEqual(r["status"],"COHORT_INCOMPLETE_NO_SCORE")
        self.assertNotIn("precision",r)
        self.assertFalse(r["p0_go"])

    def test_perfect_synthetic_nine_is_never_gold_certification(self):
        r=audit_cohort(self.p,[fake(i) for i in range(1,10)])
        self.assertEqual(r["counts"]["gold"],63)
        self.assertEqual(r["high_risk_gold"],36)
        self.assertTrue(r["preregistered_thresholds_met_arithmetically"])
        self.assertTrue(r["minimum_gold_sample_met"])
        self.assertFalse(r["prereg_gold_commitment_present"])
        self.assertFalse(r["independent_gold_verified"])
        self.assertFalse(r["precision_recall_measured"])
        self.assertFalse(r["p0_go"])

    def test_partial_set_cannot_report_recall(self):
        r=audit_cohort(self.p,[fake(i) for i in range(1,9)])
        self.assertEqual(r["reports_received"],8)
        self.assertNotIn("recall",r)

    def test_bad_high_risk_recall_rejected_by_threshold(self):
        r=audit_cohort(self.p,[fake(i,1) for i in range(1,10)])
        self.assertFalse(r["preregistered_thresholds_met_arithmetically"])
        self.assertFalse(r["p0_go"])

    def test_duplicate_replay_and_fake_approval_blocked(self):
        a=[fake(i) for i in range(1,10)]
        a[1]["slot"]="S01"
        with self.assertRaises(InvalidInput):
            audit_cohort(self.p,a)
        a=[fake(i) for i in range(1,10)]
        a[1]["measurement"]["predictions_sha256"]=a[0]["measurement"]["predictions_sha256"]
        with self.assertRaises(InvalidInput):
            audit_cohort(self.p,a)
        a=[fake(i) for i in range(1,10)]
        a[0]["measurement"]["p0_go"]=True
        with self.assertRaisesRegex(InvalidInput,"UNTRUSTED_SELF_APPROVAL"):
            audit_cohort(self.p,a)

    def test_forged_totals_rates_and_prereg_blocked(self):
        a=[fake(i) for i in range(1,10)]
        a[0]["measurement"]["counts"]["tp"]=8
        with self.assertRaises(InvalidInput):
            audit_cohort(self.p,a)
        a=[fake(i) for i in range(1,10)]
        a[0]["measurement"]["by_category"]["PENSION"]["recall"]["parts_per_million"]=1
        with self.assertRaises(InvalidInput):
            audit_cohort(self.p,a)
        p=copy.deepcopy(self.p)
        p["recall_min_ppm"]=200000
        with self.assertRaises(InvalidInput):
            audit_cohort(p,[])

if __name__=="__main__":
    unittest.main()
