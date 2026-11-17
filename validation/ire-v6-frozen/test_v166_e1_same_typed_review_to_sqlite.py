"""V166 E1 same-input typed review -> V123 -> V127.1 -> V128 -> V126 SQLite.

SYNTHETIC source and ChatGPT decision. This is an architecture integration
proof only; it is NOT owner video #1, legal evidence, E2 semantics, or E5 13-child.
"""
from __future__ import annotations

import copy
import sqlite3
import unittest
from unittest.mock import patch

from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput, QualityNotProven
from ire.v6.tests.test_atomic_exchange import HostAtomExchangeTests
from v123_chat_final_gate import assess_chat_final_gate
from test_v128_continuous_chat_atomic_parent import V128HostRunAndAtomicParentTests
from v166_shared_source_only_native_contract import (
    ROW_SCHEMA, compile_attested_source_only_quarantine,
)

CHAT_NOTE = (
    "이 발언은 8%를 확정한 금융사실이 아니라 아직 확인되지 않은 "
    "조건부 가설입니다. 해당 조건이 만족되지 않으면 수익과 손실 보장도 "
    "불가능하며 이는 금융효과의 증명도 개인 자문도 아닙니다."
)
PARENT_NOTE = (
    "ChatGPT 원문 확인: 투자 효과가 검증되지 않은 조건부 가설은 "
    "원문의 source-only 설명으로 격리하고 객관적인 승인 투자 사실과 "
    "연구 지식으로 내보내지 않습니다. 조건·예외는 별도로 확인합니다."
)


class V166E1SameTypedReviewToSQLite(unittest.TestCase):
    def setUp(self):
        old = HostAtomExchangeTests.sample

        def synthetic_speech_exchange(test):
            exchange = old(test)
            # Only the synthetic 8% 'may be' assertion is explicitly modelled
            # as a hypothetical. The exact same kind and source/host digest
            # flow to the native V123 and V128 checkpoints.
            atom = next(a for a in exchange["atoms"] if a["claim_id"]=="C00002")
            atom["kind"] = "HYPOTHETICAL"
            atom["speaker"] = "UNKNOWN"
            return exchange

        fixture = V128HostRunAndAtomicParentTests(
            "test_01_two_native_v6_children_seam_and_atomic_private_parent_publication")
        with patch.object(HostAtomExchangeTests, "sample", synthetic_speech_exchange):
            fixture.setUp()
        self.fx = fixture
        self.addCleanup(fixture.doCleanups)
        packet = fixture.packets[0]
        self.case = packet["case"]
        self.review = copy.deepcopy(self.case["chat_review"])
        self.source = self.case["source"]
        atom = next(a for a in self.case["exchange"]["atoms"]
                    if a["claim_id"] == "C00002")
        self.atom = atom
        verdict = next(v for v in self.review["atom_verdicts"]
                       if v["claim_id"] == "C00002")
        verdict.update(
            status="OPEN", finance_evidence_status="OPEN",
            official_body_sha256=None, official_effective_as_of=None,
            financial_scope_checked=False)
        cue_indices = sorted(set(atom["context_cue_indices"]))
        self.typed = {
            "schema":ROW_SCHEMA, "claim_id":"C00002",
            "atom_sha256":json_digest(atom),
            "source_sha256":self.source.source_sha256,
            "source_cue_indices":cue_indices,
            "source_context_sha256":json_digest([
                {"cue_index":i,
                 "cue_text_sha256":sha256(self.source.cues[i-1].text.encode("utf-8"))}
                for i in cue_indices]),
            "speech_type":"CONDITIONAL_PAYOFF_HYPOTHESIS_ONLY",
            "verbatim_anchor_cue_index":2,
            "verbatim_anchor":"8%일 수 있습니다",
            "source_speaker_identity":"UNKNOWN_NOT_AUDIO_AUTHENTICATED",
            "chat_meaning_analysis":CHAT_NOTE,
            "chat_meaning_analysis_sha256":sha256(CHAT_NOTE.encode("utf-8")),
            "conditions_checked":True, "exceptions_checked":True,
            "numeric_checked":True, "counterexample_checked":True,
            "speaker_stance_checked":True,
            "financial_factual_truth_certified":False,
            "strategy_effectiveness_verified":False,
            "individual_investment_advice_approved":False,
            "independent_gold_certified":False,
            "external_source_audio_authenticated":False,
            "research_knowledge_export_allowed":False,
            "source_only_attribution":True,
            "disclosure_restriction":
                "ORIGINAL_VIDEO_SPEECH_ONLY_NOT_FINANCIAL_TRUTH_OR_ADVICE"
        }
        previous_parent_review = fixture.parent_review

        def parent_review_with_quarantine(checkpoint, assembly, seams, packets):
            result = previous_parent_review(checkpoint, assembly, seams, packets)
            result.update(quarantine_dispositions_reviewed=True,
                          quarantine_cross_segment_dependencies_resolved=True)
            return result

        fixture.parent_review = parent_review_with_quarantine

    def _prepare(self):
        before = assess_chat_final_gate(
            self.source, self.case["exchange"],
            host_receipt=self.case["host_receipt"],
            chat_review=self.review,
            store=self.case["source_store"],
            official_evidence_bodies=self.case["official_evidence_bodies"])
        self.assertEqual(before["status"], "CHAT_FINAL_HOLD_OPEN")
        compiled = compile_attested_source_only_quarantine(
            self.source, self.case["exchange"], self.review, [self.typed],
            final_chat_quarantine_note=PARENT_NOTE)
        new_review = compiled["compiled_chat_review"]
        self.assertFalse(compiled["release_authorized_by_compiler"])
        self.assertEqual(compiled["source_only_quarantined_ids"], ["C00002"])
        self.case["chat_review"] = new_review
        after = assess_chat_final_gate(
            self.source, self.case["exchange"],
            host_receipt=self.case["host_receipt"],
            chat_review=new_review,
            store=self.case["source_store"],
            official_evidence_bodies=self.case["official_evidence_bodies"])
        self.assertEqual(after["status"],
                         "CHAT_FINAL_PASS_RESEARCH_CANDIDATES_ONLY")
        self.assertEqual(after.get("quarantined_claim_ids"), ["C00002"])
        return compiled

    def _counts(self):
        with sqlite3.connect(self.fx.knowledge.path) as con:
            return {t:con.execute("SELECT COUNT(*) FROM "+t).fetchone()[0]
                    for t in ("events","knowledge","parent_publications")
                    if con.execute("SELECT name FROM sqlite_master "
                                   "WHERE type='table' AND name=?",(t,)).fetchone()}

    def _assert_zero(self):
        data = self._counts()
        self.assertEqual(data.get("events",0),0)
        self.assertEqual(data.get("knowledge",0),0)
        self.assertEqual(data.get("parent_publications",0),0)

    def test_01_same_typed_review_native_v123_v127_v128_private_sqlite_commit(self):
        compiled = self._prepare()
        self.assertEqual(self.case["chat_review"],
                         compiled["compiled_chat_review"])
        result = self.fx.run_engine()
        self.assertEqual(result["status"],
                         "WHOLE_VIDEO_RESEARCH_CANDIDATE_PUBLISHED_ATOMICALLY")
        self.assertEqual(result["publication_receipt"]["entry_count"],2)
        self.assertEqual(self._counts(),
                         {"events":2,"knowledge":2,"parent_publications":1})
        with sqlite3.connect(self.fx.knowledge.path) as con:
            records=[s[0] for s in con.execute("SELECT entry_json FROM knowledge")]
        self.assertTrue(all('"claim_id":"C00002"' not in x for x in records))
        self.assertEqual(self.fx.knowledge.audit()["active_claims"],2)
        self.assertFalse(result["p0_go"])

    def test_02_missing_other_finance_original_blocks_atomic_parent(self):
        self._prepare()
        # Second child still contains an objective tax scope claim. It becomes
        # unverified and MUST NOT publish the first staged child.
        second = self.fx.packets[1]["case"]
        second["chat_review"]["atom_verdicts"][0].update(
            status="OPEN",finance_evidence_status="OPEN",
            official_body_sha256=None,official_effective_as_of=None,
            financial_scope_checked=False)
        result = self.fx.run_engine()
        self.assertEqual(result["status"],"HOLD_CHILD_CHAT_SEMANTICS_OR_FINANCE")
        self._assert_zero()

    def test_03_wrong_atom_digest_does_not_reach_publication(self):
        self.typed["atom_sha256"] = "0"*64
        with self.assertRaises(InvalidInput):
            compile_attested_source_only_quarantine(
                self.source,self.case["exchange"],self.review,[self.typed],
                final_chat_quarantine_note=PARENT_NOTE)
        self._assert_zero()

    def test_04_wrong_verbatim_anchor_does_not_reach_publication(self):
        self.typed["verbatim_anchor"] = "원문에 전혀 없던 임의 금융 주장"
        with self.assertRaises(InvalidInput):
            compile_attested_source_only_quarantine(
                self.source,self.case["exchange"],self.review,[self.typed],
                final_chat_quarantine_note=PARENT_NOTE)
        self._assert_zero()

    def test_05_changed_host_receipt_blocked_after_conversion(self):
        self._prepare()
        self.case["host_receipt"]=dict(self.case["host_receipt"])
        self.case["host_receipt"]["event_sha256"]="0"*64
        with self.assertRaises((InvalidInput,QualityNotProven)):
            self.fx.run_engine()
        self._assert_zero()

    def test_06_unreviewed_child_cue_blocked(self):
        self.review["source_cues"][1]["status"]="OPEN"
        with self.assertRaises(InvalidInput):
            compile_attested_source_only_quarantine(
                self.source,self.case["exchange"],self.review,[self.typed],
                final_chat_quarantine_note=PARENT_NOTE)
        self._assert_zero()


if __name__=="__main__":
    unittest.main()
