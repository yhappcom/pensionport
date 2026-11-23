"""Synthetic source-first gold/atomic matching, independence and false GO traps.

NO actual ETF250 owner subtitles, user predictions or reviewer keys in CI.
"""
from __future__ import annotations

import base64
import copy
import json
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from ire.v6.codec import canonical, json_digest, sha256
from ire.v6.errors import InvalidInput
from ire.v6.gold_eval import MATCH_FIELDS, evaluate_atomic_gold
from ire.v6.source import parse_srt
from ire.v6.tests.test_source_and_proof import make_srt


class P205AtomicGoldTests(unittest.TestCase):
    def setUp(self):
        self.source=make_srt([
            "A synthetic ETF rule statement for official accounts.",
            "A synthetic fee and currency condition must also be respected.",
            "This example is not a confirmed ETF offer.",
            "An unrelated sign-off phrase.",
        ])
        texts=[c.text for c in parse_srt(self.source)]
        self.cue_rows=[
            {"cue_index":i,"source_quote_sha256":sha256(text.encode("utf8")),
             "status":"REVIEWED_ATOM" if i<=2 else "NO_ATOM",
             "gold_atom_ids":[f"G{i:05d}"] if i<=2 else [],
             "reason":"Adjudicated actual proposition" if i<=2 else "No separate atomic finance proposition"}
            for i,text in enumerate(texts,1)
        ]
        self.refs=[{"cue_index":i,"quote":texts[i-1]} for i in (1,2)]
        self.native={"schema":"IRE_V6_HOST_ATOMIC_EXCHANGE_V1", "atoms":[
            {"claim_id":"C00001","kind":"FACT","source_refs":[self.refs[0]],
             "proposition":"Synthetic ETF rule"},
            {"claim_id":"C00002","kind":"FACT","source_refs":[self.refs[1]],
             "proposition":"Synthetic fee condition"},
        ]}
        self.pred_raw=canonical(self.native)
        self.gold={"schema":"IRE_P205_PRIVATE_GOLD_ATOMIC_REVIEW_V1",
            "source_srt_sha256":sha256(self.source),
            "reviewed_cues":self.cue_rows,
            "atomic_gold_claims":[
               {"gold_id":"G00001","kind":"FACT","risk":"HIGH",
                "proposition":"synthetic rule","speaker_stance":"NARRATOR_PRESENTED_TEXT",
                "as_of":"HYPOTHETICAL","high_risk_reason":"FINANCIAL_RULE_CAVEAT",
                "source_refs":[self.refs[0]],"conditions":[],"exceptions":[],"numeric_evidence":[]},
               {"gold_id":"G00002","kind":"FACT","risk":"NORMAL",
                "proposition":"synthetic fee","speaker_stance":"NARRATOR_PRESENTED_TEXT",
                "as_of":"HYPOTHETICAL","high_risk_reason":"NONE",
                "source_refs":[self.refs[1]],"conditions":["currency"],
                "exceptions":[],"numeric_evidence":[]},
            ],
        }
        self.alignment={"schema":"IRE_P205_ATOMIC_ALIGNMENT_V1",
            "pairs":[{"gold_id":"G00001","claim_id":"C00001",
                      "match_dimensions":{d:True for d in MATCH_FIELDS}},
                     {"gold_id":"G00002","claim_id":"C00002",
                      "match_dimensions":{d:True for d in MATCH_FIELDS}}],
            "unmatched_gold_ids":[],"unmatched_prediction_ids":[],
        }
        self.trust={k:Ed25519PrivateKey.generate() for k in ("reviewer_one","reviewer_two","neutral_host")}
        self.plan={"schema":"IRE_P0_2_05_ETF250_PREREGISTERED_BLIND_ATOMIC_GOLD_PLAN_V1",
           "source":{"cue_count":4,"original_srt_sha256":sha256(self.source)},
           "predictions":{"frozen_v228_native_sha256":sha256(self.pred_raw),
                          "original_unapproved_atom_count":2},
           "assessment":{"thresholds":{"atomic_precision_min_bp":9500,
                       "atomic_recall_min_bp":9800,"high_risk_false_negative_max":0}},
        }

    def run_eval(self, **overrides):
        opts={"gold":self.gold,"alignment":self.alignment,"provenance":None}
        opts.update(overrides)
        return evaluate_atomic_gold(self.plan,self.source,self.pred_raw,**opts)

    def signed_attestation(self):
        keys={role:base64.b64encode(k.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw)).decode("ascii")
              for role,k in self.trust.items()}
        self.plan["trusted_attestation_public_keys"]=keys
        record={
          "schema":"IRE_P205_BLIND_TRUST_ATTESTATION_V1",
          "plan_sha256":json_digest(self.plan),
          "gold_sha256":json_digest(self.gold),
          "alignment_sha256":json_digest(self.alignment),
          "source_sha256":sha256(self.source),
          "prediction_sha256":sha256(self.pred_raw),
          "review_session_ids":["blind_review_session_one_0001","blind_review_session_two_0002"],
          "gold_frozen_at":"2026-11-23T01:00:00+00:00",
          "aligned_at":"2026-11-23T02:00:00+00:00",
          "gold_rater_disagreement_reconciled":True,
        }
        record["signatures"]={role:base64.b64encode(k.sign(canonical(record))).decode("ascii")
                              for role,k in self.trust.items()}
        return record

    def test_01_real_source_bytes_and_predictions_are_required(self):
        r=self.run_eval(gold=None,alignment=None)
        self.assertEqual(r["status"],"HOLD_NO_INDEPENDENT_ATOMIC_GOLD")
        self.assertEqual(r["frozen_prediction_atom_count"],2)
        self.assertIsNone(r["independent_recall"])
        self.assertFalse(r["ready_for_p0_2_06"])

    def test_02_original_srt_changed_rejected(self):
        with self.assertRaisesRegex(InvalidInput,"P205_SOURCE_SHA_DRIFT"):
            evaluate_atomic_gold(self.plan,self.source+b"x",self.pred_raw)

    def test_03_original_model_prediction_changed_rejected(self):
        with self.assertRaisesRegex(InvalidInput,"P205_PREDICTION_SHA_DRIFT"):
            evaluate_atomic_gold(self.plan,self.source,self.pred_raw+b" ")

    def test_04_original_pred_atom_count_wrong_rejected(self):
        self.plan["predictions"]["original_unapproved_atom_count"]=3
        with self.assertRaisesRegex(InvalidInput,"P205_PREDICTION_ATOM_CENSUS_DRIFT"):
            self.run_eval()

    def test_05_malformed_gold_schema_rejected(self):
        self.gold["schema"]="FAKE"
        with self.assertRaisesRegex(InvalidInput,"P205_GOLD_SCHEMA_INVALID"):
            self.run_eval()

    def test_06_gold_with_less_than_all_cues_remains_hold(self):
        self.gold["reviewed_cues"].pop()
        r=self.run_eval()
        self.assertEqual(r["status"],"HOLD_INCOMPLETE_GOLD_CUE_CENSUS")
        self.assertIsNone(r["independent_precision"])

    def test_07_empty_gold_claims_remains_hold(self):
        self.gold["atomic_gold_claims"]=[]
        self.assertEqual(self.run_eval()["status"],"HOLD_GOLD_ATOMIC_CLAIMS_NOT_PROVIDED")

    def test_08_unresolved_blind_cue_blocks_certification(self):
        self.cue_rows[2]["status"]="OPEN_UNCERTAIN"
        self.assertEqual(self.run_eval()["status"],"HOLD_UNRESOLVED_BLIND_GOLD_CUES")

    def test_09_missing_cue_reason_rejected(self):
        self.cue_rows[3]["reason"]=""
        with self.assertRaisesRegex(InvalidInput,"P205_GOLD_CUE_DISPOSITION_WITHOUT_REASON"):
            self.run_eval()

    def test_10_gold_wrong_cue_hash_rejected(self):
        self.cue_rows[1]["source_quote_sha256"]="0"*64
        with self.assertRaisesRegex(InvalidInput,"P205_GOLD_CUE_ORDER_OR_HASH_CHANGED"):
            self.run_eval()

    def test_11_gold_fabricated_quote_rejected(self):
        self.gold["atomic_gold_claims"][0]["source_refs"]=[{"cue_index":1,"quote":"not in cue"}]
        with self.assertRaisesRegex(InvalidInput,"P205_GOLD_SOURCE_QUOTE_NOT_VERBATIM"):
            self.run_eval()

    def test_12_missing_gold_high_risk_label_rejected(self):
        self.gold["atomic_gold_claims"][0]["risk"]="UNSURE"
        with self.assertRaisesRegex(InvalidInput,"P205_GOLD_KIND_OR_RISK_INVALID"):
            self.run_eval()

    def test_13_duplicate_gold_id_rejected(self):
        self.gold["atomic_gold_claims"][1]["gold_id"]="G00001"
        with self.assertRaisesRegex(InvalidInput,"P205_GOLD_DUPLICATE_ATOMIC_ID"):
            self.run_eval()

    def test_14_plain_all_exact_alignment_unattested_no_certified_metrics(self):
        r=self.run_eval()
        self.assertEqual((r["tp"],r["fp"],r["fn"]),(2,0,0))
        self.assertEqual(r["diagnostic_precision"],1)
        self.assertEqual(r["diagnostic_recall"],1)
        self.assertEqual(r["diagnostic_high_risk_fn"],0)
        self.assertIsNone(r["independent_precision"])
        self.assertFalse(r["e2_full_accuracy_pass"])
        self.assertFalse(r["ready_for_p0_2_06"])

    def test_15_partial_condition_costs_fp_and_fn(self):
        self.alignment["pairs"][1]["match_dimensions"]["conditions"]=False
        r=self.run_eval()
        self.assertEqual((r["tp"],r["fp"],r["fn"]),(1,1,1))
        self.assertEqual(r["diagnostic_precision"],0.5)
        self.assertEqual(r["diagnostic_recall"],0.5)
        self.assertEqual(r["diagnostic_high_risk_fn"],0)

    def test_16_missing_high_risk_gold_atom_detected(self):
        self.alignment["pairs"]=self.alignment["pairs"][1:]
        self.alignment["unmatched_gold_ids"]=["G00001"]
        self.alignment["unmatched_prediction_ids"]=["C00001"]
        r=self.run_eval()
        self.assertEqual((r["tp"],r["fp"],r["fn"]),(1,1,1))
        self.assertEqual(r["diagnostic_high_risk_fn"],1)

    def test_17_double_match_same_prediction_rejected(self):
        self.alignment["pairs"][1]["claim_id"]="C00001"
        with self.assertRaisesRegex(InvalidInput,"P205_ALIGNMENT_DUPLICATE_SOURCE_OR_TARGET"):
            self.run_eval()

    def test_18_hide_unmatched_gold_rejected(self):
        self.alignment["pairs"].pop()
        with self.assertRaisesRegex(InvalidInput,"P205_ALIGNMENT_INCOMPLETE_OR_HIDDEN_UNMATCHED_ATOMS"):
            self.run_eval()

    def test_19_forced_match_dimensions_non_boolean_rejected(self):
        self.alignment["pairs"][0]["match_dimensions"]["exceptions"]="yes"
        with self.assertRaisesRegex(InvalidInput,"P205_ALIGNMENT_SEMANTIC_DIMENSIONS_INCOMPLETE"):
            self.run_eval()

    def test_20_pair_different_source_ref_not_counted_tp(self):
        # Spoofed semantic flags cannot hide a mismatching original source cue.
        self.alignment["pairs"][0]["claim_id"]="C00002"
        self.alignment["pairs"][1]["claim_id"]="C00001"
        r=self.run_eval()
        self.assertEqual((r["tp"],r["fp"],r["fn"]),(0,2,2))
        self.assertEqual(r["diagnostic_high_risk_fn"],1)

    def test_21_forged_kind_match_not_counted_tp(self):
        self.native["atoms"][0]["kind"]="QUESTION"
        self.pred_raw=canonical(self.native)
        self.plan["predictions"]["frozen_v228_native_sha256"]=sha256(self.pred_raw)
        r=self.run_eval()
        self.assertEqual((r["tp"],r["fp"],r["fn"]),(1,1,1))
        self.assertEqual(r["diagnostic_high_risk_fn"],1)

    def test_22_three_valid_signatures_on_synthetic_do_not_allow_project_release(self):
        att=self.signed_attestation()
        r=self.run_eval(provenance=att)
        self.assertTrue(r["attestation_signatures_verified"])
        self.assertTrue(r["thresholds_met_on_supplied_data"])
        self.assertFalse(r["independent_gold_verified"])
        self.assertIsNone(r["independent_precision"])
        self.assertFalse(r["ready_for_p0_2_06"])
        self.assertFalse(r["personalized_advice_authorized"])

    def test_23_forced_signature_not_accepted(self):
        att=self.signed_attestation()
        att["signatures"]["neutral_host"]=base64.b64encode(b"0"*64).decode("ascii")
        r=self.run_eval(provenance=att)
        self.assertFalse(r["attestation_signatures_verified"])
        self.assertIn("HOLD_REVIEWER_OR_HOST_SIGNATURE_INVALID",r["status"])

    def test_24_gold_locked_after_alignment_rejected(self):
        att=self.signed_attestation()
        att["gold_frozen_at"]="2026-11-23T04:00:00+00:00"
        r=self.run_eval(provenance=att)
        self.assertEqual(r["status"],"HOLD_GOLD_NOT_LOCKED_BEFORE_ALIGNMENT")

    def test_25_review_sessions_not_distinct_rejected(self):
        att=self.signed_attestation()
        att["review_session_ids"][1]=att["review_session_ids"][0]
        r=self.run_eval(provenance=att)
        self.assertEqual(r["status"],"HOLD_REVIEW_SESSION_ISOLATION_UNPROVEN")

    def test_26_absent_trusted_key_enrolment_refuses_self_attestation(self):
        self.assertEqual(self.run_eval()["status"],"HOLD_NO_PREREGISTERED_INDEPENDENT_REVIEWER_TRUST_KEYS")

    def test_27_signatures_frozen_to_gold_digest(self):
        att=self.signed_attestation()
        self.gold["atomic_gold_claims"][0]["proposition"]="Changed after sign-off"
        r=self.run_eval(provenance=att)
        self.assertEqual(r["status"],"HOLD_GOLD_OR_ALIGNMENT_DIGEST_NOT_LOCKED")

    def test_28_no_independent_truth_in_all_open_cues(self):
        self.gold["reviewed_cues"][0]["status"]="OPEN_UNCERTAIN"
        r=self.run_eval()
        self.assertIsNone(r["independent_high_risk_false_negative_count"])



    def test_29_missing_cue_to_gold_atom_relation_is_rejected(self):
        self.cue_rows[0]['gold_atom_ids']=[]
        with self.assertRaisesRegex(InvalidInput,'P205_GOLD_TRACE_CUE_CLAIM_GRAPH_MISMATCH'):
            self.run_eval()

    def test_30_no_atom_status_cannot_hide_known_gold_claim(self):
        self.cue_rows[0]['status']='NO_ATOM'
        with self.assertRaisesRegex(InvalidInput,'P205_GOLD_TRACE_HIDDEN_CLAIM_IN_NO_ATOM_CUE'):
            self.run_eval()

    def test_31_duplicate_gold_atom_cue_references_rejected(self):
        self.gold['atomic_gold_claims'][0]['source_refs'].append(copy.deepcopy(self.refs[0]))
        with self.assertRaisesRegex(InvalidInput,'P205_GOLD_TRACE_REF_DUPLICATE_OR_OUT_OF_RANGE'):
            self.run_eval()

    def test_32_forged_cue_to_gold_atom_relation_rejected(self):
        self.cue_rows[2]['gold_atom_ids']=['G00001']
        with self.assertRaisesRegex(InvalidInput,'P205_GOLD_TRACE_CUE_CLAIM_GRAPH_MISMATCH'):
            self.run_eval()

    def test_33_duplicate_cue_link_to_gold_atom_rejected(self):
        self.cue_rows[0]['gold_atom_ids']=['G00001','G00001']
        with self.assertRaisesRegex(InvalidInput,'P205_GOLD_TRACE_CUE_GOLD_ID_LIST_INVALID'):
            self.run_eval()

    def test_34_source_cue_claim_id_mapping_is_full_and_bidirectional(self):
        report=self.run_eval()
        self.assertEqual(report['gold_traceability']['cue_count'],4)
        self.assertEqual(report['gold_traceability']['source_ref_edges'],2)
        self.assertTrue(report['gold_traceability']['traceability_valid'])
        self.assertFalse(report['gold_traceability']['independent_semantic_truth_certified'])

    def test_35_cue_link_list_missing_is_rejected(self):
        del self.cue_rows[0]['gold_atom_ids']
        with self.assertRaisesRegex(InvalidInput,'P205_GOLD_TRACE_CUE_GOLD_ID_LIST_INVALID'):
            self.run_eval()

    def test_36_gold_trace_does_not_create_independence(self):
        report=self.run_eval()
        self.assertFalse(report['independent_gold_verified'])
        self.assertIsNone(report['independent_precision'])
        self.assertFalse(report['ready_for_p0_2_06'])


    def test_37_numeric_source_unit_warnings_are_diagnostic_not_independent_gold(self):
        self.native['atoms'][0]['numeric_references']=[
            {'cue_index':1,'token':'999'},
        ]
        self.pred_raw=canonical(self.native)
        self.plan['predictions']['frozen_v228_native_sha256']=sha256(self.pred_raw)
        r=self.run_eval(gold=None,alignment=None)
        self.assertEqual(r['prediction_numeric_source_boundary_warnings'],1)
        self.assertEqual(r['prediction_numeric_source_boundary_affected_atoms'],1)
        self.assertFalse(r['prediction_numeric_source_provenance_complete'])
        self.assertIsNone(r['independent_precision'])

    def test_38_clean_synthetic_numeric_refs_do_not_pretend_independent_truth(self):
        r=self.run_eval(gold=None,alignment=None)
        self.assertEqual(r['prediction_numeric_source_boundary_warnings'],0)
        self.assertTrue(r['prediction_numeric_source_provenance_complete'])
        self.assertFalse(r['independent_gold_verified'])

    def test_39_non_string_numeric_reference_is_reported_not_crash(self):
        self.native['atoms'][0]['numeric_references']=[
            {'cue_index':1,'token':['999']},
        ]
        self.pred_raw=canonical(self.native)
        self.plan['predictions']['frozen_v228_native_sha256']=sha256(self.pred_raw)
        r=self.run_eval(gold=None,alignment=None)
        self.assertEqual(r['prediction_numeric_source_boundary_warnings'],1)
        self.assertIsNone(r['independent_high_risk_false_negative_count'])


if __name__=="__main__":unittest.main()
