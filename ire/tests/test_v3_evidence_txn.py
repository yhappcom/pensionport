"""WAL power-interruption boundary simulations; synthetic inputs only."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ire.v3_evidence import apply_v3_scope_evidence, save_scope_evidence_pair
from ire.v3_evidence_txn import recover_scope_evidence_pairs, PREFIX
import test_v3_evidence as test_fixture


class CrashRecoveryTests(unittest.TestCase):
    def setUp(self):
        fixture = test_fixture.V3ScopedEvidenceTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        self.updated, self.receipt = apply_v3_scope_evidence(
            fixture.ledger, fixture.knowledge, fixture.document,
            fixture.review())
        self.folder = fixture.root / 'transactional_evidence'

    def save(self):
        return save_scope_evidence_pair(self.updated, self.fixture.knowledge,
                                        self.receipt, str(self.folder))

    def test_receipt_first_process_interrupt_recovers_by_rollback(self):
        with patch('ire.v3_evidence.save_private_evidence',
                   side_effect=KeyboardInterrupt('simulated abrupt exit')):
            with self.assertRaises(KeyboardInterrupt):
                self.save()
        self.assertEqual(len(list(self.folder.glob(PREFIX + '*.pending'))), 1)
        self.assertEqual(len(list(self.folder.glob('*.json'))), 1)
        result = recover_scope_evidence_pairs(str(self.folder))
        self.assertEqual(result['rolled_back_incomplete'], 1)
        self.assertEqual(result['pending_remaining'], 0)
        self.assertEqual(list(self.folder.glob('*.json')), [])
        self.assertEqual(len(list(self.folder.glob('*.done'))), 0)
        self.save()
        self.assertEqual(recover_scope_evidence_pairs(str(self.folder))[
            'verified_committed_transactions'], 1)

    def test_both_written_before_commit_interrupt_recovers_by_commit(self):
        with patch('ire.v3_evidence_txn._promote',
                   side_effect=SystemExit(20)):
            with self.assertRaises(SystemExit):
                self.save()
        self.assertEqual(len(list(self.folder.glob(PREFIX + '*.pending'))), 1)
        self.assertEqual(len(list(self.folder.glob('*.json'))), 2)
        result = recover_scope_evidence_pairs(str(self.folder))
        self.assertEqual(result['committed_after_interruption'], 1)
        self.assertEqual(result['verified_committed_transactions'], 1)
        self.assertEqual(len(list(self.folder.glob('*.json'))), 2)
        self.assertEqual(len(list(self.folder.glob('*.done'))), 1)

    def test_crash_before_first_write_recovers_empty(self):
        with patch('ire.v3_evidence.save_v3_scope_receipt',
                   side_effect=SystemExit(21)):
            with self.assertRaises(SystemExit):
                self.save()
        result=recover_scope_evidence_pairs(str(self.folder))
        self.assertEqual(result['rolled_back_incomplete'], 1)
        self.assertEqual(list(self.folder.glob('*.json')), [])

    def test_corrupted_receipt_blocks_recovery_and_preserves_forensics(self):
        with patch('ire.v3_evidence.save_private_evidence',
                   side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):self.save()
        receipt=next(self.folder.glob('*.json'))
        receipt.write_bytes(receipt.read_bytes() + b'corruption')
        with self.assertRaisesRegex(ValueError, 'V3_SCOPE_WAL_PAYLOAD_TAMPERED'):
            recover_scope_evidence_pairs(str(self.folder))
        self.assertTrue(receipt.exists())
        self.assertEqual(len(list(self.folder.glob(PREFIX+'*.pending'))), 1)

    def test_tampered_journal_blocks_recovery(self):
        with patch('ire.v3_evidence.save_private_evidence',
                   side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):self.save()
        journal=next(self.folder.glob(PREFIX+'*.pending'))
        doc=json.loads(journal.read_text(encoding='utf-8'))
        doc['ledger_id']='0'*64
        journal.write_text(json.dumps(doc),encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'V3_SCOPE_WAL_TAMPER_OR_INVALID'):
            recover_scope_evidence_pairs(str(self.folder))

    def test_broken_committed_file_blocks_future_use(self):
        ledger, receipt=self.save()
        Path(ledger).unlink()
        with self.assertRaisesRegex(ValueError, 'V3_SCOPE_WAL_COMMITTED_PAIR_BROKEN'):
            recover_scope_evidence_pairs(str(self.folder))
        self.assertTrue(Path(receipt).exists())

    def test_committed_receipt_cannot_be_replaced_with_altered_bytes(self):
        _, receipt=self.save()
        p=Path(receipt)
        p.write_bytes(p.read_bytes()+b'!')
        with self.assertRaisesRegex(ValueError, 'V3_SCOPE_WAL_PAYLOAD_TAMPERED'):
            recover_scope_evidence_pairs(str(self.folder))

    def _real_process_crash(self, phase, expected):
        """Abrupt os._exit bypasses exception handlers and finally blocks."""
        payload=self.fixture.root/'synthetic_payload.json'
        payload.write_text(json.dumps({
            "knowledge":self.fixture.knowledge,
            "ledger":self.updated,
            "receipt":self.receipt,
            "dir":str(self.folder),
        }),encoding='utf-8')
        child=r"""
import json,os,sys
from ire import v3_evidence as e
from ire import v3_evidence_txn as txn
record=json.load(open(sys.argv[1],encoding='utf-8'))
if sys.argv[2]=='receipt':
    e.save_private_evidence=lambda *a,**k:os._exit(37)
else:
    txn._promote=lambda *a,**k:os._exit(38)
e.save_scope_evidence_pair(record['ledger'],record['knowledge'],
                           record['receipt'],record['dir'])
"""
        child_result=subprocess.run([sys.executable,'-c',child,
                                     str(payload),phase],check=False,
                                    capture_output=True,text=True)
        self.assertEqual(child_result.returncode,expected)
        self.assertEqual(len(list(self.folder.glob(PREFIX+'*.pending'))),1)

    def test_real_os_exit_after_receipt_recovery_rolls_back(self):
        self._real_process_crash('receipt',37)
        summary=recover_scope_evidence_pairs(str(self.folder))
        self.assertEqual(summary['rolled_back_incomplete'],1)
        self.assertEqual(list(self.folder.glob('*.json')),[])

    def test_real_os_exit_after_both_recovery_commits(self):
        self._real_process_crash('both',38)
        summary=recover_scope_evidence_pairs(str(self.folder))
        self.assertEqual(summary['committed_after_interruption'],1)
        self.assertEqual(summary['verified_committed_transactions'],1)
        self.assertEqual(len(list(self.folder.glob('*.json'))),2)

    def test_committed_journal_is_private_and_no_raw_data_inside(self):
        self.save()
        journal=next(self.folder.glob('*.done'))
        self.assertEqual(journal.stat().st_mode & 0o077, 0)
        raw=journal.read_text()
        self.assertNotIn('가상의 상품',raw)
        self.assertNotIn('source_quote',raw)
        self.assertEqual(recover_scope_evidence_pairs(str(self.folder))[
            'financial_facts_approved'], 0)


if __name__=='__main__':unittest.main()