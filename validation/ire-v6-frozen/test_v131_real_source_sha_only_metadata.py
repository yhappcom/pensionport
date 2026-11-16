"""No owner original text; check published current real evidence only as a HOLD."""
import json
import unittest
from pathlib import Path

R=Path(__file__).with_name('V131_REAL_SOURCE_AND_DB_SHA_ONLY.json')
class V131ExistingPrivateSourceReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.d=json.loads(R.read_text())
    def test_all_1481_cues_have_hash_only_review_queue(self):
        d=self.d
        self.assertEqual(d['cue_count'],1481)
        self.assertEqual(d['segments_total'],13)
        self.assertEqual(d['segments_complete_source_cue_queue'],13)
        self.assertTrue(d['all_original_cues_accounted'])
        self.assertRegex(d['cue_queue_census_sha256'],r'^[0-9a-f]{64}$')
    def test_risk_hints_not_independent_atom_truth(self):
        d=self.d
        self.assertEqual(d['financial_hint_cues'],162)
        self.assertEqual(d['qualifier_hint_cues'],28)
        self.assertEqual(d['multi_atom_hint_cues'],30)
        self.assertFalse(d['b0001_120_cues_semantically_exhaustive'])
        self.assertEqual(d['real_b0001_provisional_atomic_proposals'],6)
    def test_never_treat_staging_db_as_operator_owned(self):
        d=self.d
        self.assertTrue(d['isolated_v1237_db_rejected_as_operational'])
        self.assertFalse(d['actual_owner_operational_db_found'])
        self.assertFalse(d['actual_owner_operational_db_reconciled'])
        self.assertFalse(d['owner_source_authoritative_independently_signed'])
    def test_12_finance_and_qa_still_no_go(self):
        d=self.d
        self.assertEqual(d['finance_open_count'],12)
        self.assertFalse(d['all_12_official_claim_specific_original_http_bytes_verified'])
        self.assertFalse(d['approved_cumulative_knowledge_advisory_pass'])
        self.assertEqual(d['v123_full_video_child_pass_count'],0)
        self.assertEqual(d['chat_final_research_candidates_released'],0)
        self.assertFalse(d['portfolio_drive_integration_started'])
        self.assertFalse(d['p0_go'])

if __name__=='__main__':unittest.main()
