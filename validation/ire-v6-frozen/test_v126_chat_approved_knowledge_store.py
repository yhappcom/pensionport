"""V126 synthetic end-to-end: REAL V6 batch + REAL V123 gate + private SQLite.

Synthetic finance body is deliberately NOT a genuine law or P0 acceptance.
"""
import copy
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from ire.v6.codec import ZERO_SHA, json_digest, sha256
from ire.v6.errors import QualityNotProven
import test_v123_chat_final_gate as v123_fixture
from v126_chat_approved_knowledge_store import PrivateKnowledgeStore


def explicit_relation_decisions(exchange, pending):
    by_id={r["claim_id"]:r for r in pending["relations"]}
    relations={"SAME_PENDING":"SAME","EXTENDS_PENDING":"EXTENDS",
               "NOVEL_PENDING":"NEW","DISTINCT_PENDING":"NEW",
               "CONFLICT_PENDING":"CONFLICT"}
    return [{"claim_id":a["claim_id"],"atom_sha256":json_digest(a),
             "relation":relations[by_id[a["claim_id"]]["relationship"]],
             "target_kind":by_id[a["claim_id"]]["target_kind"],
             "target_id":by_id[a["claim_id"]]["target_id"],
             "private_chat_relation_review_sha256":sha256(
                 ("synthetic source-linked relation "+a["claim_id"]).encode("utf-8"))}
            for a in exchange["atoms"]]


class V126RealGatePrivateCumulativeKnowledgeTests(unittest.TestCase):
    def setUp(self):
        p=v123_fixture.ChatFinalGateTests("test_01_real_native_v6_batch_then_synthetic_chat_final_pass")
        p.setUp()
        self.addCleanup(p.doCleanups)
        self.p=p
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db=PrivateKnowledgeStore(Path(self.tmp.name)/"v126_private.db")
        self.prior=p.parent.knowledge
        self.original_host_batch_replay_args=p.parent.args()
        self.decisions=explicit_relation_decisions(p.exchange,self.prior)

    def push(self,**overrides):
        args=dict(source=self.p.source,exchange=self.p.exchange,
                  prior_knowledge=self.prior,host_receipt=self.p.host,
                  chat_review=self.p.review,source_store=self.p.parent.fx.store,
                  official_evidence_bodies=self.p.evidence_bodies,
                  relation_decisions=self.decisions,
                  expected_knowledge_head=ZERO_SHA,
                  original_host_batch_replay_args=self.original_host_batch_replay_args)
        args.update(overrides)
        return self.db.add_chat_final_batch(**args)

    def test_real_chat_gate_synthetic_source_then_immutable_cumulative_store(self):
        r=self.push()
        self.assertTrue(r["chat_final_gate_passed"])
        self.assertEqual(r["entries"],3)
        self.assertTrue(r["master116_p4_untouched"])
        self.assertEqual(r["financial_fact_formal_approval"],0)
        a=self.db.audit(externally_pinned_head=r["knowledge_head_sha256"])
        self.assertEqual(a["active_claims"],3)
        self.assertTrue(a["externally_anchored_checkpoint_verified"])
        q=self.db.evidence_for_question("투자 위험 분산",max_items=5)
        self.assertFalse(q["p0_go"])
        self.assertIsNone(q.get("answer_text"))
        self.assertTrue(q["requires_live_official_source_recheck"])
        self.assertTrue(q["chatgpt_final_answer_review_required"])
        with sqlite3.connect(self.db.path) as c:
            selected=sorted(x[0] for x in c.execute("SELECT knowledge_id FROM knowledge LIMIT 2"))
        exact=self.db.evidence_for_question("ISA 또는 IRP",selected_knowledge_ids=selected)
        self.assertEqual(len(exact["claims"]),len(selected))
        self.assertFalse(exact["no_auto_personal_advice"] is False)

    def test_same_input_idempotent_without_second_events(self):
        first=self.push()
        second=self.push()
        self.assertTrue(second["idempotent_replay"])
        self.assertEqual(second["knowledge_head_sha256"],first["knowledge_head_sha256"])
        with sqlite3.connect(self.db.path) as c:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM events").fetchone()[0],3)

    def test_no_final_chat_review_writes_nothing(self):
        with self.assertRaises(QualityNotProven):
            self.push(chat_review=None)
        self.assertEqual(self.db.audit()["active_claims"],0)

    def test_any_chat_open_blocks_all_batch(self):
        rev=copy.deepcopy(self.p.review)
        rev["atom_verdicts"][0].update(status="OPEN",finance_evidence_status="OPEN",
                                       official_body_sha256=None,
                                       official_effective_as_of=None,
                                       financial_scope_checked=False)
        with self.assertRaises(QualityNotProven):
            self.push(chat_review=rev)
        self.assertEqual(self.db.audit()["active_claims"],0)

    def test_missing_or_forged_relation_blocks_all_writes(self):
        for mode in ("missing","forged_target","self_approval"):
            rows=copy.deepcopy(self.decisions)
            if mode=="missing": rows.pop()
            elif mode=="forged_target": rows[0]["target_id"]="fake-claim"
            else:rows[0]["private_chat_relation_review_sha256"]="BAD"
            with self.subTest(mode=mode),self.assertRaises(QualityNotProven):
                self.push(relation_decisions=rows)
            self.assertEqual(self.db.audit()["active_claims"],0)

    def test_stale_host_batch_prior_relations_cannot_be_substituted(self):
        modified=copy.deepcopy(self.prior)
        modified["relations"][0]["relationship"]="CONFLICT_PENDING"
        with self.assertRaisesRegex(QualityNotProven,"SOURCE_HOST_BATCH_REPLAY_INPUT_DRIFT"):
            self.push(prior_knowledge=modified)
        self.assertEqual(self.db.audit()["active_claims"],0)

    def test_missing_exact_host_replay_denied(self):
        with self.assertRaisesRegex(QualityNotProven,"SOURCE_HOST_BATCH_REPLAY_INPUT_DRIFT"):
            self.push(original_host_batch_replay_args={})
        self.assertEqual(self.db.audit()["active_claims"],0)

    def test_stale_expected_head_fails_closed_for_other_batch(self):
        first=self.push()
        fake=copy.deepcopy(self.decisions)
        fake[0]["private_chat_relation_review_sha256"]="1"*64
        with self.assertRaises(QualityNotProven):
            self.push(relation_decisions=fake)
        self.assertEqual(self.db.audit()["head_sha256"],first["knowledge_head_sha256"])

    def test_tampering_sqlite_private_entry_detected_on_read(self):
        self.push()
        with sqlite3.connect(self.db.path) as c:
            kid=c.execute("SELECT knowledge_id FROM knowledge LIMIT 1").fetchone()[0]
            c.execute("UPDATE knowledge SET entry_json=? WHERE knowledge_id=?",("{}",kid))
        with self.assertRaises(QualityNotProven):
            self.db.audit()

    def test_chat_tombstone_retains_source_and_hides_claim(self):
        r=self.push()
        with sqlite3.connect(self.db.path) as c:
            kid=c.execute("SELECT knowledge_id FROM knowledge ORDER BY knowledge_id LIMIT 1").fetchone()[0]
        new=self.db.revoke(kid,chat_review_sha256="1"*64,
                           expected_knowledge_head=r["knowledge_head_sha256"])
        audit=self.db.audit(externally_pinned_head=new["head_sha256"])
        self.assertEqual((audit["active_claims"],audit["revoked_claims"]),(2,1))
        with self.assertRaises(QualityNotProven):
            self.db.evidence_for_question("ETF",selected_knowledge_ids=[kid])
        with self.assertRaises(QualityNotProven):
            self.db.audit(externally_pinned_head=r["knowledge_head_sha256"])
        with sqlite3.connect(self.db.path) as c:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0],3)
            self.assertEqual(c.execute("SELECT COUNT(*) FROM events").fetchone()[0],4)

    def test_nonexistent_or_quarantined_knowledge_cannot_support_answer(self):
        with self.assertRaises(QualityNotProven):
            self.db.evidence_for_question("투자",selected_knowledge_ids=["0"*64])

if __name__=="__main__":
    unittest.main()