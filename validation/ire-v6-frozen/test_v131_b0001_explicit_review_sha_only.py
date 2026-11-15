"""Public SHA receipt of private B0001 actual cue review. No private text."""
import json
import unittest
from pathlib import Path
P=Path(__file__).with_name('V131_B0001_EXPLICIT_CUE_PARTIAL_SHA_ONLY.json')
class V131B0001ExplicitChatReviewReceipt(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.r=json.loads(P.read_text(encoding='utf-8'))
    def test_source_first_cue_count_and_partial_atom_manifest(self):
        d=self.r
        self.assertEqual(d['b0001_first_cue'],1)
        self.assertEqual(d['b0001_last_cue'],120)
        self.assertEqual(d['exact_cue_rows_reviewed'],120)
        self.assertEqual(d['provisional_atoms_submitted_for_structural_audit'],12)
    def test_unresolved_111_and_120_keep_hold(self):
        d=self.r
        self.assertEqual(d['unresolved_cue_indices'],[111,120])
        self.assertEqual(d['b0001_status'],'HOLD_OPEN_CUE_DISPOSITIONS')
        self.assertEqual(d['full_source_13_segments_v123_final_passed'],0)
        self.assertFalse(d['v123_final_gate_passed'])
        self.assertFalse(d['all_atomic_claims_exhausted'])
        self.assertFalse(d['p0_go'])
    def test_sha_only_cue_review_stored_off_github(self):
        d=self.r
        self.assertRegex(d['cue_dispositions_sha256'],r'^[a-f0-9]{64}$')
        self.assertRegex(d['b0001_packet_sha256'],r'^[a-f0-9]{64}$')
        self.assertRegex(d['source_sha256'],r'^[a-f0-9]{64}$')
        self.assertNotIn('source_text',d)
if __name__=='__main__':unittest.main()
