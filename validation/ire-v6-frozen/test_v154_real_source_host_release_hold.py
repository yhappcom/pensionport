"""Synthetic negative controls for V154 real owner replay summary.

No owner SRT or private model/meaning content is present in public CI.
"""
import copy
import json
import unittest
from pathlib import Path

from v154_real_source_host_release_hold import (
    V154InvalidReleaseEvidence,audit_v154_public_owner_replay_hold
)

MANIFEST=Path(__file__).with_name("V154_REAL_ONE_TURN_OWNER_REPLAY_SHA_ONLY.json")


class V154PublicOwnerReplayTest(unittest.TestCase):
    def setUp(self):
        self.r=json.loads(MANIFEST.read_text(encoding="utf-8"))

    def wrong(self,field,value,reason):
        x=copy.deepcopy(self.r);x[field]=value
        with self.assertRaisesRegex(V154InvalidReleaseEvidence,reason):
            audit_v154_public_owner_replay_hold(x)

    def test_01_real_source_host_structural_still_hold(self):
        out=audit_v154_public_owner_replay_hold(self.r)
        self.assertEqual(out["real_original_source_scopes_native_host_structural_committed"],13)
        self.assertEqual(out["v123_real_final_pass_scopes"],0)
        self.assertFalse(out["p0e_go"])

    def test_02_108_must_reconcile(self):
        self.wrong("original_108_cue_remaining_unresolved",0,"REAL_REPLAY_CENSUS")

    def test_03_cannot_create_fake_host_receipts(self):
        self.wrong("native_v6_host_batches_committed",14,"REAL_REPLAY_CENSUS")

    def test_04_cannot_claim_v123_final_pass(self):
        self.wrong("v123_real_chat_final_pass",13,"REAL_REPLAY_CENSUS")

    def test_05_cannot_claim_v128_parent_commit(self):
        self.wrong("v128_approved_knowledge_publications",1,"REAL_REPLAY_CENSUS")

    def test_06_cannot_claim_high_risk_FN_zero(self):
        self.wrong("zero_high_risk_false_negatives_certified",True,"FALSE_RESEARCH_APPROVAL")

    def test_07_cannot_claim_95_98_gold(self):
        self.wrong("precision_95_recall_98_certified",True,"FALSE_RESEARCH_APPROVAL")

    def test_08_owner_signing_not_proven(self):
        self.wrong("operator_derived_owner_inventory_not_independently_attested",False,"OWNER_PROVENANCE")

    def test_09_cannot_claim_personal_advice(self):
        self.wrong("real_v128_approved_knowledge_based_advice_tested",True,"FALSE_RESEARCH_APPROVAL")

    def test_10_private_owner_file_sha_pin_required(self):
        x=copy.deepcopy(self.r);x["private_file_sha256"]["native_host_13_receipts"]="0"
        with self.assertRaisesRegex(V154InvalidReleaseEvidence,"PRIVATE_SHA_CENSUS"):
            audit_v154_public_owner_replay_hold(x)

if __name__=="__main__":
    unittest.main()
