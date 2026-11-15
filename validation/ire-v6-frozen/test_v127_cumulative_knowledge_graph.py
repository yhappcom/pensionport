"""Synthetic cross-video conflict/revocation graph, real V126 SQLite events."""
import copy
import json
import sqlite3
import unittest

from ire.v6.codec import canonical,json_digest,sha256,ZERO_SHA
from ire.v6.errors import QualityNotProven
from test_v126_chat_approved_knowledge_store import V126RealGatePrivateCumulativeKnowledgeTests
from v127_cumulative_knowledge_graph import audit_private_cumulative_knowledge_graph,inspect_cumulative_knowledge_graph

class V127CrossVideoConflictQuarantineTests(unittest.TestCase):
    def setUp(self):
        prior=V126RealGatePrivateCumulativeKnowledgeTests("test_real_chat_gate_synthetic_source_then_immutable_cumulative_store")
        prior.setUp()
        self.addCleanup(prior.doCleanups)
        self.prior=prior
        self.store=prior.db
        self.first=prior.push()
        with self.store._session() as con:
            self.root=json.loads(con.execute("SELECT entry_json FROM knowledge ORDER BY knowledge_id LIMIT 1").fetchone()[0])

    def insert(self,*,relation="CONFLICT",target=None,proposition="교차 영상 상충 주장",same_concept=None):
        target=self.root["knowledge_id"] if target is None else target
        kid=sha256((relation+":"+str(target)+":"+proposition).encode())
        entry=copy.deepcopy(self.root)
        entry.update(knowledge_id=kid,concept_id=same_concept if same_concept is not None else kid,
                     video_id="XyAbc987654",source_sha256=sha256(b"synthetic other video"),
                     host_event_sha256=sha256(b"synthetic other host"),
                     chat_review_sha256=sha256(b"synthetic other chat"),
                     relation=relation,target_kind="CUMULATIVE" if relation!="NEW" else "NONE",
                     target_id=target if relation!="NEW" else None)
        entry["atom"]["proposition"]=proposition
        with self.store._session() as con:
            con.execute("BEGIN IMMEDIATE")
            head,_=self.store._audit(con)
            con.execute("INSERT INTO knowledge VALUES(?,?,?)",
                        (kid,canonical(entry).decode(),json_digest(entry)))
            self.store._event(con,"ADD",kid,json_digest(entry),head)
            con.commit()
        return kid

    def test_conflict_explicitly_quarantines_existing_target_and_new_challenger(self):
        challenger=self.insert()
        result=audit_private_cumulative_knowledge_graph(self.store)
        self.assertEqual(result["active_conflict_links"],1)
        self.assertIn(self.root["knowledge_id"],result["blocked_knowledge_ids"])
        self.assertIn(challenger,result["blocked_knowledge_ids"])
        self.assertEqual(result["quarantined_rows"],2)
        with self.assertRaisesRegex(QualityNotProven,"QUESTION_REFERENCES_UNVERIFIED"):
            self.store.evidence_for_question("분산",selected_knowledge_ids=[self.root["knowledge_id"]])

    def test_unaffected_third_claim_still_retrievable(self):
        self.insert()
        remaining=sorted(set(x["knowledge_id"] for x in
               self.store.evidence_for_question("투자 위험 분산",max_items=10)["claims"]))
        self.assertNotIn(self.root["knowledge_id"],remaining)
        self.assertEqual(self.store.audit()["active_claims"],4)  # raw status; independent query gate excludes 2
        self.assertEqual(audit_private_cumulative_knowledge_graph(self.store)["active_retrievable_rows"],2)

    def test_revoked_root_quarantines_cross_video_same_descendant(self):
        child=self.insert(relation="SAME",same_concept=self.root["concept_id"])
        before=audit_private_cumulative_knowledge_graph(self.store)
        self.assertIn(child,before["active_knowledge_ids"])
        after=self.store.revoke(self.root["knowledge_id"],
            chat_review_sha256=sha256(b"synthetic revoke"),
            expected_knowledge_head=before["current_knowledge_head_sha256"])
        graph=audit_private_cumulative_knowledge_graph(self.store,
                             externally_pinned_head=after["head_sha256"])
        self.assertIn(child,graph["blocked_knowledge_ids"])
        with self.assertRaises(QualityNotProven):
            self.store.evidence_for_question("분산",selected_knowledge_ids=[child])

    def test_wrong_equivalence_concept_is_integrity_failure(self):
        self.insert(relation="SAME")  # wrong concept; appears as SAME under another concept
        with self.assertRaisesRegex(QualityNotProven,"SAME_CONCEPT_IDENTITY"):
            audit_private_cumulative_knowledge_graph(self.store)

    def test_cross_video_identical_words_distinct_concepts_not_auto_reused(self):
        self.insert(relation="NEW",proposition=self.root["atom"]["proposition"])
        graph=audit_private_cumulative_knowledge_graph(self.store)
        self.assertEqual(graph["same_text_distinct_concept_frontiers"],1)
        self.assertIn(self.root["knowledge_id"],graph["blocked_knowledge_ids"])
        with self.assertRaises(QualityNotProven):
            self.store.evidence_for_question("분산",selected_knowledge_ids=[self.root["knowledge_id"]])

    def test_missing_source_record_or_cycle_fails_closed(self):
        self.insert(target="0"*64)
        with self.assertRaisesRegex(QualityNotProven,"ORPHAN_OR_SELF"):
            audit_private_cumulative_knowledge_graph(self.store)

    def test_1500_link_chain_does_not_hit_recursion_depth(self):
        rows=[]
        root=self.root["knowledge_id"]
        for i in range(1500):
            e=copy.deepcopy(self.root)
            kid=sha256(("large chain "+str(i)).encode())
            e["knowledge_id"]=kid
            e["concept_id"]=root
            e["relation"]="SAME"
            e["target_kind"]="CUMULATIVE"
            e["target_id"]=rows[-1]["knowledge_id"] if rows else root
            e["atom"]["proposition"]="long chain unique "+str(i)
            rows.append(e)
        graph=inspect_cumulative_knowledge_graph([self.root]+rows,
                    {r["knowledge_id"]:"ACTIVE" for r in [self.root]+rows})
        self.assertEqual(graph["active_retrievable_rows"],1501)
        self.assertEqual(graph["cumulative_relationship_edges"],1500)

    def test_forged_cycle_rejected_even_if_entries_individually_hashed(self):
        a=copy.deepcopy(self.root)
        b=copy.deepcopy(self.root)
        a["knowledge_id"]=sha256(b"fake cycle a")
        b["knowledge_id"]=sha256(b"fake cycle b")
        for e,other in ((a,b),(b,a)):
            e["concept_id"]=self.root["concept_id"]
            e["target_kind"]="CUMULATIVE"
            e["relation"]="SAME"
            e["target_id"]=other["knowledge_id"]
            e["atom"]["proposition"]="cycle "+e["knowledge_id"]
        with self.assertRaisesRegex(QualityNotProven,"CUMULATIVE_CYCLE"):
            inspect_cumulative_knowledge_graph([a,b],{
                a["knowledge_id"]:"ACTIVE",b["knowledge_id"]:"ACTIVE"})

    def test_external_head_mismatch_fails_closed(self):
        with self.assertRaisesRegex(QualityNotProven,"OWNER_CHECKPOINT_DRIFT"):
            audit_private_cumulative_knowledge_graph(self.store,externally_pinned_head="1"*64)

if __name__=="__main__":
    unittest.main()