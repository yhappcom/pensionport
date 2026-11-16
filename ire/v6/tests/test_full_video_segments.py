"""Owner-pinned full-video workplan: segmentation is not execution."""
from __future__ import annotations

import copy
import json
import unittest

from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput, QualityNotProven
from ire.v6.source import verify_source
from ire.v6.trust import verify_owner_inventory
from ire.v6.full_video_segments import propose_full_video_segments
from ire.v6.tests import test_atomic_exchange


class PrivateFullVideoSegmentsTests(unittest.TestCase):
    def setUp(self):
        base=test_atomic_exchange.HostAtomExchangeTests(
            "test_all_cues_number_context_and_stance_bound_but_not_semantic_gold")
        base.setUp()
        self.addCleanup(base.doCleanups)
        self.fx=base
        self.owner,self.pin=base.attest()

    def propose(self,**updates):
        args=dict(raw=self.fx.raw,manifest=self.fx.manifest,
                  inventory_bytes=self.owner,
                  expected_inventory_sha256=self.pin,max_cues=2)
        args.update(updates)
        return propose_full_video_segments(**args)

    def test_full_parent_original_cues_partition_without_gaps(self):
        result=self.propose()
        self.assertEqual(result["segment_count"],2)
        self.assertEqual([(s["first_cue"],s["last_cue"]) for s in result["segments"]],
                         [(1,2),(3,4)])
        self.assertEqual([s["source_window_ids"] for s in result["segments"]],
                         [["W00001"],["W00002"]])
        self.assertTrue(result["full_cue_partition_structurally_verified"])
        self.assertFalse(result["whole_video_research_complete"])
        self.assertFalse(result["p0_go"])

    def test_child_manifest_uses_original_raw_bytes_not_text_replacement(self):
        plan=self.propose()
        for chunk in plan["segments"]:
            derived=chunk["child_manifest"]
            source=verify_source(self.fx.raw,derived,
                  expected_source_sha256=sha256(self.fx.raw),
                  expected_manifest_sha256=json_digest(derived))
            self.assertEqual(source.scope_first_cue,chunk["first_cue"])
            self.assertEqual(source.scope_last_cue,chunk["last_cue"])
            self.assertEqual(chunk["child_manifest_sha256"],json_digest(derived))

    def test_child_plan_digests_are_not_existing_owner_pins(self):
        plan=self.propose()
        for chunk in plan["segments"]:
            self.assertFalse(chunk["child_owner_inventory_pinned"])
            with self.assertRaises(InvalidInput):
                verify_owner_inventory(self.fx.raw,chunk["child_manifest"],self.owner,
                         expected_inventory_sha256=self.pin)

    def test_original_one_turn_video_no_segmentation_required(self):
        out=self.propose(max_cues=4)
        self.assertEqual(out["status"],"FULL_SOURCE_FITS_EXISTING_HOST_TURN")
        self.assertFalse(out["segmentation_needed"])
        self.assertEqual(out["segment_count"],0)
        self.assertFalse(out["whole_video_research_complete"])

    def test_window_exceeding_max_host_budget_rejected(self):
        with self.assertRaisesRegex(QualityNotProven,"OWNER_WINDOW_EXCEEDS"):
            self.propose(max_cues=1)

    def test_parent_source_bytes_tamper_is_hard_blocked(self):
        with self.assertRaises(InvalidInput):
            self.propose(raw=self.fx.raw+b"\n")

    def test_unpinned_modified_window_manifest_rejected(self):
        m=copy.deepcopy(self.fx.manifest)
        m["windows"][0]["last_cue"]=3
        with self.assertRaises(InvalidInput):
            self.propose(manifest=m)

    def test_partial_parent_cannot_masquerade_as_full_video(self):
        m=copy.deepcopy(self.fx.manifest)
        m["scope"]={"mode":"PARTIAL","first_cue":1,"last_cue":2}
        m["windows"]=m["windows"][:1]
        # A different plan lacks the owner-trusted source pin and is refused
        # even before the explicit full-video scope check.
        with self.assertRaises(InvalidInput):
            self.propose(manifest=m)

    def test_no_private_cue_text_in_plan_or_git_safe_metadata(self):
        result=self.propose()
        data=json.dumps(result,ensure_ascii=False)
        for cue in self.fx.source.cues:
            self.assertNotIn(cue.text,data)
        self.assertNotIn("turn_payload",result)
        self.assertTrue(result["child_manifest_digests_are_not_owner_attestations"])

    def test_output_is_deterministic_and_source_bounded(self):
        a,b=self.propose(),self.propose()
        self.assertEqual(a,b)
        self.assertRegex(a["child_plan_census_sha256"],r"^[a-f0-9]{64}$")
        self.assertEqual(sum(x["scoped_cue_count"] for x in a["segments"]),4)

    def test_invalid_cue_limits_and_boolean_rejected(self):
        for amount in (0,True,121,"120"):
            with self.subTest(max_cues=amount),self.assertRaises(InvalidInput):
                self.propose(max_cues=amount)


if __name__=="__main__":
    unittest.main()
