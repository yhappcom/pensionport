"""V172 engine-path regression: all children audited before any publication.

All video cues, ChatGPT replies and official HTTPS bodies here are SYNTHETIC.
The V123, E4, sealed SQLite and V128 parent code under test are REAL.
"""
import copy
import sqlite3
import unittest
from unittest.mock import patch

from ire.v6.codec import ZERO_SHA
from ire.v6.errors import InvalidInput
from test_v166_e4_primary_approval_gate import (
    BODY, V166E4E3V128RealSQLiteIntegration,
)
from v172_full_video_engine import run_exhaustive_full_video


class V172FullVideoEngineTests(unittest.TestCase):
    def setUp(self):
        owner = V166E4E3V128RealSQLiteIntegration(
            "test_14_both_valid_synthetic_children_do_publish_research_only")
        owner.setUp()
        self.addCleanup(owner.doCleanups)
        self.owner = owner
        self.fx = owner.fx
        self.issued = []
        self.review_count = 0
        self.parent_review_count = 0
        self.seam_count = 0

    def _child(self, sid, manifest, stage, raw):
        self.issued.append(sid)
        self.assertEqual(stage, "PREFLIGHT_ALL_SCOPES")
        return self.fx.child(sid, manifest, stage, raw)

    def _parent(self, checkpoint, assembly, seams, packets):
        self.parent_review_count += 1
        return self.fx.parent_review(checkpoint, assembly, seams, packets)

    def _seams(self, checkpoint, cases):
        self.seam_count += 1
        return self.fx.seams(checkpoint, cases)

    def run_engine(self, **changes):
        kwargs = dict(
            checkpoint=self.fx.checkpoint,
            knowledge_store=self.fx.knowledge,
            review_or_load_child=self._child,
            review_seams=self._seams,
            review_parent=self._parent,
            primary_manifest_for_child=lambda sid, case: self.owner.manifests.get(sid),
            typed_inventory_for_child=lambda sid, case: self.owner.typed_inventories.get(sid),
            typed_manifest_for_child=lambda sid, case: self.owner.typed_manifests.get(sid),
            expected_knowledge_head=ZERO_SHA,
            now_as_of="2026-11-17",
            expected_scope_count=2,
        )
        kwargs.update(changes)
        with patch("v166_e4_primary_approval_gate._fetch_approved_primary_https",
                   return_value=BODY):
            return run_exhaustive_full_video(**kwargs)

    def test_01_two_children_full_native_e4_parent_atomic_success(self):
        r = self.run_engine()
        self.assertEqual(r["status"], "E4_SEALED_PARENT_PUBLISHED_RESEARCH_ONLY")
        self.assertEqual(self.issued, list(self.fx.checkpoint.child_ids))
        self.assertEqual(r["owner_video_scope_count"], 2)
        self.assertEqual(r["child_scopes_examined"], 2)
        self.assertEqual(r["blocked_scope_count"], 0)
        self.assertTrue(r["official_parent_invoked"])
        self.assertTrue(r["all_video_knowledge_published"])
        self.assertEqual(self.fx._counts(),
                         {"events": 3, "knowledge": 3, "parent_publications": 1})
        self.assertTrue(self.fx.knowledge.verify_e4_certificate(
            externally_pinned_seal_sha256=r["e4_owner_pin_sha256"])[
                "all_original_sqlite_rows_unchanged"])
        self.assertEqual(self.parent_review_count, 1)
        self.assertEqual(self.seam_count, 1)
        self.assertFalse(r["chatgpt_automatically_invoked_by_python"])

    def test_02_first_child_primary_missing_does_not_skip_second(self):
        del self.owner.manifests[self.fx.checkpoint.child_ids[0]]
        r = self.run_engine()
        self.assertEqual(self.issued, list(self.fx.checkpoint.child_ids))
        self.assertEqual(r["child_scopes_examined"], 2)
        self.assertEqual(r["blocked_scope_count"], 1)
        self.assertEqual(r["blocked_scope_ids"], [self.fx.checkpoint.child_ids[0]])
        self.assertEqual(r["child_preflights"][1]["e4_status"],
                         "E4_PASS_RESEARCH_CANDIDATES_ONLY")
        self.assertEqual(r["status"], "EXHAUSTIVE_E4_HOLD_ALL_SCOPES_CHECKED")
        self.assertFalse(r["official_parent_invoked"])
        self.assertEqual(self.fx._counts().get("knowledge", 0), 0)
        self.assertEqual(self.fx.checkpoint.progress()["passed_child_scopes"], 0)
        self.assertEqual(self.parent_review_count, 0)

    def test_03_last_child_primary_missing_still_checks_both(self):
        del self.owner.manifests[self.fx.checkpoint.child_ids[1]]
        r = self.run_engine()
        self.assertEqual(len(self.issued), 2)
        self.assertEqual(r["blocked_scope_ids"], [self.fx.checkpoint.child_ids[1]])
        self.assertEqual(self.fx._counts().get("knowledge", 0), 0)

    def test_04_all_children_primary_missing_collects_both_reasons(self):
        self.owner.manifests.clear()
        r = self.run_engine()
        self.assertEqual(r["blocked_scope_count"], 2)
        self.assertEqual(r["blocked_scope_ids"], list(self.fx.checkpoint.child_ids))
        self.assertFalse(r["all_video_knowledge_published"])

    def test_05_native_chat_open_does_not_terminate_first_segment(self):
        self.fx.packets[0]["case"]["chat_review"]["atom_verdicts"][0]["status"] = "OPEN"
        r = self.run_engine()
        self.assertEqual(len(self.issued), 2)
        self.assertEqual(r["child_preflights"][0]["reason_code"], "NATIVE_CHAT_NOT_PASS")
        self.assertEqual(r["child_preflights"][1]["e4_status"],
                         "E4_PASS_RESEARCH_CANDIDATES_ONLY")
        self.assertFalse(r["all_video_knowledge_published"])

    def test_06_invalid_issuer_fails_closed_but_next_checked(self):
        first = self.fx.checkpoint.child_ids[0]
        self.owner.manifests[first]["rows"][0]["official_url"] = "https://invalid.example.org/claim"
        r = self.run_engine()
        self.assertEqual(len(self.issued), 2)
        self.assertEqual(r["child_preflights"][0]["e4_status"],
                         "E4_CHILD_VERIFIER_ERROR")
        self.assertEqual(r["child_preflights"][0]["reason_code"], "InvalidInput")
        self.assertNotIn("invalid.example.org", str(r))
        self.assertFalse(r["all_video_knowledge_published"])

    def test_07_wrong_target_scope_count_rejected_before_model_calls(self):
        with self.assertRaisesRegex(InvalidInput, "COMPLETE_PINNED_VIDEO_SCOPE_CENSUS"):
            self.run_engine(expected_scope_count=13)
        self.assertEqual(self.issued, [])

    def test_08_missing_chat_host_callback_rejected_before_processing(self):
        with self.assertRaisesRegex(InvalidInput, "LIVE_CHAT_HOST_CALLBACKS_REQUIRED"):
            self.run_engine(review_or_load_child=None)
        self.assertEqual(self.issued, [])

    def test_09_missing_parent_review_never_certifies_publication(self):
        r = self.run_engine(review_parent=lambda *args: None)
        self.assertEqual(r["child_scopes_examined"], 2)
        self.assertTrue(r["official_parent_invoked"])
        self.assertEqual(r["status"], "PARENT_REPLAY_FAILED_NO_CERTIFIED_RELEASE")
        self.assertFalse(r["all_video_knowledge_published"])
        self.assertEqual(self.fx._counts().get("knowledge",0),0)

    def test_10_missing_cross_segment_chat_review_no_publication(self):
        r = self.run_engine(review_seams=lambda *args: [])
        self.assertEqual(len(self.issued), 2)
        self.assertFalse(r["all_video_knowledge_published"])
        self.assertEqual(self.fx._counts().get("knowledge",0),0)

    def test_11_callback_exception_on_first_child_does_not_hide_second(self):
        def bad(sid, manifest, stage, raw):
            self.issued.append(sid)
            if sid == self.fx.checkpoint.child_ids[0]:
                raise RuntimeError("private sensitive detail must never leak")
            return self.fx.child(sid, manifest, stage, raw)
        r = self.run_engine(review_or_load_child=bad)
        self.assertEqual(len(self.issued), 2)
        self.assertEqual(r["blocked_scope_count"], 1)
        self.assertNotIn("private sensitive detail", str(r))
        self.assertFalse(r["all_video_knowledge_published"])

    def test_13_thirteen_scope_control_plane_inspects_all_after_first_hold(self):
        # Synthetic 13-scope scheduling stress; the native V123/E4 logic for
        # individual scopes is verified in the other non-mocked integration tests.
        from types import SimpleNamespace
        parent = SimpleNamespace(
            child_ids=[f"B{i:04d}" for i in range(1,14)],
            child_manifests=[{"test_scope":i} for i in range(1,14)],
            raw=b"synthetic stub, never a genuine owner SRT",
            progress=lambda: {"checkpoint_head_sha256":"0"*64})
        seen=[]
        def child(sid,manifest,stage,raw):
            seen.append(sid)
            return {"case":{"manifest":manifest}}
        def gate(case, primary, **kwargs):
            i=case["manifest"]["test_scope"]
            if i in (1,7,13):
                return {"status":"E4_HOLD_INELIGIBLE_APPROVAL",
                        "reason_code":"SYNTHETIC_MISSING_PRIMARY",
                        "native_chat_decision":"HOLD_UNRELEASED",
                        "native_unapproved_open_claim_count":1}
            return {"status":"E4_PASS_RESEARCH_CANDIDATES_ONLY"}
        with patch("v172_full_video_engine.assess_e4_primary_authority_gate",gate):
            result=self.run_engine(
                checkpoint=parent,expected_scope_count=13,
                review_or_load_child=child,
                primary_manifest_for_child=lambda sid,case: None,
                typed_inventory_for_child=lambda sid,case: None,
                typed_manifest_for_child=lambda sid,case: None)
        self.assertEqual(len(seen),13)
        self.assertEqual(seen,parent.child_ids)
        self.assertEqual(result["child_scopes_examined"],13)
        self.assertEqual(result["blocked_scope_ids"],["B0001","B0007","B0013"])
        self.assertEqual(self.fx._counts().get("knowledge",0),0)
        self.assertFalse(result["all_video_knowledge_published"])

    def test_12_full_e4_pins_work_without_a_new_model_invocation(self):
        r = self.run_engine()
        self.assertEqual(len(self.issued), 2)
        self.assertEqual(self.parent_review_count, 1)
        self.assertEqual(self.seam_count, 1)
        self.assertTrue(r["e4_owner_pin_sha256"])
        self.assertFalse(r["personal_advice_approved"])
        self.assertFalse(r["p0_go"])


if __name__ == "__main__":
    unittest.main()