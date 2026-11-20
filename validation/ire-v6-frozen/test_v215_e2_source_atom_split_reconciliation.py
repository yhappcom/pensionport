"""V215 E2 atomic meaning split / visual quarantine, synthetic CI only."""
from __future__ import annotations

import copy
import json
import unittest

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import parse_srt
from ire.v6.atomic_exchange import audit_host_atomic_exchange
from v176_chat_engine_loop import make_original_plan
from test_v210_e2_private_original_source_inventory import RAW, synthetic
from v214_e2_real_srt_provisional_native_v6 import construct_provisional_native_v6
from v215_e2_source_atom_split_reconciliation import (
    SCHEMA,reconcile_private_native_source_splits,
)


class TestV215RealNativeReconciling(unittest.TestCase):
    def setUp(self):
        self.inventory=synthetic()
        self.v210=self.dumps(self.inventory)
        self.native,self.base_receipt=construct_provisional_native_v6(
            RAW,self.inventory,expected_source_sha256=sha256(RAW),
            private_v210_source_bytes=self.v210,
            expected_v210_source_sha256=sha256(self.v210),window_size=2)
        self.v214=self.dumps(self.native)
        cues=parse_srt(RAW)

        def patchrow(n,i,kind,prop):
            original=cues[i-1].text
            return {
                "source_split_id":f"E215SRC-{n:03d}",
                "from_v210_provisional_id":"E2REAL-001",
                "cue_indices":[i],
                "exact_original_quotes":[{"cue_index":i,"quote":original,
                   "source_text_sha256":sha256(original.encode("utf-8"))}],
                "kind":kind,"proposition_unverified":prop,
                "reviewer_rationale":
                  "원본 자막의 서로 다른 금융 서술을 분리하며 확정 사실이 아닌 미승인 원자로 남깁니다.",
                "semantic_risks":["UNAPPROVED_REVIEW"],
                "speaker_audio_verified":False,"final_stance_certified":False,
                "financial_fact_approved":False,
                "independent_gold_certified":False,
                "e2_final_pass":False,"e3_e4_e5_authorized":False,
            }
        self.patch={
            "schema":SCHEMA,
            "video_id":"Synth123456","source_sha256":sha256(RAW),
            "v210_original_bytes_sha256":sha256(self.v210),
            "v214_previous_native_bytes_sha256":sha256(self.v214),
            "replaced_parent_ids":["E2REAL-001"],
            "previously_blocked_source_maths_recovered_as_spoken_premises":[],
            "video_only_parent_ids_held":[],
            "new_source_only_atomic_candidates":[
                patchrow(1,1,"FACT","ETF는 펀드의 일종이라는 설명"),
                patchrow(2,2,"QUESTION","ISA에서 연 8% 수익을 보장하는지 묻는 질문"),
            ],
            "equivalence_review_is_internal_chat_only":True,
            "audio_screen_evidence_unavailable":True,
            "old_v176_owner_absent":True,
            "independent_gold_certified":False,"financial_facts_approved":False,
            "e2_final_pass":False,"e3_e4_e5_authorized":False,
            "knowledge_written":False,
        }

    @staticmethod
    def dumps(obj):
        return (json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode("utf-8")

    def run_patch(self,patch=None,v210=None,v214=None,source=RAW,
                  v210_bytes=None,v214_bytes=None,patch_bytes=None,
                  expected_patch_sha=None):
        patch=self.patch if patch is None else patch
        v210=self.inventory if v210 is None else v210
        v214=self.native if v214 is None else v214
        x=self.dumps(v210) if v210_bytes is None else v210_bytes
        y=self.dumps(v214) if v214_bytes is None else v214_bytes
        z=self.dumps(patch) if patch_bytes is None else patch_bytes
        return reconcile_private_native_source_splits(
            source,v210,v214,patch,expected_source_sha256=sha256(RAW),
            v210_original_bytes=x,expected_v210_bytes_sha256=sha256(self.v210),
            v214_original_bytes=y,expected_v214_bytes_sha256=sha256(self.v214),
            patch_original_bytes=z,
            expected_patch_bytes_sha256=(
                sha256(z) if expected_patch_sha is None else expected_patch_sha),
            window_size=2,
        )

    def test_01_native_frozen_2_to_3_atomic_split_is_source_checked(self):
        ex,r=self.run_patch()
        src,_=make_original_plan(RAW,"Synth123456",
                  expected_source_sha256=sha256(RAW),window_size=2)
        self.assertEqual(audit_host_atomic_exchange(src,ex)["proposed_atomic_claims"],3)
        self.assertEqual(r["baseline_native_unapproved_atoms"],2)
        self.assertEqual(r["parent_native_atoms_replaced"],1)
        self.assertEqual(r["new_source_anchored_atomic_children"],2)
        self.assertEqual(r["native_v6_unapproved_atoms_after_reconciliation"],3)
        self.assertEqual([x["claim_id"] for x in ex["atoms"]],
                         ["C00002","C00003","C00004"])
        self.assertEqual(ex["atoms"][-1]["kind"],"QUESTION")
        self.assertEqual(ex["atoms"][-1]["speaker"],"UNKNOWN")
        self.assertEqual(ex["atoms"][-1]["stance"],"UNRESOLVED")
        self.assertFalse(r["e2_final_pass"])
        self.assertFalse(r["historical_v176_owner_replayed"])

    def test_02_unspoken_math_cannot_be_mapped_to_native_fact(self):
        bad=copy.deepcopy(self.patch)
        bad["new_source_only_atomic_candidates"][0]["proposition_unverified"]+=" 99% 보장"
        with self.assertRaisesRegex(InvalidInput,
                                    "MATH_OR_NUMBER_NOT_SPOKEN_IN_SOURCE"):
            self.run_patch(patch=bad)

    def test_03_wrong_original_quote_is_not_a_source_proof(self):
        bad=copy.deepcopy(self.patch)
        bad["new_source_only_atomic_candidates"][0]["exact_original_quotes"][0]["quote"]="보장된 99%"
        with self.assertRaisesRegex(InvalidInput,"SOURCE_QUOTE_SHA_MISMATCH"):
            self.run_patch(patch=bad)

    def test_04_wrong_source_bytes_rejected_before_source_audit(self):
        with self.assertRaisesRegex(InvalidInput,"SOURCE_BYTES_CHANGED"):
            self.run_patch(source=RAW+b" ")

    def test_05_changed_prior_v210_bytes_are_fail_closed(self):
        with self.assertRaisesRegex(InvalidInput,
                                    "V210_ORIGINAL_BYTES_TAMPERED"):
            self.run_patch(v210_bytes=self.v210+b" ")

    def test_06_changed_prior_native_bytes_are_fail_closed(self):
        with self.assertRaisesRegex(InvalidInput,
                                    "V214_ORIGINAL_BYTES_TAMPERED"):
            self.run_patch(v214_bytes=self.v214+b" ")

    def test_07_wrong_patch_sha_is_fail_closed(self):
        with self.assertRaisesRegex(InvalidInput,
                                    "PATCH_ORIGINAL_BYTES_TAMPERED"):
            self.run_patch(expected_patch_sha="f"*64)

    def test_08_reviewer_can_never_claim_external_gold(self):
        for k in ("independent_gold_certified","financial_facts_approved",
                  "e2_final_pass","e3_e4_e5_authorized","knowledge_written"):
            bad=copy.deepcopy(self.patch)
            bad[k]=True
            with self.assertRaisesRegex(InvalidInput,
                                        "PATCH_SOURCE_OR_APPROVAL_SCHEMA"):
                self.run_patch(patch=bad)

    def test_09_claim_source_outside_original_parent_neighborhood_rejected(self):
        bad=copy.deepcopy(self.patch)
        item=bad["new_source_only_atomic_candidates"][1]
        item["cue_indices"]=[4]
        item["exact_original_quotes"]=[{
            "cue_index":4,
            "quote":"감사합니다.",
            "source_text_sha256":sha256("감사합니다.".encode("utf-8"))}]
        with self.assertRaisesRegex(InvalidInput,
                                    "SOURCE_SPLIT_OUTSIDE_ORIGINAL_PARENT_NEIGHBORHOOD"):
            self.run_patch(patch=bad)

    def test_10_missing_original_atomic_child_is_not_silent(self):
        bad=copy.deepcopy(self.patch)
        bad["new_source_only_atomic_candidates"].pop()
        with self.assertRaisesRegex(InvalidInput,
                                    "MISSING_SPLIT_CHILDREN_FOR_PARENT"):
            self.run_patch(patch=bad)

    def test_11_video_quarantine_without_visual_evidence_risk_rejected(self):
        bad=copy.deepcopy(self.patch)
        bad["video_only_parent_ids_held"]=["E2REAL-002"]
        with self.assertRaisesRegex(InvalidInput,
                                    "VISUAL_HOLD_WITHOUT_DOCUMENTED_SOURCE_RISK"):
            self.run_patch(patch=bad)

    def test_12_case_with_old_parent_not_marked_as_new_external_owner(self):
        ex,r=self.run_patch()
        self.assertFalse(r["historical_v176_owner_replayed"])
        self.assertFalse(r["historical_v179_owner_atom_equivalence_complete"])
        self.assertFalse(r["independent_gold_precision_recall_measured"])
        self.assertFalse(r["financial_truth_gold_certified"])
        self.assertFalse(r["speaker_stance_audio_verified"])
        self.assertFalse(r["knowledge_published"])
        self.assertNotIn("quote",str(r))

    def test_13_forged_audio_verification_never_passes(self):
        bad=copy.deepcopy(self.patch)
        bad["new_source_only_atomic_candidates"][0]["speaker_audio_verified"]=True
        with self.assertRaisesRegex(InvalidInput,"SOURCE_SPLIT_ROW_INPUT_INVALID"):
            self.run_patch(patch=bad)

    def test_14_duplicate_original_cue_in_child_not_allowed(self):
        bad=copy.deepcopy(self.patch)
        p=bad["new_source_only_atomic_candidates"][0]
        p["cue_indices"]=[1,1]
        p["exact_original_quotes"].append(copy.deepcopy(p["exact_original_quotes"][0]))
        with self.assertRaisesRegex(InvalidInput,"SOURCE_SPLIT_ROW_INPUT_INVALID"):
            self.run_patch(patch=bad)

    def test_15_private_byte_hash_is_replayable_without_mutation(self):
        a,r=self.run_patch()
        b,s=self.run_patch()
        self.assertEqual(a,b)
        self.assertEqual(r,s)

    def test_16_malformed_parent_type_fails_without_typeerror(self):
        bad=copy.deepcopy(self.patch)
        bad["new_source_only_atomic_candidates"][0]["from_v210_provisional_id"]=[]
        with self.assertRaisesRegex(InvalidInput,"SOURCE_SPLIT_ROW_INPUT_INVALID"):
            self.run_patch(patch=bad)


if __name__=="__main__":
    unittest.main()
