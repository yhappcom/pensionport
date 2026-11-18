"""V170 two tool calls -> V169 private journal -> V168 frozen V123 -> E4 HOLD.

Every reviewer response in this CI module is synthetic. Real ChatGPT has to
write the semantic decision during the chat turn, not through these mocks.
"""
import tempfile
import unittest
from pathlib import Path

from test_v168_chat_native_replay import V168NativeBridgeTests, proposal_reviewer
from v168_chat_native_replay import compile_and_replay_native
from v169_chat_research_journal import ChatReviewJournal
from v170_in_chat_review_bridge import prepare_chat_turn, commit_chat_turn
from v170_evidence_revisit import EvidenceRevisitJournal
from v166_e4_primary_approval_gate import assess_e4_primary_authority_gate


class V170ChatTwoToolNativeFlowTests(unittest.TestCase):
    def setUp(self):
        fx=V168NativeBridgeTests("test_01_no_changes_replayed_real_native_v123_hold")
        fx.setUp()
        self.addCleanup(fx.doCleanups)
        self.fx=fx
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.journal=ChatReviewJournal(Path(self.tmp.name)/"owner-private.sqlite",fx.docket)

    def _chat_round(self, decision, evidence):
        prepared=prepare_chat_turn(self.journal,evidence_retriever=evidence,limit=1)
        replies=[proposal_reviewer(q,decision) for q in prepared.challenge['requests']]
        return commit_chat_turn(self.journal,prepared,replies)

    def test_01_real_frozen_v123_remains_hold_for_chat_keep_open(self):
        receipt=self._chat_round('KEEP_OPEN',lambda _:[])
        self.assertEqual(receipt['still_open_in_this_batch'],1)
        props=self.journal.export_unreleased_proposals()
        out=compile_and_replay_native(self.fx.docket,props,
                                       cases_by_segment={'B0001':self.fx.case})
        self.assertEqual(out['receipt']['native_results'][0]['native_status'],
                         'CHAT_FINAL_HOLD_OPEN')
        self.assertFalse(out['receipt']['knowledge_publication_authorized'])

    def test_02_chat_candidate_secondary_native_pass_but_e4_fails(self):
        receipt=self._chat_round('CANDIDATE_NEEDS_NATIVE_REVIEW',self.fx.evidence)
        self.assertEqual(receipt['candidates_needing_native_and_e4'],1)
        props=self.journal.export_unreleased_proposals()
        sec={self.fx.claim:self.fx.secondary(props)}
        out=compile_and_replay_native(self.fx.docket,props,
            cases_by_segment={'B0001':self.fx.case},secondary_chat_reviews=sec)
        self.assertEqual(out['receipt']['native_results'][0]['native_status'],
                         'CHAT_FINAL_PASS_RESEARCH_CANDIDATES_ONLY')
        self.assertFalse(out['receipt']['knowledge_publication_authorized'])
        case={**self.fx.case,
              'chat_review':out['native_private_drafts']['B0001']['review']}
        e4=assess_e4_primary_authority_gate(case,None,now_as_of='2026-11-19')
        self.assertEqual(e4['status'],'E4_HOLD_INELIGIBLE_APPROVAL')
        self.assertEqual(e4['reason_code'],'PRIMARY_PROVENANCE_MISSING')

    def test_03_reopen_old_keep_open_produces_new_candidate_but_e4_hold(self):
        self._chat_round('KEEP_OPEN',lambda _:[])
        revisits=EvidenceRevisitJournal(self.journal)
        status=revisits.run_revisit(self.fx.claim,
            evidence_retriever=self.fx.evidence,
            chat_reviewer=lambda q:proposal_reviewer(q,'CANDIDATE_NEEDS_NATIVE_REVIEW'))
        self.assertEqual(status['candidate_not_native_approved'],1)
        props=revisits.export_effective_unreleased_proposals()
        sec={self.fx.claim:self.fx.secondary(props)}
        out=compile_and_replay_native(self.fx.docket,props,
            cases_by_segment={'B0001':self.fx.case},secondary_chat_reviews=sec)
        self.assertEqual(out['receipt']['native_results'][0]['native_status'],
                         'CHAT_FINAL_PASS_RESEARCH_CANDIDATES_ONLY')
        self.assertFalse(out['receipt']['e4_approved'])
        self.assertFalse(out['receipt']['knowledge_publication_authorized'])


if __name__=='__main__':unittest.main()