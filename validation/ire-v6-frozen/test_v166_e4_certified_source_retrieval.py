"""E4 signed store -> E2 separated quote actual V126 SQLite read, synthetic.

No user portfolio, no external finance truth, no finalized investment advice.
If external owner pin, source, E2 reviewer digest or durable V126 row changes
then the certified research read must FAIL CLOSED.
"""
import copy
import json
import sqlite3
import unittest

from ire.v6.codec import ZERO_SHA
from ire.v6.errors import InvalidInput,QualityNotProven
from test_v166_e2_v126_source_separated_retrieval import V166E2ActualV126SafeAnswerContext
from test_v166_e4_primary_approval_gate import (
    make_manifest,replace_synthetic_official_body)
from v166_e4_sealed_knowledge import E4SealedKnowledgeStore
from v166_e4_primary_approval_gate import run_e4_guarded_parent

TEST_KEY=b"SYNTHETIC_E4_SIGNED_RESEARCH_CONTEXT_KEY_"*2


class V166E4CertifiedE2ContextRealSqliteTests(unittest.TestCase):
    def setUp(self):
        self.e2=V166E2ActualV126SafeAnswerContext(
            "test_01_real_v126_retrieval_strips_mixed_proposition")
        self.e2.setUp()
        self.addCleanup(self.e2.doCleanups)
        self.fx=self.e2.fx
        self.fx.knowledge=E4SealedKnowledgeStore(
            self.fx.knowledge.path,external_signing_key=TEST_KEY)
        self.manifests={}
        for sid,packet in zip(self.fx.checkpoint.child_ids,self.fx.packets):
            replace_synthetic_official_body(packet["case"])
            self.manifests[sid]=make_manifest(packet["case"])

    def _approved_pin_and_ids(self):
        from unittest.mock import patch
        from test_v166_e4_primary_approval_gate import BODY
        with patch("v166_e4_primary_approval_gate._fetch_approved_primary_https",
                   return_value=BODY):
            published=run_e4_guarded_parent(
                self.fx.checkpoint,self.fx.knowledge,
                review_or_load_child=self.fx.child,
                review_seams=self.fx.seams,
                review_parent=self.fx.parent_review,
                primary_manifest_for_child=lambda sid,case:self.manifests[sid],
                expected_knowledge_head=ZERO_SHA,
                now_as_of="2026-11-17")
        self.assertEqual(published["status"],"E4_PARENT_RESEARCH_CANDIDATES_PUBLISHED")
        pin=published["e4_external_owner_pin_sha256"]
        with sqlite3.connect(str(self.fx.knowledge.path)) as con:
            entries=[json.loads(r[0]) for r in
                     con.execute("SELECT entry_json FROM knowledge")]
        ids=[r["knowledge_id"] for r in entries if r["claim_id"]=="C00001"]
        self.assertEqual(len(ids),1)
        return pin,ids

    def _read(self,pin,ids,ledger=None):
        return self.fx.knowledge.certified_e2_source_separated_context(
            "투자 수익률 조건과 위험",externally_pinned_seal_sha256=pin,
            source=self.e2.source,exchange=self.e2.exchange,
            ledger=self.e2.ledger if ledger is None else ledger,
            selected_knowledge_ids=ids)

    def test_01_certified_source_quote_separate_chat_caution_not_legacy_proposition(self):
        pin,ids=self._approved_pin_and_ids()
        item=self._read(pin,ids)
        self.assertEqual(item["schema"],"IRE_V166_E4_E2_CERTIFIED_RESEARCH_CONTEXT_V1")
        self.assertTrue(item["e4_db_rows_certified_twice"])
        self.assertEqual(item["count"],1)
        self.assertNotIn("proposition",item["claims"][0])
        self.assertNotIn("atom",item["claims"][0])
        self.assertEqual(item["claims"][0]["reviewer_role"],
                         "CHATGPT_CAUTION_NOT_ORIGINAL_SPEAKER_QUOTE")
        self.assertFalse(item["personal_investment_advice_approved"])
        self.assertTrue(item["chatgpt_final_advice_review_required"])

    def test_02_valid_db_wrong_external_owner_pin_blocks_read(self):
        pin,ids=self._approved_pin_and_ids()
        with self.assertRaises(QualityNotProven):
            self._read("0"*64,ids)

    def test_03_corrupted_reviewer_semantic_proof_blocks_read(self):
        pin,ids=self._approved_pin_and_ids()
        ledger=copy.deepcopy(self.e2.ledger)
        ledger["rows"][0]["reviewer_note_sha256"]="f"*64
        with self.assertRaises(InvalidInput):
            self._read(pin,ids,ledger)

    def test_04_same_file_legacy_mutation_blocks_certified_evidence(self):
        pin,ids=self._approved_pin_and_ids()
        with sqlite3.connect(str(self.fx.knowledge.path)) as con:
            con.execute("UPDATE knowledge SET entry_json='{}' "
                        "WHERE knowledge_id=?",(ids[0],))
        with self.assertRaises(QualityNotProven):
            self._read(pin,ids)

    def test_05_unmatched_other_child_scope_fails_closed(self):
        pin,ids=self._approved_pin_and_ids()
        with sqlite3.connect(str(self.fx.knowledge.path)) as con:
            rows=[json.loads(r[0]) for r in
                  con.execute("SELECT entry_json FROM knowledge")]
        mismatched=[r["knowledge_id"] for r in rows
                    if r["source_sha256"] != self.e2.source.source_sha256]
        self.assertTrue(mismatched)
        with self.assertRaises(InvalidInput):
            self._read(pin,mismatched[:1])


if __name__=="__main__":
    unittest.main()
