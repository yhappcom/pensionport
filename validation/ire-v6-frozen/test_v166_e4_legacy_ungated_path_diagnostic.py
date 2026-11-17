"""V166 E4 diagnostic: old V128 research writer still bypasses E4 provenance.

GREEN here means the bypass was DETECTED, not that E4 approval succeeded.
This is intentionally part of the E4 failure receipt to keep E5 blocked until
the sole supported publication route enforces E4 and historical routing is
restricted or explicitly quarantined for non-advice uses.
"""
from __future__ import annotations
import json
import unittest
from test_v166_e3_chat_decision_delivery import V166E3NativeDecisionDelivery


class E4LegacyUngatedResearchPublicationDiagnostic(unittest.TestCase):
    def test_e4_ungated_legacy_research_writer_is_still_reachable(self):
        f=V166E3NativeDecisionDelivery(
            "test_01_all_chat_approved_children_preserve_research_only_pass")
        f.setUp()
        try:
            # Absolutely no E4 manifest and NO trusted official fetch.
            # Historical V123 synthetic 'government' body still passes here.
            output=f.run_host()
            counts=f.fx._counts()
            self.assertEqual(output["explicit_e3_status"],
                             "PUBLISHED_RESEARCH_CANDIDATES_ONLY")
            self.assertEqual(counts["knowledge"],3)
            self.assertEqual(counts["parent_publications"],1)
            self.assertFalse(output["formal_financial_fact_approved"])
            print(json.dumps({
                "schema":"V166_E4_LEGACY_UNGATED_PUBLICATION_DIAGNOSTIC_V1",
                "legacy_research_path_accessible_without_e4":True,
                "synthetic_knowledge_entries_created":counts["knowledge"],
                "formal_financial_fact_approved":False,
                "e4_engine_pass":False,
                "next_step_e5_authorized":False,
            },sort_keys=True))
        finally:
            f.doCleanups()


if __name__=="__main__":
    unittest.main()
