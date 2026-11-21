"""V215.1 source-locked all-pairs lexical triage tests, synthetic only."""
from __future__ import annotations

import copy
import json
import unittest

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from test_v210_e2_private_original_source_inventory import RAW,synthetic
from v214_e2_real_srt_provisional_native_v6 import construct_provisional_native_v6
from v2151_e2_private_pairwise_source_screen import (
    source_only_native_pairwise_screen,
)


class TestV2151PairScreen(unittest.TestCase):
    def setUp(self):
        self.v210=synthetic()
        b=json.dumps(self.v210,ensure_ascii=False,indent=2).encode()
        self.exchange,_=construct_provisional_native_v6(
            RAW,self.v210,expected_source_sha256=sha256(RAW),
            private_v210_source_bytes=b,
            expected_v210_source_sha256=sha256(b),window_size=2)

    def check(self,exchange=None,raw=RAW,original_bytes=None,
              expected_exchange_sha=None,**kwargs):
        ex=self.exchange if exchange is None else exchange
        bytes_=json.dumps(ex,ensure_ascii=False,indent=2).encode() if (
            original_bytes is None) else original_bytes
        return source_only_native_pairwise_screen(
            raw,ex,bytes_,expected_source_sha256=sha256(RAW),
            expected_exchange_sha256=(
                sha256(bytes_) if expected_exchange_sha is None else
                expected_exchange_sha),
            window_size=2,**kwargs)

    def test_01_every_possible_pair_screened_without_semantic_equivalence(self):
        r=self.check()
        self.assertEqual(r["native_unapproved_atoms"],2)
        self.assertEqual(r["native_pairwise_pairs_lexically_screened"],1)
        self.assertEqual(len(r["top_pairs_for_chat_meaning_review"]),1)
        self.assertFalse(r["top_pairs_for_chat_meaning_review"][0][
            "semantic_equivalence_verified"])
        self.assertTrue(r["lexical_similarity_does_not_imply_equivalence"])
        self.assertEqual(r["automatic_atom_merges"],0)
        self.assertFalse(r["independent_gold_certified"])
        self.assertFalse(r["e2_final_pass"])
        self.assertNotIn("proposition",str(r))

    def test_02_exact_same_proposition_still_requires_review(self):
        ex=copy.deepcopy(self.exchange)
        clone=copy.deepcopy(ex["atoms"][0])
        clone["claim_id"]="C00003"
        ex["atoms"].append(clone)
        i=clone["source_refs"][0]["cue_index"]-1
        ex["cue_dispositions"][i]["claim_ids"].append(clone["claim_id"])
        ex["cue_dispositions"][i]["claim_ids"].sort()
        r=self.check(exchange=ex)
        self.assertEqual(r["native_pairwise_pairs_lexically_screened"],3)
        self.assertEqual(r["exact_same_text_pair_count"],1)
        self.assertEqual(r["automatic_atom_merges"],0)
        self.assertFalse(r["all_pairs_source_semantically_verified"])

    def test_03_old_exchange_sha_pin_rejects_tampering(self):
        with self.assertRaisesRegex(InvalidInput,
                                    "PRIVATE_NATIVE_BYTES_OR_HASH_NOT_PINNED"):
            self.check(expected_exchange_sha="f"*64)

    def test_04_changed_original_srt_fails_before_pair_scoring(self):
        with self.assertRaisesRegex(InvalidInput,"SOURCE_BYTES_CHANGED"):
            self.check(raw=RAW+b" ")

    def test_05_reformatted_json_without_matching_object_rejected(self):
        b=json.dumps({"fake":"unrelated"}).encode()
        with self.assertRaisesRegex(InvalidInput,
                                    "SOURCE_NATIVE_ARGS_MISMATCH"):
            self.check(original_bytes=b)

    def test_06_invalid_top_limit_returns_invalidinput(self):
        with self.assertRaisesRegex(InvalidInput,"SOURCE_NATIVE_ARGS_MISMATCH"):
            self.check(top_n=0)

    def test_07_nonint_threshold_returns_invalidinput_not_typeerror(self):
        with self.assertRaisesRegex(InvalidInput,"SOURCE_NATIVE_ARGS_MISMATCH"):
            self.check(threshold_basis_points=[])

    def test_08_auto_speaker_promotion_not_allowed(self):
        ex=copy.deepcopy(self.exchange)
        ex["atoms"][0]["speaker"]="NARRATOR"
        with self.assertRaisesRegex(InvalidInput,
                                    "SOURCE_SPEAKER_PREMATURELY_CERTIFIED"):
            self.check(exchange=ex)

    def test_09_top_n_is_bounded_screen_not_auto_semantic_merger(self):
        r=self.check(top_n=1,threshold_basis_points=0)
        self.assertEqual(r["pairs_at_or_above_threshold"],1)
        self.assertEqual(len(r["top_pairs_for_chat_meaning_review"]),1)
        self.assertFalse(r["top_pairs_for_chat_meaning_review"][0][
            "automatic_merge_authorized"])

    def test_10_duplicate_draft_deterministic_without_private_leak(self):
        a=self.check()
        b=self.check()
        self.assertEqual(a,b)
        self.assertFalse(a["knowledge_published"])
        self.assertFalse(a["e3_e4_e5_authorized"])


if __name__=="__main__":
    unittest.main()
