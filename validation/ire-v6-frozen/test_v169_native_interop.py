"""Synthetic V169 journal -> V168 -> actual frozen V123 / E4 HOLD.

No actual ChatGPT model API, real issuer provenance, or owner publication.
"""
import tempfile
import unittest
from pathlib import Path
from test_v168_chat_native_replay import (V168NativeBridgeTests, proposal_reviewer)
from v168_chat_native_replay import compile_and_replay_native
from v169_chat_research_journal import ChatReviewJournal
from v166_e4_primary_approval_gate import assess_e4_primary_authority_gate


class V169NativeInteropTests(unittest.TestCase):
    def setUp(self):
        fx=V168NativeBridgeTests("test_01_no_changes_replayed_real_native_v123_hold")
        fx.setUp()
        self.addCleanup(fx.doCleanups)
        self.fx=fx
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.journal=ChatReviewJournal(Path(self.tmp.name)/"owner-private.sqlite",
                                       fx.docket)

    def test_01_durable_proposals_no_native_accept_without_review(self):
        self.journal.run_round(evidence_retriever=lambda _:[],
            chat_reviewer=lambda q:proposal_reviewer(q,'KEEP_OPEN'),limit=1)
        j=ChatReviewJournal(self.journal.path,self.fx.docket)
        proposal=j.export_unreleased_proposals()
        result=compile_and_replay_native(self.fx.docket,proposal,
            cases_by_segment={'B0001':self.fx.case})
        self.assertEqual(result['receipt']['native_results'][0]['native_status'],
                         'CHAT_FINAL_HOLD_OPEN')
        self.assertEqual(result['receipt']['native_rows_changed'],0)
        self.assertFalse(result['receipt']['e4_approved'])
        self.assertFalse(result['receipt']['e5_authorized'])

    def test_02_candidate_secondary_native_pass_but_e4_hold(self):
        self.journal.run_round(evidence_retriever=self.fx.evidence,
            chat_reviewer=lambda q:proposal_reviewer(q,
                    'CANDIDATE_NEEDS_NATIVE_REVIEW'),limit=1)
        p=self.journal.export_unreleased_proposals()
        secondary={self.fx.claim:self.fx.secondary(p)}
        r=compile_and_replay_native(self.fx.docket,p,
            cases_by_segment={'B0001':self.fx.case},secondary_chat_reviews=secondary)
        self.assertEqual(r['receipt']['native_results'][0]['native_status'],
                         'CHAT_FINAL_PASS_RESEARCH_CANDIDATES_ONLY')
        self.assertFalse(r['receipt']['knowledge_publication_authorized'])
        case={**self.fx.case,'chat_review':r['native_private_drafts']['B0001']['review']}
        e4=assess_e4_primary_authority_gate(case,None,now_as_of='2026-11-18')
        self.assertEqual(e4['status'],'E4_HOLD_INELIGIBLE_APPROVAL')
        self.assertEqual(e4['reason_code'],'PRIMARY_PROVENANCE_MISSING')

if __name__=='__main__':unittest.main()