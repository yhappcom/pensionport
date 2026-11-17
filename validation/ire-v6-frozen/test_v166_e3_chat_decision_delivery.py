"""V166 E3 final ChatGPT PASS/HOLD/REJECT/QUARANTINE delivery tests.

Real frozen native V123, V127.1 checkpoint, V128 parent runner and V126
private SQLite; text and reviewer judgments SYNTHETIC unless stated.
"""
from __future__ import annotations

import copy
import unittest

from ire.v6.codec import ZERO_SHA
from ire.v6.errors import InvalidInput, QualityNotProven
from test_v128_continuous_chat_atomic_parent import V128HostRunAndAtomicParentTests
from test_v166_e1_same_typed_review_to_sqlite import V166E1SameTypedReviewToSQLite
from v166_e3_chat_decision_delivery import (
    replay_chat_decision_envelope, run_full_video_with_e3_decisions,
)


class V166E3NativeDecisionDelivery(unittest.TestCase):
    def setUp(self):
        self.fx=V128HostRunAndAtomicParentTests(
            "test_01_two_native_v6_children_seam_and_atomic_private_parent_publication")
        self.fx.setUp()
        self.addCleanup(self.fx.doCleanups)

    def run_host(self):
        return run_full_video_with_e3_decisions(
            self.fx.checkpoint,self.fx.knowledge,
            review_or_load_child=self.fx.child,
            review_seams=self.fx.seams,
            review_parent=self.fx.parent_review,
            expected_knowledge_head=ZERO_SHA,
        )

    def test_01_all_chat_approved_children_preserve_research_only_pass(self):
        result=self.run_host()
        self.assertEqual(result["explicit_e3_status"],
                         "PUBLISHED_RESEARCH_CANDIDATES_ONLY")
        self.assertTrue(result["all_video_knowledge_published"])
        self.assertEqual([c["decision"] for c in result["child_decisions"]],
                         ["PASS_RESEARCH_CANDIDATES_ONLY"]*2)
        self.assertEqual(self.fx._counts(),
                         {"events":3,"knowledge":3,"parent_publications":1})
        self.assertFalse(result["personal_advice_approved"])
        self.assertFalse(result["formal_financial_fact_approved"])

    def test_02_missing_source_body_preserves_chat_hold_and_no_publish(self):
        self.fx.packets[1]["case"]["official_evidence_bodies"]={}
        result=self.run_host()
        self.assertEqual(result["native_v128_status"],
                         "HOLD_CHILD_CHAT_SEMANTICS_OR_FINANCE")
        self.assertEqual(result["explicit_e3_status"],"CHILD_HOLD_UNRELEASED")
        self.assertEqual(result["child_decisions"][0]["v127_checkpoint_decision"],
                         "PASS")
        self.assertEqual(result["child_decisions"][1]["v127_checkpoint_decision"],
                         "HOLD")
        self.assertFalse(result["all_video_knowledge_published"])
        self.assertEqual(self.fx._counts().get("knowledge",0),0)

    def test_03_rejected_chat_atom_never_relabelled_hold(self):
        self.fx.packets[1]["case"]["chat_review"]["atom_verdicts"][0]["status"]="REJECT"
        result=self.run_host()
        self.assertEqual(result["native_v128_status"],
                         "HOLD_CHILD_CHAT_SEMANTICS_OR_FINANCE")
        self.assertEqual(result["explicit_e3_status"],"CHILD_REJECTED_FINAL_CHAT")
        self.assertEqual(result["child_decisions"][1]["decision"],"REJECTED")
        self.assertEqual(result["child_decisions"][1]["v127_checkpoint_decision"],
                         "REJECT")
        self.assertGreaterEqual(result["child_decisions"][1]["rejected"],1)
        self.assertFalse(result["all_video_knowledge_published"])
        self.assertEqual(self.fx._counts().get("knowledge",0),0)

    def test_04_reject_has_priority_even_when_another_atom_open(self):
        # B0002 has one synthetic atom. B0001 carries two independent
        # atoms, so this is the correct composite REJECT + OPEN fixture.
        case=self.fx.packets[0]["case"]
        self.assertGreaterEqual(len(case["chat_review"]["atom_verdicts"]),2)
        case["chat_review"]["atom_verdicts"][0]["status"]="REJECT"
        case["chat_review"]["atom_verdicts"][1]["status"]="OPEN"
        result=self.run_host()
        self.assertEqual(result["explicit_e3_status"],"CHILD_REJECTED_FINAL_CHAT")
        self.assertEqual(result["child_decisions"][0]["decision"],"REJECTED")
        self.assertGreaterEqual(result["child_decisions"][0]["open"],1)

    def test_05_chat_review_missing_fails_closed(self):
        self.fx.packets[0]["case"]["chat_review"]=None
        with self.assertRaises(InvalidInput):
            self.run_host()
        self.assertEqual(self.fx._counts().get("knowledge",0),0)

    def test_06_review_modified_after_pass_not_replay_or_republish(self):
        result=self.run_host()
        self.assertTrue(result["all_video_knowledge_published"])
        original=self.fx._counts()
        self.fx.packets[0]["case"]["chat_review"]["atom_verdicts"][0][
            "private_review_note_sha256"]="0"*64
        with self.assertRaises((InvalidInput,QualityNotProven)):
            self.run_host()
        self.assertEqual(self.fx._counts(),original)

    def test_07_cannot_pretend_rejected_child_was_accepted_without_revision(self):
        case=self.fx.packets[1]["case"]
        original=copy.deepcopy(case["chat_review"])
        case["chat_review"]["atom_verdicts"][0]["status"]="REJECT"
        r=self.run_host()
        self.assertEqual(r["explicit_e3_status"],"CHILD_REJECTED_FINAL_CHAT")
        case["chat_review"]=original
        with self.assertRaises(QualityNotProven):
            self.run_host()
        self.assertEqual(self.fx._counts().get("knowledge",0),0)

    def test_08_atom_decision_note_sha_and_original_source_digest_are_pinned(self):
        case=self.fx.packets[0]["case"]
        item=replay_chat_decision_envelope(case)
        self.assertEqual(item["source_sha256"],case["source"].source_sha256)
        self.assertEqual(len(item["atom_decisions"]),
                         len(case["exchange"]["atoms"]))
        self.assertTrue(all(a["review_note_sha256"] for a in item["atom_decisions"]))
        self.assertEqual(item["native_gate_status"],
                         "CHAT_FINAL_PASS_RESEARCH_CANDIDATES_ONLY")
        self.assertFalse(item["personal_investment_advice_authorized"])


class V166E3QuarantinedSourceOnlyDecision(unittest.TestCase):
    def setUp(self):
        self.t=V166E1SameTypedReviewToSQLite(
            "test_01_same_typed_review_native_v123_v127_v128_private_sqlite_commit")
        self.t.setUp()
        self.addCleanup(self.t.doCleanups)

    def _run(self):
        self.t._prepare()
        f=self.t.fx
        return run_full_video_with_e3_decisions(
            f.checkpoint,f.knowledge,
            review_or_load_child=f.child,
            review_seams=f.seams,
            review_parent=f.parent_review,
            expected_knowledge_head=ZERO_SHA)

    def test_09_source_quarantined_not_promoted_to_approved_finance(self):
        result=self._run()
        self.assertEqual(result["explicit_e3_status"],
                         "PUBLISHED_RESEARCH_CANDIDATES_ONLY")
        child=result["child_decisions"][0]
        self.assertEqual(child["quarantined"],1)
        excluded=[a for a in child["atoms"] if a["disposition"] ==
                  "QUARANTINED_NOT_RESEARCH_KNOWLEDGE"]
        self.assertEqual([x["claim_id"] for x in excluded],["C00002"])
        self.assertEqual(excluded[0]["reason_code"],"NON_RESEARCH_CONTENT")
        self.assertEqual(self.t.fx._counts(),
                         {"events":2,"knowledge":2,"parent_publications":1})

    def test_10_quarantine_reason_mutation_fails_before_publication(self):
        self.t._prepare()
        case=self.t.case
        case["chat_review"]["quarantine"]["atom_rows"][0]["reason_code"]="UNSUPPORTED"
        with self.assertRaises(InvalidInput):
            replay_chat_decision_envelope(case)
        self.assertEqual(self.t.fx._counts().get("knowledge",0),0)


if __name__=="__main__":
    unittest.main()
