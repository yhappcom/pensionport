"""Public-safe synthetic tests: no owner SRT or private V75 data."""
import hashlib
from pathlib import Path
import tempfile
import unittest
import zipfile

from v76_private_resume_preflight import source_audit, bundle_audit, preflight


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class ResumePreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.vid = 'TESTid00001'
        self.texts = ['수익은 보장되지 않습니다', '계좌 유형을 확인하세요']
        self.srt = ('\n\n'.join(f'{i}\n00:00:0{i},000 --> 00:00:0{i+1},000\n{text}'
                             for i, text in enumerate(self.texts, 1))).encode('utf-8')
        self.source = self.root / 'owner.zip'
        with zipfile.ZipFile(self.source, 'w') as z:
            z.writestr('sources/youtube-transcript-' + self.vid + '.srt', self.srt)
        self.census = [(1, self.vid, 2, sha(self.srt))]
        self.anchors = {(self.vid, 1): sha(self.texts[0].encode())}

    def test_synthetic_source_success_and_no_raw_text(self):
        out = source_audit(self.source, sha(self.source.read_bytes()), self.census, self.anchors)
        self.assertEqual(out['original_cues_checked'], 2)
        self.assertEqual(out['unique_original_anchor_cues_checked'], 1)
        self.assertNotIn(self.texts[0], str(out))

    def test_mismatched_source_archive_rejected(self):
        with self.assertRaisesRegex(ValueError, 'SOURCE_SHA_MISMATCH'):
            source_audit(self.source, sha(b'wrong'), self.census, self.anchors)

    def test_mismatched_cue_anchor_rejected(self):
        with self.assertRaisesRegex(ValueError, 'SOURCE_CUE_ANCHOR_SHA_MISMATCH'):
            source_audit(self.source, sha(self.source.read_bytes()), self.census,
                         {(self.vid, 1): sha(b'altered')})

    def make_bundle(self, files):
        bundle = self.root / 'recovery.zip'
        with zipfile.ZipFile(bundle, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            for k, v in files.items():
                z.writestr(k, v)
        expected = {name: sha(body) for name, body in files.items()}
        return bundle, expected

    def test_bundle_positive_four_exact_hashes(self):
        files = {'m.json': b'meaning', 'queue.json': b'queue',
                 'r.json': b'receipt', 'events.sqlite': b'sqlite'}
        bundle, hashes = self.make_bundle(files)
        out = bundle_audit(bundle, sha(bundle.read_bytes()), bundle.stat().st_size, 4,
                           {k: hashes[v] for k, v in zip(('meaning60','queue298','receipt','sqlite'), files)})
        self.assertTrue(out['v75_queue_exact_bytes_available_for_source_first_host_review'])

    def test_missing_queue_hash_fails_closed(self):
        files = {'m.json': b'meaning', 'queue.json': b'queue',
                 'r.json': b'receipt', 'events.sqlite': b'sqlite'}
        bundle, hashes = self.make_bundle(files)
        with self.assertRaisesRegex(ValueError, 'REQUIRED_RECEIPT_BLOB_MISSING:queue298'):
            bundle_audit(bundle, sha(bundle.read_bytes()), bundle.stat().st_size, 4,
                         {'queue298': sha(b'different')})

    def test_unsafe_zip_member_rejected(self):
        bundle, _ = self.make_bundle({'../escape.json': b'unsafe'})
        with self.assertRaisesRegex(ValueError, 'UNSAFE_ZIP_MEMBER_NAME'):
            bundle_audit(bundle, sha(bundle.read_bytes()), bundle.stat().st_size, 1, {})

    def test_bundle_wrong_sha_fails_before_inspecting(self):
        bundle, _ = self.make_bundle({'queue.json': b'queue'})
        with self.assertRaisesRegex(ValueError, 'BUNDLE_SHA_OR_SIZE_MISMATCH'):
            bundle_audit(bundle, sha(b'alt'), bundle.stat().st_size, 1, {})

    def test_real_config_missing_private_source_fails_closed(self):
        out = preflight(self.root / 'missing_owner.zip', None)
        self.assertEqual(out['status'], 'BLOCKED_SOURCE_PROVENANCE')
        self.assertEqual(out['new_semantic_parent_reviews'], 0)
        self.assertFalse(out['p0_go'])
        self.assertFalse(out['personal_advice_approved'])


if __name__ == '__main__':
    unittest.main()