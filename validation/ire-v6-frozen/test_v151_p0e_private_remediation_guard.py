"""Synthetic negative tests for V151. Never use synthesized cues as live proof."""
from __future__ import annotations
import copy
import hashlib
import unittest

from v151_p0e_private_remediation_guard import (
    V151RemediationError, audit_public_hold_receipt,
    verify_private_cue_partition, verify_provisional_seam
)

def h(s):
    return hashlib.sha256(s.encode()).hexdigest()

class V151P0ERemediationTest(unittest.TestCase):
    def setUp(self):
        self.r = {
            "schema": "V151_PRIVATE_SOURCE_REMEDIATION_SUMMARY_V1",
            "video_id": "5NvtBlmt93Y", "source_sha256": h("source"),
            "change_sha256": h("changes"), "237_cue_triage_sha256": h("237"),
            "202_claim_lineage_sha256": h("202"), "seam_sha256": h("seam"),
            "new_b0012_exchange_sha256": h("B12"),
            "new_b0013_exchange_sha256": h("B13"),
            "original_cue_count": 1481, "old_v145_atoms": 274,
            "prior_unreferenced_count": 254, "v150_reviewed_cues": 17,
            "v151_remaining_screened": 237,
            "v151_pending_semantic_gold_cues": 237,
            "prior_pending_claims": 202,
            "v151_pending_claims_structurally_verified": 202,
            "v151_pending_claims_semantically_approved": 0,
            "existing_v123_final_approved_scopes": 0,
            "v128_new_publication_count": 0, "draft_correction_count": 7,
            "revised_segment_atoms": {"B0012": 17, "B0013": 6},
            "new_claim_ids": ["C00275", "C00276"],
            "status": "PRIVATE_SOURCE_FIRST_DRAFT_CORRECTIONS_REPLAY_HOLD_NO_APPROVAL",
            "host_v6_exchange_reissued": False,
            "chat_final_semantic_review_all_13_completed": False,
            "current_law_individual_application_approved": False,
            "full_video_precision_measured": False,
            "full_video_recall_measured": False,
            "externally_independent_gold": False,
            "p0e_go": False, "p0_go": False,
        }

    def test_01_actual_status_remains_hold(self):
        result = audit_public_hold_receipt(self.r)
        self.assertFalse(result["p0e_go"])
        self.assertEqual(result["source_cues_partition_screened"], 254)
        self.assertEqual(result["prior_pending_claims_structurally_reconciled"], 202)

    def test_02_false_go_is_blocked(self):
        d=copy.deepcopy(self.r);d["p0_go"]=True
        with self.assertRaisesRegex(V151RemediationError,"FALSE_COMPLETION"):
            audit_public_hold_receipt(d)

    def test_03_false_semantic_approval_is_blocked(self):
        d=copy.deepcopy(self.r);d["v151_pending_claims_semantically_approved"]=202
        with self.assertRaisesRegex(V151RemediationError,"COUNT_"):
            audit_public_hold_receipt(d)

    def test_04_missing_split_is_blocked(self):
        d=copy.deepcopy(self.r);d["new_claim_ids"].pop()
        with self.assertRaisesRegex(V151RemediationError,"ATOMIC_SPLITS"):
            audit_public_hold_receipt(d)

    def test_05_hash_pinning_is_required(self):
        d=copy.deepcopy(self.r);d["seam_sha256"]="not-a-digest"
        with self.assertRaisesRegex(V151RemediationError,"SHA"):
            audit_public_hold_receipt(d)

    def test_06_237_partition_proves_only_source(self):
        cues={i: f"test cue {i}" for i in range(1,1482)}
        queue=[{"cue_index":i,"original_text":cues[i],
                "source_text_sha256":h(cues[i])} for i in range(1,255)]
        first=[{"cue_index":i} for i in range(1,18)]
        rest=[{"cue_index":i,"source_text_sha256":h(cues[i]),
               "semantic_gold_finalized":False,"pending_v123":True,
               "possible_false_negative_not_certified":True}
              for i in range(18,255)]
        result=verify_private_cue_partition(queue,first,rest,cues)
        self.assertFalse(result["final_semantic_certified"])
        rest[-1]["semantic_gold_finalized"]=True
        with self.assertRaisesRegex(V151RemediationError,"TRIAGE_MASQUERADES"):
            verify_private_cue_partition(queue,first,rest,cues)

    @staticmethod
    def fixture_seam():
        cues={i: f"synthetic cue {i}" for i in range(1321,1482)}
        b12={"schema":"IRE_V6_HOST_ATOMIC_EXCHANGE_V1","video_id":"5NvtBlmt93Y",
             "source_sha256":h("test source"),"atoms":[],"cue_dispositions":[]}
        b13=copy.deepcopy(b12)
        def add(packet,cid,indices,stance="UNRESOLVED",kind="OPINION",conds=None):
            packet["atoms"].append({
                "claim_id":cid,"source_refs":[{"cue_index":i,"quote":cues[i]} for i in indices],
                "kind":kind,"stance":stance,"condition_cue_indices":conds or [],
                "context_cue_indices":indices})
        add(b12,"C00261",list(range(1377,1384)))
        add(b12,"C00276",list(range(1384,1388)))
        add(b12,"C00262",list(range(1388,1391)))
        add(b12,"C00268",list(range(1429,1437)))
        add(b12,"C00269",[1437,1438],stance="QUOTED",kind="RECOMMENDATION")
        add(b13,"C00270",[1441,1442])
        add(b13,"C00275",[1443,1444,1445,1446],stance="CONDITIONAL",conds=[1444,1445])
        add(b13,"C00271",[1446,1447,1448])
        # Pad with disjoint test atoms, not research claims.
        for j in range(12):add(b12,f"C01{j:03d}",[1321+j])
        for j in range(3):add(b13,f"C02{j:03d}",[1465+j])
        for pkt,lo,hi in ((b12,1321,1440),(b13,1441,1481)):
            by={}
            for atom in pkt["atoms"]:
                for ref in atom["source_refs"]:
                    by.setdefault(ref["cue_index"],set()).add(atom["claim_id"])
            for i in range(lo,hi+1):
                ids=sorted(by.get(i,set()))
                pkt["cue_dispositions"].append({
                    "cue_index":i,"disposition":"CANDIDATES" if ids else "UNRESOLVED",
                    "claim_ids":ids,"cue_text_sha256":h(cues[i]),"note":"synthetic",
                    "numeric_tokens":[]})
        return b12,b13,cues

    def test_07_seam_split_guard_and_source_quote(self):
        a,b,cues=self.fixture_seam()
        r=verify_provisional_seam(a,b,cues)
        self.assertFalse(r["p0e_go"])
        a["atoms"][4]["source_refs"].append({"cue_index":1440,"quote":cues[1440]})
        with self.assertRaisesRegex(V151RemediationError,"MISATTRIBUTED"):
            verify_provisional_seam(a,b,cues)

    def test_08_merged_risk_atom_is_rejected(self):
        a,b,cues=self.fixture_seam()
        b["atoms"]=[x for x in b["atoms"] if x["claim_id"]!="C00275"]
        with self.assertRaisesRegex(V151RemediationError,"MANDATORY_ATOM"):
            verify_provisional_seam(a,b,cues)

    def test_09_quote_forgery_rejected(self):
        a,b,cues=self.fixture_seam()
        b["atoms"][0]["source_refs"][0]["quote"]="fake invented text"
        with self.assertRaisesRegex(V151RemediationError,"QUOTE_NOT_FROM"):
            verify_provisional_seam(a,b,cues)

if __name__=="__main__":
    unittest.main()
