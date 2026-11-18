"""Only synthetic provenance. Revisit does not equate source retrieval with truth."""
import copy
import sqlite3
import tempfile
import unittest
from pathlib import Path

from test_v167_chat_research_loop import fixture, evidence, reviewer
from v166_e4_full_video_readiness import h
from v167_chat_research_loop import prepare_open_docket
from v169_chat_research_journal import ChatReviewJournal
from v170_evidence_revisit import EvidenceRevisitJournal


class V170NewEvidenceRevisitTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        raw,cues,segments=fixture()
        self.docket=prepare_open_docket(raw,cues,segments,
                 expected_source_sha256=h(raw),as_of='2026-11-19')
        self.db=Path(self.tmp.name)/'private.sqlite'
        self.journal=ChatReviewJournal(self.db,self.docket)
        self.journal.run_round(evidence_retriever=lambda _:[],
                   chat_reviewer=lambda req:reviewer(req,'KEEP_OPEN'),limit=2)
        self.revisits=EvidenceRevisitJournal(self.journal)
        self.cid=self.docket['items'][0]['claim_id']

    def review(self,decision='KEEP_OPEN',source=evidence):
        return self.revisits.run_revisit(self.cid,evidence_retriever=source,
                   chat_reviewer=lambda req:reviewer(req,decision))

    def test_01_initial_cursor_finished_does_not_mean_resolved(self):
        s=self.revisits.status()
        self.assertEqual(s['never_researched_count'],0)
        self.assertEqual(s['latest_still_open_count'],2)
        self.assertFalse(s['e4_approved'])
        self.assertFalse(s['e5_authorized'])

    def test_02_real_new_evidence_reopens_old_keep_open_without_native_approval(self):
        s=self.review('CANDIDATE_NEEDS_NATIVE_REVIEW')
        self.assertEqual(s['revisit_events'],1)
        self.assertEqual(s['latest_still_open_count'],1)
        self.assertEqual(s['candidate_not_native_approved'],1)
        merged=self.revisits.export_effective_unreleased_proposals()
        self.assertEqual(merged['candidate_proposals'],1)
        self.assertEqual(merged['proposals_created'],2)
        self.assertFalse(merged['knowledge_publication_authorized'])
        self.assertEqual(self.journal.export_unreleased_proposals()['candidate_proposals'],0)

    def test_03_same_source_body_cannot_be_replayed_as_progress(self):
        self.review('KEEP_OPEN')
        with self.assertRaisesRegex(ValueError,'EVIDENCE_NOT_NEW'):
            self.review('CANDIDATE_NEEDS_NATIVE_REVIEW')
        self.assertEqual(self.revisits.status()['revisit_events'],1)

    def test_04_missing_new_evidence_is_not_a_review(self):
        with self.assertRaisesRegex(ValueError,'EVIDENCE_NOT_NEW'):
            self.review(source=lambda _:[])
        self.assertEqual(self.revisits.status()['revisit_events'],0)

    def test_05_stale_claim_not_in_original_processed_log(self):
        with self.assertRaisesRegex(ValueError,'ONLY_PREVIOUSLY_RESEARCHED_OPEN'):
            self.revisits.run_revisit('C99999',evidence_retriever=evidence,
                            chat_reviewer=reviewer)

    def test_06_candidate_cannot_be_reopened_as_keep_open_without_native_replay(self):
        self.review('CANDIDATE_NEEDS_NATIVE_REVIEW')
        with self.assertRaisesRegex(ValueError,'NOT_STILL_OPEN'):
            self.review('KEEP_OPEN')

    def test_07_db_chain_reopen_verifies_mutations(self):
        self.review('KEEP_OPEN')
        with sqlite3.connect(self.db) as con:
            con.execute('UPDATE revisit_receipts SET head=? WHERE seq=1',('0'*64,))
        with self.assertRaisesRegex(ValueError,'REVISIT_CHAIN_HASH_DRIFT'):
            EvidenceRevisitJournal(ChatReviewJournal(self.db,self.docket))

    def test_08_injected_failure_rolls_back_revisit(self):
        def boom(_): raise RuntimeError('disk fault')
        with self.assertRaisesRegex(RuntimeError,'disk fault'):
            self.revisits.run_revisit(self.cid,evidence_retriever=evidence,
                  chat_reviewer=lambda q:reviewer(q,'KEEP_OPEN'),
                  _failure_injector=boom)
        self.assertEqual(self.revisits.status()['revisit_events'],0)

    def test_09_chat_review_callback_failure_has_zero_writes(self):
        def boom(_): raise RuntimeError('chat unavailable')
        with self.assertRaisesRegex(RuntimeError,'chat unavailable'):
            self.revisits.run_revisit(self.cid,evidence_retriever=evidence,
                   chat_reviewer=boom)
        self.assertEqual(self.revisits.status()['revisit_events'],0)

    def test_10_revisit_carries_original_atom_and_note_hash(self):
        self.review('KEEP_OPEN')
        row=self.revisits.export_effective_unreleased_proposals()['proposals'][0]
        original=self.journal.export_unreleased_proposals()['proposals'][0]
        self.assertEqual(row['atom_sha256'],original['atom_sha256'])
        self.assertEqual(row['prior_review_sha256'],original['prior_review_sha256'])
        self.assertNotEqual(row['chat_decision_sha256'],original['chat_decision_sha256'])


if __name__=='__main__':unittest.main()