"""V243 canonical gateway: synthetic E4/E5, REAL HOST E3 remains HOLD."""
from __future__ import annotations
import copy
import unittest
from unittest.mock import patch
from ire.v6.codec import ZERO_SHA
from ire.v6.errors import InvalidInput,QualityNotProven
from v193_e3_two_user_turn_contract import validate_manual_turn_receipt
from v166_e4_primary_approval_gate import _fetch_approved_primary_https
from test_v166_e4_primary_approval_gate import (
    V166E4E3V128RealSQLiteIntegration, BODY)
from v243_canonical_e1_e5_route import SCHEMA,run_canonical_research_route


class CanonicalRouteContractTests(unittest.TestCase):
    def setUp(self):
        fixture=V166E4E3V128RealSQLiteIntegration(
            "test_14_both_valid_synthetic_children_do_publish_research_only")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.f=fixture
        self.source=fixture.fx.checkpoint.parent.source_sha256
        self.head=fixture.fx.checkpoint.progress()["checkpoint_head_sha256"]
        self.a={"phase":"RESEARCH_AND_FREEZE","user_message_ref":"user:turn1",
                "user_message_sha256":"a"*64,"source_sha256":self.source,
                "owner_head_sha256":self.head,"research_frozen":True}
        self.b={"phase":"CHATGPT_FINAL_SEMANTIC_VERIFICATION",
                "user_message_ref":"user:turn2","user_message_sha256":"b"*64,
                "source_sha256":self.source,"owner_head_sha256":self.head,
                "review_recorded":True,"review_head_sha256":"c"*64}
    def run_route(self,**updates):
        f=self.f
        opts=dict(checkpoint=f.fx.checkpoint,knowledge_store=f.fx.knowledge,
                  first_user_turn=self.a,second_user_turn=self.b,
                  original_source_raw=f.fx.checkpoint.raw,
                  source_sha256=self.source,owner_freeze_sha256=self.head,
                  expected_knowledge_head=ZERO_SHA,
                  review_or_load_child=f.fx.child,
                  review_seams=f.fx.seams,review_parent=f.fx.parent_review,
                  primary_manifest_for_child=lambda sid,case:f.manifests.get(sid),
                  typed_inventory_for_child=lambda sid,case:f.typed_inventories.get(sid),
                  typed_manifest_for_child=lambda sid,case:f.typed_manifests.get(sid),
                  now_as_of="2026-11-17")
        opts.update(updates)
        return run_canonical_research_route(**opts)
    def test_01_manual_turns_reach_actual_v123_e4_e5_without_forged_host_success(self):
        # No patch of the V193 verdict or approval gate. Only official-network
        # transport is synthetic in this software test.
        with patch("v166_e4_primary_approval_gate._fetch_approved_primary_https",
                   return_value=BODY):
            r=self.run_route()
        self.assertEqual(r["schema"],SCHEMA)
        self.assertEqual(r["claimed_distinct_user_commands"],2)
        self.assertFalse(r["trusted_host_two_user_turns_verified"])
        self.assertTrue(r["manual_two_user_commands_recorded_not_platform_authenticated"])
        self.assertTrue(r["e4_invoked"])
        self.assertTrue(r["e5_invoked"])
        self.assertTrue(r["all_video_knowledge_published"])
        self.assertEqual(self.f.fx._counts()["knowledge"],3)
    def test_02_missing_turn2_must_not_write_or_approve(self):
        r=self.run_route(second_user_turn=None)
        self.assertEqual(r["claimed_distinct_user_commands"],1)
        self.assertFalse(r["e4_invoked"])
        self.assertFalse(r["e5_invoked"])
        self.assertFalse(r["all_video_knowledge_published"])
        self.assertEqual(self.f.fx._counts().get("events",0),0)
    def test_03_self_identical_user_message_is_not_two_turns(self):
        bad=copy.deepcopy(self.b);bad["user_message_ref"]="user:turn1"
        with self.assertRaisesRegex(InvalidInput,"SAME_USER_COMMAND"):
            self.run_route(second_user_turn=bad)
        self.assertEqual(self.f.fx._counts().get("events",0),0)
    def test_04_wrong_source_or_head_fails_before_any_commit(self):
        with self.assertRaises(QualityNotProven):
            self.run_route(source_sha256="0"*64)
        self.assertEqual(self.f.fx._counts().get("events",0),0)
    def test_05_cannot_use_legacy_unsealed_store(self):
        from v126_chat_approved_knowledge_store import PrivateKnowledgeStore
        with self.assertRaisesRegex(InvalidInput,"E4_SEALED"):
            self.run_route(knowledge_store=PrivateKnowledgeStore(self.f.fx.knowledge.path))
        self.assertEqual(self.f.fx._counts().get("events",0),0)
    def test_06_cannot_omit_typed_e4_callbacks(self):
        with self.assertRaisesRegex(InvalidInput,"MANDATORY_HOST"):
            self.run_route(typed_inventory_for_child=None)
    def test_07_synthetic_mock_can_exercise_real_e4_and_atomic_e5(self):
        # V193 returns "CLAIMED_UNVERIFIED" without any patched process
        # attestation. Genuine frozen E4 + V128 SQLite execute under synthetic
        # offline official-HTTPS transport only.
        with patch("v166_e4_primary_approval_gate._fetch_approved_primary_https",
                   return_value=BODY):
            r=self.run_route()
        self.assertEqual(r["status"],"RESEARCH_CANDIDATE_PARENT_COMMITTED_AWAIT_OWNER_PIN_CUSTODY")
        self.assertTrue(r["e4_sqlite_parent_logically_replayed_after_commit"])
        self.assertFalse(r["externally_independent_owner_pin_reverified"])
        self.assertIsInstance(r["e4_external_pin_returned_not_yet_owner_custodied"],str)
        self.assertTrue(r["all_video_knowledge_published"])
        self.assertEqual(self.f.fx._counts(),{"events":3,"knowledge":3,"parent_publications":1})
        self.assertFalse(r["formal_financial_fact_approved"])
        self.assertFalse(r["personal_advice_approved"])
    def test_08_synthetic_e4_missing_primary_blocks_e5_write(self):
        sid=self.f.fx.checkpoint.child_ids[1]
        del self.f.manifests[sid]
        with patch("v166_e4_primary_approval_gate._fetch_approved_primary_https",
                   return_value=BODY):
            out=self.run_route()
        self.assertEqual(out["status"],"HOLD_E4_PRIMARY_EVIDENCE")
        self.assertFalse(out["all_video_knowledge_published"])
        self.assertFalse(out["e5_invoked"])
        self.assertEqual(self.f.fx._counts().get("knowledge",0),0)
    def test_09_untrusted_turn_refs_not_exported_as_e5_release(self):
        report=self.run_route(second_user_turn=None)
        self.assertNotIn("e4_receipt",report)
        self.assertNotIn("publication_receipt",report)
        self.assertFalse(report["p0_go"])
    def test_11_unsealed_legacy_write_after_certification_invalidates_e4_readback(self):
        import sqlite3
        from ire.v6.errors import QualityNotProven
        from v126_chat_approved_knowledge_store import PrivateKnowledgeStore
        with patch("v166_e4_primary_approval_gate._fetch_approved_primary_https",
                   return_value=BODY):
            r=self.run_route()
        pin=r["e4_external_pin_returned_not_yet_owner_custodied"]
        self.f.fx.knowledge.verify_e4_certificate(
            externally_pinned_seal_sha256=pin)
        # Same-file legacy store remains physically importable. An attacker who
        # writes to its SQLite path must INVALIDATE the certified E4 readback.
        legacy=PrivateKnowledgeStore(self.f.fx.knowledge.path)
        with sqlite3.connect(legacy.path) as con:
            con.execute("UPDATE knowledge SET entry_json='{}' WHERE "
                        "knowledge_id=(SELECT knowledge_id FROM knowledge LIMIT 1)")
        with self.assertRaises(QualityNotProven):
            self.f.fx.knowledge.verify_e4_certificate(
                externally_pinned_seal_sha256=pin)

    def test_12_forged_e4_success_dict_without_sqlite_or_seal_rejected(self):
        evil={"schema":"IRE_V166_E4_PARENT_APPROVAL_V1",
              "status":"E4_PARENT_RESEARCH_CANDIDATES_PUBLISHED",
              "all_video_knowledge_published":True,
              "e4_external_owner_pin_sha256":"b"*64,
              "e4_durable_certification_verified":True,
              "child_preflights":[],"e3_parent_status":"PUBLISHED_RESEARCH_CANDIDATES_ONLY",
              "formal_financial_fact_approved":False,
              "personal_advice_approved":False,"p0_go":False}
        with patch("v243_canonical_e1_e5_route.run_e4_guarded_parent",
                   return_value=evil):
            with self.assertRaises(QualityNotProven):
                self.run_route()
        self.assertEqual(self.f.fx._counts().get("knowledge",0),0)

    def test_13_e4_hold_with_legacy_direct_write_cannot_masquerade_as_clean_hold(self):
        import sqlite3
        def unauthorized(*args,**kwargs):
            with sqlite3.connect(self.f.fx.knowledge.path) as con:
                con.execute("INSERT INTO knowledge VALUES(?,?,?)",
                            ("unapproved","{}", "0"*64))
            return {"schema":"IRE_V166_E4_PARENT_APPROVAL_V1",
                    "status":"E4_HOLD_UNVERIFIED_CHILD",
                    "all_video_knowledge_published":False,
                    "formal_financial_fact_approved":False,
                    "personal_advice_approved":False,"p0_go":False}
        with patch("v243_canonical_e1_e5_route.run_e4_guarded_parent",
                   side_effect=unauthorized):
            with self.assertRaises(QualityNotProven):
                self.run_route()
        self.assertEqual(self.f.fx._counts().get("knowledge",0),1)

    def test_14_crash_after_e5_sqlite_commit_before_e4_seal_cannot_be_read_as_approved(self):
        from pathlib import Path
        from ire.v6.errors import QualityNotProven
        with patch("v166_e4_primary_approval_gate._fetch_approved_primary_https",
                   return_value=BODY),patch(
                   "v166_e4_sealed_knowledge.os.replace",
                   side_effect=OSError("SYNTHETIC_BEFORE_SEAL_REPLACE")):
            with self.assertRaisesRegex(OSError,"BEFORE_SEAL_REPLACE"):
                self.run_route()
        self.assertEqual(self.f.fx._counts()["parent_publications"],1)
        self.assertFalse(Path(str(self.f.fx.knowledge.path)+".e4seal.json").exists())
        with self.assertRaises(QualityNotProven):
            self.f.fx.knowledge.verify_e4_certificate(
                externally_pinned_seal_sha256="a"*64)

    def test_16_original_source_byte_tamper_aborts_before_all_writes(self):
        with self.assertRaisesRegex(QualityNotProven,"OWNER_SOURCE_OR_FREEZE_DRIFT"):
            self.run_route(original_source_raw=self.f.fx.checkpoint.raw+b" ")
        self.assertEqual(self.f.fx._counts().get("knowledge",0),0)

    def test_17_missing_original_bytes_aborts_before_all_writes(self):
        with self.assertRaisesRegex(InvalidInput,"ORIGINAL_SOURCE_BYTES_REQUIRED"):
            self.run_route(original_source_raw=None)
        self.assertEqual(self.f.fx._counts().get("events",0),0)

    def test_15_success_e4_pin_is_not_a_user_custody_attestation(self):
        with patch("v166_e4_primary_approval_gate._fetch_approved_primary_https",
                   return_value=BODY):
            r=self.run_route()
        self.assertTrue(r["all_video_knowledge_published"])
        self.assertFalse(r["externally_independent_owner_pin_reverified"])
        self.assertFalse(r["p0_go"])

    def test_18_same_user_text_hash_in_distinct_user_turns_is_not_duplicate_identity(self):
        turn2=copy.deepcopy(self.b)
        turn2["user_message_sha256"]=self.a["user_message_sha256"]
        with patch("v166_e4_primary_approval_gate._fetch_approved_primary_https",
                   return_value=BODY):
            result=self.run_route(second_user_turn=turn2)
        self.assertTrue(result["e4_invoked"])
        self.assertFalse(result["trusted_host_two_user_turns_verified"])
        self.assertEqual(self.f.fx._counts()["parent_publications"],1)

    def test_19_bad_manual_turn_review_head_cannot_publish(self):
        turn2=copy.deepcopy(self.b)
        turn2["review_head_sha256"]="NOT_A_SHA"
        with self.assertRaisesRegex(InvalidInput,"SECOND_USER_OR_REVIEW_EVIDENCE_MISSING"):
            self.run_route(second_user_turn=turn2)
        self.assertEqual(self.f.fx._counts().get("events",0),0)

    def test_20_thirteen_child_source_without_typed_parent_overlay_refused(self):
        # P0-1-03: a real 13-child body may NOT omit 21 external atoms.
        checkpoint=self.f.fx.checkpoint
        original=list(checkpoint.child_ids)
        checkpoint.child_ids=original+[
            f"B{i:04d}" for i in range(3,14)]
        try:
            with self.assertRaisesRegex(InvalidInput,
                                        "PARENT_TYPED_OVERLAY_REQUIRED"):
                self.run_route()
            self.assertEqual(self.f.fx._counts().get("knowledge",0),0)
        finally:
            checkpoint.child_ids=original

    def test_21_unpaired_overlay_parameters_refused_without_e4(self):
        with self.assertRaisesRegex(InvalidInput,
                                    "PARENT_TYPED_OVERLAY_REQUIRED"):
            self.run_route(parent_typed_review_overlay={"untrusted":True})
        self.assertEqual(self.f.fx._counts().get("knowledge",0),0)

    def _synthetic_typed_parent_stub(self, *, cross_atoms):
        from v244_e1_private_parent_child_source_graph import source_child_plan
        from ire.v6.codec import json_digest
        cp=self.f.fx.checkpoint
        plan=source_child_plan(cp.raw,cp.parent.video_id,
            expected_source_sha256=self.source,window_size=cp.max_cues)
        self.assertEqual(len(plan["children"]),len(cp.child_ids))
        overlay={"source_sha256":self.source,
            "typed_overlay_sha256":"d"*64,
            "cross_atom_count":cross_atoms,
            "cross_typed_edge_count":3 if cross_atoms else 0,
            "atom_count":3,
            "child_count":len(cp.child_ids),
            "child_review_inputs":[{
                "child_id":p["child_id"],
                "child_plan_sha256":json_digest(p),
                "review_input_sha256":"e"*64
            } for p in plan["children"]]}
        args={
            "parent_typed_review_overlay":overlay,
            "expected_parent_typed_overlay_sha256":"d"*64,
            "parent_native_raw":b"synthetic-native-pinned",
            "parent_cue_raw":b"synthetic-cue-pinned",
            "parent_e3_raw":b"synthetic-e3-pinned",
            "parent_pairs_raw":b"synthetic-pairs-pinned",
            "expected_parent_native_sha256":"a"*64,
            "expected_parent_source_graph_sha256":"b"*64}
        return overlay,args

    def test_22_pending_external_full_parent_context_exposes_review_input_no_e4(self):
        overlay,kwargs=self._synthetic_typed_parent_stub(cross_atoms=1)
        with patch("v243_canonical_e1_e5_route.verify_typed_parent_review_overlay",
                   return_value={"status":"PARENT_TYPED_CHILD_INPUTS_SOURCE_VERIFIED_NOT_APPROVED"}):
            result=self.run_route(**kwargs)
        self.assertEqual(result["status"],
                         "HOLD_PARENT_CROSS_CHILD_SEMANTIC_REVIEW_REQUIRED")
        self.assertEqual(result["typed_parent_overlay_sha256"],"d"*64)
        self.assertEqual(len(result["formal_child_review_inputs_private"]),2)
        self.assertEqual(result["unapproved_cross_child_parent_atoms"],1)
        self.assertFalse(result["e4_invoked"])
        self.assertFalse(result["e5_invoked"])
        self.assertEqual(self.f.fx._counts().get("knowledge",0),0)

    def test_23_typed_callback_must_ack_exact_parent_input_before_e4(self):
        overlay,kwargs=self._synthetic_typed_parent_stub(cross_atoms=0)
        def bad_callback(segment_id,manifest,stage,raw,review_input):
            return self.f.fx.child(segment_id,manifest,stage,raw)
        with patch("v243_canonical_e1_e5_route.verify_typed_parent_review_overlay",
                   return_value={"status":"PARENT_TYPED_CHILD_INPUTS_SOURCE_VERIFIED_NOT_APPROVED"}):
            with self.assertRaisesRegex(InvalidInput,
                                        "CHILD_CHAT_INPUT_NOT_ACKNOWLEDGED"):
                self.run_route(review_or_load_child=bad_callback,**kwargs)
        self.assertEqual(self.f.fx._counts().get("knowledge",0),0)

    def test_24_zero_cross_typed_parent_ack_proceeds_to_real_e4_sqlite(self):
        overlay,kwargs=self._synthetic_typed_parent_stub(cross_atoms=0)
        def checked_callback(segment_id,manifest,stage,raw,review_input):
            packet=self.f.fx.child(segment_id,manifest,stage,raw)
            return {**packet,
                    "parent_typed_review_input_sha256":review_input["review_input_sha256"],
                    "parent_typed_overlay_sha256":overlay["typed_overlay_sha256"]}
        with patch("v243_canonical_e1_e5_route.verify_typed_parent_review_overlay",
                   return_value={"status":"PARENT_TYPED_CHILD_INPUTS_SOURCE_VERIFIED_NOT_APPROVED"}),patch(
                   "v166_e4_primary_approval_gate._fetch_approved_primary_https",
                   return_value=BODY):
            result=self.run_route(review_or_load_child=checked_callback,**kwargs)
        self.assertTrue(result["typed_parent_full_context_delivered_to_each_child"])
        self.assertTrue(result["all_video_knowledge_published"])
        self.assertEqual(self.f.fx._counts()["parent_publications"],1)

    def test_10_public_interface_has_no_cli(self):
        import v243_canonical_e1_e5_route as api
        self.assertEqual(api.__all__,("run_canonical_research_route",))
        self.assertFalse(hasattr(api,"main"))

if __name__=="__main__":
    unittest.main()
