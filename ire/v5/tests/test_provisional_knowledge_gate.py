"""Check 53 new claims are linked to 20 legacy nodes without unsafe promotion."""
import copy
import unittest
from pathlib import Path
from unittest.mock import patch
from ire.v5 import provisional_knowledge_gate as m

ROOT=Path(__file__).resolve().parents[3]

class IntegrationTests(unittest.TestCase):
    def test_actual_20_plus_five_joins_are_present(self):
        x=m.audit(ROOT)
        self.assertEqual(x["core_claims_unchanged"],20)
        self.assertEqual(x["new_source_study_videos"],5)
        self.assertEqual(x["new_research_claims"],53)
        self.assertEqual(x["linked_research_edges"],101)
        self.assertEqual(x["core_nodes_receiving_new_evidence"],17)
        self.assertEqual(x["external_personal_finance_excluded"],2)
        self.assertEqual(x["challenged_core_nodes"],4)
        self.assertFalse(x["advisory_go"])

    def mutate(self,fn):
        original=m.load
        def fake(path):
            value=original(path)
            if str(path).endswith("provisional_integrated_20_plus_5_20261104.json"):
                value=copy.deepcopy(value)
                fn(value)
            return value
        with patch.object(m,"load",side_effect=fake):
            return m.audit(ROOT)

    def test_missing_one_link_is_detected(self):
        with self.assertRaisesRegex(m.IntegrationError,"INTEGRATION_NEW_EVIDENCE_LOST"):
            self.mutate(lambda x:x["nodes"][0]["incoming_research_links"].pop())

    def test_forged_advice_approval_fails(self):
        with self.assertRaisesRegex(m.IntegrationError,"INTEGRATION_UNVERIFIED_CLAIM_PROMOTED"):
            self.mutate(lambda x:x["nodes"][0].update(advisory_approved=True))

    def test_legacy_original_cannot_be_silently_edited(self):
        with self.assertRaisesRegex(m.IntegrationError,"INTEGRATION_ORIGINAL_KNOWLEDGE_CHANGED"):
            self.mutate(lambda x:x["nodes"][0].update(original_legacy_claim="falsified"))

    def test_out_of_scope_car_debt_cannot_be_merged(self):
        with self.assertRaisesRegex(m.IntegrationError,"INTEGRATION_UNRELATED_CONSUMER_FINANCE_NOT_EXCLUDED"):
            self.mutate(lambda x:x["excluded_non_investment_items"].clear())
