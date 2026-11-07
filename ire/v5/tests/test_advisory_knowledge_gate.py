"""Adversarial 20 legacy claim and five real-indexed SRT integration tests."""
import copy
import unittest
from pathlib import Path

from ire.v5.advisory_knowledge_gate import (
    verify_core20, read_json, KnowledgeGateError)
from ire.v5.new_video_gate import verify_five

ROOT=Path(__file__).resolve().parents[3]
C=ROOT/"ire/v5/advisory_knowledge/core20_candidates_20261104.json"
F=ROOT/"ire/v5/advisory_knowledge/five_video_intake_20261104.json"

class TwentyPlusFiveTests(unittest.TestCase):
    def setUp(self):
        self.c=read_json(C)
        self.f=read_json(F)

    def test_real_20_claims_five_domains_and_sources(self):
        r=verify_core20(ROOT,self.c)
        self.assertEqual(r["claims_reviewed"],20)
        self.assertEqual(r["official_source_candidates"],11)
        self.assertEqual(r["claim_to_evidence_links"],33)
        self.assertEqual(sorted(r["by_domain"].values()),[4]*5)
        self.assertEqual(r["independent_financial_fact_approvals"],0)
        self.assertEqual(r["advisory_items_approved"],0)

    def test_five_new_sources_are_not_claimed_analyzed(self):
        r=verify_five(ROOT,self.f)
        self.assertEqual(r["registered_videos"],5)
        self.assertEqual(r["source_cues"],3313)
        self.assertEqual(r["semantic_analyses_completed"],0)
        self.assertEqual(r["approved_new_relations"],0)
        self.assertFalse(r["advisory_go"])

    def test_claim_text_mutation_breaks_lineage(self):
        x=copy.deepcopy(self.c)
        x["claims"][0]["legacy_claim"]="This was never the source claim"
        with self.assertRaisesRegex(KnowledgeGateError,"SOURCE_PROVENANCE"):
            verify_core20(ROOT,x)

    def test_forged_promotion_is_blocked(self):
        x=copy.deepcopy(self.c)
        x["claims"][3]["approved_for_personalized_advice"]=True
        with self.assertRaisesRegex(KnowledgeGateError,"UNVERIFIED_FINANCIAL_ADVICE"):
            verify_core20(ROOT,x)

    def test_legacy_claim_ledger_wrong_sha_is_blocked(self):
        x=copy.deepcopy(self.c)
        x["legacy_ledger_blob_sha1"]="0"*40
        with self.assertRaisesRegex(KnowledgeGateError,"LEGACY_LEDGER_BLOB_MISMATCH"):
            verify_core20(ROOT,x)

    def test_missing_evidence_and_scope_is_blocked(self):
        x=copy.deepcopy(self.c)
        x["claims"][0]["evidence_source_ids"]=[]
        with self.assertRaisesRegex(KnowledgeGateError,"CLAIM_OFFICIAL_EVIDENCE_MISSING"):
            verify_core20(ROOT,x)
        x=copy.deepcopy(self.c)
        x["claims"][0]["condition"]=""
        with self.assertRaisesRegex(KnowledgeGateError,"CONDITIONS_OR_EXCEPTIONS"):
            verify_core20(ROOT,x)

    def test_nonofficial_source_host_is_blocked(self):
        x=copy.deepcopy(self.c)
        x["sources"][0]["url"]="https://unofficial.example.com/rules"
        with self.assertRaisesRegex(KnowledgeGateError,"EVIDENCE_UNTRUSTED_HOST"):
            verify_core20(ROOT,x)

    def test_policy_proposal_cannot_be_called_enacted_law(self):
        x=copy.deepcopy(self.c)
        target=next(s for s in x["sources"] if s["source_id"]=="IRP-PROPOSAL")
        target["kind"]="LAW_TEXT"
        with self.assertRaisesRegex(KnowledgeGateError,"IRP_PROPOSAL_MISCLASSIFIED"):
            verify_core20(ROOT,x)

    def test_five_original_source_hash_cannot_be_replaced(self):
        x=copy.deepcopy(self.f)
        x["items"][0]["source_sha256"]="0"*64
        with self.assertRaisesRegex(KnowledgeGateError,"FIVE_ORIGINAL_VIDEO_ID_MISMATCH"):
            verify_five(ROOT,x)

    def test_existing_research_id_must_not_be_called_new(self):
        x=copy.deepcopy(self.f)
        x["items"][0]["video_id"]="4TFtEQxSM38"
        with self.assertRaises(KnowledgeGateError):
            verify_five(ROOT,x)

    def test_topic_title_hint_cannot_be_final_relation(self):
        x=copy.deepcopy(self.f)
        x["items"][0]["knowledge_relations_adjudicated"]=True
        with self.assertRaisesRegex(KnowledgeGateError,"FIVE_UNVERIFIED_ADVICE_APPROVAL"):
            verify_five(ROOT,x)

    def test_semantic_analysis_must_not_be_faked(self):
        x=copy.deepcopy(self.f)
        x["semantic_video_analyses_completed_in_this_stage"]=5
        with self.assertRaisesRegex(KnowledgeGateError,"FIVE_FALSE_PROGRESS"):
            verify_five(ROOT,x)

    def test_cross_topic_legacy_match_must_not_be_inferred(self):
        x=copy.deepcopy(self.f)
        x["items"][0]["legacy_claim_ids_for_future_comparison"]=["GOMHEE-C97"]
        with self.assertRaisesRegex(KnowledgeGateError,"FIVE_UNSUPPORTED_RELATION"):
            verify_five(ROOT,x)

if __name__=="__main__":
    unittest.main()
