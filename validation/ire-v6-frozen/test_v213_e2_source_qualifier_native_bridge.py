"""V213 tests: real (synthetic-source) V176 owner→native V6, not a mock V6.

Each audit goes through the SAME native V176.compile_native_v6_stage and
ire.v6.atomic_exchange.audit_host_atomic_exchange. Tests never approve E2.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import EngineChatSession, COMMIT
from v213_e2_source_qualifier_native_bridge import (
    ANSWER, E2QualifierCustody, compile_e2_safe_native_stage, ZERO,
)

RAW=(
    "1\n00:00:01,000 --> 00:00:01,900\n"
    "ETF는 조건에 따라 손실이 발생할 수 있습니다.\n\n"
    "2\n00:00:02,000 --> 00:00:02,900\n"
    "다만 원금이 보장되는 상품은 아닙니다.\n\n"
    "3\n00:00:03,000 --> 00:00:03,900\n"
    "여기서 가상 ETF 설명을 마칩니다.\n"
).encode("utf-8")

NOTE="원본의 조건 표현과 설명자의 추가적인 투자 주의사항을 구분해서 미확정 상태로 보관합니다."


class TestV213NativeQualifierBridge(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db=Path(self.tmp.name)/"owner.sqlite"
        self.private=Path(self.tmp.name)/"private_source_qualifiers.sqlite"
        self.owner=EngineChatSession(
            self.db,RAW,"AbCdEf12345",owner_source_sha256=sha256(RAW),
            window_size=3,expected_window_count=1)
        task=self.owner.prepare(limit=3,source_first_only=True)
        responses=[]
        for t in task["target_cues"]:
            i=t["cue_index"]
            atom=([{
                "proposition":"ETF 투자에는 특정 조건에서 손실 가능성이 있다는 설명입니다.",
                "kind":"FACT",
                "quote":"ETF는 조건에 따라 손실이 발생할 수 있습니다.",
                "context_cue_indices":[1,2],
                "conditions":["조건이 적용되는 경우"],
                "exceptions":["원금이 보장된다는 의미는 아닙니다"],
                "numeric_tokens":[],
                "high_risk":True,"needs_official_source":True,
            }] if i==1 else [])
            responses.append({
                "cue_index":i,
                "source_text_sha256":t["source_text_sha256"],
                "disposition":"ASSERTION" if atom else "NON_RESEARCH",
                "analysis":"원본에 존재하는 투자 조건과 금융 설명을 예비 검토했으며 사실 승인하지 않았습니다.",
                "speaker_role":"HOST","claims":atom,
                "limitations_checked":True,
            })
        res=self.owner.submit(task,{
            "schema":COMMIT,"challenge_sha256":task["challenge_sha256"],
            "review_executor":"CHATGPT_IN_CHAT","responses":responses})
        self.assertFalse(res["e4_approved"])
        self.head=self.owner.progress()["checkpoint_head_sha256"]
        self.journal=E2QualifierCustody(
            self.owner,self.private,expected_owner_head=self.head)

    def prepare_answers(self,origins=("SOURCE_EXPLICIT","SOURCE_EXPLICIT")):
        packet=self.journal.prepare(limit=10)
        self.assertEqual(len(packet["term_ids"]),2)
        reviews=[]
        for item,origin in zip(packet["terms"],origins):
            if origin in {"SOURCE_EXPLICIT","SOURCE_CONTEXT"}:
                cue=1 if item["field"]=="conditions" else 2
                quote=("조건에 따라" if cue==1 else
                       "원금이 보장되는 상품은 아닙니다")
            else:
                cue=None;quote=None
            reviews.append({
                "term_id":item["term_id"],"term_sha256":item["term_sha256"],
                "origin":origin,"source_quote":quote,"source_cue_index":cue,
                "meaning_rationale":NOTE,
                "speaker_condition_certified":False,
                "financial_fact_approved":False,
                "independent_gold_certified":False,
                "e2_final_pass":False,"e3_e4_e5_authorized":False,
            })
        answer={
            "schema":ANSWER,"challenge_sha256":packet["challenge_sha256"],
            "review_executor":"CHATGPT_IN_CHAT","responses":reviews}
        return packet,answer

    def submit_reviewer(self,origins=("SOURCE_EXPLICIT","SOURCE_EXPLICIT")):
        packet,answer=self.prepare_answers(origins)
        return self.journal.submit(
            packet,answer,
            expected_private_head=packet["private_qualifier_head_sha256"])

    def test_01_v182_loss_reproduced_then_original_condition_and_exception_mapped(self):
        original,summary=self.owner.compile_native_v6_stage()
        self.assertEqual(original["atoms"][0]["condition_cue_indices"],[])
        self.assertEqual(original["atoms"][0]["exception_cue_indices"],[])
        self.assertEqual(summary["semantic_projection_gate"]["unprojected_condition_terms"],1)
        self.assertEqual(summary["semantic_projection_gate"]["unprojected_exception_terms"],1)
        self.submit_reviewer()
        exchange,receipt=compile_e2_safe_native_stage(self.owner,self.journal)
        self.assertEqual(exchange["atoms"][0]["condition_cue_indices"],[1])
        self.assertEqual(exchange["atoms"][0]["exception_cue_indices"],[2])
        self.assertEqual(exchange["atoms"][0]["context_cue_indices"],[1,2])
        self.assertEqual(receipt["source_explicit_condition_exception_terms_mapped"],2)
        self.assertEqual(receipt["source_terms_not_projected_as_speaker_spoken"],0)
        self.assertTrue(receipt["all_v6_projected_indices_match_verbatim_source_reviews"])
        self.assertEqual(exchange["atoms"][0]["stance"],"UNRESOLVED")
        self.assertEqual(exchange["atoms"][0]["speaker"],"UNKNOWN")
        self.assertFalse(receipt["e2_final_pass"])
        self.assertFalse(receipt["e3_e4_e5_authorized"])
        self.assertFalse(receipt["financial_truth_approved"])

    def test_02_reviewer_caution_not_speaker_exception(self):
        self.submit_reviewer(("SOURCE_EXPLICIT","REVIEWER_ADDED"))
        exchange,receipt=compile_e2_safe_native_stage(self.owner,self.journal)
        self.assertEqual(exchange["atoms"][0]["condition_cue_indices"],[1])
        self.assertEqual(exchange["atoms"][0]["exception_cue_indices"],[])
        self.assertEqual(receipt["source_explicit_condition_exception_terms_mapped"],1)
        self.assertEqual(receipt["source_terms_not_projected_as_speaker_spoken"],1)

    def test_03_source_context_not_misclassified_as_spoken_qualifier(self):
        self.submit_reviewer(("SOURCE_CONTEXT","REVIEWER_ADDED"))
        exchange,receipt=compile_e2_safe_native_stage(self.owner,self.journal)
        self.assertEqual(exchange["atoms"][0]["condition_cue_indices"],[])
        self.assertEqual(exchange["atoms"][0]["exception_cue_indices"],[])
        self.assertEqual(receipt["source_terms_not_projected_as_speaker_spoken"],2)

    def test_04_all_unresolved_kept_in_private_owner_not_erased(self):
        self.submit_reviewer(("UNRESOLVED","UNRESOLVED"))
        exchange,receipt=compile_e2_safe_native_stage(self.owner,self.journal)
        self.assertEqual(exchange["atoms"][0]["condition_cue_indices"],[])
        self.assertEqual(receipt["source_terms_not_projected_as_speaker_spoken"],2)
        with sqlite3.connect(self.db) as db:
            atom=json.loads(db.execute(
                "SELECT record FROM cue_reviews WHERE cue_index=1").fetchone()[0])["claims"][0]
        self.assertEqual(len(atom["conditions"]),1)
        self.assertEqual(len(atom["exceptions"]),1)

    def test_05_forged_nonverbatim_condition_rejected(self):
        packet,answer=self.prepare_answers()
        answer["responses"][0]["source_quote"]="ETF는 원금을 보장합니다"
        with self.assertRaisesRegex(InvalidInput,
                                    "SOURCE_QUOTE_NOT_VERBATIM_IN_CONTEXT"):
            self.journal.submit(packet,answer,
                expected_private_head=packet["private_qualifier_head_sha256"])

    def test_06_external_cue_quote_wrong_context_rejected(self):
        packet,answer=self.prepare_answers()
        answer["responses"][0]["source_cue_index"]=3
        with self.assertRaisesRegex(InvalidInput,
                                    "SOURCE_QUOTE_NOT_VERBATIM_IN_CONTEXT"):
            self.journal.submit(packet,answer,
                expected_private_head=packet["private_qualifier_head_sha256"])

    def test_07_reviewer_added_cannot_forge_original_quote(self):
        packet,answer=self.prepare_answers(("REVIEWER_ADDED","UNRESOLVED"))
        answer["responses"][0]["source_quote"]="조건에 따라"
        with self.assertRaisesRegex(InvalidInput,
                                    "REVIEWER_CAUTION_CANNOT_BECOME_SOURCE_ANCHOR"):
            self.journal.submit(packet,answer,
                expected_private_head=packet["private_qualifier_head_sha256"])

    def test_08_any_authority_escalation_rejected(self):
        for field in ("speaker_condition_certified","financial_fact_approved",
                      "independent_gold_certified","e2_final_pass",
                      "e3_e4_e5_authorized"):
            packet,answer=self.prepare_answers()
            answer["responses"][0][field]=True
            with self.assertRaisesRegex(InvalidInput,
                                        "QUALIFIER_RESPONSE_OR_FALSE_AUTHORITY"):
                self.journal.submit(packet,answer,
                    expected_private_head=packet["private_qualifier_head_sha256"])

    def test_09_owner_checkpoint_wrong_prevents_private_journal(self):
        with self.assertRaisesRegex(InvalidInput,
                                    "OWNER_HEAD_OR_CUE_CENSUS_CHANGED"):
            E2QualifierCustody(self.owner,Path(self.tmp.name)/"wrong.sqlite",
                expected_owner_head="f"*64)

    def test_10_reopen_replays_exact_private_source_qualifier_head(self):
        saved=self.submit_reviewer()
        reloaded=E2QualifierCustody(
            self.owner,self.private,expected_owner_head=self.head)
        p=reloaded.progress(expected_private_head=saved["private_head_sha256"])
        self.assertEqual(p["reviewed_terms"],2)
        ex,receipt=compile_e2_safe_native_stage(self.owner,reloaded)
        self.assertEqual(ex["atoms"][0]["exception_cue_indices"],[2])
        self.assertEqual(receipt["e2_qualifier_private_head_sha256"],
                         saved["private_head_sha256"])

    def test_11_private_sqlite_hash_tamper_rejected(self):
        self.submit_reviewer()
        with sqlite3.connect(self.private) as db:
            db.execute("UPDATE events SET event_sha=? WHERE seq=1",("f"*64,))
        with self.assertRaisesRegex(InvalidInput,
                                    "QUALIFIER_EVENT_HASH_OR_FIELDS_CHANGED"):
            self.journal.progress()

    def test_12_private_sqlite_permissions_rejected(self):
        self.private.chmod(0o644)
        with self.assertRaisesRegex(InvalidInput,
                                    "QUALIFIER_SQLITE_PERMISSIONS_CHANGED"):
            self.journal.progress()

    def test_13_duplicate_stale_submission_rejected_no_extra_event(self):
        packet,answer=self.prepare_answers()
        self.journal.submit(packet,answer,expected_private_head=ZERO)
        with self.assertRaisesRegex(InvalidInput,"QUALIFIER_HEAD_STALE"):
            self.journal.submit(packet,answer,expected_private_head=ZERO)
        with sqlite3.connect(self.private) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM events").fetchone()[0],1)

    def test_14_private_head_pin_external_conflict_rejected(self):
        self.submit_reviewer()
        with self.assertRaisesRegex(InvalidInput,
                                    "EXTERNAL_PRIVATE_CHECKPOINT_HEAD_MISMATCH"):
            self.journal.progress(expected_private_head="f"*64)

    def test_15_source_first_stage_before_terms_review_stays_hold(self):
        exchange,receipt=compile_e2_safe_native_stage(self.owner,self.journal)
        self.assertEqual(receipt["source_explicit_condition_exception_terms_mapped"],0)
        self.assertEqual(receipt["source_terms_not_projected_as_speaker_spoken"],2)
        self.assertFalse(receipt["all_original_owner_terms_reviewed"])
        self.assertEqual(exchange["atoms"][0]["condition_cue_indices"],[])
        self.assertFalse(receipt["e2_final_pass"])


    def test_16_missing_task_ids_returns_invalidinput_not_typeerror(self):
        packet,answer=self.prepare_answers()
        packet["term_ids"]=None
        with self.assertRaisesRegex(InvalidInput,
                                    "QUALIFIER_TASK_NOT_ISSUED_OR_STALE"):
            self.journal.submit(packet,answer,expected_private_head=ZERO)

    def test_17_unhashable_task_ids_return_invalidinput_not_typeerror(self):
        packet,answer=self.prepare_answers()
        packet["term_ids"]=[{"unhashable":"old-schema"}]
        with self.assertRaisesRegex(InvalidInput,
                                    "QUALIFIER_TASK_NOT_ISSUED_OR_STALE"):
            self.journal.submit(packet,answer,expected_private_head=ZERO)

    def test_18_corrupted_private_event_with_list_term_id_fail_closed(self):
        from ire.v6.codec import canonical,json_digest
        self.submit_reviewer()
        with sqlite3.connect(self.private) as db:
            frame=json.loads(db.execute(
                "SELECT payload FROM events WHERE seq=1").fetchone()[0])
            frame["challenge"]["term_ids"]=[{"bad":"historical schema"}]
            db.execute("UPDATE events SET payload=?,event_sha=? WHERE seq=1",
                (canonical(frame).decode("utf-8"),json_digest(frame)))
        with self.assertRaisesRegex(InvalidInput,"TERM_TASK_INDEX_SCHEMA"):
            self.journal.progress()

    def test_19_stage_summary_remains_e2_hold_even_with_full_source_mapping(self):
        self.submit_reviewer()
        exchange,receipt=compile_e2_safe_native_stage(self.owner,self.journal)
        _,native=self.owner.compile_native_v6_stage(
            qualifier_provenance=self.journal)
        self.assertFalse(native["semantic_projection_gate"][
            "full_semantic_projection_verified"])
        self.assertFalse(native["semantic_projection_gate"][
            "v123_e4_approval_permitted"])
        self.assertTrue(receipt["all_original_owner_terms_reviewed"])
        self.assertFalse(receipt["speaker_and_stance_finalized"])
        self.assertEqual(len(exchange["atoms"]),1)


if __name__=="__main__":
    unittest.main()
