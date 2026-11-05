"""P1 requires atomic scope and dates; old graph similarity is not proof."""
import unittest
from pathlib import Path
from ire.v5 import advisory_evidence as p1

ROOT=Path(__file__).resolve().parents[3]

class EvidenceP1Tests(unittest.TestCase):
    def test_p1_atomic_fact_catalog_and_negative_cases(self):
        out=p1.audit(ROOT)
        self.assertEqual(out["atomic_source_scoped_facts"],6)
        self.assertEqual(out["question_fact_scope_tests"],8)
        self.assertEqual(out["false_legacy_graph_edges_explicitly_blocked"],5)
        self.assertTrue(out["not_all_60_legacy_claims_reverified"])

    def test_isa_foreign_tax_is_not_isa_pension_transfer(self):
        out=p1.plan("ISA 미국 배당 ETF의 외국원천세 신고는?",ROOT)
        factids={x["fact_id"] for x in out["direct_scoped_evidence"]}
        self.assertIn("P1-FUND-FOREIGN-TAX-2025",factids)
        self.assertNotIn("P1-ISA-60D",factids)
        self.assertNotIn("P1-ISA-TRANSFER-10PCT",factids)

    def test_isa_70_days_shows_deadline_but_cannot_certify_personal(self):
        out=p1.plan("ISA 만기 후 70일에 연금계좌로 이체해도 되나요?",ROOT)
        self.assertIn("P1-ISA-60D",[f["fact_id"] for f in out["direct_scoped_evidence"]])
        self.assertFalse(out["personal_trade_authorized"])
        self.assertFalse(out["all_relevant_rules_verified"])

    def test_graph_mislinks_always_reported_as_blocked(self):
        out=p1.plan("ISA 미국 배당 ETF와 ISA 만기 연금전환 세금은 어떻게 다른가요?",ROOT)
        self.assertTrue(all(x["action"]=="DO_NOT_USE_LEGACY_GRAPH_EDGE_AS_PROOF"
                            for x in out["blocked_false_core_links"]))

    def test_old_tax_year_not_auto_accepted_as_current(self):
        with self.assertRaisesRegex(p1.EvidenceP1Error,"P1_NEW_EFFECTIVE_DATE_REQUIRES"):
            p1.plan("연금저축 세액공제",ROOT,as_of="2027-01-01")

    def test_unrelated_markets_never_claim_approved_source(self):
        out=p1.plan("오늘 반도체를 매도하면 수익이 보장되나요",ROOT)
        self.assertEqual(out["direct_scoped_evidence"],[])

    def test_every_matched_fact_has_explicit_source_and_conditions(self):
        out=p1.plan("ETF NAV 괴리율 추적오차의 의미는?",ROOT)
        self.assertTrue(out["direct_scoped_evidence"])
        for r in out["direct_scoped_evidence"]:
            self.assertTrue(r["authority_url"].startswith("https://"))
            self.assertTrue(r["application_conditions"])
            self.assertTrue(r["exceptions"])
            self.assertFalse(r["currently_reopened_by_python"])

if __name__=="__main__":
    unittest.main()
