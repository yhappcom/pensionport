"""V40 synthetic atomic checkpoint regressions; no owner private transcript."""
import copy
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from ire.v6.errors import (ConcurrentHeadChanged, IdempotencyConflict,
                           InvalidInput, LedgerCorrupted)
from ire.v6.semantic_checkpoint_v40 import PrivateSemanticCheckpointV40, ZERO_SHA
from ire.v6.tests import test_host_semantic_custody_v39 as v39_fixture_module


class SemanticCheckpointV40Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / 'owner_private_semantic_checkpoint.sqlite'
        self.store = PrivateSemanticCheckpointV40(self.db)
        fx = v39_fixture_module.SourceBoundSemanticReviewV39Tests(
            'test_all_source_bound_candidates_and_notes_replayed')
        fx.setUp()
        self.fx = fx
        self.original = copy.deepcopy(fx.raws)
        self.sources = copy.deepcopy(fx.sources)
        self.windows = copy.deepcopy(fx.windows)
        self.rows = copy.deepcopy(fx.rows)
        self.vid = fx.vid
        self.sha = fx.sources[0]['original_srt_sha256']

    def submit(self, **changes):
        data = dict(run_id='turn_00001',expected_head=ZERO_SHA,
                    original_srt_bytes=self.original,
                    source_pins=self.sources,window_pins=self.windows,
                    host_rows=self.rows)
        data.update(changes)
        return self.store.submit(**data)

    def test_one_turn_v39_preflight_to_durable_sqlite_chain(self):
        row=self.submit()
        self.assertTrue(row['atomic_checkpoint_committed'])
        self.assertEqual(row['reviewed_candidates'],len(self.rows))
        self.assertEqual(row['chat_review_notes'],len(self.rows))
        self.assertFalse(row['p0_go'])
        self.assertFalse(row['financial_truth_independently_verified'])
        snap=self.store.verify_chain(self.vid,self.sha)
        self.assertEqual(snap['head_sha256'],row['event_sha256'])
        self.assertEqual(snap['checkpoint_count'],1)
        self.assertEqual(snap['reviewed_window_count'],1)

    def test_repeat_run_is_idempotent(self):
        one=self.submit()
        two=self.submit()
        self.assertTrue(two['idempotent_replay'])
        self.assertEqual(one['event_sha256'],two['event_sha256'])
        self.assertEqual(self.store.snapshot(self.vid,self.sha)['checkpoint_count'],1)

    def test_changed_semantic_note_same_run_rejected(self):
        self.submit()
        notes=copy.deepcopy(self.rows)
        notes[0]['semantic_notes'][0]['meaning']='변경된 의미 검토 설명입니다.'
        with self.assertRaisesRegex(IdempotencyConflict,'REUSED_RUN_ID'):
            self.submit(host_rows=notes)

    def test_other_run_with_stale_head_rejected(self):
        self.submit()
        with self.assertRaisesRegex(ConcurrentHeadChanged,'EXPECTED_HEAD_STALE'):
            self.submit(run_id='turn_00002')

    def test_same_source_window_cannot_double_count(self):
        saved=self.submit()
        with self.assertRaisesRegex(IdempotencyConflict,'WINDOW_ALREADY_CHECKPOINTED'):
            self.submit(run_id='turn_00002',expected_head=saved['event_sha256'])
        self.assertEqual(self.store.snapshot(self.vid,self.sha)['reviewed_window_count'],1)

    def test_missing_source_candidate_blocks_all_writes(self):
        with self.assertRaisesRegex(InvalidInput,'MISSING_CANDIDATE'):
            self.submit(host_rows=self.rows[:-1])
        self.assertEqual(self.store.snapshot(self.vid,self.sha)['checkpoint_count'],0)

    def test_duplicate_source_candidate_blocks_all_writes(self):
        with self.assertRaisesRegex(InvalidInput,'DUPLICATE_CANDIDATE'):
            self.submit(host_rows=self.rows+[copy.deepcopy(self.rows[0])])
        self.assertEqual(self.store.snapshot(self.vid,self.sha)['checkpoint_count'],0)

    def test_forged_original_srt_blocks_all_writes(self):
        with self.assertRaisesRegex(InvalidInput,'ORIGINAL_SRT_SHA_DRIFT'):
            self.submit(original_srt_bytes={self.vid:self.original[self.vid]+b' '})
        self.assertEqual(self.store.snapshot(self.vid,self.sha)['checkpoint_count'],0)

    def test_v37_source_window_pin_drift_blocks_all_writes(self):
        changed=copy.deepcopy(self.windows)
        changed[0]['original_window_text_sha256']='a'*64
        with self.assertRaisesRegex(InvalidInput,'DIGEST_DRIFT'):
            self.submit(window_pins=changed)
        self.assertEqual(self.store.snapshot(self.vid,self.sha)['checkpoint_count'],0)

    def test_false_independent_finance_approval_blocks_write(self):
        changed=copy.deepcopy(self.rows)
        changed[0]['finance_fact_certified']=True
        with self.assertRaisesRegex(InvalidInput,'UNSUPPORTED_FACT_AUDIO_GOLD'):
            self.submit(host_rows=changed)
        self.assertEqual(self.store.snapshot(self.vid,self.sha)['checkpoint_count'],0)

    def test_mid_transaction_failure_rolls_back_checkpoint_and_ownership(self):
        def fail(stage):
            if stage=='AFTER_CHECKPOINT_INSERT':
                raise RuntimeError('FAULT_INJECTED')
        self.store._before_commit=fail
        with self.assertRaisesRegex(RuntimeError,'FAULT_INJECTED'):
            self.submit()
        self.store._before_commit=lambda stage: None
        self.assertEqual(self.store.snapshot(self.vid,self.sha)['checkpoint_count'],0)
        with sqlite3.connect(self.db) as con:
            self.assertEqual(con.execute(
                'SELECT COUNT(*) FROM v40_window_ownership').fetchone()[0],0)
        self.assertTrue(self.submit()['atomic_checkpoint_committed'])

    def test_sqlite_checkpoint_hash_tamper_detected(self):
        self.submit()
        with sqlite3.connect(self.db) as con:
            con.execute('UPDATE v40_checkpoints SET reviewed_candidates=reviewed_candidates+1')
        with self.assertRaisesRegex(LedgerCorrupted,'CHAIN_TAMPERED'):
            self.store.verify_chain(self.vid,self.sha)

    def test_sqlite_window_ownership_tamper_detected(self):
        self.submit()
        with sqlite3.connect(self.db) as con:
            con.execute("UPDATE v40_window_ownership SET window_id='W00002'")
        with self.assertRaisesRegex(LedgerCorrupted,'OWNERSHIP_CENSUS_DRIFT'):
            self.store.verify_chain(self.vid,self.sha)

    def test_single_video_and_bounded_window_scope_required(self):
        with self.assertRaisesRegex(InvalidInput,'EXACT_ONE_VIDEO'):
            self.submit(source_pins=self.sources+self.sources)
        with self.assertRaisesRegex(InvalidInput,'BOUNDED_WINDOWS'):
            self.submit(window_pins=self.windows*5)
        self.assertEqual(self.store.snapshot(self.vid,self.sha)['checkpoint_count'],0)

    def test_public_receipt_and_private_db_contain_no_speech_text(self):
        result=self.submit()
        public=json.dumps(result,ensure_ascii=False)
        sqlite_bytes=self.db.read_bytes()
        for source in (x['source_excerpt'] for x in self.rows):
            self.assertNotIn(source,public)
            self.assertNotIn(source.encode('utf8'),sqlite_bytes)
        self.assertNotIn('semantic_notes',public)
        self.assertEqual(result['semantic_custody_sha256'],
                         self.fx.audit()['receipt_sha256'])

    def test_empty_chain_cannot_claim_research_complete(self):
        result=self.store.verify_chain(self.vid,self.sha)
        self.assertEqual(result['checkpoint_count'],0)
        self.assertEqual(result['head_sha256'],ZERO_SHA)
        self.assertFalse(result['research_complete'])


if __name__=='__main__':
    unittest.main()
