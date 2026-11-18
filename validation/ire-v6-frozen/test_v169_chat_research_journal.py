"""V169 transport durability tests. Semantic reviewer/evidence callbacks are synthetic."""
from __future__ import annotations
import copy
import os
import sqlite3
import stat
import tempfile
import unittest
from pathlib import Path

from test_v167_chat_research_loop import fixture, evidence, reviewer
from v166_e4_full_video_readiness import h
from v167_chat_research_loop import prepare_open_docket, execute_chat_review_round
from v169_chat_research_journal import ChatReviewJournal

class V169PrivateJournalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        raw,cues,segments=fixture()
        self.docket=prepare_open_docket(raw,cues,segments,
                         expected_source_sha256=h(raw),as_of='2026-11-18')
        self.path=Path(self.tmp.name)/'private.sqlite'
        self.j=ChatReviewJournal(self.path,self.docket)

    def re_open(self):
        return ChatReviewJournal(self.path,self.docket)

    def keep(self, task=None):
        return lambda q:reviewer(q,'KEEP_OPEN')

    def test_01_restrictive_file_mode_and_zero_progress(self):
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode),0o600)
        r=self.j.status()
        self.assertEqual((r['processed_count'],r['remaining_count']),(0,2))
        self.assertFalse(r['e5_authorized'])
        self.assertFalse(r['model_origin_cryptographically_authenticated'])

    def test_02_one_then_restart_and_resume(self):
        r=self.j.run_round(evidence_retriever=lambda _:[],chat_reviewer=self.keep(),limit=1)
        self.assertEqual((r['processed_count'],r['remaining_count']),(1,1))
        second=self.re_open()
        self.assertEqual([x['claim_id'] for x in second.next_tasks()],['C00003'])
        done=second.run_round(evidence_retriever=lambda _:[],chat_reviewer=self.keep(),limit=1)
        self.assertEqual((done['processed_count'],done['remaining_count']),(2,0))
        p=second.export_unreleased_proposals()
        self.assertEqual((p['original_open_count'],p['proposals_created'],p['unprocessed_open_count']),(2,2,0))
        self.assertFalse(p['knowledge_publication_authorized'])

    def test_03_batch_crash_rolls_back_entire_batch(self):
        def fail(seq):
            if seq==2: raise RuntimeError('injected crash')
        with self.assertRaisesRegex(RuntimeError,'injected crash'):
            self.j.run_round(evidence_retriever=lambda _:[],chat_reviewer=self.keep(),
                             limit=2,_failure_injector=fail)
        self.assertEqual(self.re_open().status()['processed_count'],0)
        self.j.run_round(evidence_retriever=lambda _:[],chat_reviewer=self.keep(),limit=2)
        self.assertEqual(self.j.status()['processed_count'],2)

    def test_04_no_reprocessing_after_completion(self):
        self.j.run_round(evidence_retriever=lambda _:[],chat_reviewer=self.keep())
        head=self.j.status()['journal_head_sha256']
        def no(_): raise AssertionError('must not rereview')
        self.j.run_round(evidence_retriever=no,chat_reviewer=no)
        self.assertEqual(self.j.status()['journal_head_sha256'],head)

    def test_05_changed_docket_cannot_resume(self):
        doc=copy.deepcopy(self.docket)
        doc['items'][0]['source_context'][0]['text']='different'
        from v166_e4_full_video_readiness import digest
        doc['docket_sha256']=digest({k:v for k,v in doc.items() if k!='docket_sha256'})
        with self.assertRaisesRegex(ValueError,'FROZEN_SOURCE_OR_DOCKET_VERSION_CHANGED'):
            ChatReviewJournal(self.path,doc)

    def test_06_review_callback_failure_is_no_write(self):
        def boom(_): raise LookupError('model host unavailable')
        with self.assertRaises(LookupError):
            self.j.run_round(evidence_retriever=lambda _:[],chat_reviewer=boom)
        self.assertEqual(self.j.status()['processed_count'],0)

    def test_07_missing_callbacks_rejected_and_unchanged(self):
        with self.assertRaisesRegex(ValueError,'CHAT_HOST_CALLBACK_REQUIRED'):
            self.j.run_round(evidence_retriever=lambda _:[],chat_reviewer=None)
        self.assertEqual(self.j.status()['processed_count'],0)

    def test_08_reject_wrong_review_digest_at_source(self):
        with self.assertRaisesRegex(ValueError,'CHAT_DECISION_PIN_MISMATCH'):
            self.j.run_round(evidence_retriever=lambda _:[],
                chat_reviewer=lambda q:{**reviewer(q,'KEEP_OPEN'),'request_sha256':'1'*64})
        self.assertEqual(self.j.status()['processed_count'],0)

    def test_09_tamper_private_proposal_body_rejected(self):
        self.j.run_round(evidence_retriever=lambda _:[],chat_reviewer=self.keep(),limit=1)
        with sqlite3.connect(self.path) as con:
            con.execute("UPDATE receipts SET proposal_json='{}' WHERE seq=1")
        with self.assertRaisesRegex(ValueError,'PROPOSAL_DRIFT_OR_RELEASE_FORGED'):
            self.re_open()

    def test_10_tamper_private_chain_rejected(self):
        self.j.run_round(evidence_retriever=lambda _:[],chat_reviewer=self.keep(),limit=1)
        with sqlite3.connect(self.path) as con:
            con.execute("UPDATE receipts SET head=? WHERE seq=1",('9'*64,))
        with self.assertRaisesRegex(ValueError,'CHAIN_HASH_MISMATCH'):
            self.re_open()

    def test_11_insecure_world_readable_path_rejected(self):
        os.chmod(self.path,0o644)
        with self.assertRaisesRegex(ValueError,'UNSAFE_PRIVATE_DB_MODE'):
            self.re_open()

    def test_12_source_docket_mutation_does_not_change_journal(self):
        self.docket['items'][0]['source_context'][0]['text']='tamper caller'
        self.assertEqual(self.j.status()['processed_count'],0)
        with self.assertRaisesRegex(ValueError,'ROOT_DOCKET_TAMPERED'):
            ChatReviewJournal(Path(self.tmp.name)/'extra.sqlite',self.docket)

    def test_13_high_risk_first_even_after_restart(self):
        self.assertEqual([x['claim_id'] for x in self.j.next_tasks(2)],['C00001','C00003'])
        self.j.run_round(evidence_retriever=lambda _:[],chat_reviewer=self.keep(),limit=1)
        self.assertEqual(self.re_open().next_tasks(1)[0]['claim_id'],'C00003')

    def test_14_second_round_v167_receipt_stays_source_pinned(self):
        r=execute_chat_review_round(self.docket,evidence_retriever=lambda _:[],
             chat_reviewer=self.keep(),limit=1,start_after='C00001')
        self.assertEqual(r['proposals_created'],1)
        self.assertEqual(r['proposals'][0]['claim_id'],'C00003')
        self.assertEqual(r['docket_sha256'],self.docket['docket_sha256'])

    def test_15_unknown_start_after_rejected(self):
        with self.assertRaisesRegex(ValueError,'START_AFTER_NOT_IN_DOCKET'):
            execute_chat_review_round(self.docket,evidence_retriever=lambda _:[],
                                      chat_reviewer=self.keep(),start_after='C99999')

    def test_16_candidate_receipt_export_remains_not_approved(self):
        self.j.run_round(evidence_retriever=evidence,chat_reviewer=reviewer,limit=2)
        p=self.j.export_unreleased_proposals()
        self.assertEqual(p['candidate_proposals'],2)
        self.assertFalse(p['native_v123_status_changed'])
        self.assertFalse(p['e5_authorized'])
        self.assertTrue(all(not x['approved_by_e4'] for x in p['proposals']))

if __name__=='__main__':unittest.main()