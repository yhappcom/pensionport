"""V29 synthetic source-context negative controls and source blob pins (not gold)."""
from __future__ import annotations

import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from ire.v6.errors import InvalidInput
from ire.v6.private_replay_receipt_v29 import (
    attest_v29_code_blobs, audit_elided_pension_basis_v29)


class V29PrivateReplayReceiptTests(unittest.TestCase):
    def setUp(self):
        # Lazy fixtures avoid rediscovering imported older test-case methods.
        from ire.v6.tests.test_stage_repair import fixture,atom,exchange
        self.src=fixture([
            '연금',
            '저축의 인출 조건을 알아봅니다.',
            '세액공제를 받지 않은 원금은',
            '언제든 인출할 수 있다고 소개합니다.',
        ])
        self.ex=exchange(self.src,[
            atom(self.src,'C00001',[1,2],[1,2],
                 '연금저축의 인출 조건을 설명한다.',stance='UNRESOLVED'),
            atom(self.src,'C00002',[3,4],[3,4],
                 '비공제 원금은 언제든 인출할 수 있다.',stance='UNRESOLVED'),
        ])
        self.q='연금저축에서 비공제 원금은 인출할 수 있나요?'
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        (self.root/'ire/v5').mkdir(parents=True)
        self.file=self.root/'ire/v5/synthetic.py'
        self.file.write_text('print("synthetic only")\n',encoding='utf-8')
        self.gitsha=self._hash(self.file)

    @staticmethod
    def _hash(path):
        b=path.read_bytes()
        return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()

    def test_elided_pension_subject_mislabeled_off_topic_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'V29_PENSION_BASIS_CONTEXT_ELISION_UNSELECTED'):
            audit_elided_pension_basis_v29(self.src,self.ex,self.q,['C00001'])

    def test_explicitly_selected_elided_claim_allowed_without_gold(self):
        r=audit_elided_pension_basis_v29(self.src,self.ex,self.q,['C00001','C00002'])
        self.assertEqual(r['selected_count'],2)
        self.assertEqual(r['suspicious_elided_unselected_count'],0)
        self.assertFalse(r['source_semantic_completeness_independently_proven'])

    def test_other_subject_is_not_automatically_pension_claim(self):
        r=audit_elided_pension_basis_v29(self.src,self.ex,
                                        'ETF 분배금 과세 차이를 알려주세요',['C00001'])
        self.assertFalse(r['p0_go'])

    def test_selection_duplicates_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'V29_SELECTED_DUPLICATE_CLAIM'):
            audit_elided_pension_basis_v29(self.src,self.ex,self.q,['C00001','C00001'])

    def test_original_quote_forgery_rejected_before_context(self):
        bad=copy.deepcopy(self.ex)
        bad['atoms'][0]['source_refs'][0]['quote']='FORGED NOT IN ORIGINAL'
        with self.assertRaisesRegex(InvalidInput,'QUOTE_NOT_IN_ORIGINAL'):
            audit_elided_pension_basis_v29(self.src,bad,self.q,['C00001','C00002'])

    def test_code_blobs_verified_using_real_git_blob_algorithm(self):
        r=attest_v29_code_blobs(self.root,{'ire/v5/synthetic.py':self.gitsha})
        self.assertEqual(r['verified_git_blob_count'],1)
        self.assertFalse(r['entire_repo_or_dependencies_independently_attested'])

    def test_code_bytes_tamper_rejected(self):
        self.file.write_text('print("altered")\n',encoding='utf-8')
        with self.assertRaisesRegex(InvalidInput,'V29_CODE_BLOB_SHA_MISMATCH'):
            attest_v29_code_blobs(self.root,{'ire/v5/synthetic.py':self.gitsha})

    def test_missing_source_file_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'V29_CODE_PINNED_FILE_MISSING'):
            attest_v29_code_blobs(self.root,{'ire/v6/not_present.py':self.gitsha})

    def test_invalid_git_blob_digest_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'V29_CODE_PIN_FORMAT_INVALID'):
            attest_v29_code_blobs(self.root,{'ire/v5/synthetic.py':'bad'})

    def test_empty_code_pin_map_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'V29_CODE_PIN_MAP_REQUIRED'):
            attest_v29_code_blobs(self.root,{})

    def test_code_path_traversal_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'V29_CODE_PIN_FORMAT_INVALID'):
            attest_v29_code_blobs(self.root,{'ire/v5/../synthetic.py':self.gitsha})

    def test_disallowed_extension_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'V29_CODE_PIN_FORMAT_INVALID'):
            attest_v29_code_blobs(self.root,{'ire/v5/original.srt':self.gitsha})

    def test_runtime_pin_does_not_certify_independent_review(self):
        r=attest_v29_code_blobs(self.root,{'ire/v5/synthetic.py':self.gitsha})
        self.assertIs(r['entire_repo_or_dependencies_independently_attested'],False)


if __name__=='__main__':
    unittest.main()
