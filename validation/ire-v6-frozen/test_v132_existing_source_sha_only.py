"""Public SHA-only guard; never open user-private video subtitles on CI."""
from __future__ import annotations
import json,re,unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent

class V132RealPrivateSourceSeamReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads((HERE/'V132_SOURCE_SEAM_REVERIFY_SHA_ONLY.json').read_text(encoding='utf-8'))
        cls.p=json.loads((HERE/'V131_B0001_EXPLICIT_CUE_PARTIAL_SHA_ONLY.json').read_text(encoding='utf-8'))
    def test_source_hash_video_child_count_preserved(self):
        r=self.d
        self.assertEqual(r['source_sha256'],self.p['source_sha256'])
        self.assertEqual(r['total_original_cues'],1481)
        self.assertEqual(r['existing_source_segments'],13)
        self.assertEqual(r['left_source_span'],[1,120])
        self.assertEqual(r['right_source_span'],[121,240])
        self.assertEqual(r['source_followup_span'],[120,125])
    def test_only_the_cross_scope_discourse_open_cue_is_resolved(self):
        r=self.d
        self.assertEqual(r['prior_open_cue_count'],2)
        self.assertEqual(r['now_open_cue_count'],1)
        self.assertEqual(r['open_cue_index_still'],111)
        self.assertTrue(r['cue_120_rhetorical_question_context_link_reviewed'])
        self.assertFalse(r['cue_111_audio_speaker_identity_verified'])
    def test_sha_only_source_evidence_and_genuine_hold(self):
        r=self.d
        for k in ('old_b0001_packet_sha256','new_b0001_packet_sha256',
                  'cross_segment_chat_seam_review_sha256','private_full_review_sha256'):
            self.assertRegex(r[k],r'^[a-f0-9]{64}$')
        self.assertEqual(len(r['source_followup_cue_sha256']),6)
        self.assertTrue(all(re.fullmatch(r'[a-f0-9]{64}',v) for v in r['source_followup_cue_sha256']))
        self.assertEqual(r['b0002_targeted_risk_groups_reviewed'],8)
        self.assertFalse(r['b0002_full_120_cue_atomic_completeness_verified'])
        self.assertFalse(r['whole_video_all_atomic_claims_exhausted'])
        self.assertEqual(r['v123_final_passed_child_segments'],0)
    def test_engine_and_privacy_phase_not_promoted(self):
        r=self.d
        self.assertFalse(r['owner_operational_db_externally_attested'])
        self.assertEqual(r['finance_open_claims'],12)
        self.assertFalse(r['real_advisory_approved'])
        self.assertFalse(r['knowledge_export_allowed'])
        self.assertFalse(r['p0_go'])

if __name__=='__main__':unittest.main()
