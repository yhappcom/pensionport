"""V161 synthetic tests: no owner SRT; source-only never means finance approval."""
from __future__ import annotations
import copy
import unittest

from ire.v6.codec import sha256, json_digest
from ire.v6.source import verify_source
from ire.v6.errors import InvalidInput
from ire.v6.tests.test_source_and_proof import make_srt, make_manifest
from v161_source_utterance_scope import (
    audit_source_utterance_only, SCHEMA, USE_SCOPE,
)
from v161_finance_evidence_router import triage_finance_open_claim


class V161SourceOnlyTests(unittest.TestCase):
    def setUp(self):
        raw = make_srt([
            "투자 책을 읽는데 제가 이해하기 어렵습니다.",
            "사례가 낯설어 해설이 필요합니다.",
            "매수하면 무조건 수익을 보장합니다.",
            "연간 수익률은 10%입니다.",
        ])
        m = make_manifest(raw, cut=2)
        self.source = verify_source(raw,m,expected_source_sha256=sha256(raw),
                                    expected_manifest_sha256=json_digest(m))
        self.atom = {
            "claim_id":"C00001","kind":"OPINION",
            "context_cue_indices":[1,2],"numeric_references":[],
            "proposition":"화자는 투자 관련 책의 사례가 낯설고 어려웠다고 느낀다.",
        }
        note=sha256(b"synthetic human-in-chat speech act review")
        self.row = {
            "claim_id":"C00001","atom_sha256":json_digest(self.atom),
            "status":"SOURCE_ATTESTED_ONLY","financial_claim":True,
            "high_risk":False,"finance_evidence_status":"OPEN",
            "speaker_stance_checked":True,"conditions_exceptions_checked":True,
            "numeric_period_checked":True,"counterexample_checked":True,
            "private_review_note_sha256":note,
        }
        self.cues=[{"cue_index":i,"status":"REVIEWED"} for i in range(1,5)]
        self.row["source_utterance_attestation"]={
            "schema":SCHEMA,"claim_id":"C00001",
            "atom_sha256":json_digest(self.atom),
            "original_cue_indices":[1,2],
            "source_context_sha256":json_digest([
                {"cue_index":i,"cue_text_sha256":sha256(self.source.cues[i-1].text.encode())}
                for i in [1,2]]),
            "private_chat_note_sha256":note,"use_scope":USE_SCOPE,
            "external_financial_fact_verified":False,"source_audio_authenticated":False,
            "independent_gold_certified":False,"personal_advice_approved":False,
        }

    def audit(self,atom=None,row=None,cues=None):
        return audit_source_utterance_only(self.source,
            self.atom if atom is None else atom,
            self.row if row is None else row,
            self.cues if cues is None else cues)

    def test_01_safe_book_impression_stays_nonexportable(self):
        r=self.audit()
        self.assertFalse(r["primary_financial_fact_verified"])
        self.assertFalse(r["research_candidate_export_allowed"])
        self.assertFalse(r["personalized_advice_approved"])

    def test_02_source_atom_hash_tampering_fails(self):
        r=copy.deepcopy(self.row);r["source_utterance_attestation"]["atom_sha256"]="0"*64
        with self.assertRaises(InvalidInput):self.audit(row=r)

    def test_03_unreviewed_original_cue_fails(self):
        cues=copy.deepcopy(self.cues);cues[0]["status"]="OPEN"
        with self.assertRaises(InvalidInput):self.audit(cues=cues)

    def test_04_excluded_original_cue_fails(self):
        cues=copy.deepcopy(self.cues);cues[1]["status"]="EXCLUDED_FROM_RESEARCH"
        with self.assertRaises(InvalidInput):self.audit(cues=cues)

    def test_05_high_risk_may_not_bypass_financial_proof(self):
        r=copy.deepcopy(self.row);r["high_risk"]=True
        with self.assertRaises(InvalidInput):self.audit(row=r)

    def test_06_false_financial_fact_approval_fails(self):
        r=copy.deepcopy(self.row)
        r["source_utterance_attestation"]["external_financial_fact_verified"]=True
        with self.assertRaises(InvalidInput):self.audit(row=r)

    def test_07_false_personal_advice_approval_fails(self):
        r=copy.deepcopy(self.row)
        r["source_utterance_attestation"]["personal_advice_approved"]=True
        with self.assertRaises(InvalidInput):self.audit(row=r)

    def test_08_numeric_finance_atom_cannot_use_speech_only(self):
        atom=copy.deepcopy(self.atom)
        atom["numeric_references"]=[{"cue_index":1,"token":"10%"}]
        with self.assertRaises(InvalidInput):self.audit(atom=atom)

    def test_09_numeric_source_cue_cannot_hide_under_empty_atom_numbers(self):
        atom=copy.deepcopy(self.atom);atom["context_cue_indices"]=[3,4]
        r=copy.deepcopy(self.row)
        r["source_utterance_attestation"]["atom_sha256"]=json_digest(atom)
        r["source_utterance_attestation"]["original_cue_indices"]=[3,4]
        r["source_utterance_attestation"]["source_context_sha256"]=json_digest([
            {"cue_index":i,"cue_text_sha256":sha256(self.source.cues[i-1].text.encode())}
            for i in [3,4]])
        with self.assertRaises(InvalidInput):self.audit(atom=atom,row=r)

    def test_10_fact_kind_cannot_be_source_only(self):
        atom=copy.deepcopy(self.atom);atom["kind"]="FACT"
        with self.assertRaises(InvalidInput):self.audit(atom=atom)

    def test_11_external_quote_cannot_be_source_only(self):
        atom=copy.deepcopy(self.atom);atom["kind"]="QUOTE"
        with self.assertRaises(InvalidInput):self.audit(atom=atom)

    def test_12_private_chat_note_mismatch_fails(self):
        r=copy.deepcopy(self.row)
        r["source_utterance_attestation"]["private_chat_note_sha256"]="a"*64
        with self.assertRaises(InvalidInput):self.audit(row=r)

    def test_13_finance_work_queue_exact_source_pin(self):
        row={"claim_id":"C00001","atom_sha256":json_digest(self.atom),
             "status":"OPEN","financial_claim":True}
        got=triage_finance_open_claim(self.source,self.atom,row)
        self.assertTrue(got["ChatGPT_meaning_review_required"])
        self.assertFalse(got["finance_evidence_approved"])
        row["atom_sha256"]="0"*64
        with self.assertRaises(InvalidInput):
            triage_finance_open_claim(self.source,self.atom,row)

    def test_14_routing_cannot_accept_a_claim(self):
        row={"claim_id":"C00001","atom_sha256":json_digest(self.atom),
             "status":"ACCEPT_FOR_RESEARCH","financial_claim":True}
        with self.assertRaises(InvalidInput):
            triage_finance_open_claim(self.source,self.atom,row)

    def test_15_current_law_needs_effective_scope(self):
        atom=copy.deepcopy(self.atom)
        atom["proposition"]="연금저축 세액공제는 실제 적용 법령에 따라야 한다"
        row={"claim_id":"C00001","atom_sha256":json_digest(atom),
             "status":"OPEN","financial_claim":True}
        q=triage_finance_open_claim(self.source,atom,row)
        self.assertEqual(q["evidence_work_queue"],"CURRENT_LAW_EFFECTIVE_SCOPE")
        self.assertFalse(q["current_rule_applicability_verified"])

    def test_16_issuer_fact_needs_company_primary_source(self):
        atom=copy.deepcopy(self.atom)
        atom["proposition"]="삼성전자 HBM 생산 역사에 대한 외부 사실 주장"
        row={"claim_id":"C00001","atom_sha256":json_digest(atom),
             "status":"OPEN","financial_claim":True}
        q=triage_finance_open_claim(self.source,atom,row)
        self.assertEqual(q["evidence_work_queue"],"CORPORATE_ISSUER_FACT")
        self.assertFalse(q["finance_evidence_approved"])



    def test_17_additive_overlay_keeps_native_v123_open_and_blocks_v128(self):
        from unittest.mock import patch
        from v161_source_review_overlay import assess_source_only_overlay_then_v123
        original = {"atom_verdicts":[{"claim_id":"C00001","status":"OPEN","financial_claim":True}],
                    "source_cues":self.cues}
        fake_native={"status":"CHAT_FINAL_HOLD_OPEN","atoms_open":1,"finance_open":1,
                     "research_candidate_export_allowed":False}
        with patch("v161_source_review_overlay.audit_host_atomic_exchange",return_value={}), \
             patch("v161_source_review_overlay.assess_chat_final_gate",return_value=fake_native):
            got=assess_source_only_overlay_then_v123(
                self.source,{"atoms":[self.atom]},host_receipt=None,chat_review=original,
                store=None,official_evidence_bodies={},source_only_reviews=[self.row])
        self.assertEqual(got["native_v123_atoms_open_unchanged"],1)
        self.assertEqual(got["native_finance_fact_evidence_open_unchanged"],1)
        self.assertEqual(got["source_first_semantic_tasks_remaining"],0)
        self.assertEqual(original["atom_verdicts"][0]["status"],"OPEN")
        self.assertFalse(got["research_export_allowed"])
        self.assertFalse(got["v126_v128_knowledge_publish_allowed"])

    def test_18_additive_overlay_cannot_repeat_source_only_proof(self):
        from unittest.mock import patch
        from v161_source_review_overlay import assess_source_only_overlay_then_v123
        original = {"atom_verdicts":[{"claim_id":"C00001","status":"OPEN","financial_claim":True}],
                    "source_cues":self.cues}
        with patch("v161_source_review_overlay.audit_host_atomic_exchange",return_value={}):
            with self.assertRaises(InvalidInput):
                assess_source_only_overlay_then_v123(
                    self.source,{"atoms":[self.atom]},host_receipt=None,chat_review=original,
                    store=None,official_evidence_bodies={},source_only_reviews=[self.row,self.row])

    def test_19_additive_overlay_rejects_nonopen_native_atom(self):
        from unittest.mock import patch
        from v161_source_review_overlay import assess_source_only_overlay_then_v123
        original = {"atom_verdicts":[{"claim_id":"C00001","status":"ACCEPT_FOR_RESEARCH","financial_claim":True}],
                    "source_cues":self.cues}
        with patch("v161_source_review_overlay.audit_host_atomic_exchange",return_value={}):
            with self.assertRaises(InvalidInput):
                assess_source_only_overlay_then_v123(
                    self.source,{"atoms":[self.atom]},host_receipt=None,chat_review=original,
                    store=None,official_evidence_bodies={},source_only_reviews=[self.row])

if __name__=="__main__":
    unittest.main()
