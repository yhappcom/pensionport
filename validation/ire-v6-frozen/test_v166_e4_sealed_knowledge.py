"""E4 HMAC durable research certification; synthetic artifacts ONLY.

This suite deliberately proves plain V126 can still physically corrupt or
append to SQLite, while E4's external-owner-pinned trust route REFUSES to
accept those rows as E4-approved research knowledge.
"""
import json
import sqlite3
import unittest
from pathlib import Path

from ire.v6.errors import InvalidInput,QualityNotProven
from test_v166_e4_primary_approval_gate import V166E4E3V128RealSQLiteIntegration
from v126_chat_approved_knowledge_store import PrivateKnowledgeStore
from v166_e4_sealed_knowledge import E4SealedKnowledgeStore

KEY=b"SYNTHETIC_TEST_KEY_NOT_PRODUCTION_"*2
BAD_KEY=b"WRONG_SYNTHETIC_KEY_NOT_PRODUCTION_"*2


class V166E4DurableExternalApprovalSealTests(unittest.TestCase):
    def setUp(self):
        self.parent=V166E4E3V128RealSQLiteIntegration(
            "test_14_both_valid_synthetic_children_do_publish_research_only")
        self.parent.setUp()
        self.addCleanup(self.parent.doCleanups)
        self.fx=self.parent.fx
        self.db=self.fx.knowledge.path
        self.store=E4SealedKnowledgeStore(self.db,external_signing_key=KEY)
        self.fx.knowledge=self.store

    def publish(self):
        result=self.parent.run_guarded()
        self.assertEqual(result["status"],"E4_PARENT_RESEARCH_CANDIDATES_PUBLISHED")
        pin=result["e4_external_owner_pin_sha256"]
        self.assertEqual(len(pin),64)
        self.assertTrue(result["e4_durable_certification_verified"])
        return pin

    def test_01_verified_e4_parent_is_sealed_to_owner_pin_and_all_sqlite_rows(self):
        pin=self.publish()
        result=self.store.audit_authorized_research(
            externally_pinned_seal_sha256=pin)
        self.assertEqual(result["knowledge_count"],3)
        self.assertEqual(result["parent_count"],1)
        self.assertEqual(result["approved_child_receipts_count"],2)
        self.assertFalse(result["source_finance_fact_legally_certified"])
        self.assertFalse(result["personal_investment_advice_approved"])
        self.assertEqual(self.fx._counts(),
                         {"events":3,"knowledge":3,"parent_publications":1})

    def test_02_legacy_v126_reopen_can_mutate_bytes_but_certification_fails(self):
        pin=self.publish()
        # The attacker CAN modify the same file from a separate connection;
        # no Python object can prohibit it. Crucially the E4 trust reader fails.
        with sqlite3.connect(str(self.db)) as con:
            con.execute("UPDATE knowledge SET entry_json='{}' "
                        "WHERE knowledge_id=(SELECT knowledge_id FROM knowledge LIMIT 1)")
        with self.assertRaises(QualityNotProven):
            self.store.audit_authorized_research(
                externally_pinned_seal_sha256=pin)

    def test_03_legacy_v126_publication_before_first_seal_cannot_be_certified(self):
        # The existing E3/V128 fixture used to produce 3 research entries even
        # with no E4 manifest. This DB is forever uncertified by E4 unless
        # explicitly rebuilt from approved primary evidence, never retrofitted.
        self.fx.knowledge=PrivateKnowledgeStore(self.db)
        result=self.parent.e3.run_host()
        self.assertTrue(result["all_video_knowledge_published"])
        self.assertEqual(self.fx._counts()["knowledge"],3)
        with self.assertRaises(QualityNotProven):
            self.store.audit_authorized_research(
                externally_pinned_seal_sha256="0"*64)
        self.fx.knowledge=self.store
        with self.assertRaises(QualityNotProven):
            self.parent.run_guarded()

    def test_04_wrong_hmac_signing_key_does_not_trust_valid_sqlite(self):
        pin=self.publish()
        wrong=E4SealedKnowledgeStore(self.db,external_signing_key=BAD_KEY)
        with self.assertRaisesRegex(QualityNotProven,"INVALID_EXTERNAL_HMAC"):
            wrong.audit_authorized_research(
                externally_pinned_seal_sha256=pin)

    def test_05_wrong_or_missing_owner_pin_fails_closed(self):
        pin=self.publish()
        with self.assertRaisesRegex(QualityNotProven,"OWNER_PIN_MISMATCH"):
            self.store.audit_authorized_research(
                externally_pinned_seal_sha256="a"*64)
        with self.assertRaises(InvalidInput):
            self.store.audit_authorized_research(
                externally_pinned_seal_sha256=None)

    def test_06_missing_seal_cannot_claim_approved_knowledge(self):
        with self.assertRaises(QualityNotProven):
            self.store.audit_authorized_research(
                externally_pinned_seal_sha256="0"*64)

    def test_07_after_commit_normal_v126_answer_query_disabled_in_certified_store(self):
        pin=self.publish()
        self.store.audit_authorized_research(
            externally_pinned_seal_sha256=pin)
        with self.assertRaisesRegex(QualityNotProven,"RAW_V126_EVIDENCE_REQUIRES"):
            self.store.evidence_for_question("수익률")

    def test_08_seal_file_tampering_is_caught_before_any_data_is_read(self):
        pin=self.publish()
        seal=Path(str(self.db)+".e4seal.json")
        doc=json.loads(seal.read_text(encoding="utf-8"))
        doc["payload"]["approved_child_receipts"][0][
            "primary_manifest_sha256"]="b"*64
        seal.write_text(json.dumps(doc),encoding="utf-8")
        with self.assertRaises(QualityNotProven):
            self.store.audit_authorized_research(
                externally_pinned_seal_sha256=pin)

    def test_09_previously_certified_db_requires_out_of_band_prior_owner_pin(self):
        pin=self.publish()
        reopen=E4SealedKnowledgeStore(self.db,external_signing_key=KEY)
        with self.assertRaisesRegex(QualityNotProven,"PREVIOUS_EXTERNAL_OWNER_PIN"):
            with reopen.begin_e4_parent_approval(["another_segment"]):
                pass
        reopened=E4SealedKnowledgeStore(self.db,external_signing_key=KEY,
                                       prior_owner_pin=pin)
        self.assertEqual(reopened.audit_authorized_research(
            externally_pinned_seal_sha256=pin)["parent_count"],1)

    def test_10_truncated_signing_key_rejected(self):
        with self.assertRaises(InvalidInput):
            E4SealedKnowledgeStore(self.db,external_signing_key=b"test")

    def test_11_fake_parent_receipt_cannot_seal_without_approved_e4_scope(self):
        with self.assertRaises(QualityNotProven):
            self.store.certify_completed_parent(
                child_ids=self.fx.checkpoint.child_ids,
                e3_downstream_result={"explicit_e3_status":
                    "PUBLISHED_RESEARCH_CANDIDATES_ONLY",
                    "all_video_knowledge_published":True})


if __name__=="__main__":
    unittest.main()
