"""Metadata-only fail-closed tests; all source/ChatGPT data remains private."""
import copy
import json
import unittest
from pathlib import Path
from v144_owner_quarantine_readiness_gate import (
    assess_real_source_preflight, require_native_v123_release_from_provisional,
    QuarantineEvidenceNotComplete,
)


class V144RealSourcePreparationSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta=json.loads((Path(__file__).parent/'V144_SOURCE_FIRST_SHA_ONLY.json').read_text('utf-8'))

    def test_01_real_source_preflight_explicitly_holds(self):
        out=assess_real_source_preflight(self.meta)
        self.assertFalse(out['knowledge_export_allowed'])
        self.assertFalse(out['p0_go'])
        self.assertTrue(out['canonical_v6_host_replay_required'])
        self.assertEqual(out['proposed_quarantine_cues'],52)

    def test_02_cannot_self_attest_source_scope_or_open_counts(self):
        for key, fake in [('source_sha256','0'*64),('original_cue_count',1480),
                ('candidate_high_impact_cue_quarantines',51),
                ('context_classifiable_audio_not_authenticated',35),
                ('v142_original_open_cues',87),
                ('claims_adjacent_to_quarantined_cues_for_dependency_review',82)]:
            with self.subTest(key=key):
                v=copy.deepcopy(self.meta);v[key]=fake
                with self.assertRaises(QuarantineEvidenceNotComplete):
                    assess_real_source_preflight(v)

    def test_03_unverified_v6_host_cannot_be_marked_ready(self):
        data=copy.deepcopy(self.meta)
        data['v6_owner_host_receipts_verified']=13
        with self.assertRaises(QuarantineEvidenceNotComplete):
            assess_real_source_preflight(data)

    def test_04_v123_or_v128_self_approval_denied(self):
        for field, forged in [('v123_final_approved_segments',13),
                              ('v128_private_knowledge_entries_published',191),
                              ('p0_go',True),('personalized_advice_approved',True)]:
            with self.subTest(field=field):
                data=copy.deepcopy(self.meta);data[field]=forged
                with self.assertRaises(QuarantineEvidenceNotComplete):
                    assess_real_source_preflight(data)

    def test_05_cannot_pretend_original_audio_is_present(self):
        data=copy.deepcopy(self.meta);data['original_audio_available_in_user_original_archive']=True
        with self.assertRaises(QuarantineEvidenceNotComplete):
            assess_real_source_preflight(data)

    def test_06_v141_provisional_atom_ids_not_native_v6_digest(self):
        data=copy.deepcopy(self.meta)
        data['v123_canonical_atom_sha256_not_yet_bound']=False
        with self.assertRaises(QuarantineEvidenceNotComplete):
            assess_real_source_preflight(data)

    def test_07_missing_or_fake_owner_sha_digests_fail_closed(self):
        for field in ('quarantine_rows_digest_sha256','atom_preparation_rows_digest_sha256',
                      'segment_preflight_digest_sha256'):
            with self.subTest(field=field):
                data=copy.deepcopy(self.meta);data[field]='notahash'
                with self.assertRaises(QuarantineEvidenceNotComplete):
                    assess_real_source_preflight(data)

    def test_08_provisional_packet_never_promoted_even_if_consistent(self):
        with self.assertRaisesRegex(QuarantineEvidenceNotComplete,'NOT_V123_APPROVAL'):
            require_native_v123_release_from_provisional(self.meta)

if __name__=='__main__':
    unittest.main(verbosity=2)
