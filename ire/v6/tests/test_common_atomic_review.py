"""Common review contract tests: synthetic only, no owner source."""
import copy, unittest
from ire.v6.codec import canonical,json_digest,sha256
from ire.v6.errors import InvalidInput
from ire.v6.common_atomic_review import source_packet,compile_review,check_exact_typed_axes,RUBRIC_SHA256
from ire.v6.assessment_plan import CAMPAIGN_SCHEMA,THRESHOLDS
from ire.v6.gold_eval import MATCH_FIELDS
from ire.v6.operational_assessment import POLICY_ID,evaluate_common_operational_trial
from ire.v6.source import verify_source
from ire.v6.tests.test_source_and_proof import make_srt,make_manifest

class CommonAtomicReviewTests(unittest.TestCase):
    def setUp(self):
        self.raw=make_srt(["연금 원금 300만 원만 인출합니다.","해당 자격을 충족한 경우에 한합니다.",
                           "세금 계산은 별도입니다.","오늘 교육을 마칩니다."])
        self.manifest=make_manifest(self.raw)
        self.src=verify_source(self.raw,self.manifest,expected_source_sha256=sha256(self.raw),
                               expected_manifest_sha256=json_digest(self.manifest))
        self.inventory=canonical({"schema":"IRE_V6_OWNER_INVENTORY_V1","entries":[{
            "video_id":self.src.video_id,"source_sha256":self.src.source_sha256,
            "manifest_sha256":self.src.manifest_sha256,"cue_census_sha256":self.src.cue_census_sha256}]})
        f={"proposition":"연금 원금 300만 원을 인출합니다.","kind":"FACT",
           "source_refs":[{"cue_index":1,"quote":self.src.cues[0].text}],
           "context_cue_indices":[1,2],"condition_cue_indices":[2],"exception_cue_indices":[],
           "numeric_references":[{"cue_index":1,"token":"300만 원"}],"as_of":None,
           "role":"NARRATOR","attribution":"DIRECT","polarity":"AFFIRMED","modality":"CONDITIONAL",
           "correction":False,"meaning_reason":"A conditional withdrawal assertion."}
        g=copy.deepcopy(f);g.update(proposition="세금 계산은 별도입니다.",kind="FACT",
            source_refs=[{"cue_index":3,"quote":self.src.cues[2].text}],context_cue_indices=[3],
            condition_cue_indices=[],numeric_references=[],modality="ASSERTED",
            meaning_reason="A separate tax calculation assertion.")
        u={"subject":"연금 원금","predicate":"인출","object":"300만 원","atomicity_reason":"One independently testable claim."}
        self.first={"schema":"IRE_COMMON_ATOMIC_REVIEW_V2",
              "source_packet_sha256":json_digest(source_packet(self.src)),
              "atoms":[{"frame":f,"unit":u,"qualifiers":[{"type":"CONDITION","cue_index":2,
                          "quote":self.src.cues[1].text,"reason":"Condition governs withdrawal."}],
                        "risk":"HIGH","risk_reason":"Withdrawal applicability is material."},
                       {"frame":g,"unit":{"subject":"세금","predicate":"별도 계산","object":"세액",
                        "atomicity_reason":"Separately assessable assertion."},"qualifiers":[],
                        "risk":"NORMAL","risk_reason":"No specific tax rule asserted."}],
              "cue_reviews":[{"cue_index":i,"cue_text_sha256":sha256(c.text.encode()),
                    "status":s,"reason":"Explicit source review disposition."}
                    for i,(c,s) in enumerate(zip(self.src.cues,["DIRECT","CONTEXT","DIRECT","NONCLAIM"]),1)]}
        self.second=copy.deepcopy(self.first)
        self.second["atoms"][0]["frame"]["meaning_reason"]="Second review found same conditional withdrawal."
        self.alignment={"schema":"IRE_P205_ATOMIC_ALIGNMENT_V1",
            "pairs":[{"gold_id":f"G{i:05d}","claim_id":f"C{i:05d}",
                      "match_dimensions":{k:True for k in MATCH_FIELDS}} for i in (1,2)],
            "unmatched_gold_ids":[],"unmatched_prediction_ids":[]}

    def compile(self,p=None):return compile_review(self.src,self.first if p is None else p)

    def test_same_compiler_preserves_role_qualifiers_and_cue_links(self):
        a=self.compile();b=self.compile(self.second)
        self.assertEqual(a["exchange"],b["exchange"])
        self.assertEqual(a["reference"],b["reference"])
        self.assertNotEqual(a["packet_sha256"],b["packet_sha256"])
        self.assertEqual(a["reference"]["atomic_gold_claims"][0]["conditions"][0]["cue_index"],2)
        self.assertEqual(a["reference"]["reviewed_cues"][1]["status"],"NO_ATOM")
        self.assertFalse(a["independent_gold_verified"])
        check_exact_typed_axes(a,b,self.alignment)

    def test_condition_cannot_be_silently_dropped(self):
        self.first["atoms"][0]["qualifiers"]=[]
        with self.assertRaisesRegex(InvalidInput,"QUALIFIER_GRAPH"):self.compile()

    def test_wrong_qualifier_quote_rejected(self):
        self.first["atoms"][0]["qualifiers"][0]["quote"]="Not in original"
        with self.assertRaisesRegex(InvalidInput,"QUALIFIER_EDGE"):self.compile()

    def test_context_cannot_be_hidden_as_nonclaim(self):
        self.first["cue_reviews"][1]["status"]="NONCLAIM"
        with self.assertRaisesRegex(InvalidInput,"CUE_LINK"):self.compile()

    def test_number_from_unrelated_context_rejected(self):
        f=self.first["atoms"][1]["frame"]
        f["context_cue_indices"]=[1,3];f["numeric_references"]=[{"cue_index":1,"token":"300만 원"}]
        with self.assertRaisesRegex(InvalidInput,"NUMERIC_NOT_IN_GOVERNING_QUOTE"):self.compile()

    def test_question_and_reported_role_are_not_silent_exact(self):
        self.second["atoms"][0]["frame"]["attribution"]="REPORTED"
        a=self.compile();b=self.compile(self.second)
        with self.assertRaisesRegex(InvalidInput,"FALSE_TYPED_ROLE_MATCH"):
            check_exact_typed_axes(a,b,self.alignment)
        self.alignment["pairs"][0]["match_dimensions"]["speaker_and_stance"]=False
        check_exact_typed_axes(a,b,self.alignment)

    def test_full_two_packet_evaluator_and_copy_rejection(self):
        a=self.compile();b=self.compile(self.second);prediction=canonical(a["exchange"])
        plan={"schema":CAMPAIGN_SCHEMA,"campaign_id":"synthetic_common",
            "engine_commit_sha":"a"*40,"purpose":"HOLDOUT","registered_at":"2026-11-24T01:00:00+00:00",
            "source":{"video_id":self.src.video_id,"cue_count":4,"original_srt_sha256":sha256(self.raw)},
            "predictions":{"frozen_native_sha256":sha256(prediction),"atom_count":2},
            "assessment":{"thresholds":THRESHOLDS},"source_only_packet_sha256":json_digest(source_packet(self.src))}
        review={"schema":"IRE_P205_INTERNAL_TWO_TURN_REVIEW_V1","policy_id":POLICY_ID,
            "cohort_sha256":"b"*64,"domain":"PENSION","selection_sha256":"c"*64,
            "turn1_user_ref":"synthetic first message","turn2_user_ref":"synthetic second message",
            "prediction_frozen_at":"2026-11-24T02:00:00+00:00","turn2_at":"2026-11-24T03:00:00+00:00",
            "reference_frozen_at":"2026-11-24T04:00:00+00:00","aligned_at":"2026-11-24T05:00:00+00:00",
            "reference_sha256":json_digest(b["reference"]),"alignment_sha256":json_digest(self.alignment),
            "alignment_reasons":{f"G{i:05d}:C{i:05d}":"Explicit reviewed semantic agreement." for i in (1,2)},
            "unmatched_reasons":{},"high_risk_reviews":{"G00001":{"disposition":"QUARANTINE_PENDING_E3",
                "reason":"Official applicability remains pending.","evidence_sha256":"d"*64}}}
        lock={"rubric_sha256":RUBRIC_SHA256,"first_packet_sha256":a["packet_sha256"],
              "second_packet_sha256":b["packet_sha256"]}
        args=dict(manifest=self.manifest,inventory_bytes=self.inventory,
              expected_inventory_sha256=sha256(self.inventory),first_packet=self.first,second_packet=self.second,
              alignment=self.alignment,review=review,rubric_lock=lock)
        r=evaluate_common_operational_trial(plan,self.raw,prediction,**args)
        self.assertTrue(r["internal_thresholds_met"]);self.assertEqual(r["tp"],2)
        self.assertTrue(r["common_typed_review_replayed"]);self.assertIsNone(r["independent_precision"])
        self.assertFalse(r["research_publication_authorized"])
        lock["second_packet_sha256"]=a["packet_sha256"];args["second_packet"]=self.first
        with self.assertRaisesRegex(InvalidInput,"COMMON_COPIED_PACKET"):
            evaluate_common_operational_trial(plan,self.raw,prediction,**args)
