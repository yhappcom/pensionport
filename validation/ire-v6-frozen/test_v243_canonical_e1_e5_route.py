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
    def test_01_distinct_manual_turns_do_not_invent_host_attestation(self):
        r=self.run_route()
        self.assertEqual(r["schema"],SCHEMA)
        self.assertEqual(r["status"],"HOLD_E3_HOST_TURN_PROVENANCE_NOT_VERIFIED")
        self.assertEqual(r["claimed_distinct_user_commands"],2)
        self.assertFalse(r["trusted_host_two_user_turns_verified"])
        self.assertFalse(r["e4_invoked"])
        self.assertFalse(r["e5_invoked"])
        self.assertEqual(self.f.fx._counts().get("knowledge",0),0)
    def test_02_missing_turn2_must_not_write_or_approve(self):
        r=self.run_route(second_user_turn=None)
        self.assertEqual(r["claimed_distinct_user_commands"],1)
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
        # This is a **CI fake trusted-host verifier**, NOT proof of a real
        # ChatGPT two-turn event. It exercises the frozen production functions.
        claimed={"host_separate_turns_verified":True,
                 "two_user_turns_proven":True,"recorded_distinct_user_commands":2}
        with patch("v243_canonical_e1_e5_route.validate_manual_turn_receipt",
                   return_value=claimed), patch(
                   "v166_e4_primary_approval_gate._fetch_approved_primary_https",
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
        with patch("v243_canonical_e1_e5_route.validate_manual_turn_receipt",
                   return_value={"host_separate_turns_verified":True,
                                 "two_user_turns_proven":True,
                                 "recorded_distinct_user_commands":2}), patch(
                   "v166_e4_primary_approval_gate._fetch_approved_primary_https",
                   return_value=BODY):
            out=self.run_route()
        self.assertEqual(out["status"],"HOLD_E4_PRIMARY_EVIDENCE")
        self.assertFalse(out["all_video_knowledge_published"])
        self.assertFalse(out["e5_invoked"])
        self.assertEqual(self.f.fx._counts().get("knowledge",0),0)
    def test_09_untrusted_turn_refs_not_exported_as_e5_release(self):
        report=self.run_route()
        self.assertNotIn("e4_receipt",report)
        self.assertNotIn("publication_receipt",report)
        self.assertFalse(report["p0_go"])
    def test_11_unsealed_legacy_write_after_certification_invalidates_e4_readback(self):
        import sqlite3
        from ire.v6.errors import QualityNotProven
        from v126_chat_approved_knowledge_store import PrivateKnowledgeStore
        trusted={"host_separate_turns_verified":True,
                 "two_user_turns_proven":True,"recorded_distinct_user_commands":2}
        with patch("v243_canonical_e1_e5_route.validate_manual_turn_receipt",
                   return_value=trusted),patch(
                   "v166_e4_primary_approval_gate._fetch_approved_primary_https",
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
        trusted={"host_separate_turns_verified":True,
                 "two_user_turns_proven":True,"recorded_distinct_user_commands":2}
        evil={"schema":"IRE_V166_E4_PARENT_APPROVAL_V1",
              "status":"E4_PARENT_RESEARCH_CANDIDATES_PUBLISHED",
              "all_video_knowledge_published":True,
              "e4_external_owner_pin_sha256":"b"*64,
              "e4_durable_certification_verified":True,
              "child_preflights":[],"e3_parent_status":"PUBLISHED_RESEARCH_CANDIDATES_ONLY",
              "formal_financial_fact_approved":False,
              "personal_advice_approved":False,"p0_go":False}
        with patch("v243_canonical_e1_e5_route.validate_manual_turn_receipt",
                   return_value=trusted),patch(
                   "v243_canonical_e1_e5_route.run_e4_guarded_parent",
                   return_value=evil):
            with self.assertRaises(QualityNotProven):
                self.run_route()
        self.assertEqual(self.f.fx._counts().get("knowledge",0),0)

    def test_13_e4_hold_with_legacy_direct_write_cannot_masquerade_as_clean_hold(self):
        import sqlite3
        trusted={"host_separate_turns_verified":True,
                 "two_user_turns_proven":True,"recorded_distinct_user_commands":2}
        def unauthorized(*args,**kwargs):
            with sqlite3.connect(self.f.fx.knowledge.path) as con:
                con.execute("INSERT INTO knowledge VALUES(?,?,?)",
                            ("unapproved","{}", "0"*64))
            return {"schema":"IRE_V166_E4_PARENT_APPROVAL_V1",
                    "status":"E4_HOLD_UNVERIFIED_CHILD",
                    "all_video_knowledge_published":False,
                    "formal_financial_fact_approved":False,
                    "personal_advice_approved":False,"p0_go":False}
        with patch("v243_canonical_e1_e5_route.validate_manual_turn_receipt",
                   return_value=trusted),patch(
                   "v243_canonical_e1_e5_route.run_e4_guarded_parent",
                   side_effect=unauthorized):
            with self.assertRaises(QualityNotProven):
                self.run_route()
        self.assertEqual(self.f.fx._counts().get("knowledge",0),1)

    def test_14_crash_after_e5_sqlite_commit_before_e4_seal_cannot_be_read_as_approved(self):
        from pathlib import Path
        from ire.v6.errors import QualityNotProven
        trusted={"host_separate_turns_verified":True,
                 "two_user_turns_proven":True,"recorded_distinct_user_commands":2}
        with patch("v243_canonical_e1_e5_route.validate_manual_turn_receipt",
                   return_value=trusted),patch(
                   "v166_e4_primary_approval_gate._fetch_approved_primary_https",
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

    def test_15_success_e4_pin_is_not_a_user_custody_attestation(self):
        trusted={"host_separate_turns_verified":True,
                 "two_user_turns_proven":True,"recorded_distinct_user_commands":2}
        with patch("v243_canonical_e1_e5_route.validate_manual_turn_receipt",
                   return_value=trusted),patch(
                   "v166_e4_primary_approval_gate._fetch_approved_primary_https",
                   return_value=BODY):
            r=self.run_route()
        self.assertTrue(r["all_video_knowledge_published"])
        self.assertFalse(r["externally_independent_owner_pin_reverified"])
        self.assertFalse(r["p0_go"])

    def test_10_public_interface_has_no_cli(self):
        import v243_canonical_e1_e5_route as api
        self.assertEqual(api.__all__,("run_canonical_research_route",))
        self.assertFalse(hasattr(api,"main"))

if __name__=="__main__":
    unittest.main()
