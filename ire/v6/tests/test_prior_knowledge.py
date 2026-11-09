"""Protected master/P4 content and no-auto-merge candidate regression tests."""
from __future__ import annotations
import copy
import json
import unittest
from pathlib import Path

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from ire.v6.prior_knowledge import _index_prior,audit_prior_candidates,MASTER_BLOB


ROOT=Path(__file__).resolve().parents[3]


class PriorKnowledgeTests(unittest.TestCase):
    def setUp(self):
        from ire.v6.tests.test_atomic_exchange import HostAtomExchangeTests
        fx=HostAtomExchangeTests(methodName="test_all_cues_number_context_and_stance_bound_but_not_semantic_gold")
        fx.setUp()
        self.addCleanup(fx.doCleanups)
        self.fx=fx
        self.master=(ROOT/"data/claims.jsonl").read_bytes()
        self.p22=(ROOT/"ire/v5/advisory_knowledge/p4_integrated_scoped_education22_20261106.json").read_bytes()
        self.p7=(ROOT/"ire/v5/advisory_knowledge/p4_p3_incremental_education29_20261106.json").read_bytes()
        self.index=_index_prior(self.master,self.p22,self.p7)
        self.inputs={"master116_bytes":self.master,"p4_22_bytes":self.p22,
                     "p4_7_bytes":self.p7,"relations":[]}
        for atom in fx.exchange["atoms"]:
            self.inputs["relations"].append({
                "claim_id":atom["claim_id"],
                "candidate_source_sha256":fx.source.source_sha256,
                "target_kind":"NONE","target_id":None,
                "target_content_sha256":None,"relationship":"NOVEL_PENDING",
                "rationale":"아직 독립 의미 검토가 완료되지 않은 신규 주장 후보",
                "independent_semantic_review_verified":False,
                "personalized_action_approved":False,
            })
        self.inputs["relations"][0].update({
            "target_kind":"MASTER116","target_id":"GOMHEE-C01",
            "target_content_sha256":self.index[("MASTER116","GOMHEE-C01")],
            "relationship":"SAME_PENDING"})
        self.inputs["relations"][1].update({
            "target_kind":"P4_EDUCATION","target_id":"EDU-DCA-DIVERSIFICATION",
            "target_content_sha256":self.index[("P4_EDUCATION","EDU-DCA-DIVERSIFICATION")],
            "relationship":"EXTENDS_PENDING"})

    def test_116_and_p4_29_are_replayed_without_approval(self):
        result=audit_prior_candidates(self.fx.source,self.fx.exchange,self.inputs)
        self.assertEqual(result["protected_master_claims_replayed"],116)
        self.assertEqual(result["p4_general_education_context_nodes_replayed"],29)
        self.assertEqual(result["host_candidate_atoms_accounted_for"],3)
        self.assertEqual(result["pending_relation_count"],3)
        self.assertFalse(result["prior_semantic_relation_independently_verified"])
        self.assertFalse(result["knowledge_auto_merged"])
        self.assertFalse(result["advisory_personal_action_approved"])

    def test_mutated_master_or_p4_bytes_rejected(self):
        for field in ("master116_bytes","p4_22_bytes","p4_7_bytes"):
            data=copy.deepcopy(self.inputs)
            data[field]=data[field]+b" "
            with self.subTest(field=field),self.assertRaises(InvalidInput):
                audit_prior_candidates(self.fx.source,self.fx.exchange,data)

    def test_relation_must_match_actual_prior_content(self):
        data=copy.deepcopy(self.inputs)
        data["relations"][0]["target_content_sha256"]="0"*64
        with self.assertRaisesRegex(InvalidInput,"TARGET_CONTENT_DRIFT"):
            audit_prior_candidates(self.fx.source,self.fx.exchange,data)

    def test_cannot_self_certify_or_automerge_new_knowledge(self):
        for field in ("independent_semantic_review_verified","personalized_action_approved"):
            data=copy.deepcopy(self.inputs)
            data["relations"][0][field]=True
            with self.assertRaisesRegex(InvalidInput,"SELF_APPROVAL"):
                audit_prior_candidates(self.fx.source,self.fx.exchange,data)

    def test_every_atom_requires_prior_disposition(self):
        data=copy.deepcopy(self.inputs)
        data["relations"].pop()
        with self.assertRaisesRegex(InvalidInput,"EVERY_HOST_ATOM"):
            audit_prior_candidates(self.fx.source,self.fx.exchange,data)

    def test_knowledge_and_atomic_replay_share_owner_bound_snapshot(self):
        owner,pin=self.fx.attest()
        result=self.fx.store.snapshot_with_atomic_exchange(
            scope_id="host_scope",raw=self.fx.raw,manifest=self.fx.manifest,
            inventory_bytes=owner,expected_inventory_sha256=pin,
            exchange=self.fx.exchange,knowledge=self.inputs)
        self.assertEqual(result["knowledge_audit"]["protected_master_claims_replayed"],116)
        self.assertEqual(result["knowledge_audit"]["p4_general_education_context_nodes_replayed"],29)
        self.assertFalse(result["knowledge_audit"]["knowledge_auto_merged"])
        self.assertFalse(result["p0_go"])


if __name__=="__main__":
    unittest.main()
