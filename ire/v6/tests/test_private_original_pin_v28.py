"""V28 synthetic ZIP/SRT byte-provenance tests, never public private subtitles."""
from __future__ import annotations

import copy
import hashlib
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path

from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from ire.v6.private_original_pin_v28 import verify_private_original_archive


class V28PrivateSourcePinTests(unittest.TestCase):
    def setUp(self):
        from ire.v6.tests.test_source_and_proof import make_srt, make_manifest, VIDEO
        from ire.v6.tests.test_stage_repair import atom,exchange
        from ire.v6.source import verify_source
        self.raw=make_srt()
        self.video=VIDEO
        self.member='samples/youtube-transcript-'+VIDEO+'.srt'
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'source.zip'
        self._make_zip()
        self.manifest=make_manifest(self.raw)
        self.source=verify_source(
            self.raw,self.manifest,expected_source_sha256=sha256(self.raw),
            expected_manifest_sha256=json_digest(self.manifest))
        self.exchange=exchange(self.source,[
            atom(self.source,'C00001',[1],[1],
                 'One bounded source sample is present in the text.',
                 stance='UNRESOLVED')])

    def _make_zip(self,extra=None):
        with zipfile.ZipFile(self.path,'w',compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr(self.member,self.raw)
            for name,data in (extra or []):
                z.writestr(name,data)

    def _args(self):
        return dict(zip_path=self.path,member_name=self.member,
            expected_zip_sha256=sha256(self.path.read_bytes()),
            expected_srt_sha256=sha256(self.raw),
            expected_video_id=self.video,
            expected_cue_count=4)

    def test_actual_zip_bytes_and_srt_bound_without_private_text(self):
        out=verify_private_original_archive(**self._args())
        self.assertEqual(out['original_cue_count'],4)
        self.assertEqual(out['srt_sha256'],sha256(self.raw))
        self.assertFalse(out['private_full_v27_answer_path_executed'])
        self.assertFalse(out['p0_go'])
        self.assertNotIn('original source',str(out).lower())

    def test_srt_literal_hash_length_60_is_rejected_even_when_zip_is_pinned(self):
        args=self._args()
        args['expected_srt_sha256']=args['expected_srt_sha256'][:60]
        with self.assertRaisesRegex(InvalidInput,'SRT_SHA256_INVALID'):
            verify_private_original_archive(**args)

    def test_modified_zip_bytes_fail_precommit(self):
        args=self._args()
        args['expected_zip_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'ARCHIVE_BYTES_MISMATCH'):
            verify_private_original_archive(**args)

    def test_zip_repacked_but_srt_same_needs_new_archive_pin(self):
        args=self._args()
        self._make_zip(extra=[('metadata.txt',b'new metadata')])
        with self.assertRaisesRegex(InvalidInput,'ARCHIVE_BYTES_MISMATCH'):
            verify_private_original_archive(**args)

    def test_source_srt_text_change_with_updated_zip_sha_still_fails(self):
        args=self._args()
        self.raw=self.raw.replace(b'A statement',b'Another statement')
        self._make_zip()
        args['expected_zip_sha256']=sha256(self.path.read_bytes())
        with self.assertRaisesRegex(InvalidInput,'SRT_BYTES_MISMATCH'):
            verify_private_original_archive(**args)

    def test_source_number_of_cues_must_match(self):
        args=self._args()
        args['expected_cue_count']=5
        with self.assertRaisesRegex(InvalidInput,'CUE_COUNT_MISMATCH'):
            verify_private_original_archive(**args)

    def test_zip_missing_member_fails(self):
        args=self._args()
        args['member_name']='other/youtube-transcript-'+self.video+'.srt'
        with self.assertRaisesRegex(InvalidInput,'MISSING_OR_DUPLICATE'):
            verify_private_original_archive(**args)

    def test_duplicate_member_name_fails(self):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',UserWarning)
            with zipfile.ZipFile(self.path,'a') as z:
                z.writestr(self.member,self.raw)
        args=self._args()
        with self.assertRaisesRegex(InvalidInput,'MISSING_OR_DUPLICATE'):
            verify_private_original_archive(**args)

    def test_mac_apple_double_metadata_rejected(self):
        args=self._args()
        args['member_name']='__MACOSX/samples/youtube-transcript-'+self.video+'.srt'
        with self.assertRaisesRegex(InvalidInput,'UNSAFE_OR_INVALID_ZIP_MEMBER'):
            verify_private_original_archive(**args)

    def test_path_traversal_rejected(self):
        args=self._args()
        args['member_name']='../samples/youtube-transcript-'+self.video+'.srt'
        with self.assertRaisesRegex(InvalidInput,'UNSAFE_OR_INVALID_ZIP_MEMBER'):
            verify_private_original_archive(**args)

    def test_exchange_requires_plan_and_pin(self):
        args=self._args()
        args['exchange']=self.exchange
        with self.assertRaisesRegex(InvalidInput,'EXCHANGE_WITHOUT_SOURCE_PLAN'):
            verify_private_original_archive(**args)

    def test_plan_requires_independent_expected_digest(self):
        args=self._args()
        args['source_manifest']=self.manifest
        with self.assertRaisesRegex(InvalidInput,'SOURCE_PLAN_PIN_REQUIRED'):
            verify_private_original_archive(**args)

    def test_real_parser_and_atomic_exchange_bind_complete_source(self):
        args=self._args()
        args['source_manifest']=self.manifest
        args['expected_manifest_sha256']=json_digest(self.manifest)
        args['exchange']=self.exchange
        r=verify_private_original_archive(**args)
        self.assertTrue(r['source_plan_verified'])
        self.assertTrue(r['atomic_exchange_verified'])
        self.assertEqual(r['atomic_candidate_count'],1)
        self.assertFalse(r['original_source_semantic_recall_independently_proven'])
        self.assertFalse(r['private_full_v27_answer_path_executed'])

    def test_changed_source_plan_bytes_refused(self):
        args=self._args()
        args['source_manifest']=copy.deepcopy(self.manifest)
        args['expected_manifest_sha256']=json_digest(self.manifest)
        args['source_manifest']['windows'][0]['text_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'PINNED_SOURCE_OR_PLAN_BYTES_MISMATCH'):
            verify_private_original_archive(**args)

    def test_original_cue_quote_forgery_rejected_after_zip_attestation(self):
        args=self._args()
        args['source_manifest']=self.manifest
        args['expected_manifest_sha256']=json_digest(self.manifest)
        args['exchange']=copy.deepcopy(self.exchange)
        args['exchange']['atoms'][0]['source_refs'][0]['quote']='FAKE SOURCE WORDS'
        with self.assertRaisesRegex(InvalidInput,'QUOTE_NOT_IN_ORIGINAL'):
            verify_private_original_archive(**args)


if __name__=='__main__':
    unittest.main()
