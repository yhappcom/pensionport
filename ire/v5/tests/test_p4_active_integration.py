"""P4 can actively retrieve 22 education items but never promote W41-67."""
import copy
from pathlib import Path
import unittest

from ire.v5 import p4_active_integration as p4

ROOT = Path(__file__).resolve().parents[3]


class P4ActiveIntegrationTests(unittest.TestCase):
    def test_materialized_graph_integrates_13_and_9_without_master_mutation(self):
        g = p4.load(ROOT)
        self.assertEqual(g["active_education_node_count"], 22)
        self.assertEqual(g["quarantined_p3_window_count"], 27)
        self.assertEqual(g["legacy_claims_preserved"], 116)
        self.assertEqual(g["formal_master_merges"], 0)
        self.assertEqual(g["p3_verified_atomic_claims"], 0)
        self.assertEqual(g["release"], "ACTIVE_EDUCATION_RETRIEVAL_ONLY")

    def test_isa_pension_cross_namespace_retrieval(self):
        out = p4.retrieve(ROOT, "ISA 만기자금 연금전환 60일", limit=22)
        got = {x["knowledge_id"] for x in out["items"]}
        self.assertIn("EDU-KR-ISA-TO-PENSION-2026-01", got)
        self.assertIn("V5-001-40-ISA_MATURITY_TO_PENSION", got)
        self.assertEqual(out["P3_promoted_fact_count"], 0)

    def test_pension_tax_1500_cross_namespace_retrieval(self):
        out = p4.retrieve(ROOT, "사적연금 1,500만원 분리과세", limit=22)
        got = {x["knowledge_id"] for x in out["items"]}
        self.assertIn("EDU-KR-PRIVATE-PENSION-1500-2026-01", got)
        self.assertIn("V5-001-40-PRIVATE_PENSION_1500_TAX", got)

    def test_p3_unreviewed_windows_not_active_education(self):
        g = p4.load(ROOT)
        self.assertFalse(any("W0004" in n["knowledge_id"] for n in g["nodes"]))
        manifest = p4.read(ROOT / p4.MANIFEST)
        self.assertTrue(all(not w["formal_claim_approved"]
                            and not w["financial_fact_verified"]
                            and not w["knowledge_node_created"]
                            for w in manifest["p3_pending_windows"]))

    def test_any_forged_p3_approval_blocks_integrated_graph(self):
        m = p4.read(ROOT / p4.MANIFEST)
        m["p3_pending_windows"][0]["financial_fact_verified"] = True
        with self.assertRaisesRegex(p4.P4IntegrationError,
                                    "P4_UNVERIFIED_P3_PROMOTION"):
            p4.load(ROOT, manifest_override=m)

    def test_unsupported_equal_relation_is_rejected(self):
        m = p4.read(ROOT / p4.MANIFEST)
        m["cross_namespace_education_edges"][0]["relation"] = "IDENTICAL_FINANCIAL_FACT"
        with self.assertRaisesRegex(p4.P4IntegrationError, "P4_ILLEGAL_EQUIVALENCE"):
            p4.load(ROOT, manifest_override=m)

    def test_tampered_node_statement_is_rejected(self):
        m = p4.read(ROOT / p4.MANIFEST)
        m["nodes"][0]["statement"] = "반드시 수익이 보장됩니다"
        with self.assertRaisesRegex(p4.P4IntegrationError,
                                    "P4_LEGACY_NODE|P4_FIRST40_NODE"):
            p4.load(ROOT, manifest_override=m)

    def test_forged_approval_flags_rejected(self):
        m = p4.read(ROOT / p4.MANIFEST)
        m["P3_formal_claim_approvals"] = 1
        with self.assertRaisesRegex(p4.P4IntegrationError, "P4_FALSE_RELEASE"):
            p4.load(ROOT, manifest_override=m)

    def test_unrelated_and_personal_order_returns_no_claims(self):
        self.assertEqual(p4.retrieve(ROOT, "영화관 주차권 안내")["match_count"], 0)
        self.assertEqual(p4.retrieve(ROOT, "내 계좌에서 전량 매도해줘",
                                     intent="order_execution")["match_count"], 0)

    def test_catalog_audit_is_real_live_retrieval(self):
        a = p4.audit(ROOT)
        self.assertEqual(a["integrated_education_nodes"], 22)
        self.assertEqual(a["actual_integrated_queries_verified"], 3)
        self.assertFalse(a["legacy_master_116_changed"])
        self.assertEqual(a["P3_new_approved_facts"], 0)


if __name__ == "__main__":
    unittest.main()
