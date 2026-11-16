"""V123 chat-last gate against the REAL V6 synthetic host-batch receipt.

All evidence in these tests is synthetic. A structural PASS does not prove a
ChatGPT judgment is factually correct, a real law snapshot, or P0 readiness.
"""
import copy
import unittest

from ire.v6.atomic_exchange import audit_host_atomic_exchange
from v123_chat_final_gate import (
    assess_chat_final_gate, require_chat_final_release, SCHEMA,
)
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput, QualityNotProven
from ire.v6.tests.test_host_batch import HostBatchTests


def sha(text):
    return sha256(text.encode("utf-8"))


class ChatFinalGateTests(unittest.TestCase):
    def setUp(self):
        parent = HostBatchTests("test_one_command_commits_all_models_and_proofs_atomically")
        parent.setUp()
        self.addCleanup(parent.doCleanups)
        self.parent = parent
        self.source = parent.fx.source
        self.exchange = parent.fx.exchange
        self.host = parent.fx.store.submit_host_atomic_batch(**parent.args())
        audit = audit_host_atomic_exchange(self.source, self.exchange)
        self.review = {
            "schema": SCHEMA,
            "review_executor": "CHATGPT_IN_CHAT",
            "as_of": "2026-11-15",
            "source_sha256": self.source.source_sha256,
            "manifest_sha256": self.source.manifest_sha256,
            "host_event_sha256": self.host["event_sha256"],
            "host_bundle_sha256": self.host["bundle_sha256"],
            "atom_candidate_digest": audit["atom_candidate_digest"],
            "cue_disposition_digest": audit["cue_disposition_digest"],
            "blindness": "PRIOR_EXPOSED",
            "source_first_pass_completed": True,
            "counterexample_pass_completed": True,
            "disagreements_adjudicated": True,
            "source_cues": [
                {"cue_index": c.index,
                 "cue_text_sha256": sha(c.text),
                 "status": "REVIEWED",
                 "review_note_sha256": sha("synthetic cue note " + str(c.index))}
                for c in self.source.cues
            ],
            "atom_verdicts": [],
            "unresolved_high_risk_omissions": 0,
            "unresolved_audio_visual": 0,
            "external_independent_certified": False,
            "personalized_advice_approved": False,
            "p0_go": False,
            "review_private_evidence_sha256": sha("synthetic chat A/B evidence"),
        }
        self.evidence_bodies={a["claim_id"]:b"synthetic-only government text, not real law"
                              for a in self.exchange["atoms"]}
        for atom in self.exchange["atoms"]:
            self.review["atom_verdicts"].append({
                "claim_id": atom["claim_id"],
                "atom_sha256": json_digest(atom),
                "status": "ACCEPT_FOR_RESEARCH",
                "speaker_stance_checked": True,
                "conditions_exceptions_checked": True,
                "numeric_period_checked": True,
                "counterexample_checked": True,
                "high_risk": True,
                "financial_claim": True,
                "finance_evidence_status": "PRIMARY_BODY_AND_DATE_CHAT_CHECKED",
                "official_body_sha256": sha("synthetic-only government text, not real law"),
                "official_effective_as_of": "2026-11-10",
                "financial_scope_checked": True,
                "private_review_note_sha256": sha("synthetic claim note " + atom["claim_id"]),
            })

    def assess(self, review=None, host=None):
        return assess_chat_final_gate(self.source, self.exchange,
                   host_receipt=self.host if host is None else host,
                   chat_review=self.review if review is None else review,
                   store=self.parent.fx.store,
                   official_evidence_bodies=self.evidence_bodies)

    def test_01_real_native_v6_batch_then_synthetic_chat_final_pass(self):
        result = self.assess()
        self.assertEqual(result["status"], "CHAT_FINAL_PASS_RESEARCH_CANDIDATES_ONLY")
        self.assertTrue(result["research_candidate_export_allowed"])
        self.assertEqual(result["atoms_accepted"], 3)
        self.assertEqual(result["cues_reviewed"], 4)
        self.assertEqual(result["formal_financial_fact_approved"], 0)
        self.assertFalse(result["p0_go"])
        self.assertFalse(result["master_p4_knowledge_auto_merged"])

    def test_02_export_wrapper_requires_chat_last(self):
        decision = require_chat_final_release(self.source, self.exchange,
                                host_receipt=self.host, chat_review=self.review,
                                store=self.parent.fx.store,
                   official_evidence_bodies=self.evidence_bodies)
        self.assertTrue(decision["research_candidate_export_allowed"])
        with self.assertRaises(QualityNotProven):
            require_chat_final_release(self.source, self.exchange,
                                       host_receipt=self.host, chat_review=None,
                                       store=self.parent.fx.store,
                   official_evidence_bodies=self.evidence_bodies)

    def test_03_no_host_batch_no_export(self):
        result = assess_chat_final_gate(self.source, self.exchange,
                                        host_receipt=None, chat_review=self.review,
                                        store=self.parent.fx.store,
                   official_evidence_bodies=self.evidence_bodies)
        self.assertEqual(result["status"], "HOLD_MISSING_V6_HOST_BATCH_OR_STORE")
        self.assertFalse(result["research_candidate_export_allowed"])

    def test_04_missing_chat_no_export(self):
        result = assess_chat_final_gate(self.source, self.exchange,
                                        host_receipt=self.host, chat_review=None,
                                       store=self.parent.fx.store,
                   official_evidence_bodies=self.evidence_bodies)
        self.assertEqual(result["status"], "HOLD_MISSING_CHAT_FINAL_REVIEW")
        self.assertFalse(result["research_candidate_export_allowed"])

    def test_05_finance_open_holds_everything(self):
        self.review["atom_verdicts"][0].update(
            finance_evidence_status="OPEN", official_body_sha256=None,
            official_effective_as_of=None, financial_scope_checked=False,
        )
        r = self.assess()
        self.assertEqual(r["status"], "CHAT_FINAL_HOLD_OPEN")
        self.assertEqual(r["finance_open"], 1)
        self.assertFalse(r["research_candidate_export_allowed"])

    def test_06_rejected_claim_holds(self):
        self.review["atom_verdicts"][0]["status"] = "REJECT"
        self.assertEqual(self.assess()["atoms_rejected"], 1)
        self.assertEqual(self.assess()["status"],"CHAT_FINAL_REJECTED")
        self.assertFalse(self.assess()["research_candidate_export_allowed"])

    def test_07_open_cue_holds(self):
        self.review["source_cues"][0]["status"] = "OPEN"
        self.assertEqual(self.assess()["cues_open"], 1)
        self.assertFalse(self.assess()["research_candidate_export_allowed"])

    def test_08_high_risk_FN_and_audio_open_hold(self):
        self.review["unresolved_high_risk_omissions"] = 1
        self.review["unresolved_audio_visual"] = 1
        self.assertFalse(self.assess()["research_candidate_export_allowed"])
        self.assertEqual(self.assess()["high_risk_open"], 1)

    def test_09_missing_adjudication_holds(self):
        self.review["disagreements_adjudicated"] = False
        self.assertFalse(self.assess()["research_candidate_export_allowed"])

    def test_10_unchecked_condition_cannot_accept(self):
        self.review["atom_verdicts"][0]["conditions_exceptions_checked"] = False
        with self.assertRaisesRegex(InvalidInput, "UNVERIFIED_SEMANTIC_ACCEPTANCE"):
            self.assess()

    def test_11_false_external_independence_disallowed(self):
        self.review["external_independent_certified"] = True
        with self.assertRaisesRegex(InvalidInput, "FALSE_INDEPENDENT"):
            self.assess()

    def test_12_personal_advice_and_GO_disallowed(self):
        self.review["p0_go"] = True
        with self.assertRaises(InvalidInput):
            self.assess()
        self.review["p0_go"] = False
        self.review["personalized_advice_approved"] = True
        with self.assertRaises(InvalidInput):
            self.assess()

    def test_13_forged_source_cue_sha_rejected(self):
        self.review["source_cues"][1]["cue_text_sha256"] = "0"*64
        with self.assertRaisesRegex(InvalidInput, "CHAT_CUE_SOURCE"):
            self.assess()

    def test_14_wrong_host_receipt_sha_rejected(self):
        self.review["host_event_sha256"] = "1"*64
        with self.assertRaisesRegex(InvalidInput, "WRONG_FROZEN_SOURCE_OR_HOST"):
            self.assess()

    def test_15_duplicate_or_missing_atom_rejected(self):
        self.review["atom_verdicts"][1]["claim_id"] = self.review["atom_verdicts"][0]["claim_id"]
        with self.assertRaises(InvalidInput):
            self.assess()

    def test_16_downgrading_financial_claim_to_no_law_forbidden(self):
        self.review["atom_verdicts"][0].update(
            financial_claim=False,finance_evidence_status="NOT_APPLICABLE",
            official_body_sha256=None,official_effective_as_of=None,
            financial_scope_checked=False)
        with self.assertRaisesRegex(InvalidInput, "FINANCE_CLASSIFICATION_DOWNGRADE"):
            self.assess()

    def test_17_fake_future_effective_law_rejected(self):
        self.review["atom_verdicts"][0]["official_effective_as_of"]="2027-01-01"
        with self.assertRaisesRegex(InvalidInput, "FUTURE_EFFECTIVE_LAW"):
            self.assess()

    def test_18_no_fake_primary_body_for_open_source(self):
        self.review["atom_verdicts"][0]["finance_evidence_status"]="OPEN"
        with self.assertRaisesRegex(InvalidInput, "FINANCE_EVIDENCE_FAKED"):
            self.assess()

    def test_19_atom_proposition_tampering_rejected(self):
        self.review["atom_verdicts"][0]["atom_sha256"]="0"*64
        with self.assertRaisesRegex(InvalidInput, "CHAT_ATOM_SOURCE"):
            self.assess()

    def test_20_host_false_completion_rejected(self):
        host=copy.deepcopy(self.host)
        host["research_complete"] = True
        with self.assertRaisesRegex(InvalidInput, "HOST_FALSE_QUALITY_APPROVAL"):
            self.assess(host=host)

    def test_21_reject_private_source_text_in_receipt(self):
        receipt=self.assess()
        data=str(receipt)
        for c in self.source.cues:
            self.assertNotIn(c.text,data)
        for a in self.exchange["atoms"]:
            self.assertNotIn(a["proposition"],data)

    def test_22_extra_private_fields_are_not_accepted_as_public(self):
        self.review["owner_transcript_text"] = "secret synthetic"
        with self.assertRaisesRegex(InvalidInput, "CHAT_REVIEW_SCHEMA"):
            self.assess()

    def test_23_chat_source_first_not_claimed_as_external_gold(self):
        self.assertFalse(self.assess()["external_independent_gold"])
        self.assertFalse(self.assess()["research_complete_791"])

    def test_26_host_receipt_without_real_store_is_hold(self):
        got = assess_chat_final_gate(self.source,self.exchange,
                    host_receipt=self.host,chat_review=self.review,store=None)
        self.assertFalse(got["research_candidate_export_allowed"])
        self.assertEqual(got["status"],"HOLD_MISSING_V6_HOST_BATCH_OR_STORE")

    def test_27_stale_store_head_cannot_pass_chat_review(self):
        class StaleStore:
            def snapshot(self, scope_id):
                return {"ledger_head_sha256":"0"*64,
                        "progress":{"model_windows_recorded":2,
                                    "current_revision_structural_proof_records":2}}
        with self.assertRaisesRegex(InvalidInput,"HOST_STORE_STALE_OR_PROOF_NOT_COMMITTED"):
            assess_chat_final_gate(self.source,self.exchange,
                    host_receipt=self.host,chat_review=self.review,store=StaleStore(),official_evidence_bodies=self.evidence_bodies)

    def test_28_hash_only_official_without_bytes_is_hold(self):
        got=assess_chat_final_gate(self.source,self.exchange,
                 host_receipt=self.host,chat_review=self.review,
                 store=self.parent.fx.store,official_evidence_bodies={})
        self.assertEqual(got["status"],"CHAT_FINAL_HOLD_OPEN")
        self.assertEqual(got["finance_open"],3)

    def test_29_wrong_official_bytes_rejected(self):
        forged=copy.deepcopy(self.evidence_bodies)
        forged[self.exchange["atoms"][0]["claim_id"]]=b"wrong primary source"
        with self.assertRaisesRegex(InvalidInput,"OFFICIAL_BODY_BYTES_MISMATCH"):
            assess_chat_final_gate(self.source,self.exchange,
                 host_receipt=self.host,chat_review=self.review,
                 store=self.parent.fx.store,official_evidence_bodies=forged)

class ChatValidatedPriorPreviewTests(unittest.TestCase):
    def setUp(self):
        self.base=ChatFinalGateTests("test_01_real_native_v6_batch_then_synthetic_chat_final_pass")
        self.base.setUp()
        self.addCleanup(self.base.doCleanups)

    def test_24_final_chat_gate_blocks_p1_preview_without_chat(self):
        from v123_chat_validated_knowledge_preview import preview_chat_validated_candidates
        with self.assertRaises(QualityNotProven):
            preview_chat_validated_candidates(
                self.base.source,self.base.exchange,self.base.parent.knowledge,
                host_receipt=self.base.host,chat_review=None,store=self.base.parent.fx.store,
                official_evidence_bodies=self.base.evidence_bodies)

    def test_25_final_chat_gate_allows_only_readonly_p1(self):
        from v123_chat_validated_knowledge_preview import preview_chat_validated_candidates
        got = preview_chat_validated_candidates(
            self.base.source,self.base.exchange,self.base.parent.knowledge,
            host_receipt=self.base.host,chat_review=self.base.review,store=self.base.parent.fx.store,
                official_evidence_bodies=self.base.evidence_bodies)
        self.assertEqual(got["candidate_count"],3)
        self.assertEqual(got["status"],"CHAT_REVIEWED_RESEARCH_CANDIDATES_READONLY")
        self.assertFalse(got["master_p4_merged"])
        self.assertFalse(got["p0_go"])

if __name__ == "__main__":
    unittest.main()
