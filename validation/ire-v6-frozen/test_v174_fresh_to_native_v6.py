"""Synthetic regression: production converter uses genuine frozen V6 auditors.
No owner SRT or substantive ChatGPT judgment is committed to GitHub.
"""
from __future__ import annotations
from copy import deepcopy
import unittest

from ire.v6.codec import json_digest,sha256
from ire.v6.errors import InvalidInput
from v174_fresh_to_native_v6 import compile_fresh_native_v6

VIDEO="AbCdEf12345"
TEXT=["The investment target is 10% per year",
      "A related condition must be discussed",
      "The book recounts an example",
      "A closing anecdote about the book"]

def inputs():
    raw="\n\n".join(f"{i}\n00:00:{i:02d},000 --> 00:00:{i:02d},900\n{text}"
                     for i,text in enumerate(TEXT,1)).encode()
    pin=sha256(raw)
    def claim(id,idx,kind,text,risk):
        return {"id":id,"segment_id":f"B{(idx-1)//2+1:04d}",
            "source_cue_span":{"first":idx,"last":idx},
            "source_ref":{"cue_index":idx,"quote":TEXT[idx-1],
                          "original_cue_sha256":sha256(TEXT[idx-1].encode())},
            "claim":text,"speech_act_kind":kind,"speaker_stance":"UNRESOLVED",
            "high_risk":risk,"chat_semantic_status":"HOLD_EXTERNAL",
            "conditions_exceptions_and_limitations":"Synthetic test only; no primary issuer origin proof"}
    claims=[claim("FRESH-0001",1,"FACT",TEXT[0],True),
            claim("FRESH-0002",3,"BOOK_CLAIM",TEXT[2],False)]
    review={"metadata":{"video_id":VIDEO,"source_cue_count":4,"source_bytes":len(raw),
            "original_source_sha256":pin,"scope_count":2,
            "previous_research_consumed":False,"manual_source_anchored_claim_count":2,
            "native_v123_final_gate_replayed":False,"actual_e4_status":"HOLD",
            "e5_authorized":False},
            "scope_census":[{"segment_id":"B0001","first_cue":1,"last_cue":2},
                            {"segment_id":"B0002","first_cue":3,"last_cue":4}],
            "fresh_manual_claims":claims}
    census={"source_sha256":pin,"cues":[
        {"cue_index":idx,"cue_sha256":sha256(text.encode()),
         "cue_source_first_disposition":"REVIEWED_MEANING_UNIT_CONTEXT" if idx%2 else "NON_INVESTMENT_DIALOGUE",
         "new_manual_review_context_claim_ids":[f"FRESH-{(idx+1)//2:04d}"] if idx%2 else []}
        for idx,text in enumerate(TEXT,1)]}
    return raw,review,census,pin

class FreshOwnerNativeV6BridgeTests(unittest.TestCase):
    def run_bridge(self,**changes):
        raw,review,census,pin=inputs()
        kw=dict(owner_pinned_source_sha256=pin,expected_video_id=VIDEO,
                expected_scope_count=2,scope_width=2)
        kw.update(changes)
        return compile_fresh_native_v6(raw,review,census,**kw)

    def test_01_exact_frozen_v6_structural_checks_across_all_children(self):
        r=self.run_bridge()
        s=r["summary"]
        self.assertEqual((s["source_cue_count"],s["native_v6_candidate_atoms"],s["scopes_native_structurally_checked"]),(4,2,2))
        self.assertEqual(s["cues_still_v6_unresolved"],2)
        self.assertFalse(s["native_v123_chat_approval"])
        self.assertEqual(s["native_e4_approved_children"],0)
        self.assertFalse(s["e5_authorized"])
        for child in r["native_children_private"]:
            self.assertEqual(child["native_v6_structural_audit"]["status"],
                             "HOST_ATOM_EXCHANGE_STRUCTURAL_REVIEW_ONLY")
            self.assertFalse(child["native_v6_structural_audit"]["all_atomic_claims_exhausted"])

    def test_02_no_unsupported_speech_act_promoted_to_semantic_fact(self):
        r=self.run_bridge()
        atom=r["native_children_private"][1]["exchange"]["atoms"][0]
        self.assertEqual(atom["kind"],"FACT")
        self.assertEqual(atom["speaker"],"UNKNOWN")
        self.assertEqual(atom["stance"],"UNRESOLVED")
        self.assertEqual(r["source_semantic_crosswalk_private"][1]["original_speech_act_kind"],"BOOK_CLAIM")
        self.assertTrue(r["source_semantic_crosswalk_private"][1]["requires_in_chat_native_v123_review"])

    def test_03_wrong_owner_bytes_or_owner_pin_rejected(self):
        with self.assertRaisesRegex(InvalidInput,"SOURCE_SHA_NOT_OWNER_PINNED"):
            self.run_bridge(owner_pinned_source_sha256="0"*64)
        raw,review,census,pin=inputs()
        with self.assertRaisesRegex(InvalidInput,"SOURCE_SHA_NOT_OWNER_PINNED"):
            compile_fresh_native_v6(raw+b"X",review,census,owner_pinned_source_sha256=pin,
                expected_video_id=VIDEO,expected_scope_count=2,scope_width=2)

    def test_04_partial_video_scopes_refused(self):
        with self.assertRaisesRegex(InvalidInput,"COMPLETE_VIDEO_SCOPE_CENSUS"):
            self.run_bridge(expected_scope_count=1)

    def test_05_original_quote_cue_bytes_tampered_refused(self):
        raw,review,census,pin=inputs()
        review["fresh_manual_claims"][0]["source_ref"]["quote"]="NOT IN THE ORIGINAL"
        with self.assertRaisesRegex(InvalidInput,"ORIGINAL_CUE_QUOTE_HASH_OR_CONTEXT_DRIFT"):
            compile_fresh_native_v6(raw,review,census,owner_pinned_source_sha256=pin,
                expected_video_id=VIDEO,expected_scope_count=2,scope_width=2)

    def test_06_no_silent_numeric_rewrite(self):
        raw,review,census,pin=inputs()
        review["fresh_manual_claims"][0]["claim"]="The investment target is 15% per year"
        r=compile_fresh_native_v6(raw,review,census,owner_pinned_source_sha256=pin,
            expected_video_id=VIDEO,expected_scope_count=2,scope_width=2)
        self.assertEqual(r["summary"]["native_v6_candidate_atoms"],1)
        self.assertEqual(r["summary"]["v6_unconverted_meaning_units"],1)
        self.assertEqual(r["unconverted_private"][0]["reason"],"V6_NUMERIC_TOKENS_NOT_IN_CONTEXT")

    def test_07_source_pinned_in_chat_reexpression_stays_unapproved(self):
        raw,review,census,pin=inputs()
        review["fresh_manual_claims"][0]["claim"]="The investment target is 10 percent per year"
        original=deepcopy(review["fresh_manual_claims"][0])
        repairs={"FRESH-0001":{"original_claim_sha256":json_digest(original),
                 "source_sha256":pin,"new_proposition":TEXT[0],
                 "reason":"SOURCE_NUMERIC_NOTATION_RECONCILED_IN_CHAT"}}
        r=compile_fresh_native_v6(raw,review,census,owner_pinned_source_sha256=pin,
             expected_video_id=VIDEO,expected_scope_count=2,scope_width=2,
             reviewed_source_reexpressions=repairs)
        self.assertEqual(r["summary"]["source_reexpressions_pending_secondary_review"],1)
        self.assertEqual(r["summary"]["native_v6_candidate_atoms"],2)
        self.assertFalse(r["summary"]["native_v123_chat_approval"])
        self.assertTrue(r["source_semantic_crosswalk_private"][0]["source_reexpression_requires_independent_meaning_review"])

    def test_08_wrong_original_review_digest_refuses_reexpression(self):
        raw,review,census,pin=inputs()
        repairs={"FRESH-0001":{"original_claim_sha256":"f"*64,
                 "source_sha256":pin,"new_proposition":TEXT[0],
                 "reason":"SOURCE_NUMERIC_NOTATION_RECONCILED_IN_CHAT"}}
        with self.assertRaisesRegex(InvalidInput,"SOURCE_REEXPRESSION_UNATTESTED_OR_CHANGED"):
            compile_fresh_native_v6(raw,review,census,owner_pinned_source_sha256=pin,
                expected_video_id=VIDEO,expected_scope_count=2,scope_width=2,
                reviewed_source_reexpressions=repairs)

    def test_09_missing_claim_context_links_rejected(self):
        raw,review,census,pin=inputs()
        census["cues"][2]["new_manual_review_context_claim_ids"]=[]
        with self.assertRaisesRegex(InvalidInput,"UNLINKED_FRESH_MEANING_UNIT"):
            compile_fresh_native_v6(raw,review,census,owner_pinned_source_sha256=pin,
                expected_video_id=VIDEO,expected_scope_count=2,scope_width=2)

    def test_10_wrong_full_cue_sha_rejected(self):
        raw,review,census,pin=inputs()
        census["cues"][3]["cue_sha256"]="0"*64
        with self.assertRaisesRegex(InvalidInput,"FRESH_CUE_INDEX_OR_SHA_DRIFT"):
            compile_fresh_native_v6(raw,review,census,owner_pinned_source_sha256=pin,
                expected_video_id=VIDEO,expected_scope_count=2,scope_width=2)

    def test_11_forged_prior_v123_pass_is_not_fresh_input(self):
        raw,review,census,pin=inputs()
        review["metadata"]["native_v123_final_gate_replayed"]=True
        with self.assertRaisesRegex(InvalidInput,"NOT_A_NEW_UNAPPROVED_OWNER_INPUT"):
            compile_fresh_native_v6(raw,review,census,owner_pinned_source_sha256=pin,
                expected_video_id=VIDEO,expected_scope_count=2,scope_width=2)

    def test_12_partial_foreign_scope_claim_refused(self):
        raw,review,census,pin=inputs()
        review["fresh_manual_claims"][1]["segment_id"]="B0001"
        with self.assertRaisesRegex(InvalidInput,"SEGMENT_OR_CROSS_BORDER_CLAIM"):
            compile_fresh_native_v6(raw,review,census,owner_pinned_source_sha256=pin,
                expected_video_id=VIDEO,expected_scope_count=2,scope_width=2)

if __name__=="__main__":unittest.main()