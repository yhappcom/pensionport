"""Synthetic Ed25519 adversarial tests; these are NOT real reviewer identities."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from ire.v6.blind_custody import (
    PREREG_RAW_SHA256, measure_with_private_gold_custody,
    verify_private_gold_custody,
)
from ire.v6.codec import canonical, json_digest, sha256
from ire.v6.errors import InvalidInput, QualityNotProven
from ire.v6.tests import test_source_and_proof as source_fx

ROOT=Path(__file__).resolve().parents[3]
PREREG=(ROOT/"validation/ire-v6-frozen/BLIND_PREREGISTRATION_V1.json").read_bytes()
GOOD_FRAME={name:"명확" for name in (
    "modality","conditions","exceptions","measurements",
    "speaker_attribution","effective_date")}

class PrivateGoldCustodyTests(unittest.TestCase):
    def setUp(self):
        self.raw=source_fx.make_srt([
            "연금저축의 세액공제 조건은 개인별로 다릅니다.",
            "ISA 만기 금액은 연금계좌로 전환할 수 있습니다.",
            "하지만 세액공제와 적용 시점을 따로 확인해야 합니다.",
            "퇴직연금의 적용 규정은 시점에 따라 달라질 수 있습니다."])
        self.manifest=source_fx.make_manifest(self.raw)
        self.source_sha=sha256(self.raw)
        self.manifest_sha=json_digest(self.manifest)
        def claim(gid,index,category,*,pred=False):
            q=self.raw.decode("utf-8").split("\n\n")[index-1].split("\n")[-1]
            return {
               "claim_id" if pred else "gold_id":gid,
               "category":category,"proposition":q,
               "source_refs":[{"cue_index":index,"quote":q}],
               "frame":dict(GOOD_FRAME)}
        self.gold={"schema":"IRE_V6_BLIND_GOLD_V1","video_id":source_fx.VIDEO,
                   "source_sha256":self.source_sha,
                   "claims":[claim("G00001",1,"TAX"),claim("G00002",2,"PENSION")]}
        self.pred={"schema":"IRE_V6_BLIND_PREDICTIONS_V1","video_id":source_fx.VIDEO,
                   "source_sha256":self.source_sha,
                   "claims":[claim("C00001",1,"TAX",pred=True),
                             claim("C00002",2,"PENSION",pred=True)]}
        self.keys={k:Ed25519PrivateKey.generate() for k in (
            "REVIEWER_A","REVIEWER_B","ADJUDICATOR")}
        self.slot="S01"
        self.roster={"schema":"IRE_V6_EXTERNALLY_PINNED_REVIEWER_ROSTER_V1",
                     "slot":self.slot,"source_sha256":self.source_sha,
                     "manifest_sha256":self.manifest_sha,
                     "prereg_sha256":PREREG_RAW_SHA256,
                     "roles":[{"role":k,"person_id":"PERSON_"+k,
                       "ed25519_public_key_hex":self.keys[k].public_key().public_bytes(
                         encoding=serialization.Encoding.Raw,
                         format=serialization.PublicFormat.Raw).hex()} for k in self.keys]}
        self.roster_sha=json_digest(self.roster)
        self.reviewers=[]
        for k in ("REVIEWER_A","REVIEWER_B"):
            statement="SOURCE_FIRST_NO_MODEL_PREDICTIONS_SEEN_AT_SIGNING"
            r=self.gold if k=="REVIEWER_A" else copy.deepcopy(self.gold)
            message={"schema":"IRE_V6_REVIEWER_SIGNED_SOURCE_FIRST_V1",
                     "role":k,"slot":self.slot,
                     "source_sha256":self.source_sha,
                     "manifest_sha256":self.manifest_sha,
                     "prereg_sha256":PREREG_RAW_SHA256,
                     "review_document_sha256":json_digest(r),
                     "statement":statement}
            sig=self.keys[k].sign(canonical(message)).hex()
            self.reviewers.append({"role":k,"review_document":r,
                                  "statement":statement,"signature_hex":sig})
        hashes=[]
        for r in self.reviewers:
            m={"schema":"IRE_V6_REVIEWER_SIGNED_SOURCE_FIRST_V1",
               "role":r["role"],"slot":self.slot,
               "source_sha256":self.source_sha,
               "manifest_sha256":self.manifest_sha,
               "prereg_sha256":PREREG_RAW_SHA256,
               "review_document_sha256":json_digest(r["review_document"]),
               "statement":r["statement"]}
            hashes.append(json_digest({"message":m,"signature_hex":r["signature_hex"]}))
        ad_statement="SOURCE_FIRST_REVIEWER_DISPUTES_ADJUDICATED_BEFORE_PREDICTIONS"
        ad_msg={"schema":"IRE_V6_ADJUDICATOR_GOLD_SEAL_V1",
                "role":"ADJUDICATOR","slot":self.slot,
                "source_sha256":self.source_sha,
                "manifest_sha256":self.manifest_sha,
                "prereg_sha256":PREREG_RAW_SHA256,
                "trusted_roster_sha256":self.roster_sha,
                "gold_sha256":json_digest(self.gold),
                "reviewer_signed_packet_sha256s":sorted(hashes),
                "statement":ad_statement}
        self.adj={"role":"ADJUDICATOR","gold_sha256":json_digest(self.gold),
                  "reviewer_signed_packet_sha256s":sorted(hashes),
                  "statement":ad_statement,
                  "signature_hex":self.keys["ADJUDICATOR"].sign(canonical(ad_msg)).hex()}
        self.plan={"schema":"IRE_V6_BLIND_EVAL_PLAN_V1",
                   "video_id":source_fx.VIDEO,
                   "source_sha256":self.source_sha,
                   "manifest_sha256":self.manifest_sha,
                   "window_ids":[w[0] for w in
                                 source_fx.verify_source(self.raw,self.manifest,
                     expected_source_sha256=self.source_sha,
                     expected_manifest_sha256=self.manifest_sha).primary_windows],
                   "sampling_protocol":"Prospective source-first blinded held-out protocol",
                   "rubric_version":"2026-11-v1",
                   "gold_commitment_sha256":json_digest(self.gold),
                   "reviewer_protocol_sha256":PREREG_RAW_SHA256,
                   "precision_min_ppm":950000,"recall_min_ppm":900000,
                   "high_risk_recall_min_ppm":950000,
                   "gold_sealed_before_predictions":True}
        self.match={"schema":"IRE_V6_BLIND_ALIGNMENT_V1",
                    "plan_sha256":json_digest(self.plan),
                    "gold_sha256":json_digest(self.gold),
                    "predictions_sha256":json_digest(self.pred),
                    "adjudicator_id":"PERSON_ADJUDICATOR",
                    "pairs":[{"gold_id":f"G{i:05d}",
                              "predicted_id":f"C{i:05d}",
                              "verdict":"EXACT",
                              "field_verdicts":{k:"CORRECT" for k in GOOD_FRAME}}
                             for i in (1,2)],
                    "all_claims_compared":True}

    def args(self,**updates):
        d=dict(raw=self.raw,manifest=self.manifest,
               expected_source_sha256=self.source_sha,
               expected_manifest_sha256=self.manifest_sha,
               prereg_raw=PREREG,slot=self.slot,trusted_roster=self.roster,
               expected_roster_sha256=self.roster_sha,
               reviewer_packets=self.reviewers,gold=self.gold,
               adjudication_packet=self.adj)
        d.update(updates)
        return d

    def test_two_and_one_valid_digital_signatures_never_p0_go(self):
        r=verify_private_gold_custody(**self.args())
        self.assertTrue(r["cryptographic_source_scope_and_signatures_verified"])
        self.assertEqual(r["distinct_signature_keys_verified"],3)
        self.assertEqual(r["adjudicated_gold_sha256"],json_digest(self.gold))
        self.assertFalse(r["human_identity_independently_verified"])
        self.assertFalse(r["real_world_pre_prediction_chronology_verified"])
        self.assertFalse(r["independent_gold_completeness_verified"])
        self.assertFalse(r["p0_go"])

    def test_measurement_is_bound_to_signed_gold_but_still_unapproved(self):
        args=self.args()
        for name in ("gold","raw","manifest"):
            args.pop(name)
        out=measure_with_private_gold_custody(
            self.raw,self.manifest,self.plan,self.gold,self.pred,self.match,**args)
        self.assertEqual(out["counts"]["tp"],2)
        self.assertEqual(out["precision"]["parts_per_million"],1000000)
        self.assertTrue(out["cryptographic_gold_custody_receipt_sha256"])
        self.assertEqual(out["verified_signed_reviewer_keys"],3)
        self.assertFalse(out["actual_reviewer_identity_verified"])
        self.assertFalse(out["p0_go"])

    def test_reviewer_private_document_tamper_blocks_signature(self):
        p=copy.deepcopy(self.reviewers)
        p[0]["review_document"]["claims"][0]["proposition"]="가짜 내용이 추가되었습니다."
        with self.assertRaisesRegex(QualityNotProven,"SIGNATURE_MISMATCH"):
            verify_private_gold_custody(**self.args(reviewer_packets=p))

    def test_fake_gold_without_adjudicator_resigning_blocked(self):
        g=copy.deepcopy(self.gold)
        g["claims"][0]["proposition"]="위조된 금융 사실입니다."
        with self.assertRaisesRegex(InvalidInput,"PARENTAGE"):
            verify_private_gold_custody(**self.args(gold=g))

    def test_distinct_persons_are_not_sufficient_without_distinct_keys(self):
        r=copy.deepcopy(self.roster)
        r["roles"][1]["ed25519_public_key_hex"]=r["roles"][0]["ed25519_public_key_hex"]
        with self.assertRaisesRegex(InvalidInput,"KEY_CONFLICT"):
            verify_private_gold_custody(**self.args(
                trusted_roster=r,expected_roster_sha256=json_digest(r)))

    def test_signer_alias_person_blocks(self):
        r=copy.deepcopy(self.roster)
        r["roles"][1]["person_id"]=r["roles"][0]["person_id"]
        with self.assertRaisesRegex(InvalidInput,"KEY_CONFLICT"):
            verify_private_gold_custody(**self.args(
                trusted_roster=r,expected_roster_sha256=json_digest(r)))

    def test_roster_external_pin_is_mandatory(self):
        with self.assertRaisesRegex(InvalidInput,"ROSTER_SHA_OR_SCOPE"):
            verify_private_gold_custody(**self.args(expected_roster_sha256="f"*64))

    def test_duplicate_reviewer_role_fails_closed(self):
        p=copy.deepcopy(self.reviewers)
        p[1]["role"]="REVIEWER_A"
        with self.assertRaisesRegex(InvalidInput,"DUPLICATE_REVIEWER"):
            verify_private_gold_custody(**self.args(reviewer_packets=p))

    def test_adjudicator_missing_or_changed_parent_packet(self):
        a=copy.deepcopy(self.adj)
        a["reviewer_signed_packet_sha256s"][0]="0"*64
        with self.assertRaisesRegex(InvalidInput,"PARENTAGE"):
            verify_private_gold_custody(**self.args(adjudication_packet=a))

    def test_false_model_exposure_statement_rejected(self):
        p=copy.deepcopy(self.reviewers)
        p[0]["statement"]="I_SEEN_THE_PREDICTIONS"
        with self.assertRaisesRegex(InvalidInput,"UNSAFE_REVIEW"):
            verify_private_gold_custody(**self.args(reviewer_packets=p))

    def test_fake_self_approval_field_rejected(self):
        p=copy.deepcopy(self.reviewers)
        p[0]["semantic_accuracy_certified"]=True
        with self.assertRaisesRegex(InvalidInput,"REVIEW_PACKET_SCHEMA"):
            verify_private_gold_custody(**self.args(reviewer_packets=p))

    def test_adjudicator_key_signature_invalid_blocks(self):
        a=copy.deepcopy(self.adj)
        a["signature_hex"]="0"*128
        with self.assertRaisesRegex(QualityNotProven,"SIGNATURE_MISMATCH"):
            verify_private_gold_custody(**self.args(adjudication_packet=a))

    def test_cannot_swap_underlying_srt_without_repin(self):
        with self.assertRaises(InvalidInput):
            verify_private_gold_custody(**self.args(raw=self.raw+b" "))

    def test_source_first_original_public_protocol_must_be_unchanged(self):
        with self.assertRaisesRegex(InvalidInput,"PREREG_ORIGINAL_DRIFT"):
            verify_private_gold_custody(**self.args(prereg_raw=PREREG+b" "))

    def test_nine_slot_contract_rejects_tenth_slot(self):
        with self.assertRaisesRegex(InvalidInput,"SLOT_INVALID"):
            verify_private_gold_custody(**self.args(slot="S10"))

    def test_bad_prediction_alignment_still_fails(self):
        a=self.args()
        for field in ("gold","raw","manifest"):a.pop(field)
        match=copy.deepcopy(self.match)
        match["pairs"][0]["field_verdicts"]["conditions"]="INCORRECT"
        with self.assertRaises(InvalidInput):
            measure_with_private_gold_custody(
                self.raw,self.manifest,self.plan,self.gold,self.pred,match,**a)

    def test_signed_gold_source_does_not_leak_into_receipt(self):
        receipt=verify_private_gold_custody(**self.args())
        encoded=json.dumps(receipt,ensure_ascii=False)
        for item in self.gold["claims"]:
            self.assertNotIn(item["proposition"],encoded)
            self.assertNotIn(item["source_refs"][0]["quote"],encoded)
        self.assertNotIn("signature_hex",encoded)


if __name__=="__main__":
    unittest.main()
