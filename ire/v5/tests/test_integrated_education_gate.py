"""Prove that all 13 concepts retain source lineage and cannot auto-promote."""
import copy
import unittest
from pathlib import Path

from ire.v5 import integrated_education_gate as gate

ROOT=Path(__file__).resolve().parents[3]
GRAPH=ROOT/"ire/v5/advisory_knowledge/integrated_education13_20261104.json"

class IntegratedEducationGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=gate.read(ROOT,str(gate.GRAPH))

    def modify(self,fn):
        o=copy.deepcopy(self.original)
        fn(o)
        return gate.verify(ROOT,o)

    def test_integration_4_plus_9_is_13_with_17_source_links(self):
        actual=gate.verify(ROOT)
        self.assertEqual(actual["knowledge_concepts"],13)
        self.assertEqual(actual["source_evidence_links"],17)
        self.assertEqual(actual["new_concepts_deduplicated"],9)
        self.assertEqual(actual["corroborating_new_source_claims"],12)
        self.assertEqual(actual["legacy_20_nodes"],20)
        self.assertEqual(actual["videos_with_original_cue_lineage"],5)
        self.assertEqual(actual["unassessed_or_blocked_claims_auto_promoted"],0)
        self.assertEqual(actual["independent_blind_human_verdicts"],0)
        self.assertFalse(actual["personal_financial_advice_go"])

    def test_prior_four_education_assertions_are_immutable(self):
        with self.assertRaisesRegex(gate.GraphGateError,
                                    "GRAPH_SILENT_CHANGE_TO_PREVIOUS_EDUCATION_FACT"):
            self.modify(lambda g:g["nodes"][0].update(
                safe_general_statement="현재 ISA는 모든 사람이 어떤 소득에도 전액 비과세된다고 보장합니다."))

    def test_cannot_drop_one_of_two_video_supports_for_age_rule(self):
        def change(g):
            node=next(x for x in g["nodes"] if x["knowledge_id"]=="EDU-KR-PENSION-55-5")
            node["source_links"].pop()
        with self.assertRaisesRegex(gate.GraphGateError,"GRAPH_EVIDENCE_LINKS_LOST"):
            self.modify(change)

    def test_no_personalized_advice_or_blind_approval_escalation(self):
        with self.assertRaisesRegex(gate.GraphGateError,"GRAPH_CONCEPT_UNAUTHORIZED_APPROVAL"):
            self.modify(lambda g:g["nodes"][0].update(
                personalized_advice_approved=True))

    def test_overall_go_must_remain_false(self):
        with self.assertRaisesRegex(gate.GraphGateError,"GRAPH_FALSE_APPROVAL"):
            self.modify(lambda g:g.update(formal_financial_advice_approved=True))

    def test_source_cue_hash_provenance_must_match_original(self):
        def change(g):
            g["nodes"][0]["source_links"][0]["original_cue_span_sha256"]="0"*64
        with self.assertRaisesRegex(gate.GraphGateError,
                                    "GRAPH_EXISTING_ORIGINAL_CUE_PROVENANCE_CHANGED"):
            self.modify(change)

    def test_new_source_cue_hash_provenance_must_match_original(self):
        def change(g):
            node=next(x for x in g["nodes"] if x["knowledge_id"]=="EDU-IRP-LIFECYCLE")
            node["source_links"][0]["original_cue_span_sha256"]="0"*64
        with self.assertRaisesRegex(gate.GraphGateError,
                                    "GRAPH_NEW_CUE_OR_AUTHORITY_MISMATCH"):
            self.modify(change)

    def test_catalog_must_not_falsely_claim_human_verification(self):
        with self.assertRaisesRegex(gate.GraphGateError,
                                    "GRAPH_FABRICATED_INDEPENDENT_SOURCE"):
            self.modify(lambda g:g["source_reference_catalog"][0].update(
                source_verified_by_external_human=True))

    def test_unreviewed_historical_claim_cannot_be_inserted(self):
        def change(g):
            node=next(x for x in g["nodes"] if x["knowledge_id"]=="EDU-ETF-NAV-TRACKING")
            node["source_links"][0]["source_claim_id"]="E229-06"
        with self.assertRaisesRegex(gate.GraphGateError,
                                    "GRAPH_NEW_CUE_OR_AUTHORITY_MISMATCH"):
            self.modify(change)

    def test_missing_legacy_reference_must_fail(self):
        def change(g):
            node=g["nodes"][0]
            node["existing_core_claim_ids"].append("FAKE-NONEXISTENT")
        with self.assertRaisesRegex(gate.GraphGateError,
                                    "GRAPH_EXISTING_CORE_CLAIM_LINEAGE_CHANGED"):
            self.modify(change)

if __name__=="__main__":
    unittest.main()
