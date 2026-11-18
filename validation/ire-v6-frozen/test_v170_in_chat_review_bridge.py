"""V170 challenge -> actual in-chat response IO contract; synthetic callbacks only.

The tests *do not* invoke an LLM. Assertions prove no response substitution,
no SQLite advance after errors and no false V123/E4 issuance.
"""
from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from test_v167_chat_research_loop import fixture, evidence, reviewer
from v166_e4_full_video_readiness import h
from v167_chat_research_loop import prepare_open_docket
from v169_chat_research_journal import ChatReviewJournal
from v170_in_chat_review_bridge import prepare_chat_turn, commit_chat_turn


class V170RealChatBoundaryProtocolTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        raw,cues,segments=fixture()
        self.docket=prepare_open_docket(raw,cues,segments,
                            expected_source_sha256=h(raw),as_of='2026-11-19')
        self.db=Path(self.tmp.name)/'private.sqlite'
        self.journal=ChatReviewJournal(self.db,self.docket)
        self.bundle=prepare_chat_turn(self.journal,evidence_retriever=evidence,limit=2)
        self.replies=[reviewer(q,'KEEP_OPEN') for q in self.bundle.challenge['requests']]

    def test_01_current_chat_two_step_commit_and_private_bytes_not_shared(self):
        self.assertEqual(len(self.bundle.challenge['requests']),2)
        self.assertFalse(self.bundle.challenge['python_called_any_model'])
        self.assertFalse(self.bundle.challenge['chat_model_identity_cryptographically_attested'])
        self.assertTrue(self.bundle.raw_evidence)
        for q in self.bundle.challenge['requests']:
            self.assertNotIn('body',q['evidence'][0])
        result=commit_chat_turn(self.journal,self.bundle,self.replies)
        self.assertEqual(result['reviewed_request_count'],2)
        self.assertEqual(result['still_open_in_this_batch'],2)
        self.assertEqual(result['never_reviewed_count'],0)
        self.assertFalse(result['e5_authorized'])
        self.assertFalse(result['native_v123_final_approval'])
        self.assertFalse(self.journal.export_unreleased_proposals()['knowledge_publication_authorized'])

    def test_02_second_call_stale_receipt_rejected(self):
        commit_chat_turn(self.journal,self.bundle,self.replies)
        old=self.journal.status()['journal_head_sha256']
        with self.assertRaisesRegex(ValueError,'STALE_OR_WRONG_OWNER_REVISION'):
            commit_chat_turn(self.journal,self.bundle,self.replies)
        self.assertEqual(self.journal.status()['journal_head_sha256'],old)

    def test_03_swapped_responses_rejected_without_writes(self):
        with self.assertRaisesRegex(ValueError,'RESPONSE_ORDER_OR_SOURCE_PIN'):
            commit_chat_turn(self.journal,self.bundle,list(reversed(self.replies)))
        self.assertEqual(self.journal.status()['processed_count'],0)

    def test_04_missing_chat_response_is_not_synthesized(self):
        with self.assertRaisesRegex(ValueError,'COMPLETE_CHAT_BATCH_REQUIRED'):
            commit_chat_turn(self.journal,self.bundle,self.replies[:1])
        self.assertEqual(self.journal.status()['processed_count'],0)

    def test_05_modified_evidence_bytes_rejected_even_with_matching_public_request(self):
        self.bundle.raw_evidence[self.replies[0]['claim_id']][0]['body']=b'forged publisher fake bytes'*4
        with self.assertRaisesRegex(ValueError,'EVIDENCE_'):
            commit_chat_turn(self.journal,self.bundle,self.replies)
        self.assertEqual(self.journal.status()['processed_count'],0)

    def test_06_fake_model_identity_flag_and_source_hash_rejected(self):
        answers=copy.deepcopy(self.replies)
        answers[0]['chat_reviewer_identity_attested']=True
        with self.assertRaisesRegex(ValueError,'CHAT_SEMANTIC_OR_AUTHORITY_NOT_SAFE'):
            commit_chat_turn(self.journal,self.bundle,answers)
        self.assertEqual(self.journal.status()['processed_count'],0)

    def test_07_stale_prepared_batch_on_concurrent_journal_advance(self):
        self.journal.run_round(evidence_retriever=lambda _:[],
            chat_reviewer=lambda q:reviewer(q,'KEEP_OPEN'),limit=1)
        with self.assertRaisesRegex(ValueError,'STALE_OR_WRONG_OWNER_REVISION'):
            commit_chat_turn(self.journal,self.bundle,self.replies)
        self.assertEqual(self.journal.status()['processed_count'],1)

    def test_08_candidate_is_only_unreleased_proposal(self):
        reply=[reviewer(q,'CANDIDATE_NEEDS_NATIVE_REVIEW')
               for q in self.bundle.challenge['requests']]
        out=commit_chat_turn(self.journal,self.bundle,reply)
        self.assertEqual(out['candidates_needing_native_and_e4'],2)
        self.assertFalse(out['official_e4_approval'])
        self.assertFalse(out['knowledge_published'])
        self.assertEqual(self.journal.export_unreleased_proposals()['candidate_proposals'],2)

    def test_09_new_host_challenge_rejected_after_review_state_mutation(self):
        forged=copy.deepcopy(self.bundle)
        forged.challenge['requests'][0]['task']['source_context'][0]['text']='forgery'
        with self.assertRaisesRegex(ValueError,'CHALLENGE_TAMPERED'):
            commit_chat_turn(self.journal,forged,self.replies)
        self.assertEqual(self.journal.status()['processed_count'],0)

    def test_10_current_chat_responds_to_each_relevant_original_quote(self):
        for request in self.bundle.challenge['requests']:
            self.assertEqual(request['task']['prior_verdict'],'OPEN')
            self.assertTrue(request['task']['source_refs'])
            self.assertTrue(request['task']['source_context'])
            self.assertTrue(request['task']['candidate_is_not_approved_knowledge'])


if __name__=='__main__': unittest.main()