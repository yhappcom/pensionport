"""Offline replay runner uses actual SQLite; fixtures are synthetic only."""
import copy,unittest
from pathlib import Path

from ire.v6.codec import canonical,sha256
from ire.v6.errors import InvalidInput
from ire.v6.offline_revision_replay import replay_private_revision
from ire.v6.chat_revision import compile_chat_atom_revision
from ire.v6.tests.test_chat_revision import edit,frame


class OfflineRevisionReplayTests(unittest.TestCase):
    def setUp(self):
        from ire.v6.tests.test_prior_knowledge import PriorKnowledgeTests
        parent=PriorKnowledgeTests(methodName="test_116_and_p4_29_are_replayed_without_approval")
        parent.setUp()
        self.addCleanup(parent.doCleanups)
        fx=parent.fx
        inventory,pin=fx.attest()
        old=fx.exchange["atoms"][0]
        edits=[edit([old["claim_id"]],frame(old,kind="HYPOTHETICAL",
               modality="HYPOTHETICAL",meaning_reason="Expected not guaranteed return."))]
        result=compile_chat_atom_revision(fx.source,fx.exchange,edits=edits)
        knowledge=copy.deepcopy(parent.inputs)
        for row in knowledge["relations"]:
            if row["claim_id"]==old["claim_id"]:
                row.update(claim_id=result["edit_lineage"][0]["new_claim_ids"][0],
                           target_kind="NONE",target_id=None,target_content_sha256=None,
                           relationship="NOVEL_PENDING",rationale="Requires a new relation review.")
        original=canonical(fx.exchange);review=canonical({"edits":edits,"cue_reviews":[]})
        self.path=Path(fx.tmp.name)/"offline"/"new.db"
        self.args=dict(database_path=self.path,scope_id="offline_scope",run_id="offline_run",
             raw=fx.raw,manifest=fx.manifest,inventory_bytes=inventory,
             expected_inventory_sha256=pin,frozen_native_bytes=original,
             expected_native_sha256=sha256(original),reviewer_bytes=review,
             expected_reviewer_sha256=sha256(review),knowledge=knowledge)

    def test_end_to_end_and_exclusive_new_db(self):
        r=replay_private_revision(**self.args)
        self.assertTrue(r["reopened_exact_revision"])
        self.assertTrue(r["sqlite_integrity_ok"])
        self.assertEqual(r["sequence"],8)
        self.assertFalse(r["research_complete"])
        with self.assertRaisesRegex(InvalidInput,"OFFLINE_NEW_DATABASE_REQUIRED"):
            replay_private_revision(**self.args)

    def test_bad_input_pin_does_not_create_db(self):
        with self.assertRaises(InvalidInput):
            replay_private_revision(**{**self.args,"reviewer_bytes":self.args["reviewer_bytes"]+b" "})
        self.assertFalse(self.path.exists())

    def test_missing_relation_does_not_create_db(self):
        self.args["knowledge"]["relations"].pop()
        with self.assertRaises(InvalidInput):replay_private_revision(**self.args)
        self.assertFalse(self.path.exists())
