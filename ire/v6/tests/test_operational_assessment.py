"""Operational metric tests use synthetic bytes only, not actual trials."""
import copy,unittest
from ire.v6.codec import canonical,json_digest,sha256
from ire.v6.errors import InvalidInput
from ire.v6.gold_eval import MATCH_FIELDS
from ire.v6.assessment_plan import CAMPAIGN_SCHEMA,THRESHOLDS
from ire.v6.operational_assessment import POLICY_ID,evaluate_operational_trial


class OperationalAssessmentTests(unittest.TestCase):
    def setUp(self):
        from ire.v6.tests.test_atomic_exchange import HostAtomExchangeTests
        fx=HostAtomExchangeTests();fx.setUp()
        self.addCleanup(fx.doCleanups)
        self.fx=fx
        inv,pin=fx.attest()
        self.raw=canonical(fx.exchange)
        self.plan={"schema":CAMPAIGN_SCHEMA,"campaign_id":"synthetic_operational",
                   "engine_commit_sha":"a"*40,"purpose":"HOLDOUT",
                   "registered_at":"2026-11-24T01:00:00+00:00",
                   "source":{"video_id":fx.source.video_id,"cue_count":4,
                             "original_srt_sha256":sha256(fx.raw)},
                   "predictions":{"frozen_native_sha256":sha256(self.raw),"atom_count":3},
                   "assessment":{"thresholds":copy.deepcopy(THRESHOLDS)},
                   "source_only_packet_sha256":"b"*64}
        atoms=[];cues=[];pairs=[]
        for i,c in enumerate(fx.source.cues,1):
            gid=f"G{i:05d}"
            cues.append({"cue_index":i,"source_quote_sha256":sha256(c.text.encode()),
                         "status":"REVIEWED_ATOM" if i<=3 else "NO_ATOM",
                         "gold_atom_ids":[gid] if i<=3 else [],
                         "reason":"Source reviewed for actual proposition."})
            if i>3:continue
            a=fx.exchange["atoms"][i-1]
            atoms.append({"gold_id":gid,"kind":a["kind"],"risk":"HIGH" if i==3 else "NORMAL",
                 "proposition":a["proposition"],"speaker_stance":a["stance"],"as_of":"UNSPECIFIED",
                 "high_risk_reason":"Tax applicability" if i==3 else "NONE",
                 "source_refs":a["source_refs"],"conditions":a["condition_cue_indices"],
                 "exceptions":a["exception_cue_indices"],"numeric_evidence":a["numeric_references"]})
            pairs.append({"gold_id":gid,"claim_id":a["claim_id"],
                          "match_dimensions":{k:True for k in MATCH_FIELDS}})
        self.reference={"schema":"IRE_P205_PRIVATE_GOLD_ATOMIC_REVIEW_V1",
                        "source_srt_sha256":sha256(fx.raw),"reviewed_cues":cues,"atomic_gold_claims":atoms}
        self.alignment={"schema":"IRE_P205_ATOMIC_ALIGNMENT_V1","pairs":pairs,
                        "unmatched_gold_ids":[],"unmatched_prediction_ids":[]}
        self.review={"schema":"IRE_P205_INTERNAL_TWO_TURN_REVIEW_V1","policy_id":POLICY_ID,
                    "cohort_sha256":"c"*64,"domain":"PENSION","selection_sha256":"d"*64,
                    "turn1_user_ref":"synthetic first user turn","turn2_user_ref":"synthetic second user turn",
                    "prediction_frozen_at":"2026-11-24T02:00:00+00:00",
                    "turn2_at":"2026-11-24T03:00:00+00:00",
                    "reference_frozen_at":"2026-11-24T04:00:00+00:00",
                    "aligned_at":"2026-11-24T05:00:00+00:00",
                    "reference_sha256":json_digest(self.reference),"alignment_sha256":json_digest(self.alignment),
                    "alignment_reasons":{p["gold_id"]+":"+p["claim_id"]:"Explicit comparison of all source axes." for p in pairs},
                    "unmatched_reasons":{},"high_risk_reviews":{"G00003":{
                        "disposition":"QUARANTINE_PENDING_E3","reason":"Official rule applicability not yet resolved.",
                        "evidence_sha256":"e"*64}}}
        self.args=dict(manifest=fx.manifest,inventory_bytes=inv,expected_inventory_sha256=pin,
                       reference=self.reference,alignment=self.alignment,review=self.review)

    def run_trial(self):
        return evaluate_operational_trial(self.plan,self.fx.raw,self.raw,**self.args)

    def relock(self):
        self.review.update(reference_sha256=json_digest(self.reference),
                           alignment_sha256=json_digest(self.alignment))

    def test_internal_positive_is_not_independent_or_publication(self):
        r=self.run_trial()
        self.assertEqual((r["tp"],r["fp"],r["fn"]),(3,0,0))
        self.assertTrue(r["internal_thresholds_met"])
        self.assertFalse(r["independent_gold_verified"])
        self.assertIsNone(r["independent_precision"])
        self.assertFalse(r["research_publication_authorized"])

    def test_numeric_and_condition_mismatches_fail(self):
        for axis in ("numeric_value_and_unit","conditions","exceptions"):
            self.alignment["pairs"][0]["match_dimensions"][axis]=False
            self.relock()
            r=self.run_trial()
            self.assertFalse(r["internal_thresholds_met"])
            self.assertEqual(r["critical_pair_mismatches"],1)
            self.alignment["pairs"][0]["match_dimensions"][axis]=True

    def test_high_risk_missed_fails(self):
        p=self.alignment["pairs"].pop()
        self.alignment["unmatched_gold_ids"]=[p["gold_id"]]
        self.alignment["unmatched_prediction_ids"]=[p["claim_id"]]
        del self.review["alignment_reasons"][p["gold_id"]+":"+p["claim_id"]]
        self.review["unmatched_reasons"]={"reference:"+p["gold_id"]:"Unmatched source proposition.",
                                           "prediction:"+p["claim_id"]:"Unmatched native proposition."}
        self.relock()
        r=self.run_trial()
        self.assertEqual(r["high_risk_fn"],1)
        self.assertFalse(r["internal_thresholds_met"])

    def test_open_reference_rejected_not_a_score(self):
        self.reference["reviewed_cues"][0]["status"]="OPEN_UNCERTAIN"
        self.relock()
        with self.assertRaisesRegex(InvalidInput,"INCOMPLETE_INTERNAL_REFERENCE"):self.run_trial()

    def test_distinct_turn_and_reference_lock_required(self):
        self.review["turn2_user_ref"]=self.review["turn1_user_ref"]
        with self.assertRaisesRegex(InvalidInput,"DISTINCT_USER_TURNS"):self.run_trial()
        self.review["turn2_user_ref"]="different second user message"
        self.review["aligned_at"]=self.review["reference_frozen_at"]
        with self.assertRaisesRegex(InvalidInput,"FREEZE_ORDER"):self.run_trial()

    def test_missing_risk_disposition_and_pair_reason(self):
        del self.review["high_risk_reviews"]["G00003"]
        with self.assertRaisesRegex(InvalidInput,"NONVACUOUS_HIGH_RISK_CENSUS"):self.run_trial()
        del self.review["alignment_reasons"]["G00001:C00001"]
        with self.assertRaisesRegex(InvalidInput,"PAIR_REASONS_INCOMPLETE"):self.run_trial()

    def test_source_and_prediction_cannot_be_replaced(self):
        self.raw=self.raw+b" "
        with self.assertRaises(InvalidInput):self.run_trial()
