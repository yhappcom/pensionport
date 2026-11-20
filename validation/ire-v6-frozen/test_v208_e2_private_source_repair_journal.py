"""V208 private E2 source correction integration: normal, held and adversarial.

Synthetic Korean cue text only. Exercises the SAME private file for V206
census, V207 ChatGPT repair and V208 append-only custody; never E3 approval.
"""
from __future__ import annotations

import copy
from pathlib import Path
import sqlite3
import tempfile
import unittest

from ire.v6.codec import ZERO_SHA
from ire.v6.errors import InvalidInput
from v206_e2_full_cue_semantic_census import prepare_e2_cue_challenge
from v206_e2_private_cue_checkpoint import PrivateE2CensusCheckpoint
from v208_e2_private_source_repair_journal import PrivateE2RepairJournal
from test_v206_e2_full_cue_semantic_census import (
    TestV206KoreanQuestionQuoteMeaningGap,answered)
from test_v207_e2_unreleased_chat_repair import authored_plan


class TestV208PrivateSourceCorrection(unittest.TestCase):
    def setUp(self):
        self.fx=TestV206KoreanQuestionQuoteMeaningGap(
            "test_15_embedded_question_and_quoted_claim_do_not_disappear_as_noatom")
        self.fx.setUp()
        self.addCleanup(self.fx.doCleanups)
        self.owner=self.fx.owner
        self.head=self.fx.head
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/"owner_e2_census_and_repairs.db"
        self.census=PrivateE2CensusCheckpoint(
            self.path,self.owner,expected_owner_head=self.head)
        self.journal=PrivateE2RepairJournal(
            self.path,self.owner,expected_owner_head=self.head)
        self.c1=prepare_e2_cue_challenge(
            self.owner,expected_owner_head=self.head,
            start_cue=1,limit=2)
        self.a1=answered(self.c1,source_risks={
            1:("QUESTION_WITH_EMBEDDED_ASSERTION","8%가 무조건 비과세"),
            2:("QUOTE_WITH_FACT_DEPENDENCY","모든 소득이 비과세"),
        })
        self.plan=authored_plan(self.owner,self.c1,self.a1,self.head)
        self.c2=prepare_e2_cue_challenge(
            self.owner,expected_owner_head=self.head,start_cue=3,limit=2)
        self.a2=answered(self.c2)

    def checkpoint(self,all_cues=False):
        first=self.census.record(
            self.c1,self.a1,expected_private_head=ZERO_SHA)
        if all_cues:
            second=self.census.record(
                self.c2,self.a2,
                expected_private_head=first["private_head_sha256"])
            return second["private_head_sha256"]
        return first["private_head_sha256"]

    def store_repair(self,*,expected_census_head,expected_repair_head=ZERO_SHA,
                     plan=None,cue=None,answer=None):
        return self.journal.record_chat_repair(
            cue if cue is not None else self.c1,
            answer if answer is not None else self.a1,
            plan if plan is not None else self.plan,
            expected_census_head=expected_census_head,
            expected_repair_head=expected_repair_head)

    def test_01_requires_matching_original_cue_checkpoint_before_repair(self):
        with self.assertRaisesRegex(InvalidInput,
                                    "REPAIR_NOT_LINKED_TO_SAVED_CUE_REVIEW"):
            self.store_repair(expected_census_head=ZERO_SHA)
        self.assertEqual(self.journal.progress()["repair_batches_recorded"],0)

    def test_02_checkpoint_cue_then_explicit_repair_same_private_sqlite(self):
        c_head=self.checkpoint()
        before=self.owner.progress()["checkpoint_head_sha256"]
        r=self.store_repair(expected_census_head=c_head)
        self.assertEqual(r["status"],"E2_REPAIR_SAVED_UNRELEASED_PRIVATE")
        self.assertEqual(r["issues_reviewed"],2)
        self.assertEqual(r["unreleased_draft_claims"],2)
        self.assertEqual(self.owner.progress()["checkpoint_head_sha256"],before)
        p=self.journal.progress(externally_pinned_repair_head=
                                r["repair_head_sha256"])
        self.assertEqual(p["repair_batches_recorded"],1)
        self.assertEqual(p["held_batches_awaiting_explicit_chat_repair"],0)
        self.assertEqual(p["unreleased_draft_claims"],2)
        self.assertFalse(p["e2_final_pass"])
        self.assertFalse(p["e3_e4_e5_authorized"])
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute(
                "SELECT COUNT(*) FROM e2_events").fetchone()[0],1)
            self.assertEqual(db.execute(
                "SELECT COUNT(*) FROM e2_repairs").fetchone()[0],1)

    def test_03_private_reopen_replays_review_and_source_bound_repair(self):
        h=self.checkpoint(all_cues=True)
        r=self.store_repair(expected_census_head=h)
        reloaded=PrivateE2RepairJournal(
            self.path,self.owner,expected_owner_head=self.head)
        p=reloaded.progress(externally_pinned_repair_head=
                             r["repair_head_sha256"])
        self.assertEqual(p["source_review_batches"],2)
        self.assertEqual(p["repair_batches_recorded"],1)
        self.assertEqual(p["unreleased_draft_claims"],2)
        self.assertFalse(p["independent_semantic_gold_certified"])

    def test_04_duplicate_chat_repair_is_idempotent_no_new_row(self):
        h=self.checkpoint()
        r=self.store_repair(expected_census_head=h)
        repeated=self.store_repair(
            expected_census_head=h,
            expected_repair_head=ZERO_SHA)
        self.assertEqual(repeated["status"],"IDEMPOTENT_E2_REPAIR_REPLAY")
        self.assertEqual(repeated["repair_head_sha256"],
                         r["repair_head_sha256"])
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute(
                "SELECT COUNT(*) FROM e2_repairs").fetchone()[0],1)

    def test_05_conflicting_chat_repair_does_not_replace_existing_decision(self):
        h=self.checkpoint()
        self.store_repair(expected_census_head=h)
        changed=copy.deepcopy(self.plan)
        changed["decisions"][0]["review_action"]="KEEP_OPEN"
        changed["decisions"][0]["draft_claims"]=[]
        with self.assertRaisesRegex(InvalidInput,
                                    "CONFLICTING_SOURCE_REPAIR_NO_OVERWRITE"):
            self.store_repair(expected_census_head=h,plan=changed)
        self.assertEqual(self.journal.progress()["repair_batches_recorded"],1)

    def test_06_repair_only_for_originally_checkpointed_review(self):
        h=self.checkpoint()
        with self.assertRaisesRegex(InvalidInput,
                                    "REPAIR_NOT_LINKED_TO_SAVED_CUE_REVIEW"):
            self.store_repair(
                expected_census_head=h,answer=answered(self.c1))
        self.assertEqual(self.journal.progress()["repair_batches_recorded"],0)

    def test_07_stale_census_head_after_second_review_fails_closed(self):
        old=self.checkpoint()
        self.census.record(self.c2,self.a2,expected_private_head=old)
        with self.assertRaisesRegex(InvalidInput,
                                    "CENSUS_CHANGED_DURING_REPAIR"):
            self.store_repair(expected_census_head=old)
        self.assertEqual(self.journal.progress()["repair_batches_recorded"],0)

    def test_08_corrupt_repair_hash_rejected_on_reopen_and_progress(self):
        h=self.checkpoint()
        self.store_repair(expected_census_head=h)
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE e2_repairs SET event_sha256=? WHERE seq=1",
                       ("f"*64,))
        with self.assertRaisesRegex(InvalidInput,
                                    "CHAIN_RECORD_OR_HASH_CHANGED"):
            self.journal.progress()
        with self.assertRaisesRegex(InvalidInput,
                                    "CHAIN_RECORD_OR_HASH_CHANGED"):
            PrivateE2RepairJournal(
                self.path,self.owner,expected_owner_head=self.head)

    def test_09_external_repair_head_pin_rejects_substituted_history(self):
        h=self.checkpoint()
        self.store_repair(expected_census_head=h)
        with self.assertRaisesRegex(InvalidInput,
                                    "EXTERNAL_REPAIR_HEAD_CHANGED"):
            self.journal.progress(externally_pinned_repair_head="f"*64)

    def test_10_bad_plan_never_enqueues_repair(self):
        h=self.checkpoint()
        altered=copy.deepcopy(self.plan)
        altered["financial_fact_approved"]=True
        with self.assertRaisesRegex(InvalidInput,"PIN_OR_FALSE_RELEASE"):
            self.store_repair(expected_census_head=h,plan=altered)
        self.assertEqual(self.journal.progress()["repair_batches_recorded"],0)

    def test_11_owner_head_drift_never_releases_repair(self):
        h=self.checkpoint()
        with self.assertRaisesRegex(InvalidInput,
                                    "EXTERNAL_OWNER_HEAD_STALE"):
            self.journal.record_chat_repair(
                self.c1,self.a1,self.plan,
                expected_census_head=h,
                expected_repair_head=ZERO_SHA)
        # In this specific test the original owner remains unchanged.
        self.assertEqual(self.journal.progress()["repair_batches_recorded"],0)


if __name__=="__main__":
    unittest.main()
