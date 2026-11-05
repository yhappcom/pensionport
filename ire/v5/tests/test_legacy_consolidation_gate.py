"""Defensive tests for bounded legacy inventory and first source-aware batch."""
from __future__ import annotations
import copy
import unittest
from pathlib import Path

from ire.v5 import legacy_consolidation_gate as gate

ROOT = Path(__file__).resolve().parents[3]


class LegacyConsolidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.master = gate.load_json(ROOT / gate.MASTER)
        cls.batch = gate.load_json(ROOT / gate.B01)
        cls.batch2 = gate.load_json(ROOT / gate.B02)
        cls.batch3 = gate.load_json(ROOT / gate.B03)

    def amended(self, mut_master=None, mut_batch=None, mut_batch2=None, mut_batch3=None):
        m = copy.deepcopy(self.master)
        b = copy.deepcopy(self.batch)
        c = copy.deepcopy(self.batch2)
        d = copy.deepcopy(self.batch3)
        if mut_master:
            mut_master(m)
        if mut_batch:
            mut_batch(b)
        if mut_batch2:
            mut_batch2(c)
        if mut_batch3:
            mut_batch3(d)
        return gate.verify(ROOT, m, b, c, d)

    def test_baseline_b01_exact_coverage(self):
        s = gate.verify(ROOT)
        self.assertEqual(s["master_claims_indexed"], 116)
        self.assertEqual(s["first_batch_claims_integrated"], 20)
        self.assertEqual(s["first_batch_video_links_checked"], 51)
        self.assertEqual(s["first_batch_source_doc_paths_mapped"], 52)
        self.assertEqual(s["preexisting_v5_education_node_core_claims"], 16)
        self.assertEqual(s["preexisting_v5_education_node_core_edges"], 32)
        self.assertEqual(s["remaining_batches_not_claimed_complete"], 3)
        self.assertEqual(s["third_batch_claims_integrated"],20)
        self.assertEqual(s["second_batch_claims_integrated"], 20)
        self.assertEqual(s["second_batch_video_links_checked"], 30)
        self.assertEqual(s["second_batch_summary_documents_read"], 27)
        self.assertFalse(s["new_claims_independently_verified_by_script"])

    def test_missing_canonical_video_cannot_pass(self):
        with self.assertRaisesRegex(gate.LegacyConsolidationError,
                                    "LEGACY_SUPPORTING_VIDEO_ID_CHANGED"):
            self.amended(mut_batch=lambda b: b["records"][0]["source_videos"][0].update(
                video_id="UNKNOWN_ID"))

    def test_original_statement_must_remain_verbatim(self):
        with self.assertRaisesRegex(gate.LegacyConsolidationError,
                                    "LEGACY_RESEARCH_STATEMENT_OR_MEANING_LOST"):
            self.amended(mut_batch=lambda b: b["records"][0].update(
                original_statement="자동으로 100% 손실 방지 확정"))

    def test_2019_pension_rule_is_not_current_without_refresh(self):
        with self.assertRaisesRegex(gate.LegacyConsolidationError,
                                    "LEGACY_TIME_SENSITIVE_FINANCIAL_LAW_WAS_AUTOPROMOTED"):
            self.amended(mut_batch=lambda b: b["records"][6].update(
                research_triage="GENERAL_EDUCATION_LINK_CANDIDATE"))

    def test_tr_etf_2025_distribution_changes_not_ignored(self):
        with self.assertRaisesRegex(gate.LegacyConsolidationError,
                                    "LEGACY_TIME_SENSITIVE_FINANCIAL_LAW_WAS_AUTOPROMOTED"):
            self.amended(mut_batch=lambda b: b["records"][16].update(
                research_triage="STRATEGY_CONTEXT_ONLY"))

    def test_els_transcript_needed_must_not_auto_approve(self):
        with self.assertRaisesRegex(gate.LegacyConsolidationError,
                                    "LEGACY_UNVERIFIED_SOURCE_GOT_PROMOTED"):
            self.amended(mut_batch=lambda b: b["records"][13].update(
                research_triage="GENERAL_EDUCATION_LINK_CANDIDATE"))

    def test_no_unearned_human_or_chat_fact_certification(self):
        with self.assertRaisesRegex(gate.LegacyConsolidationError,
                                    "LEGACY_METADATA_MISREPORTED_AS_FACT_VERIFIED"):
            self.amended(mut_batch=lambda b: b["records"][5].update(
                chat_evidence_fact_approved_this_batch=True))

    def test_existing_graph_core_reference_cannot_be_reinvented(self):
        with self.assertRaisesRegex(gate.LegacyConsolidationError,
                                    "LEGACY_EXISTING_V5_EDUCATION_GRAPH_LINK_INACCURATE"):
            self.amended(mut_batch=lambda b: b["records"][7].update(
                existing_v5_graph_core_references=[]))

    def test_thematic_similarity_does_not_equal_approved_fact(self):
        with self.assertRaisesRegex(gate.LegacyConsolidationError,
                                    "LEGACY_THEMATIC_LINK_FALSELY_APPROVED"):
            self.amended(mut_batch=lambda b: b["records"][12][
                "integrated_knowledge_links"][0].update(relation="EXACT_VERIFIED_FACT"))

    def test_future_batches_cannot_be_marked_completed(self):
        with self.assertRaisesRegex(gate.LegacyConsolidationError,
                                    "LEGACY_PARTITION_OR_COMPLETION_MISMATCH"):
            self.amended(mut_master=lambda m: m["batches"][2].update(
                state="METADATA_AND_SOURCE_DOCUMENT_TRIAGE_COMPLETED"))

    def test_legacy_document_not_found(self):
        with self.assertRaisesRegex(gate.LegacyConsolidationError,
                                    "LEGACY_VIDEO_DOCUMENT_NOT_FOUND"):
            self.amended(mut_batch=lambda b: b["records"][0]["source_videos"][0].update(
                video_document_paths=["videos/fabricated_AzY0FU-HxME.md"]))

    def test_legacy_confidence_not_equal_new_approval(self):
        with self.assertRaisesRegex(gate.LegacyConsolidationError,
                                    "LEGACY_INDEX_UNTRACED_OR_OVERPROMOTED_CLAIM"):
            self.amended(mut_master=lambda m: m["claims"][0].update(
                fact_acceptance_this_index="VERIFIED_ALL"))

    def test_no_unverified_srt_cue_claims(self):
        with self.assertRaisesRegex(gate.LegacyConsolidationError,
                                    "LEGACY_METADATA_MISREPORTED_AS_FACT_VERIFIED"):
            self.amended(mut_batch=lambda b: b["records"][17].update(
                original_srt_full_cue_coverage_reverified_this_batch=True))


    def test_second_batch_fact_approval_cannot_be_forged(self):
        with self.assertRaisesRegex(gate.LegacyConsolidationError,
                                    "LEGACY_B02_UNSUPPORTED_FACT_OR_ADVICE_APPROVED"):
            self.amended(mut_batch2=lambda b: b["records"][0].update(
                chat_evidence_fact_approved_this_batch=True))

    def test_second_batch_missing_study_document_rejected(self):
        with self.assertRaisesRegex(gate.LegacyConsolidationError,
                                    "LEGACY_B02_VIDEO_DOCUMENT_NOT_FOUND"):
            self.amended(mut_batch2=lambda b: b["records"][0]["source_videos"][0].update(
                video_document_paths=["videos/undated/fake_fkBKf67l3uo_tax.md"],
                reviewed_document_paths=["videos/undated/fake_fkBKf67l3uo_tax.md"]))

    def test_isa_foreign_tax_is_not_the_same_as_isa_pension_transfer(self):
        with self.assertRaisesRegex(gate.LegacyConsolidationError,
                                    "LEGACY_B02_ISA_FOREIGN_TAX_LINK_CONFLATED"):
            self.amended(mut_batch2=lambda b: b["records"][12].update(
                existing_v5_link_semantic_warning="NONE"))

    def test_unreviewed_2026_account_law_not_promoted(self):
        with self.assertRaisesRegex(gate.LegacyConsolidationError,
                                    "LEGACY_B02_CURRENT_TAX_MARKET_RULE_FALSELY_APPROVED"):
            self.amended(mut_batch2=lambda b: b["records"][19].update(
                research_triage="GENERAL_EDUCATION_LINK_CANDIDATE"))

    def test_original_material_video_is_not_full_transcript(self):
        with self.assertRaisesRegex(gate.LegacyConsolidationError,
                                    "LEGACY_B02_SOURCE_STATUS_MISREPRESENTED"):
            self.amended(mut_batch2=lambda b: b["records"][9]["source_videos"][0].update(
                original_full_transcript_reviewed_this_batch=True))

    def test_b02_to_b03_no_phantom_completion(self):
        with self.assertRaisesRegex(gate.LegacyConsolidationError,
                                    "LEGACY_PARTITION_OR_COMPLETION_MISMATCH"):
            self.amended(mut_master=lambda m: m["batches"][4].update(
                state="METADATA_AND_SOURCE_DOCUMENT_TRIAGE_COMPLETED"))

    def test_run_fail_prevention_must_be_documented(self):
        path = ROOT / "ire/v5/AGENTS.md"
        body = path.read_text(encoding="utf-8")
        for required in ("atomic", "preflight", "cancel-in-progress",
                         "expected_sha", "main", "failure"):
            self.assertIn(required, body)


    def test_b03_accepts_no_unverified_tax_rule(self):
        with self.assertRaisesRegex(gate.LegacyConsolidationError,"LEGACY_B03_FAKE_FACT_OR_ADVICE_APPROVAL"):
            self.amended(mut_batch3=lambda b:b["records"][1].update(
                chat_evidence_fact_approved_this_batch=True))

    def test_b03_breakeven_and_withdrawal_risk(self):
        with self.assertRaisesRegex(gate.LegacyConsolidationError,"LEGACY_B03_UNSAFE_WITHDRAWAL_OR_REPEATED_SOURCE"):
            self.amended(mut_batch3=lambda b:b["records"][4].update(
                interpretation_and_exceptions="모든 은퇴자 8% 출금은 절대 확실하고 손실이 없다고 보장됨 " * 4))

    def test_b03_isa_tax_and_dca_wrong_link_not_approved(self):
        with self.assertRaisesRegex(gate.LegacyConsolidationError,"LEGACY_B03_TAX_OR_ALLOCATION_RELATION_CONFLATED"):
            self.amended(mut_batch3=lambda b:b["records"][11].update(
                existing_v5_link_semantic_warning="NONE"))

    def test_b03_missing_source_file(self):
        with self.assertRaisesRegex(gate.LegacyConsolidationError,"LEGACY_B03_VIDEO_DOCUMENT_MISSING"):
            self.amended(mut_batch3=lambda b:b["records"][0]["source_videos"][0].update(
                video_document_paths=["videos/2026/fabricated_-71DQQIcTlc.md"],
                reviewed_document_paths=["videos/2026/fabricated_-71DQQIcTlc.md"]))

    def test_b03_remaining_batch_cannot_be_marked_complete(self):
        with self.assertRaisesRegex(gate.LegacyConsolidationError,"LEGACY_PARTITION_OR_COMPLETION_MISMATCH"):
            self.amended(mut_master=lambda m:m["batches"][3].update(
                state="METADATA_AND_SOURCE_DOCUMENT_TRIAGE_COMPLETED"))


if __name__ == "__main__":
    unittest.main()
